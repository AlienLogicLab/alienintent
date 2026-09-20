"""Provider-neutral durable operational-state boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol


class StoreUnavailable(RuntimeError):
    """The configured durable store cannot currently serve an operation."""


class VersionConflict(RuntimeError):
    """A write did not match the aggregate's expected version."""


class ReservationRejected(RuntimeError):
    """A durable reservation or blocked mutation was rejected."""


class StaleFence(ReservationRejected):
    """An owner tried to act using an old reservation fence."""


class SchemaIncompatible(RuntimeError):
    """The persisted schema cannot be safely opened by this binary."""


@dataclass(frozen=True)
class Receipt:
    identity: str
    aggregate: str
    version: int


@dataclass(frozen=True)
class Reservation:
    scope: str
    key: str
    owner: str
    fence: int


@dataclass(frozen=True)
class Effect:
    identity: str
    aggregate: str
    payload: Mapping[str, object]


@dataclass(frozen=True)
class SchemaPreflight:
    current_version: int | None
    migration: tuple[int, int] | None


class OperationalStore(Protocol):
    def receive(self, profile: str, event_id: str, digest: str, aggregate: str, expected_version: int, state: Mapping[str, object]) -> Receipt: ...
    def record_receipt(self, profile: str, event_id: str, digest: str, aggregate: str) -> Receipt: ...
    def apply_receipt(self, profile: str, event_id: str, expected_version: int, state: Mapping[str, object], effect_id: str, payload: Mapping[str, object]) -> int: ...
    def commit(self, profile: str, aggregate: str, expected_version: int, state: Mapping[str, object]) -> int: ...
    def acquire(self, profile: str, scope: str, key: str, owner: str) -> Reservation: ...
    def release(self, profile: str, scope: str, key: str, owner: str, fence: int) -> None: ...
    def read_state(self, profile: str, aggregate: str) -> tuple[int, dict[str, object]]: ...
    def commit_with_effect(self, profile: str, aggregate: str, expected_version: int, state: Mapping[str, object], effect_id: str, payload: Mapping[str, object]) -> int: ...
    def mark_effect_unknown(self, profile: str, effect_id: str) -> None: ...
    def claim_effect(self, profile: str, effect_id: str) -> Effect: ...
    def confirm_effect(self, profile: str, effect_id: str, receipt: str) -> None: ...
    def pending_effects(self, profile: str) -> tuple[Effect, ...]: ...
    def unresolved_effects(self, profile: str) -> tuple[Effect, ...]: ...
    def recovery_reservations(self, profile: str) -> tuple[Reservation, ...]: ...
