"""Release admission reads work units and execution packets from the release point (Issue #83,
BRD-83), and binds the Agent Ready receipt to them (SF-REQ-002 amendment 2026-09-29).

The #83 fault: a record landed on origin/main was invisible to the gate because the gate read the
shared checkout's working tree, which had not pulled it. #80 and #81 were then released only
with a hand-made native-receipt comment. The same rule now covers what the receipt is bound to:
the work-unit document whose digest the receipt carries, and the execution packet that names the
exact baseline, are read at the release point, never from a working tree.

Every test here runs the real CLI against a disposable world: a bare `origin` repository, a
separate clone standing in for the shared checkout, and a fake `gh` that answers from a JSON
file and logs each call. Nothing reaches GitHub, the live Project or the live state file.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

GATE = Path(__file__).with_name("release_admission.py")
ISSUE = 901
OPERATOR = "sanookdu"
UNIT_DIR = "docs/work-units/wave2"
PACKET_DIR = "docs/evidence/wave2-execution-packets"
DOCUMENT = "# {unit}\nThe task packet exactly as Agent Ready assessed it.\n"
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


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def receipt(unit: str, input_sha256: str, disposition: str = "READY", **overrides) -> str:
    record = {"record_kind": "ReadinessAssessment", "outcome": "ASSESSED", "disposition": disposition,
              "work_unit_id": unit, "provenance": {"producer": "agent-ready-cli", "input_sha256": input_sha256}}
    record.update(overrides)
    return f"Native Agent Ready receipt.\n<!-- AGENT_READY_ASSESSMENT: {json.dumps(record)} -->"


class World:
    def __init__(self, root: Path):
        self.root = root
        self.env = {**os.environ,
                    "HOME": str(root / "home"),
                    "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@invalid",
                    "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@invalid",
                    "PATH": f"{root / 'bin'}{os.pathsep}{os.environ['PATH']}",
                    "FAKE_GH_ISSUE": str(root / "issue.json"),
                    "FAKE_GH_PROJECT": str(root / "project.json"),
                    "FAKE_GH_LOG": str(root / "gh.log")}
        self.env.pop("ALIENINTENT_WORKDIR", None)
        (root / "home").mkdir()
        (root / "bin").mkdir()
        # Isolated wipLimit, operators and active-claims state so admission is not affected by
        # the real host's configuration or currently running invocations.
        host_config_dir = root / "home" / ".config" / "alienintent"
        host_config_dir.mkdir(parents=True)
        (host_config_dir / "self-hosting.json").write_text(json.dumps(
            {"operator": {"authorizedGithubLogins": [OPERATOR]}}))
        (host_config_dir / "factory-director-host.json").write_text(json.dumps(
            {"wipLimit": 1, "selfHostingConfig": str(host_config_dir / "self-hosting.json")}))
        runtime_state_dir = root / "home" / ".local" / "state" / "alienintent"
        runtime_state_dir.mkdir(parents=True)
        (runtime_state_dir / "state.json").write_text(json.dumps({"active": {}}))
        gh = root / "bin" / "gh"
        gh.write_text(FAKE_GH.format(python=sys.executable))
        gh.chmod(0o755)
        (root / "project.json").write_text(json.dumps({"items": [
            {"id": "PVTI_parent", "content": {"number": 23}, "priority": "P1", "status": "PLAN"},
            {"id": "PVTI_child", "content": {"number": ISSUE}, "priority": "P1", "status": "READY"},
        ]}))

        self.origin, self.seed, self.work = root / "origin.git", root / "seed", root / "work"
        self.git(root, "init", "-q", "--bare", "-b", "main", str(self.origin))
        self.git(root, "init", "-q", "-b", "main", str(self.seed))
        (self.seed / "README").write_text("fixture\n")
        self.git(self.seed, "add", "README")
        self.git(self.seed, "commit", "-q", "-m", "baseline")
        self.git(self.seed, "remote", "add", "origin", str(self.origin))
        self.git(self.seed, "push", "-q", "origin", "main")
        self.baseline = self.git(self.seed, "rev-parse", "HEAD").strip()
        # The "shared checkout": cloned now, never pulled afterwards.
        self.git(root, "clone", "-q", str(self.origin), str(self.work))

    def git(self, cwd, *args) -> str:
        return subprocess.run(["git", *args], cwd=cwd, env=self.env, check=True,
                              capture_output=True, text=True).stdout

    def files(self, unit: str, directory: str = UNIT_DIR, document: str | None = None,
              baseline: str | None = None) -> dict[str, str]:
        text = DOCUMENT.format(unit=unit) if document is None else document
        packet = {"biu_id": unit, "starting_authority": {"baseline_sha": baseline or self.baseline}}
        return {f"{directory}/{unit}.md": text, f"{PACKET_DIR}/{unit}.packet.json": json.dumps(packet)}

    def land(self, unit: str, **files_options) -> str:
        """Commit a work unit and its packet on origin/main from elsewhere; the shared checkout
        does not see it. Returns the document's digest."""
        files = self.files(unit, **files_options)
        for path, text in files.items():
            target = self.seed / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
            self.git(self.seed, "add", path)
        self.git(self.seed, "commit", "-q", "-m", f"land {unit}")
        self.git(self.seed, "push", "-q", "origin", "main")
        return digest(next(text for path, text in files.items() if path.endswith(".md")))

    def issue(self, body: str = "", comments: tuple[str, ...] = (), author: str = OPERATOR) -> None:
        payload = {"body": body, "labels": [],
                   "comments": [{"author": {"login": author}, "body": text} for text in comments],
                   "projectItems": [{"title": "AlienIntent", "status": {"name": "READY"}}]}
        (self.root / "issue.json").write_text(json.dumps(payload))

    def assessed(self, unit: str, input_sha256: str | None = None, **overrides) -> None:
        """The Issue carries the operator's native READY receipt for `unit`."""
        self.issue(comments=(receipt(unit, input_sha256 or digest(DOCUMENT.format(unit=unit)), **overrides),))

    def admit(self, gate: Path = GATE, cwd: Path | None = None, workdir: Path | None = None, *extra: str):
        env = dict(self.env)
        if workdir is not None:
            env["ALIENINTENT_WORKDIR"] = str(workdir)
        return subprocess.run([sys.executable, str(gate), str(ISSUE), *extra], cwd=cwd or self.root,
                              env=env, capture_output=True, text=True)

    def gh_calls(self) -> list[list[str]]:
        log = self.root / "gh.log"
        return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def _admitted(result) -> bool:
    return result.returncode == 0 and "ADMITTED" in result.stdout


