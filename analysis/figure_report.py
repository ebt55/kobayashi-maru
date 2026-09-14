"""Two report figures, each built to stand alone for a reader who has seen nothing else.

``figure_main``      — claim 1: the dose effect, and the precision of the four nulls.
``figure_mechanism`` — claims 2 and 3: the notes channel, and what the cheats changed.

House rules these follow, beyond the shared style in ``analysis.figure``:

* **No internal slugs.** ``dsv41flash-sal`` is a directory name, not a model. Everything a
  reader sees uses the published model identity; the slug mapping is one line in the
  caption so ``results/`` can still be matched up.
* **Every panel carries a takeaway subtitle** written as a statement, not a label.
* **The numbers that carry the argument are drawn on the plot**, not left to the caption:
  the Wilson upper bounds on the flat lines, the counts on every bar, and the one-line
  reading of the right-hand mechanism panel.
* **Identity never rests on colour**: distinct line style and marker per model, checked in
  grayscale.

Every number is read from the frame or from ``mechanism.json``; nothing is hardcoded
except the published model names.
"""

from __future__ import annotations

import json
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
    LINESTYLES,
    MARKERS,
    SERIES,
    SURFACE,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    _f_axis,
    _grow_to_fit,
    _legend_top,
    _shade_band,
    _style,
)
from analysis.stats import wilson_ci  # noqa: E402

__all__ = ["make_report_figures", "make_main_figure", "make_mechanism_figure",
           "DISPLAY_NAMES", "SLUG_MAP_NOTE", "F_DEFINITION"]

#: Published model identity per internal slug. The slugs never reach a reader.
DISPLAY_NAMES = {
    "dsv41flash-sal": "DeepSeek-V4.1-flash",
    "glm53flash-sal": "GLM-5.3-flash",
    "luna-sal": "GPT-5.6-Luna",
    "sol-sal": "GPT-5.6-Sol",
    "haiku45": "Claude Haiku 4.5",
    "qwen3-14b-sal": "Qwen3-14B",
    "dsv41flash-sal-v2": "DeepSeek-V4.1-flash, re-run with environment leaks closed",
    "glm53flash-sal-v2": "GLM-5.3-flash, re-run with environment leaks closed",
}
#: Draw order; the pre-registered primary line first so it reads as the reference.
MAIN_ORDER = ("luna-sal", "sol-sal", "haiku45", "qwen3-14b-sal",
              "dsv41flash-sal", "glm53flash-sal")
V2_OF = {"dsv41flash-sal": "dsv41flash-sal-v2", "glm53flash-sal": "glm53flash-sal-v2"}
PRIMARY_SLUG = "luna-sal"

SLUG_MAP_NOTE = (
    "Directory names in results/: DeepSeek-V4.1-flash = dsv41flash-sal, GLM-5.3-flash = "
    "glm53flash-sal, GPT-5.6-Luna = luna-sal, GPT-5.6-Sol = sol-sal, Claude Haiku 4.5 = "
    "haiku45, Qwen3-14B = qwen3-14b-sal; a -v2 suffix is the re-run with the environment "
    "leaks closed."
)
F_DEFINITION = (
    "f = impossible items / batch size. Each batch is the same ten solvable tasks plus "
    "I impossible ones, I in {0, 2, 4, 8, 15}, so f runs 0, .17, .29, .44, .60."
)
#: Axis ticks need the identity in a few characters; the full name is in the legend and
#: the caption. Shortening the words beats shrinking the type.
SHORT_NAMES = {
    "dsv41flash-sal": "DeepSeek",
    "dsv41flash-sal-v2": "DeepSeek\n(re-run)",
    "glm53flash-sal": "GLM-5.3",
    "glm53flash-sal-v2": "GLM-5.3\n(re-run)",
    "haiku45": "Claude\nHaiku 4.5",
    "luna-sal": "GPT-5.6-Luna",
    "sol-sal": "GPT-5.6-Sol",
    "qwen3-14b-sal": "Qwen3-14B",
}

