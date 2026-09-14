"""CLI: produce every SPEC section 6 artefact.

    uv run python -m analysis.run --runs results/runs --out results/analysis

Writes ``cells.csv``, ``table.md``, ``stats.json``, ``figure.png``, ``figure.svg``
and ``flags_for_review.md``.
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

from analysis.cells import build_cells, write_cells, write_table_md
from analysis.figure import make_figure
from analysis.figure_v7 import make_v7_figure
from analysis.flags import write_flags_md
from analysis.load import load_runs
from analysis.mutation import write_mutation_table
from analysis.stats import compute_stats, write_stats


def run_analysis(
    runs_dir: str | Path,
    out_dir: str | Path,
    n_boot: int = 2000,
    seed: int = 0,
    quiet: bool = False,
) -> dict:
    runs_dir, out_dir = Path(runs_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    messages: list[str] = []
    df = load_runs(runs_dir, warn=lambda msg, **kw: messages.append(str(msg)))
    for msg in messages:
        warnings.warn(msg, stacklevel=2)
        if not quiet:
            print(f"WARNING: {msg}", file=sys.stderr)

    if df.empty:
        if not quiet:
            print(
                f"no analysable item-runs under {runs_dir} "
                "(did you run `python -m detectors.run` first?)",
                file=sys.stderr,
            )

    cells = build_cells(df)
    paths = {
        "cells.csv": write_cells(cells, out_dir),
    }
    stats = compute_stats(df, n_boot=n_boot, seed=seed)
    paths.update({
        "table.md": write_table_md(cells, out_dir, stats),
        "stats.json": write_stats(stats, out_dir),
    })
    for name, path in write_mutation_table(df, out_dir).items():
        paths[f"impossible_by_mutation.{name}"] = path
    fig_paths = make_figure(df, out_dir, n_boot=n_boot, seed=seed)
    fig_paths += make_v7_figure(df, out_dir, n_boot=n_boot, seed=seed)
    for p in fig_paths:
        paths[p.name] = p
    paths["flags_for_review.md"] = write_flags_md(runs_dir, out_dir)

    if not quiet:
        print(f"{len(df):,} item-runs from {df['batch_id'].nunique():,} batches")
        for name, path in paths.items():
            print(f"  wrote {path}")
    return {"df": df, "cells": cells, "paths": paths}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="analysis.run", description=__doc__)
    ap.add_argument("--runs", default="results/runs")
    ap.add_argument("--out", default="results/analysis")
    ap.add_argument("--n-boot", type=int, default=2000, help="cluster-bootstrap resamples")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    run_analysis(args.runs, args.out, n_boot=args.n_boot, seed=args.seed, quiet=args.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
