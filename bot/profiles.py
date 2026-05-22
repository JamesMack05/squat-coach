"""Per-user profile.md storage + DC-22 audit log surface.

Format: profile.md is a JSON document keyed by field name. Set fields (per
profile-template.md schema) are simple values; append-only fields
(drill_ledger, symptom_reports, group_share_history) are arrays.

The coach reads the rendered profile (formatted markdown view) at the start
of every turn; the bot writes structured updates via apply_updates() based
on the model's profile_updates output. Every write appends an audit-log entry
to audit/<chat_id>.log (DC-22 walker observability — load-bearing for several
eval trajectories).
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

from .config import AUDIT_DIR, PROFILES_DIR
from .schemas import APPEND_FIELDS, SET_FIELDS, ProfileUpdate


def _profile_path(chat_id: int) -> Path:
    return PROFILES_DIR / f"{chat_id}.md"


def _audit_path(chat_id: int) -> Path:
    return AUDIT_DIR / f"{chat_id}.log"


def _empty_profile() -> dict[str, Any]:
    profile: dict[str, Any] = {f: None for f in SET_FIELDS}
    for f in APPEND_FIELDS:
        profile[f] = []
    return profile


def _load_struct(chat_id: int) -> dict[str, Any]:
    p = _profile_path(chat_id)
    if not p.exists():
        return _empty_profile()
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _empty_profile()


def _save_struct(chat_id: int, profile: dict[str, Any]) -> None:
    p = _profile_path(chat_id)
    p.write_text(json.dumps(profile, indent=2), encoding="utf-8")


def read_profile(chat_id: int) -> str:
    """Return profile rendered as JSON text for prompt injection.

    The coach reads this in the user message's <user_profile> block. JSON is
    cleaner for the model to parse field-by-field than markdown tables, and
    keeps round-trip consistency with the apply_updates() write path.
    """
    if not _profile_path(chat_id).exists():
        return ""
    return _profile_path(chat_id).read_text(encoding="utf-8")


def profile_exists(chat_id: int) -> bool:
    return _profile_path(chat_id).exists()


def is_onboarded(chat_id: int) -> bool:
    """Onboarding complete = goals + experience_level both populated."""
    profile = _load_struct(chat_id)
    return bool(profile.get("goals")) and bool(profile.get("experience_level"))


def apply_updates(chat_id: int, updates: list[ProfileUpdate]) -> list[str]:
    """Apply each ProfileUpdate to profile.md atomically; return summaries.

    DC-22: every mutation appends an audit-log entry with the model's stated
    reason. Returns one summary string per applied update (for the bot log
    + walker observability). Invalid updates (unknown field, append on set
    field, etc.) are skipped with an "invalid:" prefix.
    """
    if not updates:
        return []

    profile = _load_struct(chat_id)
    summaries: list[str] = []
    stamp = _dt.datetime.now().isoformat(timespec="seconds")

    for u in updates:
        if u.field not in SET_FIELDS and u.field not in APPEND_FIELDS:
            summary = f"invalid: unknown field '{u.field}'"
            _audit(chat_id, f"WRITE_REJECTED {summary} reason='{u.reason}'")
            summaries.append(summary)
            continue

        if u.operation == "set":
            if u.field not in SET_FIELDS:
                summary = f"invalid: cannot 'set' on append-only field '{u.field}'"
                _audit(chat_id, f"WRITE_REJECTED {summary}")
                summaries.append(summary)
                continue
            prior = profile.get(u.field)
            profile[u.field] = _coerce_value(u.field, u.value)
            summary = f"set {u.field}: {prior!r} -> {profile[u.field]!r}"

        elif u.operation == "append":
            if u.field not in APPEND_FIELDS:
                summary = f"invalid: cannot 'append' on set field '{u.field}'"
                _audit(chat_id, f"WRITE_REJECTED {summary}")
                summaries.append(summary)
                continue
            entry = _parse_append_value(u.value, stamp)
            if not isinstance(profile.get(u.field), list):
                profile[u.field] = []
            profile[u.field].append(entry)
            summary = f"append {u.field}: {entry!r}"

        else:
            summary = f"invalid: unknown operation '{u.operation}'"
            _audit(chat_id, f"WRITE_REJECTED {summary}")
            summaries.append(summary)
            continue

        _audit(chat_id, f"WRITE {summary} reason='{u.reason}'")
        summaries.append(summary)

    _save_struct(chat_id, profile)
    return summaries


def ensure_first_name(chat_id: int, name: str | None) -> None:
    """Capture Telegram first_name on first contact. Idempotent — first wins.

    Telegram-derived, system-managed (not user-editable via DC-22). Called
    from main.py handlers before any coach dispatch. Once set, never
    overwritten by this path — the field is a one-time capture, not a
    state mutation.
    """
    if not name:
        return
    profile = _load_struct(chat_id)
    if profile.get("user_first_name"):
        return
    profile["user_first_name"] = name
    _save_struct(chat_id, profile)
    _audit(chat_id, f"SYSTEM set user_first_name='{name}' (from Telegram)")


def log_audit(chat_id: int, event: str) -> None:
    """Append a non-write event (read, decision, refusal) to the audit log."""
    _audit(chat_id, event)


def _audit(chat_id: int, event: str) -> None:
    stamp = _dt.datetime.now().isoformat(timespec="seconds")
    _audit_path(chat_id).open("a", encoding="utf-8").write(f"[{stamp}] {event}\n")


def _coerce_value(field: str, raw: str) -> Any:
    """Best-effort coerce string -> typed value matching profile-template schema."""
    raw = raw.strip()
    if raw in ("null", "None", ""):
        return None
    # Booleans
    if field == "heel_elevation_access":
        return raw.lower() in ("true", "yes", "y", "1")
    # Ints
    if field in ("sessions_per_week", "squat_frequency_per_week"):
        try:
            return int(raw)
        except ValueError:
            return raw
    # years_lifting: int | range string | "<1"
    if field == "years_lifting":
        try:
            return int(raw)
        except ValueError:
            return raw
    # Everything else stays as the string the model produced
    return raw


def _parse_append_value(raw: str, default_timestamp: str) -> dict[str, Any]:
    """Append-only entries are JSON objects. Fall back to a wrapper if model
    didn't structure it (defensive — bot still records the attempt)."""
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            parsed.setdefault("timestamp", default_timestamp)
            return parsed
    except json.JSONDecodeError:
        pass
    return {"timestamp": default_timestamp, "raw": raw}
