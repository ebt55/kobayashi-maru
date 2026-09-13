"""CLI: fill ``detectors`` / ``declared_impossible_heuristic`` / ``outcome``.

    uv run python -m detectors.run --runs results/runs [--batch <batch_id>]

Rewrites every ``results/runs/<batch_id>/items.jsonl`` atomically (temp file +
``os.replace``).  Idempotent: re-running produces byte-identical files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path

from detectors.detect import declared_impossible, detect, outcome

OUTCOMES = (
    "error",
    "refusal",
    "cheat",
    "declared_impossible",
    "honest_pass",
    "honest_fail",
)


def annotate(record: dict) -> dict:
    """Fill the three detector-stage fields on one record, in place."""
    det = detect(record)
    record["detectors"] = det
    record["declared_impossible_heuristic"] = declared_impossible(record)
    record["outcome"] = outcome(record, det)
    return record


def _atomic_write_jsonl(path: Path, records: list[dict]) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            for rec in records:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def process_batch(items_path: Path) -> Counter:
    records: list[dict] = []
    with items_path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{items_path}:{lineno}: malformed JSON ({exc})") from exc

    counts: Counter = Counter()
    for rec in records:
        annotate(rec)
        counts[rec["outcome"]] += 1
    _atomic_write_jsonl(items_path, records)
    return counts


def find_batches(runs_dir: Path, batch: str | None) -> list[Path]:
    if not runs_dir.is_dir():
        raise SystemExit(f"runs directory not found: {runs_dir}")
    if batch:
        p = runs_dir / batch / "items.jsonl"
        if not p.is_file():
            raise SystemExit(f"no items.jsonl for batch {batch!r} under {runs_dir}")
        return [p]
    return sorted(runs_dir.glob("*/items.jsonl"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="detectors.run", description=__doc__)
    ap.add_argument("--runs", default="results/runs", help="directory of <batch_id>/items.jsonl")
    ap.add_argument("--batch", default=None, help="only this batch_id")
    args = ap.parse_args(argv)

    runs_dir = Path(args.runs)
    paths = find_batches(runs_dir, args.batch)
    if not paths:
        print(f"no batches found under {runs_dir}")
        return 0

    total: Counter = Counter()
    for items_path in paths:
        counts = process_batch(items_path)
        total.update(counts)
        summary = "  ".join(f"{k}={counts[k]}" for k in OUTCOMES if counts[k])
        n = sum(counts.values())
        print(f"{items_path.parent.name:<40} n={n:<4} {summary}")

    print("-" * 60)
    print(
        f"{'TOTAL':<40} n={sum(total.values()):<4} "
        + "  ".join(f"{k}={total[k]}" for k in OUTCOMES if total[k])
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
