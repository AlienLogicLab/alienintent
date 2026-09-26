"""The PY-10 live-proof run profile, offline.

Every rule the live run depends on is exercised here against the same code the
sandbox drives — only the GitHub transport and the worker's own task are
recorded. The final test drains a backlog end to end through the real
coordinator, the real worker provider, real Git worktrees and real candidate
custody, so the live run is a rehearsal's environment change rather than the
first time the wiring is tried.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from alienintent.composition.sandbox_run_profile import (
    BacklogRejected,
    ProjectDecisionNotifier,
    SandboxBacklogComposition,
    SandboxRunProfile,
    contract_from_document,
    decision_body,
    descriptor_from_body,
    worker_environment,
)
from alienintent.control_plane.application.decision_inbox import DecisionInbox
from alienintent.execution_coordination.application.factory_coordinator import StopReason
from alienintent.execution_coordination.domain.escalation import DecisionSubmission, HumanDecisionRequired
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.domain.release import ReleaseRequest, ReleaseSource, admit_release
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter, ref_safe
from alienintent.invocation_runtime.domain.runtime import InvocationRole
from tests.composition.test_sandbox_profile import document
from tests.support.feature_regressions import seed_verification_runner
from tests.support.live_github import (
    PRIORITY_FIELD,
    SANDBOX_PROJECT,
    SANDBOX_REPOSITORY,
    STATUS_FIELD,
    RecordedTransport,
    project_graphql,
    rest_answers,
)

WORKER = """#!/bin/bash
set -euo pipefail
invocation="${ALIENINTENT_INVOCATION_ID:?the worker is not told which invocation it is}"
biu="${invocation#launch:}"
biu="${biu%:*}"
test -z "${GIT_CONFIG_COUNT:-}" || { echo "worker inherited a publication credential" >&2; exit 3; }
if [ "${ALIENINTENT_ROLE:-}" = VERIFIER ]; then
  # K2: the verifier accepts the exact revision checked out in its fresh workspace.
  mkdir -p .alienintent
  printf '{"verdict": "accept", "revision": "%s", "findings": []}\n' "$(git rev-parse HEAD)" > .alienintent/verdict.json
  exit 0
