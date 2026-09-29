"""Release admission end to end: the real CLI against a fake `gh` and an isolated HOME.

Admission reads the Agent Ready disposition from one place, the newest native receipt posted
by an authorized operator, and never from comment prose or a record cited in the Issue body.
Issue #83 once taught the gate to read body-cited records at a release point; live Issues cite
none, and a body-cited record can be older than the current receipt, so that reader is gone.

Nothing here reaches GitHub, the live Project or the live state file.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

GATE = Path(__file__).with_name("release_admission.py")
ISSUE = 901
OPERATOR = "sanookdu"
READY_RECORD = {"record_kind": "ReadinessAssessment", "outcome": "ASSESSED", "disposition": "READY",
                "provenance": {"producer": "agent-ready-cli", "input_sha256": "0" * 64}}
FAKE_GH = """#!{python}
import json, os, sys
args = sys.argv[1:]
with open(os.environ["FAKE_GH_LOG"], "a") as log:
    log.write(json.dumps(args) + "\\n")
if args[:2] == ["issue", "view"]:
    print(open(os.environ["FAKE_GH_ISSUE"]).read())
elif args[:2] == ["project", "item-list"]:
    print(open(os.environ["FAKE_GH_PROJECT"]).read())
elif args[:2] == ["api", "graphql"]:
    print(json.dumps({{"data": {{"repository": {{"issue": {{"parent": {{"number": 23}}}}}}}}}}))
elif args[:1] == ["api"] and args[1].endswith("/dependencies/blocked_by"):
    print("[]")
else:
    sys.exit(3)
"""


def receipt(record: dict = READY_RECORD) -> str:
    return "Native Agent Ready receipt.\n<!-- AGENT_READY_ASSESSMENT: " + json.dumps(record) + " -->"


class World:
    def __init__(self, root: Path):
        self.root = root
        self.env = {**os.environ,
                    "HOME": str(root / "home"),
                    "PATH": f"{root / 'bin'}{os.pathsep}{os.environ['PATH']}",
                    "FAKE_GH_ISSUE": str(root / "issue.json"),
                    "FAKE_GH_PROJECT": str(root / "project.json"),
                    "FAKE_GH_LOG": str(root / "gh.log")}
        (root / "bin").mkdir()
        # Isolated host configuration, operator list and runtime state, so admission is not
        # affected by the real host's configuration or currently running invocations.
        config_dir = root / "home" / ".config" / "alienintent"
        config_dir.mkdir(parents=True)
        self.self_hosting = config_dir / "self-hosting.json"
        self.self_hosting.write_text(json.dumps({"operator": {"authorizedGithubLogins": [OPERATOR]}}))
        (config_dir / "factory-director-host.json").write_text(json.dumps(
            {"wipLimit": 1, "selfHostingConfig": str(self.self_hosting)}))
        state_dir = root / "home" / ".local" / "state" / "alienintent"
        state_dir.mkdir(parents=True)
        (state_dir / "state.json").write_text(json.dumps({"active": {}}))
        gh = root / "bin" / "gh"
        gh.write_text(FAKE_GH.format(python=sys.executable))
        gh.chmod(0o755)
        (root / "project.json").write_text(json.dumps({"items": [
            {"id": "PVTI_parent", "content": {"number": 23}, "priority": "P1", "status": "PLAN"},
            {"id": "PVTI_child", "content": {"number": ISSUE}, "priority": "P1", "status": "READY"},
        ]}))

    def issue(self, body: str = "", comments: tuple[tuple[str, str], ...] = ()) -> None:
        payload = {"body": body, "labels": [],
                   "comments": [{"author": {"login": author}, "body": text, "includesCreatedEdit": False}
                                for author, text in comments],
                   "projectItems": [{"title": "AlienIntent", "status": {"name": "READY"}}]}
        (self.root / "issue.json").write_text(json.dumps(payload))

    def admit(self, *args: str):
        return subprocess.run([sys.executable, str(GATE), *(args or (str(ISSUE),))], cwd=self.root,
                              env=self.env, capture_output=True, text=True)

    def gh_calls(self) -> list[list[str]]:
        log = self.root / "gh.log"
        return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def _admitted(result) -> bool:
    return result.returncode == 0 and "ADMITTED" in result.stdout


def test_a_ready_receipt_admits_without_any_release_prose(world):
    world.issue(body="TASKS is not READY and grants no release authority", comments=((OPERATOR, receipt()),))

    result = world.admit()

    assert _admitted(result), result.stdout + result.stderr
    assert "agent_ready=READY" in result.stdout


def test_a_later_comment_mentioning_released_without_a_baseline_does_not_refuse(world):
    """#125: back-references to an earlier RELEASED order were read as the newest release record."""
    world.issue(comments=((OPERATOR, receipt()),
                          (OPERATOR, "Following the earlier RELEASED next-slot order, nothing changes.")))

    assert _admitted(world.admit())


