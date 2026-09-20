from pathlib import Path
from types import SimpleNamespace

import pytest


def test_cancel_is_idempotent_and_records_a_guarded_cancellation(tmp_path: Path) -> None:
    """Replacing the coordinator protocol with a raw worker call must fail this test."""
    from alienintent.composition.offline_profile import OfflineProfile
    from alienintent.control_plane.application.operator import OperatorControlPlane

    class Work:
        def import_ready_snapshot(self): return ()
    class Worker:
        def __init__(self): self.calls = 0
        def cancel(self, *_): self.calls += 1; return "cancelled"

    worker = Worker()
    profile = OfflineProfile(tmp_path / "state.db", Work(), worker, tmp_path / "artifacts")
    profile.store.commit("offline", "factory:PY-08", 0, {"stage": "IMPLEMENT", "version": 0, "accepted": False, "closure": []})
    service = OperatorControlPlane(profile.name, profile.store, profile.work, profile.coordinator, lambda: True)

    fields = {"target": "PY-08", "actor": "morty", "authority": "operator", "intent": "cancel", "expected_version": 1, "reason": "operator stop", "idempotency_key": "cancel-1"}
    assert service.cancel(**fields)["status"] == "cancelled"
    assert service.cancel(**fields)["status"] == "cancelled"
    assert worker.calls == 1
    _, persisted = profile.store.read_state("offline", "factory:PY-08")
    assert persisted["outcome"] == "cancelled-by-operator"
    assert persisted["cancellation"]["actor"] == "morty"
    assert persisted["cancellation"]["authority"] == "operator"


def test_reconcile_reports_current_execution_without_starting_work() -> None:
    """Turning reconcile into start() would incorrectly create autonomous work."""
    from alienintent.control_plane.application.operator import OperatorControlPlane

    class Store:
        def read_state(self, *_): return 0, {"version": 0}
    class Coordinator:
        def reconcile(self, target): return {"target": target, "source": "execution-revision", "status": "reconciled"}

    result = OperatorControlPlane("p", Store(), None, Coordinator(), lambda: True).reconcile(
        target="PY-08", actor="morty", authority="operator", intent="repair", expected_version=0, reason="repair", idempotency_key="r1"
    )
    assert result == {"target": "PY-08", "source": "execution-revision", "status": "reconciled"}


def test_stop_leaves_accepted_done_work_untouched(tmp_path: Path) -> None:
    """Removing the terminal-state check would overwrite accepted evidence."""
    from alienintent.composition.offline_profile import OfflineProfile

    class Work:
        def import_ready_snapshot(self): return ()
    class Worker:
        def cancel(self, *_): raise AssertionError("accepted work must not be cancelled")

    profile = OfflineProfile(tmp_path / "state.db", Work(), Worker(), tmp_path / "artifacts")
    profile.store.commit("offline", "factory:PY-07", 0, {"stage": "DONE", "accepted": True, "outcome": "success"})

    assert profile.coordinator.stop_owned("morty", "operator", 1, "quiesce", "stop-1") == {"stopped": []}
    _, state = profile.store.read_state("offline", "factory:PY-07")
    assert state == {"stage": "DONE", "accepted": True, "outcome": "success"}


def test_cancel_rejects_terminal_accepted_work_without_mutating_its_evidence(tmp_path: Path) -> None:
    from alienintent.composition.offline_profile import OfflineProfile

    class Work:
        def import_ready_snapshot(self): return ()
    class Worker:
        def cancel(self, *_): raise AssertionError("terminal work must not reach the worker")

    profile = OfflineProfile(tmp_path / "state.db", Work(), Worker(), tmp_path / "artifacts")
    accepted = {"stage": "DONE", "accepted": True, "outcome": "success", "closure": []}
    profile.store.commit("offline", "factory:PY-07", 0, accepted)

    with pytest.raises(ValueError, match="terminal"):
        profile.coordinator.cancel("PY-07", "morty", "operator", 1, "quiesce", "cancel-1")
    assert profile.store.read_state("offline", "factory:PY-07")[1] == accepted


def test_stop_quiesces_each_nonterminal_item_at_its_own_revision(tmp_path: Path) -> None:
    from alienintent.composition.offline_profile import OfflineProfile

    class Work:
        def import_ready_snapshot(self): return ()
    class Worker:
        def __init__(self): self.cancelled = []
        def cancel(self, identity, _): self.cancelled.append(identity); return "cancelled"

    worker = Worker()
    profile = OfflineProfile(tmp_path / "state.db", Work(), worker, tmp_path / "artifacts")
    profile.store.commit("offline", "factory:PY-08", 0, {"stage": "IMPLEMENT", "accepted": False, "closure": []})
    profile.store.commit("offline", "factory:PY-09", 0, {"stage": "IMPLEMENT", "accepted": False, "closure": []})
    profile.store.commit("offline", "factory:PY-09", 1, {"stage": "IMPLEMENT", "accepted": False, "closure": [], "note": "newer"})

    result = profile.coordinator.stop_owned("morty", "operator", 0, "quiesce", "stop-1")
    assert {entry["target"] for entry in result["stopped"]} == {"PY-08", "PY-09"}
    assert worker.cancelled == ["PY-08", "PY-09"]