fi
mkdir -p docs
printf '%s completed by the factory under %s\\n' "$biu" "$invocation" >> "docs/${biu}.md"
git add -A
git commit -qm "${biu}: factory candidate"
"""


# --- fixtures -----------------------------------------------------------------


def contract_document(identity: str, *, dependencies: tuple[str, ...] = (), capabilities: tuple[str, ...] = ("python",), **overrides) -> dict:
    payload = {
        "identity": identity, "version": "1", "intent": f"record that {identity} was executed by the factory",
        "satisfied_requirement_ids": ["SF-REQ-001"], "fixed_decisions": ["FD-03"],
        "authorized_scope": [f"docs/{identity}.md"], "excluded_scope": ["every other path"],
        "dependencies": list(dependencies), "required_capabilities": list(capabilities),
        "budget_policy": {
            "hard_required_dimensions": ["attempts", "retries"], "maximum_attempts": 1,
            "hard_wall_clock_seconds": 60, "retry_limit": 0, "concurrency_limit": 1, "cancellation_limit": 1,
        },
        "retry_policy": "no-retry", "completion_criteria": [f"docs/{identity}.md records the invocation"],
        "verification_obligations": ["candidate read back from a fresh clone"], "required_evidence": ["artifact-verified"],
        "non_goals": ["anything outside the named note"],
        "candidate_custody_requirements": ["published source revision, independently read back"],
        "release_policy": "automatic-on", "authority_issuer": "PY-10 live proof",
        "authority_references": ["SWF-11"], "target_repositories": [SANDBOX_REPOSITORY],
        "baselines": ["main"], "required_closure_actions": ["candidate-published"],
        "stop_escalation_conditions": ["authority outside the profile"],
        "task": {"note": f"docs/{identity}.md"},
    }
    payload.update(overrides)
    return payload


def project_item(item_id: str, identity: str, *, priority: str, ready_at: str, digest: str, depends_on: tuple[str, ...] = (), contract_path: str | None = None) -> dict:
    body = "\n".join([
        f"biu: {identity}", f"contract: {contract_path or f'biu/{identity}.json'}",
        f"readiness_digest: {digest}", f"depends_on: {', '.join(depends_on)}",
    ])
    return {
        "id": item_id,
        "content": {"id": f"DI_{item_id}", "title": f"{identity} — sandbox task", "body": body},
        "fieldValues": {"nodes": [
            {"name": "READY", "updatedAt": ready_at, "field": {"id": STATUS_FIELD, "name": "Status"}},
            {"name": priority, "updatedAt": ready_at, "field": {"id": PRIORITY_FIELD, "name": "Priority"}},
        ]},
    }


def digest_of(document: dict) -> str:
    return contract_from_document(document).content_digest


def backlog(tmp_path: Path, items: list[dict], documents: dict[str, dict]) -> SandboxBacklogComposition:
    contents = {path: json.dumps(value).encode() for path, value in documents.items()}
    transport = RecordedTransport(rest_answers(contents=contents), project_graphql(items=items))
    return SandboxBacklogComposition(document(tmp_path), tmp_path / "state.sqlite", lambda _: None, transport, lambda: 1758445000.0)


# --- the upstream descriptor --------------------------------------------------


def test_the_project_item_body_carries_the_whole_upstream_descriptor() -> None:
    descriptor = descriptor_from_body(
        "biu: SB-04\ncontract: biu/SB-04.json\nreadiness_digest: sha256:abc\ndepends_on: SB-05, SB-03\n"
    )

    assert (descriptor.identity, descriptor.contract_path) == ("SB-04", "biu/SB-04.json")
    assert descriptor.readiness_digest == "sha256:abc"
    assert descriptor.dependencies == ("SB-05", "SB-03")


@pytest.mark.parametrize("body", [
    None, "", "biu: SB-01", "contract: biu/SB-01.json\nreadiness_digest: sha256:abc",
    "biu: SB-01\ncontract: biu/SB-01.json",
])
def test_an_incomplete_upstream_descriptor_is_refused(body: str | None) -> None:
    with pytest.raises(BacklogRejected):
        descriptor_from_body(body)


def test_an_item_with_no_declared_dependency_imports_none() -> None:
    descriptor = descriptor_from_body("biu: SB-01\ncontract: biu/SB-01.json\nreadiness_digest: sha256:abc")

    assert descriptor.dependencies == ()


# --- the BIU contract document ------------------------------------------------


def test_a_contract_document_becomes_the_immutable_contract_value() -> None:
    contract = contract_from_document(contract_document("SB-01"))

    assert contract.identity == "SB-01"
    assert contract.content_digest.startswith("sha256:")
    assert contract.budget_policy.required_dimensions == ("attempts", "retries", "wall-clock", "concurrency", "cancellation")


def test_a_contract_document_carrying_an_unknown_field_is_refused() -> None:
    with pytest.raises(BacklogRejected, match="unknown field"):
        contract_from_document(contract_document("SB-01", release_authority="whoever"))


def test_a_contract_document_missing_a_binding_field_is_refused() -> None:
    incomplete = contract_document("SB-01")
    incomplete["required_evidence"] = []

    with pytest.raises(BacklogRejected, match="not a valid contract"):
        contract_from_document(incomplete)


def test_two_different_contract_documents_do_not_share_a_digest() -> None:
    assert digest_of(contract_document("SB-01")) != digest_of(contract_document("SB-02"))


# --- ordering: priority, then upstream READY-entry time -----------------------


def test_equal_priority_work_is_ordered_by_the_moment_its_status_became_ready(tmp_path: Path) -> None:
    """AC 3's FIFO key is upstream READY-entry time, not Project listing order."""
    later, earlier = contract_document("SB-LATE"), contract_document("SB-EARLY")
    # The identities are deliberately ordered against the timestamps: an
    # implementation that fell back to item order, or to the Project's own
    # listing order, would answer "SB-LATE" first.
    composed = backlog(tmp_path, [
        project_item("PVTI_a_later", "SB-LATE", priority="P1", ready_at="2026-09-21T11:00:09Z", digest=digest_of(later)),
        project_item("PVTI_z_earlier", "SB-EARLY", priority="P1", ready_at="2026-09-21T11:00:01Z", digest=digest_of(earlier)),
    ], {"biu/SB-LATE.json": later, "biu/SB-EARLY.json": earlier})

    imported = composed.work.import_ready_snapshot()

    assert [item.identity for item in imported] == ["SB-EARLY", "SB-LATE"]
    assert [item.fifo for item in imported] == [0, 1]


