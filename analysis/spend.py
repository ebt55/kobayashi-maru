"""What the sweep cost.

    uv run python -m analysis.spend --runs results/runs [--prices analysis/prices.json]
                                    [--csv results/analysis/spend.csv]

Sums token usage per (provider, model) over every item record -- the agent seat
from ``record["usage"]`` and the monitor seat from ``record["monitor"]["usage"]``
-- and prices it against ``analysis/prices.json``.  Cache-read input tokens are
billed at 10% of the input price.  An unknown model is warned about and priced at
zero, so the printed total is a *lower* bound whenever a warning appears.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

__all__ = ["load_prices", "collect_usage", "price_rows", "format_table", "main"]

PRICES_PATH = Path(__file__).resolve().parent / "prices.json"


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


def collect_usage(runs_dir: str | Path) -> dict:
    """``{(seat, provider, model): {"runs","in","out","cached"}}`` over every record."""
    runs_dir = Path(runs_dir)
    if not runs_dir.is_dir():
        raise SystemExit(f"runs directory not found: {runs_dir}")

    acc: dict[tuple[str, str, str], dict] = defaultdict(
        lambda: {"runs": 0, "in": 0, "out": 0, "cached": 0}
    )
    for items_path in sorted(runs_dir.glob("*/items.jsonl")):
        with items_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)

                i, o, c = _usage_of(rec)
                key = ("agent", str(rec.get("provider") or "?"), str(rec.get("model") or "?"))
                acc[key]["runs"] += 1
                acc[key]["in"] += i
                acc[key]["out"] += o
                acc[key]["cached"] += c

                mon = rec.get("monitor")
                if isinstance(mon, dict) and mon.get("model") and not mon.get("cached"):
                    mi, mo, mc = _usage_of(mon)
                    mkey = (
                        "monitor",
                        str(mon.get("provider") or "?"),
                        str(mon.get("model") or "?"),
                    )
                    acc[mkey]["runs"] += 1
                    acc[mkey]["in"] += mi
                    acc[mkey]["out"] += mo
                    acc[mkey]["cached"] += mc
    return dict(acc)


def price_rows(usage: dict, prices: dict) -> tuple[list[dict], list[str]]:
    mult = float(prices.get("cache_read_multiplier", 0.1))
    rows: list[dict] = []
    warnings: list[str] = []
    for (seat, provider, model), u in sorted(usage.items()):
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
        usd = (
            u["in"] / 1e6 * pin
            + u["out"] / 1e6 * pout
            + u["cached"] / 1e6 * pin * mult
        )
        rows.append(
            {
                "seat": seat,
                "provider": provider,
                "model": model,
                "priced_as": matched,
                "item_runs": u["runs"],
                "input_tokens": u["in"],
                "output_tokens": u["out"],
                "cache_read_tokens": u["cached"],
                "price_in_per_mtok": pin,
                "price_out_per_mtok": pout,
                "priced": entry is not None,
                "usd": round(usd, 4),
            }
        )
    return rows, warnings


def format_table(rows: list[dict]) -> str:
    head = (
        f"{'seat':<8} {'provider':<11} {'model':<32} {'runs':>7} "
        f"{'in tok':>12} {'out tok':>10} {'cached in':>11} {'USD':>9}"
    )
    lines = [head, "-" * len(head)]
    tot = {"item_runs": 0, "input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "usd": 0.0}
    for r in rows:
        flag = "" if r["priced"] else " *"
        lines.append(
            f"{r['seat']:<8} {r['provider']:<11} {(r['model'] + flag)[:32]:<32} "
            f"{r['item_runs']:>7,} {r['input_tokens']:>12,} {r['output_tokens']:>10,} "
            f"{r['cache_read_tokens']:>11,} {r['usd']:>9,.2f}"
        )
        for k in tot:
            tot[k] += r[k]
    lines.append("-" * len(head))
    lines.append(
        f"{'TOTAL':<8} {'':<11} {'':<32} {tot['item_runs']:>7,} "
        f"{tot['input_tokens']:>12,} {tot['output_tokens']:>10,} "
        f"{tot['cache_read_tokens']:>11,} {tot['usd']:>9,.2f}"
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="analysis.spend", description=__doc__)
    ap.add_argument("--runs", default="results/runs")
    ap.add_argument("--prices", default=None, help="path to a price table (default analysis/prices.json)")
    ap.add_argument("--csv", default=None, help="also write the rows to this CSV")
    ap.add_argument("--json", dest="as_json", action="store_true", help="print JSON instead of a table")
    args = ap.parse_args(argv)

    prices = load_prices(args.prices)
    usage = collect_usage(args.runs)
    rows, warns = price_rows(usage, prices)

    for w in warns:
        print(f"WARNING: {w}", file=sys.stderr)

    if args.as_json:
        print(json.dumps({"rows": rows, "warnings": warns}, indent=2))
    else:
        print(format_table(rows))
        if warns:
            print("\n* priced at $0 -- the total is a lower bound.")
        print(
            "\nCache-read input billed at "
            f"{float(prices.get('cache_read_multiplier', 0.1)):.0%} of the input price. "
            "Monitor rows count only uncached calls (a cache hit costs nothing)."
        )

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
