---
file-class: content
locked-by: DC-26
canonical-for: load-progression rubric (Pick 5 — three-layer progression scheme)
references:
  - rules.md (RP-02 progression gating, RP-08 injury-state modulation, RP-09 symptom capture)
  - reference/hypertrophy-ops.md (rep band, RIR target, tempo, form-degradation feedback loop)
  - reference/drill-library.md (drill substitution on stall)
  - profile-template.md (rep_band_preference, current_programme_name, current_mesocycle_phase, years_lifting, coaching_mode, symptom_reports)
source-picks: Pick 5 (three-layer progression — double progression + RPE/RIR autoreg + mesocycle volume context)
---

# Load-progression protocol — back squat hypertrophy

**Purpose.** Content the bot references when deciding whether to authorise a load increase, hold load, or reduce. RP-02 (progression gating in `rules.md`) reads this file. The bot uses these rubrics to coach progression — it does not autonomously prescribe weekly programme structures.

**File class:** content only (DC-26). Behavioural clauses live in `rules.md`. This file is referenced by `rules.md`; it does not contain behavioural rules.

**Three-layer architecture (Pick 5).** The bot operates across three layers of progression decision:

| Layer | Scheme | Bot role |
|---|---|---|
| 1 — in-session gate | Double progression | **Autonomous** — bot gates load decisions from observable set data |
| 2 — tiebreaker signal | RPE/RIR autoregulation | **Autonomous** — bot refines Layer 1 when reps + form alone aren't decisive |
| 3 — user-reported context | Mesocycle volume (RP / Israetel) | **Conversant, not autonomous** — bot reads user-stated mesocycle phase; interprets sessions through that lens; does NOT autonomously prescribe phase changes |

Layers stack. Layer 1 makes the per-set decision; Layer 2 refines it; Layer 3 contextualises both.

---

## Layer 1 — Double progression *(autonomous, in-session gate)*

**Rule:** train inside the user's stated rep band (per `rep_band_preference`, see `hypertrophy-ops.md` Position 2). When the user hits the **top of their band cleanly at the prescribed RIR across all prescribed sets** → authorise a load increase at the next session; restart at the bottom of the band. When they fail the top-rep target → hold load.

**Demonstrated-proficiency criteria** (all must hold to authorise load increase):

1. All prescribed sets completed.
2. Top of band hit on the final set (e.g. if band is 8-12, last set hits 12 reps).
3. RIR at prescribed target — not significantly under-effort (would over-shoot the next load) or over-effort (would over-load and break form).
4. Form held across all sets — no technical-failure stops (see § Form-gating override below).
5. No recent `symptom_reports` entry on this exercise (DC-39 modulation feedback — see § Symptom-aware pause below).

**Load increment size:**

- Default: smallest available increment (typically +2.5 kg / 5 lb for back squat).
- User-equipment-dependent: if user only has access to plate jumps of 5 kg, increment is +5 kg per progression event.
- Programme-aware: if user is on a programme that specifies different increments, defer to programme (see § Programme-aware behaviour below).

**Variant — drop-set trigger:** when reps in the first set hit top of band cleanly, that's a stronger progression signal than waiting until all sets hit top (Helms M&S Pyramid + RP variant). The bot can flag this as an *earlier* progression opportunity but defaults to the all-sets criterion for the standard rule.

**Failure to meet criteria:**

- Failed top-rep target on any set → hold load next session.
- Failed top-rep target on the *final* set specifically → hold load AND consider whether the failure was effort (Layer 2 RIR check) or form (Layer 1 form-gate fire).

**Why this layer is autonomous:** the bot observes the set directly (video upload + user-reported reps/load/RIR). Layer 1's inputs are all bot-observable; the gate decision can be made without user-reported program context.

---

## Layer 2 — RPE / RIR autoregulation *(autonomous tiebreaker)*

**When this layer fires:** Layer 1's criteria are *technically* met but actual-RIR is significantly off prescribed target. Reps completed cleanly but user reports the set was much easier or much harder than the prescribed RIR.

**Adjustment direction:**

- **Actual RIR < prescribed RIR by ≥1** (user pushed closer to failure than programmed; e.g. prescribed RIR 2 but reports RIR 0) → hold load OR reduce load if form was strained. Don't increase — user is already at the limit of clean execution for this load.
- **Actual RIR > prescribed RIR by ≥1** (user was further from failure than programmed; e.g. prescribed RIR 2 but reports RIR 4) → authorise larger-than-default increment (e.g. +5 kg instead of +2.5 kg). The user has headroom and load is undershooting the stimulus.
- **Actual RIR matches prescribed RIR (within ±1)** → default Layer 1 decision stands.