def test_work_made_ready_in_the_same_second_falls_back_to_a_deterministic_order(tmp_path: Path) -> None:
    first, second = contract_document("SB-A"), contract_document("SB-B")
    composed = backlog(tmp_path, [
        project_item("PVTI_b", "SB-B", priority="P1", ready_at="2026-09-21T11:00:01Z", digest=digest_of(second)),
        project_item("PVTI_a", "SB-A", priority="P1", ready_at="2026-09-21T11:00:01Z", digest=digest_of(first)),
    ], {"biu/SB-A.json": first, "biu/SB-B.json": second})

    assert [item.identity for item in composed.work.import_ready_snapshot()] == ["SB-A", "SB-B"]


def test_an_item_whose_status_is_not_a_release_status_is_not_imported(tmp_path: Path) -> None:
    ready = contract_document("SB-01")
    item = project_item("PVTI_1", "SB-01", priority="P0", ready_at="2026-09-21T11:00:01Z", digest=digest_of(ready))
    item["fieldValues"]["nodes"][0]["name"] = "IMPLEMENT"
    composed = backlog(tmp_path, [item], {"biu/SB-01.json": ready})

    assert composed.work.import_ready_snapshot() == ()


# --- the per-item contract ----------------------------------------------------


def test_each_imported_item_carries_its_own_contract(tmp_path: Path) -> None:
    first, second = contract_document("SB-01"), contract_document("SB-02")
    composed = backlog(tmp_path, [
        project_item("PVTI_1", "SB-01", priority="P0", ready_at="2026-09-21T11:00:01Z", digest=digest_of(first)),
        project_item("PVTI_2", "SB-02", priority="P1", ready_at="2026-09-21T11:00:02Z", digest=digest_of(second)),
    ], {"biu/SB-01.json": first, "biu/SB-02.json": second})

    imported = composed.work.import_ready_snapshot()

    assert [item.contract.identity for item in imported] == ["SB-01", "SB-02"]
    assert imported[0].contract.content_digest != imported[1].contract.content_digest
    assert all(item.readiness_digest == item.contract.content_digest for item in imported)


def test_a_contract_document_naming_other_work_is_refused(tmp_path: Path) -> None:
    other = contract_document("SB-99")
    composed = backlog(tmp_path, [
        project_item("PVTI_1", "SB-01", priority="P0", ready_at="2026-09-21T11:00:01Z", digest=digest_of(other)),
    ], {"biu/SB-01.json": other})

    with pytest.raises(BacklogRejected, match="does not name the imported work item"):
        composed.work.import_ready_snapshot()


def test_dependency_edges_that_disagree_with_the_contract_are_refused(tmp_path: Path) -> None:
    """Upstream and the contract must agree, or neither can be trusted as the edge."""
    declared = contract_document("SB-04", dependencies=("SB-05",))
    composed = backlog(tmp_path, [
        project_item("PVTI_4", "SB-04", priority="P2", ready_at="2026-09-21T11:00:01Z", digest=digest_of(declared), depends_on=("SB-03",)),
    ], {"biu/SB-04.json": declared})

    with pytest.raises(BacklogRejected, match="dependency edges disagree"):
        composed.work.import_ready_snapshot()


def test_a_readiness_digest_that_no_longer_matches_the_contract_refuses_release(tmp_path: Path) -> None:
    """AC 12's sibling: work released against a contract that has since changed."""
    published = contract_document("SB-01")
    composed = backlog(tmp_path, [
        project_item("PVTI_1", "SB-01", priority="P0", ready_at="2026-09-21T11:00:01Z", digest="sha256:" + "0" * 64),
    ], {"biu/SB-01.json": published})
    item = composed.work.import_ready_snapshot()[0]

    with pytest.raises(ValueError, match="stale readiness reference"):
        admit_release({}, ReleaseRequest(
            item.identity, item.contract, item.readiness_digest, frozenset(item.dependencies),
            frozenset({"python", "filesystem", "process-control"}),
            {dimension: 1 for dimension in item.contract.budget_policy.required_dimensions},
            "test", ReleaseSource.AUTOMATIC_POLICY,
        ))


# --- projection ---------------------------------------------------------------


