---
file-class: state-template
locked-by: DC-26
populated-by: onboarding (DC-07)
written-by: DC-22 read-before-write (mechanism a)
---

# User profile (template)

Per-user state slot template. Stamped at onboarding to create the live `profile.md` (which is gitignored and never committed).

## State slots

The schema below is principle-locked; field types + defaults are stable.

### Onboarding-derived fields (DC-07 + DC-17 + DC-37)

| Field | Type | Source | Notes |
|---|---|---|---|
| `goals` | text | DC-07 onboarding | User's stated goal — free-text |
| `fears` | text | DC-07 onboarding | User's stated concerns — free-text |
| `experience_level` | enum + free-text | DC-17 open-ended Q | Bot parses level routing from free-text answer |
| `current_programme_name` | text \| null | DC-37 Q1 | e.g. "RP Hypertrophy", "5/3/1", "made-up split", null if none |
| `sessions_per_week` | int \| null | DC-37 Q1 | Parsed from free-text |
| `squat_frequency_per_week` | int \| null | DC-37 Q1 | When squat falls in the week |
| `years_lifting` | int \| range \| `"<1"` \| null | DC-37 Q1 | Parsed from free-text |
| `current_mesocycle_phase` | enum(MEV / MAV / MRV / deload / unknown) \| null | DC-37 Q1 | User-stated; bot does NOT autonomously transition |
| `rep_band_preference` | text \| null | DC-37 Q2 | Within 5-30 envelope (Pick 2). e.g. "8-12", "6-10", "12-15" |
| `equipment_notes` | text \| null | DC-37 Q3 | Free-text — bar type, safety bars, plates, etc |
| `heel_elevation_access` | bool \| null | DC-37 Q3 | Extracted from equipment_notes — gates Pick 4 heel-elevated prescription |
| `injury_notes` | text \| null | DC-37 Q4 (skippable) | Free-text + extracted location (controlled vocab via DC-39 extraction) |

### Coaching-mode + symptom state (DC-38 + DC-39 + RP-08 + RP-09)

| Field | Type | Source | Notes |
|---|---|---|---|
| `coaching_mode` | enum(healthy / injury_managing / injury_recovery / return_to_training / unknown) | DC-38 — derived from `injury_notes` at onboarding; null/empty → `healthy` | User-stated or user-confirmed transitions ONLY in both directions. Bot does NOT autonomously transition. Reverse transitions: bot prompts after 21d OR 8 sessions without symptoms; user must confirm; 14d/4-session cooldown if declined |
| `symptom_reports` | list of entries (append-only) | DC-39 — RP-09 capture | Each entry: `{timestamp, exercise, set_context, location_raw (verbatim), location_extracted (knee / back / hip / ankle / shoulder / other), intensity, when (during / post-set / post-session / next-day), user_words, pattern_flag (first / repeated_same_location / escalating)}`. Memory window for pattern detection: 14 days OR last 5 sessions, whichever is longer. Always fires across ALL coaching_modes (even healthy — symptom report IS the trigger for mode-transition prompt) |
| `last_physio_consult_acknowledgement` | timestamp \| null | DC-38 — re-surface gating | Tracks whether user has reported a physio consult; if null in `injury_managing` mode, generic recommendation re-surfaces periodically |
| `reverse_transition_prompt_last_offered` | timestamp \| null | DC-38 | Tracks cooldown — if user declined a reverse-transition prompt, no re-prompt for 14d/4 sessions |

### Drill state (RP-04 + DC-18)

| Field | Type | Source | Notes |
|---|---|---|---|
| `drill_ledger` | list of entries (append-only) | RP-04 — drill assignments + completion state | Each entry: `{timestamp, drill_name, prescribed_for_fault, user_confirmation_of_completion, follow-up_observation}` |

### Voice / register state (RP-06)

| Field | Type | Source | Notes |
|---|---|---|---|
| `register_mode` | enum(empathy_first / push_hard) | RP-06 onboarding pick | User-selectable at onboarding; can be changed mid-session via explicit user request |

### Group-share state (DC-19)

| Field | Type | Source | Notes |
|---|---|---|---|
| `group_share_history` | list of per-post opt-in events | DC-19 — never a remembered preference | Each entry: `{timestamp, post_id, user_consent (YES / NO)}`. No remembered "always share" preference — every post is a fresh decision |

## DC-22 read-before-write discipline

Every auto-write to live `profile.md` goes through Claude's read-before-write conflict check. Hallucinated goals, contradictory entries, never-corrected mistakes are caught before commit. Mechanism (a) for ship: user re-states drill completion in next-session opening (user-as-evaluator).

**Critical safety surfaces** (read-before-write is load-bearing, NOT optional):
- `coaching_mode` transitions (silent flip is structurally invisible — see F-coach-45 + F-coach-56)
- `injury_notes` updates (mismatched extraction lands in safety state)
- `symptom_reports` appends (silent capture means user can't correct — F-coach-51)
- All other writes follow standard DC-22 mechanism (a)

## Append-only fields

`symptom_reports`, `drill_ledger`, `group_share_history` are **append-only**. Overwriting prior entries is a state-corruption failure mode (F-coach-52 covers symptom_reports specifically; same shape applies to the others).