def test_a_body_cited_record_never_outranks_the_newest_receipt(world):
    older = "docs/evidence/wave2-readiness-assessments/WO-220505.2026-09-26T123342.214094Z.assessment.json"
    world.issue(body=f"Readiness record `{older}` (HOLD).", comments=((OPERATOR, receipt()),))

    assert _admitted(world.admit())


@pytest.mark.parametrize("disposition", ["HOLD", "CLARIFY", "SPLIT"])
def test_a_newest_non_ready_receipt_refuses(world, disposition):
    world.issue(comments=((OPERATOR, receipt()), (OPERATOR, receipt({**READY_RECORD, "disposition": disposition}))))

    result = world.admit()

    assert result.returncode == 1 and f"agent_ready={disposition}" in result.stdout, result.stdout


def test_a_receipt_from_a_non_operator_is_not_counted(world):
    world.issue(comments=(("drive-by", receipt()),))

    result = world.admit()

    assert result.returncode == 1 and "agent_ready=None" in result.stdout, result.stdout


def test_an_unreadable_operator_list_refuses_and_says_so(world):
    world.self_hosting.write_text("{}")
    world.issue(comments=((OPERATOR, receipt()),))

    result = world.admit()

    assert result.returncode == 1 and "assessment unreadable" in result.stdout, result.stdout


def test_the_gate_only_reads_from_github(world):
    world.issue(comments=((OPERATOR, receipt()),))

    world.admit()

    verbs = [call[:2] for call in world.gh_calls()]
    assert verbs and all(v in (["issue", "view"], ["project", "item-list"]) or v[0] == "api"
                         for v in verbs), verbs
    assert all("-X" not in call and "--method" not in call for call in world.gh_calls())


def test_the_cli_takes_only_an_issue_number(world):
    world.issue(comments=((OPERATOR, receipt()),))

    result = world.admit(str(ISSUE), "origin/main")

    assert result.returncode == 2 and "usage" in result.stderr


def _gate_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("release_admission_under_test", GATE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_priority_reconciliation_repairs_blank_child_from_parent(monkeypatch):
    gate = _gate_module()
    items = [
        {"id": "PVTI_parent", "content": {"number": 23}, "priority": "P0"},
        {"id": "PVTI_child", "content": {"number": 120}, "priority": None},
    ]
    refreshed = [
        {"id": "PVTI_parent", "content": {"number": 23}, "priority": "P0"},
        {"id": "PVTI_child", "content": {"number": 120}, "priority": "P0"},
    ]
    monkeypatch.setattr(gate, "_parent_issue_number", lambda root, issue: 23)
    monkeypatch.setattr(gate, "_gh_json", lambda *args: {"items": refreshed})
    writes = []

    class Done:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(gate.subprocess, "run", lambda args, **kwargs: writes.append(args) or Done())
    result = gate.reconcile_inherited_priority("/repo", 120, items)

    assert result == {"status": "REPAIRED", "priority": "P0", "parent_issue": 23}
    assert len(writes) == 1
    assert gate.PRIORITY_FIELD in writes[0]
    assert gate.PRIORITY_OPTIONS["P0"] in writes[0]


def test_priority_reconciliation_is_zero_write_when_already_correct(monkeypatch):
    gate = _gate_module()
    items = [
        {"id": "PVTI_parent", "content": {"number": 23}, "priority": "P0"},
        {"id": "PVTI_child", "content": {"number": 120}, "priority": "P0"},
    ]
    monkeypatch.setattr(gate, "_parent_issue_number", lambda root, issue: 23)
    monkeypatch.setattr(gate.subprocess, "run",
                        lambda *args, **kwargs: pytest.fail("matching priority must not write"))
    assert gate.reconcile_inherited_priority("/repo", 120, items) == {
        "status": "ALREADY_MATCHED", "priority": "P0", "parent_issue": 23}


def test_priority_reconciliation_repairs_drifted_child(monkeypatch):
    gate = _gate_module()
    items = [
        {"id": "PVTI_parent", "content": {"number": 23}, "priority": "P0"},
        {"id": "PVTI_child", "content": {"number": 120}, "priority": "P3"},
    ]
    monkeypatch.setattr(gate, "_parent_issue_number", lambda root, issue: 23)
    monkeypatch.setattr(gate, "_gh_json", lambda *args: {"items": [
        {"id": "PVTI_parent", "content": {"number": 23}, "priority": "P0"},
        {"id": "PVTI_child", "content": {"number": 120}, "priority": "P0"},
    ]})

    class Done:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(gate.subprocess, "run", lambda *args, **kwargs: Done())
    assert gate.reconcile_inherited_priority("/repo", 120, items)["status"] == "REPAIRED"


def test_priority_reconciliation_refuses_to_invent_without_parent(monkeypatch):
    gate = _gate_module()
    items = [{"id": "PVTI_child", "content": {"number": 120}, "priority": None}]
    monkeypatch.setattr(gate, "_parent_issue_number", lambda root, issue: None)
    result = gate.reconcile_inherited_priority("/repo", 120, items)
    assert result == {"status": "UNRESOLVED", "reason": "missing-parent-and-priority"}
