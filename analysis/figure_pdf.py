"""Report-PDF variants of the two argument figures, sized for a 6.5-inch text column.

``fig1_dose``       — the dose curve: ``figure_main``'s two line panels, and nothing else.
``fig2_mechanism``  — the notes crosstab (``figure_mechanism`` panel A) beside the notes
                      ablation (``figure_v7`` panel B): the correlation, and the
                      experiment that switches it off, side by side.

These exist because the README figures bake their caption paragraph into the canvas and
are laid out to be read at full browser width. Dropped into a 6.5in text column that
caption block turns into grey mush and eats half the image. Here the captions, the
suptitles and the two EVIDENCE / NOT EVIDENCE boxes all come *out* of the image and are
set as real type in the report; what is left is the plot, drawn at its final print width
so that every point size on the canvas is a point size on the page.

Nothing in this module computes a statistic, reads a different file, or re-draws a panel.
Each panel is produced by the same function that produces the README figure —
``analysis.figure_report._draw_lines`` and ``._panel_notes``, and
``analysis.figure_v7._panel_ablation`` — so the report figures cannot drift away from the
frozen ones. This module only chooses the canvas, the type sizes, and where things sit.

    uv run python -m analysis.figure_pdf --runs results/runs --out results/analysis/report
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402

from analysis.figure import (  # noqa: E402
    GRID,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    _f_axis,
    _shade_band,
    _style,
)
from analysis.figure_report import (  # noqa: E402
    SHORT_NAMES,
    _draw_lines,
    _name,
    _notes_rows,
    _panel_notes,
    _style_for,
)
from analysis.figure_v7 import (  # noqa: E402
    IMPOSSIBLE_KINDS,
    _ablation_ymax,
    _panel_ablation,
)

__all__ = ["make_pdf_figures", "make_dose_figure", "make_mechanism_combo_figure",
           "FIG_WIDTH_IN", "DPI", "MIN_PT", "TYPE_SIZES"]

#: the report's text column, and the resolution the PDF wants.
FIG_WIDTH_IN = 6.5
DPI = 300

#: the legibility floor: nothing on either canvas may be smaller than this at print size.
MIN_PT = 7.0

# Type sizes. The canvas is drawn at its final print width, so these ARE final points --
# no shrink-to-fit happens between here and the page, and none of them may go under
# MIN_PT. They sit above the figure_report sizes because those were drawn at 7.4in and
# then shrunk by the layout.
PT_TITLE = 10.0     # panel titles
PT_TAG = 8.2        # the CORRELATIONAL / CAUSAL line under a panel title
PT_AXIS = 9.0       # axis labels
PT_TICK = 8.5       # tick labels
PT_TICK_GROUP = 8.0  # five group labels across one panel: the tightest tick row there is
PT_LEGEND = 8.0     # legend
PT_ANNOT = 7.4      # counts printed on bars and markers, the band label

TYPE_SIZES = {"panel title": PT_TITLE, "panel tag": PT_TAG, "axis label": PT_AXIS,
              "tick label": PT_TICK, "group tick label": PT_TICK_GROUP,
              "legend": PT_LEGEND, "in-plot annotation": PT_ANNOT}

#: breathing room between stacked blocks, in inches.
PAD_IN = 0.055
GAP_IN = 0.07

#: the model whose ablation panel B draws. Panel B of figure_v7 hardcodes the first
#: series colour; here it has to match the DeepSeek bars in panel A and the DeepSeek line
#: in fig1, or the same model changes colour between two panels of one figure.
ABLATION_SLUG = "dsv41flash-sal"

#: One line per group, because five two-line labels under a 3.6in panel touch. The
#: re-runs lose "(re-run)" for "v2", which is what the directory and the report call them.
GROUP_TICKS = {"dsv41flash-sal": "DeepSeek", "dsv41flash-sal-v2": "DeepSeek v2",
               "glm53flash-sal": "GLM-5.3", "glm53flash-sal-v2": "GLM-5.3 v2",
               "haiku45": "Haiku 4.5"}


def _rc() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": TEXT_PRIMARY,
                         "axes.labelcolor": TEXT_SECONDARY, "svg.fonttype": "path",
                         "figure.dpi": DPI, "savefig.dpi": DPI})


# ------------------------------------------------------------------ measuring helpers

def _renderer(fig):
    fig.canvas.draw()
    return fig.canvas.get_renderer()


def _text_width_in(fig, s: str, size: float) -> float:
    """Width of ``s`` in inches, measured rather than estimated from a character count."""
    w, _h, _d = fig.canvas.get_renderer().get_text_width_height_descent(
        s, FontProperties(family="DejaVu Sans", size=size), False)
    return float(w) / float(fig.dpi)


def _wrap_to_width(fig, text: str, size: float, width_in: float) -> str:
    """Greedy wrap to a measured width. A leading panel letter stays with its first word.

    ``textwrap`` wraps on a character count, which is a poor proxy at 10pt in a 2.6in
    panel: one word too many and the title overhangs into the next panel.
    """
    words = text.split()
    if len(words) > 1 and len(words[0]) <= 3 and words[0].endswith("."):
        words = [f"{words[0]}  {words[1]}", *words[2:]]
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}" if cur else w
        if cur and _text_width_in(fig, trial, size) > width_in:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def _panel_width_in(fig, ax) -> float:
    return ax.get_position().width * fig.get_figwidth()


def _tag_lines(fig, ax, tag: str | None) -> int:
    """How many lines the tag will take once wrapped to this panel."""
    if not tag:
        return 0
    return _wrap_to_width(fig, tag, PT_TAG, _panel_width_in(fig, ax)).count("\n") + 1


def _panel_title(fig, ax, text: str, tag: str | None = None, pad_lines: int = 0):
    """Panel letter + title, wrapped to the panel's own width, over an optional tag line.

    Same shape as ``figure_report._panel_head`` -- title padded by the height of whatever
    sits under it, with ``pad_lines`` a floor so two titles in a row line up -- but at
    report type sizes, and with the title wrapped to the panel instead of overhanging
    into its neighbour or off the canvas.
    """
    width_in = _panel_width_in(fig, ax)
    title = _wrap_to_width(fig, text, PT_TITLE, width_in)
    n_tag = 0
    tag_artist = None
    if tag:
        body = _wrap_to_width(fig, tag, PT_TAG, width_in)
        n_tag = body.count("\n") + 1
        tag_artist = ax.text(0.0, 1.014, body, transform=ax.transAxes, fontsize=PT_TAG,
                             color=TEXT_SECONDARY, va="bottom", ha="left",
                             linespacing=1.3)
    # set_title returns the artist, which for loc="left" is NOT ax.title: measuring
    # ax.title here would measure the empty centre title and clip the real one away.
    title_artist = ax.set_title(
        title, fontsize=PT_TITLE, color=TEXT_PRIMARY, loc="left",
        pad=5.0 + max(pad_lines, n_tag) * (PT_TAG * 1.3 + 2.2))
    return [a for a in (title_artist, tag_artist) if a is not None]


def _bump_type(ax, floor: float = MIN_PT) -> None:
    """Raise anything a reused panel drew below the legibility floor.

    ``_f_axis`` labels the shaded band at 6.4pt and ``_panel_ablation`` prints its counts
    at 6.2pt: both were drawn on a canvas that got shrunk, and both are under the bar
    here.
    """
    for t in ax.texts:
        if t.get_fontsize() < floor:
            t.set_fontsize(floor)


def _declutter(fig, ax, gap_pt: float = 1.6, passes: int = 12) -> list[str]:
    """Push overlapping in-plot count labels apart vertically; report what moved.

    The counts are the point of both mechanism panels, so none of them may be dropped or
    shrunk out of legibility. At 6.5in two of them collide (the ablation's bar count and
    its contradict-marker count both sit near zero on the notes-off bar), so the higher
    one steps up until the boxes clear.
    """
    texts = [t for t in ax.texts if t.get_transform() is ax.transData and t.get_text()]
    moved: dict[str, int] = {}
    gap_px = gap_pt * fig.dpi / 72.0
    for _ in range(passes):
        r = _renderer(fig)
        boxes = [t.get_window_extent(r) for t in texts]
        clash = False
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, b = boxes[i], boxes[j]
                if not (a.x0 - gap_px < b.x1 and b.x0 - gap_px < a.x1
                        and a.y0 - gap_px < b.y1 and b.y0 - gap_px < a.y1):
                    continue
                clash = True
                k = i if a.y0 >= b.y0 else j
                dy = (min(a.y1, b.y1) - max(a.y0, b.y0)) + gap_px
                x, y = texts[k].get_position()
                px = ax.transData.transform((x, y))
                texts[k].set_position(
                    (x, float(ax.transData.inverted().transform((px[0], px[1] + dy))[1])))
                moved[texts[k].get_text()] = moved.get(texts[k].get_text(), 0) + 1
                break
            if clash:
                break
        if not clash:
            break
    return sorted(moved)


def _above_in(fig, ax, artists) -> float:
    """Inches occupied above the axes by the title block (its artists, measured)."""
    r = _renderer(fig)
    inv = fig.transFigure.inverted()
    y1 = ax.get_position().y1
    for a in artists:
        if a is not None:
            y1 = max(y1, a.get_window_extent(r).transformed(inv).y1)
    return (y1 - ax.get_position().y1) * fig.get_figheight()


def _below_in(fig, ax, extras=()) -> float:
    """Inches occupied below the axes by tick labels, the axis label and any footnote."""
    r = _renderer(fig)
    inv = fig.transFigure.inverted()
    y0 = ax.xaxis.get_tightbbox(r).transformed(inv).y0
    for a in extras:
        if a is not None:
            y0 = min(y0, a.get_window_extent(r).transformed(inv).y0)
    return (ax.get_position().y0 - y0) * fig.get_figheight()


def _fit_vertical(fig, gs, legend, above_in: float, below_in: float,
                  min_plot_in: float, height_in: float) -> float:
    """Stack title / plot / axis / legend in inches, growing the canvas if it will not fit.

    Font sizes are absolute and the gridspec is fractional, so every block's height in
    inches is fixed and only the plot can absorb a change of canvas height. That makes
    the arithmetic exact instead of iterative.
    """
    legend_in = 0.0
    if legend is not None:
        r = _renderer(fig)
        legend_in = (legend.get_window_extent(r)
                     .transformed(fig.transFigure.inverted()).height) * fig.get_figheight()
    fixed = above_in + below_in + legend_in + 2 * PAD_IN + GAP_IN
    height = max(height_in, fixed + min_plot_in)
    fig.set_size_inches(FIG_WIDTH_IN, height, forward=True)
    if legend is not None:
        legend.set_bbox_to_anchor((0.5, PAD_IN / height), transform=fig.transFigure)
    gs.update(top=1.0 - (above_in + PAD_IN) / height,
              bottom=(PAD_IN + legend_in + GAP_IN + below_in) / height)
    return height


def _save(fig, out_dir: Path, stem: str) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in ("png", "svg"):
        p = out_dir / f"{stem}.{ext}"
        fig.savefig(p, dpi=DPI, facecolor=SURFACE, edgecolor="none")
        paths.append(p)
    plt.close(fig)
    return paths


def _legend(fig, handles, ncol: int, **kw):
    leg = fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, PAD_IN),
                     ncol=ncol, fontsize=PT_LEGEND, frameon=True, framealpha=1.0,
                     edgecolor=GRID, facecolor=SURFACE, borderpad=0.5, labelspacing=0.42,
                     handletextpad=0.6, **kw)
    leg.get_frame().set_linewidth(0.9)
    for t in leg.get_texts():
        t.set_color(TEXT_SECONDARY)
    return leg


# ------------------------------------------------------------------------- fig1_dose

def _short_legend(label: str) -> str:
    """The legend has to fit two columns inside 6.5in; the caption carries the rest.

    Only the parenthetical wording is cut. Every published model identity survives intact,
    because the identity is the part a reader has to match across figures.
    """
    return (label
            .replace(", re-run with environment leaks closed", ", leaks closed")
            .replace("  ← pre-registered primary line", " (pre-registered primary)"))


def make_dose_figure(df: pd.DataFrame, out_dir: str | Path, n_boot: int = 2000,
                     seed: int = 0, stem: str = "fig1_dose",
                     height_in: float = 3.6) -> list[Path]:
    """Claim 1 at report size: the two dose panels, the legend, and nothing else.

    Dropped against ``figure_main``: the suptitle, the grey caption block, the two
    EVIDENCE / NOT EVIDENCE boxes, the definition of f, and the two takeaway subtitles --
    all of them report prose, and the subtitles specifically because at 6.5in they cost
    more plot height than they are worth. Panel A's title is shortened so that both
    titles sit on one line. Every line, band, marker and axis is the same call that draws
    figure_main, and the y scale is computed by the same expression, so the two figures
    plot the same numbers on the same scale.
    """
    out_dir = Path(out_dir)
    _rc()
    fig = plt.figure(figsize=(FIG_WIDTH_IN, height_in))
    gs = fig.add_gridspec(1, 2, wspace=0.20, left=0.083, right=0.988,
                          top=0.86, bottom=0.30)
    ax1, ax2 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    _style(fig, (ax1, ax2))
    for ax in (ax1, ax2):
        ax.tick_params(labelsize=PT_TICK, length=3.2, width=0.9)
        _shade_band(ax)

    handles, ymax_a = _draw_lines(ax1, df, impossible=False, n_boot=n_boot, seed=seed)
    _, ymax_b = _draw_lines(ax2, df, impossible=True, n_boot=n_boot, seed=seed)
    if not handles:
        for ax in (ax1, ax2):
            ax.text(0.5, 0.5, "no item-runs", ha="center", va="center",
                    transform=ax.transAxes, fontsize=PT_AXIS, color=TEXT_SECONDARY)
    top = max(10.0, ymax_a, ymax_b) * 1.16          # identical to figure_main

    for ax, band_label in ((ax1, False), (ax2, True)):
        _f_axis(ax, top, band_label=band_label)
        ax.set_ylim(0, top)
        ax.set_xlabel("fraction of the batch that is impossible,  f",
                      fontsize=PT_AXIS, color=TEXT_SECONDARY, labelpad=2)
        ax.set_ylabel("cheat rate (% of item-runs)", fontsize=PT_AXIS,
                      color=TEXT_SECONDARY)
        _bump_type(ax, PT_ANNOT)                     # the 6.4pt "~30-40%" band label

    # both titles on one line at this width: a two-line title over one panel and a
    # one-line title over the other buys nothing and costs the plot a quarter inch.
    head1 = _panel_title(fig, ax1, "A.  Cheating on the solvable tasks")
    head2 = _panel_title(fig, ax2, "B.  Cheating on the impossible tasks")

    leg = None
    if handles:
        for h in handles:
            h.set_label(_short_legend(h.get_label()))
        leg = _legend(fig, handles, ncol=2, handlelength=2.9, columnspacing=1.4)

    _fit_vertical(fig, gs, leg,
                  above_in=max(_above_in(fig, ax1, head1), _above_in(fig, ax2, head2)),
                  below_in=max(_below_in(fig, ax1), _below_in(fig, ax2)),
                  min_plot_in=2.15, height_in=height_in)
    return _save(fig, out_dir, stem)


# -------------------------------------------------------------------- fig2_mechanism

def _load_mech(out_dir: Path, mech: dict | None) -> dict:
    if mech is not None:
        return mech
    for cand in (out_dir / "mechanism.json",
                 out_dir.parent / "mechanism.json",
                 Path(__file__).resolve().parents[1] / "results" / "analysis"
                 / "mechanism.json"):
        if cand.is_file():
            return json.loads(cand.read_text(encoding="utf-8"))
    return {}


def make_mechanism_combo_figure(df: pd.DataFrame, out_dir: str | Path,
                                mech: dict | None = None, stem: str = "fig2_mechanism",
                                height_in: float = 3.4) -> list[Path]:
    """Claims 2 and 3 at report size: the correlation beside the experiment.

    Panel A is ``figure_mechanism`` panel A (the notes crosstab) and panel B is
    ``figure_v7`` panel B (the ablation at f = 0.60) -- the two halves of one argument,
    which in the README live in different files and so never appear side by side. Both
    caption blocks and both suptitles are dropped; every printed count is kept.
    """
    out_dir = Path(out_dir)
    mech = _load_mech(out_dir, mech)
    _rc()
    fig = plt.figure(figsize=(FIG_WIDTH_IN, height_in))
    # panel A carries five groups of two bars and needs most of the width; the gap is
    # only as wide as panel B's own y axis needs, not the usual third of a panel.
    gs = fig.add_gridspec(1, 2, width_ratios=[1.85, 1.0], wspace=0.16, left=0.078,
                          right=0.993, top=0.86, bottom=0.30)
    ax1, ax2 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    _style(fig, (ax1, ax2))
    for ax in (ax1, ax2):
        ax.tick_params(labelsize=PT_TICK, length=3.2, width=0.9)

    rows = _notes_rows(mech)
    if rows:
        ax1.set_ylim(0, max(10.0, _panel_notes(ax1, rows)))
        ax1.set_xticklabels(
            [GROUP_TICKS.get(r["slug"],
                             SHORT_NAMES.get(r["slug"], _name(r["slug"])).replace("\n", " "))
             for r in rows], color=TEXT_SECONDARY)
    else:
        ax1.text(0.5, 0.5, "mechanism.json not found" + chr(10)
                 + "run `python -m analysis.mechanism` first", transform=ax1.transAxes,
                 ha="center", va="center", fontsize=PT_AXIS, color=TEXT_SECONDARY)
        ax1.set_xticks([])

    colour = _style_for(ABLATION_SLUG)[0]
    if df.empty:
        ax2.text(0.5, 0.5, "no item-runs", ha="center", va="center",
                 transform=ax2.transAxes, fontsize=PT_AXIS, color=TEXT_SECONDARY)
    else:
        _panel_ablation(ax2, df, max(4.0, _ablation_ymax(df) * 1.22), colour=colour)

    # bring everything the two reused panels drew up to report type
    ax2.yaxis.label.set_fontsize(PT_AXIS)
    ax2.yaxis.labelpad = 2.0
    for ax in (ax1, ax2):
        ax.tick_params(labelsize=PT_TICK)
        _bump_type(ax, PT_ANNOT)
    # both x axes are rows of group labels one plot-unit apart; at 8.5pt "notes on" and
    # "notes off" sit a single word-space apart and read as one run of text
    for ax in (ax1, ax2):
        ax.tick_params(axis="x", labelsize=PT_TICK_GROUP)

    # The ablation's "all impossible items: ... -> ... -> ..." line is one centred line
    # under a panel that is now narrower than the line is long, so it ran off the right
    # edge of the canvas. Same characters, same numbers, broken at its own colon.
    footnote = None
    for t in ax2.texts:
        if t.get_text().startswith("all impossible items"):
            footnote = t
    if footnote is not None:
        head, sep, tail = footnote.get_text().partition(":")
        if sep and tail.strip():
            footnote.set_text(f"{head}{sep}\n{tail.strip()}")
        r = _renderer(fig)
        ticks_y0 = ax2.transAxes.inverted().transform(
            (0.0, ax2.xaxis.get_tightbbox(r).y0))[1]
        footnote.set_position((0.5, min(-0.19, ticks_y0 - 0.045)))

    # Panel B is the narrow one, so its title carries the letter and the what, and the
    # tag under it carries the which-model-and-where; a wrapped two-line title reading
    # "Notes ablation at f = / 0.60 (DeepSeek)" breaks the number across lines.
    tag_a = ("CORRELATIONAL — the agent's own notes, not anything the experiment "
             "varied.")
    tag_b = "CAUSAL — the pre-registered ablation, DeepSeek at f = 0.60."
    pad = max(_tag_lines(fig, ax1, tag_a), _tag_lines(fig, ax2, tag_b))
    head1 = _panel_title(fig, ax1, "A.  Where the notes named the answer file",
                         tag=tag_a, pad_lines=pad)
    head2 = _panel_title(fig, ax2, "B.  Notes ablation", tag=tag_b, pad_lines=pad)

    moved = _declutter(fig, ax1) + _declutter(fig, ax2)

    handles = [
        plt.Line2D([], [], marker="s", linestyle="none", markersize=8.5,
                   markerfacecolor=TEXT_SECONDARY, markeredgecolor=TEXT_SECONDARY,
                   alpha=0.9, label="an earlier note named the answer file  (A)"),
        plt.Line2D([], [], marker="s", linestyle="none", markersize=8.5,
                   markerfacecolor="none", markeredgecolor=TEXT_SECONDARY,
                   markeredgewidth=1.4, label="no earlier note named it  (A)"),
    ] + [
        plt.Line2D([], [], color=colour, marker=mk, markersize=7.5, linestyle="none",
                   markerfacecolor="none", markeredgewidth=1.9, label=f"{lbl}  (B)")
        for _kind, mk, _dx, lbl in IMPOSSIBLE_KINDS
    ]
    leg = _legend(fig, handles, ncol=2, handlelength=1.6, columnspacing=1.8)

    _fit_vertical(fig, gs, leg,
                  above_in=max(_above_in(fig, ax1, head1), _above_in(fig, ax2, head2)),
                  below_in=max(_below_in(fig, ax1), _below_in(fig, ax2, (footnote,))),
                  min_plot_in=2.0, height_in=height_in)
    if moved:
        print(f"  nudged apart to clear a neighbour: {', '.join(moved)}", file=sys.stderr)
    return _save(fig, out_dir, stem)


def make_pdf_figures(df: pd.DataFrame, out_dir: str | Path, n_boot: int = 2000,
                     seed: int = 0, mech: dict | None = None) -> list[Path]:
    """Both report-PDF figures; returns every path written."""
    paths = make_dose_figure(df, out_dir, n_boot=n_boot, seed=seed)
    paths += make_mechanism_combo_figure(df, out_dir, mech=mech)
    return paths


def main(argv: list[str] | None = None) -> int:
    from analysis.load import load_runs

    ap = argparse.ArgumentParser(prog="analysis.figure_pdf", description=__doc__)
    ap.add_argument("--runs", default="results/runs")
    ap.add_argument("--out", default="results/analysis/report")
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = load_runs(Path(args.runs))
    for p in make_pdf_figures(df, args.out, n_boot=args.n_boot, seed=args.seed):
        print(f"  wrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
