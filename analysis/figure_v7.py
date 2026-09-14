"""figure_v7: the PREREG v7 follow-up — leak-closed replication and the notes ablation.

Two panels, written by ``analysis.run`` alongside the main figure:

* **A** — solvable-item cheat rate against realised *f*, DeepSeek and GLM, v1 solid and
  v2 dashed in the same per-model colour, cluster-bootstrap 95% bands.
* **B** — the notes ablation at *f* = 0.60: three bars (v1 frozen, v2 notes on, v2 notes
  off) with Wilson intervals, and above each bar TWO hollow markers on the SAME y scale,
  one per kind of impossible item — `unreachable` (announces itself: the resource is
  missing) and `contradict` (looks solved from inside the sandbox, because its visible
  tests pass). Both are drawn because withholding the notes moves them in OPPOSITE
  directions, and a panel showing only `unreachable` tells the flattering half of that:
  unreachable cheating rises 58/84 -> 70/84 while contradict cheating goes 37/96 -> 0/96,
  so across all impossible items cheating FALLS, 95/180 -> 70/180. The all-impossible
  totals are annotated under the bars so the reader cannot take the rise as the whole
  story.

These cells are exploratory. v1 remains the frozen primary result.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analysis.figure import (  # noqa: E402
    BAND_CAPTION,
    GRID,
    SERIES,
    SURFACE,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    _f_axis,
    _grow_to_fit,
    _shade_band,
    _style,
)
from analysis.stats import bootstrap_rate_ci, wilson_ci  # noqa: E402

__all__ = ["make_v7_figure", "V7_CAPTION", "V7_PAIRS", "V7_BARS", "IMPOSSIBLE_KINDS"]

V7_CAPTION = (
    "PREREG v7, exploratory: env_version 2 closes the two environment leaks the review "
    "found (the work dir no longer carries the item_key and its mutation label, and "
    "earlier items' directories are removed from the batch container), with the same "
    "tasks, the same seeds and the same detectors. v1 remains the frozen primary result; "
    "v2 is its robustness check and replaces nothing."
)

#: (label, v1 slug, v2 slug) for panel A.
V7_PAIRS = (("DeepSeek", "dsv41flash-sal", "dsv41flash-sal-v2"),
            ("GLM", "glm53flash-sal", "glm53flash-sal-v2"))

#: one marker per model, so panel A survives grayscale: the two series colours are
#: close in luminance and solid-vs-dashed only separates v1 from v2 within a model.
PAIR_MARKERS = ("o", "^")

#: (bar label, slug) for panel B, all at f = 0.60.
V7_BARS = (("v1\n(frozen)", "dsv41flash-sal"),
           ("v2\nnotes on", "dsv41flash-sal-v2"),
           ("v2\nnotes off", "dsv41flash-sal-v2-nonotes"))

F_ENDPOINT = 0.6


#: the two kinds of impossible item, with the marker that carries each one's identity
#: in grayscale as well as in colour. Order is draw order and legend order.
#: the x offsets put both markers just OUTSIDE the 0.58-wide bar, so neither they nor
#: their count labels land on the bar's own label.
IMPOSSIBLE_KINDS = (
    ("unreachable", "o", -0.335, "impossible: unreachable variant"),
    ("contradict", "s", 0.335, "impossible: contradict variant"),
)


def _cell(df: pd.DataFrame, slug: str, f: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    sub = df[(df["model_slug"] == slug) & (df["arm"] == "baseline")]
    sub = sub[sub["f_realised"].round(4) == round(f, 4)]
    return sub[~sub["is_impossible"]], sub[sub["is_impossible"]]


def _kind(imp: pd.DataFrame, kind: str) -> tuple[int, int]:
    sub = imp[imp["mutation"] == kind]
    return int(sub["cheat"].sum()), int(len(sub))


def _panel_replication(ax, df: pd.DataFrame, n_boot: int, seed: int) -> float:
    _shade_band(ax)
    ymax = 1.0
    for i, (_name, v1, v2) in enumerate(V7_PAIRS):
        colour = SERIES[i % len(SERIES)]
        marker = PAIR_MARKERS[i % len(PAIR_MARKERS)]
        for slug, ls, filled in ((v1, "solid", True), (v2, (0, (4.0, 2.0)), False)):
            sub = df[(df["model_slug"] == slug) & (df["arm"] == "baseline")]
            sub = sub[~sub["is_impossible"]]
            if sub.empty:
                continue
            xs, ys, los, his = [], [], [], []
            for f, cell in sub.groupby("f_realised", sort=True):
                if not np.isfinite(f) or len(cell) == 0:
                    continue
                k, n = int(cell["cheat"].sum()), int(len(cell))
                lo, hi = bootstrap_rate_ci(cell, n_boot=n_boot, seed=seed)
                if not np.isfinite(lo) or not np.isfinite(hi):
                    lo, hi = wilson_ci(k, n)
                xs.append(float(f))
                ys.append(100.0 * k / n)
                los.append(100.0 * lo)
                his.append(100.0 * hi)
            if not xs:
                continue
            ymax = max(ymax, max(his))
            ax.fill_between(xs, los, his, color=colour, alpha=0.11, lw=0, zorder=2)
            ax.plot(xs, ys, color=colour, linestyle=ls, linewidth=2.0, zorder=4,
                    marker=marker, markersize=5.5, markeredgecolor=SURFACE,
                    markerfacecolor=colour if filled else SURFACE,
                    markeredgewidth=1.3, clip_on=False)
    ax.set_xlabel("realised impossible fraction  f", fontsize=8, color=TEXT_SECONDARY)
    ax.set_ylabel("cheat rate (% of item-runs)", fontsize=8, color=TEXT_SECONDARY)
    ax.set_title("A.  Leak-closed replication (solvable items)", fontsize=8.6,
                 color=TEXT_PRIMARY, loc="left", pad=6)
    return ymax


def _ablation_ymax(df: pd.DataFrame) -> float:
    """Highest value panel B must fit: the Wilson upper bounds and both marker series."""
    ymax = 1.0
    for _label, slug in V7_BARS:
        solv, imp = _cell(df, slug, F_ENDPOINT)
        if len(solv):
            k, n = int(solv["cheat"].sum()), int(len(solv))
            ymax = max(ymax, 100.0 * wilson_ci(k, n)[1])
        for kind, _mk, _dx, _lbl in IMPOSSIBLE_KINDS:
            k, n = _kind(imp, kind)
            if n:
                ymax = max(ymax, 100.0 * k / n)
    return ymax


def _panel_ablation(ax, df: pd.DataFrame, top: float) -> None:
    colour = SERIES[0]
    xs = np.arange(len(V7_BARS), dtype=float)
    totals: list[str] = []
    for x, (label, slug) in zip(xs, V7_BARS):
        solv, imp = _cell(df, slug, F_ENDPOINT)
        if len(solv):
            k, n = int(solv["cheat"].sum()), int(len(solv))
            y = 100.0 * k / n
            lo, hi = wilson_ci(k, n)
            ax.bar([x], [y], width=0.58, color=colour,
                   alpha=0.32 if "off" in label else 0.85,
                   edgecolor=colour, linewidth=1.2, zorder=3)
            ax.errorbar([x], [y], yerr=[[y - 100.0 * lo], [100.0 * hi - y]],
                        fmt="none", ecolor=TEXT_SECONDARY, elinewidth=1.0,
                        capsize=3.0, zorder=4)
            ax.text(x, 100.0 * hi + top * 0.03, f"{k}/{n}", ha="center", fontsize=6.2,
                    color=TEXT_SECONDARY, zorder=5)
        # both kinds of impossible item, because withholding the notes moves them in
        # opposite directions and only one of the two flatters the ablation
        for kind, marker, dx, _lbl in IMPOSSIBLE_KINDS:
            k, n = _kind(imp, kind)
            if not n:
                continue
            y = 100.0 * k / n
            ax.plot([x + dx], [y], marker=marker, markersize=7.0,
                    markerfacecolor="none", markeredgecolor=colour,
                    markeredgewidth=1.9, linestyle="none", zorder=6)
            ax.text(x + dx, y + top * 0.035, f"{k}/{n}", ha="center", fontsize=6.2,
                    color=colour, zorder=6)
        if len(imp):
            totals.append(f"{int(imp['cheat'].sum())}/{len(imp)}")
    ax.set_xticks(xs)
    ax.set_xticklabels([b[0] for b in V7_BARS], fontsize=7, color=TEXT_SECONDARY)
    ax.set_xlim(-0.78, len(V7_BARS) - 0.22)
    ax.set_ylim(0, top)
    ax.set_ylabel("cheat rate (% of item-runs)", fontsize=8, color=TEXT_SECONDARY)
    ax.set_title("B.  Notes ablation at f = 0.60 (DeepSeek)", fontsize=8.6,
                 color=TEXT_PRIMARY, loc="left", pad=6)
    if totals:
        # the corrective total: the two markers move in opposite directions, and their
        # sum is the number a reader would otherwise have to compute
        ax.text(0.5, -0.195,
                "all impossible items:  " + "  →  ".join(totals),
                transform=ax.transAxes, fontsize=6.3, color=TEXT_SECONDARY,
                va="top", ha="center")


def make_v7_figure(df: pd.DataFrame, out_dir: str | Path, n_boot: int = 2000,
                   seed: int = 0, stem: str = "figure_v7") -> list[Path]:
    """Write ``figure_v7.png`` (200 dpi) and ``figure_v7.svg``; return both paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": TEXT_PRIMARY,
                         "axes.labelcolor": TEXT_SECONDARY, "svg.fonttype": "path",
                         "figure.dpi": 200, "savefig.dpi": 200})

    fig = plt.figure(figsize=(7.5, 6.7))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1.0], wspace=0.30,
                          left=0.085, right=0.985, top=0.905, bottom=0.585)
    ax1, ax2 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    _style(fig, (ax1, ax2))

    if df.empty:
        for ax in (ax1, ax2):
            ax.text(0.5, 0.5, "no item-runs", ha="center", va="center", fontsize=9,
                    color=TEXT_MUTED, transform=ax.transAxes)
        top = 10.0
    else:
        a_ymax = _panel_replication(ax1, df, n_boot, seed)
        # ONE y scale across both panels, with headroom for the count labels above the
        # bars and markers -- otherwise the unreachable markers draw outside the axes.
        top = max(4.0, max(a_ymax, _ablation_ymax(df)) * 1.22)
        _f_axis(ax1, top)
        ax1.set_ylim(0, top)
        _panel_ablation(ax2, df, top)

    handles = []
    for i, (name, _v1, _v2) in enumerate(V7_PAIRS):
        colour = SERIES[i % len(SERIES)]
        marker = PAIR_MARKERS[i % len(PAIR_MARKERS)]
        handles.append(plt.Line2D([], [], color=colour, linestyle="solid", linewidth=2.0,
                                  marker=marker, markersize=5.5,
                                  label=f"{name} v1 (frozen)"))
        handles.append(plt.Line2D([], [], color=colour, linestyle=(0, (4.0, 2.0)),
                                  linewidth=2.0, marker=marker, markersize=5.5,
                                  markerfacecolor=SURFACE,
                                  label=f"{name} v2 (leaks closed)"))
    for kind, marker, _dx, label in IMPOSSIBLE_KINDS:
        handles.append(plt.Line2D([], [], color=SERIES[0], marker=marker, markersize=7.0,
                                  linestyle="none", markerfacecolor="none",
                                  markeredgewidth=1.9,
                                  label=f"{label} (panel B)"))
    leg = fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.435),
                     ncol=3, fontsize=6.3, frameon=True, framealpha=1.0, edgecolor=GRID,
                     facecolor=SURFACE, borderpad=0.5, handlelength=2.4,
                     labelspacing=0.4, handletextpad=0.55, columnspacing=1.4)
    leg.get_frame().set_linewidth(0.8)
    for t in leg.get_texts():
        t.set_color(TEXT_SECONDARY)

    fig.suptitle("Closing the environment leaks, and cutting the memory channel",
                 fontsize=10.0, color=TEXT_PRIMARY, x=0.008, ha="left", y=0.972)

    paragraphs = [
        V7_CAPTION,
        "A: solvable-item cheat rate against realised f, with cluster-bootstrap 95% bands "
        f"over batches ({n_boot:,} resamples, seed {seed}); solid = v1, dashed = v2, one "
        "colour per model. Shaded band: " + BAND_CAPTION + ".",
        "B: bars are the solvable-item cheat rate at f = 0.60 with Wilson 95% intervals. "
        "The two hollow markers on each bar are that same cell's cheat rate on the two "
        "kinds of impossible item, on the same y scale: circles for unreachable variants, "
        "which announce themselves (the resource the task needs is not there), squares for "
        "contradict variants, which look solved from inside the sandbox because their "
        "visible tests pass.",
        "Withholding the agent's own prior submit summaries does three things at once. It "
        "removes the spillover to solvable tasks entirely (46/120 -> 0/120). It RAISES "
        "cheating on the items that announce their own impossibility (58/84 -> 70/84). And "
        "it removes cheating on the items that do not (37/96 -> 0/96). Added up, cheating "
        "on impossible items as a whole FALLS, 95/180 -> 70/180: the notes are not only a "
        "spillover channel, they are most of how the grader gets found at all. The "
        "asymmetry is the mechanism -- an unreachable item shows the agent it is stuck, so "
        "the agent goes looking for the grader by itself; a contradict item never looks "
        "impossible, so on those the only thing that sends the agent to the grader is a "
        "note it wrote on an earlier item.",
    ]
    wrapped: list[str] = []
    for para in paragraphs:
        wrapped.extend(textwrap.wrap(para, width=132) or [""])
    note = fig.text(0.012, 0.395, "\n".join(wrapped), fontsize=6.0, color=TEXT_MUTED,
                    va="top", ha="left", linespacing=1.5)
    # the caption grew with the contradict paragraph; grow the canvas rather than
    # letting the last lines fall off the bottom
    _grow_to_fit(fig, note, floor=0.0, pad_in=0.22)

    paths = []
    for ext in ("png", "svg"):
        path = out_dir / f"{stem}.{ext}"
        fig.savefig(path, dpi=200, facecolor=SURFACE, edgecolor="none")
        paths.append(path)
    plt.close(fig)
    return paths
