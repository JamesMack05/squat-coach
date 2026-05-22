---
file-class: content
locked-by: DC-26
canonical-for: hypertrophy operationalisation (DC-11)
references:
  - rules.md (RP-02 progression gating, RP-08 injury-state modulation, RP-09 symptom capture)
  - reference/progression-protocol.md (Pick 5 three-layer progression)
  - reference/drill-library.md (Pick 7 tabular drill library + drill-prescription pool)
  - profile-template.md (rep_band_preference, current_mesocycle_phase, coaching_mode, symptom_reports, equipment fields)
source-picks: Pick 1 (tempo) · Pick 2 (rep band) · Pick 3 (RIR target) · Pick 4 (depth standard) · Pick 6 (volume framework) · Pick 7 (drill bias)
---

# Hypertrophy operationalisation — back squat

**Purpose.** Content the bot references when reasoning about hypertrophy-specific squat coaching. Defines *what the coach prescribes* for back-squat-for-hypertrophy work, distinct from strength training (e.g. 5/3/1, Starting Strength, powerlifting prep) or power training (e.g. dynamic-effort, Olympic-lifting variants).

**File class:** content only (DC-26). Behavioural clauses — when the bot prescribes, how it phrases, how it handles edge cases — live in `rules.md` (RP-01..09). This file is *referenced by* `rules.md`; it does not *contain* behavioural rules.

**Hedging discipline (DC-09).** The literature converges on broad ranges, not point values. Where the literature has named disagreement zones, this file states the coach's locked position AND names the disagreement. The bot should not over-claim a position as settled when the literature is genuinely split.

---

## Frame — what hypertrophy operationalisation means

Hypertrophy = muscle growth. The coach's job is to drive the stimulus that produces it (mechanical tension under stretch, sufficient volume, proximity to failure without form breakdown) while protecting the lifter from the form-degradation that derails it.

This is distinct from:

- **Strength training** — load increment per session/cycle; rep range narrow (1-5); failure-proximity often farther; back squat is the test lift, not a hypertrophy lift. Example programmes: Starting Strength, 5/3/1, Texas Method intensity day.
- **Power training** — speed/intent per rep; load is sub-maximal but moved fast; rep range very low (1-3); back squat may be a means to vertical jump / Olympic lift transfer. Example: dynamic-effort squats in Westside-derived programming.

The coach's prescriptive defaults below assume **hypertrophy** is the goal. The bot reads `coaching_mode` + `current_programme_name` + `rep_band_preference` from `profile.md` to handle cases where the user is on a different programme shape (see § Modulation pointers below).

---

## Position 1 — Tempo *(Pick 1)*

**Locked position:** prescribed tempo for hypertrophy back-squat work = **3-4s eccentric (descent) + 1-2s pause at bottom + controlled concentric (no specified time)**.

**Why this position:**

- **Pearson et al. 2024** (PMC11754408) — squat-specific RCT. Slow eccentric (4s ecc + 1s con) produced significantly greater vastus lateralis hypertrophy than fast eccentric (1s + 1s), ES 1.74 vs 1.37, p < 0.05. Slow-ecc group also gained more 1RM (+11.1 kg vs +5.6 kg).
- **Israetel (RP, via BarBend)** — recommends 1-2s pause at bottom of hypertrophy squats specifically "to eliminate the rebound effect during the amortisation phase… slightly increases your safety and reduces injury risk."
- **Practitioner-bodybuilding tradition** — slow eccentric + bottom pause is the standard hypertrophy-squat tempo across Helms, Israetel, Nippard.

**Disagreement zone the bot should know about:**

- **Schoenfeld et al. 2015 + 2024** — repetition durations of 0.5-8s produced similar hypertrophy in their meta-analysis; durations >10s were inferior. Schoenfeld camp position: "tempo within 2-8s total is largely irrelevant; pick whatever the lifter executes cleanly."
- **Resolution:** Pearson 2024 sits *inside* Schoenfeld's 2-8s envelope, so not flatly contradictory. The divergence is whether the lifter should be coached to a specific tempo (our position) or left to natural cadence (Schoenfeld camp). We pick deliberate tempo because (a) it gives the coach something detectable + prescribable, (b) Pearson is recent direct squat-specific evidence, (c) practitioner-bodybuilding consensus aligns.