def test_cancelled_work_is_not_dispatched_again(tmp_path: Path) -> None:
    """Replacing the kernel cancellation outcome with an unrecognised sidecar breaks this."""
    from alienintent.composition.offline_profile import OfflineProfile
    from alienintent.control_plane.application.operator import OperatorControlPlane
    class Work:
        def import_ready_snapshot(self): return ()
        def propose_release(self, _): raise AssertionError("cancelled work must not release")
    class Worker:
        def cancel(self, *_): return "cancelled"
        def start(self, *_): raise AssertionError("cancelled work must not dispatch")

    profile = OfflineProfile(tmp_path / "state.db", Work(), Worker(), tmp_path / "artifacts")
    profile.store.commit("offline", "factory:PY-08", 0, {"stage": "IMPLEMENT", "version": 0, "accepted": False, "closure": []})
    service = OperatorControlPlane(profile.name, profile.store, profile.work, profile.coordinator, lambda: True)
    service.cancel(target="PY-08", actor="morty", authority="operator", intent="cancel", expected_version=1, reason="operator stop", idempotency_key="cancel-1")

    assert not profile.coordinator._eligible(SimpleNamespace(identity="PY-08", dependencies=(), automatic_release=True))


def test_mutation_uses_the_published_store_revision_for_staleness(tmp_path: Path) -> None:
    """Comparing a payload field instead of the aggregate revision must fail this test."""
    from alienintent.composition.offline_profile import OfflineProfile
    from alienintent.control_plane.application.operator import OperatorControlPlane, OperatorDenied

    class Work:
        def import_ready_snapshot(self): return ()
    class Worker:
        def cancel(self, *_): return "cancelled"

    profile = OfflineProfile(tmp_path / "state.db", Work(), Worker(), tmp_path / "artifacts")
    profile.store.commit("offline", "factory:PY-08", 0, {"stage": "IMPLEMENT", "version": 0, "accepted": False, "closure": []})
    service = OperatorControlPlane(profile.name, profile.store, profile.work, profile.coordinator, lambda: True)
    fields = dict(target="PY-08", actor="morty", authority="operator", intent="cancel", expected_version=1, reason="operator stop", idempotency_key="cancel-1")

    assert service.cancel(**fields)["idempotent"] is False
    with pytest.raises(OperatorDenied, match="stale expected version"):
        service.cancel(**(fields | {"idempotency_key": "cancel-2"}))


def test_mutation_requires_an_operator_intent() -> None:
    from alienintent.control_plane.application.operator import OperatorControlPlane, OperatorDenied

    class Store:
        def read_state(self, *_): return 0, {"stage": "IMPLEMENT"}

    with pytest.raises(OperatorDenied, match="intent"):
        OperatorControlPlane("p", Store(), None, None, lambda: True)._admit({
            "target": "PY-08", "actor": "morty", "authority": "operator", "expected_version": 0,
            "reason": "repair", "idempotency_key": "key",
        })


def test_status_does_not_claim_healthy_projection_without_deliveries() -> None:
    from alienintent.control_plane.application.operator import OperatorControlPlane

    class Store:
        def list_states(self, *_): return ()
    class Work:
        def import_ready_snapshot(self): return ()
    class Coordinator:
        delivery_health = {}

    status = OperatorControlPlane("p", Store(), Work(), Coordinator(), lambda: True).status()
    assert status["projection"] == {"source": "decision-notifier", "status": "unknown"}


def test_explain_uses_the_coordinator_guard_account() -> None:
    from alienintent.control_plane.application.operator import OperatorControlPlane

    class Coordinator:
        def guard_account(self, target): return {"target": target, "eligible": False, "reason": "authority-block", "evidence": {"execution_revision": 4}}

    result = OperatorControlPlane("p", None, None, Coordinator(), lambda: True).explain("PY-08")
    assert result == {"target": "PY-08", "guard_outcomes": {"eligible": False, "reason": "authority-block"}, "evidence": {"execution_revision": 4}}


def test_reconcile_calls_the_coordinator_recovery_boundary() -> None:
    from alienintent.control_plane.application.operator import OperatorControlPlane

    class Store:
        def read_state(self, *_): return 0, {"stage": "IMPLEMENT"}
    class Coordinator:
        def reconcile(self, target): return {"target": target, "source": "execution-revision", "status": "reconciled", "recovered": True}

    result = OperatorControlPlane("p", Store(), None, Coordinator(), lambda: True).reconcile(
        target="PY-08", actor="morty", authority="operator", intent="repair projection", expected_version=0, reason="repair", idempotency_key="r1"
    )
    assert result["recovered"] is True


def test_resume_recovers_before_starting_the_loop() -> None:
    from alienintent.control_plane.application.operator import OperatorControlPlane

    class Store:
        def read_state(self, *_): return 0, {"stage": "IMPLEMENT"}
    class Coordinator:
        def __init__(self): self.calls = []
        def reconcile(self, target): self.calls.append(("reconcile", target)); return {"target": target}
        def start(self): self.calls.append(("start",)); return "started"

    coordinator = Coordinator()
    result = OperatorControlPlane("p", Store(), None, coordinator, lambda: True).resume(
        target="PY-08", actor="morty", authority="operator", intent="resume", expected_version=0,
        reason="restart", idempotency_key="resume-1",
    )
    assert result == "started"
    assert coordinator.calls == [("reconcile", "PY-08"), ("start",)]


def test_repeated_unavailable_upstream_is_coalesced_durably(tmp_path: Path) -> None:
    from alienintent.composition.offline_profile import OfflineProfile
    from alienintent.control_plane.application.operator import OperatorControlPlane

    class Work:
        def import_ready_snapshot(self): raise RuntimeError("unavailable")
    class Worker:
        def cancel(self, *_): return "cancelled"

    profile = OfflineProfile(tmp_path / "state.db", Work(), Worker(), tmp_path / "artifacts")
    service = OperatorControlPlane(profile.name, profile.store, profile.work, profile.coordinator, lambda: True)
    first, second = service.status(), service.status()

    assert first["diagnostics"][0]["transition"] is True
    assert second["diagnostics"][0]["transition"] is False
    _, persisted = profile.store.read_state("offline", "control-plane-diagnostic:upstream-unavailable")
    assert persisted["repeat_count"] == 2
    assert persisted["last_seen"]