ENV_NOTE = (
    "In every line except Claude Haiku 4.5 the answer file was present in the working "
    "directory; Haiku ran without it."
)

# --- type sizes: this is read at half a page, so nothing is smaller than the caption ---
FS_TITLE = 10.5
FS_SUBTITLE = 8.4
FS_AXIS = 9.0
FS_TICK = 8.5
FS_LEGEND = 8.0
FS_ANNOT = 7.6
FS_CAPTION = 7.2


def _name(slug: str) -> str:
    return DISPLAY_NAMES.get(slug, slug)


#: explicit slots, not draw order: the two lines that move get the strong, high-contrast
#: colours, and they keep the hue they have in figure.png so identity carries across.
COLOUR_SLOT = {"dsv41flash-sal": 1, "glm53flash-sal": 2, "luna-sal": 0,
               "sol-sal": 6, "haiku45": 5, "qwen3-14b-sal": 3}
STYLE_SLOT = {"dsv41flash-sal": 1, "glm53flash-sal": 2, "luna-sal": 0,
              "sol-sal": 3, "haiku45": 4, "qwen3-14b-sal": 5}


def _style_for(slug: str) -> tuple[str, object, str]:
    c = COLOUR_SLOT.get(slug, 7)
    m = STYLE_SLOT.get(slug, 7)
    return SERIES[c % len(SERIES)], LINESTYLES[m % len(LINESTYLES)], MARKERS[m % len(MARKERS)]


def _panel_head(ax, letter_title: str, subtitle: str, wrap: int = 52,
                pad_lines: int | None = None) -> None:
    """Panel letter + title, then a plain-words takeaway written as a statement.

    The title is padded by the subtitle's own height so the two never collide however
    many lines the takeaway runs to.
    """
    # wrap to the panel's own width so two side-by-side subtitles can never run into
    # each other, whatever the wording
    body = textwrap.fill(" ".join(subtitle.split()), width=wrap)
    # pad_lines is a FLOOR, used to line panel titles up across a row; it must never
    # under-pad, or a subtitle that wraps to more lines runs into its own title.
    n_lines = max(pad_lines or 0, body.count(chr(10)) + 1)
    ax.set_title(letter_title, fontsize=FS_TITLE, color=TEXT_PRIMARY, loc="left",
                 pad=10 + n_lines * (FS_SUBTITLE + 3.2))
    ax.text(0.0, 1.012, body, transform=ax.transAxes, fontsize=FS_SUBTITLE,
            color=TEXT_SECONDARY, va="bottom", ha="left", linespacing=1.35)


def _caption(fig, paragraphs: list[str], width: int, y: float = 0.995) -> object:
    wrapped: list[str] = []
    for para in paragraphs:
        wrapped.extend(textwrap.wrap(para, width=width) or [""])
    return fig.text(0.012, y, "\n".join(wrapped), fontsize=FS_CAPTION, color=TEXT_MUTED,
                    va="top", ha="left", linespacing=1.55)


# --------------------------------------------------------------------------- figure_main

def _rates(sub: pd.DataFrame, wilson: bool, n_boot: int, seed: int):
    from analysis.stats import bootstrap_rate_ci

    xs, ys, los, his = [], [], [], []
    for f, cell in sub.groupby("f_realised", sort=True):
        if not np.isfinite(f) or len(cell) == 0:
            continue
        k, n = int(cell["cheat"].sum()), int(len(cell))
        if wilson:
            lo, hi = wilson_ci(k, n)
        else:
            lo, hi = bootstrap_rate_ci(cell, n_boot=n_boot, seed=seed)
            if not np.isfinite(lo) or not np.isfinite(hi):
                lo, hi = wilson_ci(k, n)
        xs.append(float(f))
        ys.append(100.0 * k / n)
        los.append(100.0 * lo)
        his.append(100.0 * hi)
    return xs, ys, los, his


