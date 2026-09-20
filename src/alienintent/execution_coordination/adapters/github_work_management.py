"""Fixture-driven GitHub Projects anti-corruption adapter; no live client is required."""

from __future__ import annotations

from collections.abc import Callable
from typing import Mapping

from alienintent.execution_coordination.domain.contract import BiuContract
from alienintent.execution_coordination.ports.work_management import ProjectionReceipt, ReadyWorkItem, WorkManagement, WorkRejected, WorkUnavailable


class GitHubProjectsWorkManagement(WorkManagement):
    """Translate complete recorded provider pages into neutral imported work."""

    def __init__(self, profile: str, repository: str, status_mapping: Mapping[str, str], projection_fields: Mapping[str, str], snapshot: Callable[[], tuple[Mapping[str, object], ...]], contract: BiuContract, projection_write: Callable[[str, str, str, int], int] | None = None) -> None:
        if not status_mapping or len(set(status_mapping.values())) != len(status_mapping):
            raise WorkRejected("ambiguous status mapping")
        self._profile, self._repository = profile, repository
        self._status_mapping, self._projection_fields, self._snapshot, self._contract, self._projection_write = dict(status_mapping), dict(projection_fields), snapshot, contract, projection_write
        self._projected_revisions: dict[str, int] = {}

    def import_ready_snapshot(self) -> tuple[ReadyWorkItem, ...]:
        try:
            rows = self._snapshot()
        except Exception as error:
            raise WorkUnavailable("upstream snapshot unavailable") from error
        imported = tuple(self._translate(row, position) for position, row in enumerate(rows))
        return tuple(item for item in imported if item.metadata and item.metadata["upstream_status"] == "READY")

    def _translate(self, row: Mapping[str, object], fifo: int) -> ReadyWorkItem:
        if not row.get("complete") or not row.get("membership") or row.get("repository") != self._repository:
            raise WorkRejected("incomplete page or missing Project membership")
        status = row.get("status")
        if not isinstance(status, str) or status not in self._status_mapping:
            raise WorkRejected("unmapped upstream status")
        identity, digest, readiness = row.get("identity"), row.get("contract_digest"), row.get("readiness")
        if not all(isinstance(value, str) and value for value in (identity, digest, readiness)):
            raise WorkRejected("incomplete imported identity or readiness evidence")
        priority = row.get("priority")
        if priority is not None:
            if not isinstance(priority, str) or priority not in {"P0", "P1", "P2", "P3", "P4", "P5"}:
                raise WorkRejected("unsupported priority")
            priority_value: int | None = int(priority[1:])
        else:
            priority_value = None
        dependencies = row.get("dependencies", ())
        if not isinstance(dependencies, list) or any(not isinstance(dep, str) or not dep for dep in dependencies):
            raise WorkRejected("unsupported dependency evidence")
        metadata = {"wave": str(row.get("wave", "")), "upstream_status": self._status_mapping[status], "source_version": str(row.get("source_version", "")), "contract_location": str(row.get("contract", ""))}
        return ReadyWorkItem(identity, fifo, self._repository, self._profile, priority_value, tuple(dependencies), self._contract, digest, readiness, metadata=metadata)

    def propose_release(self, item: ReadyWorkItem) -> None:
        # Release is a neutral proposal consumed by the application boundary, never a provider write.
        if item.profile != self._profile:
            raise WorkRejected("profile mismatch")

    def project_execution_state(self, identity: str, state: str, revision: int = 0) -> ProjectionReceipt:
        previous = self._projected_revisions.get(identity, -1)
        if revision < previous:
            return ProjectionReceipt(identity, revision, False, "stale projection fenced")
        field = self._projection_fields.get(state)
        if field is None:
            return ProjectionReceipt(identity, revision, False, "unconfirmed unsupported projection")
        if self._projection_write is None:
            return ProjectionReceipt(identity, revision, False, "projection provider unavailable")
        try:
            observed_revision = self._projection_write(identity, field, state, revision)
        except Exception:
            return ProjectionReceipt(identity, revision, False, "projection provider unavailable")
        if observed_revision != revision:
            return ProjectionReceipt(identity, revision, False, "projection read-back mismatch")
        self._projected_revisions[identity] = revision
        return ProjectionReceipt(identity, revision, True, "confirmed")
