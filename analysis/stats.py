"""Statistics for the dose curve (plan section 5 / SPEC.md section 6).

Wilson intervals and Cohen's kappa are computed by hand (numpy/scipy only, no
scikit-learn).  Logistic slopes use statsmodels GLM-Binomial with
batch-clustered standard errors; every interval over rates is a cluster
bootstrap over batches.
"""

from __future__ import annotations

import json
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from monitor.kappa import cohen_kappa, kappa_table

__all__ = [
    "wilson_ci",
    "rate",
    "per_batch_counts",
    "bootstrap_rate_ci",
    "bootstrap_diff_ci",
    "logistic_clustered",
    "spearman_across_levels",
    "endpoint_difference",
    "peer_contrasts",
    "kappa_block",
    "compute_stats",
    "write_stats",
    "N_BOOT",
    "BOOT_SEED",
]

N_BOOT = 2000
BOOT_SEED = 0
Z95 = 1.959963984540054


# --------------------------------------------------------------------------- #
# rates and Wilson intervals (by hand)
# --------------------------------------------------------------------------- #
def wilson_ci(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion, computed directly.

    ``n == 0`` returns ``(0.0, 1.0)`` -- no information, not an error.
    """
    if n <= 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denom
    lo, hi = max(0.0, centre - half), min(1.0, centre + half)
    # the closed form leaves float dust at the boundaries; the exact values are 0 and 1
    if k == 0:
        lo = 0.0
    if k == n:
        hi = 1.0
    return (lo, hi)


def rate(series: pd.Series) -> float:
    """Mean of a boolean series; ``nan`` when empty."""
    if len(series) == 0:
        return float("nan")
    return float(pd.Series(series).astype(float).mean())


def per_batch_counts(df: pd.DataFrame, col: str = "cheat", cluster: str = "batch_id") -> np.ndarray:
    """``(B, 2)`` array of ``(successes, n)`` per batch -- the bootstrap unit."""
    if df.empty:
        return np.zeros((0, 2), dtype=float)
    g = df.groupby(cluster, sort=True)[col].agg(["sum", "count"])
    return g.to_numpy(dtype=float)


# --------------------------------------------------------------------------- #
# cluster bootstrap over batches
# --------------------------------------------------------------------------- #
def _boot_rates(kn: np.ndarray, n_boot: int, rng: np.random.Generator) -> np.ndarray:
    """Resample batches with replacement; return the pooled rate each time."""
    b = kn.shape[0]
    if b == 0:
        return np.array([])
    idx = rng.integers(0, b, size=(n_boot, b))
    k = kn[:, 0][idx].sum(axis=1)
    n = kn[:, 1][idx].sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = np.where(n > 0, k / np.where(n > 0, n, 1), np.nan)
    return out


def bootstrap_rate_ci(
    df: pd.DataFrame,
    col: str = "cheat",
    n_boot: int = N_BOOT,
    seed: int = BOOT_SEED,
    cluster: str = "batch_id",
) -> tuple[float, float]:
    kn = per_batch_counts(df, col, cluster)
    if kn.shape[0] == 0:
        return (float("nan"), float("nan"))
    draws = _boot_rates(kn, n_boot, np.random.default_rng(seed))
    draws = draws[np.isfinite(draws)]
    if draws.size == 0:
        return (float("nan"), float("nan"))
    return (float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5)))


def bootstrap_diff_ci(
    df_hi: pd.DataFrame,
    df_lo: pd.DataFrame,
    col: str = "cheat",
    n_boot: int = N_BOOT,
    seed: int = BOOT_SEED,
    cluster: str = "batch_id",
) -> dict:
    """Cluster bootstrap for ``rate(hi) - rate(lo)``.

    Batches are resampled independently inside each cell (a batch belongs to
    exactly one cell), which is the usual cluster bootstrap for a two-group
    contrast.  Percentile 95% CI.
    """
    kn_hi = per_batch_counts(df_hi, col, cluster)
    kn_lo = per_batch_counts(df_lo, col, cluster)
    point = float("nan")
    if kn_hi.shape[0] and kn_lo.shape[0] and kn_hi[:, 1].sum() and kn_lo[:, 1].sum():
        point = kn_hi[:, 0].sum() / kn_hi[:, 1].sum() - kn_lo[:, 0].sum() / kn_lo[:, 1].sum()
    if kn_hi.shape[0] == 0 or kn_lo.shape[0] == 0:
        return {
            "diff": point,
            "ci_lo": float("nan"),
            "ci_hi": float("nan"),
            "n_boot": 0,
            "n_batches_hi": int(kn_hi.shape[0]),
            "n_batches_lo": int(kn_lo.shape[0]),
        }
    rng = np.random.default_rng(seed)
    draws = _boot_rates(kn_hi, n_boot, rng) - _boot_rates(kn_lo, n_boot, rng)
    draws = draws[np.isfinite(draws)]
    if draws.size == 0:
        return {
            "diff": point,
            "ci_lo": float("nan"),
            "ci_hi": float("nan"),
            "n_boot": 0,
            "n_batches_hi": int(kn_hi.shape[0]),
            "n_batches_lo": int(kn_lo.shape[0]),
        }
    return {
        "diff": point,
        "ci_lo": float(np.percentile(draws, 2.5)),
        "ci_hi": float(np.percentile(draws, 97.5)),
        "p_boot_ge_0": float((draws <= 0).mean()),
        "n_boot": int(draws.size),
        "n_batches_hi": int(kn_hi.shape[0]),
        "n_batches_lo": int(kn_lo.shape[0]),
        "n_hi": int(kn_hi[:, 1].sum()),
        "n_lo": int(kn_lo[:, 1].sum()),
    }


# --------------------------------------------------------------------------- #
# clustered logistic regression
# --------------------------------------------------------------------------- #
def logistic_clustered(
    df: pd.DataFrame,
    x: str,
    y: str = "cheat",
    cluster: str = "batch_id",
) -> dict:
    """Logistic regression ``y ~ x`` with batch-clustered standard errors.

    Returns a dict with ``slope``, ``se``, ``z``, ``p``, ``ci_lo``, ``ci_hi``,
    ``intercept``, ``n``, ``n_clusters``.  When the outcome is constant, the
    cluster count is too small, or the fit separates, ``slope`` is ``None`` and
    ``note`` says ``"not estimable"`` with a reason.
    """
    out: dict = {
        "x": x,
        "n": int(len(df)),
        "n_clusters": int(df[cluster].nunique()) if len(df) else 0,
        "n_events": int(pd.Series(df[y]).astype(float).sum()) if len(df) else 0,
        "slope": None,
        "se": None,
        "z": None,
        "p": None,
        "ci_lo": None,
        "ci_hi": None,
        "intercept": None,
        "note": None,
    }
    if len(df) == 0:
        out["note"] = "not estimable: no item-runs"
        return out

    yv = pd.Series(df[y]).astype(float).to_numpy()
    xv = pd.to_numeric(df[x], errors="coerce").astype(float).to_numpy()
    ok = np.isfinite(xv) & np.isfinite(yv)
    yv, xv = yv[ok], xv[ok]
    groups = pd.Series(df[cluster]).to_numpy()[ok]
    out["n"] = int(yv.size)
    out["n_events"] = int(yv.sum())
    out["n_clusters"] = int(pd.unique(groups).size)

    if yv.size == 0:
        out["note"] = "not estimable: no item-runs"
        return out
    if yv.sum() == 0 or yv.sum() == yv.size:
        out["note"] = "not estimable: outcome is constant (complete separation)"
        return out
    if np.allclose(xv, xv[0]):
        out["note"] = f"not estimable: {x} is constant"
        return out
    if out["n_clusters"] < 2:
        out["note"] = "not estimable: fewer than 2 batches to cluster on"
        return out

    import statsmodels.api as sm

    design = sm.add_constant(xv.reshape(-1, 1), has_constant="add")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = sm.GLM(yv, design, family=sm.families.Binomial())
            res = model.fit(cov_type="cluster", cov_kwds={"groups": groups})
    except Exception as exc:  # PerfectSeparationError and friends
        out["note"] = f"not estimable: {type(exc).__name__}: {exc}"[:200]
        return out

    slope = float(res.params[1])
    se = float(res.bse[1])
    if not np.isfinite(slope) or not np.isfinite(se) or abs(slope) > 50:
        out["note"] = "not estimable: separation (unbounded coefficient)"
        return out

    out.update(
        {
            "intercept": float(res.params[0]),
            "slope": slope,
            "se": se,
            "z": float(res.tvalues[1]),
            "p": float(res.pvalues[1]),
            "ci_lo": slope - Z95 * se,
            "ci_hi": slope + Z95 * se,
            "odds_ratio": float(np.exp(slope)),
        }
    )
    return out


# --------------------------------------------------------------------------- #
# trend across the five levels
# --------------------------------------------------------------------------- #
def spearman_across_levels(df: pd.DataFrame, col: str = "cheat") -> dict:
    """Spearman of per-level cheat rate against realised f (plan P1)."""
    from scipy import stats as sps

    g = df.groupby("f_realised", sort=True)[col].agg(["mean", "count"])
    levels = g.index.to_numpy(dtype=float)
    rates = g["mean"].to_numpy(dtype=float)
    out = {
        "levels": [float(v) for v in levels],
        "rates": [float(v) for v in rates],
        "n_per_level": [int(v) for v in g["count"].to_numpy()],
        "rho": None,
        "p": None,
        "note": None,
    }
    if len(levels) < 3:
        out["note"] = f"not estimable: only {len(levels)} f level(s)"
        return out
    if np.allclose(rates, rates[0]):
        out["note"] = "not estimable: identical rates at every level"
        return out
    res = sps.spearmanr(levels, rates)
    out["rho"] = float(res.statistic)
    out["p"] = float(res.pvalue)
    return out


def endpoint_difference(
    df: pd.DataFrame,
    f_hi: float = 0.60,
    f_lo: float = 0.0,
    n_boot: int = N_BOOT,
    seed: int = BOOT_SEED,
    col: str = "cheat",
) -> dict:
    """``P(cheat | f = f_hi) - P(cheat | f = f_lo)`` with a cluster-bootstrap CI (plan H2)."""
    f = pd.to_numeric(df["f_realised"], errors="coerce")
    hi = df[np.isclose(f, f_hi, atol=0.005)]
    lo = df[np.isclose(f, f_lo, atol=0.005)]
    out = bootstrap_diff_ci(hi, lo, col=col, n_boot=n_boot, seed=seed)
    out["f_hi"] = f_hi
    out["f_lo"] = f_lo
    out["rate_hi"] = rate(hi[col]) if len(hi) else float("nan")
    out["rate_lo"] = rate(lo[col]) if len(lo) else float("nan")
    if len(hi) == 0 or len(lo) == 0:
        out["note"] = f"not estimable: no item-runs at f={f_hi if len(hi) == 0 else f_lo}"
    return out


def peer_contrasts(
    df: pd.DataFrame, n_boot: int = N_BOOT, seed: int = BOOT_SEED, col: str = "cheat"
) -> list[dict]:
    """``peer_tip - peer_neutral`` at every f level where both arms ran (plan H3)."""
    out: list[dict] = []
    if df.empty or "arm" not in df:
        return out
    peers = df[df["arm"].isin(["peer_tip", "peer_neutral"])]
    for i, f in enumerate(sorted(peers["f_realised"].dropna().unique())):
        at_f = peers[np.isclose(pd.to_numeric(peers["f_realised"]), f, atol=0.005)]
        tip = at_f[at_f["arm"] == "peer_tip"]
        neutral = at_f[at_f["arm"] == "peer_neutral"]
        if tip.empty or neutral.empty:
            continue
        res = bootstrap_diff_ci(tip, neutral, col=col, n_boot=n_boot, seed=seed + 101 + i)
        res.update(
            {
                "f_realised": float(f),
                "rate_tip": rate(tip[col]),
                "rate_neutral": rate(neutral[col]),
                "contrast": "peer_tip - peer_neutral",
            }
        )
        out.append(res)
    return out


# --------------------------------------------------------------------------- #
# detector vs monitor agreement
# --------------------------------------------------------------------------- #
def kappa_block(df: pd.DataFrame) -> dict:
    """Cohen's kappa detector-vs-monitor plus the 2x2 disagreement cells."""
    rated = df[df["monitor_cheated"].notna()]
    a = [bool(v) for v in rated["cheat"].tolist()]
    b = [bool(v) for v in rated["monitor_cheated"].tolist()]
    table = kappa_table(a, b)
    k = cohen_kappa(a, b)
    monitor_models = sorted({m for m in rated["monitor_model"].dropna().unique()})
    return {
        "kappa": None if (k is None or not np.isfinite(k)) else float(k),
        "n_rated": table["n"],
        "n_unrated": int(len(df) - len(rated)),
        "monitor_models": monitor_models,
        "table": {
            "detector_and_monitor": table["both"],
            "detector_only": table["a_only"],
            "monitor_only": table["b_only"],
            "neither": table["neither"],
        },
        "detector_rate": rate(rated["cheat"]) if len(rated) else float("nan"),
        "monitor_rate": rate(rated["monitor_cheated"].astype(float)) if len(rated) else float("nan"),
    }


def _kappa_by_pair(df: pd.DataFrame) -> list[dict]:
    """kappa per (agent model, monitor model) pair (coordinator's cross-lineage policy)."""
    rated = df[df["monitor_cheated"].notna() & df["monitor_model"].notna()]
    out: list[dict] = []
    if rated.empty:
        return out
    for (agent_model, monitor_model), sub in rated.groupby(["model", "monitor_model"], sort=True):
        block = kappa_block(sub)
        block["agent_model"] = agent_model
        block["monitor_model"] = monitor_model
        block.pop("monitor_models", None)
        out.append(block)
    return out


# --------------------------------------------------------------------------- #
# the whole stats.json
# --------------------------------------------------------------------------- #
def _jsonable(obj):
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return None if not math.isfinite(v) else v
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if obj is None or isinstance(obj, (str, int)):
        return obj
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    return str(obj)


def compute_stats(df: pd.DataFrame, n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> dict:
    """Everything SPEC section 6 asks ``stats.json`` to hold."""
    out: dict = {
        "n_boot": n_boot,
        "boot_seed": seed,
        "n_item_runs": int(len(df)),
        "n_batches": int(df["batch_id"].nunique()) if len(df) else 0,
        "undetected_batches": list(df.attrs.get("undetected_batches", [])),
        "models": {},
    }
    if df.empty:
        out["note"] = "no item-runs"
        return out

    solv_all = df[~df["is_impossible"]]

    for model_slug, mdf in df.groupby("model_slug", sort=True):
        solv = mdf[~mdf["is_impossible"]]
        imp = mdf[mdf["is_impossible"]]
        base = solv[solv["arm"] == "baseline"] if (solv["arm"] == "baseline").any() else solv

        cells = []
        for f, sub in base.groupby("f_realised", sort=True):
            k = int(sub["cheat"].sum())
            n = int(len(sub))
            lo, hi = wilson_ci(k, n)
            blo, bhi = bootstrap_rate_ci(sub, n_boot=n_boot, seed=seed)
            cells.append(
                {
                    "f_realised": float(f),
                    "n_solvable_item_runs": n,
                    "n_batches": int(sub["batch_id"].nunique()),
                    "cheats": k,
                    "cheat_rate": k / n if n else float("nan"),
                    "wilson_lo": lo,
                    "wilson_hi": hi,
                    "boot_lo": blo,
                    "boot_hi": bhi,
                }
            )

        entry = {
            "model": sorted({str(m) for m in mdf["model"].dropna().unique()}),
            "provider": sorted({str(p) for p in mdf["provider"].dropna().unique()}),
            "n_item_runs": int(len(mdf)),
            "n_solvable_item_runs": int(len(solv)),
            "n_impossible_item_runs": int(len(imp)),
            "n_batches": int(mdf["batch_id"].nunique()),
            "cells": cells,
            "logistic_cheat_on_f": logistic_clustered(base, "f_realised"),
            "logistic_cheat_on_f_discoverable": {
                **logistic_clustered(base, "f_discoverable"),
                "note_secondary": (
                    "SECONDARY exposure measure, not a replacement for realised f anywhere. "
                    "f_discoverable = (unreachable variants in the batch) / batch_size: a "
                    "`contradict` variant looks solved from inside the sandbox because its "
                    "visible tests pass, while an `unreachable` variant announces itself as a "
                    "missing resource, so only the latter is plainly impossible to the agent "
                    "while it works. Pre-registration fixes f_realised as the IV; this fit is "
                    "exploratory and was added after the pilot showed every impossible-item "
                    "cheat landing on unreachable variants"
                ),
            },
            "endpoint_difference": endpoint_difference(base, 0.60, 0.0, n_boot=n_boot, seed=seed),
            "spearman": spearman_across_levels(base),
            "cumulative_dose": {
                **logistic_clustered(solv, "n_impossible_before"),
                "note_confounded": (
                    "pooled across f; n_impossible_before is mechanically confounded with f "
                    "(a larger f means both more impossible items and a longer batch), so this "
                    "slope separates order from dose only partially (plan section 11)"
                ),
            },
            "cheat_pct_impossible": {
                "rate": rate(imp["cheat"]) if len(imp) else float("nan"),
                "n": int(len(imp)),
                "cheats": int(imp["cheat"].sum()) if len(imp) else 0,
                "note": "manipulation check (plan P5): ImpossibleBench-comparable",
            },
            "declared_impossible_rate_solvable": rate(solv["declared_impossible"]),
            "honest_pass_rate_solvable": rate(solv["honest_pass"]),
            "refusals": int(mdf["refusal"].sum()),
            "errors": int(mdf["error"].sum()),
            "peer_contrasts": peer_contrasts(solv, n_boot=n_boot, seed=seed),
            "kappa": kappa_block(mdf),
            "kappa_by_pair": _kappa_by_pair(mdf),
        }
        out["models"][str(model_slug)] = entry

    out["kappa_overall"] = kappa_block(df)
    out["kappa_by_pair"] = _kappa_by_pair(df)
    out["pooled_cumulative_dose"] = {
        **logistic_clustered(solv_all, "n_impossible_before"),
        "note_confounded": (
            "pooled across f and models; confounded with f by construction (plan section 11)"
        ),
    }
    return _jsonable(out)


def write_stats(stats: dict, out_dir: str | Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "stats.json"
    path.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
