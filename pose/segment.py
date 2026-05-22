"""DC-34 rep-segmentation pre-filter -- hip-Y peak detection.

Classifies each FrameRecord as in-rep / non-rep and assigns rep-id.
Mechanism: visibility-weighted hip-Y trajectory peak detection.
Non-rep frames excluded from downstream rep-level aggregation per DC-34.

Hand-rolled peak detection (no scipy dep) -- local maxima with prominence + min-distance.

Run as module: python -m pose.segment
"""

from dataclasses import dataclass
from typing import Optional

from pose.extract import FrameRecord

# Tuning parameters -- calibrated on family corpus (see task 4 smoke test).
# At stride 5 on 30fps source = 6Hz sample rate.
MIN_REP_DISTANCE_SAMPLES = 8       # 8 samples / 6Hz = ~1.3s minimum rep spacing
MIN_PEAK_PROMINENCE = 0.05         # normalised image coords; ~5% of frame height
HALF_REP_WINDOW_FACTOR = 1.0       # fraction of half-distance-to-neighbour to call "in-rep" -- 1.0 = windows touch at midpoint, captures top-to-top of each rep (full ROM)


@dataclass
class SegmentedFrame:
    frame: FrameRecord
    in_rep: bool
    rep_id: Optional[int]
    hip_y: float


@dataclass
class SegmentationResult:
    frames: list[SegmentedFrame]
    rep_peaks: list[int]


def _hip_y(frame: FrameRecord) -> float:
    """Visibility-weighted average of hip-Y across L+R."""
    L = frame.landmarks["hip_L"]
    R = frame.landmarks["hip_R"]
    w = L.visibility + R.visibility
    if w == 0:
        return (L.y + R.y) / 2
    return (L.y * L.visibility + R.y * R.visibility) / w


def _find_peaks(signal: list[float], min_distance: int, min_prominence: float) -> list[int]:
    """Local-maxima indices, filtered by prominence then min-distance.

    Prominence is the height above the higher of the two adjacent basins (lowest
    points before encountering a taller peak on each side, or signal boundary).
    O(n^2) implementation; signal length is small (~150 samples per clip).
    """
    n = len(signal)
    if n < 3:
        return []

    candidates = [
        i for i in range(1, n - 1)
        if signal[i] >= signal[i - 1] and signal[i] >= signal[i + 1]
    ]

    kept: list[int] = []
    for i in candidates:
        left_min = signal[i]
        for j in range(i - 1, -1, -1):
            if signal[j] > signal[i]:
                break
            left_min = min(left_min, signal[j])
        right_min = signal[i]
        for j in range(i + 1, n):
            if signal[j] > signal[i]:
                break
            right_min = min(right_min, signal[j])
        prominence = signal[i] - max(left_min, right_min)
        if prominence >= min_prominence:
            kept.append(i)

    if not kept:
        return []
    kept.sort()
    out = [kept[0]]
    for idx in kept[1:]:
        if idx - out[-1] < min_distance:
            if signal[idx] > signal[out[-1]]:
                out[-1] = idx
        else:
            out.append(idx)
    return out


def segment(frames: list[FrameRecord]) -> SegmentationResult:
    """DC-34 rep segmentation via hip-Y peak detection."""
    if not frames:
        return SegmentationResult(frames=[], rep_peaks=[])

    hip_y = [_hip_y(f) for f in frames]
    peaks = _find_peaks(hip_y, MIN_REP_DISTANCE_SAMPLES, MIN_PEAK_PROMINENCE)

    n = len(frames)
    rep_for_frame: list[Optional[int]] = [None] * n
    for rep_id, peak_idx in enumerate(peaks):
        prev_peak = peaks[rep_id - 1] if rep_id > 0 else -MIN_REP_DISTANCE_SAMPLES * 2
        next_peak = peaks[rep_id + 1] if rep_id < len(peaks) - 1 else n + MIN_REP_DISTANCE_SAMPLES * 2
        left_half = (peak_idx - prev_peak) // 2
        right_half = (next_peak - peak_idx) // 2
        window_left = max(0, peak_idx - int(left_half * HALF_REP_WINDOW_FACTOR))
        window_right = min(n - 1, peak_idx + int(right_half * HALF_REP_WINDOW_FACTOR))
        for j in range(window_left, window_right + 1):
            rep_for_frame[j] = rep_id

    segmented = [
        SegmentedFrame(
            frame=f,
            in_rep=(rep_for_frame[i] is not None),
            rep_id=rep_for_frame[i],
            hip_y=hip_y[i],
        )
        for i, f in enumerate(frames)
    ]
    return SegmentationResult(frames=segmented, rep_peaks=peaks)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    from pose.extract import extract_clip

    clip = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "./samples"
    )
    model = Path(__file__).parent.parent / "models" / "pose_landmarker_full.task"
    if clip.is_dir():
        clip = next(clip.glob("*.mp4"))
    metadata, frames = extract_clip(clip, model)
    result = segment(frames)
    in_rep_count = sum(1 for f in result.frames if f.in_rep)
    print(f"{metadata.name}: {len(frames)} sampled frames -> {len(result.rep_peaks)} reps detected, {in_rep_count} in-rep frames")
    for rep_id, peak_idx in enumerate(result.rep_peaks):
        sf = result.frames[peak_idx]
        print(f"  Rep {rep_id}: peak at ts={sf.frame.timestamp_s:.2f}s (frame {sf.frame.frame_idx}), hip_y={sf.hip_y:.3f}, knee_L={sf.frame.angles['knee_L']:.1f}deg")
