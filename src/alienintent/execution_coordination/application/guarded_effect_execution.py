"""Guarded local delivery with conservative, readback-only recovery."""
from alienintent.execution_coordination.ports.fenced_store import (
    EffectConfirmation, FencedOperationalStore, GuardVector, ReconciliationPending,
)
from alienintent.execution_coordination.ports.operational_store import Reservation


class GuardedEffectExecutor:
    def __init__(self, store: FencedOperationalStore) -> None:
        self._store = store

    def execute(self, profile: str, effect_id: str, reservations: tuple[Reservation, ...], vector: GuardVector) -> EffectConfirmation | ReconciliationPending:
        self._store.claim_guarded(profile, effect_id, reservations, vector)
        self._store.consume_guarded(profile, effect_id, reservations, vector)
        # Confirmation uses durable readback, never an assumed send result.
        return self.reconcile(profile, effect_id, reservations)

    def reconcile(self, profile: str, effect_id: str, reservations: tuple[Reservation, ...]) -> EffectConfirmation | ReconciliationPending:
        receipt = self._store.readback_guarded(profile, effect_id)
        if receipt is None:
            return ReconciliationPending(effect_id)
        return self._store.confirm_guarded(profile, effect_id, reservations, receipt)
