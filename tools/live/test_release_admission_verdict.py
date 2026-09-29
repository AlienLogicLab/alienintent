"""The dispatcher's JSON adapter over the release-admission gate (scripts/release-admission-verdict).

The gate decides; the adapter substitutes the dispatcher's live-claim count for the raw
state file (a record whose worker is gone must not occupy WIP) and adds the Director-host
pause flag and Founder holds, failing closed when either cannot be read.
"""
import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_loader = importlib.machinery.SourceFileLoader("release_admission_verdict", str(ROOT / "scripts" / "release-admission-verdict"))
_spec = importlib.util.spec_from_loader(_loader.name, _loader)
verdict = importlib.util.module_from_spec(_spec)
_loader.exec_module(verdict)

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
        seen["host_config"] = verdict.release_admission.HOST_CONFIG
        return dict(facts or GOOD, issue=number, active_claims_total=99, active_invocations=["stale#55:PRODUCER"])

    monkeypatch.setattr(verdict.release_admission, "gather", gather)
    assert verdict.main(["--issue", str(issue), "--director-host-config", str(host), "--active-claims", str(active)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert seen["host_config"] == host
    return result, {f["check"] for f in result["failures"]}


def test_admits_on_live_claim_count_not_raw_state(tmp_path, monkeypatch, capsys):
    result, checks = run(tmp_path, monkeypatch, capsys, holds=[])
    assert result["admitted"] is True and checks == set()


def test_live_claims_at_the_limit_refuse_capacity(tmp_path, monkeypatch, capsys):
    _, checks = run(tmp_path, monkeypatch, capsys, holds=[], active=1)
    assert checks == {"wip_capacity_available"}


def test_gate_refusals_pass_through_typed(tmp_path, monkeypatch, capsys):
    _, checks = run(tmp_path, monkeypatch, capsys, holds=[], facts=dict(GOOD, agent_ready="HOLD", open_dependencies=[9]))
    assert checks == {"agent_ready", "dependencies_satisfied"}


def test_founder_hold_and_pause_refuse(tmp_path, monkeypatch, capsys):
    _, checks = run(tmp_path, monkeypatch, capsys, holds=[{"issue": 55, "kind": "FOUNDER_DECISION", "reason": "r"}], paused=True)
    assert checks == {"founder_hold", "factory_paused"}


def test_unreadable_hold_record_fails_closed(tmp_path, monkeypatch, capsys):
    result, checks = run(tmp_path, monkeypatch, capsys, holds=None)
    assert result["admitted"] is False and checks == {"founder_holds_unknown"}
