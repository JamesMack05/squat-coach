---
file-class: content
locked-by: DC-26 (file-class separation) + DC-28 (tabular structure)
canonical-for: drill prescription pool (Pick 7)
references:
  - rules.md (drill-prescription selection clause; behavioural)
  - reference/hypertrophy-ops.md (Position 5 drill bias + hypertrophy_applicability rule)
  - reference/progression-protocol.md (stall handling via drill substitution)
  - profile-template.md (equipment_notes, heel_elevation_access, injury_notes, symptom_reports, current_programme_name)
source-picks: Pick 7 (drill schema + 9-drill seed) + DC-28 (tabular structure)
---

# Drill library — back squat hypertrophy

**Purpose.** Tagged lookup table the bot queries when prescribing a drill in response to a detected form fault or coaching need. Per DC-28, structured as a table (not prose) — adding a drill is a table row, not a coaching-logic rewrite.

**File class:** content only (DC-26). Behavioural clauses — when to prescribe, how to phrase, conditional logic — live in `rules.md`. This file holds the data the prescription clause reads against.

**Composition:**

- `hypertrophy-ops.md` Position 5 — drill prescription bias (hypertrophy-coach vs strength-coach drills) + the rule for `hypertrophy_applicability` tagging.
- `progression-protocol.md` § Stall handling — drill substitution as the response when a load fails to progress for 2 consecutive sessions.
- `rules.md` — the prescription selection clause + RP-NN behavioural framing.
- `profile.md` (per-user state) — equipment, injuries, symptom history, programme context that filter the drill pool.

---

## Schema *(DC-28 locked)*

| Column | Type | Notes |
|---|---|---|
| `drill_name` | text | Display name + tempo qualifier where relevant |
| `faults_addressed` | tag list | From § Fault-tag enumeration below |
| `primary_target` | tag list | From § Primary-target enumeration below |
| `hypertrophy_applicability` | enum | `primary` / `secondary` / `conditional` / `not_recommended` — see § Tag rule below |
| `equipment_required` | tag list | From § Equipment-tag enumeration below |
| `contraindications` | tag list | From § Contraindication-tag enumeration below |
| `prescription_text` | text | Coachable instruction — sets × reps × RIR + tempo + cue |
| `evidence_anchor` | text | Brief citation pointing to research source |

---

## Tag enumerations

### Fault tags *(`faults_addressed`)*

Mapped to pose-pipeline detectable signals + RP-07 / RP-05 outputs. Adding a fault tag here means RP-prescription logic in `rules.md` can detect it (via pose data) OR the user can state it.

| Tag | Signal source |
|---|---|
| `shallow_depth` | Pose: knee-angle minimum >90° per rep |
| `shallow_depth_ankle_limited` | Pose: shallow_depth + excessive_torso_lean + ankle ROM signal (user self-test via RP-03) |
| `excessive_depth_without_control` | Pose: butt-wink (pelvis posterior tilt at bottom), T-spine flexion |
| `knee_cave` | Pose: frontal-plane knee position (RP-05 low-confidence per MediaPipe FPPA noise ~19°) |
| `hip_rise_ahead_of_shoulders` | Pose: hip-Y velocity > shoulder-Y velocity in concentric (good-morning shift) |
| `eccentric_too_fast` | Pose: descent time below user's prescribed tempo |
| `concentric_grind` | Pose: VL high but reps complete (fatigue signal) |
| `inconsistent_tempo` | Pose: tempo variance across set above threshold |
| `end_position_drift` | Pose: top-of-rep position not stable across reps (RP-07 confound flag — see hypertrophy-ops Position 3) |
| `excessive_torso_lean` | Pose: torso angle past threshold at depth (independent of ankle signal) |
| `weak_upper_back_brace` | Pose: bar drift forward + chest collapse |
| `beginner_movement_quality` | Heuristic: user-stated `years_lifting < 1` + multi-fault uncoordinated pattern |
| `fear_of_depth` | User-stated psychological/confidence issue (not pose-detectable; conversational) |
| `weak_brace_under_load` | User-stated + observed (multi-rep collapse pattern under sustained load) |

**Detection-source coaching behaviour:** the bot uses the typical signal source (column above) to calibrate coaching response. **User-stated faults without pose verification** trigger RP-03 active-observation prompts (e.g. "let me see a side-on video so we can verify what you're feeling"). **Pose-detected faults** trigger RP-05 confidence-graded contradiction (high / medium / low confidence per signal quality — e.g. depth-from-knee-angle is high-confidence; knee-cave from MediaPipe FPPA is low-confidence per ~19° error floor). **Mixed (user-stated AND pose-confirmed)** is highest-confidence — bot has both subjective experience + objective signal. This routing lives in `rules.md`; the data structure here supports it via the Signal-source column.

