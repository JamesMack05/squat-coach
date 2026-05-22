"""Environment + paths. Single source of truth for runtime config."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").strip()
WEBHOOK_PORT = int(os.environ.get("WEBHOOK_PORT", "8443"))

# DC-19 group surface — Telegram group chat_id (negative integer for groups).
# When unset (0), bot runs DM-only and group-share actions no-op silently.
GROUP_CHAT_ID = int(os.environ.get("GROUP_CHAT_ID", "0").strip() or 0)

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-7").strip()
ANTHROPIC_EFFORT = os.environ.get("ANTHROPIC_EFFORT", "high").strip()
ANTHROPIC_MAX_TOKENS = int(os.environ.get("ANTHROPIC_MAX_TOKENS", "4096"))

COACH_DIR = REPO_ROOT / "coach"
REFERENCE_DIR = COACH_DIR / "reference"
PROFILES_DIR = REPO_ROOT / "profiles"
TEMP_DIR = REPO_ROOT / "temp"
AUDIT_DIR = REPO_ROOT / "audit"

for d in (PROFILES_DIR, TEMP_DIR, AUDIT_DIR):
    d.mkdir(exist_ok=True)


def use_webhook() -> bool:
    return bool(WEBHOOK_URL)


def require(name: str, value: str) -> str:
    if not value:
        raise RuntimeError(
            f"{name} not set. Copy .env.example to .env and fill it in."
        )
    return value
