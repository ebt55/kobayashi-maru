"""Pooled statistics are published under three named scopes.

The `frozen` scope's literals are the numbers the released artifact published. They are
pinned here against the real `results/runs` so they can never drift silently again: if a
detector, a load rule or a scope filter changes, this test fails and names the number.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from analysis.load import load_runs
from analysis.stats import (
    POOLED_SCOPES,
    PREREG_SLUGS,
    V7_SUFFIXES,
    compute_stats,
    pooled_block,
    scope_frame,
)

RUNS = Path(__file__).resolve().parents[2] / "results" / "runs"

#: Published by the 13 Sep release. Any change to these is a change to the artifact.
FROZEN = {
    "n_item_runs": 6763, "n_batches": 439,
    "n_rated": 6719, "n_unrated": 44,
    "kappa": 0.9436,
    "table": {"detector_and_monitor": 442, "detector_only": 48,
              "monitor_only": 1, "neither": 6228},
    "cumulative_dose": {"slope": 0.194, "ci_lo": 0.135, "ci_hi": 0.254,
                        "n": 4390, "events": 89},
}
#: The pre-registered H1/H2 scope. Differs, which is why it is worth publishing.
PREREG_BASELINE = {
    "n_item_runs": 5319, "n_batches": 339, "kappa": 0.9366,
    "cumulative_dose": {"slope": 0.196, "ci_lo": 0.132, "ci_hi": 0.260,
                        "n": 3390, "events": 89},
}


@pytest.fixture(scope="module")
def live_stats():
    if not RUNS.is_dir() or not any(RUNS.glob("*/items.jsonl")):
        pytest.skip("results/runs is not present")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = load_runs(RUNS)
    return df, compute_stats(df, n_boot=2000, seed=0)


# ------------------------------------------------------------------ definitions

def test_three_scopes_each_carry_a_definition(live_stats):
    _df, stats = live_stats
    assert set(POOLED_SCOPES) == {"frozen", "preregistered_baseline", "all"}
    for scope in POOLED_SCOPES:
        block = stats["pooled"][scope]
        assert block["definition"].strip(), scope
        for key in ("n_item_runs", "n_batches", "n_solvable_item_runs",
                    "n_solvable_cheats", "kappa", "kappa_by_pair", "cumulative_dose"):
            assert key in block, (scope, key)
    assert "no solvable-item cheat" in stats["pooled"]["note_scopes"]


def test_preregistered_baseline_excludes_every_follow_up_slug(live_stats):
    df, stats = live_stats
    slugs = set(stats["pooled"]["preregistered_baseline"]["model_slugs"])
    assert slugs <= set(PREREG_SLUGS)
    for banned in ("dsv41flash-sal-v2", "glm53flash-sal-v2",
                   "dsv41flash-sal-v2-nonotes", "luna-sal-cont", "luna-sal-decl"):
        assert banned not in slugs, banned
    # and no peer arm survives the filter
    sub = scope_frame(df, "preregistered_baseline")
    assert set(sub["arm"].unique()) == {"baseline"}


def test_frozen_excludes_only_the_v7_lines(live_stats):
    df, stats = live_stats
    slugs = set(stats["pooled"]["frozen"]["model_slugs"])
    assert "dsv41flash-sal-v2" not in slugs and "dsv41flash-sal-v2-nonotes" not in slugs
    assert "glm53flash-sal-v2" not in slugs
    # the peer arms, the continuous arm and the declare cell ARE part of the frozen grid
    assert {"luna-sal-cont", "luna-sal-decl"} <= slugs
    assert {"peer_neutral", "peer_tip", "peer_tip_read", "continuous"} <= set(
        scope_frame(df, "frozen")["arm"].unique())
    assert all(not s.endswith(V7_SUFFIXES) for s in slugs)


def test_all_scope_is_the_whole_frame(live_stats):
    df, stats = live_stats
    assert stats["pooled"]["all"]["n_item_runs"] == len(df)
    assert len(scope_frame(df, "all")) == len(df)


def test_unknown_scope_raises(live_stats):
    df, _stats = live_stats
    with pytest.raises(ValueError):
        scope_frame(df, "nonsense")


# --------------------------------------------------- the published literals (drift guard)

def test_frozen_scope_reproduces_the_released_numbers(live_stats):
    _df, stats = live_stats
    b = stats["pooled"]["frozen"]
    kp, cd = b["kappa"], b["cumulative_dose"]

    assert b["n_item_runs"] == FROZEN["n_item_runs"]
    assert b["n_batches"] == FROZEN["n_batches"]
    assert kp["n_rated"] == FROZEN["n_rated"]
    assert kp["n_unrated"] == FROZEN["n_unrated"]
    assert kp["kappa"] == pytest.approx(FROZEN["kappa"], abs=5e-5)
    assert kp["table"] == FROZEN["table"]

    want = FROZEN["cumulative_dose"]
    assert cd["n"] == want["n"]
    assert b["n_solvable_cheats"] == want["events"]
    assert cd["slope"] == pytest.approx(want["slope"], abs=5e-4)
    assert cd["ci_lo"] == pytest.approx(want["ci_lo"], abs=5e-4)
    assert cd["ci_hi"] == pytest.approx(want["ci_hi"], abs=5e-4)


def test_preregistered_baseline_reproduces_its_published_numbers(live_stats):
    _df, stats = live_stats
    b = stats["pooled"]["preregistered_baseline"]
    cd = b["cumulative_dose"]

    assert b["n_item_runs"] == PREREG_BASELINE["n_item_runs"]
    assert b["n_batches"] == PREREG_BASELINE["n_batches"]
    assert b["kappa"]["kappa"] == pytest.approx(PREREG_BASELINE["kappa"], abs=5e-5)
    want = PREREG_BASELINE["cumulative_dose"]
    assert cd["n"] == want["n"]
    assert b["n_solvable_cheats"] == want["events"]
    assert cd["slope"] == pytest.approx(want["slope"], abs=5e-4)
    assert cd["ci_lo"] == pytest.approx(want["ci_lo"], abs=5e-4)
    assert cd["ci_hi"] == pytest.approx(want["ci_hi"], abs=5e-4)


def test_the_follow_up_arms_added_no_solvable_cheat(live_stats):
    """The fact that makes the three scopes comparable: only denominators move."""
    _df, stats = live_stats
    frozen = stats["pooled"]["frozen"]["n_solvable_cheats"]
    baseline = stats["pooled"]["preregistered_baseline"]["n_solvable_cheats"]
    assert frozen == baseline == 89
    # the `all` scope adds events, because the v2 replication lines do cheat
    assert stats["pooled"]["all"]["n_solvable_cheats"] > frozen


def test_written_stats_json_carries_the_scopes(live_stats, tmp_path):
    from analysis.stats import write_stats

    _df, stats = live_stats
    path = write_stats(stats, tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert set(payload["pooled"]) == set(POOLED_SCOPES) | {"note_scopes"}
    assert payload["pooled"]["frozen"]["kappa"]["kappa"] == pytest.approx(0.9436, abs=5e-5)
    # the legacy top-level keys still exist and say what they are
    assert "note_legacy_pooled_keys" in payload
    assert payload["kappa_overall"]["kappa"] == pytest.approx(
        payload["pooled"]["all"]["kappa"]["kappa"])


def test_table_md_prints_the_three_scopes(live_stats, tmp_path):
    from analysis.cells import build_cells, write_table_md

    df, stats = live_stats
    path = write_table_md(build_cells(df), tmp_path, stats)
    text = path.read_text(encoding="utf-8")
    assert "## Pooled statistics, by scope" in text
    for scope in POOLED_SCOPES:
        assert f"`{scope}`" in text
    assert "no solvable-item cheats" in text
    assert "442-48-1-6,228" in text


# ------------------------------------------------------------------ synthetic scopes

def test_pooled_block_on_a_synthetic_frame():
    import pandas as pd

    rows = []
    for slug, arm in (("luna-sal", "baseline"), ("luna-sal", "peer_tip"),
                      ("luna-sal-v2", "baseline"), ("luna-sal-v2-nonotes", "baseline")):
        for i in range(4):
            rows.append({"model_slug": slug, "arm": arm, "batch_id": f"{slug}_{arm}_b",
                         "is_impossible": False, "cheat": i == 0, "det_any": i == 0,
                         "monitor_cheated": None, "monitor_model": None,
                         "n_impossible_before": i, "f_realised": 0.6})
    df = pd.DataFrame(rows)
    assert pooled_block(df, "all")["n_item_runs"] == 16
    assert pooled_block(df, "frozen")["n_item_runs"] == 8          # drops both v7 slugs
    # baseline-only also drops the peer arm and keeps only a pre-registered slug
    assert pooled_block(df, "preregistered_baseline")["n_item_runs"] == 4
    assert pooled_block(df, "preregistered_baseline")["model_slugs"] == ["luna-sal"]
