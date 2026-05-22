---
file-class: content
locked-by: DC-26
---

# reference/ — content

Drill library, hypertrophy operationalisation, narrated-rep cue vocabulary, progression-protocol references. Built as pluggable content the system-prompt template consumes (DC-21). All four files are stitched into Claude's system prompt by `bot/prompt.py` on every turn.

## Files

| File | Role |
|---|---|
| `drill-library.md` | Tagged lookup table (DC-28) — drill name + faults addressed (tagged) + hypertrophy applicability tag + prescription text + contraindications. Coaching logic references "prescribe one drill tagged with detected fault"; does not enumerate inline. Canonical for the drill prescription pool. |
| `hypertrophy-ops.md` | Hypertrophy operationalisation (DC-11) — RIR / RPE targets, depth / tempo / drill-bias distinct from strength or power training. Feeds rules.md RP-02 (progression gating) + RP-07 (fatigue prescription). |
| `narrated-rep.md` | Narrated cue-voice content (DC-23 axis 3) — anchors the coach's cue vocabulary for rep-level coaching. Sits alongside RP-06 voice anchor. |
| `progression-protocol.md` | Load-progression rubric — three-layer scheme (double-progression → autoreg → mesocycle). Referenced by rules.md RP-02. |

## File-class discipline

Content only — drill prose, references, examples. Behaviour clauses live in `rules.md`, NOT here. Reference is consumed BY rules; reference does not contain rules.
