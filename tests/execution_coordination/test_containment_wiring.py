"""Actual-diff containment is wired where it must run (PLAN-AUTHORITY-INHERITANCE revision 3, change 3).

By source inspection and by behaviour: `RealWorkerProvider._produce` applies the containment rule to an automatic-on
candidate before `publication-started`, publishing nothing on a violation; `RegistryClosure.close` refuses a scope
violation with a closure hold before any order is journaled or landed. A candidate that removes either call fails
here, in the factory's regression gate. Repositories, paths and contracts are TEST DATA.
"""
from __future__ import annotations

import ast
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from alienintent.composition.work_registry import RegistryClosure
from alienintent.context_assembly.domain.compilation import contract_from_payload
from alienintent.context_assembly.ports.work_item_repository import RepositoryLocation
from alienintent.execution_coordination.domain.closure import ACTIONS, hold
from alienintent.execution_coordination.domain.contract import BudgetPolicy
from alienintent.execution_coordination.domain.custody import CandidateRef
from alienintent.execution_coordination.domain.plan_authority import PLAN_PATH, PlanAuthority, parse_scope
from alienintent.execution_coordination.domain.release import ReleaseAuthorization
from alienintent.execution_coordination.domain.scope_containment import NO_PLAN_AUTHORITY, NO_TRUSTED_START
from alienintent.execution_coordination.ports.worker_provider import CLOSURE, WorkerInvocation
from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter
from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal
from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole
from tests.context_assembly.test_work_contract import satisfiable_payload

SRC = Path(__file__).resolve().parents[2] / "src" / "alienintent"
PROTECTED = ("docs/decisions/", "src/protected.py")


def plan_at(digest: str, label: str = "FIXTURE") -> PlanAuthority:
    """A live plan authority with PROTECTED and one obligation `label` over `src/` (TEST DATA)."""
    scope = {"target_repositories": ["AlienLogicLab/alienintent"], "capabilities": ["python"],
             "budget_caps": {"maximum_attempts": 3, "hard_wall_clock_seconds": 3600, "cancellation_limit": 1,
                             "retry_limit": 1, "concurrency_limit": 1, "hard_required_dimensions": ["wall-clock"]},
             "protected_paths": list(PROTECTED),
             "obligations": [{"label": label, "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
                              "allowed_paths": ["src/"], "intent": "Fixture intent.",
                              "acceptance": [{"id": f"{label}-A1", "text": "The fixture works."}],
                              "depends_on": [], "satisfied_by": []}]}
    text = f"```json alienintent-plan-authority\n{json.dumps(scope)}\n```\n"
    return PlanAuthority(PLAN_PATH, "c" * 40, digest, "sha256:" + "b" * 64, "Founder", "approved", parse_scope(text))


D1, D2 = "sha256:" + "1" * 64, "sha256:" + "2" * 64


def _method(path: Path, cls: str, name: str) -> ast.FunctionDef:
    module = ast.parse(path.read_text(encoding="utf-8"))
    owner = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == cls)
    return next(node for node in owner.body if isinstance(node, ast.FunctionDef) and node.name == name)


def _calls(function: ast.FunctionDef, name: str) -> list[int]:
    """Lines of every call of `name` or `self.name` in `function`."""
    return [node.lineno for node in ast.walk(function) if isinstance(node, ast.Call) and (
        isinstance(node.func, ast.Name) and node.func.id == name
        or isinstance(node.func, ast.Attribute) and node.func.attr == name)]


def _uses(function: ast.FunctionDef, name: str) -> list[int]:
    return [node.lineno for node in ast.walk(function) if isinstance(node, ast.Name) and node.id == name]


def test_source_the_producer_checks_containment_before_publication():
    worker = SRC / "invocation_runtime" / "application" / "real_worker.py"
    produce = _method(worker, "RealWorkerProvider", "_produce")
    checked, published = _calls(produce, "_scope_violations"), _uses(produce, "PUBLICATION_STARTED")
    assert len(checked) == 1 and published and checked[0] < min(published)
    assert _calls(_method(worker, "RealWorkerProvider", "_scope_violations"), "contained")


def test_source_closure_checks_containment_against_the_landing_base_before_every_order():
    """In `_order`, which every first order and every re-order at a new head runs through: the check on the diff
    from the landing `base`, before the merge is built and before the order is journaled."""
    registry = SRC / "composition" / "work_registry.py"
    order = _method(registry, "RegistryClosure", "_order")
    calls = [node for node in ast.walk(order) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == "_scope_violations"]
    assert len(calls) == 1 and any(isinstance(arg, ast.Name) and arg.id == "base" for arg in calls[0].args)
    assert calls[0].lineno < min(_calls(order, "_build")) and calls[0].lineno < min(_calls(order, "append"))
    assert _calls(_method(registry, "RegistryClosure", "_scope_violations"), "contained")