def test_projection_targets_the_project_item_the_identity_was_imported_from(tmp_path: Path) -> None:
    first, second = contract_document("SB-01"), contract_document("SB-02")
    composed = backlog(tmp_path, [
        project_item("PVTI_1", "SB-01", priority="P0", ready_at="2026-09-21T11:00:01Z", digest=digest_of(first)),
        project_item("PVTI_2", "SB-02", priority="P1", ready_at="2026-09-21T11:00:02Z", digest=digest_of(second)),
    ], {"biu/SB-01.json": first, "biu/SB-02.json": second})
    composed.work.import_ready_snapshot()
    written: list[tuple[str, str]] = []
    composed.projects.write_status = lambda item, status, revision: (written.append((item, status)), revision)[1]  # type: ignore[method-assign]

    assert composed.work.project_execution_state("SB-02", LifecycleStage.DONE, 7).confirmed
    assert written == [("PVTI_2", "DONE")]


def test_projecting_work_no_live_item_is_bound_to_is_refused(tmp_path: Path) -> None:
    only = contract_document("SB-01")
    composed = backlog(tmp_path, [
        project_item("PVTI_1", "SB-01", priority="P0", ready_at="2026-09-21T11:00:01Z", digest=digest_of(only)),
    ], {"biu/SB-01.json": only})
    composed.work.import_ready_snapshot()

    with pytest.raises(BacklogRejected):
        composed.project_projection_write("SB-99", "Status", "DONE", 1)


# --- the decision request, projected --------------------------------------------


def escalation(work_item: str = "SB-06") -> HumanDecisionRequired:
    return HumanDecisionRequired(
        profile="py10-sandbox", project=SANDBOX_REPOSITORY, work_item=work_item, biu_version=3,
        decision="Authorize the blocked execution to continue.", reason="release admission requires absent authority",
        options=("authorize", "defer"), tradeoffs=("authorize resumes", "defer holds"), recommendation="defer",
        affected_requirements=("SF-REQ-006",), affected_architecture=("FD-05",),
        cost_of_waiting="the affected work stays blocked", authorizations=("authorize permits one re-admission",),
    )


def test_a_decision_request_is_projected_into_the_project_with_complete_context(tmp_path: Path) -> None:
    only = contract_document("SB-01")
    composed = backlog(tmp_path, [
        project_item("PVTI_1", "SB-01", priority="P0", ready_at="2026-09-21T11:00:01Z", digest=digest_of(only)),
    ], {"biu/SB-01.json": only})
    notifier = ProjectDecisionNotifier(composed.projects)

    health = notifier.notify(escalation())

    assert health.delivered and notifier.projected["SB-06"]
    body = decision_body(escalation())
    for required in ("options:", "tradeoffs:", "authorizations:", "affected_requirements:", "affected_architecture:", "cost_of_waiting:"):
        assert required in body
    assert "authorize" in body and "defer" in body


def test_an_unprojectable_decision_request_reports_unhealthy_delivery_rather_than_raising(tmp_path: Path) -> None:
    only = contract_document("SB-01")
    composed = backlog(tmp_path, [
        project_item("PVTI_1", "SB-01", priority="P0", ready_at="2026-09-21T11:00:01Z", digest=digest_of(only)),
    ], {"biu/SB-01.json": only})
    notifier = ProjectDecisionNotifier(composed.projects)
    composed.projects.add_draft_item = lambda *_, **__: (_ for _ in ()).throw(RuntimeError("Project refused"))  # type: ignore[method-assign]

    health = notifier.notify(escalation())

    assert not health.delivered and "unavailable" in health.detail


# --- invocation identity ------------------------------------------------------


def test_a_coordinator_correlation_becomes_a_branch_git_accepts(tmp_path: Path) -> None:
    """`launch:<work>:<version>` is not a valid refname; a worktree could not be allocated."""
    repository = tmp_path / "repository"
    subprocess.run(["git", "init", "--quiet", str(repository)], check=True)
    subprocess.run(["git", "-C", str(repository), "commit", "--quiet", "--allow-empty", "-m", "baseline"], check=True, env=_git_identity())
    adapter = GitWorktreeAdapter(repository, tmp_path / "workspaces")

    workspace = adapter.allocate("launch:SB-01:0", "SB-01", "HEAD")

    assert workspace.branch == "invocation/launch-SB-01-0"
    assert workspace.path.name == "launch:SB-01:0"
    assert subprocess.run(["git", "check-ref-format", "--branch", workspace.branch], capture_output=True).returncode == 0


def test_the_invocation_identity_is_sanitised_only_where_git_requires_it() -> None:
    assert ref_safe("launch:SB-01:12") == "launch-SB-01-12"
    assert ref_safe("plain-identity") == "plain-identity"


# --- the worker environment ---------------------------------------------------


