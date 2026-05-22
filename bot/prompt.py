"""Prompt builder -- DC-21 parameterised stitching with prompt caching.

System prompt is USER-INVARIANT (identity + rules + reference + examples) so the
cache hits across every user and every turn. Per-user state (profile.md) and
per-turn data (pose markdown) live in the user message, not in system.

Render order (Anthropic prefix-match cache invariant):
    tools (none here) -> system (stable, cached) -> messages (volatile)

Single cache_control breakpoint on the last system block (covers all preceding
system content). Per claude-api skill guidance.
"""

from __future__ import annotations

from .config import COACH_DIR, REFERENCE_DIR
from .profiles import read_profile


def _read(path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_system_blocks() -> list[dict]:
    """Return the system prompt as a list of text blocks, with cache_control on the last.

    Composes the four coach/ file classes (DC-26): identity (configuration),
    rules (behaviour, DC-20 Constitutional spine), reference/ (content,
    DC-11/RP-02/DC-28), examples (few-shot priming, DC-23 axis 3 surface).
    """
    identity = _read(COACH_DIR / "identity.md")
    rules = _read(COACH_DIR / "rules.md")
    examples = _read(COACH_DIR / "examples.md")

    reference_parts = []
    for name in (
        "hypertrophy-ops.md",
        "progression-protocol.md",
        "drill-library.md",
        "narrated-rep.md",
    ):
        text = _read(REFERENCE_DIR / name)
        if text:
            reference_parts.append(f"## {name}\n\n{text}")
    reference = "\n\n".join(reference_parts)

    framing = (
        "You are a back-squat hypertrophy coach delivered as a Telegram bot. "
        "Your behaviour is governed by the RP-NN clauses in `rules.md` "
        "(Constitutional spine — DC-20). Other coach/ files carry persona "
        "(`identity.md`), few-shot examples (`examples.md`), and reference "
        "content (`reference/`). Per-user state lives in `profile.md`, which "
        "you read fresh at the start of every turn via the live user profile "
        "block in the user message.\n\n"
        "Hard rules (load-bearing):\n"
        "- DC-22 read-before-write: never mutate user state silently. When a "
        "profile.md field changes (drill completion, coaching_mode transition, "
        "symptom report, onboarding answer), announce the change explicitly in "
        "your `reply` AND emit the corresponding entry in `profile_updates`. "
        "The bot will write the update to profile.md and append the reason to "
        "the audit log. If the user pushes back next turn, emit a corrective "
        "update. **VOICE:** announce in natural conversational coach-speak — "
        "NEVER expose schema field names (`equipment_notes`, `coaching_mode`, "
        "`rep_band_preference`, `register_mode`, etc.), machine values "
        "(`true`/`false`, `empathy_first`, `healthy`), or field=value syntax "
        "in the user-facing `reply`. The structured `profile_updates` field "
        "carries the schema form; `reply` is conversation. See rules.md § "
        "DC-22 § Voice for examples.\n"
        "- DC-07 onboarding refusal: if the user has not completed onboarding "
        "(profile shows null/empty for goals/experience_level), your first job "
        "is onboarding — do NOT give coaching advice yet. Run the 6-question "
        "sequence per rules.md § Onboarding refusal.\n"
        "- DC-19 default-private group-share: emit `group_share_action` "
        "ONLY when the rules.md § DC-19 trigger conditions hold (positive AAR "
        "+ progression evidence + non-vulnerable turn + no recent offer). "
        "STRUCTURAL FLOOR — never emit `group_share_action` on vulnerable "
        "turns (injury / diagnosis / fears / register-mode pick / active "
        "injury_managing or injury_recovery mode). Day-14 trap: every share "
        "is a fresh per-post offer; NEVER reference prior consent.\n"
        "- RP-01 symptoms-not-diagnosis: when a user reports pain/discomfort, "
        "acknowledge symptoms; never accept their hypothesised cause without "
        "independent verification.\n\n"
        "Your output is a structured JSON object per the CoachResponse "
        "schema: `reply` (the user-facing message), `profile_updates` (state "
        "mutations — empty list is fine; most turns), `reasoning_trace` "
        "(short deliberation summary for walker observability — empty string "
        "is fine), and `group_share_action` (DC-19 share offer / post — "
        "`null` on every turn except the gated cases above). Always announce "
        "profile changes in `reply` AND emit the corresponding "
        "`profile_updates` entry."
    )

    return [
        {"type": "text", "text": f"# Framing\n\n{framing}"},
        {"type": "text", "text": f"# Identity (configuration)\n\n{identity}"},
        {"type": "text", "text": f"# Rules (Constitutional spine)\n\n{rules}"},
        {"type": "text", "text": f"# Reference content\n\n{reference}"},
        {
            "type": "text",
            "text": f"# Examples (few-shot)\n\n{examples}",
            "cache_control": {"type": "ephemeral"},
        },
    ]


def build_user_message(
    chat_id: int,
    user_text: str,
    pose_markdown: str | None = None,
) -> str:
    """Format the per-turn user content: profile state + pose data + user text.

    Profile and pose data are wrapped in tagged blocks so the coach can address
    them by reference. Tags chosen to be unambiguous and grep-able in audit logs.
    """
    profile = read_profile(chat_id)
    profile_block = (
        f"<user_profile>\n{profile}\n</user_profile>"
        if profile
        else "<user_profile>(empty — user has not completed onboarding)</user_profile>"
    )

    parts = [profile_block]
    if pose_markdown:
        parts.append(f"<pose_data>\n{pose_markdown}\n</pose_data>")
    parts.append(f"<user_message>\n{user_text}\n</user_message>")

    return "\n\n".join(parts)
