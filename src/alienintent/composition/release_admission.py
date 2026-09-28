"""Composition of the canonical SWF-21 release gate and attributable budget (WO-220611, B3P).

Every operational profile (``SandboxRunProfile``, ``GitHubProfileComposition``)
builds its ``FactoryCoordinator`` through ``compose_release_admission``, so the
gate and the per-BIU allocation are not optional there: a profile that records
no release authorization, names no reachable baseline, or configures no
allocation for a required budget dimension refuses release with zero launches.

Configuration is the profile's own ``release_admission`` section::

    {"release_point": "origin/main",
     "biu_limits": {"<BIU identity>": {"attempts": 3}}}

``release_point`` defaults to the configured checkout's ``HEAD``; absent
``biu_limits`` means no BIU has an allocation. Release records are durable
aggregates in the profile's own operational store (``release_records``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from alienintent.execution_coordination.adapters.release_admission import GitRevisionResolver, StoredReleaseAuthorizations
from alienintent.execution_coordination.application.release_admission import BiuLimitAllocation, ReleasePreconditionGate
from alienintent.execution_coordination.ports.operational_store import OperationalStore

DEFAULT_RELEASE_POINT = "HEAD"


class ReleaseAdmissionRejected(ValueError):
    """A profile's release-admission configuration is malformed."""


@dataclass(frozen=True)
class ReleaseAdmissionConfig:
    release_point: str = DEFAULT_RELEASE_POINT
    biu_limits: Mapping[str, Mapping[str, int]] = field(default_factory=dict)


def release_admission_config(document: Mapping[str, object]) -> ReleaseAdmissionConfig:
    """Read the ``release_admission`` section of a profile document; absent means the fail-closed default."""
    section = document.get("release_admission")
    if section is None:
        return ReleaseAdmissionConfig()
    if not isinstance(section, Mapping) or set(section) - {"release_point", "biu_limits"}:
        raise ReleaseAdmissionRejected("release_admission must be a mapping of release_point and biu_limits")
    release_point = section.get("release_point", DEFAULT_RELEASE_POINT)
    limits = section.get("biu_limits", {})
    if not isinstance(release_point, str) or not release_point or not isinstance(limits, Mapping):
        raise ReleaseAdmissionRejected("release_admission.release_point must be a revision and biu_limits a mapping")
    if any(not isinstance(dimensions, Mapping) for dimensions in limits.values()):
        raise ReleaseAdmissionRejected("release_admission.biu_limits maps each BIU to its dimension limits")
    return ReleaseAdmissionConfig(release_point, {str(identity): dict(dimensions) for identity, dimensions in limits.items()})


@dataclass(frozen=True)
class ReleaseAdmission:
    """The coordinator's release inputs for one profile, and the record source they read."""

    gate: ReleasePreconditionGate
    allocation: BiuLimitAllocation
    records: StoredReleaseAuthorizations


def compose_release_admission(store: OperationalStore, profile: str, repository: str, checkout: Path | None,
                              config: ReleaseAdmissionConfig) -> ReleaseAdmission:
    """Bind the gate to the profile's store and checkout; no checkout means no baseline resolves."""
    records = StoredReleaseAuthorizations(store, profile)
    revisions = GitRevisionResolver({} if checkout is None else {repository: checkout})
    try:
        allocation = BiuLimitAllocation(config.biu_limits)
    except ValueError as error:
        raise ReleaseAdmissionRejected(str(error)) from error
    return ReleaseAdmission(ReleasePreconditionGate(records, revisions, config.release_point), allocation, records)
