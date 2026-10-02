"""Canonical prelaunch release gate and attributable execution allocation (WO-220611, B3P)."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping

from alienintent.execution_coordination.domain.contract import BiuContract
from alienintent.execution_coordination.domain.release import (
    BaselineEvidence, admit_release_preconditions, is_exact_revision, release_wording)
from alienintent.execution_coordination.ports.release_admission import ReleaseAuthorizationRecords, RevisionResolver
from alienintent.execution_coordination.ports.work_management import ReadyWorkItem


class ReleasePreconditionGate:
    """SWF-21 preconditions 1-5 for one ready item; the coordinator launches nothing until this passes."""

    def __init__(self, records: ReleaseAuthorizationRecords, revisions: RevisionResolver, release_point: str) -> None:
        if not release_point:
            raise ValueError("an intended release point is required")
        self._records, self._revisions, self._release_point = records, revisions, release_point

    def check(self, item: ReadyWorkItem) -> None:
        authorization = self._records.release_authorization(item.identity)
        evidence = None
        if authorization is not None and is_exact_revision(authorization.baseline):
            baseline = str(authorization.baseline)
            resolves = self._revisions.resolves(item.repository, baseline)
            reachable = resolves and self._revisions.is_reachable(item.repository, baseline, self._release_point)
            evidence = BaselineEvidence(self._release_point, resolves, reachable)
        admit_release_preconditions(item.identity, authorization, evidence, _wording(item))


def _wording(item: ReadyWorkItem) -> Iterable[str]:
    """Every human-readable text the release request carries (the wording `work authorize` checks too)."""
    return release_wording(item.contract, item.readiness_evidence, item.metadata or {})


@dataclass(frozen=True)
class BiuLimitAllocation:
    """Configured per-BIU limits (the Python analogue of the Node runtime's ``execution.biuLimits``).

    A BIU with no configured limits has no allocation; each dimension's
    remaining allocation is its configured limit less durable consumption.
    """

    limits: Mapping[str, Mapping[str, int]]

    def __post_init__(self) -> None:
        frozen: dict[str, Mapping[str, int]] = {}
        for identity, dimensions in self.limits.items():
            if not identity:
                raise ValueError("allocation identity is required")
            for dimension, limit in dimensions.items():
                if not dimension or not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
                    raise ValueError(f"invalid allocation for {identity}: {dimension}={limit!r}")
            frozen[identity] = MappingProxyType(dict(dimensions))
        object.__setattr__(self, "limits", MappingProxyType(frozen))

    def available_budget(self, identity: str, contract: BiuContract, consumed: Mapping[str, int]) -> Mapping[str, int]:
        return {dimension: max(limit - consumed.get(dimension, 0), 0) for dimension, limit in self.limits.get(identity, {}).items()}
