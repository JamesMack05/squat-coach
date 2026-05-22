"""Telegram bot entry point.

Run modes:
    Long-poll (dev):    python -m bot.main           # WEBHOOK_URL unset
    Webhook (Thu+):     python -m bot.main           # WEBHOOK_URL set in .env
                       # plus: cloudflared tunnel --url http://localhost:8443
"""

from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

from telegram import Bot, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from pose import analyze_video, to_markdown

from . import config
from .groups import send_to_group
from .llm import coach_reply
from .profiles import (
    apply_updates,
    ensure_first_name,
    is_onboarded,
    log_audit,
    profile_exists,
    read_profile,
)
from .prompt import build_system_blocks, build_user_message
from .schemas import CoachResponse

log = logging.getLogger("squat-father")


async def _maybe_dispatch_group_share(
    chat_id: int,
    response: CoachResponse,
    bot: Bot,
) -> None:
    """Per DC-19: dispatch any group_share_action the coach emitted this turn.

    Offer turns log an OFFER event only — no group post. Post turns with
    user_consent='YES' + non-empty group_post_text send to GROUP_CHAT_ID
    (in coach-as-crew-leader register per RP-06). NO consent + missing-text
    cases log a skip event. Send failures soft-fail by appending a note to
    response.reply so the DM user knows the share didn't go through; the
    DM coaching reply itself is unaffected.

    profile.group_share_history append is coach-emitted via profile_updates
    (DC-22 — single write surface). This helper does NOT touch profile.md
    state directly; it owns the Telegram side-effect + the audit trail only.
    """
    gsa = response.group_share_action
    if not gsa:
        return

    if gsa.intent == "offer":
        log_audit(chat_id, f"GROUP_SHARE_OFFER post_id={gsa.post_id}")
        return

    if gsa.user_consent != "YES":
        log_audit(
            chat_id,
            f"GROUP_SHARE_SKIP post_id={gsa.post_id} consent={gsa.user_consent!r}",
        )
        return

    if not gsa.group_post_text.strip():
        log_audit(chat_id, f"GROUP_SHARE_SKIP_NO_TEXT post_id={gsa.post_id}")
        return

    try:
        msg_id = await send_to_group(bot, gsa.group_post_text)
    except Exception as exc:
        log_audit(chat_id, f"GROUP_SHARE_ERR post_id={gsa.post_id} err={exc!r}")
        response.reply += (
            "\n\n(Couldn't reach the group chat just now — your share didn't "
            "go through. Try again next session.)"
        )
        return

    if msg_id is None:
        log_audit(chat_id, f"GROUP_SHARE_NOOP_UNCONFIGURED post_id={gsa.post_id}")
    else:
        log_audit(
            chat_id,
            f"GROUP_SHARE_POSTED post_id={gsa.post_id} group_msg_id={msg_id}",
        )


async def _dispatch_text(chat_id: int, user_text: str, bot: Bot) -> str:
    log_audit(chat_id, f"text_in len={len(user_text)} onboarded={is_onboarded(chat_id)}")
    system_blocks = build_system_blocks()
    user_message = build_user_message(chat_id, user_text, pose_markdown=None)
    response = await coach_reply(system_blocks, user_message)
    if response.reasoning_trace:
        trace = response.reasoning_trace.replace("\n", " ").strip()
        log_audit(chat_id, f"REASONING {trace}")
    if response.profile_updates:
        summaries = apply_updates(chat_id, response.profile_updates)
        log_audit(chat_id, f"applied_updates n={len(summaries)}")
    await _maybe_dispatch_group_share(chat_id, response, bot)
    log_audit(chat_id, f"text_out len={len(response.reply)}")
    return response.reply


async def _dispatch_video(
    chat_id: int, video_path: Path, caption: str, bot: Bot
) -> str:
    log_audit(chat_id, f"video_in path={video_path.name} caption_len={len(caption)}")

    envelope = await asyncio.to_thread(analyze_video, video_path)
    pose_md = to_markdown(envelope)
    log_audit(chat_id, f"pose_extracted reps={len(envelope.reps)}")

    system_blocks = build_system_blocks()
    user_message = build_user_message(chat_id, caption, pose_markdown=pose_md)
    response = await coach_reply(system_blocks, user_message)
    if response.reasoning_trace:
        trace = response.reasoning_trace.replace("\n", " ").strip()
        log_audit(chat_id, f"REASONING {trace}")
    if response.profile_updates:
        summaries = apply_updates(chat_id, response.profile_updates)
        log_audit(chat_id, f"applied_updates n={len(summaries)}")
    await _maybe_dispatch_group_share(chat_id, response, bot)
    log_audit(chat_id, f"video_out len={len(response.reply)}")
    return response.reply


