"""Provider-neutral import and projection boundary for ready work."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from alienintent.execution_coordination.domain.contract import BiuContract


@dataclass(frozen=True)
class ReadyWorkItem:
    identity: str
    fifo: int
    repository: str
    profile: str
    priority: int | None
    dependencies: tuple[str, ...]
    contract: BiuContract
    readiness_digest: str
    readiness_evidence: str
    automatic_release: bool = True


class WorkManagement(Protocol):
    def import_ready_snapshot(self) -> tuple[ReadyWorkItem, ...]: ...
    def propose_release(self, item: ReadyWorkItem) -> None: ...
    def project_execution_state(self, identity: str, state: str) -> None: ...