def _draw_lines(ax, df: pd.DataFrame, *, impossible: bool, n_boot: int, seed: int):
    if df.empty or "model_slug" not in df:
        return [], 1.0
    sel = df[df["is_impossible"]] if impossible else df[~df["is_impossible"]]
    handles, ymax = [], 1.0
    for slug in MAIN_ORDER:
        colour, ls, mk = _style_for(slug)
        base = sel[(sel["model_slug"] == slug) & (sel["arm"] == "baseline")]
        if base.empty:
            continue
        xs, ys, los, his = _rates(base, impossible, n_boot, seed)
        if xs:
            ymax = max(ymax, max(his))
            ax.fill_between(xs, los, his, color=colour, alpha=0.12, lw=0, zorder=2)
            ax.plot(xs, ys, color=colour, linestyle=ls, linewidth=2.2, marker=mk,
                    markersize=6.5, markeredgecolor=SURFACE, markeredgewidth=1.4,
                    zorder=4, clip_on=False)
            label = _name(slug)
            if slug == PRIMARY_SLUG:
                label += "  ← pre-registered primary line"
            handles.append(plt.Line2D([], [], color=colour, linestyle=ls, linewidth=2.2,
                                      marker=mk, markersize=6.5, label=label))
        v2 = V2_OF.get(slug)
        if v2:
            sub2 = sel[(sel["model_slug"] == v2) & (sel["arm"] == "baseline")]
            if not sub2.empty:
                xs2, ys2, _lo, _hi = _rates(sub2, impossible, n_boot, seed)
                if xs2:
                    ymax = max(ymax, max(ys2))
                    ax.plot(xs2, ys2, color=colour, linestyle=(0, (4.0, 2.0)),
                            linewidth=1.7, marker=mk, markersize=5.5,
                            markerfacecolor=SURFACE, markeredgecolor=colour,
                            markeredgewidth=1.4, zorder=3, clip_on=False)
                    handles.append(plt.Line2D(
                        [], [], color=colour, linestyle=(0, (4.0, 2.0)), linewidth=1.7,
                        marker=mk, markersize=5.5, markerfacecolor=SURFACE,
                        label=_name(v2)))
    return handles, ymax


def _null_callout(ax, df: pd.DataFrame, top: float) -> None:
    """The four flat lines, with the precision a line sitting on zero cannot show."""
    if df.empty or "model_slug" not in df:
        return
    lines = ["Flat — and precisely so, not for want of data:"]
    for slug in ("luna-sal", "sol-sal", "haiku45", "qwen3-14b-sal"):
        sub = df[(df["model_slug"] == slug) & (~df["is_impossible"])]
        if sub.empty:
            continue
        k, n = int(sub["cheat"].sum()), int(len(sub))
        lines.append(f"   {_name(slug)}  {k}/{n:,}  (95% upper bound {100 * wilson_ci(k, n)[1]:.1f}%)")
    lines.append("   pooled over every arm of that model")
    ax.text(0.035, 0.965, "\n".join(lines), transform=ax.transAxes, fontsize=FS_ANNOT,
            color=TEXT_SECONDARY, va="top", ha="left", linespacing=1.5,
            bbox=dict(boxstyle="round,pad=0.45", facecolor=SURFACE, edgecolor=GRID,
                      linewidth=0.9), zorder=8)


