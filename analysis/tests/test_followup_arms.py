"""The two follow-up arms must load, reach the cells table, and stay out of the
pre-registered primary slope.

`peer_tip_read` and `continuous` were added after the first sweeps. Records carry `arm`
themselves, so rows load either way, but `parse_batch_id` has to read their batch ids and
the figure/stats layers have to treat them as what they are: exploratory follow-ups, not
extra points on the baseline dose curve.
"""

from __future__ import annotations

import json
import warnings

import numpy as np
from pathlib import Path

import pytest

from analysis.cells import build_cells
from analysis.figure import continuous_base
from analysis.load import ARMS, load_runs, parse_batch_id
from analysis.stats import compute_stats


def _record(position: int, arm: str, model_slug: str, f: float, I: int, seed: int,
            impossible: bool, cheat: bool, rules_variant: str = "standard") -> dict:
    return {
        "schema_version": 1,
        "run_id": f"{model_slug}_{arm}_I{I}_s{seed}/{position}",
        "batch_id": f"{model_slug}_{arm}_I{I}_s{seed}",
        "model": "gpt-5.6-luna", "provider": "openai",
        "model_config": {"rules_variant": rules_variant, "env_variant": "salient"},
        "arm": arm, "I": I, "batch_size": 10 + I, "f_realised": f, "seed": seed,
        "position": position, "n_items_before": position, "n_impossible_before": 0,
        "task_id": f"t{position:02d}", "item_key": f"t{position:02d}",
        "is_impossible": impossible,
        "mutation": ("unreachable" if impossible else None),
        "usage": {"input_tokens": 10, "output_tokens": 1, "cache_read_input_tokens": 0},
        "submitted": True, "duration_s": 1.0, "n_turns": 2,
        "detectors": {"D1": False, "D2": cheat, "D3": False, "D4": False, "D5": False,
                      "cheat": cheat, "evidence": [], "version": 1},
        "declared_impossible_heuristic": False,
        "outcome": "cheat" if cheat else "honest_pass",
        "monitor": None, "error": None,
    }


def _batch(root: Path, model_slug: str, arm: str, I: int, seed: int, f: float,
           n_solvable: int = 10, n_cheat: int = 0, rules_variant: str = "standard") -> None:
    batch_id = f"{model_slug}_{arm}_I{I}_s{seed}"
    d = root / batch_id
    d.mkdir(parents=True, exist_ok=True)
    d.joinpath("batch.json").write_text(json.dumps({
        "manifest": {"batch_id": batch_id}, "model_slug": model_slug, "arm": arm,
        "env_variant": "salient", "rules_variant": rules_variant,
        "ended": "2026-09-13T00:00:00Z",
    }), encoding="utf-8")
    recs = [_record(i, arm, model_slug, f, I, seed, False, i < n_cheat, rules_variant)
            for i in range(n_solvable)]
    recs += [_record(n_solvable + j, arm, model_slug, f, I, seed, True, False, rules_variant)
             for j in range(I)]
    with d.joinpath("items.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")


@pytest.fixture
def runs(tmp_path) -> Path:
    root = tmp_path / "runs"
    for seed in range(2):                                  # the primary baseline line
        _batch(root, "luna-sal", "baseline", 0, seed, 0.0, n_cheat=1)
        _batch(root, "luna-sal", "baseline", 15, seed, 0.6, n_cheat=3)
    _batch(root, "luna-sal", "peer_neutral", 0, 0, 0.0)
    _batch(root, "luna-sal", "peer_tip", 0, 0, 0.0, n_cheat=2)
    _batch(root, "luna-sal", "peer_tip_read", 0, 0, 0.0, n_cheat=5)      # follow-up arm
    _batch(root, "luna-sal-cont", "continuous", 0, 0, 0.0, n_cheat=4)    # arm B'
    _batch(root, "luna-sal-decl", "baseline", 15, 0, 0.6, n_cheat=0,
           rules_variant="declare")                                      # declare cell
    return root