# --- behaviour: the PRODUCER ----------------------------------------------------------------------------------------


def git(path: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, text=True).stdout.strip()


def change(path: str, link: bool = False) -> str:
    """A PRODUCER process that commits one new file (or symbolic link) at `path`."""
    make = "p.symlink_to('base.txt')" if link else "p.write_text('change')"
    return (f"import pathlib, subprocess; p = pathlib.Path({path!r}); p.parent.mkdir(parents=True, exist_ok=True); "
            f"{make}; subprocess.run(['git', 'add', {path!r}], check=True); "
            "subprocess.run(['git', 'commit', '-qm', 'change'], check=True)")


class Forged(GitSourceControl):
    """A reader whose first answer (the starting revision the worker reports) is `claim`."""

    def __init__(self, claim: str) -> None:
        self.claim, self.calls = claim, 0

    def revision(self, workspace: Path) -> str:
        self.calls += 1
        return self.claim if self.calls == 1 else super().revision(workspace)


def produce(tmp_path: Path, command: str, policy: str, protected=lambda: PROTECTED, *, trusted: bool = True,
            forge=None):
    """One PRODUCER run; with `trusted` the preparation names the starting revision (as `work context` does), and
    `forge(source)` may add history and answer the start the worker will claim."""
    remote, source = tmp_path / "remote.git", tmp_path / "source"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    git(source, "config", "user.email", "test@example.invalid")
    git(source, "config", "user.name", "Test")
    (source / "base.txt").write_text("base")
    git(source, "add", "base.txt")
    git(source, "commit", "-qm", "base")
    git(source, "remote", "add", "origin", str(remote))
    starting = git(source, "rev-parse", "HEAD")
    reader = GitSourceControl() if forge is None else Forged(forge(source))
    preparation = SimpleNamespace(prepare=lambda *_: starting, published=lambda *_: None) if trusted else None
    process = CliWorkerProvider("python", sys.executable, ("-c", command), "explicit",
                                frozenset({"wall-clock", "cancellation"}))
    invocation = WorkerInvocation("work", "producer-1")
    grant = CapabilityGrant("grant", "work", invocation.correlation_id, InvocationRole.PRODUCER, "issue", "repo",
                            frozenset({"process-control", "git-write"}), int(time.time()) + 100)
    journal = JsonlInvocationJournal(tmp_path / "journal.jsonl", time.time)
    worker = RealWorkerProvider(process, reader, source, "origin", "candidate/producer-1",
                                tmp_path / "verifier", grant, "repo",
                                GitWorktreeAdapter(source, tmp_path / "worktrees"),
                                now=time.time, sleep=time.sleep, journal=journal, protected_paths=protected,
                                preparation=preparation)
    contract = contract_from_payload(satisfiable_payload("work", release_policy=policy, authorized_scope=["src/"]))
    outcome = worker.start(invocation, contract, frozenset(), BudgetPolicy(hard_wall_clock_seconds=5,
                                                                           cancellation_limit=1))
    published = git(remote, "for-each-ref", "--format=%(refname)", "refs/heads/candidate")
    started = [r for r in journal.records() if r.get("event") == "publication-started"]
    return outcome, published, started


@pytest.mark.parametrize(("command", "words"), [
    (change("docs/notes.md"), "docs/notes.md is outside the authorized scope"),
    (change("src/protected.py"), "src/protected.py is a protected path"),
    (change("src/link", link=True), "src/link is a symbolic link (mode 120000)"),
], ids=["outside", "protected", "symlink"])
def test_an_automatic_on_candidate_outside_its_boundary_is_never_published(tmp_path, command, words):
    outcome, published, started = produce(tmp_path, command, "automatic-on")
    assert outcome.kind == "scope-violation" and outcome.candidate is None
    assert any(words in finding for finding in outcome.findings), outcome.findings
    assert (published, started) == ("", [])


def test_without_a_plan_authority_no_automatic_on_candidate_is_published(tmp_path):
    outcome, published, started = produce(tmp_path, change("src/a.py"), "automatic-on", protected=lambda: None)
    assert (outcome.kind, outcome.findings, published, started) == ("scope-violation", (NO_PLAN_AUTHORITY,), "", [])


def test_without_a_trusted_starting_revision_no_automatic_on_candidate_is_published(tmp_path):
    outcome, published, started = produce(tmp_path, change("src/a.py"), "automatic-on", trusted=False)
    assert (outcome.kind, outcome.findings, published, started) == ("scope-violation", (NO_TRUSTED_START,), "", [])


