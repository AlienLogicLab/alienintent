"""Named operator application services; presentation adapters do not mutate storage."""
from __future__ import annotations
from collections.abc import Callable
from typing import Any

class OperatorDenied(ValueError):
    """An operator command was not admissible through the normal boundary."""

class OperatorControlPlane:
    def __init__(self, profile: str, store: Any, work: Any, coordinator: Any, readiness: Callable[[], bool]) -> None:
        self._profile, self._store, self._work, self._coordinator, self._readiness = profile, store, work, coordinator, readiness

    def status(self) -> dict[str, object]:
        try:
            upstream = {"source": "work-management", "status": "available", "items": [item.identity for item in self._work.import_ready_snapshot()]}
        except Exception:
            upstream = {"source": "work-management", "status": "unavailable"}
        items = [{"identity": identity.removeprefix("factory:"), "revision": version, "lifecycle": state.get("stage"), "outcome": state.get("outcome")} for identity, version, state in self._store.list_states(self._profile, "factory:")]
        return {"profile": self._profile, "upstream": upstream, "execution": {"source": "operational-store", "status": "known", "items": items}, "projection": {"source": "projection", "status": "unknown"}}

    def run(self, **fields: str | int) -> object:
        self._admit(fields)
        if not self._readiness(): raise OperatorDenied("readiness gate failed; autonomous work was not started")
        if self._coordinator is None: raise OperatorDenied("run is unavailable for this profile")
        return self._coordinator.start()

    def resume(self, **fields: str | int) -> object: return self.run(**fields)

    def stop(self, **fields: str | int) -> object:
        self._admit(fields); return self._cancel_worker(str(fields["target"]), str(fields["reason"]))

    def cancel(self, target: str, **fields: str | int) -> object:
        fields["target"] = target; self._admit(fields); return self._cancel_worker(target, str(fields["reason"]))

    def explain(self, target: str) -> dict[str, object]:
        _, state = self._store.read_state(self._profile, f"factory:{target}")
        if not state: raise OperatorDenied(f"unknown work item: {target}")
        return {"target": target, "guard_outcomes": {"lifecycle": state.get("stage"), "outcome": state.get("outcome"), "decision": state.get("decision_choice")}, "evidence": {"execution_revision": state.get("version")}}

    def _cancel_worker(self, target: str, reason: str) -> object:
        worker = getattr(self._coordinator, "_worker", None)
        if worker is None: raise OperatorDenied("cancel is unavailable for this profile")
        return worker.cancel(target, reason)

    def _admit(self, fields: dict[str, str | int]) -> None:
        actor, authority, target, expected = fields.get("actor"), fields.get("authority"), fields.get("target"), fields.get("expected_version")
        if not isinstance(actor, str) or not actor or not isinstance(authority, str) or not authority: raise OperatorDenied("actor and authority are required")
        if not isinstance(target, str) or not target or not isinstance(expected, int): raise OperatorDenied("target and expected version are required")
        _, state = self._store.read_state(self._profile, f"factory:{target}")
        if state and state.get("version") != expected: raise OperatorDenied("stale expected version")