def _refused(result, check: str) -> bool:
    return result.returncode == 1 and f"- {check}:" in result.stdout


def test_a_work_unit_landed_at_the_release_point_but_absent_from_the_checkout_is_found(world):
    world.land("ARP-01")
    world.assessed("ARP-01")
    assert not (world.work / UNIT_DIR / "ARP-01.md").exists()
    assert world.git(world.work, "rev-parse", "origin/main").strip() == world.baseline  # stale ref

    result = world.admit(workdir=world.work)

    assert _admitted(result), result.stdout + result.stderr
    assert "agent_ready=READY" in result.stdout
    assert f"work_unit={UNIT_DIR}/ARP-01.md baseline={world.baseline}" in result.stdout
    assert "(fetched)" in result.stderr
    assert not (world.work / UNIT_DIR / "ARP-01.md").exists()  # read from git, the working tree is untouched


def test_a_work_unit_present_only_in_the_working_tree_is_not_used(world):
    for path, text in world.files("FDH-01").items():
        (world.work / path).parent.mkdir(parents=True, exist_ok=True)
        (world.work / path).write_text(text)
    world.assessed("FDH-01")

    result = world.admit(workdir=world.work)

    assert _refused(result, "receipt_bound") and _refused(result, "baseline_named"), result.stdout
    assert "work_unit=None" in result.stdout


