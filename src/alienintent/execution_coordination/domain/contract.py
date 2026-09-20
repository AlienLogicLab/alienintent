"""Immutable, content-addressed execution-contract values."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any


class ContractValidationError(ValueError):
    """Raised when a BIU contract omits a binding execution field."""


@dataclass(frozen=True)
class BudgetPolicy:
    hard_required_dimensions: tuple[str, ...] = ()
    maximum_attempts: int = 1
    hard_wall_clock_seconds: int | None = None
    retry_limit: int = 0
    concurrency_limit: int | None = None
    cancellation_limit: int | None = None

    def __post_init__(self) -> None:
        if self.maximum_attempts < 1:
            raise ContractValidationError("maximum_attempts must be positive")
        if self.retry_limit < 0:
            raise ContractValidationError("retry_limit cannot be negative")
        for name in ("hard_wall_clock_seconds", "concurrency_limit", "cancellation_limit"):
            value = getattr(self, name)
            if value is not None and value < 1:
                raise ContractValidationError(f"{name} must be positive when specified")

    @property
    def required_dimensions(self) -> tuple[str, ...]:
        configured = list(self.hard_required_dimensions)
        if self.hard_wall_clock_seconds is not None:
            configured.append("wall-clock")
        if self.concurrency_limit is not None:
            configured.append("concurrency")
        if self.cancellation_limit is not None:
            configured.append("cancellation")
        return tuple(dict.fromkeys(configured))
        if any(not dimension for dimension in self.hard_required_dimensions):
            raise ContractValidationError("budget dimensions must be non-empty")


@dataclass(frozen=True)
class BiuContract:
    identity: str
    version: str
    intent: str
    satisfied_requirement_ids: tuple[str, ...]
    fixed_decisions: tuple[str, ...]
    authorized_scope: tuple[str, ...]
    excluded_scope: tuple[str, ...]
    dependencies: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    budget_policy: BudgetPolicy
    retry_policy: str
    completion_criteria: tuple[str, ...]
    verification_obligations: tuple[str, ...]
    required_evidence: tuple[str, ...]
    non_goals: tuple[str, ...]
    candidate_custody_requirements: tuple[str, ...]
    release_policy: str
    authority_issuer: str
    authority_references: tuple[str, ...]
    target_repositories: tuple[str, ...]
    baselines: tuple[str, ...]
    required_closure_actions: tuple[str, ...]
    stop_escalation_conditions: tuple[str, ...]
    content_digest: str = field(init=False)

    def __post_init__(self) -> None:
        required_scalars = ("identity", "version", "intent", "retry_policy", "release_policy", "authority_issuer")
        for name in required_scalars:
            if not getattr(self, name):
                raise ContractValidationError(f"{name} is required")
        required_sequences = (
            "satisfied_requirement_ids", "fixed_decisions", "authorized_scope", "required_capabilities",
            "completion_criteria", "verification_obligations", "required_evidence", "candidate_custody_requirements",
            "excluded_scope", "non_goals", "authority_references", "target_repositories", "baselines", "required_closure_actions",
            "stop_escalation_conditions",
        )
        for name in required_sequences:
            values = getattr(self, name)
            if not values or any(not value for value in values):
                raise ContractValidationError(f"{name} is required")
        payload = self._payload_without_digest()
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=_json_value).encode()
        object.__setattr__(self, "content_digest", f"sha256:{sha256(encoded).hexdigest()}")

    def canonical_payload(self) -> dict[str, Any]:
        return self._payload_without_digest()

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            name: asdict(getattr(self, name)) if name == "budget_policy" else getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "content_digest"
        }


def _json_value(value: object) -> object:
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(f"not canonical JSON: {type(value).__name__}")
