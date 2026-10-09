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
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from alienintent.composition import work_registry
from alienintent.composition.model_routing import provider_command
from alienintent.composition.work_registry import WorkRegistry, launch_root, load_project_configuration
from alienintent.control_plane.application.operator import exclusive_launch_work
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.domain.release import ReleaseSource
from alienintent.invocation_runtime.adapters.git_worktree import ref_safe
from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
from alienintent.invocation_runtime.domain.runtime import workspace_folder
from tests.composition.test_work_registry import ReadyBoard, passing_suite
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
if "--contract-digest" in argv:
    argv[argv.index("--contract-digest") + 1] = {other!r}
    other = subprocess.run(argv, env=env, capture_output=True, text=True)
else:  # the export mode (worker user): the same call for another correlation
    other = subprocess.run(argv, env=env | {{"ALIENINTENT_CORRELATION": "another-invocation"}},
                           capture_output=True, text=True)
head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
role = os.environ.get("ALIENINTENT_ROLE")


def verifier_document():
    """The next step of `verifier-plan.json` (accept when none): exit (no verdict), malformed, reject or accept."""
    steps_path = Path({plan!r}).with_name("verifier-plan.json")
    steps = json.loads(steps_path.read_text()) if steps_path.exists() else []
    step = steps.pop(0) if steps else "accept"
    steps_path.write_text(json.dumps(steps))
    if step == "exit":
        sys.stderr.write("progress line\n" * 500 + "error sending request for url (https://provider.invalid/)\n")
        sys.exit(1)
    if step == "malformed":
        return {{"revision": head, "verdict": "maybe", "findings": []}}
    if step == "reject":
        return {{"revision": head, "verdict": "reject", "findings": ["VERIFIER-REJECT-FINDING"]}}
    return {{"revision": head, "verdict": "accept", "findings": []}}


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
elif role == "CLOSURE":
    plan_path = Path({plan!r})
    plan = json.loads(plan_path.read_text()) if plan_path.exists() else {{}}
    request = lines[next(i for i, line in enumerate(lines) if line.endswith("exactly one JSON file:")) + 1]
    document = {{"identity": package["identity"], "revision": head, "actions": package["closure_actions"]["actions"],
                "findings": []}}
    document.update(plan.get("request", {{}}))
    for key in plan.get("drop", []):
        document.pop(key, None)
    if "raw" in plan:
        Path(request).write_text(plan["raw"])
    elif not plan.get("no_request"):
        Path(request).write_text(json.dumps(document))
    if plan.get("push"):
        subprocess.run(plan["push"], check=True, capture_output=True)
elif "Then write your verdict as one JSON file, to this file:" in lines:
    verdict = lines[lines.index("Then write your verdict as one JSON file, to this file:") + 1]
    Path(verdict).write_text(json.dumps(verifier_document()))
else:
    document = verifier_document()
    Path(".alienintent").mkdir(exist_ok=True)
    Path(".alienintent/verdict.json").write_text(json.dumps(document))
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
        self.records, self.mode, self.plan = root / "worker-records", root / "worker-mode", root / "closure-plan.json"
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
                                                 marker=MARKER, plan=str(self.plan)))
            fake.chmod(0o755)
        self.routing = root / "model-routing.json"
        self.route(routing(str(self.codex), str(self.claude)))
        monkeypatch.setenv("ALIENINTENT_MODEL_ROUTING", str(self.routing))

    def route(self, document: dict | None) -> None:
        if document is None:
            self.routing.unlink(missing_ok=True)
        else:
            self.routing.write_text(json.dumps(document))

    def loaded(self, ownership=None) -> WorkRegistry:
        """A registry built as `work launch` builds it in its own process."""
        return WorkRegistry(load_project_configuration(self.configuration_file, PROJECT), transport=self.github,
                            host_configuration=self.host, ownership=ownership, suite_run=passing_suite)

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
    assert clone.name == f"verifier-{workspace_folder(verifier['env']['ALIENINTENT_INVOCATION_ID'])}"

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


# --- RESTART-CONTINUATION: restart continuation for registry launches -------------------------------------------------

class Owners(ProcOwnership):
    """The existing ProcOwnership, with the owner state or the owned work stated by the test where given."""

    def __init__(self, state: str | None = None, work: tuple[int, ...] | None = None) -> None:
        super().__init__()
        self.state, self.work = state, work

    def owner_state(self, owner):
        return self.state or super().owner_state(owner)

    def owned_work(self, invocation_id, owner=None, **observed):
        return super().owned_work(invocation_id, owner, **observed) if self.work is None else self.work


def work_launch(fx: Launch, identity: str, ownership=None) -> dict:
    registry = fx.loaded(ownership)
    return exclusive_launch_work(registry.launcher, identity, registry.store, registry.ownership)


def dead_owner() -> dict:
    return dict(ProcOwnership().current()) | {"pid": next(p for p in range(4_194_000, 1, -1)
                                                          if not Path(f"/proc/{p}").exists())}


def saved_launch(fx: Launch, identity: str, *, claimed: bool = False) -> str:
    """The store state of a crash after `commit_with_effect` (and, `claimed`, after `claim_effect`), written with
    the store's own calls; the first PRODUCER launch counted its IMPLEMENT cycle in that commit."""
    correlation = f"launch:{identity}:0"
    fx.store.acquire_within("registry", "wip", identity, f"work:{identity}", 3)
    fx.store.acquire("registry", "repository", fx.loaded().configuration.github.repository, correlation)
    fx.store.commit_with_effect("registry", f"factory:{identity}", 0, {
        "stage": "IMPLEMENT", "version": 0, "accepted": False, "closure": [], "candidate": None, "implement_cycles": 1,
        "verify_cycles": 0, "role": "PRODUCER", "invocation_candidate": None}, correlation,
        {"correlation": correlation, "work": identity, "role": "PRODUCER"})
    if claimed:
        fx.store.claim_effect("registry", correlation)
    return correlation


def ran(fx: Launch, identity: str) -> bool:
    return any(identity in run["env"]["ALIENINTENT_INVOCATION_ID"] for run in fx.runs())


def test_restart_continuation_one_launch_at_a_time_both_leaks_and_a_never_started_park(fx, monkeypatch):
    """Checks 0-3 through `work launch` and `work decide`: one launch at a time; the first leak is released with
    nothing written; the second is parked and keeps its slot and counts; `work decide` defers, refuses an unproven
    start, never offers cancel, authorizes without launching, and the next `work launch` is a new correlation; only
    `work launch` runs recovery in the registry profile."""
    from types import SimpleNamespace
    from alienintent.control_plane.adapters import cli
    from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator, NEVER_STARTED
    recovered = []
    original = FactoryCoordinator._recover
    monkeypatch.setattr(FactoryCoordinator, "_recover", lambda self, items: recovered.append(1) or original(self, items))
    fx.host.write_text(json.dumps({"wipLimit": 2}))
    unsaved, parked, other = fx.authorized("UNSAVED"), fx.authorized("PARKED"), fx.authorized("OTHER")
    repository = fx.loaded().configuration.github.repository
    # The first leak: a crash after the repository reservation, before `commit_with_effect`.
    fx.store.acquire_within("registry", "wip", unsaved.id, f"work:{unsaved.id}", 2)
    fx.store.acquire("registry", "repository", repository, f"launch:{unsaved.id}:0")

    # Check 0: a live launcher's reservation (this process) answers LAUNCH_IN_PROGRESS and writes nothing, and its
    # reservation of a launch with no effect is not released; an unknown owner state is never taken over.
    me = "launcher:" + json.dumps(dict(ProcOwnership().current()), sort_keys=True, separators=(",", ":"))
    held = fx.store.acquire("registry", "launch", "registry", me)
    before = fx.dump()
    assert work_launch(fx, other.id) == {"identity": other.id, "answer": "LAUNCH_IN_PROGRESS", "owner_state": "alive"}
    assert work_launch(fx, other.id, Owners("unknown"))["owner_state"] == "unknown"
    assert work_launch(fx, other.id, SimpleNamespace(current=lambda: None)) == {
        "identity": other.id, "answer": "LAUNCH_OWNER_UNAVAILABLE"}
    assert fx.dump() == before and not fx.runs() and not recovered
    fx.store.release("registry", "launch", "registry", me, held.fence)
    fx.store.acquire("registry", "launch", "registry", "launcher:" + json.dumps(dead_owner(), sort_keys=True))

    # Check 1: an ended launcher's reservation is taken over; the unsaved reservation is released, the record is
    # unchanged, no decision is requested and the launch proceeds.
    summary = work_launch(fx, other.id)
    assert summary["dispatched"] == (other.id,) and recovered == [1]
    assert fx.store.read_state("registry", f"factory:{unsaved.id}") == (0, {})
    assert unsaved.id not in fx.store.read_state("registry", "decision-inbox")[1].get("open", {})
    assert {(r.scope, r.key) for r in fx.store.recovery_reservations("registry")} == {
        ("wip", unsaved.id), ("wip", other.id)}

    # Check 2: a crash after `commit_with_effect`, before `claim_effect`, is parked by the next `work launch`.
    correlation = saved_launch(fx, parked.id)
    summary = work_launch(fx, other.id)  # OTHER's VERIFIER step still runs in the same command
    coordinator = fx.loaded().coordinator(None, None)
    assert summary["stop_reason"] != "capacity-unavailable" and coordinator.state(other.id).stage is LifecycleStage.ACCEPT
    state = coordinator.state(parked.id)
    assert (state.outcome, state.implement_cycles, state.verify_cycles) == ("authority-block", 1, 0)
    assert fx.wip_held(parked.id) and not ran(fx, parked.id)
    [request] = fx.loaded().store.read_state("registry", "decision-inbox")[1]["open"].values()
    assert (request["reason"], request["options"]) == (f"{NEVER_STARTED}: {correlation}", ["authorize", "defer"])

    # Check 3: defer keeps it parked (a repeat is a repeat); an unproven start and `cancel` write nothing.
    deferred = fx.loaded().decide(parked.id, "defer", QUOTE)
    assert fx.loaded().decide(parked.id, "defer", QUOTE) == deferred and deferred["answer"] is None
    assert fx.loaded().coordinator(None, None).state(parked.id).outcome == "authority-block"
    before = fx.dump()
    assert fx.loaded(Owners(work=(4242,))).decide(parked.id, "authorize", QUOTE)["answer"] == "START_UNPROVEN"
    with pytest.raises(ValueError):
        fx.loaded().decide(parked.id, "cancel", QUOTE)
    assert fx.dump() == before
    version, inbox = fx.store.read_state("registry", "decision-inbox")
    fx.store.commit("registry", "decision-inbox", version, {"open": {parked.id: request | {"reason": "other"}}})
    before = fx.dump()
    assert fx.loaded().decide(parked.id, "authorize", QUOTE)["answer"] == "START_UNPROVEN"
    assert fx.dump() == before
    fx.store.commit("registry", "decision-inbox", version + 1, inbox)
    # authorize lifts the effect and launches nothing; a repeat is a repeat; the next `work launch` is a new attempt.
    runs = len(fx.runs())
    decided = fx.loaded().decide(parked.id, "authorize", QUOTE)
    assert decided["answer"] is None and decided["decision"]["submission"]["actor"] == "Founder"
    assert fx.loaded().decide(parked.id, "authorize", QUOTE)["decision"] == decided["decision"]
    assert len(fx.runs()) == runs and fx.loaded().coordinator(None, None).state(parked.id).outcome == "decision-recorded"
    assert fx.loaded().decide(other.id, "authorize", QUOTE) == {"answer": "NO_OPEN_DECISION"}
    assert work_launch(fx, parked.id)["dispatched"] == (parked.id,)
    relaunched = fx.loaded().coordinator(None, None).state(parked.id)
    assert relaunched.record["correlation"] != correlation and relaunched.implement_cycles == 1

    # Only `work launch` runs recovery in the registry profile: every other command reaches no coordinator recovery.
    monkeypatch.setattr(cli, "_factory", lambda _: SimpleNamespace(work_registry=fx.loaded()))
    count, mutation = len(recovered), ["--actor", "a", "--authority", "a", "--intent", "i", "--expected-version", "0",
                                       "--reason", "r", "--idempotency-key", "k"]
    for argv in (["run", *mutation], ["resume", parked.id, *mutation], ["reconcile", parked.id, *mutation],
                 ["cancel", parked.id, *mutation], ["stop", *mutation], ["status"], ["explain", parked.id],
                 ["decisions", "list"], ["decisions", "decide", parked.id, "--choice", "authorize", "--biu-version", "0",
                                         *mutation], ["work", "show", parked.id],
                 ["work", "decide", other.id, "--choice", "authorize", "--quote", QUOTE],
                 ["work", "decide", parked.id, "--choice", "cancel", "--quote", QUOTE]):
        cli.main(["--json", "--profile-factory", "x:y", *argv])
    assert len(recovered) == count