### Primary-target tags *(`primary_target`)*

What the drill biases toward — what the lifter is working on through this drill. **Mixed semantics intentionally:** the enum contains two types of targets — **muscle targets** (`quad` · `glute` · `hamstring`) and **developmental / skill targets** (`tempo_control` · `mobility` · `brace`). Most drills span both types (paused squat = `tempo_control` + `quad`; goblet = `brace` + `mobility`). Bot may surface both types at coaching time ("working on tempo control while biasing quad stimulus") — the muscle / skill distinction at coaching time lives in `rules.md`, not the schema. Splitting into two columns would leave most cells null because most drills are dual-target; one column with documented dual semantics costs less and reads cleaner.

`quad` · `glute` · `hamstring` · `tempo_control` · `mobility` · `brace`

### Hypertrophy-applicability enum *(`hypertrophy_applicability`)*

Tagging rule (composes with `hypertrophy-ops.md` Position 5):

- **`primary`** — drill biases hypertrophy stimulus via Pearson 2024 / Schoenfeld 2024 / Israetel mechanism (longer muscle length, eccentric tempo control, paused work, ROM bias toward stretch).
- **`secondary`** — drill addresses a form fault that interferes with hypertrophy work (mobility, brace, beginner pattern) but isn't itself a hypertrophy-stimulus driver.
- **`conditional`** — depends on user context (experience level, programme, equipment, goal-shading). Selection requires reading `profile.md` state, not tag alone.
- **`not_recommended`** — strength-coach default that undermines hypertrophy intent. Bot does NOT prescribe these for users on a hypertrophy programme; can discuss if user explicitly raises them.

### Equipment-required tags *(`equipment_required`)*

Filters against `profile.md` `equipment_notes` + `heel_elevation_access` (DC-37 Q3 capture).

`none` · `front_rack` · `heel_elevation` · `safety_bars` · `specialty_bar` · `belt_squat_machine`

### Contraindication tags *(`contraindications`)*

Filters against `profile.md` `injury_notes` (DC-37 Q4) + recent `symptom_reports` (DC-39, 14d / 5-session window).

`knee_pain_acute` · `low_back_pain_acute` · `hip_impingement` · `ankle_mobility_severe` · `none`

---

## Drill prescription selection mechanism

Bot's prescription logic (lives in `rules.md`; described here so it's clear what this content supports):

```
SELECT drill
WHERE  fault IN detected_faults
  AND  hypertrophy_applicability IN (primary, secondary, conditional)
  AND  equipment_required ⊆ user_equipment
  AND  contraindications ∩ user_injuries_and_recent_symptoms = ∅
  AND  (hypertrophy_applicability ≠ conditional OR user_context_supports_conditional)

IF no fault detected AND user is on hypertrophy work → high-bar back squat (default)
IF no drill matches BUT faults detected → escalate: RP-05 low-confidence response OR RP-03 active-observation prompt for more data
```

**Default behaviour:** high-bar back squat is the **default hypertrophy back-squat prescription** when no specific fault is detected. The bot doesn't need a fault to prescribe high-bar — high-bar IS the hypertrophy back-squat working-set default per Position 5 of `hypertrophy-ops.md`. Other drills are prescribed against specific faults or developmental targets.

Detected faults come from pose pipeline (RP-07 / RP-05) + user-stated faults. Tie-breaking when multiple drills match: prefer `primary` over `secondary` over `conditional`; within tier, prefer drills with broader fault coverage (more `faults_addressed` matched) OR strongest evidence anchor.

`symptom_reports` weighting (per DC-39): drills associated with recent symptom_reports entries are **weighted down** beyond the binary `contraindications` filter — they're not strictly excluded, but bot prefers alternatives unless the symptom data narrows the choice.

---

## Drill table *(9-drill seed)*

**Prescription template placeholders.** Cells in the Prescription column use runtime placeholders that the bot fills from `profile.md` + RP-08 modulation at prescription time:

