"""A PRODUCER must change the starting tree before a candidate is published."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import time

import pytest

from alienintent.execution_coordination.domain.contract import BudgetPolicy
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter
from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal
from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole


def git(path: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, text=True).stdout.strip()


def produce(tmp_path: Path, command: str):
    remote, source = tmp_path / "remote.git", tmp_path / "source"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    git(source, "config", "user.email", "test@example.invalid")
    git(source, "config", "user.name", "Test")
    (source / "base.txt").write_text("base")
    git(source, "add", "base.txt")
    git(source, "commit", "-qm", "base")
    starting = git(source, "rev-parse", "HEAD")
    git(source, "remote", "add", "origin", str(remote))
    process = CliWorkerProvider("python", sys.executable, ("-c", command), "explicit", frozenset({"wall-clock", "cancellation"}))
    invocation = WorkerInvocation("work", "producer-1")
    grant = CapabilityGrant("grant", "work", invocation.correlation_id, InvocationRole.PRODUCER, "issue", "repo",
                            frozenset({"process-control", "git-write"}), int(time.time()) + 100)
    journal = JsonlInvocationJournal(tmp_path / "journal.jsonl", time.time)
    worker = RealWorkerProvider(process, GitSourceControl(), source, "origin", "candidate/producer-1",
                                tmp_path / "verifier", grant, "repo", GitWorktreeAdapter(source, tmp_path / "worktrees"),
                                now=time.time, sleep=time.sleep, journal=journal)
    outcome = worker.start(invocation, None, frozenset(), BudgetPolicy(hard_wall_clock_seconds=5, cancellation_limit=1))
    return outcome, worker, invocation, journal.records(), remote, starting


_EMPTY = "import subprocess; subprocess.run(['git', 'commit', '-qm', 'empty', '--allow-empty'], check=True)"
_CHANGE = "import pathlib, subprocess; pathlib.Path('new.txt').write_text('change'); subprocess.run(['git', 'add', 'new.txt'], check=True); subprocess.run(['git', 'commit', '-qm', 'change'], check=True)"
_REVERT = _CHANGE + "; subprocess.run(['git', 'revert', '--no-edit', 'HEAD'], check=True)"


@pytest.mark.parametrize("command", ["pass", _EMPTY, _REVERT], ids=["same-sha", "empty-commit", "commit-then-revert"])
def test_a_revision_with_the_starting_tree_is_no_change(tmp_path: Path, command: str) -> None:
    outcome, worker, invocation, records, remote, _ = produce(tmp_path, command)
    assert outcome.kind == "no-change" and outcome.candidate is None
    assert len(outcome.findings) == 1 and outcome.findings[0].startswith("no-change-candidate:")
    assert git(remote, "for-each-ref", "--format=%(refname)", "refs/heads/candidate") == ""
    own = [record for record in records if record.get("correlation_id") == invocation.correlation_id]
    assert not any(record["event"] == "publication-started" for record in own)
    finished = [record for record in own if record["event"] == "invocation-outcome"]
    assert len(finished) == 1
    assert (finished[0]["kind"], finished[0]["candidate"], finished[0]["findings"]) == (
        "no-change", None, list(outcome.findings))
    assert worker.read_back(invocation) == outcome


def test_a_revision_with_a_different_tree_is_admitted(tmp_path: Path) -> None:
    outcome, _, _, _, remote, starting = produce(tmp_path, _CHANGE)
    assert outcome.kind == "success" and outcome.candidate is not None
    revision = git(remote, "rev-parse", "refs/heads/candidate/producer-1")
    assert revision != starting and outcome.candidate.locator.endswith("@" + revision)


def test_a_handover_revision_with_the_starting_tree_is_never_handed_over(tmp_path: Path) -> None:
    from alienintent.invocation_runtime.domain.runtime import BudgetRecord, ProcessResult

    class Process:
        capabilities = type("Caps", (), {"enforceable_dimensions": frozenset({"wall-clock", "cancellation"})})()
        def run(self, *_): return ProcessResult("success", 0, True, BudgetRecord.unknown())

    class Workspaces:
        def allocate(self, invocation_id, owner, baseline):
            return type("Workspace", (), {"invocation_id": invocation_id, "owner": owner, "path": tmp_path})()
        def cleanup(self, *_): pass

    class Handover:
        def revision(self, _): return "a" * 40
        def tree(self, _, revision): return "b" * 40
        def hand_over(self, *_): raise AssertionError("hand_over was called")
        def publish_intake(self, *_): raise AssertionError("publish_intake was called")

    invocation = WorkerInvocation("work", "producer-1")
    grant = CapabilityGrant("grant", "work", invocation.correlation_id, InvocationRole.PRODUCER, "issue", "repo",
                            frozenset({"process-control", "git-write"}), int(time.time()) + 100)
    worker = RealWorkerProvider(Process(), GitSourceControl(), tmp_path, "origin", "candidate/producer-1",
                                tmp_path / "verifier", grant, "repo", Workspaces(), now=time.time, sleep=time.sleep,
                                handover=Handover())
    outcome = worker.start(invocation, None, frozenset(), BudgetPolicy(hard_wall_clock_seconds=5, cancellation_limit=1))
    assert outcome.kind == "no-change" and outcome.candidate is None
