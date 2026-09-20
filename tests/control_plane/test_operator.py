from pathlib import Path

import pytest


def test_status_keeps_execution_known_when_upstream_is_unavailable(tmp_path: Path) -> None:
    from alienintent.control_plane.application.operator import OperatorControlPlane
    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore

    store = SQLiteOperationalStore(tmp_path / "state.db")
    store.commit("p", "factory:PY-08", 0, {"stage": "IMPLEMENT", "version": 0, "accepted": False, "closure": []})

    class UnavailableWork:
        def import_ready_snapshot(self):
            raise RuntimeError("token=sentinel-secret upstream unavailable")

    service = OperatorControlPlane("p", store, UnavailableWork(), None, lambda: False)
    result = service.status()

    assert result["upstream"] == {"source": "work-management", "status": "unavailable"}
    assert result["execution"]["source"] == "operational-store"
    assert result["execution"]["items"][0]["identity"] == "PY-08"


def test_mutation_requires_authority_and_rejects_stale_version(tmp_path: Path) -> None:
    from alienintent.control_plane.application.operator import OperatorControlPlane, OperatorDenied
    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore

    store = SQLiteOperationalStore(tmp_path / "state.db")
    store.commit("p", "factory:PY-08", 0, {"stage": "IMPLEMENT", "version": 4, "accepted": False, "closure": []})
    service = OperatorControlPlane("p", store, None, None, lambda: True)

    with pytest.raises(OperatorDenied, match="authority"):
        service.cancel("PY-08", actor="morty", authority="", expected_version=4, reason="stop", idempotency_key="k")
    with pytest.raises(OperatorDenied, match="stale"):
        service.cancel("PY-08", actor="morty", authority="operator", expected_version=3, reason="stop", idempotency_key="k")
