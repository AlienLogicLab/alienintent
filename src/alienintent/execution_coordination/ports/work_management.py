"""Provider-neutral import and projection boundary for ready work."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from alienintent.execution_coordination.domain.contract import BiuContract


class WorkRejected(ValueError):
    """The provider evidence cannot safely become a noncanonical READY view."""


class WorkUnavailable(RuntimeError):
    """The provider cannot safely complete an import or projection."""


@dataclass(frozen=True)
class ProjectionReceipt:
    identity: str
    revision: int
    confirmed: bool
    detail: str


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
    metadata: dict[str, str] | None = None


class WorkManagement(Protocol):
    def import_ready_snapshot(self) -> tuple[ReadyWorkItem, ...]: ...
    def propose_release(self, item: ReadyWorkItem) -> None: ...
    def project_execution_state(self, identity: str, state: str, revision: int = 0) -> ProjectionReceipt: ...
