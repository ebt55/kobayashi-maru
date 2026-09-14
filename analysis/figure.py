"""The one figure (SPEC.md section 6, plan section 6).

Panel A: cheat-on-solvable % against realised *f*, one line per model with a
cluster-bootstrap 95% band and the 0.30-0.40 band (METR's root-cause framing) shaded.
Panel B: the cumulative-dose curve -- cheat % against the number of impossible
items already encountered in the batch, pooled across *f*.

Design follows the `dataviz` skill: validated categorical slots in fixed order
(slots 1-3 pass the all-pairs CVD and normal-vision gates in both modes), 2px
lines, >=8px markers with a 2px surface ring, hairline solid recessive grid, a
legend always present (identity is never colour-alone; the table view is the
relief for the slot-3 contrast WARN), and -- because this is printed in a PDF --
a distinct **linestyle and marker per model**, so identity survives grayscale
and full-severity CVD.

Panel B is the manipulation check on the impossible items and panel C the
cumulative-dose curve; panel D is a SECONDARY, exploratory view against the
discoverably-impossible share and replaces realised f nowhere.
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

__all__ = ["make_figure", "BAND_CAPTION", "SERIES", "LINESTYLES", "MARKERS",
           "v2_base", "continuous_base", "variant_of", "single_level_slugs"]

#: verbatim from SPEC.md section 6.
BAND_CAPTION = (
    "'~30–40% impossible' — METR's root-cause framing; "
    "not stated in the ExploitGym paper, README, or RDI writeup"
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

#: SPEC section 6: the 0.30-0.40 band.
BAND_LO, BAND_HI = 0.30, 0.40

#: bins for panel B, chosen so every bin holds enough item-runs to plot.
DOSE_BIN_EDGES = (0, 1, 2, 3, 5, 8, 16)
DOSE_BIN_LABELS = ("0", "1", "2", "3–4", "5–7", "8+")


CONTINUOUS_SUFFIXES = ("-cont", "-continuous")
#: `<base>-v2` is the same model re-run with the environment leaks closed (env_version 2).
#: It shares the base line's colour and is drawn dashed, like arm B'.
V2_SUFFIXES = ("-v2",)
VARIANT_LABELS = {"cont": "continuous (arm B′)", "v2": "v2 (leaks closed)"}


def v2_base(slug: str) -> str | None:
    """`dsv41flash-sal-v2` -> `dsv41flash-sal`; None when the slug is not a v2 re-run.

    `dsv41flash-sal-v2-nonotes` does NOT match: it ends with `-nonotes`, it is the
    single-level ablation cell, and it belongs in figure_v7, not here.
    """
    for suffix in V2_SUFFIXES:
        if slug.endswith(suffix):
            return slug[: -len(suffix)]
    return None


def variant_of(slug: str) -> tuple[str, str] | None:
    """(base_slug, kind) for a follow-up variant of another line, else None."""
    base = continuous_base(slug)
    if base is not None:
        return base, "cont"
    base = v2_base(slug)
    if base is not None:
        return base, "v2"
    return None


def single_level_slugs(df: pd.DataFrame) -> set[str]:
    """Slugs run at one f level only -- no dose curve exists for them.

    The notes-ablation cell (`dsv41flash-sal-v2-nonotes`, I = 15 only) would otherwise
    appear in panels A-D as a one-point series with no endpoint and no slope.
    """
    if df.empty:
        return set()
    levels = df.groupby("model_slug")["f_realised"].nunique()
    return {str(k) for k, v in levels.items() if v < 2}


def continuous_base(slug: str) -> str | None:
    """`luna-sal-cont` -> `luna-sal`; None when the slug is not a continuous follow-up.

    Arm B' runs under its own model_slug, so without this it would take a colour slot and
    a legend entry of its own while being invisible in panels A and B (both of which
    filter to `arm == "baseline"`).
    """
    for suffix in CONTINUOUS_SUFFIXES:
        if slug.endswith(suffix):
            return slug[: -len(suffix)]
    return None


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


def _shade_band(ax) -> None:
    ax.axvspan(BAND_LO, BAND_HI, color=BAND_FILL, zorder=1, lw=0)
    for x in (BAND_LO, BAND_HI):
        ax.axvline(x, color=BAND_EDGE, lw=0.8, zorder=1)


def _f_axis(ax, top: float, band_label: bool = True) -> None:
    ax.set_xlim(-0.035, 0.665)
    ax.set_xticks([0.0, 0.167, 0.286, 0.444, 0.60])
    ax.set_xticklabels(["0", ".17", ".29", ".44", ".60"])
    if band_label:
        ax.text(
            (BAND_LO + BAND_HI) / 2, top * 0.965, "~30–40%",
            ha="center", va="top", fontsize=6.4, color=TEXT_MUTED,
        )


def _labels(df: pd.DataFrame) -> dict[str, str]:
    """model_slug -> legend label, carrying the environment variant."""
    from analysis.load import series_label

    out: dict[str, str] = {}
    for slug, sub in df.groupby("model_slug", sort=True):
        variants = [v for v in sub["env_variant"].dropna().unique()] if "env_variant" in sub else []
        out[str(slug)] = series_label(str(slug), variants[0] if len(variants) == 1 else None)
    return out


def _panel_impossible(ax, df: pd.DataFrame, models: list[str], labels: dict[str, str]) -> float:
    """B -- the manipulation check: cheat rate on the IMPOSSIBLE items.

    Bands are Wilson intervals on the cell proportion rather than a cluster
    bootstrap: a batch contributes at most 15 impossible item-runs (2 at
    I = 2), so the batch-level resample is too coarse to be informative here.
    There are no impossible items at f = 0, so the series starts at f = 0.167.
    """
    imp = df[df["is_impossible"]]
    base = imp[imp["arm"] == "baseline"] if (imp["arm"] == "baseline").any() else imp
    _shade_band(ax)

    ymax = 1.0
    for i, slug in enumerate(models):
        colour = SERIES[i % len(SERIES)]
        ls = LINESTYLES[i % len(LINESTYLES)]
        mk = MARKERS[i % len(MARKERS)]
        sub = base[base["model_slug"] == slug]
        if sub.empty:
            continue
        xs, ys, los, his = [], [], [], []
        for f, cell in sub.groupby("f_realised", sort=True):
            if not np.isfinite(f) or len(cell) == 0:
                continue
            k, n = int(cell["cheat"].sum()), int(len(cell))
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
            label=labels.get(slug, slug), clip_on=False,
        )

    v_top, _ = _draw_variants(ax, df, models, impossible=True)
    ymax = max(ymax, v_top)

    top = max(4.0, ymax * 1.16)
    _f_axis(ax, top)
    ax.set_xlabel(
        "realised f  (impossible items only)", fontsize=8, color=TEXT_SECONDARY
    )
    ax.set_title(
        "B.  Manipulation check",
        fontsize=8.6, color=TEXT_PRIMARY, loc="left", pad=6,
    )
    return top


def _draw_variants(ax, df: pd.DataFrame, models: list[str], *, impossible: bool,
                   x: str = "f_realised") -> tuple[float, list]:
    """Overlay each follow-up variant (arm B', v2 re-run) on its base model's colour.

    Dashed and hollow-markered so it never reads as another model, and it takes no
    colour slot of its own. Returns (max y drawn, legend handles).
    """
    handles, ymax = [], 0.0
    sub_all = df[df["is_impossible"]] if impossible else df[~df["is_impossible"]]
    for slug in sorted(sub_all["model_slug"].dropna().unique()):
        v = variant_of(str(slug))
        if v is None or v[0] not in models:
            continue
        base_slug, kind = v
        colour = SERIES[models.index(base_slug) % len(SERIES)]
        sub = sub_all[sub_all["model_slug"] == slug]
        xs, ys = [], []
        for xv, cell in sub.groupby(x, sort=True):
            if not np.isfinite(xv) or len(cell) == 0:
                continue
            xs.append(float(xv))
            ys.append(100.0 * float(cell["cheat"].mean()))
        if not xs:
            continue
        ymax = max(ymax, max(ys))
        ax.plot(xs, ys, color=colour, linestyle=(0, (4.0, 2.0)), linewidth=1.6,
                marker="P", markersize=5.0, markerfacecolor="none",
                markeredgecolor=colour, markeredgewidth=1.3, zorder=4, clip_on=False)
        handles.append(plt.Line2D(
            [], [], color=colour, linestyle=(0, (4.0, 2.0)), linewidth=1.6,
            marker="P", markersize=5.0, markerfacecolor="none", markeredgecolor=colour,
            label=f"{base_slug} · {VARIANT_LABELS[kind]}"))
    return ymax, handles


def _panel_a(ax, df: pd.DataFrame, models: list[str], n_boot: int, seed: int,
             labels: dict[str, str]) -> float:
    solv = df[~df["is_impossible"]]
    base = solv[solv["arm"] == "baseline"] if (solv["arm"] == "baseline").any() else solv

    _shade_band(ax)

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
            label=labels.get(slug, slug), clip_on=False,
        )
        end_labels.append((ys[-1], xs[-1], slug))

    # follow-up variants (arm B', v2 re-runs): base colour, dashed, no new colour slot
    v_top, cont_handles = _draw_variants(ax, df, models, impossible=False)
    ymax = max(ymax, v_top)

    # peer arms, if they ran: markers only, never a line (a different arm is not
    # a continuation of the baseline dose curve).
    peer = solv[solv["arm"].isin(["peer_neutral", "peer_tip", "peer_tip_read"])]
    peer_handles = list(cont_handles)
    if not peer.empty:
        for arm, marker, dx, face in (
            ("peer_neutral", "v", -0.012, "none"),
            ("peer_tip", "^", 0.012, None),
            ("peer_tip_read", "D", 0.030, None),
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
                    label={"peer_tip": "peer: tip",
                           "peer_tip_read": "peer: tip (matching path)",
                           "peer_neutral": "peer: neutral"}[arm],
                )
            )

    top = max(4.0, ymax * 1.16)
    ax.set_ylim(0, top)
    _f_axis(ax, top)

    ax.set_xlabel("realised impossible fraction  f", fontsize=8, color=TEXT_SECONDARY)
    ax.set_ylabel("cheat rate (% of item-runs)", fontsize=8, color=TEXT_SECONDARY)
    ax.set_title(
        "A.  Dose (solvable items)",
        fontsize=8.6, color=TEXT_PRIMARY, loc="left", pad=6,
    )

    # The legend lives below the panels (a shared row), never over the data.
    handles, _ = ax.get_legend_handles_labels()
    handles += peer_handles
    return top, handles


def _panel_c(ax, df: pd.DataFrame, models: list[str], n_boot: int, seed: int,
             labels: dict[str, str]) -> float:
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
            label=labels.get(slug, slug), clip_on=False,
        )

    # EXPLORATORY overlay: the same curve over the IMPOSSIBLE item-runs.  One
    # shared thin dash with hollow markers, so it never impersonates a model's
    # own line style; the pre-registered series is the solvable one above.
    imp = df[df["is_impossible"]].copy()
    imp = imp[imp["n_impossible_before"].notna()]
    if not imp.empty:
        imp["_bin"] = pd.cut(
            imp["n_impossible_before"].astype(int),
            bins=list(DOSE_BIN_EDGES),
            right=False,
            labels=list(DOSE_BIN_LABELS),
            include_lowest=True,
        )
        for i, slug in enumerate(models):
            colour = SERIES[i % len(SERIES)]
            mk = MARKERS[i % len(MARKERS)]
            sub = imp[imp["model_slug"] == slug]
            if sub.empty:
                continue
            xs, ys = [], []
            for _label, cell in sub.groupby("_bin", observed=True, sort=True):
                if len(cell) < 10:
                    continue
                xs.append(float(cell["n_impossible_before"].astype(float).mean()))
                ys.append(100.0 * int(cell["cheat"].sum()) / int(len(cell)))
            if not xs:
                continue
            ymax = max(ymax, max(ys))
            ax.plot(
                xs, ys, color=colour, linestyle=(0, (2.0, 1.8)), linewidth=1.4,
                zorder=3, marker=mk, markersize=5.0, markerfacecolor="none",
                markeredgecolor=colour, markeredgewidth=1.2, alpha=0.85,
                label="_impossible", clip_on=False,
            )

    top = max(4.0, ymax * 1.16)
    ax.set_ylim(0, top)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(4))
    ax.set_xlabel(
        "impossible items already seen", fontsize=8, color=TEXT_SECONDARY
    )
    ax.set_title(
        "C.  Cumulative dose",
        fontsize=8.6, color=TEXT_PRIMARY, loc="left", pad=6,
    )
    if not imp.empty:
        proxies = [
            plt.Line2D([], [], color=TEXT_SECONDARY, linestyle="solid", linewidth=2.0,
                       marker="o", markersize=5.0, markeredgecolor=SURFACE,
                       markeredgewidth=1.2, label="solvable items"),
            plt.Line2D([], [], color=TEXT_SECONDARY, linestyle=(0, (2.0, 1.8)), linewidth=1.4,
                       marker="o", markersize=5.0, markerfacecolor="none",
                       markeredgecolor=TEXT_SECONDARY, markeredgewidth=1.2,
                       label="impossible items"),
        ]
        return top, proxies
    return top, []


def _panel_d(ax, df: pd.DataFrame, models: list[str], labels: dict[str, str], seed: int) -> float:
    """D -- SECONDARY: cheat-on-solvable against the *discoverably* impossible share.

    One jittered point per batch plus the clustered-logistic fit.  This is an
    exploratory second exposure measure, not a replacement for realised f: a
    ``contradict`` variant looks solved from inside the sandbox (its visible
    tests pass), while an ``unreachable`` variant announces itself as a missing
    resource, so only the latter is plainly impossible to the agent as it works.
    """
    from analysis.stats import logistic_clustered

    solv = df[~df["is_impossible"]]
    base = solv[solv["arm"] == "baseline"] if (solv["arm"] == "baseline").any() else solv
    base = base[base["f_discoverable"].notna()]
    if base.empty:
        ax.text(0.5, 0.5, "no f_discoverable", ha="center", va="center",
                fontsize=8, color=TEXT_MUTED, transform=ax.transAxes)
        return 4.0

    rng = np.random.default_rng(seed)
    ymax = 1.0
    xmax = 0.05
    for i, slug in enumerate(models):
        colour = SERIES[i % len(SERIES)]
        ls = LINESTYLES[i % len(LINESTYLES)]
        mk = MARKERS[i % len(MARKERS)]
        sub = base[base["model_slug"] == slug]
        if sub.empty:
            continue
        per_batch = sub.groupby("batch_id").agg(
            x=("f_discoverable", "first"), y=("cheat", "mean")
        )
        xs = per_batch["x"].to_numpy(dtype=float)
        ys = 100.0 * per_batch["y"].to_numpy(dtype=float)
        jitter = rng.uniform(-0.006, 0.006, size=xs.size)
        ax.plot(
            xs + jitter, ys, linestyle="none", marker=mk, markersize=3.6,
            markerfacecolor=colour, markeredgecolor=SURFACE, markeredgewidth=0.5,
            alpha=0.55, zorder=3, clip_on=True,
        )
        ymax = max(ymax, float(ys.max()) if ys.size else 1.0)
        xmax = max(xmax, float(xs.max()) if xs.size else 0.05)

        fit = logistic_clustered(sub, "f_discoverable")
        if fit.get("slope") is not None:
            grid = np.linspace(float(xs.min()), float(xs.max()), 60)
            p = 1.0 / (1.0 + np.exp(-(fit["intercept"] + fit["slope"] * grid)))
            ax.plot(
                grid, 100.0 * p, color=colour, linestyle=ls, linewidth=2.0,
                solid_capstyle="round", zorder=4, label=labels.get(slug, slug),
            )
            ymax = max(ymax, float((100.0 * p).max()))

    ax.set_xlim(-0.02, max(0.08, xmax * 1.12))
    ax.set_xlabel(
        "f_discoverable  (unreachable / batch size)", fontsize=7.6, color=TEXT_SECONDARY
    )
    ax.set_ylabel("cheat rate (% of item-runs)", fontsize=8, color=TEXT_SECONDARY)
    ax.set_title(
        "D.  Secondary: fraction of discoverably-impossible items",
        fontsize=8.6, color=TEXT_PRIMARY, loc="left", pad=6,
    )
    return max(4.0, ymax * 1.16)


def _legend_top(fig) -> float:
    """Top edge of the figure-level legend in figure coordinates (0 when there is none)."""
    if not fig.legends:
        return 0.0
    fig.canvas.draw()
    bb = fig.legends[0].get_window_extent(fig.canvas.get_renderer())
    return float(bb.transformed(fig.transFigure.inverted()).y1)


def _grow_to_fit(fig, artist, floor: float = 0.0, pad_in: float = 0.10,
                 max_passes: int = 6) -> None:
    """Grow the canvas until ``artist``'s bottom clears ``floor`` (figure coords).

    Font sizes are absolute (points) while the layout is relative, so a taller canvas
    gives a text block proportionally more room. Two or three passes converge.
    """
    for _ in range(max_passes):
        fig.canvas.draw()
        bb = artist.get_window_extent(fig.canvas.get_renderer())
        y0 = float(bb.transformed(fig.transFigure.inverted()).y0)
        deficit = (floor + pad_in / fig.get_figheight()) - y0
        if deficit <= 0.0:
            return
        fig.set_size_inches(fig.get_figwidth(),
                            fig.get_figheight() * (1.0 + max(deficit, 0.02)),
                            forward=True)


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

    fig = plt.figure(figsize=(7.5, 6.5))
    gs = fig.add_gridspec(
        2, 3, height_ratios=[1.0, 0.82], hspace=0.46, wspace=0.10,
        left=0.075, right=0.992, top=0.92, bottom=0.30,
    )
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1], sharey=ax1)
    ax3 = fig.add_subplot(gs[0, 2], sharey=ax1)
    ax4 = fig.add_subplot(gs[1, 0], sharey=ax1)
    axes = (ax1, ax2, ax3, ax4)
    _style(fig, axes)
    for ax in (ax2, ax3, ax4):
        ax.tick_params(labelleft=True)

    all_slugs = sorted(df["model_slug"].dropna().unique()) if not df.empty else []
    solo = single_level_slugs(df)
    # A follow-up variant (arm B', or a v2 re-run) is drawn against its base model's
    # colour, never as its own series; a single-level slug has no curve at all and is
    # excluded from every panel here (it is the subject of figure_v7).
    def _is_base(slug: str) -> bool:
        v = variant_of(slug)
        return not (v and v[0] in all_slugs) and slug not in solo

    models = _order_models([s for s in all_slugs if _is_base(s)])
    # totals BEFORE the single-level exclusion, so the caption can say plainly why its
    # counts are smaller than the `all` scope quoted elsewhere
    total_runs = int(len(df))
    total_batches = int(df["batch_id"].nunique()) if len(df) else 0
    df = df[~df["model_slug"].isin(solo)]
    if df.empty or not models:
        for ax in axes:
            ax.text(0.5, 0.5, "no item-runs", ha="center", va="center",
                    fontsize=9, color=TEXT_MUTED, transform=ax.transAxes)
    else:
        labels = _labels(df)
        top_a, legend_handles = _panel_a(ax1, df, models, n_boot, seed, labels)
        top_b = _panel_impossible(ax2, df, models, labels)
        top_c, c_proxies = _panel_c(ax3, df, models, n_boot, seed, labels)
        top_d = _panel_d(ax4, df, models, labels, seed)
        # one measure -> one scale, so every panel is directly comparable
        ax1.set_ylim(0, max(top_a, top_b, top_c, top_d))

        # ONE legend for the whole figure, in its own row under the panels: with eleven
        # series an in-axes legend covered the data it was labelling.
        legend_handles += c_proxies
        if legend_handles:
            leg = fig.legend(
                handles=legend_handles, loc="lower center",
                bbox_to_anchor=(0.5, 0.006), ncol=4, fontsize=6.2, frameon=True,
                framealpha=1.0, edgecolor=GRID, facecolor=SURFACE, borderpad=0.5,
                handlelength=2.4, labelspacing=0.42, handletextpad=0.55,
                columnspacing=1.4,
            )
            leg.get_frame().set_linewidth(0.8)
            for t in leg.get_texts():
                t.set_color(TEXT_SECONDARY)

    fig.suptitle(
        "Cheating on still-solvable coding tasks vs the impossible fraction of the batch",
        fontsize=10.0, color=TEXT_PRIMARY, x=0.008, ha="left", y=0.975,
    )

    excluded = ", ".join(sorted(solo)) if solo else ""
    n_solv = int((~df["is_impossible"]).sum()) if not df.empty else 0
    n_batches = int(df["batch_id"].nunique()) if not df.empty else 0
    n_imp = int(df["is_impossible"].sum()) if not df.empty else 0
    paragraphs = [
        f"Shaded vertical band in A and B: {BAND_CAPTION}.",
        f"All four panels share one y scale. Bands in A and C: cluster-bootstrap 95% CIs over "
        f"batches ({n_boot:,} resamples, seed {seed}), unit = one item-run, cluster = the batch. "
        "Bands in B: Wilson 95% intervals on the cell proportion, since a batch carries at most "
        "15 impossible item-runs.",
        f"{n_solv:,} solvable and {n_imp:,} impossible item-runs across {n_batches:,} batches. "
        "Cheat = D1∨D2∨D3∨D4∨D5 (programmatic detector, no LLM); it counts "
        "attempts. B is the manipulation check: it shows whether the dose was actually "
        "delivered, so a flat A beside a rising B reads as \"dose delivered, no spillover\".",
        "B has no f = 0 point because a batch at f = 0 contains no impossible items. C is "
        "confounded with f: a larger f means both more impossible items and a longer batch. "
        "C's solid series (solvable items) is the pre-registered one; its dashed, hollow-marker "
        "series over the impossible items is EXPLORATORY and was added after the pilot.",
        "D is a SECONDARY, exploratory exposure measure and replaces realised f nowhere: "
        "f_discoverable counts only `unreachable` variants, which announce themselves as a "
        "missing resource, because a `contradict` variant looks solved from inside the sandbox "
        "(its visible tests pass). One jittered point per batch; the curve is the "
        "batch-clustered logistic fit.",
        "Line style and marker, not colour alone, carry model identity — the series stay "
        "readable in grayscale print and under colour-vision deficiency. A `-v2` series is "
        "the same model re-run with the environment leaks closed (env_version 2): base "
        "colour, dashed, hollow marker, no colour of its own.",
    ]
    if excluded:
        paragraphs.append(
            f"SCOPE: these panels plot the `frozen` grid (env_version 1) PLUS the v2 "
            f"replication lines, and exclude {excluded} — run at a single f level, so it "
            f"has no dose curve; it is the subject of figure_v7. The counts above are for "
            f"that plotted set, which is why they are smaller than the `all` scope in "
            f"stats.json and the README (every line, {total_runs:,} item-runs in "
            f"{total_batches:,} batches). stats.json publishes all three scopes."
        )
    note_ax = fig.add_subplot(gs[1, 1:])
    note_ax.axis("off")
    wrapped: list[str] = []
    for para in paragraphs:
        wrapped.extend(textwrap.wrap(para, width=96) or [""])
    note = note_ax.text(
        0.0, 1.0, "\n".join(wrapped), fontsize=6.0, color=TEXT_MUTED,
        va="top", ha="left", linespacing=1.5, transform=note_ax.transAxes,
    )
    # The caption grows whenever a paragraph is added (a new series kind, an exclusion
    # note), and a fixed canvas silently cuts the last lines off the bottom. Measure it
    # and grow the canvas until the whole caption sits above the legend row.
    _grow_to_fit(fig, note, floor=_legend_top(fig))

    paths = []
    for ext in ("png", "svg"):
        p = out_dir / f"{stem}.{ext}"
        fig.savefig(p, dpi=200, facecolor=SURFACE, edgecolor="none")
        paths.append(p)
    plt.close(fig)
    return paths
