"""The work item storage boundary: one project database table and the Git calls that save packet references.

Exactly one adapter implements this port and it is the only code that writes `work_item`. Every method is usable
inside `transaction()` (the outermost one is `BEGIN IMMEDIATE` ... `COMMIT`, or `ROLLBACK` on any exception) or wraps
itself in its own. Tag writes recorded while storing a pointer happen only after the outermost `COMMIT` succeeds.
"""
from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from alienintent.context_assembly.domain.work_identity import MigrationEntry, Pointer, RequestRef, StoredPointer, WorkItem
from alienintent.evidence_learning.domain.refs import Ref


@dataclass(frozen=True)
class RepositoryLocation:
    """One repository of the project configuration: its one configured clone per project, the remote the clone
    publishes to (named explicitly, never inferred), and the branches that retain packet commits."""
    clone: Path
    remote: str
    default_branch: str
    packets_branch: str

    def __post_init__(self) -> None:
        for name in ("remote", "default_branch", "packets_branch"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or value.startswith("-") or any(c in value for c in " *?[:\\~^"):
                raise ValueError(f"repository location {name} is not a plain name: {value!r}")
        if not isinstance(self.clone, Path):
            raise ValueError("repository location clone must be a path")


class WorkItemRepository(Protocol):
    def transaction(self) -> AbstractContextManager[None]: ...

    def in_transaction(self) -> bool: ...

    def register(self, request_ref: RequestRef, label: str, kind: str, parent_id: str | None,
                 pointer: Pointer | None) -> WorkItem: ...

    def import_completed(self, request_ref: RequestRef, label: str, kind: str, pointer: Pointer | None,
                         evidence: dict[str, Ref]) -> WorkItem: ...

    def retire(self, identity: str) -> WorkItem: ...

    def find(self, id_or_label: str) -> WorkItem | None: ...

    def find_request(self, request_ref: str) -> WorkItem | None: ...

    def children(self, identity: str) -> tuple[WorkItem, ...]: ...

    def set_evidence(self, identity: str, which: str, ref: Ref) -> WorkItem: ...

    def set_state(self, identity: str, state: str) -> WorkItem: ...

    def holds(self, pointer: Pointer) -> bool: ...

    def commit_packet(self, repo: str, path: str, data: bytes, existing: StoredPointer | None) -> str: ...

    def set_pointer(self, identity: str, pointer: Pointer) -> WorkItem: ...

    def packets_head(self, repo: str) -> str | None: ...

    def insert_migrated(self, entry: MigrationEntry) -> WorkItem: ...

    def rekey(self, identity: str, request_ref: str) -> WorkItem: ...
