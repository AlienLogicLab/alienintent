"""Executable PY-06 custody, grant, budget, and process-boundary proofs."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import time
from threading import Thread

import pytest


def test_verifier_is_independent_and_cannot_approve_producer_output() -> None:
    from alienintent.invocation_runtime.domain.runtime import InvocationRole, VerifierIndependence

    with pytest.raises(PermissionError, match="self-approval"):
        VerifierIndependence("producer-1", "producer-1").require(InvocationRole.VERIFIER)
    VerifierIndependence("producer-1", "verifier-1").require(InvocationRole.VERIFIER)


def test_reservations_keep_verifier_out_of_mutating_slot_and_bound_capacity() -> None:
    from alienintent.invocation_runtime.domain.runtime import InvocationRole, ReservationBook

    slots = ReservationBook(mutating_limit=1, global_limit=2)
    slots.reserve("producer", InvocationRole.PRODUCER)
    slots.reserve("verifier", InvocationRole.VERIFIER)
    with pytest.raises(RuntimeError, match="global"):
        slots.reserve("another", InvocationRole.VERIFIER)
    slots.release("producer")
    slots.reserve("next", InvocationRole.PRODUCER)


def test_retry_schedule_is_finite_and_records_next_eligible_event() -> None:
    from alienintent.invocation_runtime.domain.runtime import RetrySchedule

    schedule = RetrySchedule(maximum_attempts=2, retry_limit=1, base_delay_seconds=1, jitter_seconds=0)
    assert schedule.next_after_failure(1, 10) == 11
    assert schedule.next_after_failure(2, 11) is None


def test_source_candidate_must_be_published_and_read_back_from_a_fresh_clone(tmp_path: Path) -> None:
    """Removing publication or fresh-clone verification must reject VERIFY entry."""
    from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
    from alienintent.invocation_runtime.domain.runtime import CandidateUnavailable

    remote = tmp_path / "remote.git"
    source = tmp_path / "source"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "init", str(source)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(source), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(source), "config", "user.name", "Test"], check=True)
    (source / "candidate.txt").write_text("candidate")
    subprocess.run(["git", "-C", str(source), "add", "candidate.txt"], check=True)
    subprocess.run(["git", "-C", str(source), "commit", "-m", "candidate"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(source), "remote", "add", "origin", str(remote)], check=True)

    control = GitSourceControl()
    revision = control.revision(source)
    with pytest.raises(CandidateUnavailable, match="not published"):
        control.read_back_candidate(source, "origin", "candidate/test", revision, tmp_path / "verifier")

    candidate = control.publish_and_read_back(source, "origin", "candidate/test", revision, tmp_path / "verifier")

    assert candidate.verify_admissible
    assert revision in candidate.identity
    assert (tmp_path / "verifier" / ".git").exists()


def test_grant_denies_cross_target_and_revocation_fences_new_actions() -> None:
    """Changing target matching or revocation must make capability use incorrectly succeed."""
    from alienintent.invocation_runtime.domain.runtime import CapabilityDenied, CapabilityGrant, InvocationRole

    grant = CapabilityGrant(
        identifier="grant-1", biu_version="PY-06@1", invocation_id="producer-1",
        role=InvocationRole.PRODUCER, issuer="issue-54", target="AlienLogicLab/alienintent",
        operations=frozenset({"git-write"}), expires_at=100,
    )
    grant.require("git-write", "AlienLogicLab/alienintent", 99)
    with pytest.raises(CapabilityDenied, match="target"):
        grant.require("git-write", "other/repository", 99)
    with pytest.raises(CapabilityDenied, match="revoked"):
        grant.revoke("operator").require("git-write", "AlienLogicLab/alienintent", 99)


def test_hard_required_unenforceable_budget_is_ineligible_and_unknown_cost_is_not_zero() -> None:
    """Dropping hard dimensions or defaulting missing spend to zero must fail this test."""
    from alienintent.invocation_runtime.domain.runtime import BudgetIneligible, BudgetRecord, ProviderCapabilities, require_eligible

    provider = ProviderCapabilities("cli", frozenset({"wall-clock", "attempts", "retries", "concurrency", "cancellation"}))
    with pytest.raises(BudgetIneligible, match="token"):
        require_eligible(provider, frozenset({"wall-clock", "token"}))
    record = BudgetRecord.unknown()
    assert record.token_cost is None and record.monetary_cost is None


def test_cli_adapter_times_out_and_cancellation_is_idempotent_with_quiescence(tmp_path: Path) -> None:
    """Removing timeout termination or process confirmation must leave a live child."""
    from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
    from alienintent.invocation_runtime.domain.runtime import InvocationRole

    provider = CliWorkerProvider("python", sys.executable, ("-c", "import time; time.sleep(10)"), "explicit", frozenset({"wall-clock", "cancellation"}))
    result = provider.run("run-1", InvocationRole.PRODUCER, tmp_path, 0.05)

    assert result.kind == "timeout"
    assert result.quiescent
    assert provider.cancel("run-1", "repeat").kind == "already-finished"


def test_cli_adapter_cancels_a_live_child_process(tmp_path: Path) -> None:
    from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
    from alienintent.invocation_runtime.domain.runtime import InvocationRole

    provider = CliWorkerProvider("python", sys.executable, ("-c", "import time; time.sleep(10)"), "explicit", frozenset({"wall-clock", "cancellation"}))
    thread = Thread(target=lambda: provider.run("live", InvocationRole.PRODUCER, tmp_path, 10))
    thread.start()
    for _ in range(100):
        if "live" in provider._active:
            break
        time.sleep(.01)
    result = provider.cancel("live", "operator")
    thread.join(2)
    assert result.kind == "cancelled" and result.quiescent and not thread.is_alive()


def test_workspace_cleanup_retains_a_plausibly_live_owned_workspace(tmp_path: Path) -> None:
    """Removing liveness checking would delete the evidence-bearing live worktree."""
    from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter
    from alienintent.invocation_runtime.domain.runtime import CandidateUnavailable

    repo = tmp_path / "repo"
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    (repo / "seed").write_text("seed")
    subprocess.run(["git", "-C", str(repo), "add", "seed"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "seed"], check=True, capture_output=True)
    adapter = GitWorktreeAdapter(repo, tmp_path / "worktrees")
    workspace = adapter.allocate("producer-1", "producer", "HEAD")
    live = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"])
    try:
        with pytest.raises(CandidateUnavailable, match="live"):
            adapter.cleanup(workspace, live.pid)
        assert workspace.path.exists()
    finally:
        live.terminate()
        live.wait()
    adapter.cleanup(workspace, live.pid)
    assert not workspace.path.exists()


def test_real_worker_returns_only_a_published_independently_read_back_source_candidate(tmp_path: Path) -> None:
    """Bypassing the source-control handoff would allow a producer-local candidate into VERIFY."""
    from alienintent.execution_coordination.domain.contract import BudgetPolicy
    from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
    from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
    from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
    from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter
    from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
    from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole

    remote, source = tmp_path / "remote.git", tmp_path / "source"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "init", str(source)], check=True, capture_output=True)
    for key, value in (("user.email", "test@example.invalid"), ("user.name", "Test")):
        subprocess.run(["git", "-C", str(source), "config", key, value], check=True)
    (source / "candidate").write_text("candidate")
    subprocess.run(["git", "-C", str(source), "add", "candidate"], check=True)
    subprocess.run(["git", "-C", str(source), "commit", "-m", "candidate"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(source), "remote", "add", "origin", str(remote)], check=True)
    cli = CliWorkerProvider("python", sys.executable, ("-c", "pass"), "explicit", frozenset({"wall-clock", "cancellation"}))
    grant = CapabilityGrant("grant", "PY-06@1", "producer-1", InvocationRole.PRODUCER, "issue-54", "AlienLogicLab/alienintent", frozenset({"process-control", "git-write"}), int(time.time()) + 100)
    worker = RealWorkerProvider(cli, GitSourceControl(), source, "origin", "candidate/producer-1", tmp_path / "verifier", grant, "AlienLogicLab/alienintent", GitWorktreeAdapter(source, tmp_path / "worktrees"), now=lambda: int(time.time()))

    outcome = worker.start(WorkerInvocation("PY-06", "producer-1"), None, frozenset(), BudgetPolicy(hard_wall_clock_seconds=5, cancellation_limit=1))

    assert outcome.kind == "success"
    assert outcome.candidate is not None and outcome.candidate.verify_admissible


def test_real_worker_rejects_expired_grant_in_production_path(tmp_path: Path) -> None:
    from alienintent.execution_coordination.domain.contract import BudgetPolicy
    from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
    from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
    from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
    from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole

    class Unused: pass
    grant = CapabilityGrant("g", "PY-06@1", "p", InvocationRole.PRODUCER, "issue", "target", frozenset({"process-control", "git-write"}), 1)
    worker = RealWorkerProvider(CliWorkerProvider("python", sys.executable, ("-c", "pass"), "explicit", frozenset({"wall-clock", "cancellation"})), Unused(), tmp_path, "origin", "candidate/p", tmp_path / "v", grant, "target", Unused(), now=lambda: int(time.time()))
    assert worker.start(WorkerInvocation("PY-06", "p"), None, frozenset(), BudgetPolicy(hard_wall_clock_seconds=1, cancellation_limit=1)).kind == "ineligible"


def test_control_plane_rechecks_a_source_candidate_even_when_worker_claims_read_back(tmp_path: Path) -> None:
    """Trusting a worker-set flag would admit an unreachable source candidate to VERIFY."""
    from alienintent.execution_coordination.application.local_artifact_custody import verify_in_fresh_process
    from alienintent.execution_coordination.domain.custody import CandidateRef

    revision = "a" * 40
    digest = "sha256:" + __import__("hashlib").sha256(revision.encode()).hexdigest()
    claimed = CandidateRef.source_revision(digest, f"git:{tmp_path / 'missing.git'}#{revision}", identity=f"revision:missing@{revision}@{digest}").with_independent_read_back()

    with pytest.raises(ValueError, match="read-back"):
        verify_in_fresh_process(claimed, tmp_path / "verifier")