def test_restart_continuation_authorize_reconciles_a_started_publication_against_the_remote(fx, monkeypatch):
    """Check 3 after a publish began: `authorize` is refused while the owner runs, is accepted only when the remote
    has no candidate branch and the attestation is `effect-unknown`, and every other remote answer writes nothing."""
    from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
    from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal
    from alienintent.invocation_runtime.domain.runtime import CandidateUnavailable
    item = fx.authorized("PUB")
    correlation = saved_launch(fx, item.id, claimed=True)
    root = launch_root(fx.loaded().configuration)
    worktree = root / "workspaces" / workspace_folder(correlation)
    git(fx.clone, "worktree", "add", "-q", "-b", "invocation/launch-x", str(worktree), "main")
    revision = fx.main()
    journal = JsonlInvocationJournal(root / "invocation-journal.jsonl", lambda: 0.0)
    attribution = {"correlation_id": correlation, "work_identity": item.id, "role": "PRODUCER"}
    journal.append({"event": "invocation-started", **attribution, "contract_digest": None, "owner": dead_owner()})
    journal.append({"event": "publication-started", **attribution, "revision": revision})
    assert work_launch(fx, item.id) == {"identity": item.id, "answer": "not-eligible"}  # recovery parked it
    assert fx.loaded().coordinator(None, None).state(item.id).outcome == "authority-block"
    branch = f"candidate/{ref_safe(correlation)}"
    remote = fx.loaded().configuration.repositories[fx.loaded().configuration.packets_repository].remote

    def refused(answer: str, ownership=None) -> dict:
        before = fx.dump()
        result = fx.loaded(ownership).decide(item.id, "authorize", QUOTE)
        assert result["answer"] == answer and fx.dump() == before
        return result
    assert refused("OWNER_STILL_RUNNING", Owners("alive"))["attestation"] == "owner-alive"
    assert refused("OWNER_STILL_RUNNING", Owners(work=(4242,)))["attestation"] == "owned-work-active"
    git(fx.clone, "push", "-q", remote, f"{revision}:refs/heads/{branch}")
    assert refused("CANDIDATE_PUBLISHED") == {"answer": "CANDIDATE_PUBLISHED", "branch": branch,
                                                   "revision": revision, "correlation": correlation,
                                                   "retained_worktree": str(worktree.resolve())}
    git(fx.clone, "push", "-q", "-f", remote, f"{revision}^:refs/heads/{branch}")
    assert refused("REMOTE_CONFLICT")["revision"] != revision
    git(fx.clone, "push", "-q", remote, f":refs/heads/{branch}")
    assert refused("REMOTE_UNVERIFIED", Owners("unknown"))["attestation"] == "owner-unattested"
    with monkeypatch.context() as patched:
        patched.setattr(GitSourceControl, "remote_revision", lambda *_: (_ for _ in ()).throw(CandidateUnavailable("x")))
        assert refused("REMOTE_UNVERIFIED")["missing"] == "a readable remote"
    worktree.rename(worktree.with_name("moved"))
    assert refused("REMOTE_UNVERIFIED")["missing"] == "the PRODUCER worktree"
    worktree.with_name("moved").rename(worktree)
    decided = fx.loaded().decide(item.id, "authorize", QUOTE)
    assert decided["answer"] is None and decided["retained_worktree"] == str(worktree.resolve())
    assert decided["cleanup_diagnostics"] == {correlation: f"{item.id}: authorized and relaunched"}
    assert fx.loaded().coordinator(None, None).state(item.id).outcome == "decision-recorded" and not ran(fx, item.id)


# --- AUTOMATED-CLOSURE: CLOSURE as a launched step ------------------------------------------------------------------

from alienintent.composition.landing_authority import LANDING_PERMISSIONS, LandingAuthority  # noqa: E402
from alienintent.composition.work_registry import (  # noqa: E402
    DISPLAY_PERMISSIONS, RegistryClosure, landing_record_path, render_landing_record)
from alienintent.context_assembly.domain.work_identity import GitReadFailed  # noqa: E402
from alienintent.control_plane.application.decision_inbox import DecisionInbox
from alienintent.execution_coordination.domain.closure import ACTIONS, receipt  # noqa: E402
from alienintent.installation.ports.github_transport import TransportResponse  # noqa: E402
from tests.support.live_github import (  # noqa: E402
    PRIORITY_FIELD, PRIORITY_OPTIONS, SANDBOX_PROJECT, STATUS_FIELD, STATUS_OPTIONS)

FIXED = {"required_closure_actions": list(ACTIONS)}
SESSION_TEXT = "SESSION-FINDING-TEXT-CLOSURE"


class Closing:
    """The launch fixture with a board that keeps each card's Status, recorded mint bodies and scope-marked tokens,
    and (optionally) landing enabled, its Landing Authority pushing to the local bare remote."""

    def __init__(self, fx: Launch, monkeypatch, *, landing: bool = True) -> None:
        self.fx, self.remote = fx, fx.root / "remote.git"
        self.mints: list[dict | None] = []
        self.ignore_status = False
        self.pushes: list[str] = []
        github, graphql, request = fx.github, fx.github._graphql, fx.github.request

        def board(query: str, variables: dict) -> object:
            if "fields(first:50)" in query:
                return {"data": {"node": {"id": SANDBOX_PROJECT, "number": 2, "title": "board", "fields": {"nodes": [
                    {"id": STATUS_FIELD, "name": "Status", "options": STATUS_OPTIONS},
                    {"id": PRIORITY_FIELD, "name": "Priority", "options": PRIORITY_OPTIONS}]}}}}
            if "updateProjectV2ItemFieldValue" in query:
                if not self.ignore_status:
                    name = next(o["name"] for o in STATUS_OPTIONS if o["id"] == variables["option"])
                    github.fields.setdefault(variables["item"], {})["Status"] = name
                return {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {
                    "id": variables["item"], "project": {"id": SANDBOX_PROJECT, "number": 2}}}}}
            answer = graphql(query, variables)
            node = (answer.get("data") or {}).get("node") if isinstance(answer, dict) else None
            if "ProjectV2Item { id project" in query and isinstance(node, dict):
                status = github.fields.get(variables["item"], {}).get("Status")
                node["fieldValues"] = {"nodes": [{"name": status, "field": {"id": STATUS_FIELD, "name": "Status"}}]
                                       if status else []}
            return answer

        def transport(method, url, headers, body=None):
            response = request(method, url, headers, body)
            if url.endswith("/access_tokens"):
                self.mints.append(json.loads(body) if body else None)
                document = json.loads(response.body)
                scope = "landing" if document.get("permissions", {}).get("contents") == "write" else "display"
                document["token"] = f"ghs-marker-{scope}"
                response = TransportResponse(response.status, json.dumps(document).encode())
            return response

        github._graphql, github.request = board, transport
        remote, pushes = str(self.remote), self.pushes

        class Local(LandingAuthority):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, push_url=remote)

            def land(self, order):
                answer = super().land(order)
                pushes.append(answer)
                return answer

        monkeypatch.setattr(work_registry, "LandingAuthority", Local)
        self.landing(landing)

    def landing(self, enabled: bool) -> None:
        self.fx.document["projects"][PROJECT]["github"]["landing"] = enabled
        self.fx.configuration_file.write_text(json.dumps(self.fx.document))

    def accepted(self, label: str = "UNIT", **changes):
        """An authorized fixed-name item launched through PRODUCER and VERIFIER to ACCEPT."""
        item = self.fx.authorized(label, **(FIXED | changes))
        self.fx.launch(item.id)
        self.fx.launch(item.id)
        assert self.state(item.id).stage is LifecycleStage.ACCEPT
        return item

    def state(self, identity: str):
        return self.fx.loaded().coordinator(None, None).state(identity)

    def close(self, identity: str, ownership=None):
        return self.fx.loaded(ownership if ownership is not None else Owners("terminated")).launcher().launch(identity)

    def plan(self, **plan) -> None:
        self.fx.plan.write_text(json.dumps(plan))

    def head(self) -> str:
        return git(self.remote, "rev-parse", "main").decode().strip()

    def journal(self) -> list[dict]:
        path = launch_root(self.fx.loaded().configuration) / "invocation-journal.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def orders(self, identity: str) -> list[dict]:
        return [r for r in self.journal() if r.get("event") == "closure-ordered" and r["work_identity"] == identity]

    def card(self, identity: str) -> str | None:
        card = self.fx.registry.records.show(identity).item.card_id
        return self.fx.github.fields.get(card, {}).get("Status")


@pytest.fixture
def closing(fx, monkeypatch) -> Closing:
    return Closing(fx, monkeypatch)


def revision_of(state) -> str:
    return state.candidate.locator.rpartition("@")[2]


def test_closure_lands_through_the_authority_with_five_exact_receipts_and_the_row_projected(closing, monkeypatch):
    """Checks 1, 4, 6, 7, 10, 13 and 14 over one real CLOSURE launch."""
    fx = closing.fx
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Borrowed User")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Borrowed User")
    item = closing.accepted()
    accepted = closing.state(item.id)
    revision, base = revision_of(accepted), closing.head()
    fx.route(routing(str(fx.codex), str(fx.claude), {"VERIFIER": {"provider": "claude", "model": "model-v"}}))
    closing.plan(request={"findings": [SESSION_TEXT, f"ready-to-land:{revision}"]})
    closing.close(item.id)
    state = closing.state(item.id)
    # Check 1: DONE through `close`, with the five exact receipts for this item and the accepted revision.
    assert state.stage is LifecycleStage.DONE
    assert state.record["receipts"] == sorted(receipt(a, item.id, revision) for a in ACTIONS)
    # Check 4: a fresh session on the VERIFIER route, in its own clone, with a new correlation and no write grant.
    [session] = fx.runs("CLOSURE")
    assert session["argv"][0] == str(fx.claude) and session["argv"][-1] == "model-v"
    correlation = session["env"]["ALIENINTENT_INVOCATION_ID"]
    assert Path(session["cwd"]).name == f"closure-{workspace_folder(correlation)}" and correlation != accepted.record["verdict"][
        "verifier_correlation"]
    package = session["package"]
    assert {"candidate", "diff", "verdict", "closure_actions"} <= set(package) and "producer_self_review" not in package
    assert package["closure_actions"]["actions"] == list(ACTIONS) and set(session["env"]) <= ALLOWED
    # The landing: record on main, its only parent the merge of (base, candidate) with the candidate's tree.
    record = closing.head()
    [order] = closing.orders(item.id)
    assert order["order"]["record"] == record and order["order"]["base"] == base and closing.pushes == ["pushed"]
    merge = git(closing.remote, "rev-parse", f"{record}^1").decode().strip()
    assert git(closing.remote, "rev-list", "--parents", "-n", "1", merge).decode().split()[1:] == [base, revision]
    assert git(closing.remote, "rev-parse", f"{merge}^{{tree}}") == git(closing.remote, "rev-parse", f"{revision}^{{tree}}")
    identities = git(closing.remote, "log", "--format=%an <%ae>%n%cn <%ce>", "-2", record).decode().splitlines()
    assert set(identities) == {"AlienIntent Landing <landing@alienintent.invalid>"}  # check 7: no borrowed user
    # Check 13: the record's bytes are the deterministic rendering; no session text reaches the remote.
    path = landing_record_path("UNIT", item.id, revision)
    data = git(closing.remote, "show", f"{record}:{path}")
    shown = fx.registry.records.show(item.id)
    assert data == render_landing_record({
        "identity": item.id, "label": "UNIT", "candidate": revision, "base": base, "merge": merge,
        "instructions_sha256": __import__("hashlib").sha256(shown.packet).hexdigest(),
        "verifier_correlation": accepted.record["verdict"]["verifier_correlation"], "closure_correlation": correlation,
        "actions": list(ACTIONS), "request_sha256": order["order"]["request_sha256"]})
    assert SESSION_TEXT.encode() not in git(closing.remote, "log", "-p", "--all")
    assert f"closure-finding: {SESSION_TEXT}" in fx.journal_findings(item.id)
    # Board: the card reads back DONE; check 10: the row projected with a work-completion record.
    assert closing.card(item.id) == "DONE"
    registry = fx.loaded()
    assert registry.identities.find(item.id).state == "DONE" and registry.completion.recorded(item.id)
    assert not fx.wip_held(item.id)
    # Check 14: every workspace of this item's correlations is gone, the landing clone included.
    verifier = launch_root(registry.configuration) / "verifier"
    assert not [p.name for p in verifier.iterdir() if item.id in p.name]
    # Checks 6 and 7: every mint is scoped; no token marker or key reaches a worker, the journal or the record.
    name = SANDBOX_REPOSITORY.split("/")[1]
    assert None not in closing.mints and {json.dumps(m, sort_keys=True) for m in closing.mints} == {
        json.dumps({"permissions": DISPLAY_PERMISSIONS, "repositories": [name]}, sort_keys=True),
        json.dumps({"permissions": LANDING_PERMISSIONS, "repositories": [name]}, sort_keys=True)}
    key = fx.root / "key.pem"
    seen = json.dumps(fx.runs()) + json.dumps(closing.journal()) + data.decode()
    for secret in ("ghs-marker-landing", "ghs-marker-display", str(key), key.read_text().splitlines()[1]):
        assert secret not in seen


from tests.support.live_github import SANDBOX_REPOSITORY  # noqa: E402


def test_without_landing_closure_is_ready_to_land_and_never_blocks_other_work(fx, monkeypatch):
    """Check 11 (and check 4: a routing change reaches the next CLOSURE command)."""
    closing = Closing(fx, monkeypatch, landing=False)
    item = closing.accepted()
    other = fx.authorized("OTHER")
    base = closing.head()
    closing.close(item.id)
    state = closing.state(item.id)
    assert (state.stage, state.outcome) == (LifecycleStage.ACCEPT, "ready-to-land")
    assert closing.head() == base and closing.orders(item.id) == [] and closing.card(item.id) == "READY"
    [session] = fx.runs("CLOSURE")
    clone = Path(session["cwd"])
    assert clone.is_dir() and not fx.wip_held(item.id)
    merge = state.record["ready_to_land"]
    landing = launch_root(fx.loaded().configuration) / "landing" / f"landing-{workspace_folder(session['env']['ALIENINTENT_INVOCATION_ID'])}"
    assert git(landing, "rev-list", "--parents", "-n", "1", merge).decode().split()[1:] == [base, revision_of(state)]
    # Not blocking: with a WIP limit of 1 another item is admitted; a launch without landing starts nothing.
    fx.host.write_text(json.dumps({"wipLimit": 1}))
    assert fx.launch(other.id).dispatched == (other.id,)
    assert closing.close(item.id) == "ready-to-land" and fx.loaded().launcher().start() is not None
    assert len(fx.runs("CLOSURE")) == 1
    # With landing on, the slot is re-acquired first: refused while taken, then a fresh CLOSURE lands.
    closing.landing(True)
    assert closing.close(item.id) == "wip-refused" and closing.state(item.id).outcome == "ready-to-land"
    fx.host.write_text(json.dumps({"wipLimit": 2}))
    fx.route(routing(str(fx.codex), str(fx.claude), {"VERIFIER": {"provider": "codex", "model": "model-c"}}))
    closing.close(item.id)
    assert closing.state(item.id).stage is LifecycleStage.DONE
    assert [r["argv"][r["argv"].index("--model") + 1] for r in fx.runs("CLOSURE")] == ["model-a", "model-c"]


