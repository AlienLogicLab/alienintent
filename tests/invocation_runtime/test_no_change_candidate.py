"""A successful PRODUCER process needs a changed Git tree before publication."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest

from alienintent.execution_coordination.domain.contract import BudgetPolicy
from alienintent.execution_coordination.ports.worker_provider import NO_CHANGE, WorkerInvocation
from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter
from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal
from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole


def git(path: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=path, check=True, capture_output=True, text=True).stdout.strip()


def producer(tmp_path: Path, command: str):
    remote, source = tmp_path / "remote.git", tmp_path / "source"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    git(tmp_path, "init", "-q", "-b", "main", str(source))
    git(source, "config", "user.name", "Test")
    git(source, "config", "user.email", "test@example.invalid")
    (source / "seed").write_text("seed")
    git(source, "add", "seed")
    git(source, "commit", "-qm", "seed")
    git(source, "remote", "add", "origin", str(remote))
    journal = JsonlInvocationJournal(tmp_path / "journal.jsonl", time.time)
    cli = CliWorkerProvider("python", sys.executable, ("-c", command), "explicit", frozenset({"wall-clock", "cancellation"}))
    invocation = WorkerInvocation("work", "producer-1")
    grant = CapabilityGrant("grant", "1", invocation.correlation_id, InvocationRole.PRODUCER, "issue", "repo",
                            frozenset({"process-control", "git-write"}), int(time.time()) + 100)
    worker = RealWorkerProvider(cli, GitSourceControl(), source, "origin", "candidate/producer-1", tmp_path / "verifier",
                                grant, "repo", GitWorktreeAdapter(source, tmp_path / "worktrees"), now=time.time,
                                sleep=time.sleep, journal=journal)
    outcome = worker.start(invocation, None, frozenset(), BudgetPolicy(hard_wall_clock_seconds=10, cancellation_limit=1))
    return outcome, worker, journal, invocation, source


@pytest.mark.parametrize("command", [
    "pass",
    "import subprocess; subprocess.run(['git', 'commit', '--allow-empty', '-qm', 'empty'], check=True)",
    "import pathlib, subprocess; pathlib.Path('change').write_text('change'); subprocess.run(['git', 'add', 'change'], check=True); subprocess.run(['git', 'commit', '-qm', 'change'], check=True); subprocess.run(['git', 'revert', '--no-edit', 'HEAD'], check=True)",
], ids=["same-sha", "empty-commit", "commit-then-revert"])
def test_a_revision_with_the_starting_tree_is_no_change(tmp_path: Path, command: str) -> None:
    outcome, worker, journal, invocation, source = producer(tmp_path, command)
    assert outcome.kind == NO_CHANGE and outcome.candidate is None
    assert len(outcome.findings) == 1 and outcome.findings[0].startswith("no-change-candidate:")
    assert git(source, "ls-remote", "origin", "refs/heads/candidate/producer-1") == ""
    records = journal.records()
    assert not any(record["event"] == "publication-started" for record in records)
    recorded = [record for record in records if record["event"] == "invocation-outcome"]
    assert len(recorded) == 1
    assert recorded[0]["kind"] == NO_CHANGE and recorded[0]["candidate"] is None
    assert recorded[0]["findings"] == list(outcome.findings)
    assert worker.read_back(invocation) == outcome


def test_a_revision_with_a_different_tree_is_admitted(tmp_path: Path) -> None:
    command = "import pathlib, subprocess; pathlib.Path('change').write_text('change'); subprocess.run(['git', 'add', 'change'], check=True); subprocess.run(['git', 'commit', '-qm', 'change'], check=True)"
    outcome, _, _, _, source = producer(tmp_path, command)
    assert outcome.kind == "success" and outcome.candidate is not None
    revision = outcome.candidate.locator.rsplit("@", 1)[1]
    assert git(source, "ls-remote", "origin", "refs/heads/candidate/producer-1").split()[0] == revision


def test_a_handover_revision_with_the_starting_tree_is_never_handed_over(tmp_path: Path) -> None:
    class Handover:
        def __init__(self): self.calls = []
        def revision(self, _): return "a" * 40
        def tree(self, _, revision): return "b" * 40
        def hand_over(self, *_): self.calls.append("hand_over")
        def publish_intake(self, *_): self.calls.append("publish_intake")
    handover = Handover()
    class Workspaces:
        def allocate(self, invocation_id, owner, baseline):
            return type("W", (), {"invocation_id": invocation_id, "owner": owner, "path": tmp_path})()
        def cleanup(self, *_): pass
    from alienintent.invocation_runtime.domain.runtime import BudgetRecord, ProcessResult
    class Process:
        capabilities = type("Caps", (), {"enforceable_dimensions": frozenset({"wall-clock", "cancellation"})})()
        def run(self, *_): return ProcessResult("success", 0, True, BudgetRecord.unknown())
    invocation = WorkerInvocation("work", "p")
    grant = CapabilityGrant("grant", "1", "p", InvocationRole.PRODUCER, "issue", "repo",
                            frozenset({"process-control", "git-write"}), int(time.time()) + 100)
    worker = RealWorkerProvider(Process(), GitSourceControl(), tmp_path, "origin", "candidate/p", tmp_path / "verify",
                                grant, "repo", Workspaces(), now=time.time, sleep=time.sleep, handover=handover)
    outcome = worker.start(invocation, None, frozenset(), BudgetPolicy(hard_wall_clock_seconds=1, cancellation_limit=1))
    assert outcome.kind == NO_CHANGE and handover.calls == []
