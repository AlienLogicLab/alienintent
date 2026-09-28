"""Pure release and admission guards for immutable BIU contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re
from types import MappingProxyType
from typing import Iterable, Mapping

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


# --- SWF-21 release preconditions (SF-REQ-002 amendment 2026-09-21) ----------
#
# The record-completeness gate in front of ``admit_release``: before any worker
# is launched, a durable record must explicitly authorize IMPLEMENT, name an
# exact baseline that resolves and is reachable from the intended release point,
# and no unsuperseded non-authorization wording may coexist with it. A failed
# check is a refusal to transition, not a warning.

UNAUTHORIZED_WORDING = re.compile(
    r"\bimplement(?:ation)?\b(?:\s+is)?\s+\*{0,2}(?:(?:not|never)\*{0,2}(?:\s+(?:yet|currently))?\s+authori[sz]ed|unauthori[sz]ed)"
    r"|\brelease\s+(?:is\s+)?\*{0,2}(?:refused|denied)\b",
    re.I,
)
EXACT_REVISION = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
NULL_REVISION = re.compile(r"0+")


class ReleasePreconditionRefused(ValueError):
    """A SWF-21 release precondition failed; ``check`` names which one."""

    def __init__(self, check: str, reason: str) -> None:
        super().__init__(f"{check}: {reason}")
        self.check = check


@dataclass(frozen=True)
class ReleaseAuthorization:
    """A durable release record for one BIU, as read back from its record source.

    ``superseding_record`` is the reference of an explicit record, distinct
    from this one, that supersedes earlier non-authorization wording; without
    it such wording refuses the release.
    """

    identity: str
    record_ref: str
    authorizes_implement: bool
    baseline: str | None
    text: str = ""
    superseding_record: str | None = None


@dataclass(frozen=True)
class BaselineEvidence:
    """Repository facts for a named baseline, observed through a revision port."""

    release_point: str
    resolves: bool
    reachable: bool


def is_exact_revision(revision: str | None) -> bool:
    return bool(revision) and EXACT_REVISION.fullmatch(revision) is not None


def admit_release_preconditions(identity: str, authorization: ReleaseAuthorization | None,
                                baseline: BaselineEvidence | None, wording: Iterable[str]) -> None:
    """Refuse unless all five SWF-21 record preconditions hold (the sixth is the caller's launch order)."""
    if authorization is None or not authorization.record_ref:
        raise ReleasePreconditionRefused("implementation-authorized", "no durable release record exists for this BIU")
    if authorization.identity != identity:
        raise ReleasePreconditionRefused("implementation-authorized", "the release record names a different BIU")
    if not authorization.authorizes_implement:
        raise ReleasePreconditionRefused("implementation-authorized", "the release record does not explicitly authorize IMPLEMENT")
    if not is_exact_revision(authorization.baseline):
        raise ReleasePreconditionRefused("baseline-named", "the release record does not name an exact baseline revision")
    if baseline is None or NULL_REVISION.fullmatch(str(authorization.baseline)) or not baseline.resolves:
        raise ReleasePreconditionRefused("baseline-resolves", "the baseline does not resolve to a real repository revision")
    if not baseline.reachable:
        raise ReleasePreconditionRefused("baseline-reachable", f"the baseline is not reachable from release point {baseline.release_point}")
    if UNAUTHORIZED_WORDING.search(authorization.text):
        raise ReleasePreconditionRefused("authority-wording-consistent", "the release record itself states implementation is not authorized")
    superseded = bool(authorization.superseding_record) and authorization.superseding_record != authorization.record_ref
    if not superseded and any(UNAUTHORIZED_WORDING.search(text) for text in wording):
        raise ReleasePreconditionRefused("authority-wording-consistent",
                                         "non-authorization wording coexists with the release without an explicit superseding record")