def test_the_worker_is_told_which_invocation_it_is_and_inherits_no_publication_credential(tmp_path: Path) -> None:
    from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
    from alienintent.invocation_runtime.domain.runtime import InvocationRole

    observed = tmp_path / "observed.txt"
    script = tmp_path / "observe.py"
    script.write_text(
        "import os,sys,pathlib\n"
        "pathlib.Path(sys.argv[1]).write_text(repr(sorted(k for k in os.environ if k.startswith('GIT_CONFIG')))"
        " + '|' + os.environ.get('ALIENINTENT_INVOCATION_ID','') + '|' + os.environ.get('ALIENINTENT_ROLE',''))\n"
    )
    worker = CliWorkerProvider(
        "claude", sys.executable, (str(script), str(observed)), "bypassPermissions",
        frozenset({"wall-clock", "cancellation"}),
        environment=worker_environment(tmp_path),
    )

    assert worker.run("launch:SB-01:0", InvocationRole.PRODUCER, tmp_path, 30).kind == "success"
    assert observed.read_text() == "[]|launch:SB-01:0|PRODUCER"


def test_a_worker_with_no_configured_environment_still_inherits_the_process_environment(tmp_path: Path) -> None:
    from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
    from alienintent.invocation_runtime.domain.runtime import InvocationRole

    observed = tmp_path / "inherited.txt"
    script = tmp_path / "inherited.py"
    script.write_text("import os,sys,pathlib; pathlib.Path(sys.argv[1]).write_text(os.environ.get('PATH','')[:4])\n")
    worker = CliWorkerProvider("claude", sys.executable, (str(script), str(observed)), "explicit", frozenset({"wall-clock", "cancellation"}))

    assert worker.run("launch:SB-01:0", InvocationRole.PRODUCER, tmp_path, 30).kind == "success"
    assert observed.read_text()


def test_the_stated_worker_environment_excludes_the_control_plane_credential(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "url.https://x-access-token:secret@github.com/a/b.insteadOf")

    stated = worker_environment(tmp_path)

    assert not any(name.startswith("GIT_CONFIG") for name in stated)
    assert "secret" not in json.dumps(stated)
    assert stated["GIT_AUTHOR_EMAIL"] == "worker@alienintent.invalid"


# --- candidate custody per invocation -----------------------------------------


def _git_identity() -> dict[str, str]:
    import os

    return dict(os.environ) | {
        "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@invalid",
        "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@invalid",
    }


def test_successive_invocations_publish_to_their_own_branches_and_read_back_separately(tmp_path: Path) -> None:
    """One shared branch makes the second candidate a non-fast-forward, so custody fails."""
    from alienintent.execution_coordination.domain.contract import BudgetPolicy
    from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
    from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
    from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
    from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole, ReservationBook

    remote, checkout = _seeded_repository(tmp_path)
    worker = RealWorkerProvider(
        CliWorkerProvider("claude", "/bin/bash", ("worker/run.sh",), "bypassPermissions",
                          frozenset({"wall-clock", "attempts", "retries", "concurrency", "cancellation"}),
                          environment=worker_environment(tmp_path)),
        GitSourceControl(), checkout, "origin", SandboxRunProfile.candidate_branch,
        tmp_path / "read-back",
        lambda invocation: CapabilityGrant("g", "1", invocation.correlation_id, InvocationRole.PRODUCER, "p", "target", frozenset({"process-control", "git-write"}), 9999999999),
        "target", GitWorktreeAdapter(checkout, tmp_path / "workspaces"), ReservationBook(1, 2),
        now=lambda: 1.0, sleep=lambda _: None,
    )
    budget = BudgetPolicy(hard_required_dimensions=("attempts", "retries"), hard_wall_clock_seconds=60, concurrency_limit=1, cancellation_limit=1)

    first = worker.start(WorkerInvocation("SB-01", "launch:SB-01:0"), None, frozenset(), budget)
    second = worker.start(WorkerInvocation("SB-02", "launch:SB-02:0"), None, frozenset(), budget)

    assert first.kind == "success" and second.kind == "success"
    assert first.candidate is not None and second.candidate is not None
    assert first.candidate.independent_read_back_proven and second.candidate.independent_read_back_proven
    assert first.candidate.content_digest != second.candidate.content_digest
    published = subprocess.run(["git", "ls-remote", "--heads", str(remote)], capture_output=True, text=True, check=True).stdout
    assert "candidate/launch-SB-01-0" in published and "candidate/launch-SB-02-0" in published


