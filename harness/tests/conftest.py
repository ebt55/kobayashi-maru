"""Shared fixtures and marker registration for the harness tests.

Markers:
  ``docker``  -- needs Docker and the ``dosecurve-sandbox:latest`` image
  ``ollama``  -- needs a live Ollama at 127.0.0.1:11434 with ``llama3.1:8b``

Everything unmarked runs with no Docker, no Ollama and no API key.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.config import FIXTURE_TASKS_DIR, RunConfig
from harness.sandbox import LocalSandbox, docker_available, image_available


# Markers `docker`, `ollama` and `live` are registered in pyproject.toml by the
# orchestrator; this file only supplies fixtures.


@pytest.fixture(scope="session")
def tasks_dir() -> Path:
    return FIXTURE_TASKS_DIR


@pytest.fixture(scope="session")
def template_dir(tasks_dir) -> Path:
    return tasks_dir / "_template"


@pytest.fixture(scope="session")
def runner_path(tasks_dir) -> Path:
    return tasks_dir / "_runner" / "run_cases.py"


@pytest.fixture
def local_cfg(tasks_dir, tmp_path) -> RunConfig:
    return RunConfig(provider="fake", model="fake-model", model_slug="fake",
                     tasks_dir=tasks_dir, out_dir=tmp_path / "runs", dry_run=True,
                     item_wall_clock_s=120)


@pytest.fixture
def local_sandbox(tasks_dir, tmp_path):
    sb = LocalSandbox("test_batch", tasks_dir=tasks_dir, root=tmp_path / "work")
    sb.start()
    yield sb
    sb.close()


@pytest.fixture
def local_grader_factory(tasks_dir, tmp_path):
    """A LocalSandbox factory for fresh_grade -- unit tests only, never experiments."""
    counter = {"n": 0}

    def factory():
        counter["n"] += 1
        return LocalSandbox(f"grade_{counter['n']}", tasks_dir=tasks_dir,
                            root=tmp_path / f"grade_{counter['n']}").start()

    return factory


def require_docker():
    if not docker_available():
        pytest.skip("Docker is not available")
    if not image_available():
        pytest.skip("dosecurve-sandbox:latest is not built "
                    "(docker build -t dosecurve-sandbox:latest harness/docker)")
