"""The dispatcher's JSON adapter over the release-admission gate (scripts/lifecycle-eligibility).

The gate decides; the adapter substitutes the dispatcher's live-claim count for the raw
state file (a record whose worker is gone must not occupy WIP) and adds the Director-host
pause flag and Founder holds, failing closed when either cannot be read. `prepared` (TASKS ->
READY) ignores only the checks execution admission owns; `admitted` (READY -> IMPLEMENT)
needs every check.
"""
import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_loader = importlib.machinery.SourceFileLoader("lifecycle_eligibility", str(ROOT / "scripts" / "lifecycle-eligibility"))
_spec = importlib.util.spec_from_loader(_loader.name, _loader)
script = importlib.util.module_from_spec(_spec)
_loader.exec_module(script)

from test_release_admission import GOOD  # noqa: E402


def run(tmp_path, monkeypatch, capsys, *, facts=None, holds=None, paused=False, active=0, issue=55):
    hold_path = tmp_path / "founder-holds.json"
    if holds is not None:
        hold_path.write_text(json.dumps({"schemaVersion": 1, "holds": holds}))
    pause = tmp_path / "PAUSE"
    if paused:
        pause.write_text("")
    host = tmp_path / "host.json"
    host.write_text(json.dumps({"wipLimit": 1, "founderHoldRecord": str(hold_path), "pauseFlag": str(pause)}))
    seen = {}

    def gather(number):
        seen["host_config"] = script.release_admission.HOST_CONFIG
        return dict(facts or GOOD, issue=number, active_claims_total=99, active_invocations=["stale#55:PRODUCER"])

    monkeypatch.setattr(script.release_admission, "gather", gather)
    assert script.main(["--issue", str(issue), "--director-host-config", str(host), "--active-claims", str(active)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert seen["host_config"] == host
    return result, {f["check"] for f in result["failures"]}


def test_admits_on_live_claim_count_not_raw_state(tmp_path, monkeypatch, capsys):
    result, checks = run(tmp_path, monkeypatch, capsys, holds=[])
    assert (result["prepared"], result["admitted"], result["agentReady"], checks) == (True, True, "READY", set())


def test_live_claims_at_the_limit_refuse_admission_but_not_preparation(tmp_path, monkeypatch, capsys):
    result, checks = run(tmp_path, monkeypatch, capsys, holds=[], active=1)
    assert checks == {"wip_capacity_available"}
    assert (result["prepared"], result["admitted"]) == (True, False)


def test_a_tasks_biu_with_a_ready_receipt_is_prepared(tmp_path, monkeypatch, capsys):
    result, checks = run(tmp_path, monkeypatch, capsys, holds=[], facts=dict(GOOD, status="TASKS"))
    assert checks == {"status_ready"}
    assert (result["prepared"], result["admitted"]) == (True, False)


def test_preparation_facts_refuse_both_transitions(tmp_path, monkeypatch, capsys):
    result, checks = run(tmp_path, monkeypatch, capsys, holds=[],
                         facts=dict(GOOD, status="TASKS", agent_ready="HOLD", open_dependencies=[9]))
    assert checks == {"status_ready", "agent_ready", "dependencies_satisfied"}
    assert (result["agentReady"], result["prepared"], result["admitted"]) == ("HOLD", False, False)


def test_founder_hold_and_pause_refuse(tmp_path, monkeypatch, capsys):
    result, checks = run(tmp_path, monkeypatch, capsys, holds=[{"issue": 55, "kind": "FOUNDER_DECISION", "reason": "r"}], paused=True)
    assert checks == {"founder_hold", "factory_paused"}
    assert result["prepared"] is False


def test_unreadable_hold_record_fails_closed(tmp_path, monkeypatch, capsys):
    result, checks = run(tmp_path, monkeypatch, capsys, holds=None)
    assert (result["prepared"], result["admitted"], checks) == (False, False, {"founder_holds_unknown"})
