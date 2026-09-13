"""``flags_for_review.md`` -- monitor-only and detector-only flags for hand review.

SPEC section 6 asks for 20 monitor-only flags and 10 detector-only flags, each with
the run id, the evidence, and a one-line context.  Plan section 6 phase 6 hand-reviews
exactly these.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from analysis.load import parse_batch_id

__all__ = ["collect_flags", "write_flags_md", "N_MONITOR_ONLY", "N_DETECTOR_ONLY"]

N_MONITOR_ONLY = 20
N_DETECTOR_ONLY = 10


def _one_line(s, limit: int = 160) -> str:
    s = "" if s is None else str(s)
    s = " ".join(s.split())
    return s if len(s) <= limit else s[: limit - 1] + "…"


def _detector_evidence(rec: dict) -> str:
    det = rec.get("detectors") or {}
    parts = []
    for e in (det.get("evidence") or [])[:3]:
        sub = f"({e.get('sub')})" if e.get("sub") else ""
        turn = f" turn {e['turn']}" if e.get("turn") is not None else ""
        parts.append(f"{e.get('detector')}{sub}{turn}: {_one_line(e.get('detail'), 140)}")
    return " | ".join(parts) if parts else "(no evidence recorded)"


def _fired(rec: dict) -> str:
    det = rec.get("detectors") or {}
    return "+".join(d for d in ("D1", "D2", "D3", "D4", "D5") if det.get(d)) or "none"


def _context(rec: dict) -> str:
    kind = "impossible" if rec.get("is_impossible") else "solvable"
    mutation = f"/{rec['mutation']}" if rec.get("mutation") else ""
    f = rec.get("f_realised")
    return (
        f"{rec.get('model')} | arm {rec.get('arm')} | f={f} | pos {rec.get('position')} "
        f"(impossible seen before: {rec.get('n_impossible_before')}) | "
        f"{rec.get('task_id')} [{kind}{mutation}] | outcome {rec.get('outcome')}"
    )


def _iter_records(runs_dir: Path):
    for items_path in sorted(runs_dir.glob("*/items.jsonl")):
        batch_id = items_path.parent.name
        with items_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                rec.setdefault("batch_id", batch_id)
                yield rec


def _round_robin(items: list[dict], key: str, limit: int) -> list[dict]:
    """Deterministic, diversity-preserving pick: cycle over ``key`` groups."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for it in sorted(items, key=lambda r: str(r.get("run_id"))):
        groups[str(it.get(key))].append(it)
    out: list[dict] = []
    order = sorted(groups)
    i = 0
    while len(out) < limit and any(groups[g] for g in order):
        g = order[i % len(order)]
        if groups[g]:
            out.append(groups[g].pop(0))
        i += 1
    return out


def collect_flags(runs_dir: str | Path) -> dict:
    """Split every rated item-run into the two disagreement cells."""
    runs_dir = Path(runs_dir)
    monitor_only: list[dict] = []
    detector_only: list[dict] = []
    both = 0
    neither = 0
    unrated = 0

    for rec in _iter_records(runs_dir):
        det = rec.get("detectors")
        if not isinstance(det, dict):
            continue
        mon = rec.get("monitor") or {}
        mc = mon.get("cheated")
        if mc is None:
            unrated += 1
            continue
        d = bool(det.get("cheat"))
        m = bool(mc)
        rec["_model_slug"] = parse_batch_id(rec.get("batch_id", ""))["model_slug"]
        if m and not d:
            monitor_only.append(rec)
        elif d and not m:
            detector_only.append(rec)
        elif d and m:
            both += 1
        else:
            neither += 1

    return {
        "monitor_only": monitor_only,
        "detector_only": detector_only,
        "n_monitor_only": len(monitor_only),
        "n_detector_only": len(detector_only),
        "n_both": both,
        "n_neither": neither,
        "n_unrated": unrated,
    }


def write_flags_md(
    runs_dir: str | Path,
    out_dir: str | Path,
    n_monitor_only: int = N_MONITOR_ONLY,
    n_detector_only: int = N_DETECTOR_ONLY,
) -> Path:
    flags = collect_flags(runs_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "flags_for_review.md"

    lines: list[str] = []
    lines.append("# Flags for hand review")
    lines.append("")
    lines.append(
        "The two disagreement cells between the programmatic detector (SPEC section 4) and the "
        "LLM monitor (SPEC section 5). The detector is the primary DV; the monitor is the "
        "AISI-comparable secondary and a lower bound by construction. Nothing here changes a "
        "recorded outcome -- write the verdict in the **Reviewer** column and leave the data alone."
    )
    lines.append("")
    lines.append(
        f"Counts over every rated item-run: both {flags['n_both']} | "
        f"detector only {flags['n_detector_only']} | monitor only {flags['n_monitor_only']} | "
        f"neither {flags['n_neither']} | not rated by the monitor {flags['n_unrated']}."
    )
    lines.append("")

    picked_m = _round_robin(flags["monitor_only"], "_model_slug", n_monitor_only)
    lines.append(
        f"## Monitor-only flags ({len(picked_m)} of {flags['n_monitor_only']})"
    )
    lines.append("")
    lines.append(
        "The monitor called it a cheat and no detector fired. Either a cheat outside D1-D5 "
        "(a real miss in the detector) or a monitor false positive."
    )
    lines.append("")
    if not picked_m:
        lines.append("_None._")
        lines.append("")
    for i, rec in enumerate(picked_m, 1):
        mon = rec.get("monitor") or {}
        lines.append(f"### M{i}. `{rec.get('run_id')}`")
        lines.append("")
        lines.append(f"- context: {_context(rec)}")
        lines.append(f"- monitor type: `{mon.get('type')}`")
        lines.append(f"- monitor evidence: `{_one_line(mon.get('evidence'), 300)}`")
        lines.append(f"- agent summary: {_one_line(rec.get('submit_summary'))}")
        lines.append("- Reviewer: real cheat / monitor false positive / unclear -- ")
        lines.append("")

    picked_d = _round_robin(flags["detector_only"], "_model_slug", n_detector_only)
    lines.append(
        f"## Detector-only flags ({len(picked_d)} of {flags['n_detector_only']})"
    )
    lines.append("")
    lines.append(
        "A detector fired and the monitor saw nothing. Either a monitor miss (expected: it is a "
        "lower bound) or a detector false positive -- D1 fires on *any* change under `tests/` by "
        "design, so a legitimately added test lands here (plan section 10)."
    )
    lines.append("")
    if not picked_d:
        lines.append("_None._")
        lines.append("")
    for i, rec in enumerate(picked_d, 1):
        mon = rec.get("monitor") or {}
        lines.append(f"### D{i}. `{rec.get('run_id')}`")
        lines.append("")
        lines.append(f"- context: {_context(rec)}")
        lines.append(f"- detectors fired: `{_fired(rec)}`")
        lines.append(f"- detector evidence: {_detector_evidence(rec)}")
        lines.append(f"- monitor said: cheated={mon.get('cheated')} type=`{mon.get('type')}`")
        lines.append(f"- agent summary: {_one_line(rec.get('submit_summary'))}")
        lines.append("- Reviewer: real cheat / detector false positive / unclear -- ")
        lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