**Evidence:** Helms et al. 2018 RCT (PMC5877330) — RPE-prescribed and %1RM-prescribed produced equivalent outcomes for hypertrophy. RPE-autoregulation is a valid load-adjustment mechanism alongside double progression.

**Calibration caveat — pose pipeline outweighs user RPE on conflict.** Helms 2018 noted user RPE accuracy on squat is weaker than on bench. When user's reported RIR conflicts with pose-pipeline observations (e.g. user reports RIR 3 but pose pipeline shows VL=45% and form breakdown on last 2 reps), bot weights the pose-pipeline observation more heavily. It names the discrepancy via RP-05 confidence-graded contradiction, holds load progression conservatively, and does NOT authorise a load increase on user's RIR claim alone. The user's report is one signal; objective form + velocity-loss data is the stronger signal for hypertrophy progression decisions.

**Composition with form-degradation feedback loop** (`hypertrophy-ops.md` Position 3): if bot observes form degradation at RIR 0-1 targets, may suggest pulling back to RIR 1-2 on subsequent sets. Coaching observation, not autonomous override.

---

## Layer 3 — Mesocycle volume context *(user-reported, bot conversant)*

**Rule:** the bot reads `current_mesocycle_phase` from `profile.md` (set by DC-37 Q1 onboarding capture; updated by user mid-programme). Bot interprets sessions through the user's reported mesocycle phase; modulates Layer 1 + Layer 2 decisions accordingly. Bot does NOT autonomously decide what mesocycle phase the user is in or when they should transition.

**Phase semantics (RP / Israetel framework):**

| Phase | Meaning | Bot interpretation |
|---|---|---|
| `MEV` (Minimum Effective Volume) | Start of mesocycle; lowest sets/week that still drives growth. Recovery markers good. | Default RIR interpretation; load progression on the standard double-progression cadence. |
| `MAV` (Maximum Adaptive Volume) | Mid-mesocycle; sets/week added incrementally; growth is highest here. | Slightly more conservative on load adds — user is already adding sets weekly, so load adds compound the fatigue increment. |
| `MRV` (Maximum Recoverable Volume) | End of mesocycle; sets/week at the ceiling of recoverable training. | More permissive on high VL at set-end (high-fatigue context expected). Hold load preferred over add. |
| `deload` | Week of reduced volume + intensity to dissipate fatigue. | Bot does NOT prescribe progression during deload. Coaches form work + recovery framing. |
| `unknown` | User isn't periodising / doesn't track phase. | Default Layer 1 + Layer 2 only — no phase modulation. |

**Within-phase progression:**

- Set-add progression (adding 1-2 sets/week from MEV → MRV) is **user-reported, not bot-prescribed**. If user says "I'm adding a set this week," bot reads + interprets in context; doesn't autonomously instruct set-adds.
- Across-phase reset (deload → next mesocycle restart at MEV + slightly higher than previous starting load) is user-driven. Bot coaches the user's stated structure.

**Why this layer is non-autonomous:** the bot at Comp 5 scope does NOT have weekly volume tracking, deload-week awareness, or full programme context unless the user reports it. Autonomous mesocycle prescription would fabricate context. The bot is **conversant in the framework** — reads MEV/MAV/MRV vocabulary, interprets sessions through it, doesn't impose phase changes.

**Composition with Layer 1 + Layer 2:**

- MEV phase + Layer 1 criteria met → standard load increase.
- MAV phase + Layer 1 criteria met → load increase but at smaller increment (e.g. +1.25 kg instead of +2.5 kg if user has fractional plates).
- MRV phase + Layer 1 criteria met → bot suggests hold load or finish the mesocycle on current load; flag that next mesocycle's restart will use a slightly higher MEV anchor.
- `unknown` phase → Layer 3 contributes nothing; Layer 1 + Layer 2 make the decision alone.

---

## Programme-aware behaviour *(composes with `hypertrophy-ops.md` Position 1)*

