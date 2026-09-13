"""Cohen's kappa for two binary raters, computed by hand (no scikit-learn)."""

from __future__ import annotations

import math

__all__ = ["cohen_kappa", "kappa_table", "agreement"]


def _clean(a: list, b: list) -> tuple[list[bool], list[bool]]:
    if len(a) != len(b):
        raise ValueError(f"rater vectors differ in length: {len(a)} vs {len(b)}")
    ca: list[bool] = []
    cb: list[bool] = []
    for x, y in zip(a, b):
        if x is None or y is None:
            continue  # a record the monitor never rated contributes nothing
        ca.append(bool(x))
        cb.append(bool(y))
    return ca, cb


def kappa_table(a: list, b: list) -> dict:
    """2x2 contingency table for rater ``a`` (rows) vs rater ``b`` (columns).

    Keys ``both``, ``a_only``, ``b_only``, ``neither`` and ``n``.  ``a_only`` and
    ``b_only`` are the two disagreement cells SPEC section 6 asks to report.
    """
    ca, cb = _clean(a, b)
    both = sum(1 for x, y in zip(ca, cb) if x and y)
    a_only = sum(1 for x, y in zip(ca, cb) if x and not y)
    b_only = sum(1 for x, y in zip(ca, cb) if y and not x)
    neither = sum(1 for x, y in zip(ca, cb) if not x and not y)
    return {
        "both": both,
        "a_only": a_only,
        "b_only": b_only,
        "neither": neither,
        "n": both + a_only + b_only + neither,
    }


def agreement(a: list, b: list) -> float:
    t = kappa_table(a, b)
    if t["n"] == 0:
        return float("nan")
    return (t["both"] + t["neither"]) / t["n"]


def cohen_kappa(a: list[bool], b: list[bool]) -> float:
    """Cohen's kappa for two binary raters.

    Returns ``nan`` when kappa is undefined: no overlapping ratings, or both
    raters are constant (expected agreement 1) -- e.g. a cell in which nobody
    cheated and the monitor flagged nobody.
    """
    t = kappa_table(a, b)
    n = t["n"]
    if n == 0:
        return float("nan")

    po = (t["both"] + t["neither"]) / n
    p_a_yes = (t["both"] + t["a_only"]) / n
    p_b_yes = (t["both"] + t["b_only"]) / n
    pe = p_a_yes * p_b_yes + (1.0 - p_a_yes) * (1.0 - p_b_yes)

    denom = 1.0 - pe
    if math.isclose(denom, 0.0, abs_tol=1e-12):
        return float("nan")
    return (po - pe) / denom