def test_a_failing_landing_runs_closure_once_per_start(closing, monkeypatch):
    """Check 11: with landing on and the Authority refusing every time, one `start()` runs CLOSURE once."""
    item = closing.accepted()
    monkeypatch.setattr(LandingAuthority, "land", lambda self, order: "refused:fixture")
    closing.fx.loaded(Owners("terminated")).launcher().release_and_start(item.id)
    assert len(closing.fx.runs("CLOSURE")) == 1 and closing.state(item.id).outcome == "authority-block"


@pytest.mark.parametrize(("plan", "landed", "outcome"), [
    ({"request": {"actions": ["candidate-published", "merged-to-main", "landing-record", "deploy"]}}, False, "failure"),
    ({"request": {"identity": "another-item"}}, False, "failure"),
    ({"request": {"revision": "0" * 40}}, False, "failure"),
    ({"request": {"extra": 1}}, False, "failure"),
    ({"request": {"actions": ["merged-to-main", "merged-to-main"]}}, False, "failure"),
    ({"request": {"findings": ["x" * 501]}}, False, "failure"),
    ({"no_request": True}, False, "failure"),
    ({"request": {"actions": ["candidate-published", "landing-record", "board-updated", "workspaces-cleaned"]}}, False,
     "authority-block"),
    ({"request": {"actions": ["candidate-published", "merged-to-main", "landing-record"]}}, True, "authority-block"),
    ({"request": {"actions": ["candidate-published"], "findings": [
        "ready-to-land:" + "a" * 40, "closure-rework:base-moved:" + "a" * 40 + ":" + "b" * 40,
        "closure-hold:landing-ambiguous", "merged-to-main:x:" + "a" * 40]}}, False, "authority-block"),
])
def test_the_bounded_request_alone_steers_nothing(closing, plan, landed, outcome):
    """Check 2 (and check 8's request without board-updated): nothing beyond the bounded request is performed and a
    session finding never changes the outcome. A malformed request is a worker failure within the attempt budget
    (here one attempt), never an authority hold."""
    item = closing.accepted()
    base, revision = closing.head(), revision_of(closing.state(item.id))
    closing.plan(**plan)
    closing.close(item.id)
    state = closing.state(item.id)
    assert (state.stage, state.outcome) == (LifecycleStage.ACCEPT, outcome)
    expected = [receipt("candidate-published", item.id, revision)]
    if landed:
        expected += [receipt(a, item.id, revision) for a in ("merged-to-main", "landing-record")]
    assert state.record["receipts"] == sorted(expected)
    assert (closing.head() != base) is landed and closing.card(item.id) == "READY"
    for finding in plan.get("request", {}).get("findings", []):
        if len(finding) <= 500:  # a refused request carries none of its findings
            assert f"closure-finding: {finding}" in closing.fx.journal_findings(item.id)



RETRYING = {"budget_policy": {"maximum_attempts": 3, "hard_wall_clock_seconds": 120, "cancellation_limit": 1}}


def _open_decision(closing: Closing, identity: str) -> bool:
    return identity in (closing.fx.store.read_state("registry", "decision-inbox")[1] or {}).get("open", {})


def test_a_malformed_closure_request_is_retried_on_the_same_candidate_without_a_decision(closing):
    """The 2026-10-09 failure: the session gave the candidate identity, not the bare commit, as `revision`. The item
    stays at ACCEPT with no decision request, and the next launch runs a fresh CLOSURE session that lands."""
    item = closing.accepted(**RETRYING)
    accepted = closing.state(item.id)
    base, revision = closing.head(), revision_of(accepted)
    closing.plan(request={"revision": accepted.candidate.identity})
    closing.close(item.id)
    state = closing.state(item.id)
    assert (state.stage, state.outcome) == (LifecycleStage.ACCEPT, "closure-retry")
    assert (state.record["closure_retries"], state.record["closure_refusal"]) == (1, "request-revision")
    assert not _open_decision(closing, item.id) and closing.head() == base and closing.pushes == []
    [session] = closing.fx.runs("CLOSURE")
    assert "git rev-parse HEAD" in session["package"]["closure_actions"]["request"]["revision"]
    assert "never the package's candidate identity" in session["stdin"]
    closing.plan()
    closing.close(item.id)
    state = closing.state(item.id)
    assert state.stage is LifecycleStage.DONE and closing.head() != base
    assert state.record["receipts"] == sorted(receipt(a, item.id, revision) for a in ACTIONS)
    first, second = closing.fx.runs("CLOSURE")
    assert first["env"]["ALIENINTENT_INVOCATION_ID"] != second["env"]["ALIENINTENT_INVOCATION_ID"]
    assert first["head"] == second["head"] == revision


def test_malformed_closure_requests_end_in_failure_at_the_attempt_budget_never_a_decision(closing):
    item = closing.accepted(**RETRYING)
    base = closing.head()
    closing.plan(request={"revision": "0" * 40})
    for attempt in (1, 2):
        closing.close(item.id)
        assert (closing.state(item.id).outcome, closing.state(item.id).record["closure_retries"]) == (
            "closure-retry", attempt)
    closing.close(item.id)
    state = closing.state(item.id)
    assert (state.stage, state.outcome, state.record["hold_reason"]) == (
        LifecycleStage.ACCEPT, "failure", "attempt-budget-exhausted")
    assert len(closing.fx.runs("CLOSURE")) == 3 and not _open_decision(closing, item.id) and closing.head() == base
    assert closing.close(item.id) is not None and len(closing.fx.runs("CLOSURE")) == 3


def test_a_second_hold_at_the_same_stage_gets_its_own_decision_and_a_replay_stays_idempotent(closing, monkeypatch):
    """The 2026-10-09 failure: at ACCEPT the version never moves, so a second hold's `authorize` reused the first
    decision's key and was taken as a repeat; the request closed and the item stayed blocked with no open decision."""
    fx = closing.fx
    item = closing.accepted()
    original = LandingAuthority.land
    monkeypatch.setattr(LandingAuthority, "land", lambda self, order: "refused:fixture")
    keys = []
    for hold in (1, 2):
        closing.close(item.id)
        assert closing.state(item.id).outcome == "authority-block" and _open_decision(closing, item.id), hold
        assert fx.loaded().decide(item.id, "authorize", QUOTE)["answer"] is None
        state = closing.state(item.id)
        assert state.outcome == "decision-recorded" and not _open_decision(closing, item.id), hold
        keys.append(state.record["decision_key"])
    assert keys[0] != keys[1]
    replay = fx.loaded().decide(item.id, "authorize", QUOTE)
    assert replay["answer"] is None and closing.state(item.id).record == state.record
    registry = fx.loaded()
    inbox = DecisionInbox(registry.store, work_registry._DecisionOnly(registry._launch_chain()[0]), "registry")
    latest = inbox.show(item.id)
    assert inbox.submit(inbox._record_for_key(keys[0]).submission).submission.idempotency_key == keys[0]
    assert inbox.show(item.id) == latest and closing.state(item.id).record == state.record
    monkeypatch.setattr(LandingAuthority, "land", original)
    closing.close(item.id)
    assert closing.state(item.id).stage is LifecycleStage.DONE

def _unrelated(closing: Closing, base: str) -> str:
    """A commit on the remote's base that does not contain the candidate."""
    clone = closing.fx.clone
    git(clone, "fetch", "-q", "origin")
    git(clone, "checkout", "-q", "-b", "unrelated", base)
    sha = commit_file(clone, "unrelated", "docs/unrelated.md", b"unrelated\n")
    git(clone, "checkout", "-q", "main")
    return sha


def test_the_control_plane_trusts_neither_the_session_nor_the_authority(closing, monkeypatch):
    """Check 3 and check 12's non-ancestor rule: a session's own push to main is reworked, never landed; an
    Authority that answers `pushed` without pushing, a record without the instructions sha256 and a card left in
    another column get no receipt."""
    fx = closing.fx
    item = closing.accepted()
    base = closing.head()
    other = _unrelated(closing, base)
    closing.plan(push=["git", "-C", str(fx.clone), "push", "-q", str(closing.remote), f"{other}:refs/heads/main"],
                 request={"findings": ["all effects succeeded"]})
    closing.close(item.id)
    state = closing.state(item.id)
    assert state.stage is LifecycleStage.IMPLEMENT and closing.head() == other
    assert closing.pushes == [] and state.record["rejections"] == 1  # the moved base is never handed over
    assert any(f.startswith("closure-rework:base-moved:") for f in state.record["findings"][-1]["findings"])
    assert item.id not in json.dumps(fx.store.read_state("registry", "decision-inbox")[1])


@pytest.mark.parametrize("fault", ["pushed-without-push", "no-instructions-digest", "card-elsewhere"])
def test_no_receipt_without_read_back(closing, monkeypatch, fault):
    item = closing.accepted()
    revision = revision_of(closing.state(item.id))
    if fault == "pushed-without-push":
        monkeypatch.setattr(LandingAuthority, "land", lambda self, order: "pushed")
    if fault == "no-instructions-digest":
        monkeypatch.setattr(work_registry, "render_landing_record",
                            lambda facts: (facts["identity"] + " " + facts["candidate"] + "\n").encode())
    if fault == "card-elsewhere":
        closing.ignore_status = True
    closing.close(item.id)
    state = closing.state(item.id)
    assert (state.stage, state.outcome) == (LifecycleStage.ACCEPT, "authority-block")
    kept = {r.split(":", 1)[0] for r in state.record["receipts"]}
    missing = {"pushed-without-push": "merged-to-main", "no-instructions-digest": "landing-record",
               "card-elsewhere": "board-updated"}[fault]
    assert missing not in kept and receipt("candidate-published", item.id, revision) in state.record["receipts"]


class Crash(Exception):
    """An injected crash of the launching process."""


def _crash(monkeypatch, target, name, *, after: bool):
    original = getattr(target, name)

    def crashing(self, *args, **kwargs):
        if after:
            original(self, *args, **kwargs)
        raise Crash(name)
    monkeypatch.setattr(target, name, crashing)
    return original


@pytest.mark.parametrize("point", ["before-push", "after-push", "after-board"])
def test_a_crash_is_recovered_from_the_journal_without_a_session(closing, monkeypatch, point):
    """Checks 8, 9 and 10: the next launch of another item settles the begun landing without a model session; a
    card already in DONE does not block recovery; the row is projected."""
    fx = closing.fx
    item = closing.accepted()
    other = fx.authorized("OTHER")
    if point == "after-board":
        original = _crash(monkeypatch, RegistryClosure, "_cleanup", after=False)
    else:
        original = _crash(monkeypatch, LandingAuthority, "land", after=point == "after-push")
    with pytest.raises(Crash):
        closing.close(item.id)
    assert len(closing.orders(item.id)) == 1
    if point == "after-board":
        assert closing.card(item.id) == "DONE"  # gone from the READY view
    monkeypatch.setattr(RegistryClosure if point == "after-board" else LandingAuthority,
                        "_cleanup" if point == "after-board" else "land", original)
    sessions = len(fx.runs())
    summary = closing.close(other.id)
    assert summary.stop_reason != "capacity-unavailable" and summary.dispatched == (other.id,)
    assert len(fx.runs("CLOSURE")) == 1 and len(fx.runs()) == sessions + 1  # only OTHER's PRODUCER ran
    state = closing.state(item.id)
    assert state.stage is LifecycleStage.DONE and closing.card(item.id) == "DONE"
    assert len(closing.orders(item.id)) == 1 and fx.loaded().identities.find(item.id).state == "DONE"
    # Exactly one push reaches the remote: the retried order (before-push), the crashed one (after-push: the crash
    # hid its answer and recovery pushes nothing), or the original (after-board).
    assert closing.pushes == {"before-push": ["pushed"], "after-push": [], "after-board": ["pushed"]}[point]
    assert git(closing.remote, "rev-parse", "main").decode().strip() == closing.orders(item.id)[0]["order"]["record"]


def test_a_request_without_board_update_crashing_after_the_push_recovers_without_moving_the_card(closing, monkeypatch):
    item = closing.accepted()
    other = closing.fx.authorized("OTHER")
    closing.plan(request={"actions": ["candidate-published", "merged-to-main", "landing-record"]})
    original = _crash(monkeypatch, LandingAuthority, "land", after=True)
    with pytest.raises(Crash):
        closing.close(item.id)
    monkeypatch.setattr(LandingAuthority, "land", original)
    closing.close(other.id)
    state = closing.state(item.id)
    assert state.outcome == "authority-block" and closing.card(item.id) == "READY"
    assert {r.split(":", 1)[0] for r in state.record["receipts"]} == {
        "candidate-published", "merged-to-main", "landing-record"}


@pytest.mark.parametrize("ambiguity", ["fast-forwarded", "unreadable"])
def test_an_ambiguous_landing_holds_with_facts_and_is_settled_before_any_later_session(closing, monkeypatch, ambiguity):
    """Check 8: the candidate already in the remote head, or an unreadable remote: a hold naming the facts, no push;
    after `authorize`, the next launch settles the earlier order before any session."""
    fx = closing.fx
    item = closing.accepted()
    other = fx.authorized("OTHER")
    revision = revision_of(closing.state(item.id))
    original = _crash(monkeypatch, LandingAuthority, "land", after=False)
    with pytest.raises(Crash):
        closing.close(item.id)
    monkeypatch.setattr(LandingAuthority, "land", original)
    if ambiguity == "fast-forwarded":
        git(closing.remote, "update-ref", "refs/heads/main", revision)
    url = RegistryClosure._url
    if ambiguity == "unreadable":
        monkeypatch.setattr(RegistryClosure, "_url", lambda self: str(closing.fx.root / "missing.git"))
    closing.close(other.id)
    state = closing.state(item.id)
    [order] = closing.orders(item.id)
    assert (state.outcome, state.record["hold_reason"]) == ("authority-block", "closure-hold:landing-ambiguous")
    assert closing.pushes == []
    facts = [order["order"][k] for k in ("base", "merge", "record")]
    escalation = json.dumps(fx.store.read_state("registry", "decision-inbox")[1]["open"][item.id])
    assert all(fact in escalation for fact in facts)
    if ambiguity == "unreadable":
        monkeypatch.setattr(RegistryClosure, "_url", url)
    assert fx.loaded().decide(item.id, "authorize", QUOTE)["answer"] is None
    sessions = len(fx.runs("CLOSURE"))
    closing.close(item.id)
    assert len(fx.runs("CLOSURE")) == sessions + (0 if ambiguity == "fast-forwarded" else 1)
    assert closing.pushes == ([] if ambiguity == "fast-forwarded" else ["pushed"])


