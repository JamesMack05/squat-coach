# bot/ — Telegram bot wrapper

Receives user video uploads, dispatches to `pose/` pipeline, builds system prompt from `coach/` folder + per-user `profile.md` (DC-21), calls Claude, replies. DC-22 read-before-write enforced on all profile mutations.

## Files

- `config.py` — env loading (.env), paths, runtime config (model, port, group_chat_id)
- `profiles.py` — per-user `profiles/<chat_id>.md` storage + audit log surface (DC-22 read-before-write)
- `schemas.py` — typed `CoachResponse` + `ProfileUpdate` (set vs append fields) for structured outputs
- `prompt.py` — DC-21 system prompt stitcher (identity + rules + reference + examples), single `cache_control` breakpoint on last system block per claude-api skill guidance
- `llm.py` — `AsyncAnthropic` call via `messages.parse` returning typed `CoachResponse`; adaptive thinking + effort=high; refusal + parse-failure fallbacks
- `groups.py` — DC-19 group-share send helper (Telegram group surface)
- `main.py` — Telegram entry point (handlers + webhook/long-poll switch)

## Run (long-poll — recommended for dev; no tunnel needed)

```
cp .env.example .env
# fill in TELEGRAM_BOT_TOKEN + ANTHROPIC_API_KEY; leave WEBHOOK_URL blank
python -m bot.main
```

Bot polls Telegram for updates. Log line `starting long-poll (WEBHOOK_URL unset)` confirms.

## Run (webhook via cloudflared — production-shape)

Closer to how this would deploy. In one terminal:
```
cloudflared tunnel --url http://localhost:8443
```

Copy the `https://<random>.trycloudflare.com` URL into `.env` as `WEBHOOK_URL`, then in another terminal:
```
python -m bot.main
```

The bot listens on `0.0.0.0:8443`; cloudflared forwards Telegram's webhook pushes to the local port.

## Commands (debug)

- `/start` — welcome message
- `/profile` — print current profile.md
- `/reset` — clear profile (for re-onboarding tests)

## Group surface (DC-19)

Group-share is default-private + per-post explicit opt-in. No remembered preference. Vulnerable moments stay DM until user actively chooses to share.

## Two-surface single voice (RP-06)

Same coach voice in DM (coach-as-confidant) and group (coach-as-crew-leader). Voice spec from `coach/identity.md` + voice-mode register switches in `coach/rules.md`.

## DC-22 observability (walker surface)

Every read/write/decision event appends to `audit/<chat_id>.log` with a timestamp. Walker reads this file alongside `profiles/<chat_id>.md` to verify read-before-write fired on every mutation, and to see the bot's decision trace.
