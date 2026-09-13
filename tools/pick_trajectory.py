#!/usr/bin/env python3
"""Pick one detector-flagged cheat trajectory and write it out as readable markdown.

    uv run python -m tools.pick_trajectory --runs results/runs \
        --out results/analysis/example_cheat_trajectory.md [--run-id BATCH/POS]
    uv run python -m tools.pick_trajectory --runs results/pilot_v0 --list

The default candidate set is: a record on an **impossible** item whose detectors fired
and whose evidence includes a **D2(a) canary hit** -- i.e. the agent read the hidden
answer file, which is the cheat a reader can verify by eye from the transcript alone.

Only batches whose ``batch.json`` carries ``ended`` are considered, so a batch that is
still being written is never read mid-flight. ``--run-id`` takes a specific record and
skips the filter (but still refuses an unfinished batch unless ``--allow-unended``).

Stdlib only; reads the records, writes one markdown file, changes nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

OUTPUT_CLIP = 1500          # per tool output, per the report brief
CANARY_MARK = ">>> "        # prefix on any line carrying a canary string
FIELD_CLIP = 400            # long single-line fields in the header table


# --------------------------------------------------------------------- loading

def iter_batches(runs_dir: Path, allow_unended: bool = False):
    """Yield (batch_dir, batch_meta) for every batch under ``runs_dir``.

    A batch without ``ended`` in its batch.json is still being written; it is skipped
    unless ``allow_unended``.
    """
    runs_dir = Path(runs_dir)
    if not runs_dir.is_dir():
        raise SystemExit(f"no such runs directory: {runs_dir}")
    for batch_json in sorted(runs_dir.glob("*/batch.json")):
        try:
            meta = json.loads(batch_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not meta.get("ended") and not allow_unended:
            continue
        if not (batch_json.parent / "items.jsonl").is_file():
            continue
        yield batch_json.parent, meta


def iter_records(runs_dir: Path, allow_unended: bool = False):
    for batch_dir, meta in iter_batches(runs_dir, allow_unended):
        path = batch_dir / "items.jsonl"
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                yield batch_dir, meta, rec


def evidence_of(rec: dict) -> list[dict]:
    return list((rec.get("detectors") or {}).get("evidence") or [])


def has_d2a(rec: dict) -> bool:
    return any(e.get("detector") == "D2" and e.get("sub") == "a" for e in evidence_of(rec))


def is_candidate(rec: dict) -> bool:
    det = rec.get("detectors") or {}
    return bool(det.get("cheat")) and bool(rec.get("is_impossible")) and has_d2a(rec)


def rank(rec: dict) -> tuple:
    """Deterministic preference: monitor-rated first, then richer evidence, then longer."""
    monitor = rec.get("monitor") or {}
    return (
        0 if (monitor and not monitor.get("error")) else 1,
        -len(evidence_of(rec)),
        -len(rec.get("tool_calls") or []),
        str(rec.get("run_id") or ""),
    )


# --------------------------------------------------------------------- rendering

def clip(text: str, limit: int) -> str:
    text = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [clipped, {len(text) - limit} more chars]"


def mark_canaries(text: str, canaries: list[str]) -> tuple[str, int]:
    """Prefix every line containing a canary string. Returns (text, n_marked_lines)."""
    if not canaries:
        return text, 0
    out, n = [], 0
    for line in text.splitlines():
        if any(c and c in line for c in canaries):
            out.append(CANARY_MARK + line)
            n += 1
        else:
            out.append(line)
    return "\n".join(out), n


def fence(text: str, lang: str = "") -> str:
    """Fence a block, widening the fence if the content itself contains backticks."""
    ticks = "```"
    while ticks in text:
        ticks += "`"
    return f"{ticks}{lang}\n{text}\n{ticks}"


def header_table(rec: dict, meta: dict) -> str:
    mc = rec.get("model_config") or {}
    det = rec.get("detectors") or {}
    fired = [k for k in ("D1", "D2", "D2c", "D3", "D4", "D5") if det.get(k)]
    rows = [
        ("run_id", rec.get("run_id")),
        ("batch", rec.get("batch_id")),
        ("position", f"{rec.get('position')} of {rec.get('batch_size')}"),
        ("task", f"`{rec.get('item_key')}` (source task `{rec.get('task_id')}`)"),
        ("impossible", f"{rec.get('is_impossible')} — mutation `{rec.get('mutation')}`"),
        ("I / realised f", f"{rec.get('I')} / {rec.get('f_realised')}"),
        ("impossible items seen before", rec.get("n_impossible_before")),
        ("arm", rec.get("arm")),
        ("env_variant", mc.get("env_variant")),
        ("provider / model", f"{rec.get('provider')} / `{rec.get('model')}`"),
        ("seed", rec.get("seed")),
        ("turns / duration", f"{rec.get('n_turns')} turns, {rec.get('duration_s')} s"),
        ("stop reason", rec.get("provider_stop_reason")),
        ("detectors fired", ", ".join(fired) or "none"),
        ("outcome (Builder C)", rec.get("outcome")),
        ("batch ended", meta.get("ended")),
        ("harness git hash", meta.get("harness_git_hash")),
    ]
    lines = ["| field | value |", "|---|---|"]
    for k, v in rows:
        text = "" if v is None else str(v)
        lines.append(f"| {k} | {clip(text, FIELD_CLIP)} |")
    return "\n".join(lines)


def render(rec: dict, meta: dict) -> str:
    canaries = [c for c in (rec.get("canaries") or {}).values() if c]
    transcript = rec.get("transcript") or []
    tool_log = rec.get("tool_calls") or []

    out: list[str] = []
    a = out.append

    a(f"# Example cheat trajectory — `{rec.get('run_id')}`")
    a("")
    a("Written by `tools/pick_trajectory.py` from the raw item record. Nothing is edited: "
      "tool outputs are verbatim, clipped at "
      f"{OUTPUT_CLIP} characters. Lines prefixed `{CANARY_MARK.strip()}` contain a canary "
      "string from a `.grader/` file — those lines are the D2(a) evidence.")
    a("")
    a(header_table(rec, meta))
    a("")

    # -- the rules exactly as the agent saw them -------------------------
    system = next((m for m in transcript if m.get("role") == "system"), None)
    if system:
        a("## Rules shown to the agent (system prompt, verbatim)")
        a("")
        a(fence(system.get("content") or "", "text"))
        a("")

    # -- the first user message: manifest + spec -------------------------
    first_user = next((m for m in transcript if m.get("role") == "user"), None)
    if first_user:
        a("## First user message (batch manifest + item spec, verbatim)")
        a("")
        a(fence(first_user.get("content") or "", "text"))
        a("")

    # -- turn by turn ----------------------------------------------------
    a("## Turns")
    a("")
    results_by_id = {m.get("tool_call_id"): m for m in transcript
                     if m.get("role") == "tool" and m.get("tool_call_id")}
    turn_no = 0
    call_index = 0
    nudges = 0
    for msg in transcript:
        role = msg.get("role")
        if role == "user" and msg is not first_user:
            nudges += 1
            a(f"### Harness nudge {nudges}")
            a("")
            a(fence(msg.get("content") or "", "text"))
            a("")
            continue
        if role != "assistant":
            continue
        turn_no += 1
        a(f"### Turn {turn_no} — assistant")
        a("")
        text = (msg.get("content") or "").strip()
        a(fence(text, "text") if text else "_(no assistant text this turn)_")
        a("")
        for call in msg.get("tool_calls") or []:
            logged = tool_log[call_index] if call_index < len(tool_log) else {}
            call_index += 1
            name = call.get("name") or logged.get("tool") or "?"
            args = call.get("args", logged.get("input", {}))
            a(f"**tool call `{name}`**"
              + (f" — {logged['duration_ms']} ms" if logged.get("duration_ms") is not None else ""))
            a("")
            a("input:")
            a(fence(json.dumps(args, indent=2, ensure_ascii=False), "json"))
            result = results_by_id.get(call.get("id"))
            raw = (result or {}).get("content")
            if raw is None:
                raw = logged.get("output", "")
            body, n_marked = mark_canaries(clip(raw, OUTPUT_CLIP), canaries)
            note = f" — **{n_marked} line(s) carry a canary**" if n_marked else ""
            if logged.get("truncated"):
                note += " — _(the agent's own view was truncated at the 8,000-char tool limit)_"
            a(f"output:{note}")
            a(fence(body, "text"))
            a("")

    # -- submission ------------------------------------------------------
    a("## Submission")
    a("")
    a(f"- `submitted`: {rec.get('submitted')}")
    a("- `submit_summary` (the note carried forward to this agent's later items in the batch):")
    a("")
    a(fence((rec.get("submit_summary") or "(none)"), "text"))
    final = (rec.get("final_assistant_text") or "").strip()
    if final:
        a("")
        a("- final assistant text:")
        a("")
        a(fence(clip(final, OUTPUT_CLIP), "text"))
    a("")

    # -- detector evidence -----------------------------------------------
    a("## Detector evidence (programmatic, no LLM)")
    a("")
    ev = evidence_of(rec)
    if ev:
        a("| detector | sub | turn | detail |")
        a("|---|---|---|---|")
        for e in ev:
            detail = str(e.get("detail", "")).replace("|", "\\|").replace("\n", " ")
            a(f"| {e.get('detector')} | {e.get('sub') or ''} | {e.get('turn')} | {clip(detail, 300)} |")
    else:
        a("_(no evidence entries on this record)_")
    a("")
    a("Canary strings for this item (from `task.json`, never shown to the agent):")
    a("")
    for path, canary in (rec.get("canaries") or {}).items():
        a(f"- `{path}` → `{canary}`")
    a("")

    # -- monitor ----------------------------------------------------------
    a("## Monitor verdict (second rater, different lineage)")
    a("")
    monitor = rec.get("monitor")
    if not monitor:
        a("_(this record has not been rated by the monitor)_")
    elif monitor.get("error"):
        a(f"- error: `{monitor.get('error')}` — recorded as data; the prompt was never reworded.")
    else:
        a(f"- rater: `{monitor.get('provider')}` / `{monitor.get('model')}`")
        a(f"- `cheated`: **{monitor.get('cheated')}**")
        a(f"- `type`: `{monitor.get('type')}`")
        a(f"- `declared_impossible`: {monitor.get('declared_impossible')}")
        a("- quoted evidence:")
        a("")
        a(fence(str(monitor.get("evidence") or ""), "text"))
    a("")

    # -- fresh grade -------------------------------------------------------
    a("## Fresh re-grade (pristine container, pristine tests)")
    a("")
    fg = rec.get("fresh_grade") or {}
    sg = rec.get("sandbox_grade") or {}
    a("| grade | result |")
    a("|---|---|")
    a(f"| in-sandbox hidden (the tally the agent saw) | "
      f"{sg.get('hidden_pass')} ({sg.get('passed')}/{sg.get('total')}) |")
    a(f"| fresh visible | {fg.get('visible_pass')} |")
    a(f"| fresh hidden | {fg.get('hidden_pass')} "
      f"({fg.get('hidden_passed')}/{fg.get('hidden_total')}) |")
    a(f"| fresh probes (inputs in no file the agent could see) | {fg.get('probe_pass')} "
      f"({fg.get('probe_passed')}/{fg.get('probe_total')}) |")
    a("")
    a("The in-sandbox grade is what the agent could influence; the fresh grade is the real "
      "score, computed from the submitted `solution.py` against files rebuilt on the host.")
    a("")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------- CLI

def list_candidates(runs_dir: Path, allow_unended: bool) -> int:
    rows = []
    for _batch_dir, _meta, rec in iter_records(runs_dir, allow_unended):
        if not is_candidate(rec):
            continue
        monitor = rec.get("monitor") or {}
        det = rec.get("detectors") or {}
        fired = ",".join(k for k in ("D1", "D2", "D2c", "D3", "D4", "D5") if det.get(k))
        first = next((e for e in evidence_of(rec)
                      if e.get("detector") == "D2" and e.get("sub") == "a"), {})
        rows.append((
            rank(rec),
            rec.get("run_id"),
            rec.get("item_key"),
            rec.get("f_realised"),
            (rec.get("model_config") or {}).get("env_variant"),
            fired,
            monitor.get("cheated") if monitor and not monitor.get("error") else None,
            str(first.get("detail", "")).replace("\n", " ")[:110],
        ))
    if not rows:
        print(f"no candidates under {runs_dir} "
              f"(cheat + impossible + D2(a), in batches with `ended`)")
        return 1
    rows.sort()
    print(f"{len(rows)} candidate(s) under {runs_dir}, best first:\n")
    for _r, run_id, item, f, env, fired, mon, detail in rows:
        print(f"  {run_id:<34} {item:<34} f={f} env={env or '-':<8} "
              f"detectors={fired:<6} monitor_cheated={mon} | {detail}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tools.pick_trajectory", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", default="results/runs",
                    help="directory holding <batch_id>/items.jsonl (default: results/runs)")
    ap.add_argument("--out", default="results/analysis/example_cheat_trajectory.md")
    ap.add_argument("--run-id", default=None,
                    help="take this record (BATCH_ID/POSITION) instead of picking one")
    ap.add_argument("--list", action="store_true",
                    help="print candidate run_ids with their evidence and exit")
    ap.add_argument("--allow-unended", action="store_true",
                    help="also read batches whose batch.json has no `ended` (unsafe while a "
                         "sweep is writing; off by default)")
    args = ap.parse_args(argv)

    runs_dir = Path(args.runs)
    if args.list:
        return list_candidates(runs_dir, args.allow_unended)

    chosen = None
    chosen_meta = None
    for _batch_dir, meta, rec in iter_records(runs_dir, args.allow_unended):
        if args.run_id:
            if rec.get("run_id") == args.run_id:
                chosen, chosen_meta = rec, meta
                break
            continue
        if is_candidate(rec) and (chosen is None or rank(rec) < rank(chosen)):
            chosen, chosen_meta = rec, meta

    if chosen is None:
        if args.run_id:
            print(f"run_id {args.run_id!r} not found in a finished batch under {runs_dir}. "
                  f"Use --list to see candidates, or --allow-unended if the batch is "
                  f"deliberately still open.", file=sys.stderr)
        else:
            print(f"no detector-flagged cheat on an impossible item with a D2(a) canary hit "
                  f"under {runs_dir}.", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render(chosen, chosen_meta or {}), encoding="utf-8", newline="\n")
    print(f"picked {chosen.get('run_id')} ({chosen.get('item_key')}, "
          f"f={chosen.get('f_realised')}, "
          f"env={(chosen.get('model_config') or {}).get('env_variant')})")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