def test_a_worker_reported_start_cannot_narrow_the_diff(tmp_path):
    """The worker fast-forwards to a side commit that adds a file outside the scope, then commits inside it, and
    reports the side commit as its start: the diff still runs from the trusted starting revision."""
    def side(source: Path) -> str:
        git(source, "checkout", "-q", "-b", "side")
        (source / "docs").mkdir()
        (source / "docs" / "notes.md").write_text("side")
        git(source, "add", "docs/notes.md")
        git(source, "commit", "-qm", "side")
        claim = git(source, "rev-parse", "HEAD")
        git(source, "checkout", "-q", "-")
        return claim
    prefix = "import pathlib, subprocess; "
    command = prefix + "subprocess.run(['git', 'merge', '-q', '--ff-only', 'side'], check=True); " + \
        change("src/a.py").removeprefix(prefix)
    outcome, published, started = produce(tmp_path, command, "automatic-on", forge=side)
    assert outcome.kind == "scope-violation" and (published, started) == ("", [])
    assert any("docs/notes.md is outside the authorized scope" in finding for finding in outcome.findings)


@pytest.mark.parametrize(("command", "policy"), [(change("src/a.py"), "automatic-on"),
                                                 (change("docs/notes.md"), "explicit-human-off")],
                         ids=["contained", "explicit"])
def test_a_contained_or_explicit_candidate_is_published(tmp_path, command, policy):
    outcome, published, started = produce(tmp_path, command, policy)
    assert outcome.kind == "success" and published == "refs/heads/candidate/producer-1" and len(started) == 1


# --- behaviour: CLOSURE ---------------------------------------------------------------------------------------------


def close(tmp_path: Path, path: str, policy: str, *, revert_main: bool = False, authority=None, current=None,
          reconcile_under=None, decisions: list | None = None):
    """CLOSURE of a candidate that adds `path` on top of its release baseline; with `revert_main`, main then changes
    the protected `docs/decisions/plan.md` and the candidate merges main and reverts that file. Without a Landing
    Authority a landing that may proceed ends at `ready-to-land`."""
    remote, clone = tmp_path / "remote.git", tmp_path / "clone"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(clone)], check=True)
    for key, value in (("user.email", "test@example.invalid"), ("user.name", "Test")):
        git(clone, "config", key, value)
    (clone / "base.txt").write_text("base")
    (clone / "docs" / "decisions").mkdir(parents=True)
    (clone / "docs" / "decisions" / "plan.md").write_text("approved")
    git(clone, "add", "base.txt", "docs/decisions/plan.md")
    git(clone, "commit", "-qm", "base")
    git(clone, "remote", "add", "origin", str(remote))
    git(clone, "push", "-q", "origin", "main")
    baseline = git(clone, "rev-parse", "HEAD")
    git(clone, "checkout", "-q", "-b", "candidate/c-1")
    (clone / path).parent.mkdir(parents=True, exist_ok=True)
    (clone / path).write_text("change")
    git(clone, "add", path)
    git(clone, "commit", "-qm", "candidate")
    if revert_main:
        git(clone, "checkout", "-q", "main")
        (clone / "docs" / "decisions" / "plan.md").write_text("changed on main after the release")
        git(clone, "commit", "-qam", "main changes the plan")
        git(clone, "push", "-q", "origin", "main")
        git(clone, "checkout", "-q", "candidate/c-1")
        git(clone, "merge", "-q", "--no-edit", "main")
        git(clone, "checkout", baseline, "--", "docs/decisions/plan.md")
        git(clone, "commit", "-qm", "revert the plan to the release baseline")
    git(clone, "push", "-q", "origin", "candidate/c-1")
    revision = git(clone, "rev-parse", "HEAD")
    # The scope never crosses PROTECTED (`src/` would be an ancestor of `src/protected.py`): inside the authority.
    payload = satisfiable_payload("work", release_policy=policy, authorized_scope=["src/a.py"],
                                  authority_issuer="plan-authority:" + D1 if policy == "automatic-on" else "Founder",
                                  authority_references=[f"{PLAN_PATH} obligation:FIXTURE"])
    packet = f"# Work unit\n\n```json alienintent-contract\n{json.dumps(payload)}\n```\n".encode()
    plans = [plan_at(D1) if current is None else current]
    registry = SimpleNamespace(
        configuration=SimpleNamespace(packets_repository="repo", repositories={
            "repo": RepositoryLocation(clone, "origin", "main", "alienintent/work-packets")}),
        records=SimpleNamespace(show=lambda _: SimpleNamespace(packet=packet, item=SimpleNamespace(label="UNIT"))),
        assessment=SimpleNamespace(authorizations=SimpleNamespace(release_authorization=lambda identity: (
            ReleaseAuthorization(identity, "sha256:" + "e" * 64, True, baseline, "inherited")))),
        plan_approval=SimpleNamespace(current=lambda: plans[-1]), store=SimpleNamespace(read_state=lambda *_: (0, {})),
        _owner_decision=(decisions if decisions is not None else []).append)
    request = json.dumps({"identity": "work", "revision": revision, "actions": list(ACTIONS), "findings": []})
    preparation = SimpleNamespace(read=lambda _: request.encode(), closure_request_path=lambda _: tmp_path / "r.json")
    journal = JsonlInvocationJournal(tmp_path / "journal.jsonl", time.time)
    candidate = CandidateRef.source_revision("sha256:" + sha256(revision.encode()).hexdigest(),
                                             f"git:{remote}#candidate/c-1@{revision}")
    closure = RegistryClosure(registry, tmp_path / "launch", journal, preparation, authority)
    invocation = WorkerInvocation("work", "closure-1", role=CLOSURE)
    receipts, findings = closure.close(invocation, candidate, journal)
    if reconcile_under is not None:  # another plan revision becomes current, then the journaled order is re-landed
        plans.append(reconcile_under)
        receipts, findings = closure.reconcile(invocation, candidate, tuple(
            r for r in journal.records() if r.get("event") == "closure-ordered"))
    return revision, findings, [r for r in journal.records() if r.get("event") == "closure-ordered"], \
        git(clone, "rev-parse", "main")


