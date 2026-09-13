"""The item-run record (SPEC.md section 3) and the JSONL files that hold it.

Builder B fills every key except ``detectors``, ``declared_impossible_heuristic``,
``outcome`` and ``monitor``, which Builder C writes later by rewriting the whole file
atomically. Every stage is idempotent.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1

#: Every key of the record, in SPEC.md section 3 order. Tests assert on this exact set.
RECORD_KEYS: tuple[str, ...] = (
    "schema_version",
    "run_id",
    "batch_id",
    "model",
    "provider",
    "model_config",
    "arm",
    "I",
    "batch_size",
    "f_realised",
    "seed",
    "position",
    "n_items_before",
    "n_impossible_before",
    "task_id",
    "item_key",
    "is_impossible",
    "mutation",
    "spec_text",
    "started_at",
    "ended_at",
    "duration_s",
    "n_turns",
    "tool_calls",
    "transcript",
    "submitted",
    "submit_summary",
    "final_assistant_text",
    "provider_stop_reason",
    "refusal_details",
    "usage",
    "session_context_tokens_at_start",
    "snapshot_before",
    "snapshot_after",
    "final_files",
    "sandbox_grade",
    "fresh_grade",
    "canaries",
    "expected_values",
    "visible_test_text",
    "detectors",
    "declared_impossible_heuristic",
    "outcome",
    "monitor",
    "error",
)

#: Keys Builder C owns; Builder B always writes them as null.
C_OWNED_KEYS = ("detectors", "declared_impossible_heuristic", "outcome", "monitor")

#: Keys added after the first sweeps started. Records written before they existed are
#: still valid; ``ordered()`` fills them with None so an old file can be rewritten in
#: place by a later stage without a schema error.
OPTIONAL_KEYS = ("session_context_tokens_at_start",)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def blank_record() -> dict:
    """A record with every SPEC key present and a null-ish default."""
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": None,
        "batch_id": None,
        "model": None,
        "provider": None,
        "model_config": {},
        "arm": None,
        "I": None,
        "batch_size": None,
        "f_realised": None,
        "seed": None,
        "position": None,
        "n_items_before": None,
        "n_impossible_before": None,
        "task_id": None,
        "item_key": None,
        "is_impossible": None,
        "mutation": None,
        "spec_text": "",
        "started_at": None,
        "ended_at": None,
        "duration_s": None,
        "n_turns": 0,
        "tool_calls": [],
        "transcript": [],
        "submitted": False,
        "submit_summary": None,
        "final_assistant_text": "",
        "provider_stop_reason": None,
        "refusal_details": None,
        "usage": {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0},
        # continuous arm only: input_tokens of this item's FIRST call, i.e. how much
        # session context the agent was carrying when the item started. None elsewhere.
        "session_context_tokens_at_start": None,
        "snapshot_before": {},
        "snapshot_after": {},
        "final_files": {},
        "sandbox_grade": None,
        "fresh_grade": None,
        "canaries": {},
        "expected_values": [],
        "visible_test_text": "",
        "detectors": None,
        "declared_impossible_heuristic": None,
        "outcome": None,
        "monitor": None,
        "error": None,
    }


def validate_record(rec: dict) -> None:
    """Raise if the record is missing a SPEC key or carries an unknown one.

    Keys in :data:`OPTIONAL_KEYS` may be absent: they were added after records had
    already been written to disk, and every stage must still be able to read those.
    """
    have = set(rec)
    want = set(RECORD_KEYS)
    missing = want - have - set(OPTIONAL_KEYS)
    extra = have - want
    if missing or extra:
        raise ValueError(f"record key mismatch; missing={sorted(missing)} extra={sorted(extra)}")


def ordered(rec: dict) -> dict:
    """Return the record with keys in SPEC order (stable, diff-friendly JSONL)."""
    validate_record(rec)
    return {k: rec.get(k) for k in RECORD_KEYS}


# --------------------------------------------------------------------------- JSONL

def append_jsonl(path: Path, rec: dict) -> None:
    """Append one record. Called as soon as an item completes, so a crash loses at most one."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(ordered(rec), ensure_ascii=False)
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def read_jsonl(path: Path) -> list[dict]:
    path = Path(path)
    if not path.is_file():
        return []
    out: list[dict] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def rewrite_jsonl(path: Path, records: list[dict]) -> None:
    """Atomic whole-file rewrite (how later stages update records in place)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            for rec in records:
                fh.write(json.dumps(ordered(rec), ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def write_json(path: Path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def read_json(path: Path) -> dict | None:
    path = Path(path)
    if not path.is_file():
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)
