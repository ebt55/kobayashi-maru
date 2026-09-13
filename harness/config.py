"""Paths, limits and the run configuration object (SPEC.md sections 2 and 7)."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HARNESS_DIR.parent
PROMPTS_DIR = HARNESS_DIR / "prompts"
PEER_NOTES_DIR = HARNESS_DIR / "peer_notes"
DOCKER_DIR = HARNESS_DIR / "docker"
FIXTURE_TASKS_DIR = HARNESS_DIR / "tests" / "fixtures" / "tasks"

IMAGE = "dosecurve-sandbox:latest"

# Agent-facing limits (SPEC.md section 2, "Tools exposed to the agent").
MAX_TURNS = 30
ITEM_WALL_CLOCK_S = 600          # 10 minutes per item
BASH_TIMEOUT_S = 60              # per bash call, enforced in-container AND host-side
TOOL_OUTPUT_LIMIT = 8000         # chars, then truncated: true
SUBMIT_SUMMARY_WORDS = 80
MAX_NUDGES = 2

# Harness-side limits.
RUN_TESTS_TIMEOUT_S = 120
GRADE_TIMEOUT_S = 120
SNAPSHOT_TIMEOUT_S = 120
MAX_TOKENS = 4096                # per assistant turn
FILE_CONTENT_LIMIT = 20000       # final_files / snapshot contents

ARMS = ("baseline", "peer_neutral", "peer_tip", "peer_tip_read", "continuous")
ENV_VARIANTS = ("standard", "salient")

#: Which RULES file the system prompt is loaded from. "standard" is rules.md, frozen
#: for the sweeps; "declare" is rules.md plus one paragraph saying a correctly declared
#: impossible item counts as a pass (exploratory follow-up arm).
RULES_VARIANTS = ("standard", "declare")
RULES_FILES = {"standard": "rules.md", "declare": "rules_declare.md"}

#: Peer-note file per arm. Arms not listed here get no PEER_NOTES.md.
PEER_NOTE_FILES = {"peer_neutral": "neutral.md", "peer_tip": "tip.md",
                   "peer_tip_read": "tip_read.md"}

#: Arms that hold ONE conversation for the whole batch (plan section 5, optional arm B').
#: Peer notes are not used in this arm; the context itself is the memory channel.
CONTINUOUS_ARMS = ("continuous",)
#: Whole-batch turn budget for a continuous session (per-item limits still apply).
BATCH_TURN_CAP = 400

# Container resource limits (every container, agent and grader).
CONTAINER_ARGS = [
    "--network", "none",
    "--memory", "1g",
    "--cpus", "2",
    "--pids-limit", "256",
]


def load_env() -> None:
    """Load .env from the repo root if python-dotenv is available. Never prints a key."""
    try:
        from dotenv import load_dotenv
    except Exception:  # pragma: no cover - dotenv is a declared dependency
        return
    load_dotenv(REPO_ROOT / ".env", override=False)


def git_hash() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, timeout=20,
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


@dataclass
class RunConfig:
    """One cell of the sweep: a provider/model/arm and the seeds to run at one I."""

    provider: str = "fake"
    model: str = "fake-model"
    model_slug: str = "fake"
    arm: str = "baseline"
    I: int = 0
    seeds: tuple[int, ...] = (0,)
    env_variant: str = "standard"
    rules_variant: str = "standard"
    tasks_dir: Path = FIXTURE_TASKS_DIR
    out_dir: Path = REPO_ROOT / "results" / "runs"
    concurrency: int = 1
    max_items: int | None = None
    dry_run: bool = False

    # model knobs
    num_ctx: int = 8192                    # ollama only
    max_tokens: int = MAX_TOKENS
    temperature: float | None = None
    reasoning_effort: str | None = None    # OpenAI gpt-5 family only

    # loop knobs
    max_turns: int = MAX_TURNS
    item_wall_clock_s: int = ITEM_WALL_CLOCK_S
    bash_timeout_s: int = BASH_TIMEOUT_S
    tool_output_limit: int = TOOL_OUTPUT_LIMIT

    image: str = IMAGE
    keep_containers: bool = False
    batch_turn_cap: int = BATCH_TURN_CAP   # continuous arm only
    extra: dict = field(default_factory=dict)

    @property
    def is_continuous(self) -> bool:
        return self.arm in CONTINUOUS_ARMS

    def __post_init__(self) -> None:
        self.tasks_dir = Path(self.tasks_dir)
        self.out_dir = Path(self.out_dir)
        self.seeds = tuple(self.seeds)
        if self.arm not in ARMS:
            raise ValueError(f"arm must be one of {ARMS}, got {self.arm!r}")
        if self.env_variant not in ENV_VARIANTS:
            raise ValueError(f"env_variant must be one of {ENV_VARIANTS}, got {self.env_variant!r}")
        if self.rules_variant not in RULES_VARIANTS:
            raise ValueError(f"rules_variant must be one of {RULES_VARIANTS}, "
                             f"got {self.rules_variant!r}")

    def model_config(self) -> dict:
        """The `model_config` block written into every record and into batch.json."""
        cfg = {
            "max_tokens": self.max_tokens,
            "max_turns": self.max_turns,
            "item_wall_clock_s": self.item_wall_clock_s,
            "bash_timeout_s": self.bash_timeout_s,
            "tool_output_limit": self.tool_output_limit,
            "env_variant": self.env_variant,
            "rules_variant": self.rules_variant,
            "image": self.image,
        }
        if self.dry_run:
            # A dry-run record keeps the cell's provider/model strings but is produced by
            # the scripted fake provider; this flag keeps that unambiguous downstream.
            cfg["dry_run"] = True
        if self.is_continuous:
            cfg["session_mode"] = "continuous"
            cfg["batch_turn_cap"] = self.batch_turn_cap
        if self.provider == "ollama":
            cfg["num_ctx"] = self.num_ctx
            # `think` is only sent on the wire for reasoning-capable qwen3 models; None
            # records "not sent" so the log matches the request.
            cfg["think"] = False if self.model.startswith("qwen3") else None
            cfg["keep_alive"] = "10m"
        if self.temperature is not None:
            cfg["temperature"] = self.temperature
        if self.reasoning_effort is not None:
            cfg["reasoning_effort"] = self.reasoning_effort
        return cfg

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tasks_dir"] = str(self.tasks_dir)
        d["out_dir"] = str(self.out_dir)
        d["seeds"] = list(self.seeds)
        return d


def truncate(text: str, limit: int) -> tuple[str, bool]:
    """Truncate ``text`` to ``limit`` chars; return (text, truncated_flag)."""
    if text is None:
        return "", False
    if len(text) <= limit:
        return text, False
    keep = max(limit - 60, 0)
    return text[:keep] + f"\n... [truncated: {len(text) - keep} more chars]", True


def truncate_words(text: str, max_words: int = SUBMIT_SUMMARY_WORDS) -> str:
    words = (text or "").split()
    if len(words) <= max_words:
        return (text or "").strip()
    return " ".join(words[:max_words])


def env_key(name: str) -> str | None:
    """Read an API key from the environment. Never log the value."""
    val = os.environ.get(name)
    return val.strip() if val and val.strip() else None
