"""MediaPipe Tasks-API pose extraction -> per-frame landmark + joint-angle records.

Pure extraction. Stride 5 locked (DC-34 implementation note). Joint set: bilateral
hip / knee / ankle (DC-36), extensible by adding to JOINT_TRIPLETS below.
"""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

STRIDE = 5

LANDMARK_INDEX = {
    "shoulder_L": 11, "shoulder_R": 12,
    "hip_L":      23, "hip_R":      24,
    "knee_L":     25, "knee_R":     26,
    "ankle_L":    27, "ankle_R":    28,
    "foot_L":     31, "foot_R":     32,
}

JOINT_TRIPLETS = {
    "hip_L":   ("shoulder_L", "hip_L",   "knee_L"),
    "hip_R":   ("shoulder_R", "hip_R",   "knee_R"),
    "knee_L":  ("hip_L",      "knee_L",  "ankle_L"),
    "knee_R":  ("hip_R",      "knee_R",  "ankle_R"),
    "ankle_L": ("knee_L",     "ankle_L", "foot_L"),
    "ankle_R": ("knee_R",     "ankle_R", "foot_R"),
}


@dataclass
class Landmark:
    x: float
    y: float
    z: float
    visibility: float


@dataclass
class FrameRecord:
    frame_idx: int
    timestamp_s: float
    landmarks: dict[str, Landmark]
    angles: dict[str, Optional[float]]


@dataclass
class ClipMetadata:
    name: str
    width: int
    height: int
    fps: float
    duration_s: float
    total_frames: int


def angle_deg(a: Landmark, b: Landmark, c: Landmark) -> Optional[float]:
    """Angle at b formed by rays b->a and b->c, in degrees (2D x,y)."""
    v1 = (a.x - b.x, a.y - b.y)
    v2 = (c.x - b.x, c.y - b.y)
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag = math.hypot(*v1) * math.hypot(*v2)
    if mag == 0:
        return None
    return math.degrees(math.acos(max(-1.0, min(1.0, dot / mag))))


def _to_landmark(mp_lm) -> Landmark:
    return Landmark(x=mp_lm.x, y=mp_lm.y, z=mp_lm.z, visibility=mp_lm.visibility)


def extract_clip(clip_path: Path, model_path: Path, stride: int = STRIDE) -> tuple[ClipMetadata, list[FrameRecord]]:
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}. Run setup.py first.")
    if not clip_path.exists():
        raise FileNotFoundError(f"Clip not found: {clip_path}")

    cap = cv2.VideoCapture(str(clip_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    metadata = ClipMetadata(
        name=clip_path.name,
        width=width, height=height, fps=fps,
        duration_s=total_frames / fps,
        total_frames=total_frames,
    )

    options = mp_vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(model_path)),
        running_mode=mp_vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
        output_segmentation_masks=False,
    )

    records: list[FrameRecord] = []
    with mp_vision.PoseLandmarker.create_from_options(options) as detector:
        frame_idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_idx % stride == 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                ts_ms = int((frame_idx / fps) * 1000)
                result = detector.detect_for_video(mp_image, ts_ms)
                if result.pose_landmarks:
                    lms = result.pose_landmarks[0]
                    landmarks = {
                        name: _to_landmark(lms[idx])
                        for name, idx in LANDMARK_INDEX.items()
                    }
                    angles = {
                        joint: angle_deg(landmarks[p], landmarks[v], landmarks[d])
                        for joint, (p, v, d) in JOINT_TRIPLETS.items()
                    }
                    records.append(FrameRecord(
                        frame_idx=frame_idx,
                        timestamp_s=frame_idx / fps,
                        landmarks=landmarks,
                        angles=angles,
                    ))
            frame_idx += 1
    cap.release()
    return metadata, records


if __name__ == "__main__":
    import sys
    clip = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "./samples"
    )
    model = Path(__file__).parent.parent / "models" / "pose_landmarker_full.task"
    if clip.is_dir():
        clip = next(clip.glob("*.mp4"))
    metadata, records = extract_clip(clip, model)
    print(f"{metadata.name}: {metadata.width}x{metadata.height} @ {metadata.fps:.1f}fps, {metadata.duration_s:.1f}s")
    print(f"Extracted {len(records)} frame records (every {STRIDE}th frame)")
    if records:
        last = records[-1]
        print(f"Last frame: idx={last.frame_idx}, ts={last.timestamp_s:.2f}s")
        print(f"  knee_L angle: {last.angles['knee_L']:.1f}deg" if last.angles['knee_L'] else "  knee_L: None")
        print(f"  hip_L visibility: {last.landmarks['hip_L'].visibility:.3f}")