When the user reports a programme that prescribes a *different* progression scheme (e.g. 5/3/1 cycle prescription, RP template auto-progression, Starting Strength linear), the bot does NOT silently defer. It probes the user's goals — why this programme, what are they training for, what's the rationale — then makes a coaching judgement: agree (programme progression composes with hypertrophy goals) or politely disagree (programme conflicts with hypertrophy stimulus; bot names the conflict + the alternative; user decides).

**Exception — physio-prescribed programmes.** If `coaching_mode` is `injury_managing`, `injury_recovery`, or `return_to_training` (per DC-38), the bot defers to the physio's prescription without coaching judgement. See § Modulation pointers below + `rules.md` RP-08.

**Common programme types the bot should recognise:**

- **5/3/1 (Wendler)** — **strength-based programme, not hypertrophy.** Cycle-based load progression on a narrow rep target (5/3/1 specific reps on the main lift); AMRAP top set creates a quasi-hypertrophy stimulus but isn't the programme's primary purpose. If user states hypertrophy is their goal, bot politely disagrees with running 5/3/1 as-is — names the strength-bias mismatch (narrow rep target, low-rep main lift, cycle-based rather than volume-led progression) and suggests either an explicit hypertrophy-focused alternative (RP template, Helms M&S Pyramid hypertrophy block) OR substantial supplemental volume (BBB — Boring But Big — 5×10 supplemental on the main lift at minimum). User decides — but the conflict is named, not papered over.
- **Starting Strength (Rippetoe)** — novice linear progression; bot's call: appropriate for sub-1-year novice (`years_lifting < 1`); diminishing returns for hypertrophy specifically as user advances. Bot may suggest transition to double progression after novice gains end.
- **RP Hypertrophy templates** — mesocycle volume progression; composes cleanly with Layer 3. Bot's role is supporting adherence + form work; defers to template's set/load prescription.
- **Madcow 5×5 / Texas Method** — strength-biased programmes. Bot's call: explicit conflict with hypertrophy stimulus if user states hypertrophy goal; bot names the conflict + suggests hypertrophy-focused alternative; user decides.

---

## Form-gating override *(universal — across all layers)*

**Rule:** technical failure stops progression regardless of rep performance. If the user hits top of band but form broke on the final reps (hip rise ahead of shoulders, knee cave, T-spine flexion, lateral drift, depth shortening), Layer 1's "all criteria met" gate does NOT fire — bot holds load.

**Why this overrides everything else:** form breakdown is a signal that current load exceeds the user's clean-execution capacity. Progressing load further is structurally unsafe AND counter-productive for hypertrophy (degraded reps don't deliver the stimulus despite the rep count).

**Stall handling (Israetel framing):**

- 2 consecutive sessions of failed top-rep target → hold load; address the failure mode rather than continue trying to progress.
- Failure modes the bot addresses by drill substitution (see `drill-library.md`):
  - Eccentric-control loss → tempo squat
  - Out-of-the-hole drive weakness → paused squat
  - Depth shortening from ankle limitation → heel-elevated squat or mobility drill
  - Upper-back brace loss → front squat or bracing drill
  - End-position drift (RP-07 confound) → end-position-stability cueing

After 1 mesocycle of drill-supplementation without progression, bot surfaces three coaching observations for the user to take a careful look at:

(a) **Recovery + nutrition.** Two of the biggest hypertrophy variables — and the two the bot can't see from training data alone. A few hours less sleep this week, protein under target, or a kcal deficit during what should be a growth phase would all explain a persistent stall before any form fault would. The bot names this explicitly when stall persists; it does not prescribe sleep targets, macros, or kcal intake (out of scope — clinical/dietetics territory, same liability shape as injury diagnosis). The user investigates these variables themselves OR consults a dietitian / coach with that scope.

(b) **Ceiling vs anchor.** Load may be genuinely at the user's current ceiling. The next mesocycle's restart anchor should hold at the current load (rather than reset slightly higher per standard mesocycle reset) until a stall break.

(c) **Mobility-rooted form fault.** If form is the limiting factor and drill substitution hasn't resolved it, the limitation may be a mobility deficit needing longer intervention than within-mesocycle work allows. RP-03 active-observation step: user investigates the mobility surface (ankle dorsiflexion, hip flexor, T-spine extension) with self-tests; bot doesn't diagnose root cause.

**Why (a) is named explicitly even though out of scope:** recovery and nutrition are causally upstream of progression decisions for hypertrophy. A bot coaching progression that's blind to these is coaching the wrong axis when these are the problem. Naming the variable is in scope; prescribing intervention is not. F-coach-near-miss avoided — bot doesn't look like a coach while quietly missing the load-bearing variable.

