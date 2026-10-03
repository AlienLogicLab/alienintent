"""Unit 6c-2: `work launch` through the registry launch composition (acceptance checks 1-8).

Every case runs `WorkRegistry.launcher()` — the existing CliWorkerProvider, RealWorkerProvider, GitWorktreeAdapter,
ProcOwnership, RoleBindingGuard and FactoryCoordinator chain — over the READY-view fixture of test_work_registry, with
its configuration loaded from a file, a local clone with a local bare remote and the repository's own
feature-regression runner. The worker executables are fake provider scripts named by a test routing file
(ALIENINTENT_MODEL_ROUTING); they record their argv, standard input, environment and process group, read the package
the instruction text names, run its `context_command` (and the same call with another contract digest), then commit
and write a self-review (PRODUCER) or write a verdict (VERIFIER). No model is called. Packet texts, labels, markers and
review texts are TEST DATA.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
import sys

import pytest

from alienintent.composition import work_registry
from alienintent.composition.model_routing import provider_command
from alienintent.composition.work_registry import WorkRegistry, launch_root, load_project_configuration
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.domain.release import ReleaseSource
from tests.composition.test_work_registry import ReadyBoard
from tests.context_assembly.test_initial_compilation import PROJECT, git
from tests.context_assembly.test_work_contract import contract_payload
from tests.context_assembly.test_work_identity_service import commit_file
from tests.support.feature_regressions import VERIFICATION, seed_verification_runner

SOURCE = Path(__file__).resolve().parents[2] / "src"
REVIEW = "SELF-REVIEW-TEXT-6c2: every acceptance check passes."
MARKER = "PRODUCER-OUTPUT-MARKER-6c2"
QUOTE = "I authorize implementation of this unit exactly as approved."
OTHER_DIGEST = "sha256:" + "0" * 64
# What check 8 allows in the worker's environment: the allowlist, the two variables the context command names and
# the existing ownership markers.
ALLOWED = {"PATH", "HOME", "LANG", "LC_ALL", "TERM", "SHELL", "USER", "TMPDIR", "GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL",
           "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL", "ALIENINTENT_PROJECT_CONFIGURATION", "ALIENINTENT_PROJECT",
           "ALIENINTENT_INVOCATION_ID", "ALIENINTENT_ROLE", "ALIENINTENT_INVOCATION_OWNER"}

FAKE_PROVIDER = r'''#!{python}
"""FAKE PROVIDER (test data): records what it receives and acts as the instruction text says."""
import json, os, subprocess, sys
from pathlib import Path
records, mode = Path({records!r}), Path({mode!r})
text = sys.stdin.read()
lines = text.splitlines()
package_path = lines[lines.index("Your context package is this JSON file:") + 1]
package = json.loads(Path(package_path).read_text())
command = package["context_command"]
env = dict(os.environ) | command["environment"]
own = subprocess.run(command["argv"], env=env, capture_output=True, text=True)
argv = list(command["argv"])
argv[argv.index("--contract-digest") + 1] = {other!r}
other = subprocess.run(argv, env=env, capture_output=True, text=True)
head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
role = os.environ.get("ALIENINTENT_ROLE")
record = {{"argv": sys.argv, "stdin": text, "env": dict(os.environ), "cwd": os.getcwd(), "head": head,
          "group_leader": os.getpgid(0) == os.getpid(), "package_path": package_path, "package": package,
          "own_context": own.stdout, "other_context": other.stdout}}
records.mkdir(exist_ok=True)
(records / f"{{role}}-{{len(list(records.iterdir()))}}.json").write_text(json.dumps(record))
if role == "PRODUCER":
    Path("launch-candidate.txt").write_text("candidate\n")
    subprocess.run(["git", "add", "launch-candidate.txt"], check=True)
    subprocess.run(["git", "-c", "commit.gpgsign=false", "commit", "-qm", "candidate"], check=True)
    review = lines[next(i for i, line in enumerate(lines) if line.endswith("to this file:")) + 1]
    if not (mode.exists() and mode.read_text() == "no-review"):
        Path(review).write_text({review!r})
    print({marker!r})
else:
    Path(".alienintent").mkdir(exist_ok=True)
    Path(".alienintent/verdict.json").write_text(json.dumps({{"revision": head, "verdict": "accept", "findings": []}}))
'''


def routing(codex: str, claude: str, roles: dict | None = None, model: str = "model-a") -> dict:
    return {"schemaVersion": 1, "default": {"provider": "codex", "model": model},
            "providers": {"codex": {"executable": codex, "permissionMode": "danger-full-access"},
                          "claude": {"executable": claude, "permissionMode": "bypassPermissions"}},
            "roles": roles or {}}


def payload(**changes):
    """A contract that states both launch limits, needs only admitted capabilities and reaches ACCEPT."""
    return lambda item: contract_payload(item.id, **({
        "budget_policy": {"maximum_attempts": 1, "hard_wall_clock_seconds": 120, "cancellation_limit": 1},
        "authority_references": ["README.md"], "required_evidence": ["artifact-verified"]} | changes))


class Launch(ReadyBoard):
    """The READY-view fixture with its configuration in a file, the feature-regression runner on `main`, a WIP limit,
    the fake providers named by a test routing file and a stand-in for the installed `alienintent` script."""

    def __init__(self, root: Path, monkeypatch) -> None:
        super().__init__(root)
        self.root = root
        seed_verification_runner(self.clone)
        git(self.clone, "add", *VERIFICATION)
        git(self.clone, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "-c",
            "commit.gpgsign=false", "commit", "-qm", "feature-regression runner")
        self.configuration_file = root / "project.json"
        self.configuration_file.write_text(json.dumps(self.document))
        self.host = root / "factory-director-host.json"
        self.host.write_text(json.dumps({"wipLimit": 3}))
        self.records, self.mode = root / "worker-records", root / "worker-mode"
        bin_dir = root / "bin"
        bin_dir.mkdir()
        # Stands in for the installed console script (6c-1 check 7 proves the real install), answering its own path
        # as the installed executable the way an installed script does.
        script = bin_dir / "alienintent"
        script.write_text(f"#!{sys.executable}\nimport sys\nfrom pathlib import Path\n"
                          f"sys.path.insert(0, {str(SOURCE)!r})\n"
                          "from alienintent.composition import work_registry\n"
                          "work_registry.installed_executable = lambda: Path(sys.argv[0])\n"
                          "from alienintent.control_plane.adapters.cli import main\nsys.exit(main())\n")
        script.chmod(0o755)
        monkeypatch.setattr(work_registry, "installed_executable", lambda: script)
        self.codex, self.claude = bin_dir / "fake-codex", bin_dir / "fake-claude"
        for fake in (self.codex, self.claude):
            fake.write_text(FAKE_PROVIDER.format(python=sys.executable, records=str(self.records),
                                                 mode=str(self.mode), other=OTHER_DIGEST, review=REVIEW,
                                                 marker=MARKER))
            fake.chmod(0o755)
        self.routing = root / "model-routing.json"
        self.route(routing(str(self.codex), str(self.claude)))
        monkeypatch.setenv("ALIENINTENT_MODEL_ROUTING", str(self.routing))

    def route(self, document: dict | None) -> None:
        if document is None:
            self.routing.unlink(missing_ok=True)
        else:
            self.routing.write_text(json.dumps(document))

    def loaded(self) -> WorkRegistry:
        """A registry built as `work launch` builds it in its own process."""
        return WorkRegistry(load_project_configuration(self.configuration_file, PROJECT), transport=self.github,
                            host_configuration=self.host)

    def launch(self, identity: str):
        return self.loaded().launcher().launch(identity)

    def authorized(self, label: str, authorize: bool = True, **changes):
        item = self.ready(label, at=f"2026-10-03T10:00:0{len(self.github.fields)}Z", payload=payload(**changes))
        if authorize:
            [entry] = [a for a in self.registry.assessment.consumer.history(item.id)
                       if a["raw_ref"] == asdict(item.assessment_ref)]
            assert self.registry.authorization.authorize(item.id, item.pointer.commit, entry["attempt_id"],
                                                         self.main(), QUOTE).answer is None
        return self.stored(label)

    def main(self) -> str:
        return git(self.clone, "rev-parse", "main").decode().strip()

    def runs(self, role: str | None = None) -> list[dict]:
        found = sorted(self.records.glob("*.json"), key=lambda p: int(p.stem.rsplit("-", 1)[1])) \
            if self.records.exists() else []
        values = [json.loads(path.read_text()) for path in found]
        return [value for value in values if role is None or value["env"]["ALIENINTENT_ROLE"] == role]

    @property
    def store(self):
        return self.registry.assessment.consumer.store

    def wip_held(self, identity: str) -> bool:
        return any((r.scope, r.key) == ("wip", identity) for r in self.store.recovery_reservations("registry"))

    def journal_findings(self, identity: str) -> list[str]:
        journal = launch_root(self.loaded().configuration) / "invocation-journal.jsonl"
        lines = journal.read_text().splitlines() if journal.exists() else []
        return [finding for record in map(json.loads, lines) if record.get("event") == "invocation-outcome"
                and record.get("work_identity") == identity for finding in record.get("findings", [])]

    def dump(self) -> str:
        connection = sqlite3.connect(self.root / "readiness.sqlite")
        try:
            return "\n".join(connection.iterdump())
        finally:
            connection.close()


@pytest.fixture
def fx(tmp_path, monkeypatch) -> Launch:
    return Launch(tmp_path / "fx", monkeypatch)


def held(answer: str, reason: str, *refs: str) -> None:
    document = json.loads(answer)
    assert (document["status"], document["reason"], document["affected_refs"][:len(refs)]) == ("HOLD", reason, list(refs))


def test_one_step_per_launch_each_role_gets_its_package_model_and_starting_revision(fx):
    """Checks 1-4 and 6-8 over a PRODUCER launch, a VERIFIER launch and a launch at ACCEPT."""
    item = fx.authorized("UNIT")
    baseline = fx.main()  # the release record's starting revision
    other = fx.authorized("OTHER")  # Released too, eligible and never run by `work launch UNIT`.
    fx.store.commit("registry", f"release:{other.id}", 0, {"identity": other.id, "source": ReleaseSource.EXPLICIT_HUMAN})
    later = commit_file(fx.clone, "main", "docs/later.md", b"a commit added after the release record\n")

    # --- the PRODUCER step
    summary = fx.launch(item.id)
    assert summary.dispatched == (item.id,) and summary.authority_blocked == () and summary.failed == ()
    registry = fx.loaded()
    coordinator = registry.coordinator(None, None)
    assert coordinator.state(item.id).stage is LifecycleStage.VERIFY  # waits for the next `work launch`
    with pytest.raises(KeyError):
        coordinator.state(other.id)  # check 6: the other released work item was not run
    [producer] = fx.runs()
    workspace = Path(producer["cwd"])
    # Check 2: the existing provider command for the route read at this launch; the instruction text on stdin.
    route = {"provider": "codex", "model": "model-a", "executable": str(fx.codex), "permissionMode": "danger-full-access"}
    assert producer["argv"] == provider_command(route, workspace) == [
        str(fx.codex), "exec", "--ephemeral", "--json", "--sandbox", "danger-full-access", "-C", str(workspace),
        "--model", "model-a", "-"]
    assert producer["stdin"].startswith(f"You are the PRODUCER for AlienIntent work item {item.id}")
    # Check 3: the worktree starts at the release record's baseline; the later default-branch commit is not in it.
    assert producer["head"] == baseline != later == fx.main()
    # Check 1: the package at the stated path, outside the worktree, is the PRODUCER's for this attempt.
    package = producer["package"]
    assert Path(producer["package_path"]).parent == launch_root(registry.configuration) / "context"
    assert not Path(producer["package_path"]).is_relative_to(workspace)
    assert (package["status"], package["role"], package["identity"], package["attempt"]) == (
        "PACKAGE", "PRODUCER", item.id, 0)
    assert package["starting_revision"] == baseline
    # Check 4: the worker's own context call gets exactly this package; another contract digest is held.
    assert json.loads(producer["own_context"]) == package
    held(producer["other_context"], "DIGEST_MISMATCH", "contract_digest")
    # Check 8: an owned process group, the allowlisted environment only, and the worktree cleaned up.
    assert producer["group_leader"] is True and set(producer["env"]) <= ALLOWED
    assert producer["env"]["ALIENINTENT_INVOCATION_ID"] == package["resources"]["repository"]["owner"]
    assert not workspace.exists()

    # --- the VERIFIER step, after the routing file changed between launches
    fx.route(routing(str(fx.codex), str(fx.claude), {"VERIFIER": {"provider": "claude", "model": "model-b"}}))
    summary = fx.launch(item.id)
    assert summary.dispatched == () and summary.authority_blocked == ()
    state = fx.loaded().coordinator(None, None).state(item.id)
    assert state.stage is LifecycleStage.ACCEPT
    [_, verifier] = fx.runs()
    clone = Path(verifier["cwd"])
    assert verifier["argv"] == [str(fx.claude), "-p", "--no-session-persistence", "--output-format", "json",
                                "--permission-mode", "bypassPermissions", "--model", "model-b"]
    assert verifier["stdin"].startswith(f"You are the VERIFIER for AlienIntent work item {item.id}")
    package = verifier["package"]
    assert (package["role"], package["candidate"]["locator"]) == ("VERIFIER", state.candidate.locator)
    assert verifier["head"] == state.candidate.locator.rpartition("@")[2]
    assert "launch-candidate.txt" in package["diff"]["text"]
    # Check 7: the self-review is recorded against the stored candidate and arrives under its own field only.
    assert package["producer_self_review"]["text"] == REVIEW
    assert REVIEW not in json.dumps(package["history"]) and MARKER not in json.dumps(package)
    assert json.loads(verifier["own_context"]) == package
    held(verifier["other_context"], "DIGEST_MISMATCH", "contract_digest")
    assert verifier["group_leader"] is True and set(verifier["env"]) <= ALLOWED
    assert clone.name == f"verifier-{verifier['env']['ALIENINTENT_INVOCATION_ID']}"

    # --- at ACCEPT: CLOSURE is not automated and nothing is written
    before = fx.dump()
    assert fx.launch(item.id) == "closure-not-automated"
    assert fx.dump() == before and len(fx.runs()) == 2
    with pytest.raises(KeyError):
        fx.loaded().coordinator(None, None).state(other.id)


def test_no_inherited_credential_or_alienintent_value_reaches_the_worker(fx, monkeypatch):
    """Check 8: an API key, a publication credential and an inherited ALIENINTENT_* value stay with the operator."""
    item = fx.authorized("ENV")
    for name, value in (("ANTHROPIC_API_KEY", "payg"), ("OPENAI_API_KEY", "payg"), ("GH_TOKEN", "publish"),
                        ("GIT_CONFIG_COUNT", "1"), ("GIT_CONFIG_KEY_0", "http.extraHeader"),
                        ("GIT_CONFIG_VALUE_0", "Authorization: Bearer publish"),
                        ("ALIENINTENT_SANDBOX_STATE", "/elsewhere")):
        monkeypatch.setenv(name, value)
    fx.launch(item.id)
    [run] = fx.runs()
    assert set(run["env"]) <= ALLOWED
    assert run["env"]["ALIENINTENT_PROJECT_CONFIGURATION"] == str(fx.configuration_file.resolve())


def test_a_routing_change_between_launches_changes_the_next_command_of_the_same_role(fx):
    """Check 2: the route is read at every launch, with no cache, including in the same process."""
    first, second = fx.authorized("FIRST"), fx.authorized("SECOND")
    launcher = fx.loaded()
    launcher.launcher().launch(first.id)
    fx.route(routing(str(fx.codex), str(fx.claude), model="model-c"))
    launcher.launcher().launch(second.id)
    assert [run["argv"][run["argv"].index("--model") + 1] for run in fx.runs("PRODUCER")] == ["model-a", "model-c"]


def _no_routing(fx):
    fx.route(None)


def _invalid_routing(fx):
    fx.routing.write_text("{not json")


def _unusable_route(fx):
    fx.route(routing(str(fx.codex), str(fx.claude), {"PRODUCER": {"provider": "gemini"}}))


def _evidence_differs(fx, item):
    """The release record no longer names the evidence record the work item's approval_ref holds (an authorized
    item's pointer is fixed, so a differing record is the reachable mismatch)."""
    aggregate = f"release-authorization:{item.id}"
    version, raw = fx.store.read_state("registry", aggregate)
    fx.store.commit("registry", aggregate, version, raw | {"record_ref": "sha256:" + "1" * 64})