async def start_cmd(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    log_audit(chat_id, "cmd /start")
    msg = (
        "Hi. I'm a back-squat hypertrophy coach.\n\n"
        "Send me a video of your squat (side-on, full body in frame) and I'll "
        "take a look. Or just message me and we'll talk through your training."
    )
    if not profile_exists(chat_id):
        msg += "\n\n(I haven't onboarded you yet — that'll happen on your first real turn.)"
    await update.message.reply_text(msg)


async def profile_cmd(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    log_audit(chat_id, "cmd /profile")
    profile = read_profile(chat_id)
    if not profile:
        await update.message.reply_text("(no profile yet)")
    else:
        await update.message.reply_text(f"```\n{profile[:3500]}\n```", parse_mode="Markdown")


async def reset_cmd(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    log_audit(chat_id, "cmd /reset")
    p = config.PROFILES_DIR / f"{chat_id}.md"
    if p.exists():
        p.unlink()
        await update.message.reply_text("Profile cleared.")
    else:
        await update.message.reply_text("(no profile to clear)")


async def text_handler(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    ensure_first_name(chat_id, update.effective_user.first_name)
    user_message = update.message.text or ""
    await update.message.chat.send_action("typing")
    reply = await _dispatch_text(chat_id, user_message, update.get_bot())
    await update.message.reply_text(reply)


async def video_handler(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    ensure_first_name(chat_id, update.effective_user.first_name)
    caption = update.message.caption or ""

    video = update.message.video or update.message.document
    if video is None:
        await update.message.reply_text("Hmm, I couldn't find a video on that message.")
        return

    # DC-31 resolution floor — pre-download gate using Telegram-provided metadata.
    # cv2 fallback below catches Document-type uploads that lack width/height.
    video_w = getattr(video, "width", 0) or 0
    video_h = getattr(video, "height", 0) or 0
    if video_w and video_h and min(video_w, video_h) < 480:
        log_audit(chat_id, f"video_rejected_low_res {video_w}x{video_h}")
        await update.message.reply_text(
            f"Resolution too low to analyse reliably ({video_w}×{video_h}). "
            f"Can you re-shoot at 720p or higher? I need at least 480p on the short "
            f"edge to read your form cleanly."
        )
        return

    await update.message.chat.send_action("typing")
    await update.message.reply_text("Got it — taking a look, one moment.")

    try:
        file = await video.get_file()
    except Exception as exc:
        log_audit(chat_id, f"video_download_err {exc!r}")
        await update.message.reply_text(
            "I couldn't download that video. Telegram bots are capped at 20MB — "
            "if the clip is bigger, re-shoot at 720p or trim it shorter."
        )
        return

    with tempfile.NamedTemporaryFile(
        suffix=".mp4", dir=config.TEMP_DIR, delete=False
    ) as tmp:
        tmp_path = Path(tmp.name)
    try:
        await file.download_to_drive(custom_path=tmp_path)

        # DC-31 resolution floor — cv2 fallback for Document-type uploads
        # missing Telegram width/height metadata. Cheap (~50ms) vs the pose
        # pipeline cost we'd otherwise burn on a sub-480p clip.
        import cv2
        cap = cv2.VideoCapture(str(tmp_path))
        cap_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        cap_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        if cap_w and cap_h and min(cap_w, cap_h) < 480:
            log_audit(chat_id, f"video_rejected_low_res_cv2 {cap_w}x{cap_h}")
            await update.message.reply_text(
                f"Resolution too low to analyse reliably ({cap_w}×{cap_h}). "
                f"Can you re-shoot at 720p or higher? I need at least 480p on "
                f"the short edge to read your form cleanly."
            )
            return

        reply = await _dispatch_video(chat_id, tmp_path, caption, update.get_bot())
        await update.message.reply_text(reply)
    except Exception as exc:
        log.exception("video handling failed")
        log_audit(chat_id, f"video_err {exc!r}")
        await update.message.reply_text(
            f"Something broke while analysing that video: {exc!r}"
        )
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass


def build_app() -> Application:
    token = config.require("TELEGRAM_BOT_TOKEN", config.TELEGRAM_BOT_TOKEN)
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, video_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    return app


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    app = build_app()

    if config.use_webhook():
        token = config.TELEGRAM_BOT_TOKEN
        url_path = token
        webhook_url = f"{config.WEBHOOK_URL.rstrip('/')}/{url_path}"
        log.info("starting webhook listen=0.0.0.0:%d url=%s", config.WEBHOOK_PORT, webhook_url)
        app.run_webhook(
            listen="0.0.0.0",
            port=config.WEBHOOK_PORT,
            url_path=url_path,
            webhook_url=webhook_url,
        )
    else:
        log.info("starting long-poll (WEBHOOK_URL unset)")
        app.run_polling()


if __name__ == "__main__":
    main()
