"""Release admission reads readiness records from the release point (Issue #83, BRD-83).

The fault: a record landed on origin/main was invisible to the gate because the gate read the
shared checkout's working tree, which had not pulled it. #80 and #81 were then released only
with a hand-made native-receipt comment.

Every test here runs the real CLI against a disposable world: a bare `origin` repository, a
separate clone standing in for the shared checkout, and a fake `gh` that answers from a JSON
file and logs each call. Nothing reaches GitHub, the live Project or the live state file.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

GATE = Path(__file__).with_name("release_admission.py")
ISSUE = 901
RECORD_DIR = "docs/evidence/wave2-readiness-assessments"
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
    print(json.dumps({{"items": []}}))
elif args[:1] == ["api"] and args[1].endswith("/dependencies/blocked_by"):
    print("[]")
else:
    sys.exit(3)
"""


def record_path(biu: str) -> str:
    return f"{RECORD_DIR}/{biu}.2026-09-24T000000.000000Z.assessment.json"


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
                    "FAKE_GH_LOG": str(root / "gh.log")}
        self.env.pop("ALIENINTENT_WORKDIR", None)
        (root / "home").mkdir()
        (root / "bin").mkdir()
        gh = root / "bin" / "gh"
        gh.write_text(FAKE_GH.format(python=sys.executable))
        gh.chmod(0o755)

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

    def land(self, path: str, record: dict = READY_RECORD) -> None:
        """Commit a record on origin/main from elsewhere; the shared checkout does not see it."""
        target = self.seed / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(record))
        self.git(self.seed, "add", path)
        self.git(self.seed, "commit", "-q", "-m", f"land {path}")
        self.git(self.seed, "push", "-q", "origin", "main")

    def issue(self, body: str = "", comments: tuple[str, ...] = ()) -> None:
        release = (f"RELEASED. IMPLEMENT is authorized for this BIU. Admission baseline "
                   f"`{self.baseline}` (current origin/main).")
        payload = {"body": body, "labels": [],
                   "comments": [{"body": text} for text in (*comments, release)],
                   "projectItems": [{"title": "AlienIntent", "status": {"name": "READY"}}]}
        (self.root / "issue.json").write_text(json.dumps(payload))

    def release_with_record(self, path: str, body: str = "") -> None:
        """The Director's release record itself cites the readiness record."""
        release = (f"RELEASED. IMPLEMENT is authorized for this BIU. Admission baseline "
                   f"`{self.baseline}`; native READY record `{path}`.")
        payload = {"body": body, "labels": [], "comments": [{"body": release}],
                   "projectItems": [{"title": "AlienIntent", "status": {"name": "READY"}}]}
        (self.root / "issue.json").write_text(json.dumps(payload))

    def admit(self, gate: Path = GATE, cwd: Path | None = None, workdir: Path | None = None):
        env = dict(self.env)
        if workdir is not None:
            env["ALIENINTENT_WORKDIR"] = str(workdir)
        return subprocess.run([sys.executable, str(gate), str(ISSUE)], cwd=cwd or self.root,
                              env=env, capture_output=True, text=True)

    def gh_calls(self) -> list[list[str]]:
        log = self.root / "gh.log"
        return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def _admitted(result) -> bool:
    return result.returncode == 0 and "ADMITTED" in result.stdout


def test_a_record_landed_at_the_release_point_but_absent_from_the_checkout_is_found(world):
    path = record_path("ARP-01")
    world.land(path)
    world.issue(body=f"Readiness record `{path}`.")
    assert not (world.work / path).exists()
    assert world.git(world.work, "rev-parse", "origin/main").strip() == world.baseline  # stale ref

    result = world.admit(workdir=world.work)

    assert _admitted(result), result.stdout + result.stderr
    assert "agent_ready=READY" in result.stdout
    assert "(fetched)" in result.stderr
    assert not (world.work / path).exists()  # read from git, the working tree is untouched


def test_a_record_present_only_in_the_working_tree_is_not_used(world):
    path = record_path("FDH-01")
    (world.work / path).parent.mkdir(parents=True)
    (world.work / path).write_text(json.dumps(READY_RECORD))
    world.issue(body=f"Readiness record `{path}`.")

    result = world.admit(workdir=world.work)

    assert result.returncode == 1, result.stdout
    assert "agent_ready=None" in result.stdout
    assert "- agent_ready:" in result.stdout


