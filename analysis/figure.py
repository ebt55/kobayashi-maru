"""The one figure (SPEC.md section 6, plan section 6).

Panel A: cheat-on-solvable % against realised *f*, one line per model with a
cluster-bootstrap 95% band and the organizer-added 0.30-0.40 band shaded.
Panel B: the cumulative-dose curve -- cheat % against the number of impossible
items already encountered in the batch, pooled across *f*.

Design follows the `dataviz` skill: validated categorical slots in fixed order
(slots 1-3 pass the all-pairs CVD and normal-vision gates in both modes), 2px
lines, >=8px markers with a 2px surface ring, hairline solid recessive grid, a
legend always present plus direct end labels (the relief for the slot-3 contrast
WARN), and -- because this is printed in a PDF -- a distinct **linestyle and
marker per model**, so identity survives grayscale and full-severity CVD.
"""

from __future__ import annotations

import math
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analysis.stats import bootstrap_rate_ci, rate, wilson_ci  # noqa: E402

__all__ = ["make_figure", "BAND_CAPTION", "SERIES", "LINESTYLES", "MARKERS"]

#: verbatim from SPEC.md section 6.
BAND_CAPTION = (
    "'~30–40% impossible' — organizer-added; "
    "not stated in the ExploitGym paper"
)

# --- design tokens (dataviz reference palette, light surface) ----------------
SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#807f79"
GRID = "#e6e5e1"
AXIS = "#c9c8c2"
BAND_FILL = "#f0efec"  # neutral gray midpoint
BAND_EDGE = "#d6d5d0"

#: categorical slots, fixed order, never cycled (dataviz references/palette.md).
SERIES = (
    "#2a78d6",  # 1 blue
    "#eb6834",  # 2 orange
    "#1baf7a",  # 3 aqua
    "#eda100",  # 4 yellow
    "#e87ba4",  # 5 magenta
    "#008300",  # 6 green
    "#4a3aa7",  # 7 violet
    "#e34948",  # 8 red
)
#: the grayscale/print channel: identity never rests on hue alone.
LINESTYLES = (
    "solid",
    (0, (5.5, 2.2)),
    (0, (1.4, 1.6)),
    (0, (7, 2, 1.4, 2)),
    (0, (3, 1.4, 1.4, 1.4)),
    (0, (9, 2.5)),
    (0, (1.4, 1.2, 4, 1.2)),
    (0, (2.4, 2.4)),
)
MARKERS = ("o", "s", "^", "D", "v", "P", "X", "*")

PREFERRED_MODEL_ORDER = ("haiku45", "qwen3-14b", "nemo12b")

#: SPEC section 6: the organizer-added band.
BAND_LO, BAND_HI = 0.30, 0.40

#: bins for panel B, chosen so every bin holds enough item-runs to plot.
DOSE_BIN_EDGES = (0, 1, 2, 3, 5, 8, 16)
DOSE_BIN_LABELS = ("0", "1", "2", "3–4", "5–7", "8+")


def _order_models(slugs) -> list[str]:
    known = [s for s in PREFERRED_MODEL_ORDER if s in slugs]
    rest = sorted(s for s in slugs if s not in PREFERRED_MODEL_ORDER)
    return known + rest


def _style(fig, axes) -> None:
    fig.patch.set_facecolor(SURFACE)
    for ax in axes:
        ax.set_facecolor(SURFACE)
        ax.grid(True, which="major", color=GRID, linewidth=0.8, linestyle="-", zorder=0)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(AXIS)
            ax.spines[side].set_linewidth(0.8)
        ax.tick_params(colors=TEXT_SECONDARY, labelsize=7.5, length=3, width=0.8)


def _dodge_labels(items, min_gap: float):
    """Push near-identical y positions apart so end labels never collide."""
    items = sorted(items, key=lambda t: t[0])
    for i in range(1, len(items)):
        if items[i][0] - items[i - 1][0] < min_gap:
            items[i] = (items[i - 1][0] + min_gap, *items[i][1:])
    return items


