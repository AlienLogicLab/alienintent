from pathlib import Path


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

    fields = {"target": "PY-08", "actor": "morty", "authority": "operator", "expected_version": 0, "reason": "operator stop", "idempotency_key": "cancel-1"}
    assert service.cancel(**fields)["status"] == "cancelled"
    assert service.cancel(**fields)["status"] == "cancelled"
    assert worker.calls == 1
    _, persisted = profile.store.read_state("offline", "factory:PY-08")
    assert persisted["outcome"] == "cancelled-by-operator"
    assert persisted["cancellation"]["actor"] == "morty"
