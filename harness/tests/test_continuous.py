"""Arm B' -- one continuous session per batch (LocalSandbox + FakeProvider, no Docker)."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.agent import ItemContext
from harness.batch import build_batch
from harness.config import RunConfig
from harness.continuous import ContinuousSession, first_message, next_message
from harness.providers.fake_provider import FakeProvider, honest_script
from harness.records import RECORD_KEYS, validate_record


def _cfg(tasks_dir, tmp_path, **kw) -> RunConfig:
    base = dict(provider="fake", model="fake-model", model_slug="fake", arm="continuous",
                I=1, tasks_dir=tasks_dir, out_dir=tmp_path / "runs", dry_run=True,
                item_wall_clock_s=120)
    base.update(kw)
    return RunConfig(**base)


def _ctxs(tasks_dir):
    batch = build_batch(tasks_dir, 1, 0, "fake", arm="continuous")
    out = []
    for item in batch.items:
        out.append(ItemContext(
            batch_id=batch.batch_id, task_dir=Path(item["task_dir"]),
            item_key=item["item_key"], task_id=item["task_id"],
            position=item["position"], batch_size=batch.batch_size, I=batch.I,
            f_realised=batch.f_realised, seed=0, arm="continuous",
            is_impossible=item["is_impossible"], mutation=item["mutation"],
            n_items_before=item["n_items_before"],
            n_impossible_before=item["n_impossible_before"],
        ))
    return batch, out


def _honest_provider(ctxs) -> FakeProvider:
    return FakeProvider({c.item_key: honest_script(c.task_dir) for c in ctxs})


def _run(session, ctxs, sandbox):
    records = []
    for ctx in ctxs:
        ctx.tally = session.tally
        records.append(session.run_item(ctx))
    return records


# ------------------------------------------------------------------ messages

def test_first_and_next_messages(tasks_dir):
    _batch, ctxs = _ctxs(tasks_dir)
    head = first_message(ctxs[0], "SPEC ONE")
    assert "one at a time in this same conversation" in head
    assert "This is item 1 of 3." in head
    assert "SPEC ONE" in head
    assert "Your notes from earlier items" not in head     # the context IS the memory

    nxt = next_message(ctxs[1], "SPEC TWO", tally=1, completed=1)
    assert nxt.startswith("Item 1 submitted. Running tally: 1/1 passed so far.")
    assert "Now item 2 of 3:" in nxt
    assert "SPEC TWO" in nxt


def test_peer_notes_are_not_used_in_this_arm(tasks_dir, tmp_path):
    from harness.sandbox import assemble_agent_workdir
    dest = assemble_agent_workdir(tmp_path / "w", tasks_dir / "t01_reverse_words",
                                  tasks_dir / "_template", "continuous", "standard")
    assert not (dest / "PEER_NOTES.md").exists()


# ------------------------------------------------------------------ the session

def test_three_item_continuous_batch(tasks_dir, tmp_path, local_sandbox,
                                     local_grader_factory):
    batch, ctxs = _ctxs(tasks_dir)
    assert len(ctxs) == 3
    provider = _honest_provider(ctxs)
    session = ContinuousSession(provider, local_sandbox, _cfg(tasks_dir, tmp_path),
                                template_dir=tasks_dir / "_template",
                                runner_path=tasks_dir / "_runner" / "run_cases.py",
                                grader_factory=local_grader_factory)
    records = _run(session, ctxs, local_sandbox)

    # (i) ONE growing conversation: every call sees more messages than the last, and the
    # first message is always the same batch manifest -- the context is never reset.
    lengths = provider.seen_lengths
    assert len(lengths) >= 6
    assert all(b > a for a, b in zip(lengths, lengths[1:])), lengths
    firsts = set(provider.seen_first_contents)
    assert len(firsts) == 1
    assert "This is item 1 of 3." in firsts.pop()
    assert len(session.messages) == lengths[-1] + 2   # + the last assistant and tool msg

    # (ii) three records, right positions, tally advancing on in-sandbox hidden passes
    assert [r["position"] for r in records] == [0, 1, 2]
    assert [r["run_id"] for r in records] == [f"{batch.batch_id}/{i}" for i in range(3)]
    assert all(r["arm"] == "continuous" for r in records)
    assert all(r["submitted"] for r in records)
    running = 0
    for rec in records:
        assert rec["model_config"]["session_mode"] == "continuous"
        if rec["sandbox_grade"]["hidden_pass"]:
            running += 1
    assert session.tally == running
    # the honest script solves both solvable items and cannot solve the impossible one
    solvable = [r for r in records if not r["is_impossible"]]
    impossible = [r for r in records if r["is_impossible"]]
    assert len(solvable) == 2 and len(impossible) == 1
    assert all(r["fresh_grade"]["hidden_pass"] for r in solvable)
    assert not impossible[0]["fresh_grade"]["hidden_pass"]

    # (iii) schema: every SPEC key present, C's keys still null
    for rec in records:
        validate_record(rec)
        assert set(rec) == set(RECORD_KEYS)
        assert rec["detectors"] is None and rec["outcome"] is None
        assert rec["monitor"] is None and rec["declared_impossible_heuristic"] is None


def test_transcript_is_this_items_segment_only(tasks_dir, tmp_path, local_sandbox,
                                               local_grader_factory):
    _batch, ctxs = _ctxs(tasks_dir)
    session = ContinuousSession(_honest_provider(ctxs), local_sandbox,
                                _cfg(tasks_dir, tmp_path),
                                template_dir=tasks_dir / "_template",
                                runner_path=tasks_dir / "_runner" / "run_cases.py",
                                grader_factory=local_grader_factory)
    records = _run(session, ctxs, local_sandbox)

    for rec in records:
        entries = rec["transcript"]
        assert entries[0]["role"] == "system"          # rules, on every segment
        assert entries[1]["role"] == "user"            # this item's opening message
        assert rec["spec_text"][:40] in entries[1]["content"]
    # the three segments are disjoint and, concatenated, are the whole session
    total = sum(len(r["transcript"]) - 1 for r in records)   # minus the repeated system
    assert total == len(session.messages)
    # only the first item carries the batch manifest
    assert "# Batch manifest" in records[0]["transcript"][1]["content"]
    assert "# Batch manifest" not in records[1]["transcript"][1]["content"]
    assert records[1]["transcript"][1]["content"].startswith("Item 1 submitted.")


def test_session_context_tokens_at_start_is_recorded(tasks_dir, tmp_path, local_sandbox,
                                                     local_grader_factory):
    _batch, ctxs = _ctxs(tasks_dir)
    session = ContinuousSession(_honest_provider(ctxs), local_sandbox,
                                _cfg(tasks_dir, tmp_path),
                                template_dir=tasks_dir / "_template",
                                runner_path=tasks_dir / "_runner" / "run_cases.py",
                                grader_factory=local_grader_factory)
    records = _run(session, ctxs, local_sandbox)
    # the fake provider reports a constant per-call usage, so the value is present and
    # numeric here; the live smoke is what shows it growing.
    assert all(isinstance(r["session_context_tokens_at_start"], int) for r in records)
    assert all(r["usage"]["output_tokens"] > 0 for r in records)


def test_batch_turn_cap_ends_remaining_items(tasks_dir, tmp_path, local_sandbox,
                                             local_grader_factory):
    _batch, ctxs = _ctxs(tasks_dir)
    cfg = _cfg(tasks_dir, tmp_path, batch_turn_cap=2)
    session = ContinuousSession(_honest_provider(ctxs), local_sandbox, cfg,
                                template_dir=tasks_dir / "_template",
                                runner_path=tasks_dir / "_runner" / "run_cases.py",
                                grader_factory=local_grader_factory)
    records = _run(session, ctxs, local_sandbox)

    assert len(records) == 3                       # one record per item, always
    assert records[0]["provider_stop_reason"] == "max_turns"
    for rec in records[1:]:
        assert rec["provider_stop_reason"] == "max_turns"
        assert rec["submitted"] is False
        assert rec["n_turns"] == 0
        assert "batch turn cap" in (rec["error"] or "")
        validate_record(rec)


def test_refusal_ends_the_item_and_the_session_continues(tasks_dir, tmp_path,
                                                         local_sandbox,
                                                         local_grader_factory):
    _batch, ctxs = _ctxs(tasks_dir)
    scripts = {c.item_key: honest_script(c.task_dir) for c in ctxs}
    scripts[ctxs[0].item_key] = [{"stop_reason": "refusal", "text": "I won't do this.",
                                  "refusal_details": {"category": "test",
                                                      "explanation": "scripted"}}]
    session = ContinuousSession(FakeProvider(scripts), local_sandbox,
                                _cfg(tasks_dir, tmp_path),
                                template_dir=tasks_dir / "_template",
                                runner_path=tasks_dir / "_runner" / "run_cases.py",
                                grader_factory=local_grader_factory)
    records = _run(session, ctxs, local_sandbox)

    assert records[0]["provider_stop_reason"] == "refusal"
    assert records[0]["submitted"] is False
    assert records[0]["refusal_details"]["category"] == "test"
    # the session went on to the next item rather than stopping the batch
    assert [r["position"] for r in records] == [0, 1, 2]
    assert records[1]["submitted"] is True
    assert records[1]["transcript"][1]["content"].startswith("Item 1 submitted.")


def test_resume_rebuilds_the_conversation(tasks_dir, tmp_path, local_sandbox,
                                          local_grader_factory):
    _batch, ctxs = _ctxs(tasks_dir)
    kwargs = dict(template_dir=tasks_dir / "_template",
                  runner_path=tasks_dir / "_runner" / "run_cases.py",
                  grader_factory=local_grader_factory)
    first = ContinuousSession(_honest_provider(ctxs), local_sandbox,
                              _cfg(tasks_dir, tmp_path), **kwargs)
    done = [first.run_item(ctxs[0]), first.run_item(ctxs[1])]

    resumed = ContinuousSession(_honest_provider(ctxs), local_sandbox,
                                _cfg(tasks_dir, tmp_path), **kwargs)
    resumed.resume_from(done)
    assert len(resumed.messages) == len(first.messages)
    assert [m.role for m in resumed.messages] == [m.role for m in first.messages]
    assert resumed.completed == 2
    assert resumed.tally == first.tally
    assert resumed.turns_used == sum(r["n_turns"] for r in done)
    # the rebuilt session continues the same conversation
    ctxs[2].tally = resumed.tally
    rec = resumed.run_item(ctxs[2])
    assert rec["position"] == 2
    assert rec["transcript"][1]["content"].startswith("Item 2 submitted.")


# ------------------------------------------------------------------ no leakage

def test_baseline_arm_is_untouched(tasks_dir, tmp_path, local_sandbox,
                                   local_grader_factory):
    """The per-item path must not gain a session_mode or a continuous transcript."""
    from harness.agent import run_item

    cfg = RunConfig(provider="fake", model="fake-model", model_slug="fake",
                    tasks_dir=tasks_dir, out_dir=tmp_path / "runs", dry_run=True,
                    item_wall_clock_s=120)
    assert cfg.is_continuous is False
    ctx = ItemContext(batch_id="b", task_dir=tasks_dir / "t01_reverse_words",
                      item_key="t01_reverse_words", task_id="t01_reverse_words",
                      position=0, batch_size=1, I=0, f_realised=0.0, seed=0)
    provider = FakeProvider({"t01_reverse_words": honest_script(ctx.task_dir)})
    rec = run_item(provider, local_sandbox, cfg, ctx,
                   template_dir=tasks_dir / "_template",
                   runner_path=tasks_dir / "_runner" / "run_cases.py",
                   grader_factory=local_grader_factory)

    assert "session_mode" not in rec["model_config"]
    assert rec["session_context_tokens_at_start"] is None
    assert rec["transcript"][1]["content"].startswith("# Batch manifest")
    validate_record(rec)


@pytest.mark.parametrize("arm", ["baseline", "peer_neutral", "peer_tip", "continuous"])
def test_every_arm_is_accepted(arm):
    assert RunConfig(arm=arm).arm == arm
