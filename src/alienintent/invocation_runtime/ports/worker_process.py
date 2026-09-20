"""Process-worker boundary with explicit lifecycle observation."""

from pathlib import Path
from typing import Protocol

from alienintent.invocation_runtime.domain.runtime import InvocationRole, ProcessResult


class WorkerProcess(Protocol):
    def run(self, invocation_id: str, role: InvocationRole, workspace: Path, wall_clock_seconds: float) -> ProcessResult: ...
    def cancel(self, invocation_id: str, reason: str) -> ProcessResult: ...