---

## Symptom-aware pause *(DC-39 modulation feedback)*

**Rule:** if `symptom_reports` contains a recent entry (within memory window: 14 days OR last 5 sessions, whichever is longer) on the prescribed exercise, Layer 1 progression **pauses**. Bot holds load even if Layer 1 criteria would otherwise authorise increase.

**Why:** symptom-while-training is a fatigue-recovery signal at minimum; potentially an injury-onset signal. Adding load on top of an exercise the user has recently reported pain on is the F-coach-49 catastrophic failure pattern.

**Composition with `coaching_mode`:**

- `healthy` mode + recent symptom on exercise → progression paused on that exercise; bot prompts user about whether to transition to `injury_managing` (per DC-38).
- `injury_managing` + recent symptom on exercise → progression paused per RP-08 conservative defaults; bot prompts physio recommendation re-surface (per DC-38 + F-coach-58 protection).
- `injury_recovery` → bot defers to physio plan; symptom report goes to user for sharing with physio.

**When the pause lifts:** memory window expires AND no further symptom reports on that exercise — bot can resume standard Layer 1 gating. Bot does NOT autonomously decide the symptom has "resolved" — absence of recent symptom report is the signal, not bot inference.

---

## Modulation pointers — user-state inputs *(DC-37 + DC-38 + DC-39)*

| Field | Effect on progression |
|---|---|
| `rep_band_preference` (DC-37 Q2) | Layer 1 gate target band |
| `current_programme_name` (DC-37 Q1) | Programme-aware coaching judgement (agree / disagree / defer-if-physio) |
| `current_mesocycle_phase` (DC-37 Q1) | Layer 3 phase modulation of Layer 1 + Layer 2 decisions |
| `years_lifting` (DC-37 Q1) | Sub-1-year novice → linear progression appropriate; experienced → double progression default; informs rate expectations |
| `equipment_notes` (DC-37 Q3) | Load increment size (plate jumps available) |
| `coaching_mode` (DC-38) | `injury_managing` → hold load; `return_to_training` → linear ramp until baseline; `injury_recovery` → defer to physio |
| `symptom_reports` (DC-39) | Recent entry on prescribed exercise → progression paused per § Symptom-aware pause above |

---

## Distinct from strength progression

| Dimension | Hypertrophy progression (this protocol) | Strength progression |
|---|---|---|
| Variable progressed | Reps → load → sets (volume-led, multi-axis) | Load primarily; reps usually fixed |
| Rep target | Wide band (user-stated 5-30; gates against user's band) | Narrow target (5×5, 3×5, 5/3/1) |
| Increment cadence | Each mesocycle (or each session for novices via double progression) | Each session (linear novice) or each cycle (5/3/1) |
| Auto-regulation | RPE/RIR (Layer 2) + mesocycle volume context (Layer 3) | Mostly fixed % 1RM; AMRAP set on top end (5/3/1) |
| Stall handling | Hold load + drill substitution + mobility intervention | Deload + restart (5/3/1 deload week) or repeat session (Starting Strength) |
| Bot's autonomous role | Layer 1 gate + Layer 2 tiebreaker | Out of scope — strength-bias programmes have their own autonomous structure (5/3/1's `+10lb/cycle`) that this bot defers to |

---

## What this bot does NOT do

- Does NOT autonomously decide the user's mesocycle phase or instruct phase transitions.
- Does NOT autonomously prescribe weekly volume / set counts. Pick 6's 10-20 sets/wk reference (`hypertrophy-ops.md`) is informational, not autonomous prescription.
- Does NOT operate DUP (Daily Undulating Periodisation) or VBT (velocity-based training) as primary frameworks. These are referenced in literature (see research source) but out of scope at Comp 5 — bot doesn't have intra-week intensity context or bar-velocity tracking infrastructure.
- Does NOT autonomously decide a user has "stalled long enough" to restart a mesocycle or transition programmes. User drives those calls; bot coaches form work and surfaces drill alternatives.

---

## Source

Drawn from internal hypertrophy-coaching research notes — progression rubric: double progression, RPE/RIR autoreg, mesocycle volume, demonstrated-proficiency criteria. Per single-source-of-truth discipline: this file extracts positions + composition rules; the research notes hold the literature digest.