def _seeded_repository(tmp_path: Path) -> tuple[Path, Path]:
    remote, checkout = tmp_path / "remote.git", tmp_path / "checkout"
    subprocess.run(["git", "init", "--bare", "--quiet", str(remote)], check=True)
    subprocess.run(["git", "clone", "--quiet", str(remote), str(checkout)], check=True)
    (checkout / "worker").mkdir()
    (checkout / "worker" / "run.sh").write_text(WORKER)
    (checkout / "README.md").write_text("sandbox rehearsal\n")
    seed_verification_runner(checkout)
    subprocess.run(["git", "-C", str(checkout), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(checkout), "commit", "--quiet", "-m", "baseline"], check=True, env=_git_identity())
    subprocess.run(["git", "-C", str(checkout), "push", "--quiet", "origin", "HEAD:refs/heads/main"], check=True)
    return remote, checkout


# --- the CLI-loadable shape ---------------------------------------------------


def run_profile(tmp_path: Path, items: list[dict], documents: dict[str, dict]) -> SandboxRunProfile:
    remote, checkout = _seeded_repository(tmp_path)
    composed = backlog(tmp_path, items, documents)
    return SandboxRunProfile(
        composed, tmp_path / "state", checkout,
        provider="claude", worker_command=("/bin/bash", "worker/run.sh"),
        worker_environment=worker_environment(tmp_path), clock=lambda: 1758445000.0,
    )


def test_the_run_profile_exposes_exactly_what_the_control_plane_cli_loads(tmp_path: Path) -> None:
    only = contract_document("SB-01")
    profile = run_profile(tmp_path, [
        project_item("PVTI_1", "SB-01", priority="P0", ready_at="2026-09-21T11:00:01Z", digest=digest_of(only)),
    ], {"biu/SB-01.json": only})

    assert profile.name == "py10-sandbox"
    assert profile.store is profile.composition.store
    assert profile.work is profile.composition.work
    assert callable(profile.readiness) and profile.coordinator is not None
    assert callable(getattr(profile.doctor, "run", None))


def test_each_dispatch_is_authorized_by_its_own_capability_grant(tmp_path: Path) -> None:
    """One fixed grant names one invocation, so it would admit only the first dispatch."""
    only = contract_document("SB-01")
    profile = run_profile(tmp_path, [
        project_item("PVTI_1", "SB-01", priority="P0", ready_at="2026-09-21T11:00:01Z", digest=digest_of(only)),
    ], {"biu/SB-01.json": only})

    first = profile.grant(WorkerInvocation("SB-01", "launch:SB-01:0"))
    second = profile.grant(WorkerInvocation("SB-02", "launch:SB-02:0"))

    assert first.invocation_id == "launch:SB-01:0" and second.invocation_id == "launch:SB-02:0"
    assert first.role is InvocationRole.PRODUCER
    assert first.target == SANDBOX_REPOSITORY



# --- the whole loop, offline --------------------------------------------------


def seeded_backlog() -> tuple[list[dict], dict[str, dict]]:
    """The acceptance topology: priorities, a FIFO pair, a dependency, an escalation."""
    documents = {
        "SB-01": contract_document("SB-01"),
        "SB-02": contract_document("SB-02"),
        "SB-03": contract_document("SB-03"),
        "SB-04": contract_document("SB-04", dependencies=("SB-05",)),
        "SB-05": contract_document("SB-05"),
        "SB-06": contract_document("SB-06", capabilities=("python", "network-egress")),
    }
    items = [
        project_item("PVTI_1", "SB-01", priority="P0", ready_at="2026-09-21T11:00:01Z", digest=digest_of(documents["SB-01"])),
        project_item("PVTI_6", "SB-06", priority="P0", ready_at="2026-09-21T11:00:02Z", digest=digest_of(documents["SB-06"])),
        project_item("PVTI_2", "SB-02", priority="P1", ready_at="2026-09-21T11:00:03Z", digest=digest_of(documents["SB-02"])),
        project_item("PVTI_3", "SB-03", priority="P1", ready_at="2026-09-21T11:00:04Z", digest=digest_of(documents["SB-03"])),
        project_item("PVTI_4", "SB-04", priority="P2", ready_at="2026-09-21T11:00:05Z", digest=digest_of(documents["SB-04"]), depends_on=("SB-05",)),
        project_item("PVTI_5", "SB-05", priority="P3", ready_at="2026-09-21T11:00:06Z", digest=digest_of(documents["SB-05"])),
    ]
    return items, {f"biu/{name}.json": value for name, value in documents.items()}


