"""Telegram group-surface sender — DC-19 + RP-06 cross-surface output.

Bot posts to a configured Telegram group chat when the user has consented
per DC-19 default-private discipline. Group surface is OUTPUT-only: we do
not process incoming group messages (group is a posting destination, not
a coaching surface — coaching happens in DM).

Activation: GROUP_CHAT_ID in .env. Unset → group features no-op silently
(bot runs DM-only). This keeps development unblocked without a test group
and lets ship-mode require it via config presence.
"""

from __future__ import annotations

import logging

from telegram import Bot

from . import config

log = logging.getLogger("squat-father.groups")


async def send_to_group(bot: Bot, text: str) -> int | None:
    """Send a coach message to the configured group chat.

    Returns the Telegram message_id on success — caller logs it to the
    audit log + the apply_updates() path appends to
    profile.group_share_history.

    Returns None if GROUP_CHAT_ID is unset (no group configured — DM-only
    mode; caller should audit-log a NOOP_UNCONFIGURED event).

    Raises on Telegram API error so the caller can audit-log + degrade
    gracefully (typically by appending a soft-fail note to the DM reply).
    """
    if not config.GROUP_CHAT_ID:
        log.warning("GROUP_CHAT_ID unset — group-share skipped")
        return None
    msg = await bot.send_message(chat_id=config.GROUP_CHAT_ID, text=text)
    return msg.message_id
