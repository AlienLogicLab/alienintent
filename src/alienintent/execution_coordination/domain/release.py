"""Pure release and admission guards for immutable BIU contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from .contract import BiuContract


class ReleaseConflict(ValueError):
    """A release identity was replayed with a materially different payload."""


class ReleaseSource(StrEnum):
    AUTOMATIC_POLICY = "automatic-policy"
    EXPLICIT_HUMAN = "explicit-human"


AUTOMATIC_ON = "automatic-on"
EXPLICIT_HUMAN_OFF = "explicit-human-off"


@dataclass(frozen=True)
class ReleaseRequest:
    identity: str
    contract: BiuContract
    readiness_digest: str
    satisfied_dependencies: frozenset[str]
    available_capabilities: frozenset[str]
    available_budget: Mapping[str, int] | tuple[tuple[str, int], ...]
    authorization_provenance: str
    source: ReleaseSource = ReleaseSource.EXPLICIT_HUMAN

    def __post_init__(self) -> None:
        if not self.identity or not self.authorization_provenance:
            raise ValueError("release identity and authorization provenance are required")
        object.__setattr__(self, "available_budget", tuple(sorted(dict(self.available_budget).items())))

    @property
    def fingerprint(self) -> tuple[object, ...]:
        return (self.contract.content_digest, self.readiness_digest, self.satisfied_dependencies,
                self.available_capabilities, self.available_budget, self.authorization_provenance, self.source)


@dataclass(frozen=True)
class ReleaseAdmission:
    identity: str
    releases: Mapping[str, ReleaseRequest]

    def __post_init__(self) -> None:
        object.__setattr__(self, "releases", MappingProxyType(dict(self.releases)))


def admit_release(existing: Mapping[str, ReleaseRequest], request: ReleaseRequest) -> ReleaseAdmission:
    previous = existing.get(request.identity)
    if previous:
        if previous.fingerprint != request.fingerprint:
            raise ReleaseConflict("release identity has a conflicting payload")
        return ReleaseAdmission(request.identity, existing)
    if request.contract.release_policy == AUTOMATIC_ON and request.source is not ReleaseSource.AUTOMATIC_POLICY:
        raise ValueError("automatic-on release requires attributable policy authorization")
    if request.contract.release_policy == EXPLICIT_HUMAN_OFF and request.source is not ReleaseSource.EXPLICIT_HUMAN:
        raise ValueError("explicit-human-off release requires a human authorization")
    if request.contract.release_policy not in {AUTOMATIC_ON, EXPLICIT_HUMAN_OFF}:
        raise ValueError("unknown release policy")
    if request.readiness_digest != request.contract.content_digest:
        raise ValueError("stale readiness reference")
    missing_dependencies = set(request.contract.dependencies) - request.satisfied_dependencies
    if missing_dependencies:
        raise ValueError("unsatisfied dependency")
    if not set(request.contract.required_capabilities).issubset(request.available_capabilities):
        raise ValueError("missing required capability")
    budget = dict(request.available_budget)
    if any(dimension not in budget or budget[dimension] < 1 for dimension in request.contract.budget_policy.required_dimensions):
        raise ValueError("absent hard-required budget dimension")
    return ReleaseAdmission(request.identity, {**existing, request.identity: request})
