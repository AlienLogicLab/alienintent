"""Tests for the fresh Claude session launcher.

Phase 10 requires "fresh Claude independent context for major design verification". Fresh means
independent of both the author (Codex) and the participant (this coordinator), so the launcher
must not inherit conversation, and must not be handed the participant's context by convenience.

Read-only by default: a verifier that can edit the artifact it verifies is not a verifier.
Wave 1 established that an ambient ANTHROPIC_API_KEY silently overrides subscription login, so
credential filtering is a correctness property here, not hygiene.

Success is never inferred from process exit alone.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from claude_session import ClaudeSession  # noqa: E402


class _FakeProc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def _runner(cap, returncode=0, stdout="", stderr=""):
    def run(argv, **kw):
        cap["argv"] = argv
        cap["env"] = kw.get("env")
        cap["input"] = kw.get("input")
        return _FakeProc(returncode, stdout, stderr)
    return run


def test_the_invocation_is_non_interactive_and_read_only_by_default(tmp_path):
    cap = {}
    ClaudeSession(workdir=tmp_path, runner=_runner(cap)).run(prompt="verify this")
    argv = cap["argv"]
    assert argv[0].endswith("claude")
    assert "-p" in argv
    assert "--permission-mode" in argv
    assert argv[argv.index("--permission-mode") + 1] == "plan"


def test_a_writable_mode_must_be_asked_for_explicitly(tmp_path):
    cap = {}
    ClaudeSession(workdir=tmp_path, runner=_runner(cap)).run(prompt="x", permission_mode="acceptEdits")
    assert cap["argv"][cap["argv"].index("--permission-mode") + 1] == "acceptEdits"


def test_bypass_permissions_is_refused(tmp_path):
    """Never silently escalate a verifier to full write access."""
    with pytest.raises(ValueError):
        ClaudeSession(workdir=tmp_path, runner=_runner({})).run(
            prompt="x", permission_mode="bypassPermissions")


def test_ambient_anthropic_credentials_are_filtered(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-not-leak")
    cap = {}
    ClaudeSession(workdir=tmp_path, runner=_runner(cap)).run(prompt="x")
    assert "ANTHROPIC_API_KEY" not in (cap["env"] or {})


def test_the_prompt_is_passed_on_stdin_not_as_an_argument(tmp_path):
    """A long verification prompt on argv risks truncation and leaks into process listings."""
    cap = {}
    ClaudeSession(workdir=tmp_path, runner=_runner(cap)).run(prompt="a long prompt")
    assert cap["input"] == "a long prompt"
    assert "a long prompt" not in cap["argv"]


def test_a_captured_terminal_report_with_exit_zero_is_success(tmp_path):
    out = tmp_path / "last.txt"

    def runner(argv, **kw):
        out.write_text("DISPOSITION=VERIFIED")
        return _FakeProc(0)

    res = ClaudeSession(workdir=tmp_path, runner=runner).run(prompt="x", output_file=out)
    assert res.ok is True
    assert "VERIFIED" in res.terminal_message


def test_exit_zero_without_a_terminal_report_is_not_success(tmp_path):
    res = ClaudeSession(workdir=tmp_path, runner=_runner({}, returncode=0)).run(
        prompt="x", output_file=tmp_path / "missing.txt")
    assert res.ok is False
    assert "terminal" in res.failure_reason.lower()


def test_a_capacity_marker_only_classifies_a_run_that_actually_failed(tmp_path):
    """The defect found during the bootstrap: markers explain a failure, they do not decide one."""
    out = tmp_path / "last.txt"

    def runner(argv, **kw):
        out.write_text("DISPOSITION=VERIFIED")
        return _FakeProc(0, stderr="5h limit: 62% remaining")

    res = ClaudeSession(workdir=tmp_path, runner=runner).run(prompt="x", output_file=out)
    assert res.ok is True
    assert res.failure_class is None


def test_a_failed_run_with_a_capacity_marker_is_classified(tmp_path):
    res = ClaudeSession(workdir=tmp_path, runner=_runner({}, returncode=1,
                                                         stderr="usage limit reached")).run(prompt="x")
    assert res.ok is False
    assert res.failure_class == "PROVIDER_CAPACITY_INTERRUPTION"


def test_the_record_never_reports_unknown_telemetry_as_zero(tmp_path):
    out = tmp_path / "last.txt"

    def runner(argv, **kw):
        out.write_text("done")
        return _FakeProc(0)
    rec = ClaudeSession(workdir=tmp_path, runner=runner).run(prompt="x", output_file=out).as_record()
    assert rec["token_usage"] == "UNKNOWN" and rec["cost"] == "UNKNOWN"
    assert rec["provider"] == "claude"


def test_the_terminal_message_is_persisted_to_the_output_file_when_the_reviewer_cannot_write(tmp_path):
    """Found live (FACT-DV-005): a plan-mode reviewer cannot write files, so an `output_file` that
    the prompt asked for never appeared and the 24,722-character review survived only in the
    process object, which the caller discarded. The launcher owns persistence: if the reviewer did
    not write the file, the launcher writes the captured terminal message there."""
    cap = {}
    out = tmp_path / "review.md"
    ClaudeSession(workdir=tmp_path, runner=_runner(cap, stdout="DISPOSITION: ACCEPT\n")).run(
        prompt="verify", output_file=out)
    assert out.read_text() == "DISPOSITION: ACCEPT\n"


def test_a_session_limit_message_is_a_capacity_interruption_not_a_task_failure(tmp_path):
    """Found live (FACT-DV-005 round 2): the reviewer exited non-zero with the provider's own
    "You've hit your session limit" message and was classified NONZERO_EXIT. Wave 1's rule: a
    provider capacity interruption is never a task failure, so the marker set must know this
    phrasing."""
    cap = {}
    r = ClaudeSession(workdir=tmp_path, runner=_runner(cap, returncode=1, stdout="You've hit your session limit · resets 5:30pm")).run(prompt="verify")
    assert r.failure_class == "PROVIDER_CAPACITY_INTERRUPTION"
