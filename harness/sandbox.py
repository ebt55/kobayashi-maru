"""Sandboxes: one Docker container per batch, one work dir per item.

``DockerSandbox`` is the only sandbox used for experiments. ``LocalSandbox`` exists
SOLELY so the unit tests can run on a machine without Docker; it gives the agent an
un-isolated temp directory on the host and MUST NOT be used for a real run.

Work-dir layout (SPEC.md section 1, "Sandbox work dir"): ``_template/*`` + ``spec.md`` +
``solution.py`` + ``tests/`` + ``.grader/`` (+ ``PEER_NOTES.md`` in peer arms, + a copy of
``.grader/expected_outputs.json`` at ``./expected_outputs.json`` when the salient
env-variant is on). Nothing else: no ``task.json``, no ``probes.json``, no ``reference.py``.

Every host-side subprocess call uses an argument list -- never a shell string.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path
from typing import NamedTuple

from harness.config import (
    CONTAINER_ARGS,
    DOCKER_DIR,
    IMAGE,
    PEER_NOTES_DIR,
    PEER_NOTE_FILES,
    RUN_TESTS_TIMEOUT_S,
    SNAPSHOT_TIMEOUT_S,
)

SANDBOX_UID = 10001
SANDBOX_GID = 10001
WORK_ROOT = "/work"

#: Sandbox environment version.
#:   1 = the frozen sweeps: the work dir was ``/work/<item_key>``, so the directory name
#:       carried the mutation label (``t14_luhn_check_digit__unreachable``) and leaked it
#:       through `pwd`, `ls ..`, `ls /work` and Python tracebacks; earlier items' work
#:       dirs also stayed readable for the life of the batch container.
#:   2 = the work dir is ``/work/item_<position>``: opaque, deterministic, no label, and
#:       every earlier item directory is removed before the next item is prepared.
#: Records written before the field existed are implicitly version 1.
ENV_VERSION = 2

# Files copied into the work dir from the task dir, beyond tests/ and .grader/.
TASK_FILES = ("spec.md", "solution.py")
#: NEVER copied into a sandbox.
HOST_ONLY = ("task.json", "probes.json", "reference.py")

_READ_SCRIPT = (
    "import base64,sys;"
    "sys.stdout.write(base64.b64encode(open(sys.argv[1],'rb').read()).decode())"
)
_WRITE_SCRIPT = (
    "import base64,os,sys;"
    "p=sys.argv[1];d=os.path.dirname(p);"
    "os.makedirs(d,exist_ok=True) if d else None;"
    "open(p,'wb').write(base64.b64decode(sys.stdin.read()))"
)


class SandboxError(RuntimeError):
    pass


class ExecResult(NamedTuple):
    output: str          # stdout + stderr, interleaved
    exit_code: int
    timed_out: bool


# --------------------------------------------------------------------- assembly

def _copy_tree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def resolve_template_dir(task_dir: Path, tasks_dir: Path | None = None) -> Path:
    """Find ``_template`` for a task dir (impossible variants live one level deeper)."""
    if tasks_dir is not None:
        cand = Path(tasks_dir) / "_template"
        if cand.is_dir():
            return cand
    here = Path(task_dir).resolve()
    for parent in here.parents:
        cand = parent / "_template"
        if cand.is_dir():
            return cand
    raise SandboxError(f"no _template/ found above {task_dir}")


def assemble_agent_workdir(
    dest: Path,
    task_dir: Path,
    template_dir: Path,
    arm: str = "baseline",
    env_variant: str = "standard",
) -> Path:
    """Build exactly what the agent sees, on the host, at ``dest``."""
    task_dir = Path(task_dir)
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    _copy_tree(Path(template_dir), dest)
    for name in TASK_FILES:
        src = task_dir / name
        if src.is_file():
            shutil.copy2(src, dest / name)
    for sub in ("tests", ".grader"):
        src = task_dir / sub
        if src.is_dir():
            _copy_tree(src, dest / sub)

    peer_note = PEER_NOTE_FILES.get(arm)
    if peer_note:
        shutil.copy2(PEER_NOTES_DIR / peer_note, dest / "PEER_NOTES.md")

    if env_variant == "salient":
        # Pre-registered decision rule (plan section 7, phase 3): the answer file is
        # moved into plain sight. Rules are unchanged; this is the only permitted
        # environment change and it is disclosed.
        src = task_dir / ".grader" / "expected_outputs.json"
        if src.is_file():
            shutil.copy2(src, dest / "expected_outputs.json")

    for name in HOST_ONLY:
        leaked = dest / name
        if leaked.exists():  # defensive: must never reach a sandbox
            leaked.unlink()
    return dest


def assemble_pristine_workdir(
    dest: Path,
    task_dir: Path,
    template_dir: Path,
    submitted_solution: str,
    runner_path: Path,
) -> Path:
    """Build the fresh re-grade dir: pristine task files + the SUBMITTED solution.py.

    The pristine files come from the tasks dir on the host, never from the agent's
    container. Adds ``probes.json`` and ``run_cases.py``, which the agent never sees.
    """
    task_dir = Path(task_dir)
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    _copy_tree(Path(template_dir), dest)
    for sub in ("tests", ".grader"):
        src = task_dir / sub
        if src.is_dir():
            _copy_tree(src, dest / sub)
    probes = task_dir / "probes.json"
    if probes.is_file():
        shutil.copy2(probes, dest / "probes.json")
    shutil.copy2(Path(runner_path), dest / "run_cases.py")

    (dest / "solution.py").write_text(submitted_solution or "", encoding="utf-8", newline="\n")
    return dest


# ------------------------------------------------------------------ docker sandbox

def _tar_bytes(host_dir: Path, prefix: str) -> bytes:
    """Tar a host directory under ``prefix/`` with sandbox-user ownership.

    Streaming a tar through ``docker cp -`` avoids Windows path parsing in the docker
    CLI and sets uid/gid directly, so no post-copy chown is needed.
    """
    host_dir = Path(host_dir)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        root = tarfile.TarInfo(prefix)
        root.type = tarfile.DIRTYPE
        root.mode = 0o755
        root.uid = SANDBOX_UID
        root.gid = SANDBOX_GID
        tf.addfile(root)
        for dirpath, dirnames, filenames in os.walk(host_dir):
            dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
            rel_dir = os.path.relpath(dirpath, host_dir).replace(os.sep, "/")
            for name in sorted(dirnames):
                rel = name if rel_dir == "." else f"{rel_dir}/{name}"
                ti = tarfile.TarInfo(f"{prefix}/{rel}")
                ti.type = tarfile.DIRTYPE
                ti.mode = 0o755
                ti.uid, ti.gid = SANDBOX_UID, SANDBOX_GID
                tf.addfile(ti)
            for name in sorted(filenames):
                if name.endswith(".pyc"):
                    continue
                rel = name if rel_dir == "." else f"{rel_dir}/{name}"
                full = os.path.join(dirpath, name)
                data = Path(full).read_bytes()
                ti = tarfile.TarInfo(f"{prefix}/{rel}")
                ti.size = len(data)
                ti.mode = 0o755 if name.endswith(".sh") else 0o644
                ti.uid, ti.gid = SANDBOX_UID, SANDBOX_GID
                tf.addfile(ti, io.BytesIO(data))
    return buf.getvalue()


def _safe_name(text: str) -> str:
    return "".join(c if (c.isalnum() or c in "_.-") else "-" for c in text)


class DockerSandbox:
    """One container per batch. ``--network none --memory 1g --cpus 2 --pids-limit 256``."""

    kind = "docker"

    def __init__(
        self,
        batch_id: str,
        tasks_dir: Path | None = None,
        image: str = IMAGE,
        name_prefix: str = "dc_",
        template_dir: Path | None = None,
        keep: bool = False,
        env_version: int = ENV_VERSION,
    ) -> None:
        self.batch_id = batch_id
        self.env_version = int(env_version)
        self._container_dirs: dict[str, str] = {}
        self.tasks_dir = Path(tasks_dir) if tasks_dir else None
        self.image = image
        self.name = f"{name_prefix}{_safe_name(batch_id)}"[:120]
        self.template_dir = Path(template_dir) if template_dir else None
        self.keep = keep
        self._started = False
        self._host_dirs: dict[str, Path] = {}
        self._staging = Path(tempfile.mkdtemp(prefix="dcstage_"))

    # -- lifecycle -------------------------------------------------------
    def start(self) -> "DockerSandbox":
        if self._started:
            return self
        subprocess.run(["docker", "rm", "-f", self.name],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        cmd = ["docker", "run", "-d", *CONTAINER_ARGS, "--name", self.name,
               self.image, "sleep", "infinity"]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, errors="replace", timeout=300)
        if proc.returncode != 0:
            raise SandboxError(f"docker run failed ({proc.returncode}): {proc.stdout.strip()}")
        self._started = True
        return self

    def close(self) -> None:
        if self._started and not self.keep:
            subprocess.run(["docker", "rm", "-f", self.name],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
        self._started = False
        shutil.rmtree(self._staging, ignore_errors=True)

    def __enter__(self) -> "DockerSandbox":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.close()

    # -- plumbing --------------------------------------------------------
    def _dirname(self, item_key: str) -> str:
        """Container directory name for an item.

        env v2 maps the item to an opaque ``item_<position>``; the item_key never
        reaches the container. v1 (the frozen sweeps) used the item_key itself.
        """
        return self._container_dirs.get(item_key, item_key)

    def _workdir(self, item_key: str) -> str:
        return f"{WORK_ROOT}/{self._dirname(item_key)}"

    def _exec_root(self, argv: list[str], timeout: float = 60) -> ExecResult:
        """Run an argv with /work as the cwd (used for cross-item housekeeping)."""
        try:
            proc = self._run(["docker", "exec", "-w", WORK_ROOT, self.name, *argv],
                             timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            return ExecResult((exc.output or b"").decode("utf-8", "replace"), -1, True)
        return ExecResult(proc.stdout.decode("utf-8", "replace"), proc.returncode, False)

    def clear_work_root(self) -> None:
        """Remove every item directory in the batch container.

        Called before each item is prepared (env v2). The previous item's snapshot,
        in-sandbox grade and final files have all been collected by then, so nothing is
        lost -- and the agent can no longer read a sibling item's grader files, nor see
        from `ls /work` how many items came before it.
        """
        self._exec_root(["sh", "-c", "rm -rf /work/* /work/.[!.]* 2>/dev/null; exit 0"])

    def _run(self, args: list[str], timeout: float, stdin: bytes | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            args,
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )

    def _exec_argv(self, item_key: str, argv: list[str], timeout: float,
                   stdin: bytes | None = None, interactive: bool = False) -> ExecResult:
        """Run an argv directly in the container (no shell, no in-container timeout)."""
        base = ["docker", "exec", "-w", self._workdir(item_key)]
        if interactive:
            base.append("-i")
        base.append(self.name)
        try:
            proc = self._run(base + argv, timeout=timeout, stdin=stdin)
        except subprocess.TimeoutExpired as exc:
            partial = (exc.output or b"").decode("utf-8", "replace")
            return ExecResult(partial, -1, True)
        return ExecResult(proc.stdout.decode("utf-8", "replace"), proc.returncode, False)

    def put_dir(self, item_key: str, host_dir: Path) -> None:
        """Copy a host directory to this item's work dir inside the container."""
        payload = _tar_bytes(Path(host_dir), self._dirname(item_key))
        proc = self._run(["docker", "cp", "-", f"{self.name}:{WORK_ROOT}"],
                         timeout=300, stdin=payload)
        if proc.returncode != 0:
            raise SandboxError(
                f"docker cp failed ({proc.returncode}): "
                f"{proc.stdout.decode('utf-8', 'replace').strip()}"
            )

    # -- public API ------------------------------------------------------
    def prepare_item(self, item_key: str, task_dir: Path, arm: str = "baseline",
                     env_variant: str = "standard", template_dir: Path | None = None,
                     position: int | None = None) -> Path:
        if not self._started:
            self.start()
        tdir = Path(template_dir or self.template_dir
                    or resolve_template_dir(task_dir, self.tasks_dir))
        if self.env_version >= 2:
            # opaque directory name: nothing about the task or its mutation
            self._container_dirs[item_key] = (
                f"item_{int(position):02d}" if position is not None else "item")
            # and no sibling item survives into this item's container
            self.clear_work_root()
        host_dir = self._staging / self._dirname(item_key)
        shutil.rmtree(host_dir, ignore_errors=True)
        assemble_agent_workdir(host_dir, task_dir, tdir, arm, env_variant)
        self.put_dir(item_key, host_dir)
        self._host_dirs[item_key] = host_dir
        return host_dir

    def exec(self, item_key: str, command: str, timeout_s: int = 60) -> ExecResult:
        """Run a shell command. Enforced twice: in-container `timeout` + host-side."""
        argv = ["timeout", str(int(timeout_s)), "sh", "-c", command]
        res = self._exec_argv(item_key, argv, timeout=timeout_s + 20)
        if res.exit_code == 124:  # coreutils timeout
            return ExecResult(res.output, 124, True)
        return res

    def read_file(self, item_key: str, path: str) -> str:
        res = self._exec_argv(item_key, ["python", "-c", _READ_SCRIPT, path], timeout=60)
        if res.exit_code != 0:
            raise SandboxError(res.output.strip() or f"read_file failed: {path}")
        import base64
        return base64.b64decode(res.output).decode("utf-8", "replace")

    def write_file(self, item_key: str, path: str, content: str) -> None:
        import base64
        payload = base64.b64encode((content or "").encode("utf-8"))
        res = self._exec_argv(item_key, ["python", "-c", _WRITE_SCRIPT, path],
                              timeout=60, stdin=payload, interactive=True)
        if res.exit_code != 0:
            raise SandboxError(res.output.strip() or f"write_file failed: {path}")

    def run_visible_tests(self, item_key: str, timeout_s: int = RUN_TESTS_TIMEOUT_S) -> ExecResult:
        return self.exec(item_key, "sh run_tests.sh", timeout_s=timeout_s)

    def snapshot(self, item_key: str) -> dict:
        res = self._exec_argv(item_key, ["python", "/opt/dc/snapshot.py", "."],
                              timeout=SNAPSHOT_TIMEOUT_S)
        return _parse_json(res, "snapshot")

    def hidden_grade(self, item_key: str, timeout_s: int = SNAPSHOT_TIMEOUT_S) -> dict:
        res = self._exec_argv(item_key, ["python", "/opt/dc/hidden_grade.py", "."],
                              timeout=timeout_s)
        try:
            return _parse_json(res, "hidden_grade")
        except SandboxError as exc:
            return {"hidden_pass": False, "passed": 0, "total": 0, "output": str(exc)[-4000:]}

    def run_cases(self, item_key: str, cases_file: str, module: str = "solution",
                  timeout_s: int = 120) -> dict:
        res = self._exec_argv(
            item_key,
            ["python", "run_cases.py", "--module", module, "--cases", cases_file],
            timeout=timeout_s,
        )
        try:
            payload = _parse_json(res, "run_cases")
        except SandboxError as exc:
            return {"passed": 0, "total": 0, "failures": [{"error": str(exc)[-300:]}],
                    "output": res.output[-4000:]}
        payload["output"] = res.output[-4000:]
        return payload


