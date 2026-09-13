"""The record schema and its JSONL files (SPEC.md section 3)."""

from __future__ import annotations

import pytest

from harness.config import truncate, truncate_words
from harness.records import (
    C_OWNED_KEYS,
    RECORD_KEYS,
    append_jsonl,
    blank_record,
    ordered,
    read_jsonl,
    rewrite_jsonl,
    validate_record,
)


def test_blank_record_has_exactly_the_spec_keys():
    rec = blank_record()
    assert set(rec) == set(RECORD_KEYS)
    validate_record(rec)


def test_builder_c_keys_start_null():
    rec = blank_record()
    for key in C_OWNED_KEYS:
        assert rec[key] is None


def test_ordered_preserves_spec_order():
    assert list(ordered(blank_record())) == list(RECORD_KEYS)


def test_validate_rejects_extra_and_missing_keys():
    rec = blank_record()
    rec["surprise"] = 1
    with pytest.raises(ValueError):
        validate_record(rec)
    rec.pop("surprise")
    rec.pop("usage")
    with pytest.raises(ValueError):
        validate_record(rec)


def test_append_and_rewrite_roundtrip(tmp_path):
    path = tmp_path / "items.jsonl"
    for i in range(3):
        rec = blank_record()
        rec["position"] = i
        rec["run_id"] = f"b/{i}"
        append_jsonl(path, rec)

    got = read_jsonl(path)
    assert [r["position"] for r in got] == [0, 1, 2]

    # Builder C's in-place update: fill detectors, rewrite the whole file atomically.
    for r in got:
        r["detectors"] = {"cheat": False, "evidence": []}
    rewrite_jsonl(path, got)
    again = read_jsonl(path)
    assert len(again) == 3
    assert all(r["detectors"] == {"cheat": False, "evidence": []} for r in again)
    assert [r["position"] for r in again] == [0, 1, 2]


def test_truncate_sets_flag():
    text, flag = truncate("a" * 100, 8000)
    assert flag is False and text == "a" * 100
    text, flag = truncate("a" * 9000, 8000)
    assert flag is True and len(text) < 9000 and "truncated" in text


def test_truncate_words_caps_at_eighty():
    long = " ".join(str(i) for i in range(200))
    assert len(truncate_words(long).split()) == 80
    assert truncate_words("short one") == "short one"
