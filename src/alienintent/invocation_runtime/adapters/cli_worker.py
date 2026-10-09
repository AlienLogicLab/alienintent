"""Safe explicit-mode CLI worker adapter with timeout and cancellation evidence."""

from __future__ import annotations

import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from typing import Callable, Final, Mapping, Sequence
import uuid

from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
from alienintent.invocation_runtime.domain.diagnostics import process_diagnostics
from alienintent.invocation_runtime.domain.runtime import BudgetRecord, FEATURE_REGRESSION_RECEIPT_PATH, INVOCATION_MARKER, INVOCATION_OWNER_MARKER, InvocationRole, ProcessResult, ProviderCapabilities, owner_token, require_eligible
from alienintent.invocation_runtime.ports.process_ownership import ProcessOwnership
from alienintent.invocation_runtime.ports.worker_process import WorkerProcess

# How often owned work is re-observed while the invocation waits for it.
OWNED_WORK_POLL_SECONDS = 0.05
# How much of each worker output stream `outputs` keeps, from the end.
OUTPUT_TAIL = 4000
# A per-invocation worker command: (invocation id, role, workspace) -> (argv, the text for standard input).
WorkerCommand = Callable[[str, InvocationRole, Path], tuple[Sequence[str], str]]
# The only PATH a command run as the worker user gets (unit WORKER-CREDENTIAL-BOUNDARY).
WORKER_PATH = "/usr/bin:/bin"
_FULL_SHA = re.compile(r"[0-9a-f]{40}")
_VARIABLE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _decoded(data: bytes | str | None) -> str:
    """A partial stream as text: `TimeoutExpired` carries it as bytes, or None when nothing was read."""
    return data.decode(errors="replace") if isinstance(data, bytes) else data or ""


def worker_prefix(user: str, environment: Mapping[str, str]) -> list[str]:
    """The one sudo rule every command run on a worker's behalf starts with:
    `sudo -n -u <user> -- env -i PATH=/usr/bin:/bin <the allowlisted variables>`. Nothing else is inherited."""
    if not user or user.startswith("-") or any(c.isspace() or c == "\x00" for c in user):
        raise ValueError("the worker user must be a plain user name")
    variables = []
    for name, value in sorted(environment.items()):
        if not _VARIABLE.fullmatch(name) or "\x00" in value:
            raise ValueError("worker environment variables must be plain names and values")
        if name != "PATH":
            variables.append(f"{name}={value}")
    return ["sudo", "-n", "-u", user, "--", "env", "-i", f"PATH={WORKER_PATH}", *variables]


def run_as_worker(user: str, environment: Mapping[str, str], argv: Sequence[str], *, cwd: Path | None = None,
                  input: bytes | None = None, timeout: float = 300) -> subprocess.CompletedProcess:
    """Run one command as the worker user through the sudo rule; its output is data, never trusted further."""
    return subprocess.run([*worker_prefix(user, environment), *argv], cwd=cwd, input=input, capture_output=True,
                          check=False, timeout=timeout)