def _ancestors(closing: Closing, base: str, revision: str) -> list[str]:
    """The candidate's proper ancestors above the remote base, oldest first."""
    return git(closing.fx.clone, "rev-list", "--first-parent", "--reverse", f"{base}..{revision}").decode().split()[:-1]


@pytest.mark.parametrize("moves", [1, 3])
def test_main_moving_to_an_ancestor_rebuilds_the_order_at_most_three_times(closing, monkeypatch, moves):
    """Check 12: each move to a proper ancestor of the candidate journals a new order; a third move holds."""
    for index in range(3):
        commit_file(closing.fx.clone, "main", f"docs/history-{index}.md", b"history\n")
    item = closing.accepted()
    base, revision = closing.head(), revision_of(closing.state(item.id))
    steps = iter(_ancestors(closing, base, revision)[:moves])
    original = LandingAuthority.land

    def moving(self, order):
        step = next(steps, None)
        if step is not None:
            git(closing.remote, "update-ref", "refs/heads/main", step)
        return original(self, order)
    monkeypatch.setattr(LandingAuthority, "land", moving)
    closing.close(item.id)
    state = closing.state(item.id)
    orders = closing.orders(item.id)
    if moves == 1:
        assert [o["order"]["attempt"] for o in orders] == [1, 2] and state.stage is LifecycleStage.DONE
        record = closing.head()
        assert git(closing.remote, "rev-parse", f"{record}^1^{{tree}}") == git(
            closing.remote, "rev-parse", f"{revision}^{{tree}}")
    else:
        assert [o["order"]["attempt"] for o in orders] == [1, 2, 3]
        assert (state.outcome, state.record["hold_reason"]) == ("authority-block", "closure-hold:base-unstable")


@pytest.mark.parametrize("move", ["fast-forward", "merged"])
def test_main_already_holding_the_candidate_is_ambiguous_not_rework(closing, monkeypatch, move):
    item = closing.accepted()
    revision = revision_of(closing.state(item.id))
    original = LandingAuthority.land

    def moving(self, order):
        if move == "fast-forward":
            git(closing.remote, "update-ref", "refs/heads/main", revision)
        else:
            clone = closing.fx.clone
            git(clone, "fetch", "-q", "origin")
            git(clone, "checkout", "-q", "-b", "remote-merge", "origin/main")
            git(clone, "-c", "user.name=F", "-c", "user.email=f@example.invalid", "merge", "-q", "--no-ff", "-m", "m",
                revision)
            git(clone, "push", "-q", "origin", "remote-merge:main")
            git(clone, "checkout", "-q", "main")
        return original(self, order)
    monkeypatch.setattr(LandingAuthority, "land", moving)
    closing.close(item.id)
    state = closing.state(item.id)
    assert (state.stage, state.record["hold_reason"]) == (LifecycleStage.ACCEPT, "closure-hold:landing-ambiguous")
    assert closing.pushes == ["refused:base-moved"]


@pytest.mark.parametrize("case", ["marked-child", "owner-alive"])
def test_cleanup_keeps_live_or_foreign_workspaces_and_then_issues_no_receipt(closing, monkeypatch, case):
    """Check 14: a marked process of the running CLOSURE correlation keeps its clone; an earlier correlation whose
    owner is alive (this test process) keeps its clone; another item's workspace is never touched; no receipt."""
    item = closing.accepted()
    verifier = launch_root(closing.fx.loaded().configuration) / "verifier"
    foreign = verifier / f"verifier-{workspace_folder('launch:another-item:1')}"
    foreign.mkdir()
    ownership = Owners("terminated") if case == "marked-child" else ProcOwnership()
    if case == "marked-child":  # a marked process of the running correlation outlives the session
        cleanup = RegistryClosure._cleanup
        monkeypatch.setattr(RegistryClosure, "_cleanup", lambda self, invocation: (
            setattr(ownership, "work", (1,)), cleanup(self, invocation))[1])
    closing.close(item.id, ownership=ownership)
    state = closing.state(item.id)
    assert state.outcome == "authority-block" and closing.card(item.id) == "DONE"
    assert receipt("workspaces-cleaned", item.id, revision_of(state)) not in state.record["receipts"]
    [session] = closing.fx.runs("CLOSURE")
    verifier_clone = next(p for p in verifier.iterdir() if p.name.startswith(f"verifier-launch-{workspace_folder(item.id)}-"))
    assert foreign.is_dir() and verifier_clone.is_dir()
    assert Path(session["cwd"]).is_dir() is (case == "marked-child")


def test_the_landing_token_reaches_only_the_authoritys_one_push_process(closing, monkeypatch):
    """Check 7: the landing token marker (raw or in its Basic header) is in the environment of exactly one child
    process, the Authority's push; never in the merge or record commit commands, the fetch, or a worker."""
    from base64 import b64encode
    item = closing.accepted()
    secrets = ("ghs-marker-landing", b64encode(b"x-access-token:ghs-marker-landing").decode())
    spawned: list[tuple[list[str], dict[str, str]]] = []
    popen = subprocess.Popen

    class Recording(popen):
        def __init__(self, args, *rest, **kwargs):
            env = kwargs.get("env")
            spawned.append(([str(a) for a in args] if isinstance(args, (list, tuple)) else [str(args)],
                            dict(os.environ if env is None else env)))
            super().__init__(args, *rest, **kwargs)
    monkeypatch.setattr(subprocess, "Popen", Recording)
    closing.close(item.id)
    monkeypatch.setattr(subprocess, "Popen", popen)
    assert closing.state(item.id).stage is LifecycleStage.DONE and closing.pushes == ["pushed"]
    carrying = [argv for argv, env in spawned if any(s in value for s in secrets for value in env.values())]
    assert len(carrying) == 1 and "push" in carrying[0]
    assert not [argv for argv, _ in spawned if any(s in " ".join(argv) for s in secrets)]
    for argv, env in spawned:  # the merge and record commits, the fetch, and every worker run carry no token
        if any(word in argv for word in ("commit", "merge", "fetch", "commit-tree")) or "ALIENINTENT_ROLE" in env:
            assert not any(s in value for s in secrets for value in env.values()), argv
    assert not any(s in value for s in secrets for value in os.environ.values())
    assert not any(s in json.dumps(run) for s in secrets for run in closing.fx.runs())


def test_a_correlation_with_no_journaled_owner_keeps_its_clone_and_then_issues_no_receipt(closing, monkeypatch):
    """Check 14: an earlier correlation whose `invocation-started` event has no owner keeps its clone, which is named
    in `cleanup_diagnostics`, and no `workspaces-cleaned` receipt is issued."""
    item = closing.accepted()
    registry = closing.fx.loaded()
    verifier = launch_root(registry.configuration) / "verifier"
    clone = next(p for p in verifier.iterdir() if p.name.startswith(f"verifier-launch-{workspace_folder(item.id)}-"))
    journal = launch_root(registry.configuration) / "invocation-journal.jsonl"
    records = [json.loads(line) for line in journal.read_text().splitlines()]
    [correlation] = {r["correlation_id"] for r in records if r.get("event") == "invocation-started"
                     and f"verifier-{workspace_folder(r['correlation_id'])}" == clone.name}
    for record in records:
        if record.get("event") == "invocation-started" and record.get("correlation_id") == correlation:
            assert isinstance(record.pop("owner"), dict)
    journal.write_text("".join(json.dumps(record) + "\n" for record in records))
    seen: list[RegistryClosure] = []
    cleanup = RegistryClosure._cleanup
    monkeypatch.setattr(RegistryClosure, "_cleanup", lambda self, invocation: (seen.append(self),
                                                                                 cleanup(self, invocation))[1])
    closing.close(item.id)
    state = closing.state(item.id)
    assert receipt("workspaces-cleaned", item.id, revision_of(state)) not in state.record["receipts"]
    assert clone.is_dir()
    [closure] = seen
    assert closure.cleanup_diagnostics[str(clone)] == "no journaled owner"


def test_authorize_of_a_begun_landing_waits_for_a_readable_remote_and_writes_nothing(closing, monkeypatch):
    """Change 7: `work decide --choice authorize` on a parked CLOSURE correlation with a `closure-ordered` event,
    while the remote default branch cannot be read, answers `remote-unverified` and writes nothing."""
    fx = closing.fx
    item = closing.accepted()
    other = fx.authorized("OTHER")
    original = _crash(monkeypatch, LandingAuthority, "land", after=False)
    with pytest.raises(Crash):
        closing.close(item.id)
    monkeypatch.setattr(LandingAuthority, "land", original)
    # Recovery cannot settle the begun landing, so the CLOSURE correlation's effect is parked for a decision.
    settle = work_registry.RealWorkerProvider.reconcile_closure
    monkeypatch.setattr(work_registry.RealWorkerProvider, "reconcile_closure", lambda self, invocation: None)
    closing.close(other.id)
    monkeypatch.setattr(work_registry.RealWorkerProvider, "reconcile_closure", settle)
    state = closing.state(item.id)
    correlation = state.record["correlation"]
    assert correlation in {effect.identity for effect in fx.store.unresolved_effects("registry")}
    assert any(record.get("event") == "closure-ordered" and record.get("correlation_id") == correlation
               for record in closing.journal())
    journal = launch_root(fx.loaded().configuration) / "invocation-journal.jsonl"
    before, journaled = fx.dump(), journal.read_text()
    hidden = fx.root / "remote.hidden"
    closing.remote.rename(hidden)
    try:
        answer = fx.loaded(Owners("terminated")).decide(item.id, "authorize", QUOTE)
    finally:
        hidden.rename(closing.remote)
    assert answer["answer"] == work_registry.REMOTE_UNVERIFIED and answer["missing"] == "a readable remote"
    assert answer["correlation"] == correlation
    assert (fx.dump(), journal.read_text()) == (before, journaled)
    assert fx.loaded(Owners("terminated")).decide(item.id, "authorize", QUOTE)["answer"] is None


def test_started_item_needs_the_journaled_contract_digest_and_initial_admission_is_unchanged(closing):
    """Check 9: a started item is built from its registry record only with the journaled digest; an item with no
    coordinator record whose card is not READY is not eligible."""
    fx = closing.fx
    item = closing.accepted()
    registry = fx.loaded()
    correlation = closing.state(item.id).record["correlation"]
    assert registry._started_item(item.id, correlation).contract.content_digest == next(
        r["contract_digest"] for r in closing.journal() if r.get("correlation_id") == correlation)
    journal = launch_root(registry.configuration) / "invocation-journal.jsonl"
    journal.write_text(journal.read_text().replace(next(
        r["contract_digest"] for r in closing.journal() if r.get("correlation_id") == correlation), OTHER_DIGEST))
    assert registry._started_item(item.id, correlation) is None
    waiting = fx.authorized("WAITING")
    fx.github.fields[fx.registry.records.show(waiting.id).item.card_id]["Status"] = "IMPLEMENT"
    assert fx.launch(waiting.id) == "not-eligible"


def test_a_projection_failure_never_stops_a_launch_and_is_repaired_later(closing, monkeypatch):
    """Check 10: the coordinator's DONE with the row write failing, or the remote unreadable: the launch of another
    item still runs, and a later launch projects the row."""
    from alienintent.context_assembly.application.work_completion import WorkCompletion
    item = closing.accepted()
    other, third = closing.fx.authorized("OTHER"), closing.fx.authorized("THIRD")
    original = WorkCompletion.record_coordinated
    monkeypatch.setattr(WorkCompletion, "record_coordinated", lambda *a: (_ for _ in ()).throw(RuntimeError("down")))
    closing.close(item.id)
    assert closing.state(item.id).stage is LifecycleStage.DONE
    assert closing.fx.loaded().identities.find(item.id).state != "DONE"
    monkeypatch.setattr(WorkCompletion, "record_coordinated", original)
    fetch = work_registry.WorkRegistry._fetch
    monkeypatch.setattr(work_registry.WorkRegistry, "_fetch", lambda self, repo: (_ for _ in ()).throw(
        GitReadFailed("git fetch", "remote", "unreadable")))
    assert closing.close(other.id).dispatched == (other.id,)
    assert closing.fx.loaded().identities.find(item.id).state != "DONE"
    monkeypatch.setattr(work_registry.WorkRegistry, "_fetch", fetch)
    closing.close(third.id)
    assert closing.fx.loaded().identities.find(item.id).state == "DONE"


@pytest.mark.parametrize("other", ["item", "candidate"])
def test_receipts_naming_another_item_or_candidate_never_count(closing, monkeypatch, other):
    """Check 1: the coordinator keeps only receipts naming this work item and the full custodied revision."""
    item = closing.accepted()
    real = work_registry.receipt
    monkeypatch.setattr(work_registry, "receipt", lambda action, identity, revision: real(
        action, "another-item" if other == "item" else identity, "b" * 40 if other == "candidate" else revision))
    closing.close(item.id)
    state = closing.state(item.id)
    assert (state.stage, state.outcome) == (LifecycleStage.ACCEPT, "authority-block")
    assert state.record["hold_reason"] == "closure-receipts-incomplete"


def _unescalated(closing: Closing, item_id: str) -> bool:
    return item_id not in json.dumps(closing.fx.store.read_state("registry", "decision-inbox")[1])


def test_main_moving_to_a_non_ancestor_after_the_order_reworks_without_escalation(closing, monkeypatch):
    """Check 12: the Authority refuses base-moved after the order is journaled."""
    item = closing.accepted()
    base = closing.head()
    original = LandingAuthority.land
    moved = []

    def moving(self, order):
        if not moved:
            moved.append(_unrelated(closing, base))
            git(closing.fx.clone, "push", "-q", str(closing.remote), f"{moved[0]}:refs/heads/main")
        return original(self, order)
    monkeypatch.setattr(LandingAuthority, "land", moving)
    closing.close(item.id)
    state = closing.state(item.id)
    assert len(closing.orders(item.id)) == 1
    assert closing.pushes == ["refused:base-moved"] and closing.head() == moved[0]
    assert state.stage is LifecycleStage.IMPLEMENT and state.record["rejections"] == 1
    assert any(f.startswith("closure-rework:base-moved:") for f in state.record["findings"][-1]["findings"])
    assert _unescalated(closing, item.id)


