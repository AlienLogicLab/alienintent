"""Executable proof for the S0 scripted worker transport and its durable journal."""

from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from alienintent.execution_coordination.domain.contract import BudgetPolicy
from alienintent.execution_coordination.domain.custody import CandidateRef
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation, WorkerOutcome
from alienintent.invocation_runtime.adapters.scripted_worker import (
    ScriptedWorkerProcess,
    ScriptedWorkerProvider,
    journal_append,
    journal_outcome,
    journal_provider_calls,
    journal_records,
    work_identity_of,
)
from alienintent.invocation_runtime.domain.runtime import InvocationRole, ScriptRejected

EPOCH = 1758542400.0
CLOCK = lambda: EPOCH  # noqa: E731 - the injected clock is a value, not a facility


def git_environment(home: Path) -> dict[str, str]:
    import os

    home.mkdir(parents=True, exist_ok=True)
    return {
        "PATH": os.environ["PATH"], "HOME": str(home), "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
        "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
    }


def repository(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "--initial-branch=main", str(repo)], check=True)
    env = git_environment(tmp_path / "home") | {"GIT_AUTHOR_DATE": "1758542400 +0000", "GIT_COMMITTER_DATE": "1758542400 +0000"}
    (repo / "README").write_text("seed")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, env=env)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "seed"], check=True, env=env)
    return repo


# --- journal -------------------------------------------------------------------


def test_journal_append_reads_back_with_sequence_and_the_injected_clock(tmp_path: Path) -> None:
    path = tmp_path / "journal.jsonl"

    first = journal_append(path, CLOCK, {"event": "x"})
    second = journal_append(path, CLOCK, {"event": "y"})

    assert (first["sequence"], first["at"]) == (0, EPOCH)
    assert second["sequence"] == 1
    assert [entry["event"] for entry in journal_records(path)] == ["x", "y"]


def test_journal_outcome_is_none_until_an_outcome_is_recorded_and_decodes_the_candidate(tmp_path: Path) -> None:
    path = tmp_path / "journal.jsonl"
    digest = "sha256:" + "a" * 64
    candidate = CandidateRef.source_revision(digest, "git:/remote.git#candidate/x@" + "b" * 40, identity="revision:x@" + digest).with_independent_read_back()

    assert journal_outcome(path, "launch:x:0") is None
    journal_append(path, CLOCK, {"event": "invocation-started", "correlation_id": "launch:x:0"})
    assert journal_outcome(path, "launch:x:0") is None
    journal_append(path, CLOCK, {"event": "invocation-outcome", "correlation_id": "launch:x:0", "kind": "success", "candidate": {
        "kind": "source-revision", "identity": candidate.identity, "content_digest": digest, "locator": candidate.locator, "provenance": candidate.provenance, "independent_read_back_proven": True,
    }})

    assert journal_outcome(path, "launch:x:0") == WorkerOutcome.success(candidate)
    assert journal_outcome(path, "launch:other:0") is None


def test_work_identity_is_taken_from_the_coordinator_correlation_form() -> None:
    assert work_identity_of("launch:S0-PROBE:0") == "S0-PROBE"
    assert work_identity_of("launch:w:3") == "w"
    assert work_identity_of("plain") == "plain"


# --- process -----------------------------------------------------------------


def test_an_unknown_scripted_step_is_refused_at_construction(tmp_path: Path) -> None:
    with pytest.raises(ScriptRejected, match="unknown scripted step"):
        ScriptedWorkerProcess({"w": ["mark-done"]}, {}, CLOCK, tmp_path / "j.jsonl", git_environment(tmp_path / "home"))


