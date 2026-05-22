"""pose -- back-squat coaching pose extraction pipeline.

Public API:
    from pose import analyze_video, to_json, to_markdown

    envelope = analyze_video(Path("clip.mp4"))
    json_blob = to_json(envelope)
    markdown_for_prompt = to_markdown(envelope)

Pipeline: MediaPipe pose extraction (DC-29/30) -> hip-Y rep segmentation (DC-34)
-> per-rep aggregation -> dual JSON+markdown output (DC-35). 4-file module split (DC-36).
"""

from pathlib import Path

from pose.aggregate import (
    ClipEnvelope, RepAggregate, SideAggregate, JointAggregate, FatigueSignature,
    aggregate,
)
from pose.extract import extract_clip, FrameRecord, Landmark, ClipMetadata
from pose.output import to_json, to_markdown
from pose.segment import segment, SegmentedFrame, SegmentationResult

DEFAULT_MODEL = Path(__file__).parent.parent / "models" / "pose_landmarker_full.task"


def analyze_video(clip_path: Path, model_path: Path = DEFAULT_MODEL) -> ClipEnvelope:
    """Full pipeline: video -> MediaPipe pose -> rep segmentation -> per-rep + per-clip envelope.

    Per DC-36, the module decomposes as: extract -> segment -> aggregate -> output.
    This function chains the first three; output (to_json / to_markdown) is the caller's choice.
    """
    metadata, frames = extract_clip(clip_path, model_path)
    seg = segment(frames)
    return aggregate(metadata, seg)


__all__ = [
    "analyze_video",
    "to_json",
    "to_markdown",
    "ClipEnvelope",
    "RepAggregate",
    "SideAggregate",
    "JointAggregate",
    "FatigueSignature",
    "FrameRecord",
    "Landmark",
    "SegmentedFrame",
    "SegmentationResult",
    "ClipMetadata",
]