def test_a_record_committed_only_in_the_local_checkout_is_not_used(world):
    path = record_path("FDH-01")
    (world.work / path).parent.mkdir(parents=True)
    (world.work / path).write_text(json.dumps(READY_RECORD))
    world.git(world.work, "add", path)
    world.git(world.work, "commit", "-q", "-m", "local only, never pushed")
    world.issue(body=f"Readiness record `{path}`.")

    result = world.admit(workdir=world.work)

    assert result.returncode == 1, result.stdout
    assert "agent_ready=None" in result.stdout


@pytest.mark.parametrize("biu", ["ARP-01", "FDH-01", "WO-220202"])
@pytest.mark.parametrize("cited_in", ["body", "release_record"])
def test_a_record_for_any_biu_is_admitted_from_the_body_or_the_release_record(world, biu, cited_in):
    path = record_path(biu)
    world.land(path)
    if cited_in == "body":
        world.issue(body=f"**Contract:** docs/work-units/wave2/{biu}.md · readiness record `{path}`")
    else:
        world.release_with_record(path, body=f"**Contract:** docs/work-units/wave2/{biu}.md")

    result = world.admit(workdir=world.work)

    assert _admitted(result), result.stdout + result.stderr
    assert "agent_ready=READY" in result.stdout


def test_an_explicit_release_point_is_read_instead_of_origin_main(world):
    path = record_path("ARP-01")
    world.land(path)
    world.git(world.seed, "push", "-q", "origin", f"{world.baseline}:refs/heads/older")
    world.git(world.work, "fetch", "-q", "origin")
    world.issue(body=f"Readiness record `{path}`.")

    older = subprocess.run([sys.executable, str(GATE), str(ISSUE), "origin/older"], cwd=world.root,
                           env={**world.env, "ALIENINTENT_WORKDIR": str(world.work)},
                           capture_output=True, text=True)

    assert older.returncode == 1 and "agent_ready=None" in older.stdout, older.stdout


def test_the_native_receipt_fallback_is_unchanged_when_no_record_is_cited(world):
    receipt = ("<!-- AGENT_READY_ASSESSMENT: " + json.dumps(READY_RECORD) + " -->")
    world.issue(body="no record path here", comments=(receipt,))

    result = world.admit(workdir=world.work)

    assert _admitted(result), result.stdout + result.stderr
    assert "agent_ready=READY" in result.stdout


def test_the_native_receipt_fallback_is_unchanged_when_the_cited_record_is_absent(world):
    receipt = ("<!-- AGENT_READY_ASSESSMENT: " + json.dumps(READY_RECORD) + " -->")
    world.issue(body=f"Readiness record `{record_path('ARP-01')}`.", comments=(receipt,))

    result = world.admit(workdir=world.work)

    assert _admitted(result), result.stdout + result.stderr


def test_a_cited_record_that_is_not_an_agent_ready_assessment_still_yields_no_disposition(world):
    path = record_path("ARP-01")
    world.land(path, {**READY_RECORD, "outcome": "EXECUTION_FAILURE"})
    world.issue(body=f"Readiness record `{path}`.")

    result = world.admit(workdir=world.work)

    assert result.returncode == 1 and "agent_ready=None" in result.stdout, result.stdout


def test_the_repository_is_derived_from_the_gate_location_without_an_override(world):
    path = record_path("ARP-01")
    world.land(path)
    world.issue(body=f"Readiness record `{path}`.")
    gate = world.work / "tools/live/release_admission.py"
    gate.parent.mkdir(parents=True)
    shutil.copy(GATE, gate)

    result = world.admit(gate=gate, cwd=world.root)

    assert _admitted(result), result.stdout + result.stderr
    assert f"in {world.work}" in result.stderr


def test_a_live_copy_outside_any_repository_uses_the_current_directory(world):
    path = record_path("ARP-01")
    world.land(path)
    world.issue(body=f"Readiness record `{path}`.")
    gate = world.root / "live-copy" / "release_admission.py"
    gate.parent.mkdir()
    shutil.copy(GATE, gate)

    result = world.admit(gate=gate, cwd=world.work)

    assert _admitted(result), result.stdout + result.stderr
    assert f"in {world.work}" in result.stderr


def test_the_gate_only_reads_from_github(world):
    path = record_path("ARP-01")
    world.land(path)
    world.issue(body=f"Readiness record `{path}`.")

    world.admit(workdir=world.work)

    verbs = [call[:2] for call in world.gh_calls()]
    assert verbs and all(v in (["issue", "view"], ["project", "item-list"]) or v[0] == "api"
                         for v in verbs), verbs
    assert all("-X" not in call and "--method" not in call for call in world.gh_calls())
