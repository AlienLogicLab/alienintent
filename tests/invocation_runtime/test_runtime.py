"""Executable PY-06 custody, grant, budget, and process-boundary proofs."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import time
from threading import Event, Thread

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


def test_real_worker_retries_a_failed_process_and_records_next_eligible_event(tmp_path: Path) -> None:
    """A disconnected retry value object cannot enforce the invocation budget."""
    from alienintent.execution_coordination.domain.contract import BudgetPolicy
    from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
    from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
    from alienintent.invocation_runtime.domain.runtime import BudgetRecord, CapabilityGrant, InvocationRole, ProcessResult, ReservationBook

    class Process:
        capabilities = type("Caps", (), {"enforceable_dimensions": frozenset({"wall-clock", "cancellation"})})()
        def __init__(self): self.calls = 0
        def run(self, *_):
            self.calls += 1
            return ProcessResult("failure", 1, True, BudgetRecord.unknown())
        def cancel(self, *_): return ProcessResult("cancelled", 0, True, BudgetRecord.unknown())
    class Workspaces:
        def allocate(self, invocation_id, owner, baseline): return type("W", (), {"invocation_id": invocation_id, "owner": owner, "path": tmp_path})()
        def cleanup(self, *_): pass
    class Source:
        def revision(self, _): return "a" * 40
        def publish_and_read_back(self, *_): raise AssertionError("not reached")

    process = Process()
    grant = CapabilityGrant("g", "PY-06@1", "p", InvocationRole.PRODUCER, "issue", "target", frozenset({"process-control", "git-write"}), 100)
    worker = RealWorkerProvider(process, Source(), tmp_path, "origin", "candidate/p", tmp_path / "verify", grant, "target", Workspaces(), ReservationBook(1, 2), now=lambda: 1, sleep=lambda _: None)
    result = worker.start(WorkerInvocation("PY-06", "p"), None, frozenset(), BudgetPolicy(hard_wall_clock_seconds=1, cancellation_limit=1, maximum_attempts=2, retry_limit=1))

    assert process.calls == 2
    assert result.kind == "failure"
    assert worker.retry_evidence["p"].attempts == 2
    assert worker.retry_evidence["p"].next_eligible_at is None


def test_real_worker_retains_an_authority_blocked_workspace_while_releasing_capacity(tmp_path: Path) -> None:
    """PY-07 AC 3: diagnostic custody survives an authority block, not its reservation."""
    from alienintent.execution_coordination.domain.contract import BudgetPolicy
    from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
    from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
    from alienintent.invocation_runtime.domain.runtime import BudgetRecord, CapabilityGrant, InvocationRole, ProcessResult, ReservationBook

    class Process:
        capabilities = type("Caps", (), {"enforceable_dimensions": frozenset({"wall-clock", "cancellation"})})()
        def run(self, *_): return ProcessResult("authority-block", 0, True, BudgetRecord.unknown())
        def cancel(self, *_): raise AssertionError("not reached")
    class Workspaces:
        def __init__(self): self.cleaned = []
        def allocate(self, invocation_id, owner, baseline): return type("W", (), {"invocation_id": invocation_id, "owner": owner, "path": tmp_path})()
        def cleanup(self, workspace, _): self.cleaned.append(workspace.invocation_id)
    class Source: pass

    spaces, slots = Workspaces(), ReservationBook(1, 1)
    grant = CapabilityGrant("g", "PY-07@1", "p", InvocationRole.PRODUCER, "issue", "target", frozenset({"process-control", "git-write"}), 100)
    worker = RealWorkerProvider(Process(), Source(), tmp_path, "origin", "candidate/p", tmp_path / "verify", grant, "target", spaces, slots, now=lambda: 1, sleep=lambda _: None)

    result = worker.start(WorkerInvocation("blocked", "p"), None, frozenset(), BudgetPolicy(hard_wall_clock_seconds=1, cancellation_limit=1, maximum_attempts=1, retry_limit=0))
    worker.finalize(WorkerInvocation("blocked", "p"), retain=True)

    assert result.kind == "authority-block"
    assert spaces.cleaned == []
    assert worker.retained_workspaces["p"] == tmp_path
    assert slots._held == {}


def test_real_worker_waits_for_each_exponential_jittered_retry_eligibility(tmp_path: Path) -> None:
    """Computing retry evidence without waiting must fail this production-path test."""
    from alienintent.execution_coordination.domain.contract import BudgetPolicy
    from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
    from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
    from alienintent.invocation_runtime.domain.runtime import BudgetRecord, CapabilityGrant, InvocationRole, ProcessResult

    class Process:
        capabilities = type("Caps", (), {"enforceable_dimensions": frozenset({"wall-clock", "cancellation"})})()
        def run(self, *_): return ProcessResult("failure", 1, True, BudgetRecord.unknown())
        def cancel(self, *_): return ProcessResult("cancelled", 0, True, BudgetRecord.unknown())
    class Workspaces:
        def allocate(self, invocation_id, owner, baseline): return type("W", (), {"invocation_id": invocation_id, "owner": owner, "path": tmp_path})()
        def cleanup(self, *_): pass
    class Source: pass

    sleeps: list[float] = []
    grant = CapabilityGrant("g", "PY-06@1", "p", InvocationRole.PRODUCER, "issue", "target", frozenset({"process-control", "git-write"}), 100)
    worker = RealWorkerProvider(Process(), Source(), tmp_path, "origin", "candidate/p", tmp_path / "verify", grant, "target", Workspaces(), now=lambda: 0, sleep=sleeps.append)
    result = worker.start(WorkerInvocation("PY-06", "p"), None, frozenset(), BudgetPolicy(hard_wall_clock_seconds=1, cancellation_limit=1, maximum_attempts=3, retry_limit=2))

    assert result.kind == "failure"
    assert sleeps == [0.011, 0.021]


def test_real_worker_cancel_fences_the_live_process_releases_reservation_and_cleans_owned_workspace(tmp_path: Path) -> None:
    """A cancellation path that only signals a child leaves capacity and resources unsafe."""
    from alienintent.execution_coordination.domain.contract import BudgetPolicy
    from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
    from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
    from alienintent.invocation_runtime.domain.runtime import BudgetRecord, CapabilityGrant, InvocationRole, ProcessResult, ReservationBook

    running, cancelled = Event(), Event()
    class Process:
        capabilities = type("Caps", (), {"enforceable_dimensions": frozenset({"wall-clock", "cancellation"})})()
        def run(self, *_):
            running.set()
            cancelled.wait(2)
            return ProcessResult("cancelled", 0, True, BudgetRecord.unknown())
        def cancel(self, *_):
            cancelled.set()
            return ProcessResult("cancelled", 0, True, BudgetRecord.unknown())
    class Workspaces:
        def __init__(self): self.cleaned = []
        def allocate(self, invocation_id, owner, baseline): return type("W", (), {"invocation_id": invocation_id, "owner": owner, "path": tmp_path})()
        def cleanup(self, workspace, _): self.cleaned.append(workspace.invocation_id)
    class Source: pass

    spaces, slots = Workspaces(), ReservationBook(1, 1)
    grant = CapabilityGrant("g", "PY-06@1", "p", InvocationRole.PRODUCER, "issue", "target", frozenset({"process-control", "git-write"}), 100)
    worker = RealWorkerProvider(Process(), Source(), tmp_path, "origin", "candidate/p", tmp_path / "verify", grant, "target", spaces, slots, now=lambda: 1, sleep=lambda _: None)
    thread = Thread(target=lambda: worker.start(WorkerInvocation("PY-06", "p"), None, frozenset(), BudgetPolicy(hard_wall_clock_seconds=1, cancellation_limit=1)))
    thread.start()
    assert running.wait(1)

    assert worker.cancel("p", "operator").kind == "cancelled"
    thread.join(2)
    assert not thread.is_alive()
    assert slots._held == {}
    assert spaces.cleaned == ["p"]


def test_verifier_invocation_owns_a_workspace_and_counts_global_capacity(tmp_path: Path) -> None:
    """VERIFY owns a fresh retrieval location and releases its global reservation."""
    from alienintent.execution_coordination.domain.custody import CandidateRef
    from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
    from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole, ReservationBook

    digest = "sha256:" + "c" * 64
    candidate = CandidateRef.source_revision(digest, "git:https://example.invalid/repo.git#candidate/p@" + "a" * 40, identity="revision:" + digest)
    class Source:
        def __init__(self): self.paths = []
        def retrieve_for_verification(self, value, path): self.paths.append(path); return value.with_independent_read_back()
    source = Source()
    grant = CapabilityGrant("g", "PY-06@1", "producer", InvocationRole.PRODUCER, "issue", "target", frozenset(), 100)
    worker = RealWorkerProvider(None, source, tmp_path, "origin", "candidate/p", tmp_path / "verify", grant, "target", None, ReservationBook(1, 1), now=lambda: 1, sleep=lambda _: None)

    assert worker.verify(candidate, "producer", "producer").kind == "self-approval-rejected"
    assert worker.verify(candidate, "producer", "verifier").kind == "success"
    assert source.paths == [tmp_path / "verify" / "verifier"]
    assert worker._reservations._held == {}


def test_verifier_retrieves_the_candidate_independently_not_from_producer_outcome(tmp_path: Path) -> None:
    """Returning the producer object would expose producer-private state to VERIFY."""
    from alienintent.execution_coordination.domain.custody import CandidateRef
    from alienintent.execution_coordination.ports.worker_provider import WorkerOutcome
    from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
    from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole

    digest = "sha256:" + "b" * 64
    candidate = CandidateRef.source_revision(digest, "git:https://example.invalid/repo.git#candidate/p@" + "a" * 40, identity="revision:" + digest)
    retrieved = candidate.with_independent_read_back()
    class Source:
        def __init__(self): self.calls: list[tuple[CandidateRef, Path]] = []
        def retrieve_for_verification(self, value, workspace):
            self.calls.append((value, workspace))
            return retrieved
    source = Source()
    grant = CapabilityGrant("g", "PY-06@1", "producer", InvocationRole.PRODUCER, "issue", "target", frozenset(), 100)
    worker = RealWorkerProvider(None, source, tmp_path, "origin", "candidate/p", tmp_path / "verify", grant, "target", None, now=lambda: 1, sleep=lambda _: None)

    verified = worker.verify(candidate, "producer", "verifier")

    assert verified == WorkerOutcome.success(retrieved)
    assert verified is not WorkerOutcome.success(candidate)
    assert source.calls == [(candidate, tmp_path / "verify" / "verifier")]


def test_verifier_returns_typed_unavailable_outcome_when_candidate_cannot_be_retrieved(tmp_path: Path) -> None:
    """An unavailable candidate must not turn VERIFY's typed outcome into a crash."""
    from alienintent.execution_coordination.domain.custody import CandidateRef
    from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
    from alienintent.invocation_runtime.domain.runtime import CandidateUnavailable, CapabilityGrant, InvocationRole

    digest = "sha256:" + "d" * 64
    candidate = CandidateRef.source_revision(digest, "git:https://example.invalid/repo.git#candidate/p@" + "a" * 40, identity="revision:" + digest)
    class Source:
        def retrieve_for_verification(self, _value, _workspace):
            raise CandidateUnavailable("candidate revision is not retrievable for verifier")
    grant = CapabilityGrant("g", "PY-06@1", "producer", InvocationRole.PRODUCER, "issue", "target", frozenset(), 100)
    worker = RealWorkerProvider(None, Source(), tmp_path, "origin", "candidate/p", tmp_path / "verify", grant, "target", None, now=lambda: 1, sleep=lambda _: None)

    assert worker.verify(candidate, "producer", "verifier").kind == "candidate-unavailable"


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