**Programme-aware behaviour.** When the user reports a programme prescribes a different tempo (e.g. RP template specifying 3-1-1-0, or a strength-biased programme with no prescribed tempo), the bot does NOT silently defer. It probes the user's goals — *why* are they on this programme, what are they training for, what's the rationale — then makes a coaching judgement: agree (programme tempo composes with the user's stated hypertrophy goal) or politely disagree (programme tempo conflicts with hypertrophy stimulus; bot names the conflict + the recommended alternative; user makes the final call). The bot acts as a coach, not a passive prescription-relayer.

**Exception — physio-prescribed programmes.** If the user's programme is physio-prescribed (i.e. `coaching_mode` is `injury_managing`, `injury_recovery`, or `return_to_training` per DC-38), the bot defers to the physio's prescription without coaching judgement. Clinical decisions override the hypertrophy-coach default. See `rules.md` RP-08.

**Composes with pose pipeline.** Descent time is computable from hip-Y trajectory; pause is detectable from the velocity-zero window at the bottom of the rep. The bot can verify whether the user is hitting the prescribed tempo per-rep when video is uploaded.

---

## Position 2 — Rep range *(Pick 2)*

**Locked position:** rep range is **user-stated within the 5-30 envelope** (Schoenfeld 2017 meta range). Bot reads `rep_band_preference` from `profile.md`; coaches whatever band the user trains in. Hypertrophy specialisation lives in *how* the band is coached (tempo, depth, RIR, drill bias), NOT in *which* band is prescribed.

**Why this position:**

- **Schoenfeld, Grgic, Ogborn, Krieger 2017 meta-analysis** — hypertrophy occurs across a wide spectrum of loads (5-30 reps per set) provided sets are taken close enough to failure; statistical edge favours heavier loads for both strength AND hypertrophy when matched.
- **Schoenfeld via BarBend** — "Hypertrophy can occur across a wide spectrum of rep ranges — as high as 30-RM per set… provided volume load is equated."
- **Why not impose 8-12:** strength coaches and hypertrophy coaches both work across rep ranges; the differentiation between them is cueing within the rep range, not the range itself. Imposing a single band would over-prescribe and reduce adaptive value; allowing user to pick respects the evidence-equivalence.

**Practitioner conventions the bot should know:**

- **8-12 reps** — bodybuilding convention (Helms M&S Pyramid, Legion, Hevy). Most users default here.
- **5-30 acceptable** — RP / Israetel volume-landmarks framing: "training each muscle ≥ 2× weekly within 30-85% 1RM, rep range 5-30 per set."
- **Higher rep bands (12-20)** — useful for users with technique/joint reasons to keep load moderate, or as variation within a programme.
- **Lower rep bands (5-8)** — appropriate when user is on a strength-biased programme but still working a hypertrophy block, or as variation.

**Composition with progression (Pick 5):** RP-02 progression gating reads `rep_band_preference` from profile.md and gates double-progression against that band — i.e. "did user hit top of THEIR band cleanly across all sets" rather than "did user hit 12 reps." See `progression-protocol.md`.

**Composition with RP-07 (fatigue-degradation):** the VL-to-RIR relationship shifts with rep band — final-rep velocity drops more in high-rep sets even at same RIR (cumulative fatigue per rep). The bot's interpretation of pose-pipeline VL output should compose with the user's stated band. Specifically: VL/RIR mapping is calibrated for 6-12 band; wider bands (≤5 or ≥15) marked as lower-confidence interpretation (RP-05 medium branch fires).

---

## Position 3 — RIR / failure proximity *(Pick 3)*

**Locked position:** working sets target **RPE 7-9 / RIR 1-3 baseline**. **Final set of movement closest to failure — RIR 0-1 if form holds**. Stop on technical failure regardless of RIR.

**Why this position:**

- **Schoenfeld via BarBend** — direct prescription: "RIR 2 on set 1, RIR 1 on set 2, failure on the final set" (with form-gated stop). Composes with double progression + technical-failure-stops-set.
- **Helms et al. 2018 RCT** (PMC5877330) — hypertrophy sessions prescribed 8 reps @ RPE 8 (RIR ~2). RPE-prescribed matched %1RM-prescribed for hypertrophy outcomes. Useful for autoregulation tiebreaker (see § Modulation below).
- **Grgic, Schoenfeld et al. 2022 meta-analysis** (PMC9935748) — proximity-to-failure: "No evidence to support that RT performed to momentary muscular failure is superior to non-failure RT for muscle hypertrophy" (ES = 0.12, 95% CI -0.13 to 0.37, p = 0.343). RIR 0-4 all in-range for hypertrophy.

**Disagreement zone:**

- **Beardsley / "effective reps" / stimulating-reps camp** — argues only final ~5 reps before concentric failure deliver meaningful hypertrophic stimulus; implies RIR ≤5 required for any meaningful stimulus.
- **Nuckols (Stronger By Science)** — sceptical of strict effective-reps model.
- **Practical convergence:** most evidence-based practitioners land at RIR 0-3 for hypertrophy sets, with final set closest to failure. Disagreement is over *whether RIR 0 is necessary* (Beardsley) vs *whether RIR 2-3 is sufficient* (Schoenfeld). The broad band is settled; the inner boundary is contested.

**Universal form-gating override:** technical failure stops the set, regardless of RIR target. Coaching consensus is universal that *training to muscular failure on barbell back squat is high-risk* because technical failure (hip rise, knee cave, T-spine flexion, lateral drift, depth shortening) precedes muscular failure and the difference is structurally dangerous. The "RIR 0-1 final set" prescription is conditional on form holding — if form breaks at RIR 3, the set is over.

**Form-degradation feedback loop (RP-07 + RP-08 composition).** If the bot observes form degradation on sets where the user is targeting RIR 0-1, the bot may politely suggest pulling back to RIR 1-2 on subsequent sets / sessions. This is a *coaching observation*, not an autonomous RIR-target override — bot names the observation, user decides whether to act on it. Composes with RP-09 symptom capture (if the form degradation is paired with pain reports, mode-transition consideration fires per DC-38).

**Composition with RP-07 (fatigue-degradation) + pose pipeline:**

- At RIR 1-3, expected concentric velocity loss is 20-35% across the set. This is the bot's expected signal at end-of-set.
- At RIR 0-1 final set, expected VL is 40-50%.
- VL outside expected range disambiguates via `end_position_stable` flag (RP-07 confound caught during calibration — see `pose/aggregate.py` FatigueSignature). Bot must consider end-position stability as a separate signal before diagnosing fatigue from VL alone.

**Composition with Pick 5 mesocycle layer (RP-08):**

- At user-reported MRV, high VL at set-end is *expected* (high-fatigue context); bot is more permissive in interpretation.
- At MEV (start of mesocycle), high VL is *anomalous*; bot is more concerned and may suggest user is over-shooting load for the mesocycle phase.

---

## Position 4 — Depth standard *(Pick 4)*

**Locked position:** **floor = parallel** (≥90° knee flexion at deepest point). **Default prescription = as-deep-as-form-holds** (bias longer muscle lengths per Schoenfeld 2024).

**Failure modes the bot handles distinctly:**

- **Below-parallel depth** (above 90° flexion) → prescribe deeper. Hypertrophy-specialised position, not strength-coach generic.
- **Sub-parallel via form breakdown** (butt-wink, T-spine flexion, lateral drift, foot pronation) → bot does NOT diagnose the root cause (ankle vs hip vs T-spine). RP-03 active-observation framing: bot suggests a user-driven self-verification step ("screenshot your bottom position from the side, send it back" / "test ankle dorsiflexion against a wall, send a photo"). User reports back; bot uses the user-verified data to suggest mobility or heel-elevation work. The coach guides observation; the user diagnoses.
- **Deep-with-form-holding** → prescribe maintain.

**Why this position:**

- **Schoenfeld et al. 2024 narrative review** — "Utilizing a ROM that biases longer muscle lengths should be the default approach to exercise technique when trying to maximize hypertrophy."
- **Bloomquist et al. 2013** — deep squats (0-120° knee flexion) produced greater quad CSA at multiple sites than partial squats (0-60°). Distal quad regions showed the biggest deep-squat advantage.
- **Kubo et al. 2019** — squats to 90° vs 140° knee flexion. Quad + hamstring hypertrophy similar between groups; deep squat won for adductors + gluteus maximus. Interpretation: ≥90° saturates quad hypertrophy; below-parallel adds glute + adductor stimulus.
- **Israetel (RP, via BarBend)** — for quad hypertrophy specifically: "allow knees to travel as far over the toes as possible while keeping heels on the ground… more knees over toes = more quad hypertrophy… your quads are exposed and fully stretched at the bottom." Recommends heel elevation / weightlifting shoes to permit upright torso + deeper depth.

**Equipment composition (DC-37 Q3):**

- If `heel_elevation_access = true` (user has plates, wedge, or weightlifting shoes) → heel-elevation is a prescription option for users with ankle-mobility-limited depth.
- If `heel_elevation_access = false` → mobility work + bodyweight-deep-squat-hold prescription instead (see `drill-library.md`).

**Composition with pose pipeline:**

- Depth measurable directly via knee-angle minimum per rep (after DC-34 rep-segmentation filter).
- Form-breakdown signals (butt-wink, T-spine flexion, lateral drift) are pose-detectable to varying degrees of confidence — RP-05 confidence-graded contradiction applies.

**Composition with injury modulation (RP-08):**

- In `injury_managing` mode: floor moves up to user's pain-free depth (above-parallel acceptable if below triggers pain); **no bias-deeper**. The default hypertrophy "go deeper" inverts in injury — depth that aggravates is contraindicated regardless of the hypertrophy stimulus argument.

---

## Position 5 — Drill prescription bias *(Pick 7 — full table in `drill-library.md`)*

**Locked position:** hypertrophy-coach drills bias toward quad-stimulus + longer-muscle-length + tempo-control + paused-TUT. Strength-coach drills (heavy low-bar, box squat for strength-out-of-hole, max-effort variations) are de-prescribed for hypertrophy users.

**Hypertrophy-primary drills** (see `drill-library.md` for full schema with equipment + contraindications + prescription text):

- **Paused squat (1-2s pause)** — kills rebound, increases TUT at the stretch position, drives quad stimulus.
- **Tempo squat (4-1-X eccentric/pause/concentric)** — Pearson 2024 evidence + practitioner tradition; trains eccentric control + intentional stretch loading.
- **Heel-elevated back squat** — bias quad over hip; permits upright torso + deeper depth (Israetel).
- **High-bar back squat** — bias quad over hip (less torso forward lean than low-bar).
- **Front squat** — higher quadriceps EMG than back squat across full ROM (Yavuz et al. 2015); rectus femoris, vastus lateralis, vastus medialis all peak in front squat. Hypertrophy outcomes between front + back are similar pooled (~4.4% back, ~5.1% front mean increase) despite the EMG difference — but the EMG difference makes front squat a quad-emphasis tool.

**Secondary drills** (mobility, brace, beginner-pattern):

- Goblet squat, deep squat hold, bracing drills — useful for addressing form faults that interfere with hypertrophy work; not themselves hypertrophy-stimulus drivers.

**Conditional drills** (depends on user context):

- **Low-bar back squat** — different muscle emphasis (quad-bias drops, hip/back/posterior-chain bias rises). Not "wrong" for hypertrophy — it just shifts the muscle distribution. If the user already trains low-bar by default, the bot can nudge toward high-bar by mentioning it as a quad-emphasis alternative — but if the user pushes back or states a preference for low-bar, the bot keeps them on low-bar and coaches the low-bar variation. Doesn't impose high-bar. See `drill-library.md` § conditional notes.

**Out-of-scope drills** (DC-01 — back-squat-only at Comp 5 scope):

- Leg press, hack squat, belt squat. These are cited in hypertrophy literature (Israetel notes them as quad-hypertrophy assistance) but fall outside the back-squat scope of this bot. May be added in EX-07-style expansion later; out of scope for this iteration.

**Drill prescription mechanism (lives in `rules.md`, referenced here):**

The bot picks a drill from the library where:
- `fault IN detected_faults` (from pose pipeline + RP-07/RP-05)
- `hypertrophy_applicability IN (primary, secondary)` (or `conditional` if user context supports)
- `equipment_required ⊆ user_equipment` (gates against `equipment_notes` + `heel_elevation_access`)
- `contraindications ∩ user_injuries = ∅` (gates against `injury_notes` + recent `symptom_reports`)

---

## Position 6 — Volume framework *(Pick 6)*

**Locked position:** **10-20 sets/week per quad** as convergent practitioner range. Bot uses this for *answering volume questions*, does NOT autonomously prescribe weekly volume.

**Why this position:**

- **Schoenfeld, Ogborn, Krieger 2017 meta-analysis** — dose-response: >9 sets/week showed significantly greater hypertrophy than <9. Each additional set adds ~0.38%/0.24% hypertrophy at the margin. No demonstrated ceiling within studied range.
- **RP / Israetel volume landmarks** — MEV ~6-8 sets/wk, MAV 12-18 sets/wk, MRV ~22-24 sets/wk; sweet spot for large muscles 12-16.
- **Helms M&S Pyramid v2** — ideal 10-20 sets/wk per muscle group.

10-20 covers both Camp A's sweet-spot and Camp B's threshold. The bot can cite this range when asked; doesn't commit to autonomous programming.

**Scope discipline:** the bot at Comp 5 stakes does NOT have weekly volume tracking, mesocycle phase awareness, or program-level state unless the user reports it. Autonomous weekly-volume prescription would over-prescribe for already-fatigued users or under-prescribe for users on low-volume programs. This is a *reference range*, not an *RP-N progression primitive*.

---

## Distinct from strength training

| Dimension | Hypertrophy (this bot) | Strength (e.g. 5/3/1, Starting Strength) |
|---|---|---|
| Rep target | Wide band (8-12 typical, 5-30 acceptable) | Narrow target (5×5, 3×5, 5/3/1 specific reps) |
| Load increment | Smaller, gated by completing reps at RPE | Fixed micro-increments (Starting Strength: +5-10lb squat per session; 5/3/1: +10lb/cycle squat) |
| Failure proximity | RIR 0-4 acceptable | Generally further from failure (RIR 2-4) until intensity day / AMRAP |
| Tempo | Deliberate slow eccentric + bottom pause | Whatever's needed to lift the weight; tempo not prescribed |
| Depth | Bias-deeper for muscle stretch | Parallel minimum sufficient |
| Bar position | High-bar / front squat for quad bias | Low-bar for posterior chain / lockout strength |
| Drill bias | Paused, tempo, heel-elevated, front squat | Heavy back squat (often low-bar), box squat for out-of-hole, walking-out heavy holds |
| Progression scheme | Double progression + autoreg + mesocycle volume | Linear novice / 5/3/1 cycle |

**Vocabulary the bot should NOT use as primary anchor** (signals strength-coach framing, F-coach-36):
- "% 1RM" as primary anchor (acceptable as secondary reference; not as primary)
- "max effort"
- "AMRAP" (acceptable as final-set qualifier; not as primary)

Bodybuilding competition prep (contest peaking, show day, water cut etc.) IS in scope for hypertrophy framing — the user may be prepping for a physique competition. Bot reads `goals` from profile to disambiguate "competition" = bodybuilding contest vs powerlifting meet.

## Distinct from power training

Power = sub-maximal load moved fast (dynamic-effort squats, jump squats, Olympic-lifting variants). Different stimulus from hypertrophy. If a user asks about these, the bot acknowledges, notes it's a different stimulus, and redirects to hypertrophy-relevant work.

---

## Modulation pointers — user-state inputs *(DC-37 + DC-38 + DC-39)*

The positions above are the **default coach prescription**. The bot reads from `profile.md` to modulate:

- **`rep_band_preference`** (DC-37 Q2) → Position 2 baseline band; RP-07 VL/RIR mapping conditional on band.
- **`current_programme_name`** + **`current_mesocycle_phase`** (DC-37 Q1) → Position 5 progression layer; mesocycle phase modulates RIR interpretation (Position 3) — permissive at MRV, concerned at MEV.
- **`equipment_notes`** + **`heel_elevation_access`** (DC-37 Q3) → Position 4 mobility/elevation branch; Position 5 drill-library equipment filter.
- **`injury_notes`** + **`coaching_mode`** (DC-37 Q4 + DC-38) → Position 3 (RIR conservative in `injury_managing`); Position 4 (no bias-deeper); Position 5 (contraindications filter on drill prescription); generic physio recommendation surfaced.
- **`symptom_reports`** (DC-39, last 14 days OR last 5 sessions) → drill prescription weights down drills associated with recent symptoms; Pick 5 progression layer 1 pauses load increases if recent symptom on prescribed exercise.

When the user is on a programme that prescribes differently (different tempo, different rep band, different progression scheme), bot defers to the user-reported programme prescription and notes the divergence. The coach's positions above are the *default when the user has no programme-prescribed alternative* or has asked for hypertrophy-coach guidance directly.

---

## Source

Drawn from internal hypertrophy-coaching research notes. Citation magnitudes, PubMed/PMC IDs, study sample sizes + effect sizes live in the research notes. Per single-source-of-truth discipline: this file extracts positions; the research notes hold the literature digest. Citation updates land in research first, then propagate here.