def test_a_crash_then_main_moving_to_a_non_ancestor_reworks_without_a_push(closing, monkeypatch):
    """Check 8, third bullet: recovery of a journaled order after main moved past it."""
    fx = closing.fx
    item = closing.accepted()
    other = fx.authorized("OTHER")
    base = closing.head()
    original = _crash(monkeypatch, LandingAuthority, "land", after=False)
    with pytest.raises(Crash):
        closing.close(item.id)
    monkeypatch.setattr(LandingAuthority, "land", original)
    assert len(closing.orders(item.id)) == 1
    moved = _unrelated(closing, base)
    git(fx.clone, "push", "-q", str(closing.remote), f"{moved}:refs/heads/main")
    sessions = len(fx.runs())
    closing.close(other.id)
    state = closing.state(item.id)
    assert len(fx.runs("CLOSURE")) == 1 and len(fx.runs()) == sessions + 1
    assert closing.pushes == [] and closing.head() == moved
    assert state.stage is LifecycleStage.IMPLEMENT and state.record["rejections"] == 1
    assert any(f.startswith("closure-rework:base-moved:") for f in state.record["findings"][-1]["findings"])
    assert _unescalated(closing, item.id)


# --- WORKER-CREDENTIAL-BOUNDARY: the launch with a worker user (acceptance checks 1, 2, 4 and 6) --------------------
from tests.invocation_runtime.test_git_source_control import USER, install_fake_sudo, outside, record_git, \
    sudo_calls  # noqa: E402

# With a worker user: no configuration path; the three identity variables of the export-mode context command.
WORKER_ALLOWED = ALLOWED - {"ALIENINTENT_PROJECT_CONFIGURATION", "ALIENINTENT_PROJECT"} | {
    "ALIENINTENT_CORRELATION", "ALIENINTENT_WORK_IDENTITY", "CODEX_HOME", "LOGNAME"}
# The Founder's own provider logins: never read, copied or opened by the worker path (revision 8).
LOGINS = {".codex/auth.json": "LOGIN-CODEX-TEST-DATA", ".claude/.credentials.json": "LOGIN-CLAUDE-TEST-DATA"}
WORKER_LOGIN = "WORKER-OWN-CODEX-LOGIN-TEST-DATA"
_OPENS: list[list[str]] = []


def _audit(event: str, arguments: tuple) -> None:
    # A path opened by name; an integer is an already-open descriptor (a subprocess pipe), not a file opened.
    if event == "open" and _OPENS and isinstance(arguments[0], (str, bytes, os.PathLike)):
        _OPENS[-1].append(os.fsdecode(arguments[0]))


sys.addaudithook(_audit)


class recorded_opens:
    """Every file this process opens by path while the block runs (the `open` audit event: open, os.open, Path
    reads)."""

    def __enter__(self) -> list[str]:
        _OPENS.append([])
        return _OPENS[-1]

    def __exit__(self, *_: object) -> None:
        _OPENS.pop()


def worker_store(fx) -> Path:
    return launch_root(fx.loaded().configuration) / "worker" / "auth" / "codex"


def login_check_argv(store: Path) -> list[str]:
    return ["sh", "-c", 'test -d "$1" && ! test -L "$1" && test -f "$1/auth.json" && ! test -L "$1/auth.json"',
            "sh", str(store)]


def worker_commands(log: Path) -> list[list[str]]:
    """Each command the fake sudo ran through `env -i`, without the prefix and the allowlisted variables."""
    commands = []
    for call in sudo_calls(log):
        if call["argv"][4:6] == ["env", "-i"]:
            rest = call["argv"][6:]
            while rest and "=" in rest[0] and rest[0].split("=", 1)[0].isidentifier():
                rest = rest[1:]
            commands.append(rest)
    return commands


def cleanup_argv(store: Path) -> list[str]:
    return ["find", "-P", str(store), "-mindepth", "1", "-maxdepth", "1", "!", "-name", "auth.json", "-exec", "rm",
            "-rf", "--", "{}", "+"]


@pytest.fixture
def workerized(fx, monkeypatch):
    """The launch fixture with `worker_user` (the test's own user, behind a fake sudo that records its arguments),
    a Founder HOME holding both provider login files and a Founder credential file, the worker's own persistent
    Codex login `<launch>/worker/auth/codex/auth.json` (mode 0600, made once by the Founder as the worker), and the
    existing marker observation (a real worker uid cannot be observed in a test; check 5 covers it over a fake
    /proc)."""
    fx.document["projects"][PROJECT]["worker_user"] = USER
    fx.configuration_file.write_text(json.dumps(fx.document))
    founder = fx.root / "founder-home"
    for name, text in LOGINS.items():
        (founder / name).parent.mkdir(parents=True, exist_ok=True)
        (founder / name).write_text(text)
    (founder / ".git-credentials").write_text("https://x:FOUNDER-TOKEN@github.com\n")
    monkeypatch.setenv("HOME", str(founder))
    store = worker_store(fx)
    store.mkdir(parents=True, mode=0o700)
    (store / "auth.json").write_text(WORKER_LOGIN)
    (store / "auth.json").chmod(0o600)
    fx.founder = founder
    uids = []
    monkeypatch.setattr(work_registry, "ProcOwnership",
                        lambda *a, worker_uid=None, **k: (uids.append(worker_uid), Owners())[1])
    fx.sudo_log, fx.uids = install_fake_sudo(fx.root / "sudo-bin", monkeypatch), uids
    return fx


def test_with_a_worker_user_no_privileged_git_touches_a_worker_repository_through_landing(workerized, monkeypatch):
    """Checks 1, 4 and 6 over PRODUCER, VERIFIER and a landing CLOSURE: every session and worker-side command runs
    through the one sudo rule in its own worker clone; the candidate comes only from the intake import; no
    control-plane or Landing Authority git runs in, names GIT_DIR in, or has an argument under the worker, hand-over
    or results folders; the worker HOME holds exactly a safe.directory-only .gitconfig; every session's CODEX_HOME
    is the worker's own persistent login folder, holding only auth.json when it starts; no file under the Founder's
    ~/.codex or ~/.claude is opened (check 6, revision 8)."""
    fx = workerized
    closing = Closing(fx, monkeypatch)
    item = fx.authorized("UNIT", **FIXED)
    configuration = fx.loaded().configuration
    root, packets = launch_root(configuration), configuration.repositories[configuration.packets_repository].clone
    calls = record_git(monkeypatch)
    from alienintent.invocation_runtime.adapters.git_source_control import IntakeSourceControl
    reads, read_result = [], IntakeSourceControl.read_result
    monkeypatch.setattr(IntakeSourceControl, "read_result", lambda self, invocation, name, *rest, **limit: (
        reads.append(name), read_result(self, invocation, name, *rest, **limit))[1])
    store = root / "worker" / "auth" / "codex"
    founder_logins = (str(fx.founder / ".codex"), str(fx.founder / ".claude"))
    with recorded_opens() as opens:
        fx.launch(item.id)
    assert not [path for path in opens if path.startswith(founder_logins)]
    [producer] = fx.runs("PRODUCER")
    assert producer["env"]["CODEX_HOME"] == str(store)
    assert sorted(p.name for p in store.iterdir()) == ["auth.json"] and (store / "auth.json").read_text() == \
        WORKER_LOGIN  # the worker's own login persists; the Founder's is never copied
    assert Path(producer["cwd"]).parent == root / "worker" and Path(producer["cwd"]).name.startswith("producer-")
    assert not Path(producer["cwd"]).exists()  # removed as the worker after publication
    home = root / "worker" / "home"
    assert sorted(str(p.relative_to(home)) for p in home.rglob("*")) == [".gitconfig"]
    assert (home / ".gitconfig").read_text() == \
        f"[safe]\n\tdirectory = {packets}\n\tdirectory = {root / 'intake.git'}\n"
    assert producer["env"]["HOME"] == str(home) and set(producer["env"]) <= WORKER_ALLOWED
    assert_bounded_export(fx, root, producer)
    (home / ".git-credentials").write_text("planted\n")  # recreated empty at the next session
    for name in ("config.toml", "AGENTS.md"):  # one session leaves nothing for the next but auth.json
        (store / name).write_text("planted\n")
    (store / "sessions").mkdir()
    with recorded_opens() as opens:
        fx.launch(item.id)
    assert not [path for path in opens if path.startswith(founder_logins)]
    assert not (home / ".git-credentials").exists() and (home / ".gitconfig").is_file()
    assert sorted(p.name for p in store.iterdir()) == ["auth.json"] and (store / "auth.json").read_text() == \
        WORKER_LOGIN
    state = closing.state(item.id)
    assert state.stage is LifecycleStage.ACCEPT
    revision = revision_of(state)
    intake_ref = f"refs/intake/{ref_safe(producer['env']['ALIENINTENT_INVOCATION_ID'])}"
    [verifier] = fx.runs("VERIFIER")
    assert Path(verifier["cwd"]).parent == root / "worker" and verifier["head"] == revision
    assert "launch-candidate.txt" in verifier["package"]["diff"]["text"]
    assert verifier["package"]["producer_self_review"]["text"] == REVIEW
    closing.close(item.id)
    assert closing.state(item.id).stage is LifecycleStage.DONE and closing.pushes == ["pushed"]
    [session] = fx.runs("CLOSURE")
    assert Path(session["cwd"]).parent == root / "worker" and set(session["env"]) <= WORKER_ALLOWED
    for run in (verifier, session):
        assert_bounded_export(fx, root, run)
    assert not [p.name for p in (root / "worker").iterdir() if item.id in p.name]  # every worker clone removed
    outside(calls, root / "worker", root / "handoff", root / "results")
    assert git(root / "intake.git", "rev-parse", intake_ref).decode().strip() == revision
    assert os.getuid() in fx.uids  # the registry's ownership observes the worker's uid (the assessment's does not)
    for call in sudo_calls(fx.sudo_log):
        assert call["argv"][:7] == ["-n", "-u", USER, "--", "env", "-i", "PATH=/usr/bin:/bin"] \
            or call["argv"][:4] == ["-n", "-u", USER, "kill"], call
    assert "FOUNDER-TOKEN" not in json.dumps(fx.runs())
    # Check 6b: every worker result was read through the checked descriptor reader, and nothing else; REGRESSION-GATE
    # reads the suite's junit files and no worker-written feature-regressions.json.
    assert sorted(set(reads)) == ["closure-request.json", "self-review.md", "suite-junit.xml", "verdict.json"]
    # Check 4: each worker clone was removed as the worker, through the sudo rule.
    removed = {Path(c["argv"][-1]).name.split("-")[0] for c in sudo_calls(fx.sudo_log) if c["argv"][-4:-1] == [
        "rm", "-rf", "--"] and Path(c["argv"][-1]).parent == root / "worker"}
    assert removed == {"home", "producer", "verifier", "closure"}  # the HOME is recreated as the worker too
    # Revision 8: before each session, as the worker, the login check and then the store's cleanup, exactly.
    worker_argvs = worker_commands(fx.sudo_log)
    sessions = len(fx.runs())
    assert worker_argvs.count(login_check_argv(store)) == sessions
    assert worker_argvs.count(cleanup_argv(store)) == sessions
    for call in sudo_calls(fx.sudo_log):
        if call["argv"][4:6] == ["env", "-i"]:
            assert f"CODEX_HOME={store}" in call["argv"], call  # beside HOME and TMPDIR in the one environment


# --- WORKER-SESSION-IDENTITY: the worker's own user name; the receipt rule (acceptance checks 1-3) ---------------
LAUNCHING = "launching-founder-name"


def sudo_environments(log: Path) -> list[dict[str, str]]:
    """The variables each command the fake sudo ran through `env -i` was given (after `PATH=/usr/bin:/bin`)."""
    environments = []
    for call in sudo_calls(log):
        if call["argv"][4:6] == ["env", "-i"]:
            variables, rest = {}, call["argv"][6:]
            while rest and "=" in rest[0] and rest[0].split("=", 1)[0].isidentifier():
                name, value = rest[0].split("=", 1)
                variables[name], rest = value, rest[1:]
            environments.append(variables)
    return environments


def test_with_a_worker_user_every_worker_command_carries_the_workers_own_user_name(workerized, monkeypatch):
    """Checks 1 and 2: with the launching process's USER and LOGNAME another name, every command run through the
    fake sudo (the sessions and the clones, the REGRESSION-GATE baseline clone among them) carries USER and LOGNAME
    equal to the worker user; each session's environment names are within WORKER_ALLOWED and include both."""
    fx = workerized
    Closing(fx, monkeypatch)
    monkeypatch.setenv("USER", LAUNCHING)
    monkeypatch.setenv("LOGNAME", LAUNCHING)
    item = fx.authorized("UNIT", **FIXED)
    fx.launch(item.id)
    fx.launch(item.id)
    environments = sudo_environments(fx.sudo_log)
    commands = worker_commands(fx.sudo_log)
    # REGRESSION-GATE: the candidate's feature-regression runner no longer runs in the registry profile.
    assert not any("run_feature_regressions.py" in " ".join(c) for c in commands)
    assert any(c[:2] == ["git", "clone"] for c in commands)  # a worker clone
    assert environments and all(e.get("USER") == e.get("LOGNAME") == USER for e in environments), environments
    runs = fx.runs()
    assert fx.runs("PRODUCER") and fx.runs("VERIFIER")
    for run in runs:
        assert set(run["env"]) <= WORKER_ALLOWED and {"USER", "LOGNAME"} <= set(run["env"])
        assert run["env"]["USER"] == run["env"]["LOGNAME"] == USER