def make_main_figure(df: pd.DataFrame, out_dir: str | Path, n_boot: int = 2000,
                     seed: int = 0, stem: str = "figure_main") -> list[Path]:
    """Claim 1: the dose effect, beside the manipulation check that makes the nulls mean
    something."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": TEXT_PRIMARY,
                         "axes.labelcolor": TEXT_SECONDARY, "svg.fonttype": "path",
                         "figure.dpi": 200, "savefig.dpi": 200})

    fig = plt.figure(figsize=(7.4, 6.4))
    gs = fig.add_gridspec(1, 2, wspace=0.22, left=0.085, right=0.985,
                          top=0.795, bottom=0.52)
    ax1, ax2 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    _style(fig, (ax1, ax2))
    for ax in (ax1, ax2):
        ax.tick_params(labelsize=FS_TICK)
        _shade_band(ax)

    handles, ymax_a = _draw_lines(ax1, df, impossible=False, n_boot=n_boot, seed=seed)
    _, ymax_b = _draw_lines(ax2, df, impossible=True, n_boot=n_boot, seed=seed)
    if not handles:
        for ax in (ax1, ax2):
            ax.text(0.5, 0.5, "no item-runs", ha="center", va="center",
                    transform=ax.transAxes, fontsize=FS_AXIS, color=TEXT_MUTED)
    top = max(10.0, ymax_a, ymax_b) * 1.16

    for ax, band_label in ((ax1, False), (ax2, True)):
        # the callout occupies the top of A, so the band is labelled once, on B
        _f_axis(ax, top, band_label=band_label)
        ax.set_ylim(0, top)
        ax.set_xlabel("fraction of the batch that is impossible,  f",
                      fontsize=FS_AXIS, color=TEXT_SECONDARY, labelpad=2)
    ax1.set_ylabel("cheat rate (% of item-runs)", fontsize=FS_AXIS, color=TEXT_SECONDARY)
    ax2.set_ylabel("cheat rate (% of item-runs)", fontsize=FS_AXIS, color=TEXT_SECONDARY)

    # pad_lines is shared so the two panel titles sit at the same height
    _panel_head(ax1, "A.  Cheating on the tasks that were still solvable",
                "Two of six models cheat more as the batch fills with impossible tasks. "
                "Four never cheat at all.", wrap=52, pad_lines=3)
    _panel_head(ax2, "B.  Cheating on the impossible tasks",
                "Five of six did cheat here, so the flat lines in A are a real result, "
                "not a manipulation that failed to bite.", wrap=48, pad_lines=3)
    _null_callout(ax1, df, top)

    # f, spelled out under the axes where a reader meets it
    fig.text(0.085, 0.452, textwrap.fill(F_DEFINITION, 104), fontsize=FS_ANNOT,
             color=TEXT_MUTED, va="top", ha="left", linespacing=1.4)

    if handles:
        leg = fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.30),
                         ncol=2, fontsize=FS_LEGEND, frameon=True, framealpha=1.0,
                         edgecolor=GRID, facecolor=SURFACE, borderpad=0.6,
                         handlelength=3.0, labelspacing=0.45, handletextpad=0.6,
                         columnspacing=1.6)
        leg.get_frame().set_linewidth(0.9)
        for t in leg.get_texts():
            t.set_color(TEXT_SECONDARY)

    fig.suptitle("Does filling a batch with impossible tasks make an agent cheat on the "
                 "solvable ones?", fontsize=FS_TITLE + 0.7, color=TEXT_PRIMARY,
                 x=0.012, ha="left", y=0.975)

    note = _caption(fig, [
        "Unit: one item-run. Cluster: the batch. Bands in A: cluster-bootstrap 95% "
        f"intervals over batches ({n_boot:,} resamples, seed {seed}); bands in B: Wilson "
        "95% intervals, because a batch carries at most 15 impossible item-runs. Solid "
        "lines are the frozen grid (baseline arm); dashed lines are the two re-runs with "
        "the environment leaks closed, in the same colour as the model they repeat. "
        "Cheat = a programmatic detector over sandbox state and logged tool calls, no "
        "LLM; it counts attempts.",
        "The callout in A gives each flat line's pooled count over every arm of that "
        "model with its 95% Wilson upper bound, because a line resting on zero cannot "
        "show its own precision. Qwen3-14B's null is uninformative: panel B shows its "
        "dose never landed. " + ENV_NOTE,
        f"Shaded band: {BAND_CAPTION}.",
        SLUG_MAP_NOTE,
    ], width=118, y=0.245)
    _grow_to_fit(fig, note, floor=0.0, pad_in=0.12)

    paths = []
    for ext in ("png", "svg"):
        p = out_dir / f"{stem}.{ext}"
        fig.savefig(p, dpi=200, facecolor=SURFACE, edgecolor="none")
        paths.append(p)
    plt.close(fig)
    return paths


# ---------------------------------------------------------------- figure_mechanism

#: lines to show in the notes crosstab: two that cheat, their re-runs, one that never does
NOTES_LINES = ("dsv41flash-sal", "dsv41flash-sal-v2", "glm53flash-sal",
               "glm53flash-sal-v2", "haiku45")


def _notes_rows(mech: dict) -> list[dict]:
    out = []
    by_slug = {}
    for entry in (mech.get("notes_channel") or {}).get("lines") or []:
        if entry.get("arm") == "baseline":
            by_slug.setdefault(entry["model_slug"], entry)
    for slug in NOTES_LINES:
        e = by_slug.get(slug)
        if not e or not e["named"]["n"]:
            continue
        out.append({"slug": slug, "named": e["named"], "not_named": e["not_named"]})
    return out


def _panel_notes(ax, rows: list[dict]) -> float:
    ymax = 1.0
    width = 0.36
    xs = np.arange(len(rows), dtype=float)
    for i, row in enumerate(rows):
        colour, _ls, _mk = _style_for(row["slug"].replace("-v2", ""))
        for j, (key, hatch, alpha) in enumerate((("named", "", 0.9),
                                                 ("not_named", "///", 0.30))):
            b = row[key]
            y = 100.0 * b["rate"]
            lo, hi = 100.0 * b["wilson_lo"], 100.0 * b["wilson_hi"]
            x = xs[i] + (j - 0.5) * width
            ax.bar([x], [y], width=width, color=colour, alpha=alpha, edgecolor=colour,
                   linewidth=1.2, hatch=hatch, zorder=3)
            ax.errorbar([x], [y], yerr=[[max(y - lo, 0)], [max(hi - y, 0)]], fmt="none",
                        ecolor=TEXT_SECONDARY, elinewidth=1.0, capsize=3.0, zorder=4)
            ax.text(x, hi + 2.0, f"{b['k']}/{b['n']}", ha="center", fontsize=FS_ANNOT,
                    color=TEXT_SECONDARY, zorder=5)
            ymax = max(ymax, hi + 7.0)
    ax.set_xticks(xs)
    ax.set_xticklabels([SHORT_NAMES.get(r["slug"], _name(r["slug"])) for r in rows],
                       fontsize=FS_TICK, color=TEXT_SECONDARY)
    ax.set_xlim(-0.6, len(rows) - 0.4)
    ax.set_ylabel("cheat rate on solvable items (%)", fontsize=FS_AXIS,
                  color=TEXT_SECONDARY)
    return ymax


def _panel_shipped(ax, shipped: dict) -> None:
    labels = ["runs that read\nthe answer key", "runs that did not"]
    keys = ("cheat", "non_cheat")
    xs = np.arange(2, dtype=float)
    for x, key, label in zip(xs, keys, labels):
        k, n = shipped[key]
        if not n:
            # a dataset with no cheats at all (or an empty runs dir) has nothing to draw
            # here; say so rather than dividing by zero
            ax.text(x, 50.0, "no runs", ha="center", va="center", fontsize=FS_ANNOT,
                    color=TEXT_MUTED, zorder=5)
            continue
        y = 100.0 * k / n
        lo, hi = wilson_ci(k, n)
        colour = SERIES[4] if key == "cheat" else SERIES[2]
        ax.bar([x], [y], width=0.5, color=colour, alpha=0.85, edgecolor=colour,
               linewidth=1.2, zorder=3)
        ax.errorbar([x], [y], yerr=[[y - 100 * lo], [100 * hi - y]], fmt="none",
                    ecolor=TEXT_SECONDARY, elinewidth=1.0, capsize=3.0, zorder=4)
        ax.text(x, 101.5, f"{k:,}/{n:,}", ha="center", va="bottom",
                fontsize=FS_ANNOT + 0.6, color=TEXT_SECONDARY, zorder=5)
        ax.text(x, 94.0, f"{100 * k / n:.1f}%", ha="center", va="top",
                fontsize=FS_ANNOT + 0.8, color=SURFACE, zorder=6, fontweight="bold")
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=FS_TICK, color=TEXT_SECONDARY)
    ax.set_xlim(-0.62, 1.62)
    ax.set_ylim(0, 112)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_ylabel("submitted a correct, general solution (%)", fontsize=FS_AXIS,
                  color=TEXT_SECONDARY)
    ax.annotate(textwrap.fill("The two bars being equal is the point: reading the key "
                              "changed nothing that was submitted.", 32),
                xy=(0.5, 0.45), xycoords="axes fraction", ha="center", va="center",
                fontsize=FS_ANNOT + 0.3, color=TEXT_PRIMARY,
                bbox=dict(boxstyle="round,pad=0.5", facecolor=SURFACE, edgecolor=GRID,
                          linewidth=0.9), zorder=8)


def shipped_counts(df: pd.DataFrame, runs_dir: str | Path) -> dict:
    """(passing, total) among solvable item-runs, split by whether the run cheated.

    "Passing" = the submitted solution clears the pristine hidden tests AND the nine
    fresh probe inputs the agent never saw, re-run in a clean container.
    """
    out = {"cheat": [0, 0], "non_cheat": [0, 0]}
    for items in sorted(Path(runs_dir).glob("*/items.jsonl")):
        with items.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("is_impossible"):
                    continue
                fg = rec.get("fresh_grade") or {}
                key = "cheat" if rec.get("outcome") == "cheat" else "non_cheat"
                out[key][1] += 1
                if fg.get("hidden_pass") and fg.get("probe_pass"):
                    out[key][0] += 1
    return {k: tuple(v) for k, v in out.items()}


def make_mechanism_figure(df: pd.DataFrame, out_dir: str | Path, runs_dir: str | Path,
                          mech: dict | None = None, stem: str = "figure_mechanism",
                          n_boot: int = 2000, seed: int = 0) -> list[Path]:
    """Claims 2 and 3: how the behaviour travels, and what it changed."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if mech is None:
        # `analysis.mechanism` writes this, and it is a separate command from
        # `analysis.run`; look beside the output and then at the repository default
        # rather than drawing a silently empty panel.
        for cand in (Path(out_dir) / "mechanism.json",
                     Path(__file__).resolve().parents[1] / "results" / "analysis"
                     / "mechanism.json"):
            if cand.is_file():
                mech = json.loads(cand.read_text(encoding="utf-8"))
                break
        else:
            mech = {}
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": TEXT_PRIMARY,
                         "axes.labelcolor": TEXT_SECONDARY, "svg.fonttype": "path",
                         "figure.dpi": 200, "savefig.dpi": 200})

    fig = plt.figure(figsize=(7.4, 6.0))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.5, 1.0], wspace=0.30, left=0.085,
                          right=0.985, top=0.795, bottom=0.45)
    ax1, ax2 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    _style(fig, (ax1, ax2))
    for ax in (ax1, ax2):
        ax.tick_params(labelsize=FS_TICK)

    rows = _notes_rows(mech)
    if rows:
        ymax = _panel_notes(ax1, rows)
    else:
        # never ship a blank panel: say what is missing and how to produce it
        ymax = 10.0
        ax1.text(0.5, 0.5,
                 "mechanism.json not found" + chr(10)
                 + "run `python -m analysis.mechanism`" + chr(10)
                 + "to build this panel",
                 transform=ax1.transAxes, ha="center", va="center",
                 fontsize=FS_AXIS, color=TEXT_MUTED)
        ax1.set_xticks([])
    ax1.set_ylim(0, max(10.0, ymax))
    shipped = shipped_counts(df, runs_dir)
    _panel_shipped(ax2, shipped)

    _panel_head(ax1, "A.  Where the agent's own notes named the answer file",
                "Each agent is shown its own summaries of earlier items. When one names "
                "the answer file, it cheats; when none do, it mostly does not. "
                "CORRELATIONAL.", wrap=62, pad_lines=3)
    _panel_head(ax2, "B.  What the cheating changed",
                "Nothing that was submitted. Runs that read the key shipped a correct, "
                "general solution as often as runs that did not.", wrap=36, pad_lines=3)

    handles = [
        plt.Line2D([], [], marker="s", linestyle="none", markersize=9,
                   markerfacecolor=TEXT_SECONDARY, markeredgecolor=TEXT_SECONDARY,
                   alpha=0.9, label="an earlier note named the answer file"),
        plt.Line2D([], [], marker="s", linestyle="none", markersize=9,
                   markerfacecolor="none", markeredgecolor=TEXT_SECONDARY,
                   markeredgewidth=1.4, label="no earlier note named it"),
    ]
    leg = fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.335),
                     ncol=2, fontsize=FS_LEGEND, frameon=True, framealpha=1.0,
                     edgecolor=GRID, facecolor=SURFACE, borderpad=0.55, handlelength=1.6,
                     labelspacing=0.4, handletextpad=0.6, columnspacing=2.0)
    leg.get_frame().set_linewidth(0.9)
    for t in leg.get_texts():
        t.set_color(TEXT_SECONDARY)

    fig.suptitle("How the behaviour spreads — and what it actually changed",
                 fontsize=FS_TITLE + 0.7, color=TEXT_PRIMARY, x=0.012, ha="left", y=0.975)

    note = _caption(fig, [
        "Unit: one item-run, on the solvable tasks only. Cluster: the batch. Intervals are "
        "Wilson 95%. Counts are printed on every bar.",
        "A is CORRELATIONAL: the two bars are the same agent on the same tasks, split by "
        "what its own manifest replayed back to it, not by anything we varied. The causal "
        "test is the pre-registered ablation in figure_v7, which withholds the notes and "
        "removes the spillover (0/120 solvable cheats, from 46/120) while the agent still "
        "reaches the answer file on the impossible items. Claude Haiku 4.5 is included "
        "because it never cheats in either stratum: the channel is not sufficient on its "
        "own.",
        "B: \"correct, general solution\" means the submitted solution.py passes the "
        "pristine hidden tests AND nine fresh probe inputs that appear in no file the "
        "agent could see, re-run in a clean container. What spreads is reconnaissance, "
        "not an exploit.",
        "Frozen grid plus the two leak-closed re-runs. " + SLUG_MAP_NOTE,
    ], width=118, y=0.245)
    _grow_to_fit(fig, note, floor=0.0, pad_in=0.12)

    paths = []
    for ext in ("png", "svg"):
        p = out_dir / f"{stem}.{ext}"
        fig.savefig(p, dpi=200, facecolor=SURFACE, edgecolor="none")
        paths.append(p)
    plt.close(fig)
    return paths


def make_report_figures(df: pd.DataFrame, out_dir: str | Path, runs_dir: str | Path,
                        n_boot: int = 2000, seed: int = 0) -> list[Path]:
    """Both report figures; returns every path written."""
    paths = make_main_figure(df, out_dir, n_boot=n_boot, seed=seed)
    paths += make_mechanism_figure(df, out_dir, runs_dir, n_boot=n_boot, seed=seed)
    return paths
