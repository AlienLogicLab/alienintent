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
from alienintent.control_plane.application.operator import exclusive_launch_work
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.domain.release import ReleaseSource
from alienintent.invocation_runtime.adapters.git_worktree import ref_safe
from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
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

    def loaded(self, ownership=None) -> WorkRegistry:
        """A registry built as `work launch` builds it in its own process."""
        return WorkRegistry(load_project_configuration(self.configuration_file, PROJECT), transport=self.github,
                            host_configuration=self.host, ownership=ownership)

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


# --- RESTART-CONTINUATION: restart continuation for registry launches -------------------------------------------------

class Owners(ProcOwnership):
    """The existing ProcOwnership, with the owner state or the owned work stated by the test where given."""

    def __init__(self, state: str | None = None, work: tuple[int, ...] | None = None) -> None:
        super().__init__()
        self.state, self.work = state, work

    def owner_state(self, owner):
        return self.state or super().owner_state(owner)

    def owned_work(self, invocation_id, owner=None):
        return super().owned_work(invocation_id, owner) if self.work is None else self.work


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
    worktree = root / "workspaces" / correlation
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
