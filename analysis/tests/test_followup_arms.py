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