def test_a_success_step_commits_the_note_with_the_injected_clock_as_both_dates(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    process = ScriptedWorkerProcess({"w": ["success"]}, {"w": "docs/w.md"}, CLOCK, tmp_path / "j.jsonl", git_environment(tmp_path / "home"))

    result = process.run("launch:w:0", InvocationRole.PRODUCER, repo, 5)

    assert (result.kind, result.exit_status, result.quiescent) == ("success", 0, True)
    assert result.budget.token_cost is None and result.budget.monetary_cost is None
    assert (repo / "docs/w.md").read_text() == "w produced by the scripted worker under launch:w:0\n"
    dates = subprocess.run(["git", "-C", str(repo), "show", "-s", "--format=%at %ct", "HEAD"], capture_output=True, text=True, check=True).stdout.split()
    assert dates == ["1758542400", "1758542400"]
    assert [entry["event"] for entry in journal_records(tmp_path / "j.jsonl")] == ["process-run"]
    assert journal_provider_calls(tmp_path / "j.jsonl") == 0


def test_the_same_script_and_clock_reproduce_the_same_revision_in_another_root(tmp_path: Path) -> None:
    revisions = []
    for name in ("one", "two"):
        root = tmp_path / name
        root.mkdir()
        repo = repository(root)
        ScriptedWorkerProcess({"w": ["success"]}, {"w": "docs/w.md"}, CLOCK, root / "j.jsonl", git_environment(root / "home")).run("launch:w:0", InvocationRole.PRODUCER, repo, 5)
        revisions.append(subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip())
    assert revisions[0] == revisions[1]


def test_an_exhausted_script_is_refused_rather_than_improvised(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    process = ScriptedWorkerProcess({"w": ["failure"]}, {}, CLOCK, tmp_path / "j.jsonl", git_environment(tmp_path / "home"))

    assert process.run("launch:w:0", InvocationRole.PRODUCER, repo, 5).kind == "failure"
    with pytest.raises(ScriptRejected, match="no scripted step remains"):
        process.run("launch:w:1", InvocationRole.PRODUCER, repo, 5)


def test_a_provider_call_step_is_counted_and_fails_without_reaching_any_provider(tmp_path: Path) -> None:
    """The zero-provider-call counter must be able to move, or it proves nothing."""
    repo = repository(tmp_path)
    process = ScriptedWorkerProcess({"w": ["provider-call"]}, {}, CLOCK, tmp_path / "j.jsonl", git_environment(tmp_path / "home"))

    result = process.run("launch:w:0", InvocationRole.PRODUCER, repo, 5)

    assert (result.kind, result.exit_status) == ("failure", 127)
    assert process.provider_calls == 1
    assert journal_provider_calls(tmp_path / "j.jsonl") == 1


def test_cancel_reports_quiescence_only_for_an_invocation_it_ran(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    process = ScriptedWorkerProcess({"w": ["timeout"]}, {}, CLOCK, tmp_path / "j.jsonl", git_environment(tmp_path / "home"))

    unknown = process.cancel("launch:w:0", "operator")
    process.run("launch:w:0", InvocationRole.PRODUCER, repo, 5)
    finished = process.cancel("launch:w:0", "operator")

    assert (unknown.kind, unknown.quiescent) == ("unresolved-recovery", False)
    assert (finished.kind, finished.quiescent) == ("already-finished", True)


# --- provider ----------------------------------------------------------------


class Inner:
    def __init__(self, outcome: WorkerOutcome | Exception) -> None:
        self.outcome, self.finalized, self.cancelled = outcome, [], []

    def start(self, invocation, context, grants, budget):
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome

    def read_back(self, invocation):
        raise AssertionError("the journal answers read-back, not the inner provider")

    def cancel(self, invocation_id, reason):
        self.cancelled.append(invocation_id)
        return "cancelled"

    def finalize(self, invocation, retain):
        self.finalized.append((invocation.correlation_id, retain))


def candidate() -> CandidateRef:
    digest = "sha256:" + "c" * 64
    return CandidateRef.source_revision(digest, "git:/remote.git#candidate/w@" + "d" * 40, identity="revision:w@" + digest).with_independent_read_back()


def test_start_journals_before_and_after_and_read_back_answers_from_the_durable_journal(tmp_path: Path) -> None:
    path = tmp_path / "j.jsonl"
    provider = ScriptedWorkerProvider(Inner(WorkerOutcome.success(candidate())), path, CLOCK)
    invocation = WorkerInvocation("w", "launch:w:0")

    outcome = provider.start(invocation, None, frozenset(), BudgetPolicy())

    assert outcome == WorkerOutcome.success(candidate())
    assert [entry["event"] for entry in journal_records(path)] == ["invocation-started", "invocation-outcome"]
    reopened = ScriptedWorkerProvider(Inner(RuntimeError("must not be called")), path, CLOCK)
    assert reopened.read_back(invocation) == outcome
    assert ScriptedWorkerProvider(Inner(RuntimeError("x")), tmp_path / "other.jsonl", CLOCK).read_back(invocation) is None


def test_a_crash_between_start_and_outcome_reads_back_as_unresolved(tmp_path: Path) -> None:
    path = tmp_path / "j.jsonl"
    provider = ScriptedWorkerProvider(Inner(RuntimeError("crash")), path, CLOCK)

    with pytest.raises(RuntimeError, match="crash"):
        provider.start(WorkerInvocation("w", "launch:w:0"), None, frozenset(), BudgetPolicy())

    assert [entry["event"] for entry in journal_records(path)] == ["invocation-started"]
    assert provider.read_back(WorkerInvocation("w", "launch:w:0")) is None


def test_finalize_and_cancel_pass_through_and_are_journaled(tmp_path: Path) -> None:
    inner = Inner(WorkerOutcome("failure"))
    provider = ScriptedWorkerProvider(inner, tmp_path / "j.jsonl", CLOCK)

    provider.finalize(WorkerInvocation("w", "launch:w:0"), retain=True)
    assert provider.cancel("launch:w:0", "operator") == "cancelled"

    assert inner.finalized == [("launch:w:0", True)] and inner.cancelled == ["launch:w:0"]
    assert [entry["event"] for entry in journal_records(tmp_path / "j.jsonl")] == ["workspace-finalized", "invocation-cancel"]
