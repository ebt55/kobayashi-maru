"""Batch construction (SPEC.md section 2) and the ``batch.json`` manifest.

The measured solvable set is byte-identical in every batch; ``I`` impossible variants are
drawn from the mutated pool and the whole list is permuted by a seeded RNG. Both draws
are reproducible from ``(seed, I)`` alone and the realised order is logged, which also
gives the free cumulative-dose covariate ``n_impossible_before``.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path

from harness.config import git_hash
from harness.records import now_iso, write_json

IMPOSSIBLE_DIR = "impossible"


@dataclass
class Batch:
    batch_id: str
    model_slug: str
    arm: str
    env_variant: str
    I: int
    seed: int
    batch_size: int
    f_realised: float
    tasks_dir: Path
    items: list[dict] = field(default_factory=list)

    @property
    def order(self) -> list[str]:
        return [it["item_key"] for it in self.items]

    def manifest(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "model_slug": self.model_slug,
            "arm": self.arm,
            "env_variant": self.env_variant,
            "I": self.I,
            "seed": self.seed,
            "batch_size": self.batch_size,
            "f_realised": self.f_realised,
            "n_solvable": sum(1 for it in self.items if not it["is_impossible"]),
            "n_impossible": sum(1 for it in self.items if it["is_impossible"]),
            "tasks_dir": str(self.tasks_dir),
        }


def load_solvable_set(tasks_dir: Path) -> dict:
    path = Path(tasks_dir) / "SOLVABLE_SET.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} not found. Builder A writes it; pass --tasks-dir at the fixture "
            f"tasks dir to run against the harness fixtures."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def list_variants(tasks_dir: Path) -> list[str]:
    root = Path(tasks_dir) / IMPOSSIBLE_DIR
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("_"))


def _variant_meta(tasks_dir: Path, variant: str) -> tuple[str, str | None]:
    """(task_id, mutation) for an impossible variant."""
    path = Path(tasks_dir) / IMPOSSIBLE_DIR / variant / "task.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("source_task") or variant.split("__")[0], data.get("mutation")
        except json.JSONDecodeError:
            pass
    parts = variant.split("__")
    return parts[0], (parts[1] if len(parts) > 1 else None)


def make_batch_id(model_slug: str, arm: str, I: int, seed: int) -> str:
    return f"{model_slug}_{arm}_I{I}_s{seed}"


def build_batch(tasks_dir: Path, I: int, seed: int, model_slug: str,
                arm: str = "baseline", env_variant: str = "standard") -> Batch:
    tasks_dir = Path(tasks_dir)
    solvable = load_solvable_set(tasks_dir)
    measured = list(solvable["measured"])          # byte-identical across every batch
    variants = list_variants(tasks_dir)

    if I > len(variants):
        raise ValueError(f"I={I} but only {len(variants)} impossible variants exist "
                         f"under {tasks_dir / IMPOSSIBLE_DIR}")
    if I == len(variants):
        chosen = sorted(variants)
    else:
        chosen = random.Random(seed).sample(sorted(variants), I)

    items: list[dict] = []
    for task_id in measured:
        items.append({
            "item_key": task_id,
            "task_id": task_id,
            "task_dir": str(tasks_dir / task_id),
            "is_impossible": False,
            "mutation": None,
        })
    for variant in chosen:
        source, mutation = _variant_meta(tasks_dir, variant)
        items.append({
            "item_key": variant,
            "task_id": source,
            "task_dir": str(tasks_dir / IMPOSSIBLE_DIR / variant),
            "is_impossible": True,
            "mutation": mutation,
        })

    random.Random(seed + 1000 * I).shuffle(items)

    n_impossible_before = 0
    for position, item in enumerate(items):
        item["position"] = position
        item["n_items_before"] = position
        item["n_impossible_before"] = n_impossible_before
        if item["is_impossible"]:
            n_impossible_before += 1

    batch_size = len(items)
    return Batch(
        batch_id=make_batch_id(model_slug, arm, I, seed),
        model_slug=model_slug,
        arm=arm,
        env_variant=env_variant,
        I=I,
        seed=seed,
        batch_size=batch_size,
        f_realised=round(I / batch_size, 4) if batch_size else 0.0,
        tasks_dir=tasks_dir,
        items=items,
    )


# ------------------------------------------------------------------- batch.json

def batch_json_path(out_dir: Path, batch_id: str) -> Path:
    return Path(out_dir) / batch_id / "batch.json"


def items_jsonl_path(out_dir: Path, batch_id: str) -> Path:
    return Path(out_dir) / batch_id / "items.jsonl"


def new_batch_json(batch: Batch, cfg, provider_describe: dict | None = None) -> dict:
    return {
        "schema_version": 1,
        "manifest": batch.manifest(),
        "order": batch.order,
        "items": [
            {k: it[k] for k in ("position", "item_key", "task_id", "is_impossible",
                                "mutation", "n_impossible_before")}
            for it in batch.items
        ],
        "provider": cfg.provider,
        "model": cfg.model,
        "model_slug": cfg.model_slug,
        "model_config": cfg.model_config(),
        "provider_describe": provider_describe or {},
        "arm": batch.arm,
        "env_variant": batch.env_variant,
        "harness_git_hash": git_hash(),
        "run_config": cfg.to_dict(),
        "started": now_iso(),
        "ended": None,
        "tally_history": [],
        "dry_run": bool(cfg.dry_run),
    }


def write_batch_json(out_dir: Path, batch_id: str, payload: dict) -> Path:
    path = batch_json_path(out_dir, batch_id)
    write_json(path, payload)
    return path
