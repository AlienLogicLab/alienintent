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
class VerifierIndependence:
    producer_invocation_id: str
    verifier_invocation_id: str

    def require(self, role: InvocationRole) -> None:
        if role is not InvocationRole.VERIFIER or self.producer_invocation_id == self.verifier_invocation_id:
            raise PermissionError("self-approval is prohibited")


class ReservationBook:
    """In-memory invocation reservations; callers release only their own id."""
    def __init__(self, mutating_limit: int, global_limit: int) -> None:
        self._mutating_limit = mutating_limit
        self._global_limit = global_limit
        self._held: dict[str, InvocationRole] = {}

    def reserve(self, invocation_id: str, role: InvocationRole) -> None:
        if invocation_id in self._held:
            return
        if len(self._held) >= self._global_limit:
            raise RuntimeError("global capacity is exhausted")
        if role is InvocationRole.PRODUCER and sum(r is InvocationRole.PRODUCER for r in self._held.values()) >= self._mutating_limit:
            raise RuntimeError("mutating capacity is exhausted")
        self._held[invocation_id] = role

    def release(self, invocation_id: str) -> None:
        self._held.pop(invocation_id, None)


@dataclass(frozen=True)
class RetrySchedule:
    maximum_attempts: int
    retry_limit: int
    base_delay_seconds: float
    jitter_seconds: float

    def next_after_failure(self, attempt: int, now: float) -> float | None:
        if attempt >= self.maximum_attempts or attempt > self.retry_limit:
            return None
        # Deterministic bounded jitter avoids hidden random state in evidence.
        return now + self.base_delay_seconds * (2 ** (attempt - 1)) + self.jitter_seconds


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
