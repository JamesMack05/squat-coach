"""Structured-output schemas for coach responses.

The coach returns both a user-facing `reply` and a typed list of `profile_updates`
in a single API call. The bot applies the updates to profile.md and sends `reply`
to Telegram. DC-22 announce-then-confirm pattern lives in the coach's prose;
state mutation is what these schemas drive.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# Frontmatter (set) fields — per profile-template.md schema.
SET_FIELDS: set[str] = {
    "goals",
    "fears",
    "experience_level",
    "current_programme_name",
    "sessions_per_week",
    "squat_frequency_per_week",
    "years_lifting",
    "current_mesocycle_phase",
    "rep_band_preference",
    "equipment_notes",
    "heel_elevation_access",
    "injury_notes",
    "coaching_mode",
    "register_mode",
    "last_physio_consult_acknowledgement",
    "reverse_transition_prompt_last_offered",
    "user_first_name",
}

# Append-only log fields — per profile-template.md schema.
APPEND_FIELDS: set[str] = {
    "drill_ledger",
    "symptom_reports",
    "group_share_history",
}

ALL_FIELDS: set[str] = SET_FIELDS | APPEND_FIELDS


class ProfileUpdate(BaseModel):
    """One proposed mutation to profile.md.

    DC-22: every write is announced in `reply` and the reason for it captured
    here. Append-only fields (drill_ledger, symptom_reports, group_share_history)
    must use operation='append'; everything else uses 'set'.
    """

    field: str = Field(
        description=(
            "Which profile.md field to update. Set fields (frontmatter): "
            + ", ".join(sorted(SET_FIELDS))
            + ". Append-only log fields: "
            + ", ".join(sorted(APPEND_FIELDS))
        )
    )
    operation: Literal["set", "append"] = Field(
        description=(
            "'set' for frontmatter fields (replaces value); 'append' for "
            "drill_ledger, symptom_reports, group_share_history (adds an entry)."
        )
    )
    value: str = Field(
        description=(
            "The new value (for set) or the JSON-stringified entry to append "
            "(for append). Append entries are JSON objects per the "
            "profile-template.md schema."
        )
    )
    reason: str = Field(
        description=(
            "Short justification — what the user said or what pose data showed "
            "that triggered this update. Goes to the DC-22 audit log."
        )
    )


class GroupShareAction(BaseModel):
    """One group-share action emitted by the coach this turn (DC-19 + RP-06).

    The two-turn protocol — DC-19 is structurally a fresh per-post opt-in,
    never an autonomous decision:

      Turn N   — coach offers share in `reply` field (DM-side). Emit
                 `intent='offer'` here so the audit log records that an
                 offer fired. Bot does NOT post to group on offer turns.
      Turn N+1 — user has replied YES or NO in the meantime. Coach now
                 emits `intent='post'` with `user_consent='YES'` AND
                 `group_post_text` filled in crew-leader register; bot
                 sends to GROUP_CHAT_ID. On `user_consent='NO'`, bot
                 acknowledges + drops topic, does not post.

    DC-19 vulnerable-moment structural floor: NEVER emit this field on
    turns involving injury / diagnosis / fears / register-mode pick.
    Vulnerable conversations stay strictly DM-private.

    DC-19 Day-14 trap: every share fires a FRESH offer. NEVER reference
    prior consent. `profile.group_share_history` is an event log, not a
    permission cache.

    Composes with profile_updates: on `intent='post'` with YES consent,
    the coach MUST also emit a `group_share_history` append in
    profile_updates capturing the post_id + user_consent so DC-22
    audit-log discipline holds.
    """

    intent: Literal["offer", "post"] = Field(
        description=(
            "'offer' = coach is offering share in this turn's `reply` "
            "(no group post yet — bot logs the offer event only). "
            "'post' = user previously consented YES; coach is now "
            "shaping the group post in crew-leader register."
        )
    )
    post_id: str = Field(
        description=(
            "Stable id for this share event, reused across the offer "
            "and post turns + the group_share_history append. Format: "
            "short slug (e.g. 'aar-2026-05-21-clean-empty-bar')."
        )
    )
    group_post_text: str = Field(
        default="",
        description=(
            "What to send to the group when intent='post'. "
            "Coach-as-crew-leader register — third-person callout to "
            "the crew (e.g. 'Bill just had a real breakthrough on his "
            "unloaded squat — torso noticeably more upright than last "
            "week.'). Same coach identity as DM, different audience "
            "shape (RP-06). Empty string when intent='offer'."
        ),
    )
    user_consent: Literal["YES", "NO"] | None = Field(
        default=None,
        description=(
            "Set on the post turn (intent='post') to record the user's "
            "answer from the previous turn. Unset on offer turns. On "
            "NO: bot acknowledges + does not post. Do NOT pressure or "
            "re-prompt."
        ),
    )


class CoachResponse(BaseModel):
    """The coach's full output for one turn.

    `reply` is what gets sent to Telegram (must always include the DC-22
    announcement when profile_updates is non-empty, e.g. "I'm noting your
    rep band as 8-12. Sound right?").

    `profile_updates` is the typed list of state mutations to apply. Empty
    list = no state changes this turn.

    `reasoning_trace` is a 1-3 sentence summary of the key decision steps
    this turn, for walker observability (DC-22 audit + Phase D trajectory
    verification across T1, T3a/b/c, T5a/b, T6, T7, T-injury-2/3).

    `group_share_action` is optional — set ONLY when this turn involves
    a DC-19 group-share offer or post (per the rules.md § DC-19 trigger
    + vulnerable-moment floor). None on every other turn (default).
    """

    reply: str = Field(
        description=(
            "The message to send to the user. Always announce any "
            "profile_updates in this reply (DC-22 announce-then-confirm). "
            "Voice + register per identity.md and rules.md."
        )
    )
    profile_updates: list[ProfileUpdate] = Field(
        default_factory=list,
        description=(
            "Profile.md mutations to apply this turn. Empty list if no "
            "state changes."
        ),
    )
    reasoning_trace: str = Field(
        default="",
        description=(
            "Short structured summary of your key decision steps this turn "
            "— primarily state-checks and disambiguation steps that aren't "
            "visible in `reply`. 1-3 sentences. Examples: "
            "'Read profile.goals=hypertrophy; user proposed powerlifting "
            "switch; surfaced conflict per DC-22 semantic-detection.' / "
            "'Pose data: VL=22% with end_position_stable=true; fired RP-07 "
            "high-confidence regime; one-cue prescription per DC-03.' / "
            "'No state changes this turn; pure conversational reply.' "
            "Use this field for the *deliberation* — not a restatement of "
            "the reply. Mention rule names (RP-NN / DC-NN) when they "
            "fired. Empty string on turns with no deliberation worth "
            "noting. Goes to walker-only audit log, never to user."
        ),
    )
    group_share_action: GroupShareAction | None = Field(
        default=None,
        description=(
            "Optional — set when this turn involves a DC-19 group-share "
            "offer or post. None on every other turn. Strict structural "
            "floor: NEVER set on vulnerable-moment turns (injury / "
            "diagnosis / fears / register-mode pick). See "
            "GroupShareAction docstring + rules.md § DC-19 for the full "
            "trigger conditions."
        ),
    )
