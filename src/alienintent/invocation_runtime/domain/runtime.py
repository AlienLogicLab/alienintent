"""Provider-neutral invocation authority, budgets, and observable outcomes."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum


class InvocationRole(StrEnum):
    PRODUCER = "PRODUCER"
    VERIFIER = "VERIFIER"


class CapabilityDenied(PermissionError):
    pass


class BudgetIneligible(ValueError):
    pass


class CandidateUnavailable(ValueError):
    pass


@dataclass(frozen=True)
class CapabilityGrant:
    identifier: str
    biu_version: str
    invocation_id: str
    role: InvocationRole
    issuer: str
    target: str
    operations: frozenset[str]
    expires_at: int
    revoked_by: str | None = None

    def require(self, operation: str, target: str, now: int) -> None:
        if self.revoked_by is not None:
            raise CapabilityDenied("grant is revoked")
        if now > self.expires_at:
            raise CapabilityDenied("grant is expired")
        if target != self.target:
            raise CapabilityDenied("grant target does not match")
        if operation not in self.operations:
            raise CapabilityDenied("operation is outside the grant")

    def revoke(self, actor: str) -> "CapabilityGrant":
        return replace(self, revoked_by=actor)


@dataclass(frozen=True)
class ProviderCapabilities:
    provider: str
    enforceable_dimensions: frozenset[str]


@dataclass(frozen=True)
class BudgetRecord:
    token_cost: int | None
    monetary_cost: float | None

    @classmethod
    def unknown(cls) -> "BudgetRecord":
        return cls(None, None)


@dataclass(frozen=True)
class ProcessResult:
    kind: str
    exit_status: int | None
    quiescent: bool
    budget: BudgetRecord


def require_eligible(provider: ProviderCapabilities, hard_required: frozenset[str]) -> None:
    missing = hard_required - provider.enforceable_dimensions
    if missing:
        raise BudgetIneligible(f"provider cannot enforce hard dimension: {sorted(missing)[0]}")