def test_without_a_worker_user_user_stays_inherited_and_there_is_no_logname(fx, monkeypatch):
    """Check 2: without a worker user the session's USER is the launching process's and LOGNAME is absent."""
    monkeypatch.setenv("USER", LAUNCHING)
    monkeypatch.setenv("LOGNAME", LAUNCHING)
    item = fx.authorized("PLAIN")
    fx.launch(item.id)
    [producer] = fx.runs("PRODUCER")
    assert producer["env"]["USER"] == LAUNCHING and "LOGNAME" not in producer["env"]
    assert set(producer["env"]) <= ALLOWED


def _joined(name: str) -> str:
    return " ".join((Path(__file__).resolve().parents[2] / name).read_text().split())


def test_the_receipt_rule_names_where_the_receipt_lives_with_and_without_a_worker_user():
    """Check 3: AGENTS.md no longer requires the receipt inside the candidate and names both places;
    docs/operations.md names the launch results path."""
    agents = _joined("AGENTS.md")
    assert "exact candidate carries a valid passing" not in agents
    assert "`.alienintent/feature-regressions.json`" in agents and "launch results folder" in agents
    assert "`<launch>/results/<invocation>/feature-regressions.json`" in _joined("docs/operations.md")


def assert_bounded_export(fx, root: Path, run: dict) -> None:
    """Check 6d over a real session: the package named to the worker is its bounded export only, Founder-owned with
    folders 0711 and no worker ACL, the file 0640 with the one ACL entry `u:<worker>:r`; its `context_command` is
    the export mode with only the three identity variables and re-prints exactly that package; another correlation
    answers `not-in-export`; no configuration path is named; `<launch>/context` holds no package for it."""
    correlation = run["env"]["ALIENINTENT_INVOCATION_ID"]
    export = root / "exports" / correlation / "context.json"
    assert run["package_path"] == str(export)
    package = json.loads(export.read_text())
    assert run["package"] == package and package["role"] == run["env"]["ALIENINTENT_ROLE"]
    assert package["context_command"] == {
        "argv": [str(work_registry.installed_executable()), "--json", "work", "context", "--export", str(export)],
        "environment": {"ALIENINTENT_WORK_IDENTITY": package["identity"], "ALIENINTENT_ROLE": package["role"],
                        "ALIENINTENT_CORRELATION": correlation}}
    assert {name: run["env"][name] for name in package["context_command"]["environment"]} == \
        package["context_command"]["environment"]  # the sudo allowlist carries the three identity variables
    assert json.loads(run["own_context"]) == package
    assert json.loads(run["other_context"]) == {"error": "not-in-export"}
    text = export.read_text()
    assert "ALIENINTENT_PROJECT" not in text and str(fx.configuration_file) not in text
    assert not (root / "context" / f"{correlation}.json").exists()
    assert (root / "context").stat().st_mode & 0o7777 == 0o700  # Founder-only with a worker user
    for folder in (root / "exports", export.parent):
        assert folder.stat().st_uid == os.getuid() and folder.stat().st_mode & 0o7777 == 0o711
        assert [line for line in _acl(folder) if not line.startswith(("user::", "group::", "other::"))] == []
    assert export.stat().st_uid == os.getuid() and export.stat().st_mode & 0o7777 == 0o640
    assert [line for line in _acl(export) if line.startswith("user:") and not line.startswith("user::")] == \
        [f"user:{USER}:r--"]
    assert not [p for p in export.parent.iterdir() if p.name != "context.json"]


def _acl(path: Path) -> list[str]:
    return subprocess.run(["getfacl", "-cp", str(path)], capture_output=True, text=True, check=True).stdout.split()


def test_without_a_worker_user_nothing_runs_through_sudo_and_the_worktree_path_is_unchanged(fx, monkeypatch):
    """Check 4: with no `worker_user` the launch uses the existing worktree under `launch/workspaces` and no sudo."""
    log = install_fake_sudo(fx.root / "sudo-bin", monkeypatch)
    item = fx.authorized("PLAIN")
    fx.launch(item.id)
    [producer] = fx.runs("PRODUCER")
    root = launch_root(fx.loaded().configuration)
    assert Path(producer["cwd"]).parent == root / "workspaces" and sudo_calls(log) == []
    assert not (root / "worker").exists() and not (root / "intake.git").exists()


SETUP = Path(__file__).resolve().parents[2] / "tools/live/setup_worker_user.sh"


def test_the_setup_plan_grants_the_worker_no_write_on_any_control_plane_repository(tmp_path):
    """Check 2: the dry-run plan gives `worker`, `results` and `handoff` mode 0711 owned by the worker; the intake,
    intake-bundles and landing folders the Founder's, mode 0700; read and traverse only (`r-X`) on the packets clone
    and the intake repository; traverse only (`--x`, no default ACL) on the launch folder; no write ACL for the
    worker anywhere; removal of any write or default ACL; and final checks asserting it. It changes nothing."""
    launch, packets = tmp_path / "launch", tmp_path / "packets"
    configuration, evidence = tmp_path / "project.json", tmp_path / "evidence"
    databases = (tmp_path / "work.sqlite", tmp_path / "readiness.sqlite")
    result = subprocess.run(["bash", str(SETUP), "--dry-run", "--founder", "founder", "--launch", str(launch),
                             "--packets", str(packets), "--key", str(tmp_path / "keys/app.pem"),
                             "--configuration", str(configuration), "--database", str(databases[0]),
                             "--database", str(databases[1]), "--evidence", str(evidence),
                             "--read", str(tmp_path / "python")],
                            capture_output=True, text=True, check=False, timeout=60)
    assert result.returncode == 0, result.stderr
    plan = result.stdout
    assert not launch.exists()
    for name in ("worker", "results", "handoff"):
        assert f"install -d -o alienintent-worker -g alienintent-worker -m 0711 {launch / name}" in plan
    for name in ("intake.git", "intake-bundles", "landing"):
        assert f"install -d -o founder -m 0700 {launch / name}" in plan
    for path in (packets, launch / "intake.git"):
        assert f"setfacl -R -m u:alienintent-worker:r-X {path}" in plan
        assert f"find {path} -type d -exec setfacl -d -m u:alienintent-worker:r-X \\{{\\}} +" in plan
    assert f"setfacl -m u:alienintent-worker:--x {launch}" in plan
    grants = [line for line in plan.splitlines() if line.startswith("setfacl") and " -m " in line]
    assert grants
    for line in grants:
        entry = next(part for part in line.split() if part.startswith("u:alienintent-worker:"))
        assert "w" not in entry.rsplit(":", 1)[1], line
        if line.endswith(f" {launch}"):
            assert " -d " not in line, line  # the traverse-only launch folder has no default ACL
    for path in (packets, launch / "intake.git", launch / "intake-bundles", launch / "landing"):
        assert f"setfacl -R -x u:alienintent-worker {path}" in plan
        assert f"find {path} -type d -exec setfacl -x d:u:alienintent-worker \\{{\\}} +" in plan
    assert f"setfacl -x u:alienintent-worker {launch}" in plan and f"setfacl -x d:u:alienintent-worker {launch}" in plan
    assert "Defaults>alienintent-worker !use_pty, !log_output" in plan
    assert "founder ALL=(alienintent-worker) NOPASSWD: /usr/bin/env, /usr/bin/kill" in plan
    for check in ("check: not writable, not owned, no ACL beyond read and traverse:", "check: App key unreadable",
                  "check: no credential in the packets clone config"):
        assert check in plan
    # Revision 7: the bounded export folder, traverse only for the worker.
    assert f"install -d -o founder -m 0711 {launch / 'exports'}" in plan
    assert f"setfacl -m u:alienintent-worker:--x {launch / 'exports'}" in plan
    assert f"setfacl -x d:u:alienintent-worker {launch / 'exports'}" in plan
    # Revision 8: the Founder's own provider logins lose read for others too.
    for name in (".codex", ".claude"):
        assert [line for line in plan.splitlines() if line.startswith("chmod -R o-rwx ") and line.endswith(f"/{name}")]


def test_the_setup_grants_nothing_on_the_canonical_stores_and_restores_owner_only_modes(tmp_path):
    """Check 6c: no ACL grant (access or default, any permission) names the work or readiness database, the evidence
    repository (or objects/) or the registry configuration, nor any path inside them; every earlier entry is removed
    (setfacl -b, and -k on folders), owner-only modes are restored (0600 files, 0700 evidence root and objects/), and
    the final checks assert, as the worker, that none is readable or traversable and that UNSAFE_ROOT passes."""
    launch, packets = tmp_path / "launch", tmp_path / "packets"
    configuration, evidence = tmp_path / "project.json", tmp_path / "evidence"
    databases = (tmp_path / "work.sqlite", tmp_path / "readiness.sqlite")
    result = subprocess.run(["bash", str(SETUP), "--dry-run", "--founder", "founder", "--launch", str(launch),
                             "--packets", str(packets), "--key", str(tmp_path / "keys/app.pem"),
                             "--configuration", str(configuration), "--database", str(databases[0]),
                             "--database", str(databases[1]), "--evidence", str(evidence),
                             "--read", str(tmp_path / "python")], capture_output=True, text=True, check=False,
                            timeout=60)
    assert result.returncode == 0, result.stderr
    plan = result.stdout.splitlines()
    private = (configuration, *databases, evidence)
    for line in plan:
        if line.startswith(("setfacl", "find")) and (" -m " in line or "-d -m" in line):
            assert not any(str(path) in line.split() or any(word.startswith(f"{path}/") for word in line.split())
                           for path in private), line
    for path in (configuration, *databases):
        assert f"setfacl -b {path}" in plan and f"chmod 0600 {path}" in plan
    for path in databases:  # the SQLite sidecar files too, when present
        assert f"owner_only {path}-wal {path}-shm" in plan
        for sidecar in (f"{path}-wal", f"{path}-shm"):
            assert f"check: neither readable nor traversable by the worker: {sidecar}" in plan
    assert f"setfacl -R -b {evidence}" in plan
    assert f"find {evidence} -type d -exec setfacl -k \\{{\\}} +" in plan
    assert f"chmod 0700 {evidence} {evidence / 'objects'}" in plan
    for path in (configuration, *databases, evidence, evidence / "objects"):
        assert f"check: neither readable nor traversable by the worker: {path}" in plan
    assert f"check: the evidence repository's privacy check passes (UNSAFE_ROOT): {evidence}" in plan
    assert not [line for line in plan if "configuration readable" in line]
    missing = subprocess.run(["bash", str(SETUP), "--dry-run", "--founder", "founder", "--launch", str(launch),
                              "--packets", str(packets), "--key", str(tmp_path / "k"), "--configuration",
                              str(configuration)], capture_output=True, text=True, check=False, timeout=60)
    assert missing.returncode == 2  # the canonical stores must be named, so none is left with an old grant


def _unreachable(path):
    """Run the setup's own `unreachable` final check on `path`, with the current user standing in for the worker."""
    text = SETUP.read_text()
    start = text.index("unreachable() {")
    function = text[start:text.index("\n}\n", start) + 3]
    script = f'as_worker() {{ "$@"; }}\n{function}unreachable "$1"'
    return subprocess.run(["bash", "-c", script, "check", str(path)], check=False, timeout=60).returncode == 0


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads every file, so no file is unreachable to it")
def test_the_unreachable_check_judges_files_by_their_contents_and_folders_by_listing_and_traverse(tmp_path):
    """Check 6c's final check: a file whose name the worker can look up (`ls` succeeds) but whose contents it cannot
    open is unreachable; a readable file is not; a folder is unreachable only when it can be neither listed nor
    traversed; an absent SQLite sidecar is unreachable."""
    private_file, readable_file = tmp_path / "work.sqlite", tmp_path / "readable.sqlite"
    private_file.write_text("x"); readable_file.write_text("x")
    private_file.chmod(0o000)
    private_dir, open_dir = tmp_path / "evidence", tmp_path / "open"
    private_dir.mkdir(); open_dir.mkdir()
    private_dir.chmod(0o000)
    try:
        assert subprocess.run(["ls", "-a", "--", str(private_file)], capture_output=True).returncode == 0
        assert _unreachable(private_file)
        assert not _unreachable(readable_file)
        assert _unreachable(private_dir)
        assert not _unreachable(open_dir)
        assert _unreachable(tmp_path / "work.sqlite-wal")
    finally:
        private_file.chmod(0o600); private_dir.chmod(0o700)


def test_check_8d_mints_only_through_the_landing_authoritys_own_credentials(fx, monkeypatch, capsys):
    """Check 8(d), offline: the proof builds the Landing Authority over its own InstallationCredentials from the
    `github` entry and mints through exactly those, without building a WorkRegistry, opening a database or
    constructing an evidence repository, and leaves the evidence root's mode unchanged. Its record states the claim
    boundary of a pass (partial)."""
    import importlib.util
    import sqlite3
    from alienintent.composition import landing_authority
    from alienintent.evidence_learning.adapters import local_evidence_repository
    from alienintent.installation.application.installation_credentials import InstallationCredentials
    spec = importlib.util.spec_from_file_location("worker_boundary_check",
                                                  SETUP.with_name("worker_boundary_check.py"))
    check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check)
    configuration = fx.loaded().configuration
    evidence = configuration.readiness.evidence_root
    evidence.mkdir(parents=True, exist_ok=True, mode=0o700)
    mode = evidence.stat().st_mode
    monkeypatch.setattr(work_registry.WorkRegistry, "__init__", lambda *a, **k: pytest.fail("a WorkRegistry"))
    monkeypatch.setattr(local_evidence_repository.LocalEvidenceRepository, "__init__",
                        lambda *a, **k: pytest.fail("an evidence repository"))
    monkeypatch.setattr(sqlite3, "connect", lambda *a, **k: pytest.fail("a database was opened"))
    built, minted = [], []
    authority_init = landing_authority.LandingAuthority.__init__
    monkeypatch.setattr(landing_authority.LandingAuthority, "__init__", lambda self, credentials, *rest, **k: (
        built.append(credentials), authority_init(self, credentials, *rest, **k))[1])
    from types import SimpleNamespace
    monkeypatch.setattr(InstallationCredentials, "token", lambda self: (minted.append(self), SimpleNamespace(
        permissions=dict(landing_authority.LANDING_PERMISSIONS), repository_selection="selected"))[1])
    assert check.check_d(fx.configuration_file, PROJECT)
    assert len(built) == 1 and minted == built  # minted only through the authority's own credentials
    assert evidence.stat().st_mode == mode
    line = json.loads(capsys.readouterr().out)
    assert line["check"] == "8(d)" and line["partial"] is True and line["evidence_root_mode_unchanged"] is True
    assert "InstallationCredentials only" in line["claim"]
    assert check.main(["--dry-run", "--configuration", "x", "--project", "p", "--key", "k"]) == 0


