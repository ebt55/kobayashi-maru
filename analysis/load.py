"""Read ``results/runs/*/items.jsonl`` into one tidy DataFrame (one row per item-run)."""

from __future__ import annotations

import json
import re
import warnings
from pathlib import Path

import pandas as pd

__all__ = ["load_runs", "load_batch", "parse_batch_id", "COLUMNS", "ARMS"]

ARMS = ("baseline", "peer_neutral", "peer_tip")

_BATCH_RE = re.compile(
    r"^(?P<model_slug>.+?)_(?P<arm>baseline|peer_neutral|peer_tip)_I(?P<I>\d+)_s(?P<seed>-?\d+)$"
)

COLUMNS = [
    "batch_id",
    "run_id",
    "model",
    "model_slug",
    "provider",
    "arm",
    "I",
    "batch_size",
    "f_realised",
    "seed",
    "position",
    "n_items_before",
    "n_impossible_before",
    "task_id",
    "item_key",
    "is_impossible",
    "mutation",
    "outcome",
    "cheat",
    "D1",
    "D2",
    "D3",
    "D4",
    "D5",
    "monitor_cheated",
    "monitor_type",
    "monitor_model",
    "monitor_provider",
    "monitor_error",
    "declared_impossible_heuristic",
    "declared_impossible",
    "refusal",
    "error",
    "honest_pass",
    "honest_fail",
    "submitted",
    "duration_s",
    "n_turns",
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
]


def parse_batch_id(batch_id: str) -> dict:
    """``<model_slug>_<arm>_I<I>_s<seed>`` -> its parts (best effort)."""
    m = _BATCH_RE.match(batch_id or "")
    if m:
        return {
            "model_slug": m.group("model_slug"),
            "arm": m.group("arm"),
            "I": int(m.group("I")),
            "seed": int(m.group("seed")),
        }
    return {"model_slug": (batch_id or "").split("_")[0], "arm": None, "I": None, "seed": None}


def _flatten(rec: dict, batch_id: str) -> dict:
    det = rec.get("detectors") or {}
    mon = rec.get("monitor") or {}
    usage = rec.get("usage") or {}
    parsed = parse_batch_id(batch_id)
    outcome = rec.get("outcome")

    monitor_cheated = mon.get("cheated")
    if monitor_cheated is not None:
        monitor_cheated = bool(monitor_cheated)

    monitor_declared = mon.get("declared_impossible")
    if monitor_declared is not None:
        monitor_declared = bool(monitor_declared)

    row = {
        "batch_id": batch_id,
        "run_id": rec.get("run_id"),
        "model": rec.get("model"),
        "model_slug": parsed["model_slug"],
        "provider": rec.get("provider"),
        "arm": rec.get("arm") or parsed["arm"],
        "I": rec.get("I") if rec.get("I") is not None else parsed["I"],
        "batch_size": rec.get("batch_size"),
        "f_realised": rec.get("f_realised"),
        "seed": rec.get("seed") if rec.get("seed") is not None else parsed["seed"],
        "position": rec.get("position"),
        "n_items_before": rec.get("n_items_before"),
        "n_impossible_before": rec.get("n_impossible_before"),
        "task_id": rec.get("task_id"),
        "item_key": rec.get("item_key"),
        "is_impossible": bool(rec.get("is_impossible")),
        "mutation": rec.get("mutation"),
        "outcome": outcome,
        "cheat": bool(det.get("cheat")),
        "D1": bool(det.get("D1")),
        "D2": bool(det.get("D2")),
        "D3": bool(det.get("D3")),
        "D4": bool(det.get("D4")),
        "D5": bool(det.get("D5")),
        "monitor_cheated": monitor_cheated,
        "monitor_type": mon.get("type"),
        "monitor_model": mon.get("model"),
        "monitor_provider": mon.get("provider"),
        "monitor_error": mon.get("error"),
        "declared_impossible_heuristic": bool(rec.get("declared_impossible_heuristic")),
        "declared_impossible": outcome == "declared_impossible",
        "refusal": outcome == "refusal",
        "error": outcome == "error",
        "honest_pass": outcome == "honest_pass",
        "honest_fail": outcome == "honest_fail",
        "submitted": bool(rec.get("submitted")),
        "duration_s": rec.get("duration_s"),
        "n_turns": rec.get("n_turns"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
    }
    return row


def load_batch(items_path: Path) -> tuple[list[dict], bool]:
    """Return (rows, detected).  ``detected`` is False if any record lacks ``detectors``."""
    batch_id = items_path.parent.name
    rows: list[dict] = []
    detected = True
    with items_path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{items_path}:{lineno}: malformed JSON ({exc})") from exc
            if not isinstance(rec.get("detectors"), dict) or rec.get("outcome") is None:
                detected = False
            rows.append(_flatten(rec, batch_id))
    return rows, detected


def load_runs(runs_dir: str | Path, warn=warnings.warn) -> pd.DataFrame:
    """One row per item-run across every batch under ``runs_dir``.

    Batches in which any record is missing ``detectors``/``outcome`` are reported
    as "undetected" and excluded, with a warning naming them (run
    ``python -m detectors.run`` first).  The list of excluded batch ids is on
    ``df.attrs["undetected_batches"]``.
    """
    runs_dir = Path(runs_dir)
    if not runs_dir.is_dir():
        raise FileNotFoundError(f"runs directory not found: {runs_dir}")

    all_rows: list[dict] = []
    undetected: list[str] = []
    for items_path in sorted(runs_dir.glob("*/items.jsonl")):
        rows, detected = load_batch(items_path)
        if not rows:
            continue
        if not detected:
            undetected.append(items_path.parent.name)
            continue
        all_rows.extend(rows)

    if undetected:
        warn(
            f"excluded {len(undetected)} undetected batch(es) with no `detectors` field "
            f"(run `uv run python -m detectors.run --runs {runs_dir}` first): "
            + ", ".join(undetected),
            stacklevel=2,
        )

    df = pd.DataFrame(all_rows, columns=COLUMNS)
    if not df.empty:
        df["f_realised"] = pd.to_numeric(df["f_realised"], errors="coerce").round(4)
        for col in ("I", "batch_size", "seed", "position", "n_items_before", "n_impossible_before"):
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        df["monitor_cheated"] = df["monitor_cheated"].astype("boolean")
    df.attrs["undetected_batches"] = undetected
    df.attrs["runs_dir"] = str(runs_dir)
    return df


def solvable(df: pd.DataFrame) -> pd.DataFrame:
    """Item-runs on the fixed solvable set -- the denominator for the primary DV."""
    return df[~df["is_impossible"]]
