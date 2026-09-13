"""Where the money went: token usage and cost across every runs directory.

    uv run python -m analysis.spend --by provider \
        --runs results/runs results/pilot_v0 results/pilot_v1 \
               results/failed_credit results/failed_rate \
        [--md results/analysis/spend.md] [--csv ...] [--prices analysis/prices.json]

Every item record under every ``--runs`` directory is counted -- pilots and failed runs
too, because those tokens were still billed. Each record carries a ``source`` = the
basename of the runs dir it came from. ``*_mixed`` batch dirs are counted like any other;
they may repeat a position, which is fine here (the tokens were spent either way).

Two seats are priced: the agent from ``record["usage"]`` and the monitor from
``record["monitor"]["usage"]`` (only on uncached monitor calls -- a cache hit costs
nothing). Prices come from ``analysis/prices.json``; an unknown model is warned about and
priced at zero, so a total carrying a warning is a LOWER bound.

CACHE-READ ACCOUNTING (why `in tok` is not simply what the record says)
----------------------------------------------------------------------
The providers disagree about what "input tokens" means, AND THE TWO SEATS STORE IT
DIFFERENTLY. The rule is per (seat, provider):

* **agent seat**, ``harness/providers/``:
  - ``anthropic_provider.py`` stores the SDK's ``input_tokens``, which is the UNCACHED
    input only; ``cache_read_input_tokens`` is separate and additional. Price as stored.
  - ``openai_compat.py`` (both the ``openai`` and ``openrouter`` presets) stores
    ``prompt_tokens`` RAW, which already INCLUDES
    ``prompt_tokens_details.cached_tokens``. The cached part must be SUBTRACTED here, or
    it is billed twice: at the full input rate inside ``prompt_tokens`` and again at the
    cache-read rate.
  - ``ollama_provider.py`` stores ``prompt_eval_count`` and a constant zero cache read.
* **monitor seat**, ``monitor/runner.py``: ``_normalise_openai_usage`` ALREADY subtracts
  (``input_tokens -= cache_read_input_tokens`` when ``input >= cached``) before the usage
  reaches ``record["monitor"]["usage"]``, and the Anthropic monitor path copies the SDK
  attributes, which are uncached anyway. So monitor input is ALWAYS priced as stored --
  subtracting again here would undercharge the monitor.

Confirmed against the data: of 5,351 agent openai/openrouter records none has
``cached > input`` (consistent with raw ``prompt_tokens``), while 2,246 of 3,669 monitor
records do (impossible unless the stored value is already net of cache).

One wrinkle, worth cents: the runner's subtraction is guarded by ``input >= cached``, so
a monitor call that reports more cached than prompt tokens keeps its raw value. Those are
left exactly as stored rather than guessed at.

    usd = uncached_in * price_in + cached_in * price_in * cache_read_multiplier
          + out * price_out

``cache %`` = cached / (uncached_in + cached), i.e. the share of the prompt served from
cache. Anthropic cache writes (``cache_creation_input_tokens``, billed at 1.25x) are not
priced: no record in this project has a non-zero value for them.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, NamedTuple

__all__ = [
    "load_prices", "collect", "collect_usage", "price_cells", "price_rows",
    "group_rows", "format_table", "format_markdown", "main",
]

PRICES_PATH = Path(__file__).resolve().parent / "prices.json"

#: Providers whose `input_tokens` already contains the cache-read tokens.
INPUT_INCLUDES_CACHE = frozenset({"openai", "openrouter"})

#: Print order; anything else follows, alphabetically.
PROVIDER_ORDER = ("anthropic", "openai", "openrouter", "ollama")

GROUPINGS = ("provider", "model", "line", "source")

_BATCH_RE = re.compile(
    r"^(?P<slug>.+)_(?P<arm>baseline|peer_neutral|peer_tip_read|peer_tip|continuous)"
    r"_I\d+_s\d+(?:_.*)?$"
)


class Key(NamedTuple):
    seat: str
    provider: str
    model: str
    model_slug: str
    arm: str
    rules_variant: str
    source: str


def load_prices(path: str | Path | None = None) -> dict:
    p = Path(path) if path else PRICES_PATH
    if not p.is_file():
        raise SystemExit(f"price table not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _lookup(prices: dict, provider: str, model: str) -> tuple[dict | None, str]:
    """Exact id, then a dated snapshot of the same model, then a provider wildcard.

    The snapshot step lets a harness that logs ``claude-haiku-4-5`` price against
    the table's ``claude-haiku-4-5-20251001`` (and vice versa) instead of
    silently costing $0.
    """
    table = (prices.get("providers") or {}).get(provider or "", {})
    if model in table:
        return table[model], model
    snapshots = sorted(k for k in table if k.startswith(model + "-") or model.startswith(k + "-"))
    if snapshots:
        return table[snapshots[0]], snapshots[0]
    if "*" in table:
        return table["*"], "*"
    return None, model


def _usage_of(d: dict | None) -> tuple[int, int, int]:
    u = (d or {}).get("usage") or {}
    if not isinstance(u, dict):
        return (0, 0, 0)
    return (
        int(u.get("input_tokens") or u.get("prompt_tokens") or 0),
        int(u.get("output_tokens") or u.get("completion_tokens") or 0),
        int(u.get("cache_read_input_tokens") or 0),
    )


def split_cached(provider: str, in_tok: int, cached: int, seat: str = "agent") -> int:
    """Uncached input for this (seat, provider) -- see the module docstring.

    Only the AGENT seat on an OpenAI-compatible provider stores a raw ``prompt_tokens``
    that still contains the cache reads. The monitor seat is normalised upstream in
    ``monitor/runner.py``, so subtracting here would charge it too little.
    """
    if seat == "agent" and provider in INPUT_INCLUDES_CACHE:
        return max(in_tok - cached, 0)
    return in_tok


def _slug_of(batch_dir: Path) -> str:
    meta = batch_dir / "batch.json"
    if meta.is_file():
        try:
            slug = json.loads(meta.read_text(encoding="utf-8")).get("model_slug")
            if slug:
                return str(slug)
        except (OSError, json.JSONDecodeError):
            pass
    m = _BATCH_RE.match(batch_dir.name)
    return m.group("slug") if m else batch_dir.name


def _blank() -> dict:
    return {"runs": 0, "in": 0, "out": 0, "cached": 0}


def collect(runs_dirs: Iterable[str | Path] | str | Path,
            anomalies: list[str] | None = None) -> dict[Key, dict]:
    """Accumulate raw token usage over every record under every runs dir.

    ``anomalies`` collects one line per data problem worth reporting (currently: an
    agent-seat OpenAI-compatible record whose cache reads exceed its ``prompt_tokens``,
    which would mean the stored value is not raw after all).
    """
    if isinstance(runs_dirs, (str, Path)):
        runs_dirs = [runs_dirs]
    acc: dict[Key, dict] = defaultdict(_blank)
    seen_any = False
    odd_agent = 0
    for raw in runs_dirs:
        root = Path(raw)
        if not root.is_dir():
            raise SystemExit(f"runs directory not found: {root}")
        source = root.name
        for items_path in sorted(root.glob("*/items.jsonl")):
            seen_any = True
            slug = _slug_of(items_path.parent)
            with items_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    mc = rec.get("model_config") or {}
                    key = Key(
                        seat="agent",
                        provider=str(rec.get("provider") or "?"),
                        model=str(rec.get("model") or "?"),
                        model_slug=slug,
                        arm=str(rec.get("arm") or "?"),
                        rules_variant=str(mc.get("rules_variant") or "standard"),
                        source=source,
                    )
                    i, o, c = _usage_of(rec)
                    if key.provider in INPUT_INCLUDES_CACHE and c > i:
                        # An agent record here should hold raw prompt_tokens, which
                        # contain the cache reads; more cached than input means the
                        # assumption does not hold for this record. Never subtract below
                        # zero (split_cached clamps); just make it visible.
                        odd_agent += 1
                    cell = acc[key]
                    cell["runs"] += 1
                    cell["in"] += i
                    cell["out"] += o
                    cell["cached"] += c

                    mon = rec.get("monitor")
                    if isinstance(mon, dict) and mon.get("model") and not mon.get("cached"):
                        mi, mo, mc_ = _usage_of(mon)
                        mkey = Key(
                            seat="monitor",
                            provider=str(mon.get("provider") or "?"),
                            model=str(mon.get("model") or "?"),
                            model_slug="-", arm="-", rules_variant="-",
                            source=source,
                        )
                        mcell = acc[mkey]
                        mcell["runs"] += 1
                        mcell["in"] += mi
                        mcell["out"] += mo
                        mcell["cached"] += mc_
    if not seen_any:
        print("WARNING: no items.jsonl found under the given runs directories",
              file=sys.stderr)
    if odd_agent:
        msg = (f"{odd_agent} agent-seat openai/openrouter record(s) report more cache-read "
               f"tokens than input tokens; input was clamped at 0 rather than going "
               f"negative. Check whether that provider still stores raw prompt_tokens.")
        if anomalies is None:
            print(f"WARNING: {msg}", file=sys.stderr)
        else:
            anomalies.append(msg)
    return dict(acc)


def collect_usage(runs_dir: str | Path) -> dict:
    """Legacy view: ``{(seat, provider, model): {...}}`` over one runs dir."""
    out: dict[tuple[str, str, str], dict] = defaultdict(_blank)
    for key, cell in collect(runs_dir).items():
        k = (key.seat, key.provider, key.model)
        for f in ("runs", "in", "out", "cached"):
            out[k][f] += cell[f]
    return dict(out)


def _price_one(provider: str, model: str, cell: dict, prices: dict,
               warnings: list[str], seat: str) -> dict:
    mult = float(prices.get("cache_read_multiplier", 0.1))
    entry, matched = _lookup(prices, provider, model)
    if entry is None:
        warnings.append(
            f"no price for {provider}/{model} ({seat} seat) -- priced at $0; "
            "add it to analysis/prices.json"
        )
        pin = pout = 0.0
    else:
        pin = float(entry.get("input", 0.0))
        pout = float(entry.get("output", 0.0))
    cached = cell["cached"]
    uncached = split_cached(provider, cell["in"], cached, seat)
    usd = uncached / 1e6 * pin + cell["out"] / 1e6 * pout + cached / 1e6 * pin * mult
    return {
        "priced_as": matched,
        "item_runs": cell["runs"],
        "input_tokens": uncached,          # UNCACHED portion, for every provider
        "raw_input_tokens": cell["in"],    # exactly what the record said
        "output_tokens": cell["out"],
        "cache_read_tokens": cached,
        "price_in_per_mtok": pin,
        "price_out_per_mtok": pout,
        "priced": entry is not None,
        "usd": round(usd, 4),
    }


def price_cells(cells: dict[Key, dict], prices: dict) -> tuple[list[dict], list[str]]:
    """Price at the finest granularity, so any later grouping just sums USD."""
    rows: list[dict] = []
    warnings: list[str] = []
    seen_warn: set[tuple[str, str]] = set()
    for key, cell in sorted(cells.items()):
        before = len(warnings)
        priced = _price_one(key.provider, key.model, cell, prices, warnings, key.seat)
        if len(warnings) > before:
            pair = (key.provider, key.model)
            if pair in seen_warn:
                warnings.pop()
            else:
                seen_warn.add(pair)
        rows.append({**key._asdict(), **priced})
    return rows, warnings


def price_rows(usage: dict, prices: dict) -> tuple[list[dict], list[str]]:
    """Legacy view over a ``{(seat, provider, model): ...}`` dict."""
    rows: list[dict] = []
    warnings: list[str] = []
    for (seat, provider, model), cell in sorted(usage.items()):
        priced = _price_one(provider, model, cell, prices, warnings, seat)
        rows.append({"seat": seat, "provider": provider, "model": model, **priced})
    return rows, warnings


# ------------------------------------------------------------------ grouping

GROUP_FIELDS = {
    "provider": ("provider",),
    "model": ("seat", "provider", "model"),
    "line": ("seat", "provider", "model", "model_slug", "arm", "rules_variant", "source"),
    "source": ("provider", "source"),
}

NUMERIC = ("item_runs", "input_tokens", "raw_input_tokens", "output_tokens",
           "cache_read_tokens", "usd")


def _provider_rank(provider: str) -> tuple[int, str]:
    try:
        return (PROVIDER_ORDER.index(provider), "")
    except ValueError:
        return (len(PROVIDER_ORDER), provider)


def group_rows(rows: list[dict], by: str) -> list[dict]:
    fields = GROUP_FIELDS[by]
    acc: dict[tuple, dict] = {}
    for r in rows:
        k = tuple(r.get(f, "-") for f in fields)
        cur = acc.setdefault(k, {**{f: r.get(f, "-") for f in fields},
                                 **{n: 0 for n in NUMERIC}, "priced": True})
        for n in NUMERIC:
            cur[n] += r[n]
        cur["priced"] = cur["priced"] and r["priced"]
    out = list(acc.values())
    for r in out:
        r["usd"] = round(r["usd"], 4)
        total_in = r["input_tokens"] + r["cache_read_tokens"]
        r["cache_pct"] = (100.0 * r["cache_read_tokens"] / total_in) if total_in else 0.0
    out.sort(key=lambda r: (_provider_rank(r.get("provider", "")),
                            tuple(str(r.get(f, "")) for f in fields)))
    return out


def _totals(rows: list[dict]) -> dict:
    t = {n: 0 for n in NUMERIC}
    for r in rows:
        for n in NUMERIC:
            t[n] += r[n]
    total_in = t["input_tokens"] + t["cache_read_tokens"]
    t["cache_pct"] = (100.0 * t["cache_read_tokens"] / total_in) if total_in else 0.0
    t["usd"] = round(t["usd"], 4)
    return t


def _label_fields(by: str) -> tuple[str, ...]:
    return GROUP_FIELDS[by]


# ------------------------------------------------------------------ rendering

def format_table(rows: list[dict], by: str) -> str:
    fields = _label_fields(by)
    widths = {f: max(len(f), *(len(str(r.get(f, "-"))) for r in rows)) if rows else len(f)
              for f in fields}
    widths = {f: min(w, 34) for f, w in widths.items()}

    def line(vals: dict, label: str | None = None) -> str:
        if label is not None:
            head = label.ljust(sum(widths.values()) + len(fields) - 1)
        else:
            head = " ".join(str(vals.get(f, "-"))[:widths[f]].ljust(widths[f]) for f in fields)
        flag = "" if vals.get("priced", True) else " *"
        return (f"{head}{flag} {vals['item_runs']:>7,} {vals['input_tokens']:>13,} "
                f"{vals['output_tokens']:>10,} {vals['cache_read_tokens']:>13,} "
                f"{vals['cache_pct']:>6.1f}% {vals['usd']:>9,.2f}")

    header = (" ".join(f.ljust(widths[f]) for f in fields)
              + f"   {'runs':>7} {'in tok':>13} {'out tok':>10} {'cached in':>13} "
                f"{'cache':>7} {'USD':>9}")
    out = [header, "-" * len(header)]

    by_provider: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_provider[r.get("provider", "?")].append(r)
    for provider in sorted(by_provider, key=_provider_rank):
        block = by_provider[provider]
        for r in block:
            out.append(line(r))
        if len(block) > 1:                      # subtotal only when it adds something
            out.append(line(_totals(block), label=f"  subtotal {provider}"))
            out.append("")
    if out and out[-1] == "":
        out.pop()
    out.append("-" * len(header))
    out.append(line(_totals(rows), label="TOTAL"))
    return "\n".join(out)


def _md_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def format_markdown(rows: list[dict], by: str) -> str:
    fields = _label_fields(by)
    head = list(fields) + ["runs", "in tok", "out tok", "cached in", "cache %", "USD"]
    out = [f"### By {by}", "",
           _md_row(head),
           _md_row(["---"] * len(head))]

    def cells(r: dict, label: str | None = None) -> list[str]:
        if label is not None:
            lead = [f"**{label}**"] + [""] * (len(fields) - 1)
        else:
            lead = [str(r.get(f, "-")) + ("" if r.get("priced", True) else " \\*")
                    for f in fields]
        return lead + [f"{r['item_runs']:,}", f"{r['input_tokens']:,}",
                       f"{r['output_tokens']:,}", f"{r['cache_read_tokens']:,}",
                       f"{r['cache_pct']:.1f}%", f"{r['usd']:,.2f}"]

    by_provider: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_provider[r.get("provider", "?")].append(r)
    for provider in sorted(by_provider, key=_provider_rank):
        block = by_provider[provider]
        for r in block:
            out.append(_md_row(cells(r)))
        if len(block) > 1:
            out.append(_md_row(cells(_totals(block), label=f"subtotal {provider}")))
    out.append(_md_row(cells(_totals(rows), label="TOTAL")))
    return "\n".join(out)


def git_blob_hash(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def footer(rows: list[dict], runs_dirs: list[str], prices_path: Path) -> str:
    t = _totals(rows)
    mtime = datetime.fromtimestamp(prices_path.stat().st_mtime,
                                   tz=timezone.utc).isoformat(timespec="seconds")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:  # show it repo-relative when it lives inside the repo
        shown = prices_path.resolve().relative_to(Path(__file__).resolve().parents[1]).as_posix()
        shown = f"analysis/{shown}" if not shown.startswith("analysis/") else shown
    except ValueError:
        shown = prices_path.as_posix()
    return "\n".join([
        "",
        f"**Total: ${t['usd']:,.2f}** over {t['item_runs']:,} item records.",
        "",
        f"- price table: `{shown}` "
        f"(git blob `{git_blob_hash(prices_path)[:12]}`, mtime {mtime})",
        f"- runs directories: {', '.join('`' + d + '`' for d in runs_dirs)}",
        f"- generated: {now}",
        "- `in tok` is the UNCACHED input. Agent-seat openai/openrouter records store raw "
        "`prompt_tokens`, which include the cache reads, so those are subtracted before "
        "pricing; monitor-seat records are already net of cache (subtracted upstream in "
        "`monitor/runner.py`) and are priced as stored. See the module docstring in "
        "`analysis/spend.py`.",
    ])


# ------------------------------------------------------------------ CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="analysis.spend", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", nargs="+", default=["results/runs"],
                    help="one or more runs directories (default: results/runs)")
    ap.add_argument("--by", default="model", choices=[*GROUPINGS, "all"],
                    help="grouping (default: model, the historical behaviour)")
    ap.add_argument("--prices", default=None, help="path to a price table (default analysis/prices.json)")
    ap.add_argument("--csv", default=None, help="also write the priced cells to this CSV")
    ap.add_argument("--md", default=None, help="write the table(s) as GitHub markdown here")
    ap.add_argument("--json", dest="as_json", action="store_true", help="print JSON instead of a table")
    args = ap.parse_args(argv)

    prices_path = Path(args.prices) if args.prices else PRICES_PATH
    prices = load_prices(prices_path)
    anomalies: list[str] = []
    cells = collect(args.runs, anomalies)
    rows, warns = price_cells(cells, prices)
    warns = anomalies + warns

    for w in warns:
        print(f"WARNING: {w}", file=sys.stderr)

    wanted = list(GROUPINGS) if args.by == "all" else [args.by]
    grouped = {by: group_rows(rows, by) for by in wanted}

    if args.as_json:
        print(json.dumps({"groupings": grouped, "warnings": warns}, indent=2))
    else:
        for by in wanted:
            print(format_table(grouped[by], by))
            print()
        if warns:
            print("* priced at $0 -- the total is a lower bound.")
        print(
            f"Cache-read input billed at {float(prices.get('cache_read_multiplier', 0.1)):.0%} "
            "of the input price; `in tok` is the uncached portion. Agent-seat "
            "openai/openrouter input is net of cache reads here; monitor-seat input already "
            "was. Monitor rows count only uncached calls."
        )

    if args.md:
        out = Path(args.md)
        out.parent.mkdir(parents=True, exist_ok=True)
        parts = ["# Spend breakdown", ""]
        for by in wanted:
            parts.append(format_markdown(grouped[by], by))
            parts.append("")
        if warns:
            parts += ["\\* priced at $0 -- the total is a lower bound.", ""]
            parts += [f"- WARNING: {w}" for w in warns] + [""]
        parts.append(footer(rows, list(args.runs), prices_path))
        out.write_text("\n".join(parts) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {out}")

    if args.csv:
        import csv as _csv

        out = Path(args.csv)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="") as fh:
            w = _csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["seat"])
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