def _panel_a(ax, df: pd.DataFrame, models: list[str], n_boot: int, seed: int) -> float:
    solv = df[~df["is_impossible"]]
    base = solv[solv["arm"] == "baseline"] if (solv["arm"] == "baseline").any() else solv

    ax.axvspan(BAND_LO, BAND_HI, color=BAND_FILL, zorder=1, lw=0)
    for x in (BAND_LO, BAND_HI):
        ax.axvline(x, color=BAND_EDGE, lw=0.8, zorder=1)

    ymax = 1.0
    end_labels = []
    for i, slug in enumerate(models):
        colour = SERIES[i % len(SERIES)]
        ls = LINESTYLES[i % len(LINESTYLES)]
        mk = MARKERS[i % len(MARKERS)]
        sub = base[base["model_slug"] == slug]
        if sub.empty:
            continue
        xs, ys, los, his = [], [], [], []
        for f, cell in sub.groupby("f_realised", sort=True):
            if not np.isfinite(f):
                continue
            k, n = int(cell["cheat"].sum()), int(len(cell))
            if n == 0:
                continue
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
        ax.fill_between(xs, los, his, color=colour, alpha=0.13, lw=0, zorder=2)
        ax.plot(
            xs, ys, color=colour, linestyle=ls, linewidth=2.0,
            solid_capstyle="round", solid_joinstyle="round", zorder=4,
            marker=mk, markersize=6.0, markeredgecolor=SURFACE, markeredgewidth=1.4,
            label=slug, clip_on=False,
        )
        end_labels.append((ys[-1], xs[-1], slug))

    # peer arms, if they ran: markers only, never a line (a different arm is not
    # a continuation of the baseline dose curve).
    peer = solv[solv["arm"].isin(["peer_neutral", "peer_tip"])]
    peer_handles = []
    if not peer.empty:
        for arm, marker, dx, face in (
            ("peer_neutral", "v", -0.012, "none"),
            ("peer_tip", "^", 0.012, None),
        ):
            sub = peer[peer["arm"] == arm]
            if sub.empty:
                continue
            for i, slug in enumerate(models):
                colour = SERIES[i % len(SERIES)]
                msub = sub[sub["model_slug"] == slug]
                if msub.empty:
                    continue
                for f, cell in msub.groupby("f_realised", sort=True):
                    if not np.isfinite(f) or len(cell) == 0:
                        continue
                    y = 100.0 * float(cell["cheat"].mean())
                    ymax = max(ymax, y)
                    ax.plot(
                        [float(f) + dx], [y], marker=marker, markersize=6.5,
                        markerfacecolor=colour if face is None else "none",
                        markeredgecolor=colour, markeredgewidth=1.6,
                        linestyle="none", zorder=5, clip_on=False,
                    )
            peer_handles.append(
                plt.Line2D(
                    [], [], marker=marker, linestyle="none", markersize=6.5,
                    markerfacecolor=TEXT_SECONDARY if face is None else "none",
                    markeredgecolor=TEXT_SECONDARY, markeredgewidth=1.4,
                    label="peer: tip" if arm == "peer_tip" else "peer: neutral",
                )
            )

    top = max(4.0, ymax * 1.16)
    ax.set_ylim(0, top)
    # headroom on the right so the direct end labels sit inside the panel
    ax.set_xlim(-0.035, 0.78)
    ax.set_xticks([0.0, 0.167, 0.286, 0.444, 0.60])
    ax.set_xticklabels(["0", "0.167", "0.286", "0.444", "0.60"])

    # in-band marker (short), with the verbatim caption as a figure footnote.
    ax.text(
        (BAND_LO + BAND_HI) / 2, top * 0.965, "~30–40%",
        ha="center", va="top", fontsize=6.8, color=TEXT_MUTED,
    )

    # direct end labels: text ink, the coloured marker beside them carries identity.
    for y, x, slug in _dodge_labels(end_labels, min_gap=top * 0.075):
        ax.annotate(
            slug, xy=(x, y), xytext=(7, 0), textcoords="offset points",
            va="center", ha="left", fontsize=7.0, color=TEXT_SECONDARY,
        )

    ax.set_xlabel("realised impossible fraction  f = I / (10 + I)", fontsize=8, color=TEXT_SECONDARY)
    ax.set_ylabel("cheat on solvable item-runs (%)", fontsize=8, color=TEXT_SECONDARY)
    ax.set_title(
        "A.  Dose — cheat rate on the ten fixed solvable tasks",
        fontsize=8.6, color=TEXT_PRIMARY, loc="left", pad=6,
    )

    handles, labels = ax.get_legend_handles_labels()
    handles += peer_handles
    labels += [h.get_label() for h in peer_handles]
    if len(handles) >= 2:
        leg = ax.legend(
            handles, labels, loc="upper left", fontsize=7.0, frameon=True,
            framealpha=1.0, edgecolor=GRID, facecolor=SURFACE, borderpad=0.45,
            handlelength=2.6, labelspacing=0.35,
        )
        leg.get_frame().set_linewidth(0.8)
        for t in leg.get_texts():
            t.set_color(TEXT_SECONDARY)
    return top


