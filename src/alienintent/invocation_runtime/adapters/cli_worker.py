"""Safe explicit-mode CLI worker adapter with timeout and cancellation evidence."""

from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Final, Mapping
import uuid

from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
from alienintent.invocation_runtime.domain.runtime import BudgetRecord, FEATURE_REGRESSION_RECEIPT_PATH, INVOCATION_MARKER, INVOCATION_OWNER_MARKER, InvocationRole, ProcessResult, ProviderCapabilities, owner_token, require_eligible
from alienintent.invocation_runtime.ports.process_ownership import ProcessOwnership
from alienintent.invocation_runtime.ports.worker_process import WorkerProcess

# How often owned work is re-observed while the invocation waits for it.
OWNED_WORK_POLL_SECONDS = 0.05


class CliWorkerProvider(WorkerProcess):
    _SAFE_MODES: Final = frozenset({"explicit", "read-only", "workspace-write", "danger-full-access", "manual", "bypassPermissions"})

    def __init__(self, provider: str, executable: str, arguments: tuple[str, ...], permission_mode: str, dimensions: frozenset[str], environment: Mapping[str, str] | None = None, *, ownership: ProcessOwnership | None = None) -> None:
        if permission_mode not in self._SAFE_MODES or not executable or any("\x00" in part for part in (executable, *arguments)):
            raise ValueError("explicit safe permission mode and safe arguments are required")
        if environment is not None and any("\x00" in name or "\x00" in value for name, value in environment.items()):
            raise ValueError("explicit safe permission mode and safe arguments are required")
        self.capabilities = ProviderCapabilities(provider, dimensions)
        self._executable, self._arguments, self._active, self._completed = executable, arguments, {}, set()
        self._environment = None if environment is None else dict(environment)
        self._ownership = ProcOwnership() if ownership is None else ownership
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
        return self._environment | {INVOCATION_MARKER: invocation_id, "ALIENINTENT_ROLE": str(role)} | owner

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
        # The runner and every pack it starts form one process group, stopped
        # together at the wall clock; quiescence is observed, not assumed.
        done = subprocess.Popen(
            [sys.executable, str(runner), "--base", base.stdout.strip(), "--candidate", "HEAD",
             "--receipt", str(receipt)],
            cwd=workspace, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True,
        )
        try:
            done.communicate(timeout=wall_clock_seconds)
        except subprocess.TimeoutExpired:
            for signum in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.killpg(done.pid, signum)
                except ProcessLookupError:
                    break
                try:
                    done.communicate(timeout=1)
                except subprocess.TimeoutExpired:
                    continue
            try:
                os.killpg(done.pid, 0)
                quiescent = False
            except ProcessLookupError:
                quiescent = True
            return ProcessResult("timeout", None, quiescent, BudgetRecord.unknown())
        return ProcessResult("success" if done.returncode == 0 else "failure",
                             done.returncode, True, BudgetRecord.unknown())

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
        if role is InvocationRole.VERIFIER:
            regression = self._feature_regressions(workspace, wall_clock_seconds)
            if regression.kind != "success":
                self._completed.add(invocation_id)
                return regression
        deadline = time.monotonic() + wall_clock_seconds
        process = subprocess.Popen([self._executable, *self._arguments], cwd=workspace, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=self._child_environment(invocation_id, role), start_new_session=True)
        self._active[invocation_id] = process
        try:
            try:
                process.communicate(timeout=wall_clock_seconds)
            except subprocess.TimeoutExpired:
                return ProcessResult("timeout", self._stop(invocation_id, process), not self._owned(invocation_id, process), BudgetRecord.unknown())
            if not self._await_owned(invocation_id, process, deadline):
                self._stop(invocation_id, process)
                return ProcessResult("timeout", process.returncode, not self._owned(invocation_id, process), BudgetRecord.unknown())
            return ProcessResult("success" if process.returncode == 0 else "failure", process.returncode, True, BudgetRecord.unknown())
        except BaseException:
            # An unexpected failure must not leave owned work running unobserved.
            self._stop(invocation_id, process)
            raise
        finally:
            self._active.pop(invocation_id, None)
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
        return bool(self._ownership.owned_work(invocation_id, self._owner)) if self.marks_owned_work else False

    def _await_owned(self, invocation_id: str, process: subprocess.Popen, deadline: float) -> bool:
        while self._owned(invocation_id, process):
            if time.monotonic() >= deadline:
                return False
            time.sleep(OWNED_WORK_POLL_SECONDS)
        return True

    def _signal(self, invocation_id: str, process: subprocess.Popen, signum: int) -> None:
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
