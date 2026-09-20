"""Application-facing operator controls; no adapter writes the store directly."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from alienintent.control_plane.application.decision_inbox import DecisionInbox
from alienintent.execution_coordination.domain.escalation import DecisionSubmission


class OperatorError(ValueError):
    """An operator request could not be completed safely."""


class OperatorControlPlane:
    def __init__(self, profile: object) -> None:
        self._profile = profile

    def status(self) -> dict[str, object]:
        coordinator = getattr(self._profile, "coordinator", None)
        work = getattr(coordinator, "_work", None)
        items = () if work is None else work.import_ready_snapshot()
        execution: list[dict[str, object]] = []
        if coordinator is not None:
            for item in items:
                try:
                    state = coordinator.state(item.identity)
                    execution.append({"biu": item.identity, "stage": str(state.stage), "version": state.version, "outcome": state.outcome})
                except KeyError:
                    execution.append({"biu": item.identity, "stage": "unstarted"})
        store = getattr(self._profile, "store", None)
        reservations = () if store is None else store.recovery_reservations(getattr(self._profile, "name", "unknown"))
        return {
            "profile": getattr(self._profile, "name", "unknown"),
            "upstream": {"availability": "known" if work is not None else "unavailable", "items": len(items)},
            "execution": {"availability": "known", "items": execution, "wip": len(reservations), "capacity": "unavailable" if reservations else "available"},
            "projection": {"availability": "known" if coordinator is not None else "unavailable", "delivery_health": self._delivery_health(coordinator)},
        }

    def explain(self, identity: str) -> dict[str, object]:
        coordinator = self._coordinator()
        state = coordinator.state(identity)
        return {"biu": identity, "stage": str(state.stage), "version": state.version, "outcome": state.outcome, "guards": {"execution_state": "kernel", "authority_blocked": state.outcome == "authority-block"}}

    def run(self, *, actor: str, authority: str, expected_version: int, reason: str, idempotency_key: str) -> dict[str, object]:
        self._command_fields(actor, authority, expected_version, reason, idempotency_key)
        readiness = getattr(self._profile, "readiness", None)
        if not callable(readiness) or not readiness():
            raise OperatorError("readiness gate failed; autonomous work was not started")
        summary = self._coordinator().start()
        return {"stop_reason": str(summary.stop_reason), "dispatched": list(summary.dispatched)}

    def resume(self, *, actor: str, authority: str, expected_version: int, reason: str, idempotency_key: str) -> dict[str, object]:
        return self.run(actor=actor, authority=authority, expected_version=expected_version, reason=reason, idempotency_key=idempotency_key)

    def decisions(self) -> DecisionInbox:
        profile = getattr(self._profile, "name", "unknown")
        return DecisionInbox(getattr(self._profile, "store"), self._coordinator(), profile)

    def decide(self, *, actor: str, authority: str, identity: str, expected_version: int, reason: str, idempotency_key: str, choice: str) -> dict[str, object]:
        self._command_fields(actor, authority, expected_version, reason, idempotency_key)
        return asdict(self.decisions().submit(DecisionSubmission(actor, authority, identity, expected_version, expected_version, idempotency_key, choice)))

    def invoke(self, operation: str, target: str | None, *, actor: str, authority: str, expected_version: int, reason: str, idempotency_key: str) -> object:
        """Delegate a mutation to the profile's application service boundary."""
        self._command_fields(actor, authority, expected_version, reason, idempotency_key)
        service = getattr(self._profile, operation, None)
        if not callable(service):
            raise OperatorError(f"{operation} is unavailable for this profile")
        return service(target, actor=actor, authority=authority, expected_version=expected_version, reason=reason, idempotency_key=idempotency_key)

    def _coordinator(self) -> Any:
        coordinator = getattr(self._profile, "coordinator", None)
        if coordinator is None:
            raise OperatorError("profile has no executable coordinator")
        return coordinator

    @staticmethod
    def _command_fields(actor: str, authority: str, expected_version: int, reason: str, idempotency_key: str) -> None:
        if not all((actor, authority, reason, idempotency_key)) or expected_version < 0:
            raise OperatorError("mutating command requires actor, authority, expected version, reason and idempotency key")

    @staticmethod
    def _delivery_health(coordinator: object | None) -> dict[str, object]:
        health = getattr(coordinator, "delivery_health", {}) if coordinator is not None else {}
        return {identity: {"delivered": value.delivered, "detail": value.detail} for identity, value in health.items()}