@pytest.mark.parametrize(("case", "reason"), [
    ("no-release-record", "release-precondition:implementation-authorized"),
    ("release-evidence-differs", "DIGEST_MISMATCH: release_record, record_ref"),
    ("context-hold", "MISSING_RECORD: design_rules, missing-reference.md"),
    ("no-budget-limits", "MISSING_RECORD: budget_policy"),
    ("no-routing-file", "model-routing-unavailable: PRODUCER: FileNotFoundError"),
    ("invalid-routing", "model-routing-unavailable: PRODUCER: JSONDecodeError"),
    ("no-usable-route", "model-routing-unavailable: PRODUCER: ValueError: MODEL_ROUTING_INVALID")])
def test_missing_or_mismatched_facts_prevent_the_producer_launch(fx, case, reason):
    """Check 5 (PRODUCER): an authority block naming the reason, no worker process, any WIP slot kept, and the next
    `work launch` answers not-eligible instead of launching again."""
    changes = {"context-hold": {"authority_references": ["missing-reference.md"]},
               "no-budget-limits": {"budget_policy": {"maximum_attempts": 1}}}.get(case, {})
    item = fx.authorized("HELD", authorize=case != "no-release-record", **changes)
    if case == "release-evidence-differs":
        _evidence_differs(fx, item)
    {"no-routing-file": _no_routing, "invalid-routing": _invalid_routing,
     "no-usable-route": _unusable_route}.get(case, lambda fx: None)(fx)

    summary = fx.launch(item.id)

    assert summary.authority_blocked == (item.id,) and fx.runs() == []
    state = fx.loaded().coordinator(None, None).state(item.id)
    assert state.outcome == "authority-block"
    if case == "no-release-record":  # the coordinator's own release-gate record, before WIP admission
        assert state.record["hold_reason"] == reason and not fx.wip_held(item.id)
    else:  # a journaled worker outcome keeping its reason as its one finding, and the WIP slot kept
        [finding] = fx.journal_findings(item.id)
        assert finding.startswith(reason) and fx.wip_held(item.id)
        assert state.record["outcome_kind"] == "authority-block"
        _, inbox = fx.store.read_state("registry", "decision-inbox")
        assert inbox["open"][item.id]["reason"] == finding
    fx.route(routing(str(fx.codex), str(fx.claude)))
    assert fx.launch(item.id) == "not-eligible" and fx.runs() == []