def _parse_json(res: ExecResult, what: str) -> dict:
    text = (res.output or "").strip()
    for line in reversed(text.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    raise SandboxError(f"{what}: no JSON in output (rc={res.exit_code}): {text[-600:]}")


# ------------------------------------------------------------------- local sandbox

class LocalSandbox:
    """UNIT TESTS ONLY -- not isolated, NOT for experiments.

    Same interface as ``DockerSandbox`` but runs everything in a host temp directory
    with the host interpreter. It provides no network isolation, no memory/CPU/pid
    limits and no filesystem isolation, so a real run must never use it.
    """

    kind = "local"

    def __init__(self, batch_id: str, tasks_dir: Path | None = None,
                 template_dir: Path | None = None, root: Path | None = None,
                 keep: bool = False, env_version: int = ENV_VERSION, **_ignored) -> None:
        self.batch_id = batch_id
        self.env_version = int(env_version)
        self._container_dirs: dict[str, str] = {}
        self.tasks_dir = Path(tasks_dir) if tasks_dir else None
        self.template_dir = Path(template_dir) if template_dir else None
        self.keep = keep
        self._owns_root = root is None
        self.root = Path(root) if root else Path(tempfile.mkdtemp(prefix="dclocal_"))
        self._host_dirs: dict[str, Path] = {}
        self._started = True

    def start(self) -> "LocalSandbox":
        self.root.mkdir(parents=True, exist_ok=True)
        return self

    def close(self) -> None:
        if self._owns_root and not self.keep:
            shutil.rmtree(self.root, ignore_errors=True)

    def __enter__(self) -> "LocalSandbox":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.close()

    def _dirname(self, item_key: str) -> str:
        return self._container_dirs.get(item_key, item_key)

    def _dir(self, item_key: str) -> Path:
        return self.root / self._dirname(item_key)

    def clear_work_root(self) -> None:
        """Mirror of the Docker cleanup: no sibling item survives into the next one."""
        if self.root.is_dir():
            for child in self.root.iterdir():
                shutil.rmtree(child, ignore_errors=True) if child.is_dir() else child.unlink(
                    missing_ok=True)

    def put_dir(self, item_key: str, host_dir: Path) -> None:
        dest = self._dir(item_key)
        if Path(host_dir).resolve() != dest.resolve():
            shutil.rmtree(dest, ignore_errors=True)
            _copy_tree(Path(host_dir), dest)
        self._host_dirs[item_key] = dest

    def prepare_item(self, item_key: str, task_dir: Path, arm: str = "baseline",
                     env_variant: str = "standard", template_dir: Path | None = None,
                     position: int | None = None) -> Path:
        tdir = Path(template_dir or self.template_dir
                    or resolve_template_dir(task_dir, self.tasks_dir))
        if self.env_version >= 2:
            self._container_dirs[item_key] = (
                f"item_{int(position):02d}" if position is not None else "item")
            self.clear_work_root()
        dest = self._dir(item_key)
        shutil.rmtree(dest, ignore_errors=True)
        assemble_agent_workdir(dest, task_dir, tdir, arm, env_variant)
        self._host_dirs[item_key] = dest
        return dest

    def exec(self, item_key: str, command: str, timeout_s: int = 60) -> ExecResult:
        wd = self._dir(item_key)
        sh = shutil.which("sh")
        args: list[str] | str
        if sh:
            args = [sh, "-c", command]
            shell = False
        else:  # pragma: no cover - Windows without Git Bash
            args = command
            shell = True
        try:
            proc = subprocess.run(args, cwd=str(wd), shell=shell,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  timeout=timeout_s)
        except subprocess.TimeoutExpired as exc:
            return ExecResult((exc.output or b"").decode("utf-8", "replace"), -1, True)
        return ExecResult(proc.stdout.decode("utf-8", "replace"), proc.returncode, False)

    def read_file(self, item_key: str, path: str) -> str:
        target = self._dir(item_key) / path
        return target.read_text(encoding="utf-8", errors="replace")

    def write_file(self, item_key: str, path: str, content: str) -> None:
        target = self._dir(item_key) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content or "", encoding="utf-8", newline="\n")

    def _py(self, item_key: str, argv: list[str], timeout_s: int) -> ExecResult:
        try:
            proc = subprocess.run([sys.executable, *argv], cwd=str(self._dir(item_key)),
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  timeout=timeout_s, env=_clean_env())
        except subprocess.TimeoutExpired as exc:
            return ExecResult((exc.output or b"").decode("utf-8", "replace"), -1, True)
        return ExecResult(proc.stdout.decode("utf-8", "replace"), proc.returncode, False)

    def run_visible_tests(self, item_key: str, timeout_s: int = RUN_TESTS_TIMEOUT_S) -> ExecResult:
        return self._py(item_key, ["-m", "pytest", "tests/", "-q", "-p", "no:cacheprovider"],
                        timeout_s)

    def snapshot(self, item_key: str) -> dict:
        res = self._py(item_key, [str(DOCKER_DIR / "snapshot.py"), "."], SNAPSHOT_TIMEOUT_S)
        return _parse_json(res, "snapshot")

    def hidden_grade(self, item_key: str, timeout_s: int = SNAPSHOT_TIMEOUT_S) -> dict:
        res = self._py(item_key, [str(DOCKER_DIR / "hidden_grade.py"), "."], timeout_s)
        try:
            return _parse_json(res, "hidden_grade")
        except SandboxError as exc:
            return {"hidden_pass": False, "passed": 0, "total": 0, "output": str(exc)[-4000:]}

    def run_cases(self, item_key: str, cases_file: str, module: str = "solution",
                  timeout_s: int = 120) -> dict:
        res = self._py(item_key, ["run_cases.py", "--module", module, "--cases", cases_file],
                       timeout_s)
        try:
            payload = _parse_json(res, "run_cases")
        except SandboxError as exc:
            return {"passed": 0, "total": 0, "failures": [{"error": str(exc)[-300:]}],
                    "output": res.output[-4000:]}
        payload["output"] = res.output[-4000:]
        return payload


def _clean_env() -> dict:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("PYTEST_CURRENT_TEST", None)
    env.pop("PYTEST_ADDOPTS", None)
    return env


def docker_available() -> bool:
    try:
        proc = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              timeout=30)
        return proc.returncode == 0
    except Exception:
        return False


def image_available(image: str = IMAGE) -> bool:
    try:
        proc = subprocess.run(["docker", "image", "inspect", image],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              timeout=60)
        return proc.returncode == 0
    except Exception:
        return False


def timed(fn, *args, **kwargs):
    """Run ``fn`` and return (result, duration_ms)."""
    t0 = time.perf_counter()
    out = fn(*args, **kwargs)
    return out, int((time.perf_counter() - t0) * 1000)
