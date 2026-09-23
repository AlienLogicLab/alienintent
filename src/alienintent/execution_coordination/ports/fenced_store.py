"""Additive fenced admission and durable local consumer contract."""
from dataclasses import dataclass
from typing import Mapping, Protocol

from alienintent.execution_coordination.ports.operational_store import Effect, OperationalStore, Reservation, ReservationRejected


@dataclass(frozen=True)
class GuardVector:
    versions: tuple[tuple[str, int], ...]
    authority: str
    epoch: int
    invocation: str

    def __post_init__(self) -> None:
        versions = tuple(tuple(pair) for pair in self.versions)
        if (not versions or any(len(p) != 2 or not isinstance(p[0], str) or not p[0]
                                or type(p[1]) is not int or p[1] < 0 for p in versions)
                or len({p[0] for p in versions}) != len(versions)
                or self.authority not in dict(versions)
                or not isinstance(self.invocation, str) or not self.invocation
                or type(self.epoch) is not int or self.epoch < 1):
            raise ReservationRejected('invalid guard vector')
        object.__setattr__(self, 'versions', tuple(sorted(versions)))


@dataclass(frozen=True)
class ConsumerReceipt:
    effect_id: str
    invocation: str
    digest: str


@dataclass(frozen=True)
class EffectConfirmation:
    effect_id: str
    receipt: ConsumerReceipt


class FencedOperationalStore(OperationalStore, Protocol):
    def acquire_many(self, profile: str, resources: tuple[tuple[str, str], ...], owner: str) -> tuple[Reservation, ...]: ...
    def commit_guarded(self, profile: str, aggregate: str, expected_version: int, expected_vector: GuardVector, reservations: tuple[Reservation, ...], state: Mapping[str, object], effect_id: str, payload: Mapping[str, object]) -> int: ...
    def claim_guarded(self, profile: str, effect_id: str, reservations: tuple[Reservation, ...], expected_vector: GuardVector) -> Effect: ...
    def consume_guarded(self, profile: str, effect_id: str, reservations: tuple[Reservation, ...], expected_vector: GuardVector) -> ConsumerReceipt: ...
    def readback_guarded(self, profile: str, effect_id: str) -> ConsumerReceipt | None: ...
    def confirm_guarded(self, profile: str, effect_id: str, reservations: tuple[Reservation, ...], receipt: ConsumerReceipt) -> EffectConfirmation: ...


@dataclass(frozen=True)
class ReconciliationPending:
    effect_id: str
    reason: str = 'consumer outcome unavailable; retain ownership and do not resend'