def test_the_profile_drains_a_prioritised_backlog_with_a_dependency_and_an_escalation(tmp_path: Path) -> None:
    """The acceptance shape, offline: ordering, dependency, WIP, custody, decision, DONE."""
    items, documents = seeded_backlog()
    profile = run_profile(tmp_path, items, documents)
    dispatched: list[str] = []
    reserved_at_dispatch: list[int] = []
    original = profile.worker.start

    def observed(invocation, context, grants, budget):
        if invocation.role == "PRODUCER":
            dispatched.append(invocation.work_identity)
        reserved_at_dispatch.append(len(profile.store.recovery_reservations(profile.name)))
        return original(invocation, context, grants, budget)

    profile.worker.start = observed  # type: ignore[method-assign]

    summary = profile.coordinator.start()

    # AC 2, 3, 4: P0 first, the equal-priority pair in READY order, and the
    # dependent only after the blocker it outranks.
    assert dispatched == ["SB-01", "SB-02", "SB-03", "SB-05", "SB-04"]
    # AC 5: exactly one repository reservation is ever held.
    assert set(reserved_at_dispatch) == {1}
    # AC 7, 8: only the escalating BIU blocked; everything else drained.
    assert summary.authority_blocked == ("SB-06",)
    assert summary.stop_reason is StopReason.BLOCKED
    assert all(profile.coordinator.state(name).stage is LifecycleStage.DONE for name in ("SB-01", "SB-02", "SB-03", "SB-04", "SB-05"))
    # AC 12: every completed item carries an independently read-back candidate.
    for name in ("SB-01", "SB-02", "SB-03", "SB-04", "SB-05"):
        candidate = profile.coordinator.state(name).candidate
        assert candidate is not None and candidate.independent_read_back_proven

    # AC 7: the escalation is decision-ready and was projected.
    inbox = DecisionInbox(profile.store, profile.coordinator, profile.name)
    open_requests = inbox.list_open()
    assert [request.work_item for request in open_requests] == ["SB-06"]
    assert profile.notifier.projected["SB-06"]
    assert profile.coordinator.delivery_health["SB-06"].delivered

    # AC 9: an attributable decision unblocks and resumes the affected work.
    blocked = open_requests[0]
    inbox.submit(DecisionSubmission("operator", "SWF-11", "SB-06", blocked.biu_version, blocked.biu_version, "decision-1", "authorize"))

    # AC 13: all executable work reaches DONE.
    assert profile.coordinator.state("SB-06").stage is LifecycleStage.DONE
    assert dispatched == ["SB-01", "SB-02", "SB-03", "SB-05", "SB-04", "SB-06"]
    assert profile.coordinator.start().stop_reason is StopReason.EXHAUSTED


def test_a_crash_mid_dispatch_parks_the_unknown_effect_rather_than_re_executing_it(tmp_path: Path) -> None:
    """AC 10, 11: a restart neither loses the effect nor silently repeats it."""
    items, documents = seeded_backlog()
    profile = run_profile(tmp_path, items, documents)
    original = profile.worker.start

    def crash_on_first(invocation, context, grants, budget):
        if invocation.work_identity == "SB-01":
            raise RuntimeError("simulated process loss mid-dispatch")
        return original(invocation, context, grants, budget)

    profile.worker.start = crash_on_first  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="simulated process loss"):
        profile.coordinator.start()

    held = profile.store.recovery_reservations(profile.name)
    assert [reservation.owner for reservation in held] == ["launch:SB-01:0"]
    assert [effect.identity for effect in profile.store.unresolved_effects(profile.name)] == ["launch:SB-01:0"]

    # A restart is a new process: nothing the lost worker held in memory survives.
    restarted = SandboxRunProfile(
        backlog(tmp_path, items, documents), tmp_path / "state", profile.checkout,
        worker_command=("/bin/bash", "worker/run.sh"), worker_environment=worker_environment(tmp_path),
        clock=lambda: 1758445000.0,
    )
    dispatched: list[str] = []
    resumed = restarted.worker.start

    def observed(invocation, context, grants, budget):
        if invocation.role == "PRODUCER":
            dispatched.append(invocation.work_identity)
        return resumed(invocation, context, grants, budget)

    restarted.worker.start = observed  # type: ignore[method-assign]
    restarted.coordinator.start()

    # The lost effect is parked for authority, never re-dispatched on its own.
    assert "SB-01" not in dispatched
    assert restarted.coordinator.state("SB-01").outcome == "authority-block"
    assert restarted.store.recovery_reservations(restarted.name) == ()
    # Independent work continued through the block.
    assert all(restarted.coordinator.state(name).stage is LifecycleStage.DONE for name in ("SB-02", "SB-03", "SB-04", "SB-05"))

    # Only an attributable decision readmits it, and then exactly once.
    inbox = DecisionInbox(restarted.store, restarted.coordinator, restarted.name)
    blocked = next(request for request in inbox.list_open() if request.work_item == "SB-01")
    inbox.submit(DecisionSubmission("operator", "SWF-11", "SB-01", blocked.biu_version, blocked.biu_version, "decision-sb01", "authorize"))

    assert dispatched.count("SB-01") == 1
    assert restarted.coordinator.state("SB-01").stage is LifecycleStage.DONE