def test_a_work_unit_committed_only_in_the_local_checkout_is_not_used(world):
    for path, text in world.files("FDH-01").items():
        (world.work / path).parent.mkdir(parents=True, exist_ok=True)
        (world.work / path).write_text(text)
        world.git(world.work, "add", path)
    world.git(world.work, "commit", "-q", "-m", "local only, never pushed")
    world.assessed("FDH-01")

    result = world.admit(workdir=world.work)

    assert _refused(result, "receipt_bound"), result.stdout
    assert "work_unit=None" in result.stdout


@pytest.mark.parametrize("unit, directory", [
    ("ARP-01", UNIT_DIR), ("FDH-01", UNIT_DIR), ("WO-220202", UNIT_DIR),
    ("PY-09B", "docs/work-units/python"), ("SF-REQ-057", "docs/work-units")])
def test_a_bound_receipt_for_any_biu_is_admitted(world, unit, directory):
    world.land(unit, directory=directory)
    world.assessed(unit)

    result = world.admit(workdir=world.work)

    assert _admitted(result), result.stdout + result.stderr
    assert f"work_unit={directory}/{unit}.md" in result.stdout


def test_a_task_packet_edited_after_its_ready_assessment_is_refused_until_reassessed(world):
    """SWF-35: the released text is the assessed text. The receipt was for the first version."""
    world.land("WO-220611")
    world.assessed("WO-220611")
    edited = world.land("WO-220611", document=DOCUMENT.format(unit="WO-220611") + "A new requirement.\n")

    stale = world.admit(workdir=world.work)
    world.issue(comments=(receipt("WO-220611", digest(DOCUMENT.format(unit="WO-220611"))),
                          receipt("WO-220611", edited)))
    fresh = world.admit(workdir=world.work)

    assert _refused(stale, "receipt_bound") and "fresh assessment" in stale.stdout, stale.stdout
    assert _admitted(fresh), fresh.stdout + fresh.stderr


def test_an_explicit_release_point_is_read_instead_of_origin_main(world):
    world.land("ARP-01")
    world.git(world.seed, "push", "-q", "origin", f"{world.baseline}:refs/heads/older")
    world.git(world.work, "fetch", "-q", "origin")
    world.assessed("ARP-01")

    older = world.admit(GATE, None, world.work, "origin/older")

    assert _refused(older, "receipt_bound") and "work_unit=None" in older.stdout, older.stdout


def test_a_packet_baseline_that_does_not_resolve_is_refused(world):
    world.land("ARP-01", baseline="0123456789abcdef0123456789abcdef01234567")
    world.assessed("ARP-01")

    assert _refused(world.admit(workdir=world.work), "baseline_resolves")


def test_a_packet_baseline_outside_the_release_point_ancestry_is_refused(world):
    world.git(world.seed, "checkout", "-q", "-b", "side")
    (world.seed / "side").write_text("side\n")
    world.git(world.seed, "add", "side")
    world.git(world.seed, "commit", "-q", "-m", "side")
    side = world.git(world.seed, "rev-parse", "HEAD").strip()
    world.git(world.seed, "push", "-q", "origin", "side")
    world.git(world.seed, "checkout", "-q", "main")
    world.land("ARP-01", baseline=side)
    world.git(world.work, "fetch", "-q", "origin")
    world.assessed("ARP-01")

    assert _refused(world.admit(workdir=world.work), "baseline_ancestral")


def test_a_packet_without_a_baseline_is_refused(world):
    world.land("ARP-01")
    (world.seed / PACKET_DIR / "ARP-01.packet.json").write_text(json.dumps({"starting_authority": {}}))
    world.git(world.seed, "commit", "-q", "-am", "packet without baseline")
    world.git(world.seed, "push", "-q", "origin", "main")
    world.assessed("ARP-01")

    assert _refused(world.admit(workdir=world.work), "baseline_named")


