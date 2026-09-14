"""The two report figures must stand alone for a reader who has seen nothing else.

These pin the things that make that true: published model names rather than directory
slugs, a takeaway subtitle per panel, f defined on the figure, the pre-registered primary
line marked, and the numbers that carry each claim drawn on the plot.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from analysis.figure_report import (
    DISPLAY_NAMES,
    F_DEFINITION,
    MAIN_ORDER,
    SHORT_NAMES,
    SLUG_MAP_NOTE,
    V2_OF,
    _name,
    _notes_rows,
    _style_for,
    make_main_figure,
    make_mechanism_figure,
    make_report_figures,
    shipped_counts,
)
from analysis.load import load_runs

RUNS = Path(__file__).resolve().parents[2] / "results" / "runs"
SLUGS = tuple(DISPLAY_NAMES)


@pytest.fixture(scope="module")
def live_df():
    if not RUNS.is_dir() or not any(RUNS.glob("*/items.jsonl")):
        pytest.skip("results/runs is not present")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return load_runs(RUNS)


MECH_JSON = RUNS.parent / "analysis" / "mechanism.json"


@pytest.fixture(scope="module")
def rendered(live_df, tmp_path_factory):
    if not MECH_JSON.is_file():
        pytest.skip("mechanism.json is not present; run analysis.mechanism first")
    out = tmp_path_factory.mktemp("report")
    paths = make_main_figure(live_df, out, n_boot=200, seed=0)
    paths += make_mechanism_figure(
        live_df, out, RUNS,
        mech=json.loads(MECH_JSON.read_text(encoding="utf-8")), n_boot=200, seed=0)
    svgs = {p.stem: p.read_text(encoding="utf-8") for p in paths if p.suffix == ".svg"}
    return out, paths, svgs


# ------------------------------------------------------------------ naming

def test_every_plotted_slug_has_a_published_name():
    for slug in MAIN_ORDER:
        assert slug in DISPLAY_NAMES, slug
        assert _name(slug) != slug
        assert "-sal" not in _name(slug) and "45" not in _name(slug).replace("4.5", "")
    for v2 in V2_OF.values():
        assert v2 in DISPLAY_NAMES
        assert "re-run" in DISPLAY_NAMES[v2]
        assert "v2" not in DISPLAY_NAMES[v2]


def test_short_names_cover_the_bar_labels_and_stay_short():
    for slug in ("dsv41flash-sal", "dsv41flash-sal-v2", "glm53flash-sal",
                 "glm53flash-sal-v2", "haiku45"):
        short = SHORT_NAMES[slug]
        assert "-sal" not in short and short
        for line in short.split("\n"):
            assert len(line) <= 12, (slug, line)


def test_the_slug_mapping_is_stated_once_for_traceability():
    for slug in ("dsv41flash-sal", "glm53flash-sal", "luna-sal", "sol-sal",
                 "haiku45", "qwen3-14b-sal"):
        assert slug in SLUG_MAP_NOTE
    assert "-v2" in SLUG_MAP_NOTE


def test_no_directory_slug_reaches_a_legend_or_tick(rendered):
    """Slugs may appear only inside the deliberate mapping sentence in the caption."""
    _out, _paths, svgs = rendered
    for stem, svg in svgs.items():
        for slug in ("dsv41flash-sal", "glm53flash-sal", "qwen3-14b-sal", "luna-sal"):
            # the caption's mapping line is the one licensed occurrence; anything beyond
            # that would be a legend label or an axis tick
            assert svg.count(slug) <= 2, (stem, slug, svg.count(slug))
        assert "DeepSeek" in svg and "GLM-5.3" in svg


# ------------------------------------------------------------------ the figures

def test_both_figures_are_written(rendered):
    _out, paths, _svgs = rendered
    assert sorted(p.name for p in paths) == [
        "figure_main.png", "figure_main.svg",
        "figure_mechanism.png", "figure_mechanism.svg",
    ]
    assert all(p.is_file() and p.stat().st_size > 5000 for p in paths)


def test_main_figure_carries_its_takeaways_and_definitions(rendered):
    _out, _paths, svgs = rendered
    svg = svgs["figure_main"]
    # panel takeaways, written as statements
    assert "Two of six models cheat more" in svg
    assert "Five of six did cheat here" in svg
    # f spelled out for a reader who has never seen it
    assert "impossible items / batch size" in svg
    assert "ten solvable tasks" in svg
    # the pre-registered primary line is marked as such
    assert "pre-registered primary line" in svg
    # the shaded band keeps its provenance
    assert "30" in svg and "METR" in svg


def test_main_figure_draws_the_null_upper_bounds_on_the_plot(rendered, live_df):
    """A line resting on zero cannot show its precision; the callout must."""
    _out, _paths, svgs = rendered
    svg = svgs["figure_main"]
    assert "not for want of data" in svg
    for slug, total in (("luna-sal", "1,240"), ("sol-sal", "600"),
                        ("haiku45", "530"), ("qwen3-14b-sal", "300")):
        sub = live_df[(live_df["model_slug"] == slug) & (~live_df["is_impossible"])]
        assert int(sub["cheat"].sum()) == 0, slug           # still a null
        assert len(sub) == int(total.replace(",", "")), slug
    # the four upper bounds, as rendered
    for bound in ("0.3%", "0.6%", "0.7%", "1.3%"):
        assert bound in svg, bound


def test_mechanism_figure_carries_its_counts_and_the_correlational_warning(rendered):
    _out, _paths, svgs = rendered
    svg = svgs["figure_mechanism"]
    assert "CORRELATIONAL" in svg
    assert "figure_v7" in svg                     # names the causal test
    for count in ("55/126", "11/474", "15/31", "8/569", "0/20", "0/510"):
        assert count in svg, count
    assert "227/228" in svg and "5,481/5,482" in svg
    # the annotation wraps, so assert on fragments that cannot straddle a break
    assert "being equal is the" in svg
    assert "nothing that was submitted." in svg


# ------------------------------------------------------------------ the numbers

def test_notes_rows_match_mechanism_json(live_df):
    mech = json.loads((RUNS.parent / "analysis" / "mechanism.json").read_text(
        encoding="utf-8"))
    rows = {r["slug"]: r for r in _notes_rows(mech)}
    assert set(rows) == {"dsv41flash-sal", "dsv41flash-sal-v2", "glm53flash-sal",
                         "glm53flash-sal-v2", "haiku45"}
    assert (rows["dsv41flash-sal"]["named"]["k"],
            rows["dsv41flash-sal"]["named"]["n"]) == (55, 126)
    assert (rows["dsv41flash-sal"]["not_named"]["k"],
            rows["dsv41flash-sal"]["not_named"]["n"]) == (11, 474)
    assert (rows["glm53flash-sal"]["named"]["k"],
            rows["glm53flash-sal"]["named"]["n"]) == (15, 31)
    # a line that never cheats in either stratum, so the channel is not sufficient alone
    assert rows["haiku45"]["named"]["k"] == 0 and rows["haiku45"]["not_named"]["k"] == 0


def test_shipped_counts_match_the_records(live_df):
    got = shipped_counts(live_df, RUNS)
    assert got["cheat"] == (227, 228)
    assert got["non_cheat"] == (5481, 5482)
    # the whole point of claim 3: the two shares are the same to within a rounding point
    a = 100.0 * got["cheat"][0] / got["cheat"][1]
    b = 100.0 * got["non_cheat"][0] / got["non_cheat"][1]
    assert abs(a - b) < 1.0


def test_shipped_counts_on_a_synthetic_tree(tmp_path):
    runs = tmp_path / "runs"
    d = runs / "x_baseline_I0_s0"
    d.mkdir(parents=True)
    recs = [
        {"is_impossible": False, "outcome": "cheat",
         "fresh_grade": {"hidden_pass": True, "probe_pass": True}},
        {"is_impossible": False, "outcome": "cheat",
         "fresh_grade": {"hidden_pass": True, "probe_pass": False}},
        {"is_impossible": False, "outcome": "honest_pass",
         "fresh_grade": {"hidden_pass": True, "probe_pass": True}},
        {"is_impossible": True, "outcome": "cheat",          # impossible: excluded
         "fresh_grade": {"hidden_pass": True, "probe_pass": True}},
    ]
    with (d / "items.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")
    got = shipped_counts(None, runs)
    assert got["cheat"] == (1, 2)
    assert got["non_cheat"] == (1, 1)


# ------------------------------------------------------------------ grayscale safety

def test_identity_never_rests_on_colour_alone():
    """Each model needs its own line style AND marker, so the figure survives print."""
    styles = {slug: _style_for(slug) for slug in MAIN_ORDER}
    assert len({s[1] if isinstance(s[1], str) else str(s[1]) for s in styles.values()}) \
        == len(MAIN_ORDER)
    assert len({s[2] for s in styles.values()}) == len(MAIN_ORDER)
    assert len({s[0] for s in styles.values()}) == len(MAIN_ORDER)
    # a v2 re-run deliberately shares its base model's colour, and is told apart by dash
    assert _style_for("dsv41flash-sal")[0] == _style_for("dsv41flash-sal")[0]


def test_type_sizes_are_at_least_the_caption_size():
    from analysis.figure_report import (FS_ANNOT, FS_AXIS, FS_CAPTION, FS_LEGEND,
                                        FS_SUBTITLE, FS_TICK, FS_TITLE)
    for size in (FS_AXIS, FS_TICK, FS_LEGEND, FS_SUBTITLE, FS_TITLE):
        assert size >= FS_CAPTION, size
    assert FS_ANNOT >= FS_CAPTION - 0.1