def test_a_repository_file_answer_naming_another_path_is_refused(tmp_path: Path) -> None:
    """A document answered for some other path is not the contract upstream named."""
    from alienintent.execution_coordination.adapters.github_repository_api import GitHubRepositoryApi
    from alienintent.execution_coordination.ports.repository_directory import RepositoryRejected
    from alienintent.installation.ports.github_transport import TransportResponse

    class Substituting:
        def request(self, method: str, url: str, headers, body=None) -> TransportResponse:
            answered = {"path": "biu/SB-99.json", "type": "file", "encoding": "base64", "content": "e30="}
            return TransportResponse(200, json.dumps(answered).encode())

    api = GitHubRepositoryApi(SANDBOX_REPOSITORY, Substituting(), lambda: {})

    assert api.contents("biu/SB-99.json") == b"{}"
    with pytest.raises(RepositoryRejected):
        api.contents("biu/SB-01.json")


def test_a_decision_request_the_project_answers_differently_is_not_reported_delivered(tmp_path: Path) -> None:
    only = contract_document("SB-01")
    composed = backlog(tmp_path, [
        project_item("PVTI_1", "SB-01", priority="P0", ready_at="2026-09-21T11:00:01Z", digest=digest_of(only)),
    ], {"biu/SB-01.json": only})
    notifier = ProjectDecisionNotifier(composed.projects)
    from alienintent.execution_coordination.ports.project_directory import ProjectItemState
    composed.projects.read_status = lambda item: ProjectItemState(item, None, None, None, "a different title", None, None)  # type: ignore[method-assign]

    health = notifier.notify(escalation())

    assert not health.delivered and health.detail == "decision notification projection unconfirmed"


def test_autonomous_start_is_gated_on_the_live_doctor(tmp_path: Path) -> None:
    """AC 15: `run` refuses to start unless doctor passes against the sandbox."""
    from alienintent.installation.application.doctor import CheckResult, DoctorReport

    only = contract_document("SB-01")
    profile = run_profile(tmp_path, [
        project_item("PVTI_1", "SB-01", priority="P0", ready_at="2026-09-21T11:00:01Z", digest=digest_of(only)),
    ], {"biu/SB-01.json": only})
    failing = DoctorReport((CheckResult("transport", "FAIL", "correct webhook route"),), "FAIL", 1)
    passing = DoctorReport((CheckResult("transport", "PASS"),), "PASS", 0)

    profile.doctor.run = lambda: failing  # type: ignore[method-assign]
    assert profile.readiness() is False
    profile.doctor.run = lambda: passing  # type: ignore[method-assign]
    assert profile.readiness() is True


def test_the_project_query_asks_for_everything_the_live_snapshot_depends_on() -> None:
    """A recorded answer cannot notice a field the query stopped requesting.

    Every other rule here is proven against recorded GitHub documents, and a
    fixture answers what it was written to answer regardless of the selection
    set. The one thing a fixture therefore cannot discriminate is the selection
    set itself, so it is asserted directly: the live snapshot reads the item
    title, its body and the moment its Status value changed, and a query that
    stopped asking for any of them would silently produce unordered work with
    no upstream descriptor.
    """
    from alienintent.execution_coordination.adapters import github_projects_v2 as adapter

    for query in (adapter._ITEMS_QUERY, adapter._ITEM_QUERY):
        assert "ProjectV2ItemFieldSingleSelectValue { name updatedAt field" in query
        assert "... on Issue { id title body }" in query
        assert "... on DraftIssue { id title body }" in query
