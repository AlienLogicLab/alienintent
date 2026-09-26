"""FX-B0 proof for the read-only bootstrap custody manifest (WO-220501)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bootstrap_custody_manifest as bcm  # noqa: E402

RETAINED = bcm.ROOT / "docs/evidence/wo-220501-fx-b0/bootstrap-custody-manifest.json"


@pytest.fixture()
def fixture(tmp_path):
    root, units, proc, policy = bcm.build_fixture(tmp_path)
    manifest = bcm.generate(root, units, proc, bcm.ROOT, "HEAD", policy, bcm._FIXED_CLOCK)
    return manifest, root, units, proc, policy


def _asset(manifest, rel):
    return next(a for a in manifest["assets"] if a["path"] == rel)


def test_discovers_current_surface_not_historical_list(fixture):
    manifest, root, *_ = fixture
    assert bcm.check_manifest(manifest) == []
    disc = manifest["discovery"]
    assert disc["historical_eighteen_missing"] == []
    assert disc["additional_to_historical_eighteen"] == [
        "factory-director-host/factory_director_host.py", "factory_status.sh"]
    assert not any("__pycache__" in a["path"] for a in manifest["assets"])
    # Negative control: a fixed-list inventory is caught by rediscovery.
    stale = copy.deepcopy(manifest)
    stale["assets"] = [a for a in stale["assets"] if a["in_historical_eighteen"]]
    assert any(f.startswith("completeness:") for f in bcm.verify_against_root(stale, root))


def test_identity_and_consumers_are_attributed(fixture):
    manifest, root, *_ = fixture
    live = _asset(manifest, "liveness.py")
    assert live["identity"]["sha256"] == bcm._sha256((root / "liveness.py").read_bytes())
    assert live["consumers"]["service_units"][0]["unit"] == "alienintent-liveness.service"
    assert live["consumers"]["service_units"][0]["enabled_via_wants_link"] is True
    assert [p["pid"] for p in live["consumers"]["processes"]] == [4242]
    assert live["provenance"]["bootstrap_tests"] == ["test_liveness_suppression.py"]
    assert _asset(manifest, "attention.py")["consumers"]["bootstrap_assets"] == ["liveness.py"]
    # Negative control: drifted bytes are detected.
    (root / "liveness.py").write_text("import attention  # drift\n")
    assert any(f.startswith("identity:") for f in bcm.verify_against_root(manifest, root))


def test_classification_never_invents_retirement(fixture, tmp_path):
    manifest, *_ = fixture
    assert _asset(manifest, "liveness.py")["custody"]["class"] == bcm.KEEP
    assert _asset(manifest, "cycle_data.py")["custody"]["class"] == bcm.HISTORICAL
    assert _asset(manifest, "release_admission.py")["custody"]["class"] == bcm.CANDIDATE
    assert all(a["custody"]["migration_deletion_retirement_authorized"] is False for a in manifest["assets"])
    forged = copy.deepcopy(manifest)
    _asset(forged, "liveness.py")["custody"]["class"] = "RETIRE_CANDIDATE"
    assert any(f.startswith("custody_class:") for f in bcm.check_manifest(forged))
    # A historical label contradicted by an observed live consumer degrades to UNKNOWN.
    root, units, proc, policy = bcm.build_fixture(tmp_path / "conflict")
    policy["liveness.py"] = bcm.POLICY["cycle_data.py"]
    conflicted = bcm.generate(root, units, proc, bcm.ROOT, "HEAD", policy, bcm._FIXED_CLOCK)
    assert _asset(conflicted, "liveness.py")["custody"]["class"] == bcm.UNKNOWN
    with pytest.raises(ValueError):
        bcm.generate(root, units, proc, bcm.ROOT, "HEAD",
                     {"liveness.py": {**bcm.POLICY["liveness.py"], "class": "RETIRE"}}, bcm._FIXED_CLOCK)


def test_unknown_is_local_to_its_asset(fixture):
    manifest, *_ = fixture
    unknown = _asset(manifest, "factory_status.sh")
    assert unknown["custody"]["class"] == bcm.UNKNOWN
    assert all(u["blocks"] == ["factory_status.sh"] for u in unknown["custody"]["unknowns"])
    assert sum(1 for a in manifest["assets"] if a["custody"]["class"] != bcm.UNKNOWN) == 19
    widened = copy.deepcopy(manifest)
    _asset(widened, "factory_status.sh")["custody"]["unknowns"][0]["blocks"].append("liveness.py")
    assert any(f.startswith("unknown_locality:") for f in bcm.check_manifest(widened))


def test_inventory_pass_has_zero_effect(fixture, tmp_path):
    manifest, root, units, *_ = fixture
    effects = manifest["side_effect_check"]
    assert effects["unchanged"] is True and effects["changed_paths"] == []
    assert all(argv[0] == "git" and argv[1] in bcm._READ_ONLY_GIT for argv in effects["commands_executed"])
    root2, units2, proc2, policy2 = bcm.build_fixture(tmp_path / "mutating")
    touched = bcm.generate(root2, units2, proc2, bcm.ROOT, "HEAD", policy2, bcm._FIXED_CLOCK,
                           during=lambda r: (r / "observer.py").write_text("# rewritten\n"))
    assert touched["side_effect_check"]["changed_paths"] == [str(root2 / "observer.py")]
    assert any(f.startswith("zero_effect:") for f in bcm.check_manifest(touched))
    with pytest.raises(PermissionError):
        bcm.Runner(bcm.ROOT).git("checkout", "main")


def test_negative_controls_intact_fault_restored():
    records = bcm.run_negative_controls()
    assert [r["control"] for r in records] == [
        "discovery_beyond_historical_eighteen", "exact_identity", "truthful_custody_class",
        "unknown_locality", "zero_effect"]
    assert all(r["verdict"] == "PASS" for r in records), records


def test_retained_manifest_is_valid_and_covers_current_surface():
    manifest = json.loads(RETAINED.read_text())
    assert bcm.check_manifest(manifest) == []
    paths = {a["path"] for a in manifest["assets"]}
    assert set(bcm.HISTORICAL_EIGHTEEN) <= paths
    assert {"factory_status.sh", "project_add_recovery_probe.sh", "worker_credential_probe.sh",
            "factory-director-host/factory_director_host.py"} <= paths
    for asset in manifest["assets"]:
        for ref in asset["custody"]["evidence"]:
            assert (bcm.ROOT / ref).exists(), ref
