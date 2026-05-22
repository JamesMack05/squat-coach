"""Per-rep + per-clip aggregation.

DC-29: per-rep near-side detection via mean landmark visibility (shoulder + hip + knee + ankle);
       per-clip near-side is the modal value across reps; tripod_nudge_detected flags disagreement.
DC-30: far-side joints used for symmetry analysis only when far-side mean visibility >= 0.7.
RP-07: fatigue signature -- STUB per task 5a; task 10 (5b) fills in after research lands.

Run as module: python -m pose.aggregate
"""

from collections import Counter
from dataclasses import dataclass
from statistics import mean
from typing import Optional

from pose.extract import ClipMetadata
from pose.segment import SegmentationResult, SegmentedFrame

FAR_SIDE_VISIBILITY_THRESHOLD = 0.7  # DC-30

KEY_LANDMARKS_BY_SIDE = {
    "L": ["shoulder_L", "hip_L", "knee_L", "ankle_L"],
    "R": ["shoulder_R", "hip_R", "knee_R", "ankle_R"],
}


@dataclass
class JointAggregate:
    min: Optional[float]
    max: Optional[float]
    rom: Optional[float]


@dataclass
class SideAggregate:
    mean_visibility: float
    hip: JointAggregate
    knee: JointAggregate
    ankle: JointAggregate


@dataclass
class FatigueSignature:
    """RP-07 multi-rep fatigue signature.

    Reports magnitude + direction; the bot's coaching layer interprets given
    lifter context (intent, load).

    Literature anchors (Pareja-Blanco et al.):
      - <10% concentric velocity loss = fresh
      - ~20% VL = sweet spot for hypertrophy
      - ~30% VL = moderate fatigue
      - ~40-50% VL = near failure

    Caveats baked into the schema:
      - Knee valgus is NOT computed. MediaPipe FPPA noise (~19 deg) dominates the
        plausible 5-15 deg signal per research §3.6. Adding it would be theatre.
      - Cannot disambiguate fatigue from intentional tempo variation (slow eccentric
        per Pearson 2024, pauses per Israetel) without knowing the prescribed tempo.
      - depth_change_deg sign carries regime info: positive = depth grew (lab regime,
        loss of eccentric control under light load); negative = depth compressed
        (coaching regime, lifter cheats depth under heavy load).
      - Velocity is computed peak -> ascent end, where ascent end is detected via
        _find_ascent_end_idx (frame where lifter returns near pre-rep standing
        baseline). NOT rep_frames[-1] -- the segmenter's final-rep window extends
        past the actual rep, and the previous rep_frames[-1] definition inflated VL
        catastrophically (a calibration empty-bar set read VL=81.5% pre-fix, -8.1% post-fix).
    """
    concentric_velocity_loss_pct: Optional[float]   # primary VBT-style signal
    depth_change_deg: Optional[float]                # last_rep knee min - first_rep knee min
    rom_change_deg: Optional[float]                  # last_rep knee ROM - first_rep knee ROM
    max_hip_shoulder_ratio: Optional[float]          # peak hip-Y/shoulder-Y rise ratio across reps; >1.0 = hip-led good-morning shift


@dataclass
class RepAggregate:
    rep_id: int
    start_ts: float
    peak_ts: float
    end_ts: float
    frame_count: int
    near_side: str
    far_side_usable: bool
    near: SideAggregate
    far: SideAggregate
    concentric_hip_velocity: Optional[float] = None              # RP-07: hip-Y units/sec during ascent (peak -> rep end)
    hip_shoulder_concentric_velocity_ratio: Optional[float] = None  # RP-07: >1.0 = hip-led good-morning shift


@dataclass
class ClipEnvelope:
    clip_name: str
    width: int
    height: int
    fps: float
    duration_s: float
    total_reps: int
    near_side_modal: str
    tripod_nudge_detected: bool
    reps: list[RepAggregate]
    frames: list[SegmentedFrame]  # DC-35: per-frame data preserved in JSON; markdown render omits
    rp07_fatigue_signature: Optional[FatigueSignature] = None


def _joint_aggregate(angles: list[Optional[float]]) -> JointAggregate:
    clean = [a for a in angles if a is not None]
    if not clean:
        return JointAggregate(min=None, max=None, rom=None)
    return JointAggregate(min=min(clean), max=max(clean), rom=max(clean) - min(clean))


def _side_aggregate(rep_frames: list[SegmentedFrame], side: str) -> SideAggregate:
    key_lms = KEY_LANDMARKS_BY_SIDE[side]
    vis_values = [
        mean(sf.frame.landmarks[lm].visibility for lm in key_lms)
        for sf in rep_frames
    ]
    return SideAggregate(
        mean_visibility=mean(vis_values),
        hip=_joint_aggregate([sf.frame.angles[f"hip_{side}"] for sf in rep_frames]),
        knee=_joint_aggregate([sf.frame.angles[f"knee_{side}"] for sf in rep_frames]),
        ankle=_joint_aggregate([sf.frame.angles[f"ankle_{side}"] for sf in rep_frames]),
    )


