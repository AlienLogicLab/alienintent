"""Conservative durable execution and read-back reconciliation for effect intents."""

from __future__ import annotations

from collections.abc import Callable

from alienintent.execution_coordination.ports.operational_store import Effect, OperationalStore, ReservationRejected


class EffectExecutor:
    """Claims an intent before calling an idempotent external effect boundary."""

    def __init__(self, store: OperationalStore, send: Callable[[Effect], str]) -> None:
        self._store = store
        self._send = send

    def execute(self, profile: str, effect_id: str) -> str:
        effect = self._store.claim_effect(profile, effect_id)
        receipt = self._send(effect)
        self._store.confirm_effect(profile, effect_id, receipt)
        return receipt

    def reconcile(self, profile: str, effect_id: str, read_back: Callable[[Effect], str | None]) -> bool:
        effect = next((item for item in self._store.unresolved_effects(profile) if item.identity == effect_id), None)
        if effect is None:
            raise ReservationRejected("effect is not unresolved")
        receipt = read_back(effect)
        if receipt is None:
            return False
        self._store.confirm_effect(profile, effect_id, receipt)
        return True
