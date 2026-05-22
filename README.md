# squat-coach

[![Watch the walkthrough — 4:26 — 5-axis differentiator pass (V1 setup + V2 working set with bot tracking + V3 post-set analysis + V4 ICM addendum)](https://img.youtube.com/vi/qmczFRvXcRQ/maxresdefault.jpg)](https://youtu.be/qmczFRvXcRQ)

Telegram-deployed AI coach for back-squat-for-hypertrophy. Comp 5 submission (Cliefnotes; deadline Sun 2026-05-24 12:00 EST). Click the thumbnail above for the 5-axis differentiator walkthrough — start there.

## The clever part is structural

The `coach/` folder IS the ICM specialist (Jake's Information / Context / Memory framework). Telegram is one I/O layer wrapped around it. The same coach folder drops directly into a Claude Project today (zero modifications) or pairs with any other I/O surface — web, Discord, SMS, CLI. Architecture is not bound to Telegram: coupling is concentrated in two files (`bot/main.py` + `bot/groups.py`, both importing `python-telegram-bot`); everything else is I/O-agnostic.

Specialisation is deliberate. Not "fitness coach generally" — back squat, hypertrophy, RIR 1-3 baseline, 5-30 rep envelope, mesocycle awareness. Narrowing buys differentiation depth: rep-band coaching, fatigue-degraded rep analysis, drill prescription, injury-state modulation.

## Five differentiators, ordered by visibility

1. **Telegram deployment surface (DC-12).** Most submissions ship as Claude Projects. Telegram demonstrates the bot's portability AND solves the "how does a real user actually access it?" question. Demo subject in the YouTube cut.
2. **Onboarding-as-coaching (DC-07).** Onboarding is a coach-led conversation, not a setup wizard. Structurally enforces "no coaching advice before onboarding complete" via `rules.md`. The first 6 questions ARE the coach's first turn with the user.
3. **Narrated internal state (DC-09).** Bot reasoning surfaces through `audit/<chat_id>.log` — Claude's REASONING trace on every turn. Visible-engineering observability surface; debuggable in <5min during testing.
4. **Hypertrophy specialisation (DC-11).** Narrow the domain to win on depth. RIR / RPE / mesocycle / autoreg / drop-set vocabulary natural; `rep_band_preference` field load-bearing in coaching prescriptions.
5. **Cross-domain primitives.** Folder methodology (DC-26 strict file-class separation) is the agent-architecture primitive; pose-pipeline architecture (DC-29..36) is the video-analysis primitive. Both designed to lift downstream into other engagements unchanged.

## Architecture invariants

Three load-bearing structural properties. None are "if Claude remembers" defaults — all three are enforced by file layout and code.

**P1 — Coach folder = ICM specialist; portable across I/O surfaces.** `coach/` has zero dependencies on Telegram or the bot infrastructure. The folder is consumed by Claude as system-prompt content (assembled by `bot/prompt.py`). The Telegram coupling is concentrated in two files that import `python-telegram-bot`: `bot/main.py` (entry point + handlers) and `bot/groups.py` (DC-19 group-share helper). Everything else — `coach/`, `pose/`, `bot/llm.py`, `bot/profiles.py`, `bot/schemas.py`, `bot/prompt.py` — is I/O-agnostic at the code level (env var names in `bot/config.py` and one line of the system prompt in `bot/prompt.py` are surface-level renames if porting to Discord, web, SMS, etc.). The coach folder also drops directly into a Claude Project today as Project Knowledge — no code at all.

**P2 — Constitutional spine: `rules.md` is canonical for behaviour (DC-20).** `identity.md`, `examples.md`, `reference/`, `profile-template.md` reference rules by RP-NN name; they do NOT restate behaviour. Single source of truth at folder scope. A behavioural change is a one-file edit; downstream coherence inherits by construction.

**P3 — Read-before-write announce-then-confirm on profile mutations (DC-22).** Every `profile.md` mutation goes through:

1. Bot reads current profile state.
2. Claude announces the proposed change in `reply` (e.g. *"I'm setting your rep band to 6-8 based on what you said — confirm?"*).
3. User confirms in the next turn.
4. Bot writes via `apply_updates()`.

Critical surfaces (`coaching_mode` transitions, `injury_notes` updates, `symptom_reports` appends) are catastrophically unsafe under silent write — the discipline is structurally enforced via the announce-then-write split. Walker observability lives in `audit/<chat_id>.log`.

## Code layout

```
~/dev/squat-coach/
├── coach/                       ← ICM specialist (folder methodology)
│   ├── identity.md              ← role + voice anchor + structural moves
│   ├── rules.md                 ← canonical behaviour spec (RP-01..09 + DC-22 read-before-write + onboarding + injury modulation + DC-19 group surface)
│   ├── examples.md              ← worked comparative pairs (10 examples covering RP-01..07)
│   ├── profile-template.md      ← per-user state schema (stamped at onboarding)
│   └── reference/               ← canonical content (drill library, hypertrophy ops, narrated-rep prose, progression protocol)
│       ├── drill-library.md
│       ├── hypertrophy-ops.md
│       ├── narrated-rep.md
│       └── progression-protocol.md
├── bot/                         ← Telegram I/O layer
│   ├── main.py                  ← Telegram bot handlers (text + video + commands)
│   ├── llm.py                   ← Claude API call (Opus 4.7 default; structured outputs via messages.parse)
│   ├── prompt.py                ← system-prompt assembly with single cache breakpoint
│   ├── profiles.py              ← profile.md read + DC-22 announce-then-write apply_updates()
│   ├── schemas.py               ← typed CoachResponse + ProfileUpdate (set vs append fields)
│   ├── groups.py                ← group-chat post helper (DC-19 wiring)
│   └── config.py                ← env-loaded config (BOT_TOKEN, ANTHROPIC_API_KEY, paths)
├── pose/                        ← MediaPipe pose-extraction pipeline
│   ├── extract.py               ← Tasks API runner — per-frame landmarks + visibility + joint angles
│   ├── segment.py               ← hip-Y peak-detection rep segmentation (DC-34)
│   ├── aggregate.py             ← per-rep aggregates + fatigue signature (RP-07 implementation)
│   ├── output.py                ← JSON envelope (full) + markdown (Claude prompt) — dual output (DC-35)
│   └── __init__.py              ← public API: analyze_video(path) → ClipEnvelope (DC-36)
├── models/                      ← MediaPipe pose model files (downloaded by setup.py; NOT in git)
├── profiles/                    ← per-chat-id profile.md JSON state (NOT in git — PII)
├── audit/                       ← per-chat-id audit logs (DC-22 walker observability — NOT in git)
├── setup.py                     ← fetches MediaPipe pose model
└── README.md                    ← this file
```

## Design choices — the load-bearing picks

### Folder methodology (Jake's ICM pattern, adapted)

- **DC-20 — Constitutional spine.** `rules.md` is the single source of truth for behaviour (see P2 above).
- **DC-21 — Parameterisation discipline.** `identity.md` + `drill-library.md` + `reference/` built as pluggable parameters that the system-prompt template consumes — NOT hard-coded prose. Unlocks future re-skinning at near-zero marginal cost.
- **DC-26 — Strict file-class separation.** `rules.md` = behaviour / `reference/` = content / `identity.md` = configuration / `profile.md` = state. Hard rule, no cross-contamination.
- **DC-27 — RP-NN naming convention.** Every coaching behavioural primitive has a stable RP-NN identifier with named clause heading in `rules.md`. `examples.md` cites by RP name; does not restate.
- **DC-28 — Drill library as tagged lookup.** `reference/drill-library.md` is a structured table (drill name + faults addressed (tagged) + hypertrophy applicability tag + prescription text + contraindications). Coaching logic references "prescribe one drill tagged with detected fault" — does not enumerate inline.

### Coaching behavioural primitives (RP-01..RP-09)

- **RP-01 — Symptoms-not-diagnosis.** Acknowledge symptoms; never accept user's hypothesised cause without independent verification. New/escalating pain → recommend medical/physio consult.
- **RP-02 — Progression gating.** Escalate load on demonstrated proficiency (form-history + pose data), not user request. Layers: double-progression → autoreg → mesocycle. Form gate overrides.
- **RP-03 — Active observation.** Where the user can self-verify, give them a self-check step (*"screenshot deepest position, what do you see?"*) rather than asserting from pose alone.
- **RP-04 — Reactive accountability.** Track drill assignments in `drill_ledger`. On user return with an un-confirmed drill: ask BEFORE anything else.
- **RP-05 — Confidence-graded contradiction.** High-confidence (near-side vis ≥0.7 + consistent signal) → direct contradiction, zero hedging. Medium (noisy or single-rep) → name two hypotheses + propose concrete next test. Low (vis <0.7 or fragmentary) → honesty primitive + concrete actionable re-shoot instruction.
- **RP-06 — Register modes.** `empathy_first` vs `push_hard` — user picks at onboarding, can change mid-session via explicit request. Same coach identity across modes; intensity differs only.
- **RP-07 — Multi-rep fatigue-degradation analysis.** When pose data shows velocity loss + depth degradation + ROM change across reps: name fatigue-degraded reps SPECIFICALLY (not average rep) and prescribe a one-cue targeting the fatigue pattern. Composes DC-03 (one-cue) + DC-09 (narrated state) + DC-18 (reactive accountability).
- **RP-08 — Injury-state coaching modulation.** `coaching_mode` enum (`healthy` / `injury_managing` / `injury_recovery` / `return_to_training` / `unknown`) modulates RIR targets, depth floor, tempo, progression layer, and drill pool filter. Catastrophic-severity-dominant rules; silent mode flip would be structurally invisible.
- **RP-09 — Symptom capture.** 14d/5-session memory window for pattern detection (first / repeated_same_location / escalating). Fires across ALL coaching modes — even `healthy` (a symptom report IS the trigger for the mode-transition prompt).

### Pose pipeline (DC-29..DC-36)

- **DC-29 — Dynamic near-side per rep.** Per-rep mean visibility on each side. Higher-vis side = near-side for that rep. Per-clip modal across reps + `tripod_nudge_detected: bool` when reps disagree. Hard rule: do NOT hard-code L or R.
- **DC-30 — Far-side visibility threshold = 0.7.** Below 0.7 mean visibility, far-side joint angles flagged "insufficient data" + excluded from symmetry analysis.
- **DC-31 — Resolution floor = 480p.** Sub-480p clips rejected at ingestion BEFORE pose pipeline runs. Re-shoot message returned.
- **DC-32 — CPU runtime budget ~0.43× real-time.** Pose extraction ~13s on a 30s clip; total user-perceived response ~20-30s. GPU offload deferred.
- **DC-34 — Rep-segmentation pre-filter.** Hip-Y peak-detection groups frames into rep-ids. Non-rep frames (rack-out, between-rep stand, post-workout collapse) excluded from rep-level aggregation.
- **DC-35 — Dual output.** JSON envelope (full per-frame data) + markdown (per-rep aggregates only) — Claude's prompt sees the markdown, not the per-frame dump.
- **DC-36 — Public API.** `analyze_video(path) → ClipEnvelope`. One entry point; coach layer consumes via `to_markdown()` + `to_json()`.

### Prompt caching

System prompt is user-invariant (`identity.md` + `rules.md` + `reference/` + `examples.md`). Per-user state (`profile.md`) + per-turn data (pose markdown) live in the user message. Single `cache_control` breakpoint on the last system block. Cache hits across every user + every turn.

Model: Opus 4.7 default; override via `ANTHROPIC_MODEL` env to Sonnet 4.6 for cost flip. Adaptive thinking, effort=high.

## Data flow

```
User                       Bot                          Claude                Pose pipeline
 │                          │                              │                       │
 │ /start                   │                              │                       │
 ├─────────────────────────►│                              │                       │
 │                          │ ensure_first_name()          │                       │
 │                          │ profile is empty             │                       │
 │                          │ build prompt (cached system  │                       │
 │                          │  + user_profile + message)   │                       │
 │                          ├─────────────────────────────►│                       │
 │                          │                              │ reply: onboarding Q1  │
 │                          │                              │ profile_updates: []   │
 │                          │◄─────────────────────────────┤                       │
 │ "Coach Q1 reply"         │ apply_updates() noop         │                       │
 │◄─────────────────────────┤                              │                       │
 │                          │                              │                       │
 │ ...onboarding loop (Q2-Q6 per DC-37, each turn DC-22 announce-then-confirm)...   │
 │                          │                              │                       │
 │ [uploads squat video]    │                              │                       │
 ├─────────────────────────►│                              │                       │
 │                          │ ack: "~20-30s for 30s clip"  │                       │
 │◄─────────────────────────┤                              │                       │
 │                          │ analyze_video(path)          │                       │
 │                          ├──────────────────────────────┼──────────────────────►│
 │                          │                              │  ┌─────────────────┐  │
 │                          │                              │  │ extract → segment│  │
 │                          │                              │  │ → aggregate     │  │
 │                          │                              │  │ → output (JSON +│  │
 │                          │                              │  │   markdown)     │  │
 │                          │                              │  └─────────────────┘  │
 │                          │◄─────────────────────────────┼───────────────────────┤
 │                          │ build prompt (cached system  │                       │
 │                          │  + user_profile + pose       │                       │
 │                          │  markdown + user message)    │                       │
 │                          ├─────────────────────────────►│                       │
 │                          │                              │ reply: coach analysis │
 │                          │                              │ profile_updates: e.g. │
 │                          │                              │  drill_ledger append  │
 │                          │◄─────────────────────────────┤                       │
 │                          │ apply_updates() writes       │                       │
 │                          │ profile.md + audit log       │                       │
 │ "Coach reply"            │                              │                       │
 │◄─────────────────────────┤                              │                       │
```

**Subsequent sessions:** `profile.md` persists across sessions. Claude reads it every turn. `drill_ledger` accumulates assigned drills + user-confirmed completions. RP-04 (reactive accountability) fires on session re-open: if the drill assigned last session is uncompleted, the bot asks about it BEFORE accepting a new video.

**Group surface (DC-19):** every group-share moment fires a FRESH per-post offer; never references prior consent ("you said yes last time"); never skips the gate. `group_share_history` is an event log for audit and walker observability, NOT a permission cache. Vulnerable moments (injury reports / fears / register-mode pick) structurally suppress the group-share offer.

## Setup

End-to-end walkthrough — getting from clone to a working bot in Telegram. Prerequisites: Python 3.13, `ffmpeg` on PATH, a Telegram account, an Anthropic API key.

### 1. Get a Telegram bot token

In the Telegram app (mobile or desktop), search for **@BotFather** and start a chat. Send `/newbot`, give the bot a display name and a username (must end in `bot`, e.g. `my_squat_coach_bot`). BotFather replies with an HTTP API token of the shape `1234567890:AAH...` — copy it. This is your `TELEGRAM_BOT_TOKEN`.

### 2. Get an Anthropic API key

Sign in at https://console.anthropic.com → API keys → Create key. Copy the `sk-ant-...` string. This is your `ANTHROPIC_API_KEY`.

### 3. Install and set up the repo

```powershell
git clone <repo-url> ~/dev/squat-coach
cd ~/dev/squat-coach
python -m venv .venv
.\.venv\Scripts\Activate.ps1     # Windows; source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
python setup.py                  # downloads MediaPipe pose model (~9MB) into models/
```

Expected output — the `Successfully installed` line at the end of `pip install`, then the `python setup.py` confirmation:

```
$ pip install -r requirements.txt
Collecting mediapipe==0.10.35 (from -r requirements.txt (line 2))
Collecting opencv-python==4.13.0.92 (from -r requirements.txt (line 3))
Collecting python-telegram-bot==21.6 (from python-telegram-bot[webhooks]==21.6->-r requirements.txt (line 6))
Collecting anthropic==0.103.1 (from -r requirements.txt (line 7))
Collecting python-dotenv==1.0.1 (from -r requirements.txt (line 8))
[... 37 packages total: 5 direct + 32 transitive deps; output abbreviated]
Successfully installed mediapipe-0.10.35 opencv-python-4.13.0.92 python-telegram-bot-21.6 anthropic-0.103.1 python-dotenv-1.0.1 [...]

$ python setup.py
Downloading https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task
  -> models/pose_landmarker_full.task
Downloaded 9,398,198 bytes.
```

### 4. Fill in `.env`

Create a `.env` file in the repo root with the two tokens from steps 1 and 2:

```
TELEGRAM_BOT_TOKEN=1234567890:AAH...
ANTHROPIC_API_KEY=sk-ant-...

# Optional — leave WEBHOOK_URL blank to use long-poll mode (recommended for dev)
WEBHOOK_URL=
WEBHOOK_PORT=8443                  # only used when WEBHOOK_URL is set
GROUP_CHAT_ID=                     # optional — Telegram group chat_id (negative integer) for DC-19 group surface

ANTHROPIC_MODEL=claude-opus-4-7    # optional; default Opus 4.7
```

### 5. Run the bot (two paths)

**Path A — long-poll (recommended for dev; no tunnel needed).** Leave `WEBHOOK_URL` blank in `.env` and run:

```powershell
python -m bot.main
```

Expected output — two log lines confirm the bot is up and Telegram is reachable:

```
$ python -m bot.main
2026-05-22 19:22:28,958 squat-coach INFO starting long-poll (WEBHOOK_URL unset)
2026-05-22 19:22:29,119 telegram.ext.Application INFO Application started
```

The bot is now polling Telegram for updates. Open Telegram, search for your bot's username, and send `/start` — the bot stamps `user_first_name` from your Telegram metadata and (if the profile is empty) initiates onboarding per DC-07.

**Path B — webhook via cloudflared (closer to production shape).** Install cloudflared first (Windows: `winget install cloudflare.cloudflared`; macOS: `brew install cloudflared`; Linux: see https://developers.cloudflare.com/cloudflared/install/), then:

```powershell
cloudflared tunnel --url http://localhost:8443   # in one shell — match WEBHOOK_PORT in .env
```

cloudflared prints a `https://<random>.trycloudflare.com` URL. Paste that into `.env` as `WEBHOOK_URL=https://<random>.trycloudflare.com`, then in another shell:

```powershell
python -m bot.main
```

You should see the log line `starting webhook listen=0.0.0.0:8443 url=<your-tunnel-url>/<token>`. Telegram now pushes updates to your tunnel and cloudflared forwards them to the local bot. Test the same way — `/start` in Telegram.

## Honest gaps

Per Comp 5 ship-discipline — surface what is NOT shipped or NOT verified, don't bury it.

1. **Notification subsystem dropped between brainstorm and synthesis.** Pre-plan flagged proactive check-ins (Claude Code Routines / ntfy.sh / Anthropic Telegram plugin) as *"the highest-leverage differentiator distinguishing a coach from a chatbot."* The synthesis pass dropped this silently without a decision-call. The bot is reactive-only — no between-session messages. This is a real product gap.
2. **Static-only verified rule fixes from Fri PM testing** (not behaviourally re-tested due to API credit exhaustion): DC-19 fears-fix (current-turn vs historical profile data distinction), DC-19 initiator-pattern + no-pre-validation clauses, DC-19 crew-leader tone + name-anchoring via `user_first_name` plumbing, RP-07 multi-phase interpretation sub-clause, `bot/main.py video_handler` "on CPU" string removal.
3. **Untested blocker-1 sub-scenarios.** Blocker 1 NO path, vulnerable-moment floor (in-turn fear expression suppressing share), Day-14 trap (fresh per-post offer; no prior-consent reference), register-pivot check (group post NOT in confidant register). Stage 5 kill-criterion judgment was these don't gate submission; calling them out anyway.
4. **Single-user calibration.** Multi-user architecture is supported via per-chat-id `profile.md`, but the Comp 5 demo runs against one fictitious profile only.
5. **GPU pose extraction deferred.** CPU runtime ~13s for a 30s clip; GPU offload is on the roadmap, not in Comp 5 ship.

## Wider ship surface

- **YouTube cut:** https://youtu.be/qmczFRvXcRQ — 5-axis differentiator walkthrough. V1 setup + bot concept → V2 working set with bot-tracking narration → V3 post-set analysis → V4 audio addendum on freeze-frame (ICM architecture clarification). Edited mid-session for honesty: V2 over-claim "neck movement" cut, V3 active-learning over-claim trimmed at 1:04 (verified against codebase — no tendency-detection mechanism in schema).
- **Compressed video for inline embed:** the video at the top of this README is the same cut. Plays inline on repo page load — primary visibility surface for skim-judges.

---

Built for [Cliefnotes Comp 5](https://www.skool.com/cliefnotes) by James Mackellar. Comp 4 honorable mention (Jake's YouTube playlist call-out) was the upstream signal that visible-engineering wins over invisible-correctness — this submission leans into that lesson.