ASCENT_END_THRESHOLD_FRAC = 0.15


def _find_ascent_end_idx(rep_frames: list[SegmentedFrame], peak_idx: int) -> Optional[int]:
    """First frame index post-peak where hip_y returns to within ASCENT_END_THRESHOLD_FRAC
    of the pre-rep standing baseline. Returns None if the rep does not complete.

    Why: segment.py groups frames between successive peaks; the final rep's group
    extends to end of video. Using rep_frames[-1] as "rep end" therefore either
    (a) overshoots dt when standing-still time follows the rep, or
    (b) cuts off mid-ascent when the video ends before lockout.
    Both inflate concentric_velocity_loss_pct spuriously (caught during calibration
    on an empty-bar set that read VL=81.5%; the final rep had end_hip_y=0.6039 vs
    prior reps' median 0.495 because the video cut mid-ascent).
    """
    if peak_idx < 1 or peak_idx >= len(rep_frames) - 1:
        return None
    pre_peak_min = min(rep_frames[i].hip_y for i in range(peak_idx))
    peak_hip_y = rep_frames[peak_idx].hip_y
    if peak_hip_y <= pre_peak_min:
        return None
    threshold = pre_peak_min + ASCENT_END_THRESHOLD_FRAC * (peak_hip_y - pre_peak_min)
    for i in range(peak_idx + 1, len(rep_frames)):
        if rep_frames[i].hip_y <= threshold:
            return i
    return None


def _concentric_hip_velocity(rep_frames: list[SegmentedFrame], peak_idx: int) -> Optional[float]:
    """Hip-Y velocity during ascent phase (peak -> ascent end). Proxy for bar velocity.

    Larger value = faster concentric. Rep-over-rep decline is the primary VBT-style
    fatigue signal per research §3.4. Ascent end defined via _find_ascent_end_idx.
    """
    end_idx = _find_ascent_end_idx(rep_frames, peak_idx)
    if end_idx is None:
        return None
    peak = rep_frames[peak_idx]
    end = rep_frames[end_idx]
    dt = end.frame.timestamp_s - peak.frame.timestamp_s
    if dt <= 0:
        return None
    dy = peak.hip_y - end.hip_y
    return dy / dt if dy > 0 else 0.0


def _hip_shoulder_velocity_ratio(rep_frames: list[SegmentedFrame], peak_idx: int, near_side: str) -> Optional[float]:
    """Hip rise speed / shoulder rise speed during concentric.

    > 1.0 = hip rises faster than shoulder = "good morning" shift (research §3.3).

    Returns None when shoulder displacement is below MediaPipe noise floor (~0.5% of
    frame height) -- ratio becomes meaningless / explodes near zero. Empirically
    needed for YouTube-compilation edge cases (single rep, partial visibility, etc.).
    Ascent end defined via _find_ascent_end_idx (same v1 fix as _concentric_hip_velocity).
    """
    end_idx = _find_ascent_end_idx(rep_frames, peak_idx)
    if end_idx is None:
        return None
    MIN_DY = 0.005
    peak = rep_frames[peak_idx]
    end = rep_frames[end_idx]
    hip_lm = f"hip_{near_side}"
    shoulder_lm = f"shoulder_{near_side}"
    hip_dy = peak.frame.landmarks[hip_lm].y - end.frame.landmarks[hip_lm].y
    shoulder_dy = peak.frame.landmarks[shoulder_lm].y - end.frame.landmarks[shoulder_lm].y
    if hip_dy < MIN_DY or shoulder_dy < MIN_DY:
        return None
    return hip_dy / shoulder_dy


def _aggregate_rep(rep_id: int, rep_frames: list[SegmentedFrame]) -> RepAggregate:
    L = _side_aggregate(rep_frames, "L")
    R = _side_aggregate(rep_frames, "R")
    near_side = "L" if L.mean_visibility > R.mean_visibility else "R"
    near, far = (L, R) if near_side == "L" else (R, L)
    far_side_usable = far.mean_visibility >= FAR_SIDE_VISIBILITY_THRESHOLD

    peak_idx = max(range(len(rep_frames)), key=lambda i: rep_frames[i].hip_y)
    return RepAggregate(
        rep_id=rep_id,
        start_ts=rep_frames[0].frame.timestamp_s,
        peak_ts=rep_frames[peak_idx].frame.timestamp_s,
        end_ts=rep_frames[-1].frame.timestamp_s,
        frame_count=len(rep_frames),
        near_side=near_side,
        far_side_usable=far_side_usable,
        near=near,
        far=far,
        concentric_hip_velocity=_concentric_hip_velocity(rep_frames, peak_idx),
        hip_shoulder_concentric_velocity_ratio=_hip_shoulder_velocity_ratio(rep_frames, peak_idx, near_side),
    )


