"""Focused FX-B7 proof for tools/live/installation_launch.py (WO-220510). Disposable hosts only."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import installation_launch as il  # noqa: E402


@pytest.fixture
def host(tmp_path):
    return il.build_fixture(tmp_path)


ALIAS_UNIT = "[Service]\nExecStart=/usr/bin/node /opt/ai/bin/b-disp.mjs --config /c.json\n"


def test_token_classification_keeps_persisted_identities_out():
    assert il.classify_token("/x/bin/b-disp.mjs") == "ALIAS"
    assert il.classify_token("b-disp") == "ALIAS"
    assert il.classify_token("/x/bin/alienintent.mjs") == "CANONICAL"
    for identity in ("b-disp/5fb59763-dbf7", "b-disp-morty", "B-DISP:", "b-disp-ownership", "b-disp/*"):
        assert il.classify_token(identity) is None


def test_every_pinned_surface_is_covered_and_intact_fixture_passes(host):
    record = il.inventory(host)
    assert set(record["surfaces"]) == set(il.SURFACES)
    assert all(v["status"] == "SCANNED" for v in record["surfaces"].values())
    assert il.check_inventory(record) == []
    assert record["alias_retirement"] == il.RETIREMENT_COMPLETE
    assert il.gate(host) == set()


def test_launch_position_distinguishes_exec_from_other_lines(host):
    (host.root / "surfaces/systemd-user-paths/x.service").write_text(
        "[Service]\nWorkingDirectory=/opt/b-disp\nExecStart=/usr/bin/true\n")
    classes = {(r["token"], r["class"]) for r in il.inventory(host)["references"]}
    assert ("/opt/b-disp", "ALIAS_REFERENCE") in classes
    assert il.check_inventory(il.inventory(host)) == []


def test_alias_launch_holds_retirement(host):
    (host.root / "surfaces/systemd-user-paths/legacy.service").write_text(ALIAS_UNIT)
    record = il.inventory(host)
    assert record["alias_launch_count"] == 1
    assert record["alias_retirement"] == il.RETIREMENT_HELD
    assert "alias_launch" in il.check_inventory(record)


def test_retirement_is_never_claimed(host):
    record = il.inventory(host)
    for claim in ("RETIRED", "AUTHORIZED"):
        assert "retirement_claim" in il.check_inventory(record | {"alias_retirement": claim})


def test_empty_plan_is_an_explicit_no_migration_receipt(host, tmp_path):
    receipt = il.migrate(il.plan(il.inventory(host)), None, tmp_path / "r", apply=False)
    assert receipt["result"] == "NO_MIGRATION_REQUIRED" and not receipt["applied"]


def test_migration_requires_authority_and_apply_then_rolls_back_exactly(host):
    unit = host.root / "surfaces/systemd-user-paths/legacy.service"
    unit.write_text(ALIAS_UNIT)
    original = unit.read_bytes()
    steps = il.plan(il.inventory(host))
    assert il.migrate(steps, None, host.root / "r0", apply=True)["holds"] == ["authority"]
    assert il.migrate(steps, host.root / "authority.md", host.root / "r1", apply=False)["holds"] == ["MIGRATION_PENDING"]
    assert unit.read_bytes() == original
    receipt = il.migrate(steps, host.root / "authority.md", host.root / "r2", apply=True)
    assert receipt["result"] == "MIGRATED"
    assert unit.read_text() == ALIAS_UNIT.replace("b-disp.mjs", "alienintent.mjs")
    assert il.check_inventory(il.inventory(host)) == []
    il.rollback(receipt, host.root / "r2")
    assert unit.read_bytes() == original and il.check_rollback(receipt) == []


def test_readback_requires_running_canonical_entry_point(host):
    assert il.readback(host)["failures"] == []
    units = json.loads((host.root / "units.json").read_text())
    units["alienintent.service"]["sub"] = "dead"
    (host.root / "units.json").write_text(json.dumps(units))
    assert il.readback(host)["failures"] == ["readback"]


def test_readback_ignores_units_that_only_mention_the_repository_slug(host):
    units = json.loads((host.root / "units.json").read_text())
    units["worker.service"] = {"exec": ["/usr/bin/claude -p Repository: AlienLogicLab/alienintent"],
                               "active": "active", "sub": "running", "main_pid": 0}
    (host.root / "units.json").write_text(json.dumps(units))
    assert [u["unit"] for u in il.readback(host)["units"]] == ["alienintent.service"]


def test_readback_with_no_canonical_unit_is_a_hold(host):
    (host.root / "units.json").write_text("{}")
    assert il.readback(host)["failures"] == ["readback"]


def test_preservation_allows_growth_and_lane_completion_but_not_loss(host):
    before = il.snapshot(host)
    state = json.loads(host.state_path().read_text())
    state["resources"]["o/r#2:PRODUCER:bbbb"] = {}
    state["active"] = {}
    host.state_path().write_text(json.dumps(state))
    assert il.check_preservation(before, il.snapshot(host))["failures"] == []
    del state["diagnostics"]["o/r#1:PRODUCER"]
    host.state_path().write_text(json.dumps(state))
    assert il.check_preservation(before, il.snapshot(host))["failures"] == ["preservation"]


def test_every_negative_control_discriminates():
    results = il.run_controls()
    assert {r["control"] for r in results} >= {
        "alias_launch_injected", "surface_unreadable", "surface_dropped", "readback_alias_process",
        "identity_dropped", "marker_altered", "retirement_claimed", "migration_without_authority",
        "rollback_incomplete"}
    for result in results:
        assert result["application_count"] == 1, result
        assert result["discriminating"], result