- `{sets}` → from progression-protocol RP-02 prescription (typically 3-4 sets, varies by user/programme/mesocycle phase)
- `{rep_band}` → from `profile.md.rep_band_preference` (e.g. "8-12", "6-10", "12-15") per Pick 2
- `{RIR}` → from Pick 3 baseline modulated by RP-08 coaching_mode (`healthy` → RIR 1-3; `injury_managing` → RIR 2-4 with no near-failure final set; etc.)
- `{tempo}` → from Pick 1 default (3-4s ecc + 1-2s pause + controlled concentric) unless drill prescribes its own tempo (e.g. tempo squat's 4-1-X-0). Drill-prescribed tempos override default.

**Tempo notation convention.** Where used: `ecc-pauseBottom-con-pauseTop`. So `4-1-X-0` reads as 4s eccentric / 1s pause at bottom / controlled (unspecified) concentric / no pause at top. `X` denotes "controlled but unspecified seconds" — lifter executes cleanly without timing the concentric.

| Drill | Hypertrophy | Equipment | Contraindications | Faults addressed | Primary target | Prescription | Evidence |
|---|---|---|---|---|---|---|---|
| **Paused squat** | primary | `none` | `none` | shallow_depth · eccentric_too_fast · end_position_drift · concentric_grind | tempo_control · quad | `{sets}×{rep_band} @ {RIR}, {tempo} with explicit cue: 1-2s pause at bottom; controlled concentric out of the hole` | Israetel (RP, BarBend) — bottom pause kills rebound + drives quad stimulus |
| **Tempo squat (4-1-X-0)** | primary | `none` | `none` | eccentric_too_fast · inconsistent_tempo · excessive_depth_without_control | tempo_control · quad | `{sets}×{rep_band} @ {RIR}, 4-1-X-0 tempo (overrides default — more deliberate than default tempo)` | Pearson 2024 (PMC11754408) — slow-ecc 4-1 produced significantly greater vastus lateralis hypertrophy (ES 1.74) vs fast-ecc (ES 1.37) |
| **Heel-elevated back squat** | primary | `heel_elevation` | `none` | shallow_depth_ankle_limited · excessive_torso_lean | quad | `{sets}×{rep_band} @ {RIR}, {tempo}, heels on plates/wedge` | Israetel (RP, BarBend) — heel elevation permits upright torso + deeper depth, biases quad |
| **High-bar back squat** | primary | `none` | `none` | `default_hypertrophy_back_squat` (no specific fault required — see § Drill prescription selection mechanism § Default behaviour) | quad | `{sets}×{rep_band} @ {RIR}, {tempo}, bar across upper traps` | Practitioner consensus — high-bar bias quad over low-bar's posterior-chain bias; this is the default hypertrophy back-squat prescription per `hypertrophy-ops.md` Position 5 |
| **Front squat** | primary | `front_rack` | `low_back_pain_acute` | weak_upper_back_brace · shallow_depth_ankle_limited | quad · brace | `{sets}×{rep_band} @ {RIR}, {tempo}, clean front-rack` | Yavuz 2015 (PubMed 25630691) — higher quad EMG than back squat across full ROM (RF, VL, VM all peak in front squat) |
| **Goblet squat** | secondary | `none` | `none` | brace_under_load_pattern · beginner_movement_quality | brace · mobility | `{sets}×{rep_band} @ {RIR}+1 conservative-on-RIR for beginners, {tempo}, dumbbell/kettlebell at chest` | Practitioner standard for beginner pattern + brace teaching |
| **Deep squat hold (mobility)** | secondary | `none` | `hip_impingement` | ankle_mobility · hip_mobility | mobility | `3×30-45s at bottom of bodyweight squat, breathe normally, no load` — fixed prescription (not load-progressed) | Practitioner mobility standard — passive end-range loading |
| **Bracing drill (immovable resistance)** | secondary | `none` | `low_back_pain_acute` | weak_brace_under_load | brace | `5×8-10s isometric brace against immovable post / heavy bag, breathing maintained` — fixed prescription (not load-progressed) | Practitioner standard for intra-abdominal pressure + brace under load |
| **Low-bar back squat** | conditional | `none` | `none` | (different muscle emphasis — quad-bias drops, hip/back/posterior-chain bias rises) | quad → hip+glute+posterior chain | `{sets}×{rep_band} @ {RIR}, {tempo}, bar across rear delts` | Helms M&S Pyramid (neutral); practitioner-bodybuilding tradition treats high-bar as quad-bias default but low-bar valid for hypertrophy if muscle emphasis suits user goal |

---

## Drill notes

Per-drill narrative for the bot to coach effectively. Concise — enough to ground the prescription, not a coaching manual.

### Paused squat *(primary)*

Bottom of the rep is the highest-stimulus position (longest muscle length at greatest tension). 1-2s pause eliminates the stretch-reflex rebound — every concentric drive starts from a dead stop. Israetel's framing: "kills the rebound effect during the amortisation phase… slightly increases safety and reduces injury risk." Programmed for hypertrophy specifically because it extends TUT at the stretch position; programmed for strength differently (heavier load, 1-3 reps, intent to drive out of the hole).

### Tempo squat *(primary)*

4-1-X-0 notation: 4s eccentric / 1s pause at bottom / controlled (unprescribed) concentric / no top pause. Pearson 2024 evidence specifically supported the 4-1 eccentric+pause combination over fast eccentric for quad hypertrophy. The cue is "control the descent like you're holding the bar against the floor"; lifter should feel the eccentric phase, not drop into it.

### Heel-elevated back squat *(primary)*

Plate or weightlifting-shoe wedge under heels (typical: 1-2 inches / 25-50mm). Solves ankle-mobility-limited shallow depth without prescribing mobility intervention — composes with progression-protocol's stall handling (option c, mobility-rooted form fault) by sidestepping the ankle question for the immediate session. Israetel's primary cue is "let the knees travel as far over the toes as possible while keeping heels on the ground" — heel elevation makes this geometrically achievable.

### High-bar back squat *(primary)*

Bar position: across upper traps, not on rear delts. More upright torso than low-bar; quad bias rises, posterior-chain bias drops. Default position for hypertrophy back-squat work. If user already trains low-bar by default, see § Conditional drills below.

### Front squat *(primary)*

Front-rack position; bar across front delts + collarbone. Higher quad EMG than back squat across full ROM (Yavuz 2015) — RF, VL, VM all peak in front squat. Brace demand is high (forced upright torso); user with weak upper-back brace will fail front squat before quads fail. Pair with bracing drill if brace is the limiting factor.

### Goblet squat *(secondary)*

Beginner pattern + brace teaching. Front-loaded with dumbbell or kettlebell at chest. The front-loading forces upright torso (same mechanism as front squat but at lower absolute load). For beginners (sub-1-year users) it's a learning step toward back squat; for experienced users it's primarily a brace/warmup drill.

### Deep squat hold *(secondary — mobility)*

Bodyweight, no load. Passive end-range mobility work. 30-45s at bottom of squat position; lifter breathes normally; goal is loaded end-range tissue exposure, not strength. Sequenced before main squat work or as a separate mobility session. Contraindication: hip impingement (passive end-range can aggravate impingement signal).

### Bracing drill *(secondary — brace)*

Isometric brace work against immovable resistance (heavy bag, immovable post, wall plank variants). Teaches intra-abdominal pressure under load without the spinal-load risk of failed-brace squatting. 5-10s holds; emphasis on breathing maintained through brace (NOT held-breath; lifter should be able to talk through the brace). Contraindication: acute low-back pain (load on brace under pain can mask + worsen).

### Low-bar back squat *(conditional)*

See § Conditional drills behaviour below.

---

## Conditional drills behaviour

`conditional` drills require reading `profile.md` context before selection.

### Low-bar back squat

Default coaching posture: hypertrophy back-squat work biases toward high-bar (quad emphasis). The bot defaults to high-bar prescription when user is starting fresh or has no stated bar-position preference.

**When user already trains low-bar by default:**

1. Bot can **mention high-bar as a quad-emphasis alternative** — "high-bar would bias quads more if that's where you want the stimulus" — but does NOT impose it.
2. If user pushes back ("I prefer low-bar" / "low-bar is what I'm used to" / "I'm training low-bar this block"), bot **keeps user on low-bar** and coaches the low-bar variation.
3. Bot adapts coaching cues to the low-bar variant — different bar path, more torso lean acceptable, posterior-chain bias is the muscle emphasis the user is actually getting.
4. Bot does NOT keep nudging high-bar across sessions once the user has stated preference. Initial single mention is the limit at first contact; nagging is a register failure.

**Re-raise threshold:** if user has trained low-bar for **3+ consecutive mesocycles without load progression** (stall persists across 3 mesocycle resets), bot may re-mention high-bar as a potential variation worth trying — framed as "the bar position you've been training hasn't been progressing; want to try high-bar for a mesocycle to see if it unlocks the quad stimulus?" Re-raise still respects user pushback — if user says no, bot drops it for another 3 mesocycles. Engineering grounds: 3-mesocycle stall is meaningful evidence that the current bar-position-shaped stimulus isn't producing progression; raising the alternative at that point is coaching, not nagging.

**Engineering grounds:** low-bar is not "wrong" for hypertrophy — it shifts the muscle distribution toward hip + glute + posterior chain. If the user explicitly wants high-bar-shaped quad stimulus, they'd train high-bar; if they're training low-bar by preference, the bot respects the goal-shading and coaches the variation they've chosen. Imposing high-bar against user preference is the strength-coach-overreach failure mode the bot specifically avoids.

---

## Out-of-scope drills

Per DC-01 (back-squat-only at Comp 5 scope), the following are NOT in the prescription pool. Bot can discuss them if user raises them; bot does NOT autonomously prescribe them.

| Drill | Why out of scope | Where it'd land if in scope |
|---|---|---|
| Leg press | Knee-only loaded extension; not a back squat variation | Quad assistance; Israetel-cited; would be `primary` for quad isolation |
| Hack squat | Machine-based; not a back squat | Quad assistance; similar role to leg press |
| Belt squat | Specialised machine; spinal-load removed | **Promoted to EX-20** (expansion-backlog.md) — quad assistance for users with back-load issues; composes with `injury_managing` modes (loadable without back compression) + `return_to_training` (ramp without spinal stress). Freelancing-lift candidate; high paid-product value for injured / managing-pain users. |
| Box squat (any depth) | Removed from seed pool — box squat for depth confidence overlaps with goblet squat + deep squat hold without adding distinct hypertrophy value at this bot's scope | n/a — gated out |
| Jump squat | Power-training drill; different stimulus from hypertrophy | EX-X future power-training scope, not Comp 5 |
| Olympic-lifting variants (snatch balance, OHS) | Power / sport-specific; outside hypertrophy frame | EX-X future cross-domain scope |

EX-14 (drill video library) covers future linked-video demonstrations of these drills — current library is text-only.

---

## Modulation pointers — user-state inputs *(DC-37 + DC-38 + DC-39)*

| Field | Effect on drill prescription |
|---|---|
| `equipment_notes` + `heel_elevation_access` (DC-37 Q3) | `equipment_required` filter — heel-elevated squat excluded if no elevation access; front squat excluded if no front-rack |
| `injury_notes` (DC-37 Q4) | `contraindications` filter — front squat excluded if acute low-back, deep squat hold excluded if hip impingement, etc. |
| `symptom_reports` (DC-39 — 14d / 5-session window) | Drills associated with recent symptom_reports entries weighted down (not strictly excluded — bot prefers alternatives unless symptom data narrows choice) |
| `years_lifting` (DC-37 Q1) | Beginner-conditional drills (goblet squat, deep squat hold) more prescribable for sub-1-year lifters; less so for 5+ year experienced. Conditional drills require this read. |
| `current_programme_name` (DC-37 Q1) | Programme-aware behaviour — if user's programme prescribes a drill not in this library (or excludes one that's in), bot probes goals + makes coaching judgement (see `hypertrophy-ops.md` Position 1) |
| `coaching_mode` (DC-38) | `injury_managing` → contraindications filter applies more strictly + drills associated with recent symptom_reports excluded outright; `injury_recovery` → physio-prescribed drills only; `return_to_training` → bias `secondary` (mobility / brace) early, progressively unlock `primary` |

---

## Adding a drill to the library

Per DC-28's locked structure: a drill addition is a single row, not a coaching-logic rewrite. To add a drill:

1. Pick `hypertrophy_applicability` per the rule above (primary if hypertrophy-mechanism-aligned; secondary if form-fault adjunct; conditional if context-dependent; not_recommended if strength-coach default).
2. Tag `faults_addressed` from existing fault-tag enumeration (or extend enumeration if new fault type — requires `rules.md` detection logic update).
3. Tag `equipment_required` + `contraindications` from existing enumerations.
4. Draft `prescription_text` matching coachable instruction shape (sets × reps × RIR + tempo + cue).
5. Pin `evidence_anchor` to research source.

Adding a fault tag or equipment tag affects the prescription clause — that change goes through `rules.md`, not here. This file holds drill data; behavioural mechanisms live in rules.

---

## Source

Drawn from internal hypertrophy-coaching research notes — hypertrophy-vs-strength drill prescription bias, tempo evidence, depth evidence. Per single-source-of-truth discipline: this file extracts the prescription pool + tagging structure; the research notes hold the literature digest with full citations.
