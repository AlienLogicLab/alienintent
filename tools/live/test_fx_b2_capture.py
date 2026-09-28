"""FX-B2 fixture admission must reject incomplete authority before a host is launched."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import fx_b2_capture  # noqa: E402
from alienintent.execution_coordination.adapters.liveness_observations import StoreLifecycleJournal  # noqa: E402
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore  # noqa: E402
from alienintent.execution_coordination.domain.liveness import KnownActive  # noqa: E402


def test_preflight_rejects_missing_and_unbounded_authority(tmp_path):
    root = tmp_path / "profile"
    root.mkdir()
    profile = "fx-b2-liveness-operational"
    (tmp_path / "fx-b2-supervision.json").write_text(json.dumps({"root": str(root),
        "profile": profile, "host_invocation": "fx-b2-test", "host_authority": "fx-b2-operational-authorization"}))
    store = SQLiteOperationalStore(root / "liveness.sqlite")
    active = KnownActive("FX-B2-PROBE-fx-b2-test", "AlienLogicLab/alienintent", "sha256:" + "c" * 64,
                         "IMPLEMENT", 1, 1_000_000, "fx-b2-operational-authorization", True)
    StoreLifecycleJournal(store, profile=profile).enter(active)
    with pytest.raises(ValueError, match="AUTHORITY_UNAVAILABLE"):
        fx_b2_capture.preflight(root, now=2.0)
    store.commit(profile, active.authority, 0, {"schema_version": 1, "active": True,
        "epoch": 1, "invocation": "fx-b2-test"})
    with pytest.raises(ValueError, match="AUTHORITY_UNAVAILABLE"):
        fx_b2_capture.preflight(root, now=2.0)
    store.commit(profile, active.authority, 1, {"schema_version": 1, "active": True,
        "epoch": 1, "invocation": "fx-b2-test", "expires_at": 3600.0})
    assert fx_b2_capture.preflight(root, now=2.0)["active"]["generation"] == 1
    StoreLifecycleJournal(store, profile=profile).enter(KnownActive(
        active.biu, active.repository, active.contract_digest, active.stage, 2, 2_000_000,
        active.authority, True))
    with pytest.raises(ValueError, match="KNOWN_ACTIVE_INVALID"):
        fx_b2_capture.preflight(root, now=2.0)