def _proof_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("worker_boundary_check", SETUP.with_name("worker_boundary_check.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_check_8d_records_the_safe_mint_reason_and_a_scope_the_installation_does_not_grant_is_unresolved(
        fx, monkeypatch, capsys):
    """Live finding: 8(d) recorded only `CredentialUnavailable`. It records the exception's own message (it never
    holds a token). GitHub's 422 to the landing-scoped mint means the installation does not grant `contents: write`,
    which waits for the Founder's App permission decision: UNRESOLVED, not PASS. Any other failure is FAIL."""
    from alienintent.installation.application.installation_credentials import InstallationCredentials
    from alienintent.installation.domain.app_credentials import CredentialUnavailable
    check = _proof_module()
    fx.loaded().configuration.readiness.evidence_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    for message, status in (("github answered 422 where 201 was required", "UNRESOLVED"),
                            ("github answered 401 where 201 was required", "FAIL")):
        def refuse(self, message=message):
            raise CredentialUnavailable(message)
        monkeypatch.setattr(InstallationCredentials, "token", refuse)
        assert not check.check_d(fx.configuration_file, PROJECT)
        line = json.loads(capsys.readouterr().out)
        assert line["status"] == status and line["error"] == f"CredentialUnavailable: {message}"
        assert line["partial"] is True
        if status == "UNRESOLVED":
            assert "App permission decision" in line["reason"]


def test_proof_diagnostics_are_bounded_and_redacted_and_a_crashing_check_is_recorded_not_raised(tmp_path, capsys):
    """Live finding: 8(c1) kept only a return code and 8(e) ended the proof with a traceback. Output tails are
    bounded and redact token-like text (a 40-hex SHA stays readable); a check that raises is recorded FAIL with its
    reason and the proof goes on to the next check."""
    check = _proof_module()
    sha = "a" * 40
    text = (f"x" * 5000 + f" commit {sha} Authorization: Bearer abc.def token=s3cr3t sk-proj-ABCDEFGHIJKLMNOP "
            "ghs_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345 eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.c2lnbmF0dXJl").encode()
    tail = check._tail(text)
    assert len(tail) <= check.TAIL_LIMIT and sha in tail
    for secret in ("abc.def", "s3cr3t", "sk-proj-ABCDEFGHIJKLMNOP", "ghs_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345",
                   "eyJhbGciOiJIUzI1NiJ9"):
        assert secret not in tail
    def crash():
        raise RuntimeError("worker workspace operation failed")
    assert check._guarded("e", crash) is False
    line = json.loads(capsys.readouterr().out)
    assert line["check"] == "8(e)" and line["status"] == "FAIL"
    assert line["error"] == "RuntimeError: worker workspace operation failed"


@pytest.mark.parametrize("case", ["missing", "login-symlink", "store-symlink", "claude-route"])
def test_a_worker_launch_without_its_own_codex_login_or_on_another_provider_is_refused(workerized, case, tmp_path):
    """Check 6 (revision 8): after the route is resolved, a non-codex route under a worker user is refused with
    `worker provider unsupported: <provider>`; then the worker-run login check refuses a missing, symlinked or
    symlink-reached auth.json with `worker provider login missing: <store>`. No session starts, the store is not
    cleaned, and no file under the Founder's ~/.codex or ~/.claude is opened."""
    fx = workerized
    store = worker_store(fx)
    if case == "missing":
        (store / "auth.json").unlink()
    elif case == "login-symlink":
        (store / "auth.json").unlink()
        (store / "auth.json").symlink_to(fx.founder / ".codex/auth.json")
    elif case == "store-symlink":
        store.rename(tmp_path / "elsewhere")
        store.symlink_to(tmp_path / "elsewhere")
    else:
        fx.route(routing(str(fx.codex), str(fx.claude), {"PRODUCER": {"provider": "claude", "model": "model-b"}}))
    reason = "worker provider unsupported: claude" if case == "claude-route" \
        else f"worker provider login missing: {store}"
    item = fx.authorized("NOLOGIN")
    with recorded_opens() as opens:
        summary = fx.launch(item.id)
    assert summary.authority_blocked == (item.id,) and fx.runs() == []
    [finding] = fx.journal_findings(item.id)
    assert finding == reason
    assert not [path for path in opens if path.startswith((str(fx.founder / ".codex"), str(fx.founder / ".claude")))]
    worker_argvs = worker_commands(fx.sudo_log)
    assert cleanup_argv(store) not in worker_argvs
    assert (login_check_argv(store) in worker_argvs) is (case != "claude-route")


def test_prepare_worker_session_recreates_an_empty_home_and_cleans_the_store_opening_no_file(tmp_path, monkeypatch):
    """Check 6 (revision 8): as the worker, the HOME is recreated holding only the safe.directory .gitconfig, and
    everything in the store but auth.json is removed by exactly the one `find -P` command (a symlink in the store is
    removed, never followed). The function opens no file."""
    log = install_fake_sudo(tmp_path / "sudo-bin", monkeypatch)
    worker = tmp_path / "worker"
    home, temporary, store = worker / "home", worker / "tmp", worker / "auth" / "codex"
    store.mkdir(parents=True)
    (store / "auth.json").write_text(WORKER_LOGIN)
    for name in ("config.toml", "AGENTS.md"):
        (store / name).write_text("planted\n")
    (store / "sessions").mkdir()
    (store / "sessions" / "s.jsonl").write_text("x\n")
    target = tmp_path / "target"
    target.mkdir()
    (target / "keep").write_text("kept\n")
    (store / "link").symlink_to(target)
    (home / ".codex").mkdir(parents=True)
    (home / ".codex" / "auth.json").write_text("an earlier copy\n")
    environment = {"HOME": str(home), "TMPDIR": str(temporary), "CODEX_HOME": str(store)}
    packets, intake = tmp_path / "packets", tmp_path / "intake.git"
    with recorded_opens() as opens:
        work_registry.prepare_worker_session(USER, environment, packets, intake)
    assert opens == []
    assert sorted(str(p.relative_to(home)) for p in home.rglob("*")) == [".gitconfig"]
    assert (home / ".gitconfig").read_text() == f"[safe]\n\tdirectory = {packets}\n\tdirectory = {intake}\n"
    assert home.stat().st_mode & 0o7777 == 0o700 and temporary.is_dir()
    assert sorted(p.name for p in store.iterdir()) == ["auth.json"] and (store / "auth.json").read_text() == \
        WORKER_LOGIN
    assert (target / "keep").read_text() == "kept\n"
    calls = sudo_calls(log)
    assert calls and all(c["argv"][:7] == ["-n", "-u", USER, "--", "env", "-i", "PATH=/usr/bin:/bin"] for c in calls)
    assert worker_commands(log).count(cleanup_argv(store)) == 1


def test_check_8b_names_the_founders_own_provider_logins_among_the_credential_files():
    """Check 8(b) (revision 8): the Founder's ~/.codex/auth.json and ~/.claude/.credentials.json are among the files
    that must be unreadable to the worker; no login-file table remains anywhere."""
    check = _proof_module()
    assert {".codex/auth.json", ".claude/.credentials.json"} <= set(check.CREDENTIAL_FILES)
    assert not hasattr(check, "PROVIDER_LOGIN_FILES") and not hasattr(work_registry, "PROVIDER_LOGIN_FILES")


FAKE_CODEX = r"""#!{python}
# FAKE CODEX (test data): records what it sees, refreshes the login in place and leaves a file behind.
import json, os, sys
from pathlib import Path
sys.stdin.read()
home, store = Path(os.environ["HOME"]), Path(os.environ["CODEX_HOME"])
with open({log!r}, "a") as sink:
    sink.write(json.dumps({{"codex_home": str(store), "home": sorted(str(p.relative_to(home)) for p in home.rglob("*")),
                            "store": sorted(p.name for p in store.iterdir())}}) + "\n")
with open(store / "auth.json", "a") as login:
    login.write("+refreshed")
(store / "config.toml").write_text("left behind\n")
if Path({fail!r}).exists():
    sys.stdout.write("partial")
    sys.stderr.write("ERROR: 401 Unauthorized Bearer sk-live-SECRETSECRET1")
    sys.exit(1)
print("OK")
"""


@pytest.fixture
def proof_c1(fx, tmp_path, monkeypatch):
    """Check 8(c1) offline: the proof run against the launch fixture's folders, the test's own user standing in for
    the worker behind the fake sudo, a fake `codex`, the worker's own login in the store and a Founder HOME."""
    check = _proof_module()
    monkeypatch.setattr(check, "WORKER", USER)
    log = install_fake_sudo(tmp_path / "proof-sudo", monkeypatch)
    store = worker_store(fx)
    store.mkdir(parents=True, mode=0o700)
    (store / "auth.json").write_text(WORKER_LOGIN)
    (store / "auth.json").chmod(0o600)
    founder = tmp_path / "founder"
    for name, text in LOGINS.items():
        (founder / name).parent.mkdir(parents=True, exist_ok=True)
        (founder / name).write_text(text)
    codex, sessions, fail = tmp_path / "bin" / "codex", tmp_path / "codex.log", tmp_path / "fail"
    codex.parent.mkdir()
    codex.write_text(FAKE_CODEX.format(python=sys.executable, log=str(sessions), fail=str(fail)))
    codex.chmod(0o755)
    prepared, checked = [], []
    prepare, login = work_registry.prepare_worker_session, work_registry.worker_login_present
    monkeypatch.setattr(work_registry, "prepare_worker_session", lambda *a: (prepared.append(a), prepare(*a))[1])
    monkeypatch.setattr(work_registry, "worker_login_present", lambda *a: (checked.append(a), login(*a))[1])
    from types import SimpleNamespace
    return SimpleNamespace(check=check, log=log, store=store, founder=founder, codex=codex, sessions=sessions,
                           fail=fail, prepared=prepared, checked=checked,
                           home=launch_root(fx.loaded().configuration) / "worker" / "home", fx=fx)


def _run_c1(proof, capsys):
    founder = proof.founder / ".codex/auth.json"
    before = os.stat(founder)
    with recorded_opens() as opens:
        passed = proof.check.check_c1([str(proof.codex), "exec", "-"], proof.home, proof.founder,
                                      proof.fx.configuration_file, PROJECT)
    after = os.stat(founder)
    assert not [path for path in opens if path.startswith((str(proof.founder / ".codex"),
                                                           str(proof.founder / ".claude")))]
    assert (before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns)
    return passed, json.loads(capsys.readouterr().out)


def test_check_8c1_runs_two_consecutive_invocations_each_prepared_by_the_candidates_own_session_preparation(
        proof_c1, capsys):
    """Check 8(c1) (revision 8): two consecutive real invocations with the same persistent CODEX_HOME; each first
    passes the same worker-run login check as `prepare`, then is prepared by the candidate's own
    `prepare_worker_session` (the proof holds no preparation code); each starts with a HOME of only .gitconfig and a
    store of only auth.json; the store's auth.json is then a regular worker-owned 0600 file (stat as the worker); the
    Founder's ~/.codex/auth.json is never opened and keeps its inode, size and modification time."""
    passed, line = _run_c1(proof_c1, capsys)
    assert passed and line["check"] == "8(c1)" and line["status"] == "PASS", line
    store = proof_c1.store
    environment = {"HOME": str(proof_c1.home), "TMPDIR": str(proof_c1.home.parent / "tmp"), "CODEX_HOME": str(store)}
    configuration = proof_c1.fx.loaded().configuration
    packets = configuration.repositories[configuration.packets_repository].clone
    assert proof_c1.prepared == [(USER, environment, packets, proof_c1.home.parent.parent / "intake.git")] * 2
    assert proof_c1.checked == [(USER, environment, store)] * 2
    sessions = [json.loads(text) for text in proof_c1.sessions.read_text().splitlines()]
    assert sessions == [{"codex_home": str(store), "home": [".gitconfig"], "store": ["auth.json"]}] * 2
    assert [entry["returncode"] for entry in line["invocations"]] == [0, 0]
    assert line["auth_json"] == {"owner": USER, "mode": "600", "type": "regular file"}
    assert line["founder_login_unchanged"] is True
    assert (store / "auth.json").read_text() == WORKER_LOGIN + "+refreshed+refreshed"  # refreshes persist
    assert not hasattr(proof_c1.check, "PROVIDER_LOGIN_FILES")


def test_check_8c1_without_the_workers_login_fails_before_any_session(proof_c1, capsys):
    """Check 8(c1): the same login check as `prepare` runs first; without the worker's own login nothing runs."""
    (proof_c1.store / "auth.json").unlink()
    passed, line = _run_c1(proof_c1, capsys)
    assert not passed and line["status"] == "FAIL"
    assert line["reason"] == f"worker provider login missing: {proof_c1.store}"
    assert proof_c1.prepared == [] and not proof_c1.sessions.exists()


def test_check_8c1_keeps_a_bounded_redacted_tail_of_a_failed_provider_session(proof_c1, capsys):
    """A failed real provider session records the tails of its standard output and error, redacted."""
    proof_c1.fail.write_text("")
    passed, line = _run_c1(proof_c1, capsys)
    assert not passed and line["status"] == "FAIL"
    first = line["invocations"][0]
    assert first["returncode"] == 1 and first["stdout_tail"] == "partial"
    assert "401 Unauthorized" in first["stderr_tail"] and "SECRETSECRET1" not in first["stderr_tail"]


# --- VERIFIER-INFRASTRUCTURE-RETRY-AND-DIAGNOSTICS ------------------------------------------------------------------

def _verifier_plan(fx: Launch, *steps: str) -> None:
    (fx.root / "verifier-plan.json").write_text(json.dumps(list(steps)))


def _outcomes(fx: Launch, identity: str, role: str) -> list[dict]:
    path = launch_root(fx.loaded().configuration) / "invocation-journal.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines()]
    return [r for r in records if r.get("event") == "invocation-outcome" and r.get("work_identity") == identity
            and r.get("role") == role]


def _verified(fx: Launch, *steps: str):
    """An authorized item launched through its PRODUCER to VERIFY, with the VERIFIER's next steps planned."""
    item = fx.authorized("UNIT")
    fx.launch(item.id)
    _verifier_plan(fx, *steps)
    state = fx.loaded().coordinator(None, None).state(item.id)
    assert state.stage is LifecycleStage.VERIFY
    return item, state


def test_a_verifier_that_ends_without_a_verdict_is_retried_on_the_same_candidate(fx):
    """Checks 1 and 2: a VERIFIER process that exits non-zero with no verdict (here after a network-style error)
    leaves the item at VERIFY on the same candidate; the next launch runs a fresh VERIFIER that accepts, without a
    second PRODUCER. The process's bounded diagnostics are in the invocation journal after the launcher exited."""
    item, before = _verified(fx, "exit")
    fx.launch(item.id)
    state = fx.loaded().coordinator(None, None).state(item.id)
    assert (state.stage, state.outcome) == (LifecycleStage.VERIFY, "verifier-retry")
    assert state.candidate == before.candidate and state.record["verifier_retries"] == 1
    assert state.record["verifier_failure"] == "failure" and not state.record.get("rejections")
    [failed] = _outcomes(fx, item.id, "VERIFIER")
    process = failed["process"]
    assert (failed["kind"], failed["cause"], process["exit_status"]) == ("failure", "network-or-provider", 1)
    assert len(process["stderr_tail"]) == 4000 and process["stderr_tail"].endswith("(https://provider.invalid/)\n")
    assert process["executable"] == Path(str(fx.codex)).name
    fx.launch(item.id)
    state = fx.loaded().coordinator(None, None).state(item.id)
    assert state.stage is LifecycleStage.ACCEPT and state.candidate == before.candidate
    assert (len(fx.runs("PRODUCER")), len(fx.runs("VERIFIER"))) == (1, 2)
    assert [r["cause"] for r in _outcomes(fx, item.id, "VERIFIER")] == ["network-or-provider", "accept"]


def test_a_malformed_verdict_is_retried_not_a_rejection(fx):
    """Check 4."""
    item, before = _verified(fx, "malformed")
    fx.launch(item.id)
    state = fx.loaded().coordinator(None, None).state(item.id)
    assert (state.stage, state.outcome, state.record["verifier_failure"]) == (
        LifecycleStage.VERIFY, "verifier-retry", "verdict-malformed")
    assert state.candidate == before.candidate and not state.record.get("rejections")
    assert _outcomes(fx, item.id, "VERIFIER")[-1]["cause"] == "malformed-verdict"


def test_a_valid_reject_is_still_a_rejection(fx):
    """Check 3: a valid REJECT takes the normal rework path."""
    item, _ = _verified(fx, "reject")
    fx.launch(item.id)
    state = fx.loaded().coordinator(None, None).state(item.id)
    assert state.stage is LifecycleStage.IMPLEMENT and state.record["rejections"] == 1
    assert state.record["findings"][-1]["source"] == "verifier"
    assert _outcomes(fx, item.id, "VERIFIER")[-1]["cause"] == "reject"


def test_verifier_retries_end_in_a_typed_infrastructure_hold(fx):
    """Check 5: after VERIFIER_RETRY_LIMIT retries in a row, a typed hold naming the infrastructure, never a verdict,
    a rejection or a PRODUCER cycle."""
    item, before = _verified(fx, "exit", "exit", "exit")
    for retries in (1, 2):
        fx.launch(item.id)
        assert fx.loaded().coordinator(None, None).state(item.id).outcome == "verifier-retry"
    fx.launch(item.id)
    state = fx.loaded().coordinator(None, None).state(item.id)
    assert (state.stage, state.outcome, state.record["hold_reason"]) == (
        LifecycleStage.VERIFY, "authority-block", "verifier-infrastructure-exhausted:failure")
    assert state.candidate == before.candidate and not state.record.get("rejections")
    assert (len(fx.runs("PRODUCER")), len(fx.runs("VERIFIER"))) == (1, 3)
    [request] = [r for r in fx.store.read_state("registry", "decision-inbox")[1]["open"].values()
                 if r["work_item"] == item.id]
    assert "no engineering judgment" in request["reason"]


def test_a_new_candidate_starts_with_no_verifier_retries(fx):
    """Check 6. The retry count belongs to one candidate: after a rejection and a new PRODUCER candidate it starts
    again."""
    item = fx.authorized("UNIT", budget_policy={"maximum_attempts": 3, "hard_wall_clock_seconds": 120, "cancellation_limit": 1})
    fx.launch(item.id)
    _verifier_plan(fx, "exit", "reject", "exit", "exit")
    for _ in range(2):
        fx.launch(item.id)
    assert fx.loaded().coordinator(None, None).state(item.id).stage is LifecycleStage.IMPLEMENT
    fx.launch(item.id)
    state = fx.loaded().coordinator(None, None).state(item.id)
    assert state.stage is LifecycleStage.VERIFY and state.record["verifier_retries"] == 0
    for retries in (1, 2):
        fx.launch(item.id)
        state = fx.loaded().coordinator(None, None).state(item.id)
        assert (state.outcome, state.record["verifier_retries"]) == ("verifier-retry", retries)


# --- CARD-FOLLOWS-STAGE: canonical state -> durable obligation -> card projector -> read-back -> retired ----------
# The board reflects canonical Work state; it does not determine canonical Work state.

def _card_writes(monkeypatch) -> list[str]:
    written: list[str] = []
    project = work_registry.WorkRegistry._project_card

    def recording(self, identity, stage, revision):
        written.append(stage)
        return project(self, identity, stage, revision)
    monkeypatch.setattr(work_registry.WorkRegistry, "_project_card", recording)
    return written


def _pending(closing: Closing) -> tuple:
    return closing.fx.store.pending_projections("registry")


def test_the_card_follows_the_canonical_stage_and_launch_never_needs_it_ready(closing, monkeypatch):
    """IMPLEMENT is projectable while the PRODUCER works (its obligation is committed before the worker starts); the
    next launches run although the card is no longer READY."""
    from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
    item = closing.fx.authorized("UNIT", **FIXED)
    written = _card_writes(monkeypatch)
    start = RealWorkerProvider.start
    mid_run = []

    def projected_first(self, invocation, *args, **kwargs):  # the projector's pass while the worker runs
        if invocation.role == "PRODUCER":
            closing.fx.loaded().project_cards()
            mid_run.append(closing.card(item.id))
        return start(self, invocation, *args, **kwargs)
    monkeypatch.setattr(RealWorkerProvider, "start", projected_first)
    with closing.fx.loaded().card_projection(interval=60):
        closing.fx.launch(item.id)
    assert mid_run == ["IMPLEMENT"] and closing.card(item.id) == "VERIFY" and _pending(closing) == ()
    with closing.fx.loaded().card_projection(interval=60):
        closing.fx.launch(item.id)  # the card says VERIFY: resolved from the registry record
    assert closing.state(item.id).stage is LifecycleStage.ACCEPT and closing.card(item.id) == "ACCEPT"
    closing.close(item.id)
    closing.fx.loaded().project_cards()
    assert closing.card(item.id) == "DONE" and written == ["IMPLEMENT", "VERIFY", "ACCEPT", "DONE"]


def test_a_crash_after_the_commit_and_before_any_projection_is_caught_up(closing):
    item = closing.fx.authorized("UNIT", **FIXED)
    closing.fx.launch(item.id)  # no projector ran: the process "crashed" after its commits
    assert closing.card(item.id) == "READY" and [a for a, _ in _pending(closing)] == [f"factory:{item.id}"]
    assert closing.fx.loaded().project_cards() == 1  # a fresh projector
    assert closing.card(item.id) == "VERIFY" and _pending(closing) == ()


def test_a_crash_after_the_card_write_and_before_its_acknowledgement_replays_safely(closing, monkeypatch):
    """The obligation is retired only after the card reads back; a crash in between leaves it outstanding and the
    next pass writes the same status again."""
    item = closing.fx.authorized("UNIT", **FIXED)
    closing.fx.launch(item.id)
    written = _card_writes(monkeypatch)
    retire = SQLiteOperationalStore.retire_projection

    def crashing(self, profile, aggregate, revision):
        raise RuntimeError("crash before the acknowledgement")
    monkeypatch.setattr(SQLiteOperationalStore, "retire_projection", crashing)
    with pytest.raises(RuntimeError):
        closing.fx.loaded().project_cards()
    assert closing.card(item.id) == "VERIFY" and len(_pending(closing)) == 1  # written, not acknowledged
    monkeypatch.setattr(SQLiteOperationalStore, "retire_projection", retire)
    assert closing.fx.loaded().project_cards() == 1
    assert written == ["VERIFY", "VERIFY"] and closing.card(item.id) == "VERIFY" and _pending(closing) == ()


def test_a_late_older_obligation_never_moves_the_card_backward(closing, monkeypatch):
    """An obligation carries no status: a late one for an old revision projects the CURRENT canonical stage."""
    item = closing.accepted()
    closing.fx.loaded().project_cards()
    assert closing.card(item.id) == "ACCEPT" and _pending(closing) == ()
    with sqlite3.connect(closing.fx.store.path) as connection:  # a late obligation for the PRODUCER's revision
        connection.execute("INSERT INTO projections VALUES ('registry', ?, 1)", (f"factory:{item.id}",))
    written = _card_writes(monkeypatch)
    assert closing.fx.loaded().project_cards() == 1
    assert written == ["ACCEPT"] and closing.card(item.id) == "ACCEPT" and _pending(closing) == ()


def test_a_card_write_that_does_not_read_back_stays_outstanding_with_a_durable_diagnostic(closing):
    item = closing.fx.authorized("UNIT", **FIXED)
    closing.fx.launch(item.id)
    closing.ignore_status = True  # the board answers the write but keeps its Status
    assert closing.fx.loaded().project_cards() == 0
    assert closing.card(item.id) == "READY" and len(_pending(closing)) == 1
    path = launch_root(closing.fx.loaded().configuration) / "projection-diagnostics.jsonl"
    [record] = [json.loads(line) for line in path.read_text().splitlines()]
    assert (record["identity"], record["state"], record["answered"], record["error"]) == (
        item.id, "VERIFY", -1, "read back another status")
    closing.ignore_status = False
    assert closing.fx.loaded().project_cards() == 1 and closing.card(item.id) == "VERIFY"


def test_after_a_decision_a_started_item_launches_without_a_ready_card(closing, monkeypatch):
    """A recorded decision drops the item's `correlation`; it is resolved from its PRODUCER's launch."""
    item = closing.accepted()
    monkeypatch.setattr(LandingAuthority, "land", lambda self, order: "refused:fixture")
    closing.close(item.id)
    closing.fx.loaded().project_cards()
    assert closing.state(item.id).outcome == "authority-block" and closing.card(item.id) == "ACCEPT"
    assert closing.fx.loaded().decide(item.id, "authorize", QUOTE)["answer"] is None
    assert closing.state(item.id).record.get("correlation") is None
    sessions = len(closing.fx.runs("CLOSURE"))
    closing.close(item.id)
    assert len(closing.fx.runs("CLOSURE")) == sessions + 1


def test_start_runs_a_started_item_whose_card_has_moved_on(closing):
    item = closing.fx.authorized("UNIT", **FIXED)
    closing.fx.launch(item.id)
    closing.fx.loaded().project_cards()
    assert closing.card(item.id) == "VERIFY"  # not on the READY board any more
    closing.fx.loaded(Owners("terminated")).launcher().start()  # VERIFIER, then CLOSURE, in one call
    assert closing.state(item.id).stage is LifecycleStage.DONE


def test_a_projector_overtaken_by_a_newer_commit_reowes_and_the_card_converges(closing, monkeypatch):
    """Two projectors overlap: B writes and retires the newer stage while A's older write is still in flight; A's
    write lands last, so A re-owes the projection and the next pass shows the newest canonical stage."""
    item = closing.fx.authorized("UNIT", **FIXED)
    closing.fx.launch(item.id)  # VERIFY, not yet projected
    project = work_registry.WorkRegistry._project_card
    overtaken = []

    def in_flight(self, identity, stage, revision):
        if not overtaken:
            overtaken.append(stage)
            closing.fx.launch(item.id)  # a newer commit: ACCEPT
            assert closing.fx.loaded().project_cards() == 1  # projector B: ACCEPT written, obligation retired
        return project(self, identity, stage, revision)  # A's VERIFY lands last
    monkeypatch.setattr(work_registry.WorkRegistry, "_project_card", in_flight)
    closing.fx.loaded().project_cards()  # projector A
    assert overtaken == ["VERIFY"] and closing.card(item.id) == "VERIFY" and len(_pending(closing)) == 1
    monkeypatch.setattr(work_registry.WorkRegistry, "_project_card", project)
    closing.fx.loaded().project_cards()
    assert closing.card(item.id) == "ACCEPT" and _pending(closing) == ()


def test_an_overtaken_write_whose_read_back_fails_is_still_reowed(closing, monkeypatch):
    """A's VERIFY change lands after B wrote and retired ACCEPT, then A's read-back fails: A still re-owes."""
    item = closing.fx.authorized("UNIT", **FIXED)
    closing.fx.launch(item.id)
    project = work_registry.WorkRegistry._project_card
    overtaken = []

    def in_flight(self, identity, stage, revision):
        if not overtaken:
            overtaken.append(stage)
            closing.fx.launch(item.id)  # ACCEPT
            assert closing.fx.loaded().project_cards() == 1  # projector B
            project(self, identity, stage, revision)  # A's change lands ...
            return False  # ... and its read-back fails
        return project(self, identity, stage, revision)
    monkeypatch.setattr(work_registry.WorkRegistry, "_project_card", in_flight)
    closing.fx.loaded().project_cards()
    assert closing.card(item.id) == "VERIFY" and len(_pending(closing)) == 1
    closing.fx.loaded().project_cards()
    assert closing.card(item.id) == "ACCEPT" and _pending(closing) == ()
