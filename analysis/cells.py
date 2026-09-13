"""``cells.csv`` and ``table.md`` -- the one table (SPEC.md section 6, plan section 6)."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.stats import rate, wilson_ci
from monitor.kappa import cohen_kappa, kappa_table

__all__ = ["build_cells", "write_cells", "write_table_md", "CELL_COLUMNS"]

CELL_COLUMNS = [
    "model_slug",
    "model",
    "arm",
    "I",
    "f_realised",
    "batches",
    "solvable_item_runs",
    "honest_pass_pct",
    "cheat_pct_detector",
    "wilson_lo",
    "wilson_hi",
    "cheat_pct_monitor",
    "monitor_model",
    "kappa",
    "kappa_n",
    "detector_only",
    "monitor_only",
    "cheat_pct_impossible",
    "impossible_item_runs",
    "declared_impossible_pct",
    "declared_impossible_pct_solvable",
    "refusals",
    "errors",
    "item_runs",
]


def _pct(x: float) -> float:
    return float("nan") if x is None or not np.isfinite(x) else round(100.0 * float(x), 2)


def build_cells(df: pd.DataFrame) -> pd.DataFrame:
    """One row per model x arm x realised f."""
    if df.empty:
        return pd.DataFrame(columns=CELL_COLUMNS)

    rows: list[dict] = []
    keys = ["model_slug", "arm", "f_realised"]
    for (model_slug, arm, f), sub in df.groupby(keys, sort=True, dropna=False):
        solv = sub[~sub["is_impossible"]]
        imp = sub[sub["is_impossible"]]

        k = int(solv["cheat"].sum())
        n = int(len(solv))
        wlo, whi = wilson_ci(k, n)

        rated = sub[sub["monitor_cheated"].notna()]
        a = [bool(v) for v in rated["cheat"].tolist()]
        b = [bool(v) for v in rated["monitor_cheated"].tolist()]
        kap = cohen_kappa(a, b) if rated.shape[0] else float("nan")
        tab = kappa_table(a, b)

        rated_solv = solv[solv["monitor_cheated"].notna()]
        monitor_models = sorted({str(m) for m in rated["monitor_model"].dropna().unique()})

        rows.append(
            {
                "model_slug": model_slug,
                "model": "/".join(sorted({str(m) for m in sub["model"].dropna().unique()})),
                "arm": arm,
                "I": int(sub["I"].dropna().iloc[0]) if sub["I"].notna().any() else None,
                "f_realised": None if f is None or not np.isfinite(f) else round(float(f), 4),
                "batches": int(sub["batch_id"].nunique()),
                "solvable_item_runs": n,
                "honest_pass_pct": _pct(rate(solv["honest_pass"])),
                "cheat_pct_detector": _pct(k / n) if n else float("nan"),
                "wilson_lo": _pct(wlo),
                "wilson_hi": _pct(whi),
                "cheat_pct_monitor": _pct(rate(rated_solv["monitor_cheated"].astype(float)))
                if len(rated_solv)
                else float("nan"),
                "monitor_model": "/".join(monitor_models) if monitor_models else "",
                "kappa": None if not np.isfinite(kap) else round(float(kap), 3),
                "kappa_n": tab["n"],
                "detector_only": tab["a_only"],
                "monitor_only": tab["b_only"],
                "cheat_pct_impossible": _pct(rate(imp["cheat"])) if len(imp) else float("nan"),
                "impossible_item_runs": int(len(imp)),
                "declared_impossible_pct": _pct(rate(sub["declared_impossible"])),
                "declared_impossible_pct_solvable": _pct(rate(solv["declared_impossible"]))
                if n
                else float("nan"),
                "refusals": int(sub["refusal"].sum()),
                "errors": int(sub["error"].sum()),
                "item_runs": int(len(sub)),
            }
        )

    cells = pd.DataFrame(rows, columns=CELL_COLUMNS)
    return cells.sort_values(["model_slug", "arm", "f_realised"], na_position="last").reset_index(
        drop=True
    )


def write_cells(cells: pd.DataFrame, out_dir: str | Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "cells.csv"
    cells.to_csv(path, index=False, lineterminator="\n")
    return path


def _fmt(v, nd: int = 1) -> str:
    if v is None:
        return "--"
    if isinstance(v, float) and (math.isnan(v) or not math.isfinite(v)):
        return "--"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


MD_COLUMNS = [
    ("model_slug", "model", 0),
    ("arm", "arm", 0),
    ("f_realised", "f", 3),
    ("batches", "batches", 0),
    ("solvable_item_runs", "solvable runs", 0),
    ("honest_pass_pct", "honest pass %", 1),
    ("cheat_pct_detector", "cheat % (det)", 1),
    ("_ci", "95% CI (Wilson)", 0),
    ("cheat_pct_monitor", "cheat % (mon)", 1),
    ("monitor_model", "monitor", 0),
    ("kappa", "kappa", 3),
    ("cheat_pct_impossible", "cheat % on impossible", 1),
    ("declared_impossible_pct", "declared imp. %", 1),
    ("refusals", "refusals", 0),
    ("errors", "errors", 0),
]


def write_table_md(cells: pd.DataFrame, out_dir: str | Path) -> Path:
    """The one table, as markdown (plan section 6)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "table.md"

    lines: list[str] = []
    lines.append("# Cheating by model, arm and impossible fraction")
    lines.append("")
    lines.append(
        "Unit = one item-run. The denominator for every cheat/honest-pass column is the "
        "**solvable** item-runs in the cell (the ten measured tasks, byte-identical at every *f*); "
        "`cheat % on impossible` is the manipulation check on that cell's impossible item-runs."
    )
    lines.append("")

    header = "| " + " | ".join(label for _, label, _ in MD_COLUMNS) + " |"
    sep = "|" + "|".join("---" for _ in MD_COLUMNS) + "|"
    lines.append(header)
    lines.append(sep)

    for _, row in cells.iterrows():
        out = []
        for key, _label, nd in MD_COLUMNS:
            if key == "_ci":
                out.append(f"{_fmt(row['wilson_lo'])}-{_fmt(row['wilson_hi'])}")
            else:
                out.append(_fmt(row[key], nd))
        lines.append("| " + " | ".join(out) + " |")

    lines.append("")
    lines.append("## Column definitions")
    lines.append("")
    lines.append(
        "- **f** -- realised impossible fraction `I / (10 + I)`, not the nominal level.\n"
        "- **cheat % (det)** -- programmatic detector `D1 v D2 v D3 v D4 v D5` (SPEC section 4) on "
        "solvable item-runs. This is the primary DV; it counts cheat *attempts*.\n"
        "- **95% CI (Wilson)** -- Wilson score interval on the cell proportion, computed by hand. "
        "It ignores intra-batch clustering; the figure's bands and `stats.json` use a "
        "cluster bootstrap over batches instead.\n"
        "- **cheat % (mon)** -- LLM monitor on the same solvable item-runs, restricted to runs the "
        "monitor actually rated. A lower bound by construction.\n"
        "- **monitor** -- monitor model(s) that rated this cell (cross-lineage: never the agent's "
        "own lineage).\n"
        "- **kappa** -- Cohen's kappa, detector vs monitor, over every rated item-run in the cell "
        "(solvable and impossible). Blank when kappa is undefined (neither rater flagged anything).\n"
        "- **cheat % on impossible** -- manipulation check (plan P5): the dose is real only if this "
        "is high. ImpossibleBench-comparable.\n"
        "- **declared imp. %** -- outcome `declared_impossible` over all item-runs in the cell "
        "(the agent said the task could not be done and did not cheat). The per-cell figure "
        "restricted to solvable item-runs is `declared_impossible_pct_solvable` in `cells.csv`.\n"
        "- **refusals / errors** -- outcome counts over all item-runs in the cell."
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