def test_release_prose_without_a_bound_receipt_is_refused(world):
    world.land("ARP-01")
    world.issue(comments=(f"RELEASED. IMPLEMENT is authorized for this BIU. Admission baseline "
                          f"`{world.baseline}` (current origin/main).",))

    result = world.admit(workdir=world.work)

    assert _refused(result, "receipt_bound") and _refused(result, "agent_ready"), result.stdout


def test_a_later_comment_mentioning_released_without_a_baseline_does_not_refuse(world):
    """#125: later comments mentioning RELEASED were taken as the newest release record."""
    digest_ = world.land("WO-220505")
    world.issue(comments=(receipt("WO-220505", digest_), "RELEASED earlier; see the receipt above.",
                          "Director note: released work continues."))

    assert _admitted(world.admit(workdir=world.work))


def test_a_marker_that_is_not_an_agent_ready_assessment_yields_no_disposition(world):
    world.land("ARP-01")
    world.assessed("ARP-01", outcome="EXECUTION_FAILURE")

    result = world.admit(workdir=world.work)

    assert result.returncode == 1 and "agent_ready=None" in result.stdout, result.stdout


def test_a_receipt_from_a_non_operator_is_not_counted(world):
    digest_ = world.land("ARP-01")
    world.issue(comments=(receipt("ARP-01", digest_),), author="drive-by")

    result = world.admit(workdir=world.work)

    assert result.returncode == 1 and "agent_ready=None" in result.stdout, result.stdout


@pytest.mark.parametrize("unit", ["wave2/ARP-01", "../work-units/wave2/ARP-01", "ARP-01.md"])
def test_a_receipt_naming_a_path_instead_of_an_identifier_binds_nothing(world, unit):
    """Issue #83, JC R1: nothing outside the work-unit directories is read. `wave2/ARP-01` would
    reach a real document through `docs/work-units/`; it is refused, not resolved."""
    world.land("ARP-01")
    world.assessed(unit, input_sha256=digest(DOCUMENT.format(unit="ARP-01")))

    result = world.admit(workdir=world.work)

    assert _refused(result, "receipt_bound") and "work_unit=None" in result.stdout, result.stdout


def test_the_repository_is_derived_from_the_gate_location_without_an_override(world):
    world.land("ARP-01")
    world.assessed("ARP-01")
    gate = world.work / "tools/live/release_admission.py"
    gate.parent.mkdir(parents=True)
    shutil.copy(GATE, gate)

    result = world.admit(gate=gate, cwd=world.root)

    assert _admitted(result), result.stdout + result.stderr
    assert f"in {world.work}" in result.stderr


def test_a_live_copy_outside_any_repository_uses_the_current_directory(world):
    world.land("ARP-01")
    world.assessed("ARP-01")
    gate = world.root / "live-copy" / "release_admission.py"
    gate.parent.mkdir()
    shutil.copy(GATE, gate)

    result = world.admit(gate=gate, cwd=world.work)

    assert _admitted(result), result.stdout + result.stderr
    assert f"in {world.work}" in result.stderr


def test_the_gate_only_reads_from_github(world):
    world.land("ARP-01")
    world.assessed("ARP-01")

    world.admit(workdir=world.work)

    verbs = [call[:2] for call in world.gh_calls()]
    assert verbs and all(v in (["issue", "view"], ["project", "item-list"]) or v[0] == "api"
                         for v in verbs), verbs
    assert all("-X" not in call and "--method" not in call for call in world.gh_calls())


def test_a_release_point_shaped_like_an_option_is_never_passed_to_fetch(world):
    world.issue(body="no receipt here")

    result = world.admit(GATE, None, world.work, "origin/--upload-pack=touch PWNED")

    assert result.returncode == 1, result.stdout
    assert not (world.work / "PWNED").exists()
    assert "(not a remote ref)" in result.stderr


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