def _panel_b(ax, df: pd.DataFrame, models: list[str], n_boot: int, seed: int) -> float:
    solv = df[~df["is_impossible"]].copy()
    solv = solv[solv["n_impossible_before"].notna()]
    if solv.empty:
        ax.text(0.5, 0.5, "no solvable item-runs", ha="center", va="center",
                fontsize=8, color=TEXT_MUTED, transform=ax.transAxes)
        return 4.0

    solv["_bin"] = pd.cut(
        solv["n_impossible_before"].astype(int),
        bins=list(DOSE_BIN_EDGES),
        right=False,
        labels=list(DOSE_BIN_LABELS),
        include_lowest=True,
    )

    ymax = 1.0
    for i, slug in enumerate(models):
        colour = SERIES[i % len(SERIES)]
        ls = LINESTYLES[i % len(LINESTYLES)]
        mk = MARKERS[i % len(MARKERS)]
        sub = solv[solv["model_slug"] == slug]
        if sub.empty:
            continue
        xs, ys, los, his = [], [], [], []
        for _label, cell in sub.groupby("_bin", observed=True, sort=True):
            if len(cell) < 10:
                continue
            k, n = int(cell["cheat"].sum()), int(len(cell))
            lo, hi = bootstrap_rate_ci(cell, n_boot=n_boot, seed=seed)
            if not np.isfinite(lo) or not np.isfinite(hi):
                lo, hi = wilson_ci(k, n)
            xs.append(float(cell["n_impossible_before"].astype(float).mean()))
            ys.append(100.0 * k / n)
            los.append(100.0 * lo)
            his.append(100.0 * hi)
        if not xs:
            continue
        ymax = max(ymax, max(his))
        ax.fill_between(xs, los, his, color=colour, alpha=0.13, lw=0, zorder=2)
        ax.plot(
            xs, ys, color=colour, linestyle=ls, linewidth=2.0,
            solid_capstyle="round", solid_joinstyle="round", zorder=4,
            marker=mk, markersize=6.0, markeredgecolor=SURFACE, markeredgewidth=1.4,
            label=slug, clip_on=False,
        )

    top = max(4.0, ymax * 1.16)
    ax.set_ylim(0, top)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(2))
    ax.set_xlabel(
        "impossible items already seen in the batch", fontsize=8, color=TEXT_SECONDARY
    )
    ax.set_title(
        "B.  Cumulative dose — pooled across f",
        fontsize=8.6, color=TEXT_PRIMARY, loc="left", pad=6,
    )
    return top


def make_figure(
    df: pd.DataFrame,
    out_dir: str | Path,
    n_boot: int = 2000,
    seed: int = 0,
    stem: str = "figure",
) -> list[Path]:
    """Write ``figure.png`` (200 dpi) and ``figure.svg``; return both paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "text.color": TEXT_PRIMARY,
            "axes.labelcolor": TEXT_SECONDARY,
            "svg.fonttype": "path",
            "figure.dpi": 200,
            "savefig.dpi": 200,
        }
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.6), sharey=True)
    fig.subplots_adjust(left=0.082, right=0.988, top=0.855, bottom=0.285, wspace=0.14)
    _style(fig, (ax1, ax2))
    ax2.tick_params(labelleft=True)

    models = _order_models(sorted(df["model_slug"].dropna().unique())) if not df.empty else []
    if df.empty or not models:
        for ax in (ax1, ax2):
            ax.text(0.5, 0.5, "no item-runs", ha="center", va="center",
                    fontsize=9, color=TEXT_MUTED, transform=ax.transAxes)
    else:
        top_a = _panel_a(ax1, df, models, n_boot, seed)
        top_b = _panel_b(ax2, df, models, n_boot, seed)
        # one measure -> one scale, so the two panels are directly comparable
        ax1.set_ylim(0, max(top_a, top_b))

    fig.suptitle(
        "Cheating on still-solvable coding tasks vs the impossible fraction of the batch",
        fontsize=10.0, color=TEXT_PRIMARY, x=0.008, ha="left", y=0.975,
    )

    n_solv = int((~df["is_impossible"]).sum()) if not df.empty else 0
    n_batches = int(df["batch_id"].nunique()) if not df.empty else 0
    paragraphs = [
        f"Shaded vertical band: {BAND_CAPTION}.",
        f"Bands: cluster-bootstrap 95% CIs over batches ({n_boot:,} resamples, seed {seed}); "
        "unit = one item-run, cluster = the batch; both panels share one y scale.",
        f"{n_solv:,} solvable item-runs across {n_batches:,} batches. Cheat = "
        "D1∨D2∨D3∨D4∨D5 (programmatic detector, no LLM); it counts attempts.",
        "Panel B is confounded with f: a larger f means both more impossible items and a "
        "longer batch.",
        "Line style and marker, not colour alone, carry model identity — the series stay "
        "readable in grayscale print and under colour-vision deficiency.",
    ]
    wrapped: list[str] = []
    for para in paragraphs:
        wrapped.extend(textwrap.wrap(para, width=146) or [""])
    # give the footnote block its own room instead of letting it run into the axes
    fig.subplots_adjust(bottom=min(0.45, 0.115 + 0.0375 * len(wrapped)))
    fig.text(
        0.008, 0.012, "\n".join(wrapped), fontsize=6.2, color=TEXT_MUTED,
        va="bottom", linespacing=1.55,
    )

    paths = []
    for ext in ("png", "svg"):
        p = out_dir / f"{stem}.{ext}"
        fig.savefig(p, dpi=200, facecolor=SURFACE, edgecolor="none")
        paths.append(p)
    plt.close(fig)
    return paths
