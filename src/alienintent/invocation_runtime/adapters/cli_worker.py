"""Safe explicit-mode CLI worker adapter with timeout and cancellation evidence."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Final

from alienintent.invocation_runtime.domain.runtime import BudgetRecord, InvocationRole, ProcessResult, ProviderCapabilities, require_eligible
from alienintent.invocation_runtime.ports.worker_process import WorkerProcess


class CliWorkerProvider(WorkerProcess):
    _SAFE_MODES: Final = frozenset({"explicit", "read-only", "workspace-write", "danger-full-access", "manual", "bypassPermissions"})

    def __init__(self, provider: str, executable: str, arguments: tuple[str, ...], permission_mode: str, dimensions: frozenset[str]) -> None:
        if permission_mode not in self._SAFE_MODES or not executable or any("\x00" in part for part in (executable, *arguments)):
            raise ValueError("explicit safe permission mode and safe arguments are required")
        self.capabilities = ProviderCapabilities(provider, dimensions)
        self._executable, self._arguments, self._active, self._completed = executable, arguments, {}, set()

    def run(self, invocation_id: str, role: InvocationRole, workspace: Path, wall_clock_seconds: float) -> ProcessResult:
        require_eligible(self.capabilities, frozenset({"wall-clock", "cancellation"}))
        process = subprocess.Popen([self._executable, *self._arguments], cwd=workspace, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self._active[invocation_id] = process
        try:
            process.communicate(timeout=wall_clock_seconds)
            return ProcessResult("success" if process.returncode == 0 else "failure", process.returncode, True, BudgetRecord.unknown())
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.communicate(timeout=1)
                return ProcessResult("timeout", process.returncode, True, BudgetRecord.unknown())
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                return ProcessResult("timeout", process.returncode, True, BudgetRecord.unknown())
        finally:
            self._active.pop(invocation_id, None)
            self._completed.add(invocation_id)

    def cancel(self, invocation_id: str, reason: str) -> ProcessResult:
        process = self._active.get(invocation_id)
        if process is None:
            if invocation_id in self._completed:
                return ProcessResult("already-finished", None, True, BudgetRecord.unknown())
            return ProcessResult("unresolved-recovery", None, False, BudgetRecord.unknown())
        process.terminate()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        self._active.pop(invocation_id, None)
        self._completed.add(invocation_id)
        return ProcessResult("cancelled", process.returncode, True, BudgetRecord.unknown())
