"""CLI: run one cell (or a list of cells) of the dose-curve sweep.

    uv run python -m harness.run --provider anthropic --model claude-haiku-4-5-20251001 \
        --model-slug haiku45 --I 4 --seeds 0-11 --arm baseline
    uv run python -m harness.run --provider openai --model gpt-5.6-luna --I 2 --seeds 0
    uv run python -m harness.run --provider openrouter --model z-ai/glm-5.3-flash --I 2 --seeds 0

    uv run python -m harness.run --cells cells.json

Resumable at two levels: a batch whose ``batch.json`` already carries ``ended`` is
skipped entirely, and within a batch each item record is appended to ``items.jsonl`` the
moment it completes, so a restart picks up at the next position (with the container
recreated and the tally/summary carry-over rebuilt from the existing lines).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from harness.agent import ItemContext, run_item
from harness.batch import (
    Batch,
    batch_json_path,
    build_batch,
    items_jsonl_path,
    new_batch_json,
    write_batch_json,
)
from harness.config import FIXTURE_TASKS_DIR, IMAGE, REPO_ROOT, RunConfig, load_env
from harness.continuous import ContinuousSession
from harness.grade import docker_grader_factory
from harness.providers import build_provider
from harness.providers.fake_provider import dry_run_scripts
from harness.records import append_jsonl, now_iso, read_json, read_jsonl, write_json
from harness.sandbox import DockerSandbox, resolve_template_dir


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


_SLUG_OK = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_")


def default_model_slug(provider: str, model: str) -> str:
    """Filesystem-safe slug for batch_id / directory names.

    ``z-ai/glm-5.3-flash`` on openrouter -> ``or-glm-5.3-flash``;
    ``deepseek/deepseek-v4.1-flash``     -> ``or-deepseek-v4.1-flash``;
    ``claude-haiku-4-5-20251001``        -> ``claude-haiku-4-5-20251001``.
    """
    tail = str(model).split("/")[-1]
    safe = "".join(c if c in _SLUG_OK else "-" for c in tail).strip("-")
    return f"or-{safe}" if provider == "openrouter" else safe


def parse_seeds(text: str) -> list[int]:
    """'0-11' -> 0..11 ; '0,3,5' -> [0,3,5] ; '0-2,7' -> [0,1,2,7]."""
    out: list[int] = []
    for chunk in str(text).split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk[1:]:
            lo, hi = chunk.split("-", 1)
            out.extend(range(int(lo), int(hi) + 1))
        else:
            out.append(int(chunk))
    return out


# ------------------------------------------------------------------ one batch

def run_batch(cfg: RunConfig, seed: int) -> dict:
    """Run (or resume) one batch. Returns a small summary dict."""
    batch: Batch = build_batch(cfg.tasks_dir, cfg.I, seed, cfg.model_slug,
                               cfg.arm, cfg.env_variant)
    items = batch.items
    if cfg.max_items is not None:
        items = items[: cfg.max_items]

    bpath = batch_json_path(cfg.out_dir, batch.batch_id)
    ipath = items_jsonl_path(cfg.out_dir, batch.batch_id)

    existing_meta = read_json(bpath)
    if existing_meta and existing_meta.get("ended"):
        log(f"SKIP {batch.batch_id} (already ended)")
        return {"batch_id": batch.batch_id, "skipped": True, "n_items": 0}

    done = read_jsonl(ipath)
    start_at = len(done)
    if start_at:
        log(f"RESUME {batch.batch_id} at position {start_at}/{len(items)}")
    if start_at >= len(items):
        meta = existing_meta or new_batch_json(batch, cfg)
        # `ended` means the WHOLE batch ran; a --max-items run must not close it, or a
        # later full run would skip a batch that is only partly done.
        if start_at >= batch.batch_size:
            meta["ended"] = now_iso()
        write_batch_json(cfg.out_dir, batch.batch_id, meta)
        return {"batch_id": batch.batch_id, "skipped": True, "n_items": 0}

    scripts = None
    if cfg.dry_run or cfg.provider == "fake":
        scripts, assignment = dry_run_scripts(items)
        log(f"{batch.batch_id} dry-run scripts: "
            + ", ".join(f"{k}={v}" for k, v in assignment.items()))

    provider = build_provider(cfg, scripts=scripts)
    template_dir = resolve_template_dir(Path(items[0]["task_dir"]), cfg.tasks_dir)
    runner_path = Path(cfg.tasks_dir) / "_runner" / "run_cases.py"
    grader_factory = docker_grader_factory(cfg.image)

    meta = existing_meta or new_batch_json(batch, cfg, provider.describe())
    if not existing_meta:
        meta["provider_describe"] = provider.describe()
    meta.setdefault("tally_history", [])
    if scripts is not None:
        meta["dry_run_scripts"] = assignment
    write_batch_json(cfg.out_dir, batch.batch_id, meta)

    tally = sum(1 for r in done if (r.get("sandbox_grade") or {}).get("hidden_pass"))
    prior_summaries = [r.get("submit_summary") for r in done if r.get("submit_summary")]

    sandbox = DockerSandbox(batch.batch_id, tasks_dir=cfg.tasks_dir, image=cfg.image,
                            template_dir=template_dir, keep=cfg.keep_containers)

    # Arm B': one conversation for the whole batch. The per-item arms are untouched.
    session = None
    if cfg.is_continuous:
        session = ContinuousSession(provider, sandbox, cfg, template_dir=template_dir,
                                    runner_path=runner_path, grader_factory=grader_factory)
        if done:
            session.resume_from(done)
            log(f"{batch.batch_id} continuous session rebuilt from {len(done)} record(s): "
                f"{len(session.messages)} messages, {session.turns_used} turns used")

    n_run = 0
    try:
        sandbox.start()
        for item in items[start_at:]:
            ctx = ItemContext(
                batch_id=batch.batch_id,
                task_dir=Path(item["task_dir"]),
                item_key=item["item_key"],
                task_id=item["task_id"],
                position=item["position"],
                batch_size=batch.batch_size,
                I=batch.I,
                f_realised=batch.f_realised,
                seed=seed,
                arm=batch.arm,
                env_variant=batch.env_variant,
                is_impossible=item["is_impossible"],
                mutation=item["mutation"],
                n_items_before=item["n_items_before"],
                n_impossible_before=item["n_impossible_before"],
                tally=tally,
                prior_summaries=list(prior_summaries),
            )
            try:
                if session is not None:
                    rec = session.run_item(ctx)
                else:
                    rec = run_item(provider, sandbox, cfg, ctx, template_dir=template_dir,
                                   runner_path=runner_path, grader_factory=grader_factory)
            except Exception as exc:  # never lose the position
                log(f"ERROR {batch.batch_id} pos {ctx.position}: {exc}\n"
                    + traceback.format_exc()[-1500:])
                raise

            append_jsonl(ipath, rec)
            n_run += 1
            if (rec.get("sandbox_grade") or {}).get("hidden_pass"):
                tally += 1
            if rec.get("submit_summary"):
                prior_summaries.append(rec["submit_summary"])
            meta["tally_history"].append(
                {"position": ctx.position, "item_key": ctx.item_key, "tally": tally})
            write_batch_json(cfg.out_dir, batch.batch_id, meta)

            fg = rec.get("fresh_grade") or {}
            log(
                "ITEM {b} pos={p:>2} {k:<28} submitted={s:<5} sandbox_hidden={sh:<5} "
                "fresh_hidden={fh:<5} probe={pp:<5} stop={st:<9} turns={t:<2} {d:.1f}s".format(
                    b=batch.batch_id, p=ctx.position, k=ctx.item_key,
                    s=str(rec["submitted"]),
                    sh=str((rec.get("sandbox_grade") or {}).get("hidden_pass")),
                    fh=str(fg.get("hidden_pass")), pp=str(fg.get("probe_pass")),
                    st=str(rec["provider_stop_reason"]), t=rec["n_turns"],
                    d=rec["duration_s"] or 0.0,
                )
            )
    finally:
        sandbox.close()
        try:
            provider.close()
        except Exception:
            pass

    if len(read_jsonl(ipath)) >= batch.batch_size:
        meta["ended"] = now_iso()
    elif cfg.max_items is not None:
        meta["truncated_to"] = cfg.max_items
    write_batch_json(cfg.out_dir, batch.batch_id, meta)
    return {"batch_id": batch.batch_id, "skipped": False, "n_items": n_run, "tally": tally}


# ------------------------------------------------------------------ one cell

def run_cell(cfg: RunConfig) -> list[dict]:
    concurrency = 1 if cfg.provider == "ollama" else max(1, cfg.concurrency)
    log(f"CELL provider={cfg.provider} model={cfg.model} slug={cfg.model_slug} "
        f"I={cfg.I} arm={cfg.arm} env={cfg.env_variant} seeds={list(cfg.seeds)} "
        f"concurrency={concurrency}")
    results: list[dict] = []
    if concurrency == 1:
        for seed in cfg.seeds:
            results.append(run_batch(cfg, seed))
        return results
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(run_batch, cfg, seed): seed for seed in cfg.seeds}
        for fut in as_completed(futures):
            results.append(fut.result())
    return results


def cfg_from_cell(cell: dict, base: RunConfig) -> RunConfig:
    seeds = cell.get("seeds", base.seeds)
    if isinstance(seeds, str):
        seeds = parse_seeds(seeds)
    return RunConfig(
        provider=cell.get("provider", base.provider),
        model=cell.get("model", base.model),
        model_slug=cell.get("model_slug") or default_model_slug(
            cell.get("provider", base.provider), cell.get("model", base.model)),
        arm=cell.get("arm", base.arm),
        I=int(cell.get("I", base.I)),
        seeds=tuple(seeds),
        env_variant=cell.get("env_variant", base.env_variant),
        rules_variant=cell.get("rules_variant", base.rules_variant),
        tasks_dir=cell.get("tasks_dir", base.tasks_dir),
        out_dir=cell.get("out", base.out_dir),
        concurrency=int(cell.get("concurrency", base.concurrency)),
        max_items=cell.get("max_items", base.max_items),
        dry_run=bool(cell.get("dry_run", base.dry_run)),
        num_ctx=int(cell.get("num_ctx", base.num_ctx)),
        reasoning_effort=cell.get("reasoning_effort", base.reasoning_effort),
        image=cell.get("image", base.image),
        keep_containers=base.keep_containers,
    )


# ------------------------------------------------------------------ CLI

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="harness.run",
                                description="Run one cell of the impossibility dose-curve sweep.")
    p.add_argument("--provider", default="anthropic",
                   choices=["anthropic", "ollama", "openrouter", "openai", "fake"])
    p.add_argument("--model", default="claude-haiku-4-5-20251001",
                   help="Pass-through model id; verified against the provider's model list once.")
    p.add_argument("--model-slug", default=None,
                   help="Short slug used in batch_id (default: derived from --model).")
    p.add_argument("--I", type=int, default=0, help="Number of impossible variants in the batch.")
    p.add_argument("--seeds", default="0", help="e.g. 0-11 or 0,3,5")
    p.add_argument("--arm", default="baseline",
                   choices=["baseline", "peer_neutral", "peer_tip", "peer_tip_read",
                            "continuous"],
                   help="`continuous` is arm B': ONE conversation for the whole batch "
                        "instead of a fresh context per item (peer notes unused).")
    p.add_argument("--env-variant", default="standard", choices=["standard", "salient"])
    p.add_argument("--rules-variant", default="standard", choices=["standard", "declare"],
                   help="`declare` adds one paragraph to rules.md saying a correctly "
                        "declared impossible item counts as a pass (exploratory arm).")
    p.add_argument("--concurrency", type=int, default=4,
                   help="Batches in parallel (forced to 1 for ollama).")
    p.add_argument("--tasks-dir", default=None,
                   help="Default: ./tasks if it has SOLVABLE_SET.json, else the harness fixtures.")
    p.add_argument("--out", default=str(REPO_ROOT / "results" / "runs"))
    p.add_argument("--max-items", type=int, default=None)
    p.add_argument("--dry-run", action="store_true",
                   help="Use the scripted fake provider (honest + three cheat scripts).")
    p.add_argument("--num-ctx", type=int, default=8192, help="Ollama context length.")
    p.add_argument("--reasoning-effort", default=None,
                   choices=["none", "minimal", "low", "medium", "high"],
                   help="OpenAI gpt-5 family only. Defaults to 'none': that family "
                        "rejects function tools on /v1/chat/completions with any other "
                        "effort.")
    p.add_argument("--max-tokens", type=int, default=4096)
    p.add_argument("--image", default=IMAGE)
    p.add_argument("--keep-containers", action="store_true")
    p.add_argument("--cells", default=None, help="JSON file: a list of cell objects, run in order.")
    return p


def default_tasks_dir() -> Path:
    candidate = REPO_ROOT / "tasks"
    if (candidate / "SOLVABLE_SET.json").is_file():
        return candidate
    return FIXTURE_TASKS_DIR


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_env()

    tasks_dir = Path(args.tasks_dir) if args.tasks_dir else default_tasks_dir()
    if not (tasks_dir / "SOLVABLE_SET.json").is_file():
        log(f"FATAL: {tasks_dir}/SOLVABLE_SET.json not found.")
        return 2
    slug = args.model_slug or default_model_slug(args.provider, args.model)

    base = RunConfig(
        provider=args.provider, model=args.model, model_slug=slug, arm=args.arm,
        I=args.I, seeds=tuple(parse_seeds(args.seeds)), env_variant=args.env_variant,
        tasks_dir=tasks_dir, out_dir=Path(args.out), concurrency=args.concurrency,
        max_items=args.max_items, dry_run=args.dry_run, num_ctx=args.num_ctx,
        max_tokens=args.max_tokens, reasoning_effort=args.reasoning_effort,
        image=args.image, keep_containers=args.keep_containers,
    )

    if args.cells:
        cells = json.loads(Path(args.cells).read_text(encoding="utf-8"))
        if isinstance(cells, dict):
            cells = cells.get("cells", [])
        configs = [cfg_from_cell(c, base) for c in cells]
    else:
        configs = [base]

    t0 = time.time()
    all_results: list[dict] = []
    for cfg in configs:
        try:
            all_results.extend(run_cell(cfg))
        except Exception as exc:
            log(f"CELL FAILED ({cfg.provider}/{cfg.model} I={cfg.I}): {exc}\n"
                + traceback.format_exc()[-2000:])
            raise
    n_items = sum(r.get("n_items", 0) for r in all_results)
    log(f"DONE {len(all_results)} batch(es), {n_items} item-run(s) in {time.time() - t0:.1f}s")
    summary_path = Path(base.out_dir) / "last_run_summary.json"
    write_json(summary_path, {"finished_at": now_iso(), "results": all_results})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