def test_source_candidate_evidence_redacts_remote_credentials() -> None:
    from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl

    assert GitSourceControl._evidence_remote("https://user:sentinel-token@example.invalid/repo.git") == "https://example.invalid/repo.git"


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


def test_cli_adapter_does_not_assert_quiescence_for_an_unknown_process(tmp_path: Path) -> None:
    from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider

    result = CliWorkerProvider("python", sys.executable, ("-c", "pass"), "explicit", frozenset({"wall-clock", "cancellation"})).cancel("unknown", "operator")
    assert result.kind == "unresolved-recovery" and not result.quiescent


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
    worker = RealWorkerProvider(cli, GitSourceControl(), source, "origin", "candidate/producer-1", tmp_path / "verifier", grant, "AlienLogicLab/alienintent", GitWorktreeAdapter(source, tmp_path / "worktrees"), now=lambda: int(time.time()), sleep=time.sleep)

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
    worker = RealWorkerProvider(CliWorkerProvider("python", sys.executable, ("-c", "pass"), "explicit", frozenset({"wall-clock", "cancellation"})), Unused(), tmp_path, "origin", "candidate/p", tmp_path / "v", grant, "target", Unused(), now=lambda: int(time.time()), sleep=time.sleep)
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


@pytest.mark.parametrize("branch, published_revision", [("unpublished", None), ("mismatched", "different")])
def test_control_plane_rejects_reachable_remote_without_the_exact_advertised_revision(tmp_path: Path, branch: str, published_revision: str | None) -> None:
    """An empty successful ls-remote response must be a typed custody rejection, not a clone-path crash."""
    from alienintent.execution_coordination.application.local_artifact_custody import verify_in_fresh_process
    from alienintent.execution_coordination.domain.custody import CandidateRef
    from alienintent.invocation_runtime.domain.runtime import CandidateUnavailable

    remote, source = tmp_path / "remote.git", tmp_path / "source"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "init", str(source)], check=True, capture_output=True)
    for key, value in (("user.email", "test@example.invalid"), ("user.name", "Test")):
        subprocess.run(["git", "-C", str(source), "config", key, value], check=True)
    (source / "candidate").write_text("first")
    subprocess.run(["git", "-C", str(source), "add", "candidate"], check=True)
    subprocess.run(["git", "-C", str(source), "commit", "-m", "first"], check=True, capture_output=True)
    revision = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    if published_revision:
        (source / "candidate").write_text("second")
        subprocess.run(["git", "-C", str(source), "commit", "-am", "second"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(source), "push", str(remote), f"HEAD:refs/heads/{branch}"], check=True, capture_output=True)
    digest = "sha256:" + __import__("hashlib").sha256(revision.encode()).hexdigest()
    candidate = CandidateRef.source_revision(digest, f"git:{remote}#{branch}@{revision}", identity=f"revision:{branch}@{revision}@{digest}")

    with pytest.raises(CandidateUnavailable, match="not published"):
        verify_in_fresh_process(candidate, tmp_path / "verifier")