@pytest.mark.parametrize("case", ["no-self-review", "recording-fails"])
def test_a_verifier_without_the_self_review_is_not_launched(fx, monkeypatch, case):
    """Check 5 (VERIFIER) and change 5: a missing self-review file, or a recording that fails, records nothing and
    never fails the PRODUCER's launch; the VERIFIER is then held MISSING_RECORD producer_self_review."""
    if case == "no-self-review":
        fx.mode.write_text("no-review")
    else:
        def failing(*_):
            raise RuntimeError("the evidence store is unavailable")
        monkeypatch.setattr(work_registry.WorkContext, "record_self_review", failing)
    item = fx.authorized("NOREVIEW")
    assert fx.launch(item.id).dispatched == (item.id,)
    assert fx.loaded().coordinator(None, None).state(item.id).stage is LifecycleStage.VERIFY

    summary = fx.launch(item.id)

    assert summary.authority_blocked == (item.id,) and fx.runs("VERIFIER") == []
    [finding] = fx.journal_findings(item.id)[-1:]
    assert finding.startswith("MISSING_RECORD: producer_self_review") and fx.wip_held(item.id)
    assert fx.launch(item.id) == "not-eligible" and fx.runs("VERIFIER") == []


def test_a_work_item_outside_the_ready_view_is_not_eligible(fx):
    item = fx.authorized("ABSENT")
    fx.github.fields[item.card_id]["Status"] = "IMPLEMENT"
    assert fx.launch(item.id) == "not-eligible" and fx.runs() == []