def test_closure_refuses_an_automatic_on_candidate_outside_its_boundary_before_any_order(tmp_path):
    revision, findings, orders, head = close(tmp_path, "docs/decisions/x.md", "automatic-on")
    assert findings[0] == hold("scope-violation", head, revision) and orders == []
    assert any("docs/decisions/x.md is outside the authorized scope" in finding for finding in findings[1:])


def test_closure_refuses_a_candidate_outside_the_current_plan_authority_and_raises_one_owner_decision(tmp_path):
    """Released under D1, the tip is D2 at CLOSURE and no longer grants obligation FIXTURE: the contract is checked
    against the live authority at the landing gate, held before any order, with an owner-decision reason and the
    owner-decision attention item."""
    landed, decisions = [], []
    revision, findings, orders, head = close(tmp_path, "src/a.py", "automatic-on", current=plan_at(D2, "OTHER"),
                                             authority=SimpleNamespace(land=landed.append), decisions=decisions)
    assert findings[0] == hold("scope-violation", head, revision) and (orders, landed) == ([], [])
    assert any(finding.startswith("owner-decision-required: authority_references: obligation FIXTURE")
               for finding in findings[1:])
    assert decisions == ["work"]


def test_closure_lands_a_candidate_released_under_an_older_plan_revision_still_inside_the_tip(tmp_path):
    """PLAN-TIP-AUTHORITY-RUNTIME-FIX: released under D1, the tip is D2 and still grants obligation FIXTURE: the
    candidate is revalidated against the tip and reaches its landing."""
    _, findings, _, _ = close(tmp_path, "src/a.py", "automatic-on", current=plan_at(D2))
    assert [finding.split(":", 1)[0] for finding in findings] == ["ready-to-land"]


def test_a_journaled_order_is_not_re_landed_after_its_plan_authority_is_replaced(tmp_path):
    """The order was journaled and handed over under D1 (the push did not land); the tip is D2, which no longer
    grants obligation FIXTURE, when the order is re-landed at the same base: held, the Landing Authority is not called
    again."""
    landed = []
    revision, findings, orders, head = close(tmp_path, "src/a.py", "automatic-on", reconcile_under=plan_at(D2, "OTHER"),
                                             authority=SimpleNamespace(land=landed.append))
    assert len(orders) == 1 and len(landed) == 1
    assert findings[0] == hold("scope-violation", head, revision)
    assert any(finding.startswith("owner-decision-required:") for finding in findings[1:])


def test_closure_refuses_a_candidate_that_reverts_a_protected_change_main_made_after_its_release(tmp_path):
    """The release-baseline diff lists only `src/a.py`; what would land is the diff from the landing base (main's
    head), which reverts the protected plan: held before any order is journaled and before the Landing Authority."""
    landed = []
    revision, findings, orders, head = close(tmp_path, "src/a.py", "automatic-on", revert_main=True,
                                             authority=SimpleNamespace(land=landed.append))
    assert findings[0] == hold("scope-violation", head, revision) and (orders, landed) == ([], [])
    assert any("docs/decisions/plan.md is a protected path" in finding for finding in findings[1:])


@pytest.mark.parametrize(("path", "policy"), [("src/a.py", "automatic-on"), ("docs/notes.md", "explicit-human-off")],
                         ids=["contained", "explicit"])
def test_closure_lets_a_contained_or_explicit_candidate_reach_its_landing(tmp_path, path, policy):
    _, findings, _, _ = close(tmp_path, path, policy)
    assert [finding.split(":", 1)[0] for finding in findings] == ["ready-to-land"]
