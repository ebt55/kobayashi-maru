"""Batch construction (SPEC.md section 2)."""

from __future__ import annotations

import pytest

from harness.batch import build_batch, list_variants, load_solvable_set, make_batch_id
from harness.run import parse_seeds


def test_solvable_set_and_variants_exist(tasks_dir):
    solvable = load_solvable_set(tasks_dir)
    assert solvable["measured"]
    assert list_variants(tasks_dir) == ["t02_sum_evens__contradict"]


def test_batch_size_and_realised_f(tasks_dir):
    measured = load_solvable_set(tasks_dir)["measured"]
    b0 = build_batch(tasks_dir, 0, 0, "fake")
    assert b0.batch_size == len(measured)
    assert b0.f_realised == 0.0
    assert all(not it["is_impossible"] for it in b0.items)

    b1 = build_batch(tasks_dir, 1, 0, "fake")
    assert b1.batch_size == len(measured) + 1
    assert b1.f_realised == round(1 / (len(measured) + 1), 4)
    assert sum(it["is_impossible"] for it in b1.items) == 1


def test_batch_id_shape(tasks_dir):
    b = build_batch(tasks_dir, 1, 7, "haiku45", arm="peer_tip")
    assert b.batch_id == make_batch_id("haiku45", "peer_tip", 1, 7) == "haiku45_peer_tip_I1_s7"


def test_order_is_seed_reproducible(tasks_dir):
    a = build_batch(tasks_dir, 1, 3, "fake")
    b = build_batch(tasks_dir, 1, 3, "fake")
    assert a.order == b.order
    # the solvable set is the same set of ids regardless of seed
    c = build_batch(tasks_dir, 1, 4, "fake")
    assert sorted(a.order) == sorted(c.order)


def test_positions_and_cumulative_dose(tasks_dir):
    b = build_batch(tasks_dir, 1, 0, "fake")
    assert [it["position"] for it in b.items] == list(range(b.batch_size))
    seen = 0
    for it in b.items:
        assert it["n_impossible_before"] == seen
        assert it["n_items_before"] == it["position"]
        if it["is_impossible"]:
            seen += 1


def test_impossible_item_carries_mutation_and_source(tasks_dir):
    b = build_batch(tasks_dir, 1, 0, "fake")
    imp = [it for it in b.items if it["is_impossible"]][0]
    assert imp["item_key"] == "t02_sum_evens__contradict"
    assert imp["task_id"] == "t02_sum_evens"
    assert imp["mutation"] == "contradict"


def test_too_many_impossible_raises(tasks_dir):
    with pytest.raises(ValueError):
        build_batch(tasks_dir, 99, 0, "fake")


@pytest.mark.parametrize("text,want", [
    ("0", [0]),
    ("0-3", [0, 1, 2, 3]),
    ("0,3,5", [0, 3, 5]),
    ("0-2,7", [0, 1, 2, 7]),
])
def test_parse_seeds(text, want):
    assert parse_seeds(text) == want
