"""CLI: fill ``record["monitor"]`` for every item-run.

    uv run python -m monitor.run --runs results/runs [--batch <id>] [--limit N]
                                [--concurrency 4] [--provider ...] [--model ...] [--force]

Idempotent: records whose ``monitor`` is already filled are skipped unless
``--force``.  Each ``items.jsonl`` is rewritten atomically.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path

from monitor.runner import (
    DEFAULT_CACHE_DIR,
    PROVIDERS,
    MonitorError,
    _needs_monitor,
    run_monitor,
)


def _load(path: Path) -> list[dict]:
    out = []
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{lineno}: malformed JSON ({exc})") from exc
    return out


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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="monitor.run", description=__doc__)
    ap.add_argument("--runs", default="results/runs")
    ap.add_argument("--batch", default=None)
    ap.add_argument("--limit", type=int, default=None, help="rate at most N records this run")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--cache-dir", default=str(DEFAULT_CACHE_DIR))
    ap.add_argument("--provider", default=None, choices=list(PROVIDERS))
    ap.add_argument("--model", default=None)
    ap.add_argument("--force", action="store_true", help="re-rate records that already have a monitor verdict")
    args = ap.parse_args(argv)

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:  # pragma: no cover
        pass

    runs_dir = Path(args.runs)
    if not runs_dir.is_dir():
        raise SystemExit(f"runs directory not found: {runs_dir}")
    if args.batch:
        paths = [runs_dir / args.batch / "items.jsonl"]
        if not paths[0].is_file():
            raise SystemExit(f"no items.jsonl for batch {args.batch!r} under {runs_dir}")
    else:
        paths = sorted(runs_dir.glob("*/items.jsonl"))
    if not paths:
        print(f"no batches found under {runs_dir}")
        return 0

    budget = args.limit
    total: Counter = Counter()
    for items_path in paths:
        records = _load(items_path)
        pending = [r for r in records if _needs_monitor(r, args.force)]
        if budget is not None:
            if budget <= 0:
                break
            pending = pending[:budget]
        if not pending:
            print(f"{items_path.parent.name:<40} nothing to do")
            continue
        try:
            run_monitor(
                pending,
                provider=args.provider,
                model=args.model,
                cache_dir=args.cache_dir,
                concurrency=args.concurrency,
                force=args.force,
            )
        except MonitorError as exc:
            print(f"monitor failed: {exc}", file=sys.stderr)
            return 2
        _atomic_write_jsonl(items_path, records)
        if budget is not None:
            budget -= len(pending)

        counts: Counter = Counter()
        for r in pending:
            mon = r.get("monitor") or {}
            if mon.get("error"):
                counts[mon["error"].split(":")[0]] += 1
            elif mon.get("cheated"):
                counts["cheated"] += 1
            else:
                counts["clean"] += 1
            if mon.get("cached"):
                counts["cache_hit"] += 1
        total.update(counts)
        summary = "  ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        print(f"{items_path.parent.name:<40} n={len(pending):<4} {summary}")

    print("-" * 60)
    print("TOTAL  " + "  ".join(f"{k}={v}" for k, v in sorted(total.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
