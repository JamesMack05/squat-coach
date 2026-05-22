# pose/ — MediaPipe pose-extraction pipeline

Video → 33-landmark pose data → joint angles → structured output for Claude reasoning.

## API note — IMPORTANT

Uses **MediaPipe Tasks API** (`mp.tasks.python.vision.PoseLandmarker`), NOT the legacy `mp.solutions.pose` API. The legacy API was removed in MediaPipe 0.10+; reaching for it from old tutorials gives `AttributeError: module 'mediapipe' has no attribute 'solutions'`.

Reference docs: https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker

## Model

`models/pose_landmarker_full.task` (~9MB) — downloaded by setup. Source URL:
`https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task`

Model file is gitignored (large binary).

## Smoke tests (validation)

Three validation runs on Python 3.13 + MediaPipe 0.10.35:

| Clip class | Resolution / fps | Duration | Detection rate | Notes |
|---|---|---|---|---|
| Vintage PR back squat (640×360, 2010 era) | 640×360 @ 30 | 26s | 96% (150/157) | Camera on lifter's **right** side. Right joints 0.93-0.99, left knee/ankle 0.50/0.68 (LOW). Right-knee ROM 35° → 180°. |
| 31-rep continuous 140kg back squat | 1920×1080 @ 60 | 180s | 98% (2106/2159) | Camera on lifter's **left** side. Left joints 0.95-0.99, right knee/ankle 0.51/0.70. Left-knee ROM 5.3° → 180° **(5.3° reading is from a post-workout collapse frame at 168.5s, not real flexion — see DC-34 below)**. Processing 78s on CPU = 0.43× real-time. |
| Personal test corpus (N=10 clips, 3 anonymous subjects) | 1080×1920 portrait @ 30 | 21-32s each | **100% across all 10** | All camera-left consistently. Near-side vis 0.93-0.98; far-side 0.61-0.70 (confirmed across N=10). Processing 0.35-0.40× RT at 30fps. |

## Form-pattern validation — N=3 distinct subjects

The personal test corpus produced three distinct form signatures, all visually corroborated independently:

| Subject | Joint-angle signature | Form pattern |
|---|---|---|
| A | 46-51° → 180° | Full lockout + deep-parallel depth |
| B | 47-56° → **157-168°** | **Non-lockout** + deep-parallel depth |
| C | **29-34°** → 180° | Full lockout + **ATG depth** |

**What this validates:** the signal path *video → pose extraction → joint angles → distinguishable form patterns* works at N=3. The pipeline captures form variation BETWEEN subjects in a way that matches what a domain expert would say after watching the videos.

**What this does NOT validate:** that the bot's downstream Claude-reasoning layer derives these findings from pose data without explicit prompting; that subtler issues a casual review would miss are catchable; that the pipeline generalises beyond same-location filming conditions.

## Architectural locks

8 architectural locks shaped the Stage 4 build (DC-33 resolved into DC-34):

| DC | Headline | Trigger point |
|---|---|---|
| **DC-29** | Pose pipeline detects near-side DYNAMICALLY per clip — refined per-rep with modal aggregation + tripod-nudge flag | extract+aggregate boundary |
| **DC-30** | Far-side visibility threshold = 0.7; below → "insufficient data," excluded from symmetry analysis | aggregate.py |
| **DC-31** | Resolution floor (≥480p) enforced at bot ingestion — NOT in pose/ | Stage 5 bot ingest validator |
| **DC-32** | Bot UX response-time budget = 20-30s end-to-end on CPU; GPU deferred | Stage 4-5 architecture |
| **DC-33** | ~~Extreme-flexion sanity-check~~ — superseded by DC-34 | (resolved) |
| **DC-34** | Rep-segmentation pre-filter required — mechanism = hip-Y peak detection (stride 5) | segment.py |
| **DC-35** | Output = JSON artefact + markdown render; per-frame data stays out of Claude's prompt | output.py |
| **DC-36** | 4-file module split: extract / segment / aggregate / output | pose/ structure |

DC-34 (rep-segmentation, hip-Y peak detection at stride 5) sequences first; DC-29 (per-rep near-side) and DC-30 (far-side gate) run inside aggregation; DC-35 (output format) and DC-36 (4-file split) shape the module structure.

## Stage 4 status — built + validated

- [x] `extract.py` — MediaPipe Tasks-API runner + bilateral hip/knee/ankle angle computation.
- [x] `segment.py` — DC-34 hip-Y peak detection → in-rep/non-rep + rep-id grouping (hand-rolled peak finder, no scipy dep).
- [x] `aggregate.py` — DC-29 per-rep near-side (modal aggregation) + DC-30 far-side gate at 0.7 + RP-07 fatigue signature (research-grounded: concentric velocity loss + depth/ROM change + max hip-shoulder ratio; knee valgus deliberately excluded per MediaPipe FPPA noise).
- [x] `output.py` — DC-35 dual format: JSON envelope (full data) + markdown render (per-rep + per-clip only, ~2.5KB per clip).
- [x] `__init__.py` — entry point `analyze_video(path) → ClipEnvelope`.
- [x] `../setup.py` — idempotent download of `pose_landmarker_full.task` into `models/`.
- [x] End-to-end validation: 10 personal-corpus clips + 8 YouTube clips processed cleanly. Personal-corpus rep counts 9-13 match expected hypertrophy sets; near-side all L; no tripod nudges. YouTube edge cases (compilation videos, very short clips) handled gracefully (FatigueSignature = None below 2 reps).

Stride 5 locked per DC-34. Resolution check (DC-31) is Stage 5 bot-ingest, NOT in pose/.