def _compute_fatigue_signature(reps: list[RepAggregate]) -> Optional[FatigueSignature]:
    """RP-07 across-set fatigue signature. None if <2 reps (no rep-over-rep signal).

    VL computed across first / last reps with non-None concentric_hip_velocity — i.e.,
    reps where _find_ascent_end_idx detected ascent completion. Incomplete reps (video
    cut mid-ascent or rep didn't reach standing) are skipped, not folded in as garbage.
    """
    if len(reps) < 2:
        return None
    first, last = reps[0], reps[-1]

    complete_reps = [r for r in reps if r.concentric_hip_velocity is not None]
    vl_pct = None
    if (len(complete_reps) >= 2
            and complete_reps[0].concentric_hip_velocity > 0):
        v_first = complete_reps[0].concentric_hip_velocity
        v_last = complete_reps[-1].concentric_hip_velocity
        vl_pct = (v_first - v_last) / v_first * 100

    depth_change = None
    if first.near.knee.min is not None and last.near.knee.min is not None:
        # Knee min DECREASES as lifter goes deeper. Flip so positive = depth grew.
        depth_change = first.near.knee.min - last.near.knee.min

    rom_change = None
    if first.near.knee.rom is not None and last.near.knee.rom is not None:
        rom_change = last.near.knee.rom - first.near.knee.rom

    ratios = [r.hip_shoulder_concentric_velocity_ratio for r in reps
              if r.hip_shoulder_concentric_velocity_ratio is not None]
    max_ratio = max(ratios) if ratios else None

    return FatigueSignature(
        concentric_velocity_loss_pct=vl_pct,
        depth_change_deg=depth_change,
        rom_change_deg=rom_change,
        max_hip_shoulder_ratio=max_ratio,
    )


def aggregate(metadata: ClipMetadata, segmentation: SegmentationResult) -> ClipEnvelope:
    by_rep: dict[int, list[SegmentedFrame]] = {}
    for sf in segmentation.frames:
        if sf.in_rep and sf.rep_id is not None:
            by_rep.setdefault(sf.rep_id, []).append(sf)

    reps = [_aggregate_rep(rep_id, by_rep[rep_id]) for rep_id in sorted(by_rep.keys())]

    if not reps:
        return ClipEnvelope(
            clip_name=metadata.name, width=metadata.width, height=metadata.height,
            fps=metadata.fps, duration_s=metadata.duration_s, total_reps=0,
            near_side_modal="L", tripod_nudge_detected=False, reps=[],
            frames=segmentation.frames,
        )

    sides = [r.near_side for r in reps]
    near_side_modal = Counter(sides).most_common(1)[0][0]
    tripod_nudge_detected = len(set(sides)) > 1

    return ClipEnvelope(
        clip_name=metadata.name,
        width=metadata.width, height=metadata.height,
        fps=metadata.fps, duration_s=metadata.duration_s,
        total_reps=len(reps),
        near_side_modal=near_side_modal,
        tripod_nudge_detected=tripod_nudge_detected,
        reps=reps,
        frames=segmentation.frames,
        rp07_fatigue_signature=_compute_fatigue_signature(reps),
    )


if __name__ == "__main__":
    import sys
    from pathlib import Path
    from pose.extract import extract_clip
    from pose.segment import segment

    clip = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "./samples"
    )
    model = Path(__file__).parent.parent / "models" / "pose_landmarker_full.task"
    if clip.is_dir():
        clip = next(clip.glob("*.mp4"))
    metadata, frames = extract_clip(clip, model)
    seg = segment(frames)
    env = aggregate(metadata, seg)
    print(f"{env.clip_name}: {env.total_reps} reps; near-side modal={env.near_side_modal}; tripod_nudge={env.tripod_nudge_detected}")
    for r in env.reps:
        print(f"  Rep {r.rep_id} ({r.start_ts:.1f}-{r.end_ts:.1f}s, peak {r.peak_ts:.2f}s, n={r.frame_count}):")
        print(f"    near={r.near_side} vis={r.near.mean_visibility:.3f}; far_usable={r.far_side_usable} vis={r.far.mean_visibility:.3f}")
        knee_min = f"{r.near.knee.min:.1f}" if r.near.knee.min is not None else "--"
        knee_max = f"{r.near.knee.max:.1f}" if r.near.knee.max is not None else "--"
        knee_rom = f"{r.near.knee.rom:.1f}" if r.near.knee.rom is not None else "--"
        print(f"    near knee: min={knee_min} max={knee_max} ROM={knee_rom}deg")
