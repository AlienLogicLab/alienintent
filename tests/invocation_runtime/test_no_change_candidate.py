"""A PRODUCER must change the starting git tree before candidate publication."""

from pathlib import Path
import subprocess
import sys
import time

import pytest

from alienintent.execution_coordination.domain.contract import BudgetPolicy
from alienintent.execution_coordination.ports.worker_provider import NO_CHANGE, WorkerInvocation
from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter
from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal
from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def worker_for(tmp_path: Path, command: str, *, handover=None):
    remote, source = tmp_path / "remote.git", tmp_path / "source"
    git(tmp_path, "init", "--bare", str(remote))
    git(tmp_path, "init", str(source))
    git(source, "config", "user.email", "test@example.invalid")
    git(source, "config", "user.name", "Test")
    (source / "seed").write_text("seed")
    git(source, "add", "seed")
    git(source, "commit", "-qm", "seed")
    git(source, "remote", "add", "origin", str(remote))
    starting = git(source, "rev-parse", "HEAD")
    invocation = WorkerInvocation("W", "producer-1")
    grant = CapabilityGrant("grant", "W@1", invocation.correlation_id, InvocationRole.PRODUCER,
                            "issue", "repo", frozenset({"process-control", "git-write"}), int(time.time()) + 100)
    journal = JsonlInvocationJournal(tmp_path / "journal.jsonl", time.time)
    cli = CliWorkerProvider("python", sys.executable, ("-c", command), "explicit", frozenset({"wall-clock", "cancellation"}))
    worker = RealWorkerProvider(cli, GitSourceControl(), source, "origin", "candidate/producer-1", tmp_path / "verifier",
                                grant, "repo", GitWorktreeAdapter(source, tmp_path / "worktrees"),
                                now=lambda: int(time.time()), sleep=time.sleep, journal=journal, handover=handover)
    return worker, invocation, remote, source, starting, journal


@pytest.mark.parametrize("command", [
    "pass",
    "import subprocess; subprocess.run(['git', 'commit', '--allow-empty', '-qm', 'empty'], check=True)",
    "import pathlib, subprocess; pathlib.Path('change').write_text('change'); subprocess.run(['git', 'add', 'change'], check=True); subprocess.run(['git', 'commit', '-qm', 'change'], check=True); subprocess.run(['git', 'revert', '--no-edit', 'HEAD'], check=True)",
], ids=["same-sha", "empty-commit", "commit-then-revert"])
def test_a_revision_with_the_starting_tree_is_no_change(tmp_path: Path, command: str) -> None:
    worker, invocation, _, source, _, journal = worker_for(tmp_path, command)
    outcome = worker.start(invocation, None, frozenset(), BudgetPolicy(hard_wall_clock_seconds=5, cancellation_limit=1))
    assert outcome.kind == NO_CHANGE and outcome.candidate is None
    assert len(outcome.findings) == 1 and outcome.findings[0].startswith("no-change-candidate:")
    assert git(source, "ls-remote", "origin", "refs/heads/candidate/producer-1") == ""
    records = [record for record in journal.records() if record.get("correlation_id") == invocation.correlation_id]
    assert not any(record["event"] == "publication-started" for record in records)
    terminal = [record for record in records if record["event"] == "invocation-outcome"]
    assert len(terminal) == 1
    assert terminal[0]["kind"] == NO_CHANGE and terminal[0]["candidate"] is None
    assert terminal[0]["findings"] == list(outcome.findings)
    assert worker.read_back(invocation) == outcome


def test_a_revision_with_a_different_tree_is_admitted(tmp_path: Path) -> None:
    command = "import pathlib, subprocess; pathlib.Path('change').write_text('change'); subprocess.run(['git', 'add', 'change'], check=True); subprocess.run(['git', 'commit', '-qm', 'change'], check=True)"
    worker, invocation, _, source, starting, _ = worker_for(tmp_path, command)
    outcome = worker.start(invocation, None, frozenset(), BudgetPolicy(hard_wall_clock_seconds=5, cancellation_limit=1))
    assert outcome.kind == "success" and outcome.candidate is not None
    revision = outcome.candidate.locator.rsplit("@", 1)[1]
    assert revision != starting
    assert git(source, "ls-remote", "origin", "refs/heads/candidate/producer-1").split()[0] == revision


def test_a_handover_revision_with_the_starting_tree_is_never_handed_over(tmp_path: Path) -> None:
    class Handover:
        def __init__(self): self.calls = []
        def revision(self, workspace): return "a" * 40
        def tree(self, workspace, revision): return "b" * 40
        def hand_over(self, *args): self.calls.append("hand_over")
        def publish_intake(self, *args): self.calls.append("publish_intake")

    handover = Handover()
    worker, invocation, _, _, _, _ = worker_for(tmp_path, "pass", handover=handover)
    outcome = worker.start(invocation, None, frozenset(), BudgetPolicy(hard_wall_clock_seconds=5, cancellation_limit=1))
    assert outcome.kind == NO_CHANGE and outcome.candidate is None
    assert handover.calls == []
