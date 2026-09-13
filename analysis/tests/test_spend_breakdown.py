"""Multi-directory spend breakdown: grouping totals and the no-double-count rule.

A tiny synthetic tree: two sources (`runs`, `pilot_v0`), two providers, and cache reads
on both -- `anthropic`, whose `input_tokens` EXCLUDES cache reads, and `openai`, whose
`prompt_tokens` INCLUDES them. The two must be priced differently from the same-looking
record, which is the whole point of the normalisation.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from analysis.spend import (
    collect,
    collect_usage,
    format_markdown,
    format_table,
    group_rows,
    price_cells,
    price_rows,
    split_cached,
)

PRICES = {
    "cache_read_multiplier": 0.1,
    "providers": {
        "anthropic": {"claude-x": {"input": 1.0, "output": 5.0}},
        "openai": {"gpt-x": {"input": 10.0, "output": 20.0}},
    },
}

# one agent record per provider, same raw numbers, so only the convention differs
RAW_IN, RAW_OUT, RAW_CACHED = 1_000_000, 100_000, 400_000


def _rec(provider: str, model: str, arm: str, rules_variant: str, position: int) -> dict:
    return {
        "provider": provider,
        "model": model,
        "arm": arm,
        "position": position,
        "model_config": {"rules_variant": rules_variant},
        "usage": {
            "input_tokens": RAW_IN,
            "output_tokens": RAW_OUT,
            "cache_read_input_tokens": RAW_CACHED,
        },
        "monitor": None,
    }


def _write_batch(root: Path, batch_id: str, slug: str, records: list[dict]) -> None:
    d = root / batch_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "batch.json").write_text(json.dumps({"model_slug": slug, "ended": "now"}),
                                  encoding="utf-8")
    with (d / "items.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")


@pytest.fixture
def tree(tmp_path) -> dict:
    runs = tmp_path / "runs"
    pilot = tmp_path / "pilot_v0"
    _write_batch(runs, "clx_baseline_I0_s0", "clx",
                 [_rec("anthropic", "claude-x", "baseline", "standard", 0)])
    _write_batch(runs, "gptx_baseline_I0_s0", "gptx",
                 [_rec("openai", "gpt-x", "baseline", "standard", 0)])
    # a second experimental line: same model, different arm + rules variant
    _write_batch(runs, "gptx_peer_tip_read_I2_s0", "gptx",
                 [_rec("openai", "gpt-x", "peer_tip_read", "declare", 0)])
    # a `_mixed` dir in the pilot source, with a duplicated position (still billed)
    _write_batch(pilot, "gptx_baseline_I0_s0_mixed", "gptx",
                 [_rec("openai", "gpt-x", "baseline", "standard", 0),
                  _rec("openai", "gpt-x", "baseline", "standard", 0)])
    return {"runs": runs, "pilot": pilot, "dirs": [str(runs), str(pilot)]}


# ------------------------------------------------------------------ the rule

def test_split_cached_subtracts_only_for_the_agent_seat_on_openai_compatible():
    assert split_cached("openai", 1000, 400) == 600             # agent is the default
    assert split_cached("openrouter", 1000, 400, "agent") == 600
    assert split_cached("anthropic", 1000, 400, "agent") == 1000    # already uncached
    assert split_cached("ollama", 1000, 0, "agent") == 1000
    assert split_cached("openai", 100, 400, "agent") == 0           # never negative
    # monitor/runner.py._normalise_openai_usage already subtracted; do not do it twice
    assert split_cached("openai", 1000, 400, "monitor") == 1000
    assert split_cached("openrouter", 890, 2048, "monitor") == 890
    assert split_cached("anthropic", 1000, 400, "monitor") == 1000


def test_no_double_count_for_openai_and_no_subtraction_for_anthropic(tree):
    rows, warns = price_cells(collect(tree["dirs"]), PRICES)
    assert warns == []
    a = next(r for r in rows if r["provider"] == "anthropic")
    o = next(r for r in rows if r["provider"] == "openai" and r["arm"] == "baseline"
             and r["source"] == "runs")

    # anthropic: input_tokens is already uncached, cache read is ADDITIONAL
    assert a["input_tokens"] == RAW_IN == a["raw_input_tokens"]
    assert a["usd"] == pytest.approx(
        RAW_IN / 1e6 * 1.0 + RAW_OUT / 1e6 * 5.0 + RAW_CACHED / 1e6 * 1.0 * 0.1)

    # openai: cached is a SUBSET of prompt_tokens, so it is subtracted before pricing
    assert o["raw_input_tokens"] == RAW_IN
    assert o["input_tokens"] == RAW_IN - RAW_CACHED
    assert o["usd"] == pytest.approx(
        (RAW_IN - RAW_CACHED) / 1e6 * 10.0 + RAW_OUT / 1e6 * 20.0
        + RAW_CACHED / 1e6 * 10.0 * 0.1)

    # the naive formula would have billed the cached tokens twice
    naive = RAW_IN / 1e6 * 10.0 + RAW_OUT / 1e6 * 20.0 + RAW_CACHED / 1e6 * 10.0 * 0.1
    assert naive > o["usd"]
    assert naive - o["usd"] == pytest.approx(RAW_CACHED / 1e6 * 10.0)


def test_monitor_usage_is_priced_as_stored_even_when_cached_exceeds_input(tmp_path):
    """`monitor/runner.py` stores the monitor's input already net of cache reads, so a
    record with cached > input is normal there and must NOT be subtracted again."""
    runs = tmp_path / "runs"
    rec = _rec("anthropic", "claude-x", "baseline", "standard", 0)
    rec["monitor"] = {
        "provider": "openai", "model": "gpt-x", "cached": False,
        # the exact shape seen in results/runs: cached > input, already normalised
        "usage": {"input_tokens": 890, "output_tokens": 81,
                  "cache_read_input_tokens": 2048},
    }
    _write_batch(runs, "clx_baseline_I0_s0", "clx", [rec])

    anomalies: list[str] = []
    rows, warns = price_cells(collect([str(runs)], anomalies), PRICES)
    assert warns == [] and anomalies == []      # a monitor record is not an anomaly

    mon = next(r for r in rows if r["seat"] == "monitor")
    assert mon["input_tokens"] == 890           # priced as stored, not clamped to 0
    assert mon["input_tokens"] >= 0
    assert mon["raw_input_tokens"] == 890
    assert mon["usd"] == pytest.approx(          # usd is rounded to 4 dp
        890 / 1e6 * 10.0 + 81 / 1e6 * 20.0 + 2048 / 1e6 * 10.0 * 0.1, abs=5e-5)
    # subtracting again would have zeroed the input and undercharged
    assert mon["usd"] > 81 / 1e6 * 20.0 + 2048 / 1e6 * 10.0 * 0.1


def test_agent_record_with_cached_above_input_clamps_and_warns_once(tmp_path):
    runs = tmp_path / "runs"
    a = _rec("openai", "gpt-x", "baseline", "standard", 0)
    a["usage"] = {"input_tokens": 100, "output_tokens": 10,
                  "cache_read_input_tokens": 400}
    b = _rec("openai", "gpt-x", "baseline", "standard", 1)
    b["usage"] = {"input_tokens": 50, "output_tokens": 10,
                  "cache_read_input_tokens": 900}
    _write_batch(runs, "gptx_baseline_I0_s0", "gptx", [a, b])

    anomalies: list[str] = []
    rows, _ = price_cells(collect([str(runs)], anomalies), PRICES)
    assert len(anomalies) == 1                  # one line, not one per record
    assert "2 agent-seat" in anomalies[0]
    row = rows[0]
    assert row["input_tokens"] == 0             # clamped, never negative
    assert row["raw_input_tokens"] == 150
    assert row["usd"] == pytest.approx(20 / 1e6 * 20.0 + 1300 / 1e6 * 10.0 * 0.1)


def test_cache_percentage_uses_the_uncached_denominator(tree):
    rows, _ = price_cells(collect(tree["dirs"]), PRICES)
    by_provider = {r["provider"]: r for r in group_rows(rows, "provider")}
    o = by_provider["openai"]
    expect = 100.0 * o["cache_read_tokens"] / (o["input_tokens"] + o["cache_read_tokens"])
    assert o["cache_pct"] == pytest.approx(expect)
    # four openai records, all with the same raw numbers
    assert o["item_runs"] == 4
    assert o["cache_read_tokens"] == 4 * RAW_CACHED


# ------------------------------------------------------------------ grouping

def test_every_grouping_has_the_same_grand_total(tree):
    rows, _ = price_cells(collect(tree["dirs"]), PRICES)
    totals = {by: round(sum(r["usd"] for r in group_rows(rows, by)), 6)
              for by in ("provider", "model", "line", "source")}
    assert len(set(totals.values())) == 1, totals
    assert totals["provider"] == pytest.approx(round(sum(r["usd"] for r in rows), 6))

    runs_total = {by: sum(r["item_runs"] for r in group_rows(rows, by))
                  for by in ("provider", "model", "line", "source")}
    assert set(runs_total.values()) == {5}     # 1 anthropic + 4 openai records


def test_source_is_the_runs_dir_basename_and_mixed_dirs_count(tree):
    rows, _ = price_cells(collect(tree["dirs"]), PRICES)
    by_source = {r["source"]: r for r in group_rows(rows, "source")
                 if r["provider"] == "openai"}
    assert set(by_source) == {"runs", "pilot_v0"}
    # the `_mixed` dir contributed both of its duplicate-position records
    assert by_source["pilot_v0"]["item_runs"] == 2
    assert by_source["runs"]["item_runs"] == 2


def test_line_grouping_separates_arm_and_rules_variant(tree):
    rows, _ = price_cells(collect(tree["dirs"]), PRICES)
    lines = group_rows(rows, "line")
    keys = {(r["model_slug"], r["arm"], r["rules_variant"], r["source"]) for r in lines}
    assert ("gptx", "baseline", "standard", "runs") in keys
    assert ("gptx", "peer_tip_read", "declare", "runs") in keys
    assert ("gptx", "baseline", "standard", "pilot_v0") in keys
    assert ("clx", "baseline", "standard", "runs") in keys
    assert len(lines) == 4


def test_provider_order_is_anthropic_openai_openrouter_ollama(tree):
    rows, _ = price_cells(collect(tree["dirs"]), PRICES)
    order = [r["provider"] for r in group_rows(rows, "provider")]
    assert order == ["anthropic", "openai"]
    assert [r["provider"] for r in group_rows(rows, "line")][0] == "anthropic"


def test_legacy_single_dir_api_still_works(tree):
    usage = collect_usage(tree["runs"])
    assert set(usage) == {("agent", "anthropic", "claude-x"), ("agent", "openai", "gpt-x")}
    rows, warns = price_rows(usage, PRICES)
    assert warns == []
    o = next(r for r in rows if r["provider"] == "openai")
    assert o["input_tokens"] == 2 * (RAW_IN - RAW_CACHED)     # two openai batches in runs/


# ------------------------------------------------------------------ rendering

def test_table_and_markdown_render(tree):
    rows, _ = price_cells(collect(tree["dirs"]), PRICES)
    for by in ("provider", "model", "line", "source"):
        grouped = group_rows(rows, by)
        text = format_table(grouped, by)
        assert "TOTAL" in text and "cache" in text
        md = format_markdown(grouped, by)
        assert md.startswith(f"### By {by}")
        assert md.count("|") > 10
        assert "**TOTAL**" in md
    # a grouping with several rows for one provider carries a subtotal block
    assert "subtotal openai" in format_table(group_rows(rows, "line"), "line")


def test_cli_writes_markdown_with_a_footer(tree, tmp_path):
    repo = Path(__file__).resolve().parents[2]
    prices_path = tmp_path / "prices.json"
    prices_path.write_text(json.dumps(PRICES), encoding="utf-8")
    md = tmp_path / "spend.md"
    r = subprocess.run(
        [sys.executable, "-m", "analysis.spend", "--by", "all",
         "--runs", *tree["dirs"], "--prices", str(prices_path), "--md", str(md)],
        cwd=repo, capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    text = md.read_text(encoding="utf-8")
    for by in ("provider", "model", "line", "source"):
        assert f"### By {by}" in text
    assert "**Total: $" in text
    assert "git blob" in text and "runs directories" in text and "generated:" in text
    assert "pilot_v0" in text