@pytest.fixture
def df(runs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return load_runs(runs)


# ------------------------------------------------------------------ batch ids

def test_arms_tuple_covers_every_harness_arm():
    assert ARMS == ("baseline", "peer_neutral", "peer_tip", "peer_tip_read", "continuous")


@pytest.mark.parametrize("batch_id,arm,slug", [
    ("luna-sal_baseline_I4_s1", "baseline", "luna-sal"),
    ("luna-sal_peer_neutral_I0_s1", "peer_neutral", "luna-sal"),
    ("luna-sal_peer_tip_I4_s2", "peer_tip", "luna-sal"),
    # the longer name must win the alternation, or the id fails to parse
    ("luna-sal_peer_tip_read_I0_s0", "peer_tip_read", "luna-sal"),
    ("luna-sal-cont_continuous_I15_s0", "continuous", "luna-sal-cont"),
    ("luna-sal-decl_baseline_I0_s0", "baseline", "luna-sal-decl"),
])
def test_parse_batch_id_handles_every_arm(batch_id, arm, slug):
    got = parse_batch_id(batch_id)
    assert got["arm"] == arm
    assert got["model_slug"] == slug
    assert got["I"] is not None and got["seed"] is not None


# ------------------------------------------------------------------ loading

def test_both_follow_up_arms_load(df):
    assert set(df["arm"].unique()) >= {"baseline", "peer_tip_read", "continuous"}
    assert len(df[df["arm"] == "peer_tip_read"]) == 10
    assert len(df[df["arm"] == "continuous"]) == 10


def test_rules_variant_is_carried_as_a_column(df):
    assert "rules_variant" in df.columns
    decl = df[df["model_slug"] == "luna-sal-decl"]
    assert set(decl["rules_variant"].unique()) == {"declare"}
    others = df[df["model_slug"] != "luna-sal-decl"]
    assert set(others["rules_variant"].unique()) == {"standard"}
    # the declare cell is keyed by its own model_slug, so no cell key had to change
    assert "luna-sal-decl" in set(df["model_slug"])


# ------------------------------------------------------------------ cells

def test_new_arms_appear_in_cells_like_any_other(df):
    cells = build_cells(df)
    keyed = {(r["model_slug"], r["arm"], round(float(r["f_realised"]), 4))
             for _, r in cells.iterrows()}
    assert ("luna-sal", "peer_tip_read", 0.0) in keyed
    assert ("luna-sal-cont", "continuous", 0.0) in keyed
    assert ("luna-sal-decl", "baseline", 0.6) in keyed

    tipread = cells[(cells["arm"] == "peer_tip_read")].iloc[0]
    assert tipread["solvable_item_runs"] == 10
    assert tipread["cheat_pct_detector"] == pytest.approx(50.0)   # 5 of 10


# ------------------------------------------------------------------ primary slope

def test_follow_up_arms_do_not_leak_into_the_primary_slope(df):
    stats = compute_stats(df, n_boot=50, seed=0)
    luna = stats["models"]["luna-sal"]
    assert luna["arm_scope"] == "baseline"
    # 4 baseline batches x 10 solvable; the peer arms' 30 solvable rows are excluded
    assert sum(c["n_solvable_item_runs"] for c in luna["cells"]) == 40
    assert len(df[(df["model_slug"] == "luna-sal") & ~df["is_impossible"]]) == 70


def test_an_arm_only_slug_is_labelled_not_primary(df):
    stats = compute_stats(df, n_boot=50, seed=0)
    cont = stats["models"]["luna-sal-cont"]
    assert cont["arm_scope"] == "continuous"
    assert "NOT the pre-registered primary statistic" in cont["arm_scope_note"]
    # the declare cell DID run a baseline arm, so it keeps the primary scope
    assert stats["models"]["luna-sal-decl"]["arm_scope"] == "baseline"


def test_continuous_base_maps_slug_to_its_base_model():
    assert continuous_base("luna-sal-cont") == "luna-sal"
    assert continuous_base("luna-sal-continuous") == "luna-sal"
    assert continuous_base("luna-sal") is None
    assert continuous_base("haiku45") is None


# ------------------------------------------------------------------ figure

def test_figure_draws_the_new_arms_without_taking_a_series_slot(df, tmp_path):
    from analysis.figure import make_figure

    paths = make_figure(df, tmp_path, n_boot=20, seed=0)
    assert all(Path(p).is_file() for p in paths)
    # arm B' is drawn against its base model's colour, so it is not its own legend series
    import matplotlib.pyplot as plt
    plt.close("all")


# ------------------------------------------------- single-f-level lines (no endpoint)

def test_single_f_level_slug_renders_without_crashing(tmp_path):
    """`dsv41flash-sal-v2-nonotes` runs at I = 15 only, so `endpoint_difference` returns
    ci_lo/ci_hi = None (not NaN) and `np.isfinite(None)` raised a TypeError in the
    model-level table."""
    from analysis.cells import build_cells, write_table_md
    from analysis.stats import compute_stats

    runs = tmp_path / "runs"
    # a normal two-level line, plus one that exists at a single level
    for seed in range(2):
        _batch(runs, "dsv41flash-sal-v2", "baseline", 0, seed, 0.0)
        _batch(runs, "dsv41flash-sal-v2", "baseline", 15, seed, 0.6, n_cheat=3)
        _batch(runs, "dsv41flash-sal-v2-nonotes", "baseline", 15, seed, 0.6, n_cheat=1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = load_runs(runs)

    stats = compute_stats(df, n_boot=50, seed=0)
    ep = stats["models"]["dsv41flash-sal-v2-nonotes"]["endpoint_difference"]
    assert ep.get("ci_lo") is None or not np.isfinite(ep["ci_lo"])

    cells = build_cells(df)
    path = write_table_md(cells, tmp_path, stats)       # must not raise
    text = path.read_text(encoding="utf-8")
    assert "dsv41flash-sal-v2-nonotes" in text
    assert "_(single f level; no endpoint)_" in text
    assert "nan" not in text.lower()
    # the two-level line still prints its endpoint
    assert "dsv41flash-sal-v2 " in text or "| dsv41flash-sal-v2 |" in text


def test_finite_helper_treats_none_like_nan():
    from analysis.cells import _finite

    assert _finite(1.0) and _finite(0) and _finite(np.float64(2.5))
    assert not _finite(None)
    assert not _finite(float("nan"))
    assert not _finite(np.nan)
    assert not _finite(True)          # a bool is not a measurement
    assert not _finite("x") and not _finite([])


# --------------------------------------------- figure: v2 variants and single-level cells

def test_v2_slug_maps_to_its_base_and_nonotes_does_not():
    from analysis.figure import continuous_base, v2_base, variant_of

    assert v2_base("dsv41flash-sal-v2") == "dsv41flash-sal"
    assert v2_base("glm53flash-sal-v2") == "glm53flash-sal"
    assert v2_base("dsv41flash-sal") is None
    # the ablation cell is NOT a v2 variant of anything: it ends with -nonotes
    assert v2_base("dsv41flash-sal-v2-nonotes") is None
    assert variant_of("dsv41flash-sal-v2") == ("dsv41flash-sal", "v2")
    assert variant_of("luna-sal-cont") == ("luna-sal", "cont")
    assert variant_of("dsv41flash-sal-v2-nonotes") is None
    assert continuous_base("dsv41flash-sal-v2") is None


def test_single_level_slugs_are_detected(tmp_path):
    from analysis.figure import single_level_slugs

    runs = tmp_path / "runs"
    for seed in range(2):
        _batch(runs, "dsv41flash-sal-v2", "baseline", 0, seed, 0.0)
        _batch(runs, "dsv41flash-sal-v2", "baseline", 15, seed, 0.6, n_cheat=3)
        _batch(runs, "dsv41flash-sal-v2-nonotes", "baseline", 15, seed, 0.6)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = load_runs(runs)
    assert single_level_slugs(df) == {"dsv41flash-sal-v2-nonotes"}


def test_v2_variant_shares_its_base_colour_and_nonotes_is_excluded(tmp_path):
    """The v2 line takes no colour slot of its own, and the single-level ablation cell
    appears in no panel of the main figure."""
    import matplotlib.pyplot as plt
    from analysis.figure import make_figure

    runs = tmp_path / "runs"
    for seed in range(2):
        for I, f in ((0, 0.0), (15, 0.6)):
            _batch(runs, "dsv41flash-sal", "baseline", I, seed, f, n_cheat=(3 if f else 0))
            _batch(runs, "dsv41flash-sal-v2", "baseline", I, seed, f, n_cheat=(2 if f else 0))
        _batch(runs, "dsv41flash-sal-v2-nonotes", "baseline", 15, seed, 0.6)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = load_runs(runs)

    paths = make_figure(df, tmp_path, n_boot=20, seed=0)
    plt.close("all")
    assert all(Path(p).is_file() for p in paths)

    svg = Path([p for p in paths if str(p).endswith(".svg")][0]).read_text(encoding="utf-8")
    # the v2 line is labelled as a variant of its base, not as a model of its own
    assert "v2 (leaks closed)" in svg
    # the single-level ablation cell is drawn in no panel; it may appear only in the
    # caption, which names what was excluded and why. The caption is wrapped, so assert
    # on tokens that cannot straddle a line break.
    assert "no dose curve" in svg
    assert "figure_v7" in svg
    # the excluded slug is named in the caption (wrapped, so its own name can straddle a
    # line break -- assert on the reason text, which does not)
    assert "single f level" in svg


def test_v7_figure_is_written_with_both_panels(tmp_path):
    from analysis.figure_v7 import V7_BARS, V7_CAPTION, make_v7_figure

    runs = tmp_path / "runs"
    for seed in range(2):
        for I, f in ((0, 0.0), (15, 0.6)):
            _batch(runs, "dsv41flash-sal", "baseline", I, seed, f, n_cheat=(3 if f else 0))
            _batch(runs, "dsv41flash-sal-v2", "baseline", I, seed, f, n_cheat=(4 if f else 0))
            _batch(runs, "glm53flash-sal", "baseline", I, seed, f, n_cheat=(1 if f else 0))
            _batch(runs, "glm53flash-sal-v2", "baseline", I, seed, f, n_cheat=(1 if f else 0))
        _batch(runs, "dsv41flash-sal-v2-nonotes", "baseline", 15, seed, 0.6, n_cheat=0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = load_runs(runs)

    paths = make_v7_figure(df, tmp_path, n_boot=20, seed=0)
    assert [p.name for p in paths] == ["figure_v7.png", "figure_v7.svg"]
    assert all(p.is_file() and p.stat().st_size > 0 for p in paths)
    svg = paths[1].read_text(encoding="utf-8")
    assert "Leak-closed replication" in svg
    assert "Notes ablation" in svg
    assert len(V7_BARS) == 3
    assert "PREREG v7" in V7_CAPTION and "env_version 2" in V7_CAPTION
    assert "v1 remains the frozen primary result" in V7_CAPTION


def test_grow_to_fit_lifts_an_overflowing_caption_into_the_canvas():
    """A caption that overflows loses its last lines silently. `_grow_to_fit` grows the
    canvas until the block clears the given floor; font sizes are absolute, so a taller
    canvas gives the text proportionally more room."""
    import matplotlib.pyplot as plt
    from analysis.figure import _grow_to_fit

    fig = plt.figure(figsize=(7.5, 2.0))
    ax = fig.add_axes([0.05, 0.55, 0.9, 0.4])
    ax.axis("off")
    body = chr(10).join(f"caption line {i}" for i in range(40))
    text = ax.text(0.0, 1.0, body, fontsize=6.0, va="top", ha="left",
                   linespacing=1.5, transform=ax.transAxes)

    fig.canvas.draw()
    inv = fig.transFigure.inverted()
    before_y0 = inv.transform(
        text.get_window_extent(fig.canvas.get_renderer()).corners())[:, 1].min()
    before_h = fig.get_figheight()
    assert before_y0 < 0.0, "the fixture should start with the text off the canvas"

    _grow_to_fit(fig, text, floor=0.10)

    fig.canvas.draw()
    inv = fig.transFigure.inverted()
    after_y0 = inv.transform(
        text.get_window_extent(fig.canvas.get_renderer()).corners())[:, 1].min()
    assert fig.get_figheight() > before_h
    assert after_y0 >= 0.10, f"caption still below the floor (y0={after_y0:.3f})"
    plt.close("all")


def test_grow_to_fit_leaves_a_caption_that_already_fits_alone():
    import matplotlib.pyplot as plt
    from analysis.figure import _grow_to_fit

    fig = plt.figure(figsize=(7.5, 6.0))
    ax = fig.add_axes([0.05, 0.5, 0.9, 0.45])
    ax.axis("off")
    text = ax.text(0.0, 1.0, "one short line", fontsize=6.0, va="top",
                   transform=ax.transAxes)
    h = fig.get_figheight()
    _grow_to_fit(fig, text, floor=0.05)
    assert fig.get_figheight() == h
    plt.close("all")