def kill_as_worker(user: str, signum: int, target: str) -> None:
    """`sudo -n -u <user> kill -<signum> -- <target>` (a pid, or `-<pgid>` for a process group); no `env -i`."""
    try:
        subprocess.run(["sudo", "-n", "-u", user, "kill", f"-{int(signum)}", "--", target], capture_output=True,
                       check=False, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        pass


class CliWorkerProvider(WorkerProcess):
    _SAFE_MODES: Final = frozenset({"explicit", "read-only", "workspace-write", "danger-full-access", "manual", "bypassPermissions"})

    def __init__(self, provider: str, executable: str | WorkerCommand, arguments: tuple[str, ...], permission_mode: str, dimensions: frozenset[str], environment: Mapping[str, str] | None = None, *, ownership: ProcessOwnership | None = None, worker_user: str | None = None, results: Path | None = None, regression_base: Callable[[str], str | None] | None = None, work_identity: Callable[[str], str | None] | None = None, feature_regressions: bool = True) -> None:
        """`executable` with `arguments` is one fixed command line for every invocation, run with standard input
        inherited; or a WorkerCommand (with no `arguments`) evaluated at every `run`, whose text goes to the worker's
        standard input.

        With `worker_user` (it needs `environment`, `results` and `regression_base`), every session command and the
        VERIFIER's feature-regression runner run through the sudo rule (`worker_prefix`), its receipt is written
        under `<results>/<invocation id>/`, its `--base` is `regression_base(invocation id)` (the release record's
        starting revision, a full SHA) and stopping goes through `sudo -n -u <user> kill`. The session's allowlist
        also carries the three identity variables its export-mode `context_command` names: ALIENINTENT_ROLE,
        ALIENINTENT_CORRELATION (the invocation id) and ALIENINTENT_WORK_IDENTITY (`work_identity(invocation id)`).
        Without it, unchanged. `feature_regressions=False` (the registry profile, where the control plane's
        REGRESSION-GATE decides admission before the session) runs no feature-regression runner."""
        fixed = (executable, *arguments) if isinstance(executable, str) else None
        if permission_mode not in self._SAFE_MODES or not executable or (fixed is None and (not callable(executable) or arguments)) \
                or any("\x00" in part for part in fixed or ()):
            raise ValueError("explicit safe permission mode and safe arguments are required")
        if environment is not None and any("\x00" in name or "\x00" in value for name, value in environment.items()):
            raise ValueError("explicit safe permission mode and safe arguments are required")
        self.capabilities = ProviderCapabilities(provider, dimensions)
        self._executable, self._arguments, self._active, self._completed = executable, arguments, {}, set()
        self.outputs: dict[str, tuple[str, str]] = {}
        # Per invocation, the bounded diagnostics of its last process (the worker journals them with its outcome).
        self.diagnostics: dict[str, dict[str, object]] = {}
        self._environment = None if environment is None else dict(environment)
        self._ownership = ProcOwnership() if ownership is None else ownership
        if worker_user is not None and (environment is None or results is None or regression_base is None):
            raise ValueError("a worker user needs an environment, a results folder and a regression base")
        if worker_user is not None:
            worker_prefix(worker_user, environment)  # refuses an unsafe user or environment now, not at run
        self._worker_user, self._results, self._regression_base = worker_user, results, regression_base
        self._work_identity = work_identity
        self._runs_feature_regressions = feature_regressions
        # This supervisor's owner marker: the owning process and this instance.
        owner = self._ownership.current()
        self._owner = None if owner is None else f"{owner_token(owner)}/{uuid.uuid4().hex}"
        # Only a stated environment carries the markers to the worker, so only
        # then can work that outlives this process be observed and attested.
        self.marks_owned_work = self._environment is not None and self._owner is not None

    def _child_environment(self, invocation_id: str, role: InvocationRole) -> Mapping[str, str] | None:
        """The exact environment the worker runs in, or the inherited one.

        One argument vector serves every invocation, so a worker that must act
        on a named work item can only learn which one it is from here. When an
        environment is configured it *replaces* the inherited one rather than
        extending it, so a credential the control plane holds for its own
        publication is not handed to the worker process as well.
        """
        if self._environment is None:
            return None
        owner = {} if self._owner is None else {INVOCATION_OWNER_MARKER: self._owner}
        identity = {} if self._worker_user is None else {"ALIENINTENT_CORRELATION": invocation_id} | (
            {} if self._work_identity is None or not self._work_identity(invocation_id)
            else {"ALIENINTENT_WORK_IDENTITY": str(self._work_identity(invocation_id))})
        return self._environment | {INVOCATION_MARKER: invocation_id, "ALIENINTENT_ROLE": str(role)} | identity | owner

    def _feature_regressions(self, workspace: Path, wall_clock_seconds: float) -> ProcessResult:
        runner = workspace / "tools/verification/run_feature_regressions.py"
        manifest = workspace / "tools/verification/feature_regressions.json"
        if not runner.is_file() or not manifest.is_file():
            return ProcessResult("failure", 2, True, BudgetRecord.unknown())
        base = subprocess.run(["git", "merge-base", "HEAD", "origin/main"], cwd=workspace,
                              capture_output=True, text=True, check=False)
        if base.returncode != 0 or not base.stdout.strip():
            return ProcessResult("failure", base.returncode, True, BudgetRecord.unknown())
        receipt = workspace / FEATURE_REGRESSION_RECEIPT_PATH
        return self._regressions([sys.executable, str(runner), "--base", base.stdout.strip(), "--candidate", "HEAD",
                                  "--receipt", str(receipt)], workspace, wall_clock_seconds)

    def _worker_feature_regressions(self, invocation_id: str, workspace: Path,
                                    wall_clock_seconds: float) -> ProcessResult:
        """With a worker user: the runner as the worker through the sudo rule. The control plane neither inspects
        nor runs git in the worker's clone: the runner itself fails when it is missing, and `--base` is the control
        plane's own fact, the release record's starting revision (a full SHA)."""
        base = self._regression_base(invocation_id)
        if not isinstance(base, str) or not _FULL_SHA.fullmatch(base):
            return ProcessResult("failure", 2, True, BudgetRecord.unknown())
        runner = workspace / "tools/verification/run_feature_regressions.py"
        receipt = self._results / invocation_id / Path(FEATURE_REGRESSION_RECEIPT_PATH).name
        return self._regressions([*worker_prefix(self._worker_user, self._environment), sys.executable, str(runner),
                                  "--base", base, "--candidate", "HEAD", "--receipt", str(receipt)], workspace,
                                 wall_clock_seconds)

    def _regressions(self, argv: list[str], workspace: Path, wall_clock_seconds: float) -> ProcessResult:
        # The runner and every pack it starts form one process group, stopped
        # together at the wall clock; quiescence is observed, not assumed.
        done = subprocess.Popen(argv, cwd=workspace, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                start_new_session=True)
        try:
            done.communicate(timeout=wall_clock_seconds)
        except subprocess.TimeoutExpired:
            for signum in (signal.SIGTERM, signal.SIGKILL):
                if self._worker_user is not None:
                    kill_as_worker(self._worker_user, signum, f"-{done.pid}")
                try:
                    os.killpg(done.pid, signum)
                except PermissionError:
                    if self._worker_user is None:
                        raise
                except ProcessLookupError:
                    break
                try:
                    done.communicate(timeout=1)
                except subprocess.TimeoutExpired:
                    continue
            try:
                os.killpg(done.pid, 0)
                quiescent = False
            except PermissionError:
                if self._worker_user is None:
                    raise
                quiescent = False  # another user's process is still in the group
            except ProcessLookupError:
                quiescent = True
            return ProcessResult("timeout", None, quiescent, BudgetRecord.unknown())
        return ProcessResult("success" if done.returncode == 0 else "failure",
                             done.returncode, True, BudgetRecord.unknown())

    def _command(self, invocation_id: str, role: InvocationRole, workspace: Path) -> tuple[list[str], str | None]:
        """This invocation's argv and standard input text (None: inherited, the fixed command's behaviour)."""
        if isinstance(self._executable, str):
            return [self._executable, *self._arguments], None
        argv, text = self._executable(invocation_id, role, workspace)
        argv = list(argv)
        if not argv or not all(isinstance(part, str) and part and "\x00" not in part for part in argv) or not isinstance(text, str):
            raise ValueError("the worker command must be non-empty safe arguments and a standard input text")
        return argv, text

    def run(self, invocation_id: str, role: InvocationRole, workspace: Path, wall_clock_seconds: float) -> ProcessResult:
        """Run one worker process; the invocation ends only when everything it owns has ended.

        The client is started as the leader of its own process group. A
        provider/client exit is not the end of the invocation while owned work
        is still active: work still in the client's process group, or any live
        process carrying this invocation's marker (a descendant that detached
        into its own session or redirected its output away). Owned work that
        outlives the wall clock is stopped with the client. The invocation is
        recorded as finished only once no owned work is observed.
        """
        require_eligible(self.capabilities, frozenset({"wall-clock", "cancellation"}))
        if role is InvocationRole.VERIFIER and self._runs_feature_regressions:
            regression = self._feature_regressions(workspace, wall_clock_seconds) if self._worker_user is None \
                else self._worker_feature_regressions(invocation_id, workspace, wall_clock_seconds)
            if regression.kind != "success":
                self._completed.add(invocation_id)
                self.diagnostics[invocation_id] = process_diagnostics(self.capabilities.provider, ["feature-regressions"],
                                                                      regression.kind, regression.exit_status, "", "")
                return regression
        argv, text = self._command(invocation_id, role, workspace)
        command = list(argv)  # the provider command alone, before any worker-user prefix and its environment
        environment = self._child_environment(invocation_id, role)
        if self._worker_user is not None:
            # The sudo rule replaces the environment: `env -i` and the allowlisted variables only.
            argv, environment = [*worker_prefix(self._worker_user, environment), *argv], None
        deadline = time.monotonic() + wall_clock_seconds
        stdin = None if text is None else subprocess.PIPE
        process = subprocess.Popen(argv, cwd=workspace, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=environment, start_new_session=True)
        self._active[invocation_id] = process
        stdout = stderr = ""
        result: ProcessResult | None = None
        try:
            try:
                stdout, stderr = process.communicate(input=text, timeout=wall_clock_seconds)
                # Diagnostics only (the end of each stream), for a person reading why a worker failed.
                self.outputs[invocation_id] = (stdout[-OUTPUT_TAIL:], stderr[-OUTPUT_TAIL:])
            except subprocess.TimeoutExpired as expired:
                stdout, stderr = _decoded(expired.stdout), _decoded(expired.stderr)  # what it wrote before the deadline
                result = ProcessResult("timeout", self._stop(invocation_id, process), not self._owned(invocation_id, process), BudgetRecord.unknown())
                return result
            if not self._await_owned(invocation_id, process, deadline):
                self._stop(invocation_id, process)
                result = ProcessResult("timeout", process.returncode, not self._owned(invocation_id, process), BudgetRecord.unknown())
                return result
            result = ProcessResult("success" if process.returncode == 0 else "failure", process.returncode, True, BudgetRecord.unknown())
            return result
        except BaseException:
            # An unexpected failure must not leave owned work running unobserved.
            self._stop(invocation_id, process)
            raise
        finally:
            self._active.pop(invocation_id, None)
            if result is not None:
                self.diagnostics[invocation_id] = process_diagnostics(self.capabilities.provider, command, result.kind,
                                                                      result.exit_status, stdout, stderr)
            # Finished only when nothing it owns is still observed; otherwise
            # a later cancel answers unresolved rather than already-finished.
            if not self._owned(invocation_id, process):
                self._completed.add(invocation_id)

    def _owned(self, invocation_id: str, process: subprocess.Popen) -> bool:
        """Whether any work this invocation owns is still alive."""
        if process.poll() is None:
            return True
        try:
            os.killpg(process.pid, 0)
            return True
        except ProcessLookupError:
            pass
        except PermissionError:
            return True
        if self._worker_user is not None:
            # By the worker's real uid and the launched session; an unreadable worker process (None) is alive.
            work = self._ownership.owned_work(invocation_id, self._owner, session=process.pid)
            return work is None or bool(work)
        return bool(self._ownership.owned_work(invocation_id, self._owner)) if self.marks_owned_work else False

    def _await_owned(self, invocation_id: str, process: subprocess.Popen, deadline: float) -> bool:
        while self._owned(invocation_id, process):
            if time.monotonic() >= deadline:
                return False
            time.sleep(OWNED_WORK_POLL_SECONDS)
        return True

    def _signal(self, invocation_id: str, process: subprocess.Popen, signum: int) -> None:
        if self._worker_user is not None:
            # The session's group and each owned pid, as the worker; None (unreadable) is alive, so the group is
            # always signalled and nothing is concluded from it.
            kill_as_worker(self._worker_user, signum, f"-{process.pid}")
            for pid in self._ownership.owned_work(invocation_id, self._owner, session=process.pid) or ():
                kill_as_worker(self._worker_user, signum, str(pid))
            return
        try:
            os.killpg(process.pid, signum)
        except (ProcessLookupError, PermissionError):
            pass
        for pid in (self._ownership.owned_work(invocation_id, self._owner) if self.marks_owned_work else None) or ():
            try:
                os.kill(pid, signum)
            except (ProcessLookupError, PermissionError):
                pass

    def _stop(self, invocation_id: str, process: subprocess.Popen, *, drain: bool = True) -> int | None:
        """Stop the client and all owned work; return the client's exit status.

        The running call drains the client's output while it stops; a
        concurrent cancel only waits, leaving the draining to that call.
        """
        for signum in (signal.SIGTERM, signal.SIGKILL):
            self._signal(invocation_id, process, signum)
            try:
                if drain:
                    process.communicate(timeout=1)
                else:
                    process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                continue
            settle = time.monotonic() + 1
            while self._owned(invocation_id, process) and time.monotonic() < settle:
                time.sleep(OWNED_WORK_POLL_SECONDS)
            if not self._owned(invocation_id, process):
                break
        return process.returncode

    def cancel(self, invocation_id: str, reason: str) -> ProcessResult:
        process = self._active.get(invocation_id)
        if process is None:
            if invocation_id in self._completed:
                return ProcessResult("already-finished", None, True, BudgetRecord.unknown())
            return ProcessResult("unresolved-recovery", None, False, BudgetRecord.unknown())
        self._stop(invocation_id, process, drain=False)
        quiescent = not self._owned(invocation_id, process)
        self._active.pop(invocation_id, None)
        if quiescent:
            self._completed.add(invocation_id)
        return ProcessResult("cancelled", process.returncode, quiescent, BudgetRecord.unknown())
