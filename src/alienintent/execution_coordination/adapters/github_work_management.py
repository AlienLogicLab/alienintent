"""Fixture-driven GitHub Projects anti-corruption adapter; no live client is required."""

from __future__ import annotations

from collections.abc import Callable
from typing import Mapping

from alienintent.execution_coordination.domain.contract import BiuContract
from alienintent.execution_coordination.domain.escalation import HumanDecisionRequired
from alienintent.execution_coordination.ports.project_directory import ProjectDirectory, ProjectSchema
from alienintent.execution_coordination.ports.work_management import ProjectionReceipt, ReadyWorkItem, WorkManagement, WorkRejected, WorkUnavailable


class GitHubProjectsWorkManagement(WorkManagement):
    """Translate complete recorded provider pages into neutral imported work.

    `contract` is either one shared contract, as a recorded-fixture profile
    supplies, or a resolver called per row. A live backlog carries a distinct
    BIU contract per item, and release admission compares the row's readiness
    digest against that item's own contract digest, so one shared contract
    would refuse every live row.
    """

    def __init__(self, profile: str, repository: str, status_mapping: Mapping[str, str], projection_fields: Mapping[str, str], snapshot: Callable[[], tuple[Mapping[str, object], ...]], contract: BiuContract | Callable[[Mapping[str, object]], BiuContract], projection_write: Callable[[str, str, str, int], int] | None = None, decision_projection_write: Callable[[HumanDecisionRequired], str] | None = None, directory: ProjectDirectory | None = None) -> None:
        if not status_mapping or any(not isinstance(upstream, str) or not upstream or not isinstance(neutral, str) or not neutral for upstream, neutral in status_mapping.items()):
            raise WorkRejected("ambiguous status mapping")
        self._profile, self._repository = profile, repository
        self._status_mapping, self._projection_fields, self._snapshot, self._contract, self._projection_write = dict(status_mapping), dict(projection_fields), snapshot, contract, projection_write
        self._decision_projection_write, self._directory = decision_projection_write, directory
        self._projected_revisions: dict[str, int] = {}

    def resolve_project(self) -> ProjectSchema:
        """Resolve the live Project and its field and option identities.

        The configured lifecycle and projection states must exist as real Status
        options, so a profile mapped against a Project that cannot carry it is
        rejected here rather than discovered by a failed projection write.
        """
        if self._directory is None:
            raise WorkUnavailable("no project directory is bound to this profile")
        schema = self._directory.schema()
        if not schema.status_options or not schema.priority_options:
            raise WorkRejected("Project Status or Priority field carries no option identities")
        absent = sorted((set(self._status_mapping) | set(self._projection_fields)) - set(schema.status_options))
        if absent:
            raise WorkRejected("configured lifecycle states are absent from the Project Status field")
        return schema

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
        return ReadyWorkItem(identity, fifo, self._repository, self._profile, priority_value, tuple(dependencies), self._contract_for(row), digest, readiness, metadata=metadata)

    def _contract_for(self, row: Mapping[str, object]) -> BiuContract:
        """The row's own contract, or the one shared contract a fixture binds."""
        if isinstance(self._contract, BiuContract):
            return self._contract
        resolved = self._contract(row)
        if not isinstance(resolved, BiuContract):
            raise WorkRejected("row contract resolver did not yield a BIU contract")
        return resolved

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

    def project_decision_request(self, escalation: HumanDecisionRequired) -> ProjectionReceipt:
        if self._decision_projection_write is None:
            return ProjectionReceipt(escalation.work_item, escalation.biu_version, False, "decision notification projection unavailable")
        try:
            receipt = self._decision_projection_write(escalation)
        except Exception:
            return ProjectionReceipt(escalation.work_item, escalation.biu_version, False, "decision notification projection unavailable")
        return ProjectionReceipt(escalation.work_item, escalation.biu_version, bool(receipt), "confirmed" if receipt else "decision notification projection unconfirmed")
