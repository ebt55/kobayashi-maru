"""The record schema and its JSONL files (SPEC.md section 3)."""

from __future__ import annotations

import json
import os

import pytest

from harness import records

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


# --------------------------------------------------------------- atomic replace

def _flaky_replace(fail_times: int, log: list):
    """os.replace that raises WinError-5-style PermissionError the first N times."""
    real = os.replace

    def fake(src, dst):
        log.append((src, dst))
        if len(log) <= fail_times:
            raise PermissionError(5, "Access is denied", str(dst))
        return real(src, dst)

    return fake


@pytest.mark.parametrize("writer", ["write_json", "rewrite_jsonl"])
def test_replace_retries_then_lands(tmp_path, monkeypatch, writer):
    """A reader holding the file on Windows makes os.replace fail; retry, don't lose data."""
    monkeypatch.setattr(records, "RETRY_REPLACE", True)
    monkeypatch.setattr(records, "REPLACE_BACKOFF_S", 0.001)
    monkeypatch.setattr(records, "REPLACE_BACKOFF_MAX_S", 0.002)
    log: list = []
    monkeypatch.setattr(os, "replace", _flaky_replace(2, log))

    path = tmp_path / "batch.json"
    if writer == "write_json":
        records.write_json(path, {"batch_id": "b", "ended": None})
        assert json.loads(path.read_text(encoding="utf-8"))["batch_id"] == "b"
    else:
        rec = blank_record()
        rec["position"] = 0
        records.rewrite_jsonl(path, [rec])
        assert read_jsonl(path)[0]["position"] == 0

    assert len(log) == 3                     # failed twice, succeeded on the third
    assert not list(tmp_path.glob("*.tmp"))  # no temp file left behind


def test_replace_reraises_after_the_last_attempt(tmp_path, monkeypatch):
    monkeypatch.setattr(records, "RETRY_REPLACE", True)
    monkeypatch.setattr(records, "REPLACE_ATTEMPTS", 3)
    monkeypatch.setattr(records, "REPLACE_BACKOFF_S", 0.001)
    monkeypatch.setattr(records, "REPLACE_BACKOFF_MAX_S", 0.002)
    log: list = []
    monkeypatch.setattr(os, "replace", _flaky_replace(99, log))

    with pytest.raises(PermissionError):
        records.write_json(tmp_path / "batch.json", {"x": 1})
    assert len(log) == 3                     # bounded: it does not spin for ever
    assert not list(tmp_path.glob("*.tmp"))  # the failed write cleaned up after itself


def test_no_retry_off_windows(tmp_path, monkeypatch):
    monkeypatch.setattr(records, "RETRY_REPLACE", False)
    log: list = []
    monkeypatch.setattr(os, "replace", _flaky_replace(99, log))
    with pytest.raises(PermissionError):
        records.write_json(tmp_path / "batch.json", {"x": 1})
    assert len(log) == 1                     # POSIX renames over open files; one try


def test_write_is_still_atomic_never_partial(tmp_path, monkeypatch):
    """The retry must not degrade into a non-atomic write onto the live file."""
    path = tmp_path / "batch.json"
    records.write_json(path, {"generation": 1})
    monkeypatch.setattr(records, "RETRY_REPLACE", True)
    monkeypatch.setattr(records, "REPLACE_ATTEMPTS", 2)
    monkeypatch.setattr(records, "REPLACE_BACKOFF_S", 0.001)
    log: list = []
    monkeypatch.setattr(os, "replace", _flaky_replace(99, log))

    with pytest.raises(PermissionError):
        records.write_json(path, {"generation": 2})
    # the previous version is untouched: a failed replace never half-writes the target
    assert json.loads(path.read_text(encoding="utf-8")) == {"generation": 1}


def test_truncate_sets_flag():
    text, flag = truncate("a" * 100, 8000)
    assert flag is False and text == "a" * 100
    text, flag = truncate("a" * 9000, 8000)
    assert flag is True and len(text) < 9000 and "truncated" in text


def test_truncate_words_caps_at_eighty():
    long = " ".join(str(i) for i in range(200))
    assert len(truncate_words(long).split()) == 80
    assert truncate_words("short one") == "short one"
