"""Prelaunch release-admission inputs: durable release records, revisions and budget allocation."""

from __future__ import annotations

from typing import Mapping, Protocol

from alienintent.execution_coordination.domain.contract import BiuContract
from alienintent.execution_coordination.domain.release import ReleaseAuthorization


class ReleaseAuthorizationRecords(Protocol):
    def release_authorization(self, identity: str) -> ReleaseAuthorization | None: ...


class RevisionResolver(Protocol):
    def resolves(self, repository: str, revision: str) -> bool: ...
    def is_reachable(self, repository: str, revision: str, release_point: str) -> bool: ...


class ExecutionAllocation(Protocol):
    """The attributable per-BIU budget: remaining allocation for each dimension.

    ``consumed`` is what this profile has durably recorded against the BIU.
    A dimension absent from the answer, or at zero, is exhausted.
    """

    def available_budget(self, identity: str, contract: BiuContract, consumed: Mapping[str, int]) -> Mapping[str, int]: ...
