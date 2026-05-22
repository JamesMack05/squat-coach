"""DC-35 dual-format output: JSON (full data) + markdown (Claude prompt render).

JSON preserves per-frame landmarks + visibility + joint angles + in-rep + rep-id
+ per-rep aggregates + per-clip metadata. For programmatic re-consumption by bot/,
eval-fixture diffability, schema-evolution flexibility.

Markdown renders per-rep + per-clip envelope only. Per-frame data is NOT rendered
into markdown -- it would bloat Claude's context with ~150-2000 frames per clip;
Claude reasons over reps, not frames.

Run as module (full pipeline demo): python -m pose.output
"""

import json
from dataclasses import asdict
from io import StringIO
from typing import Optional

from pose.aggregate import ClipEnvelope, RepAggregate


def _fmt(v: Optional[float], precision: int = 1) -> str:
    return f"{v:.{precision}f}" if v is not None else "—"


def to_json(envelope: ClipEnvelope, indent: int = 2) -> str:
    """Full envelope (per-frame + per-rep + per-clip) as JSON string."""
    return json.dumps(asdict(envelope), indent=indent)


def _rep_row(r: RepAggregate) -> str:
    sym = "—"
    if r.far_side_usable and r.near.knee.min is not None and r.far.knee.min is not None:
        sym = f"{r.near.knee.min - r.far.knee.min:+.1f}"
    return (
        f"| {r.rep_id} | {r.start_ts:.1f}–{r.end_ts:.1f}s (peak {r.peak_ts:.2f}) | {r.frame_count} | "
        f"{r.near_side} ({r.near.mean_visibility:.2f}) | "
        f"{'yes' if r.far_side_usable else 'no'} ({r.far.mean_visibility:.2f}) | "
        f"{_fmt(r.near.knee.min)} / {_fmt(r.near.knee.max)} / {_fmt(r.near.knee.rom)} | "
        f"{_fmt(r.near.hip.rom)} | {_fmt(r.near.ankle.rom)} | {sym} |"
    )


def to_markdown(envelope: ClipEnvelope) -> str:
    """Per-rep + per-clip render for Claude prompt. Excludes per-frame data."""
    buf = StringIO()
    buf.write(f"# Clip: {envelope.clip_name}\n\n")
    buf.write(f"{envelope.width}×{envelope.height} @ {envelope.fps:.1f}fps, {envelope.duration_s:.1f}s\n\n")
    buf.write(f"**Reps:** {envelope.total_reps}; **near-side:** {envelope.near_side_modal} (modal); ")
    buf.write(f"**tripod nudge:** {'detected' if envelope.tripod_nudge_detected else 'no'}\n\n")

    if not envelope.reps:
        buf.write("_No reps detected._\n")
        return buf.getvalue()

    buf.write("## Per-rep summary\n\n")
    buf.write("Columns: knee min = depth-bottom; knee max = standing extension; ROM = max − min. ")
    buf.write("L−R knee min Δ shows side asymmetry only when far-side is usable (DC-30 visibility ≥ 0.7).\n\n")
    buf.write("| Rep | Time (peak) | Frames | Near (vis) | Far usable (vis) | "
              "Knee min/max/ROM (°) | Hip ROM (°) | Ankle ROM (°) | L−R knee min Δ (°) |\n")
    buf.write("|---|---|---|---|---|---|---|---|---|\n")
    for r in envelope.reps:
        buf.write(_rep_row(r) + "\n")

    buf.write("\n## Fatigue signature (RP-07)\n\n")
    fs = envelope.rp07_fatigue_signature
    if fs is None:
        buf.write("_Fewer than 2 reps — no rep-over-rep signal._\n")
    else:
        buf.write("Reference anchors (Pareja-Blanco et al.): <10% velocity loss = fresh; ~20% = sweet spot; ~30% = moderate fatigue; ~40-50% = near failure.\n\n")
        buf.write(f"- **Concentric velocity loss:** {_fmt(fs.concentric_velocity_loss_pct)}% (first→last rep)\n")
        buf.write(f"- **Depth change (knee min):** {_fmt(fs.depth_change_deg)}° "
                  f"(positive = depth grew across set; negative = depth compressed)\n")
        buf.write(f"- **ROM change (knee):** {_fmt(fs.rom_change_deg)}°\n")
        buf.write(f"- **Max hip-shoulder rise ratio:** {_fmt(fs.max_hip_shoulder_ratio, 2)} "
                  f"(>1.0 indicates hip-led 'good-morning' shift; literature has no firm threshold)\n\n")
        buf.write("### Per-rep concentric metrics\n\n")
        buf.write("| Rep | Concentric hip velocity (y-units/s) | Hip-shoulder rise ratio |\n")
        buf.write("|---|---|---|\n")
        for r in envelope.reps:
            buf.write(f"| {r.rep_id} | {_fmt(r.concentric_hip_velocity, 3)} | {_fmt(r.hip_shoulder_concentric_velocity_ratio, 2)} |\n")
        buf.write("\n_Caveats: (1) knee valgus is deliberately not computed — MediaPipe FPPA noise (~19°) dominates plausible signal (5-15°). "
                  "(2) Cannot disambiguate from intentional tempo variation (slow eccentric, programmed pauses) without knowing prescribed tempo._\n")

    return buf.getvalue()


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.stdout.reconfigure(encoding="utf-8")
    from pose.extract import extract_clip
    from pose.segment import segment
    from pose.aggregate import aggregate

    clip = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "./samples"
    )
    model = Path(__file__).parent.parent / "models" / "pose_landmarker_full.task"
    if clip.is_dir():
        clip = next(clip.glob("*.mp4"))

    metadata, frames = extract_clip(clip, model)
    seg = segment(frames)
    env = aggregate(metadata, seg)

    json_str = to_json(env)
    md_str = to_markdown(env)

    out_dir = Path(__file__).parent.parent / "output-demo"
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"{clip.stem}.json").write_text(json_str, encoding="utf-8")
    (out_dir / f"{clip.stem}.md").write_text(md_str, encoding="utf-8")
    print(f"JSON: {out_dir / (clip.stem + '.json')}  ({len(json_str):,} bytes)")
    print(f"MD:   {out_dir / (clip.stem + '.md')}    ({len(md_str):,} bytes)")
    print("\n--- Markdown render ---\n")
    print(md_str)
