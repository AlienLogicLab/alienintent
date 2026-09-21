"""Tests for the bounded Codex session launcher.

Flags here were discovered from the installed CLI (`codex exec --help`, codex-cli 0.155.1),
not guessed, per the bootstrap requirement. The model is resolved from
`~/.codex/config.toml`, never hardcoded.

Success is never inferred from process exit alone — a structured terminal result is required.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from codex_session import CodexSession, SessionResult  # noqa: E402


class _FakeProc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def _runner(capture, returncode=0, stdout="", stderr=""):
    def run(argv, **kw):
        capture["argv"] = argv
        capture["env"] = kw.get("env")
        return _FakeProc(returncode, stdout, stderr)
    return run


# --- invocation shape -------------------------------------------------------------


def test_the_invocation_uses_exec_with_the_discovered_flags(tmp_path):
    cap = {}
    CodexSession(workdir=tmp_path, runner=_runner(cap)).run(
        prompt="hello", sandbox="read-only", model="gpt-6-astra", output_file=tmp_path / "last.txt")
    argv = cap["argv"]
    assert argv[0].endswith("codex") and argv[1] == "exec"
    assert "--sandbox" in argv and argv[argv.index("--sandbox") + 1] == "read-only"
    assert "--model" in argv and argv[argv.index("--model") + 1] == "gpt-6-astra"
    assert "--cd" in argv and argv[argv.index("--cd") + 1] == str(tmp_path)


def test_sessions_are_fresh_and_unpersisted_by_default(tmp_path):
    cap = {}
    CodexSession(workdir=tmp_path, runner=_runner(cap)).run(prompt="x", sandbox="read-only")
    assert "--ephemeral" in cap["argv"]


def test_the_terminal_message_is_captured_to_a_file(tmp_path):
    cap = {}
    out = tmp_path / "last.txt"
    CodexSession(workdir=tmp_path, runner=_runner(cap)).run(prompt="x", sandbox="read-only",
                                                            output_file=out)
    assert "--output-last-message" in cap["argv"]
    assert str(out) in cap["argv"]


def test_read_only_is_the_default_sandbox(tmp_path):
    cap = {}
    CodexSession(workdir=tmp_path, runner=_runner(cap)).run(prompt="x")
    assert cap["argv"][cap["argv"].index("--sandbox") + 1] == "read-only"


def test_danger_full_access_is_refused(tmp_path):
    """Never silently escalate for convenience."""
    import pytest
    with pytest.raises(ValueError):
        CodexSession(workdir=tmp_path, runner=_runner({})).run(prompt="x",
                                                               sandbox="danger-full-access")


def test_an_unknown_sandbox_mode_is_refused(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        CodexSession(workdir=tmp_path, runner=_runner({})).run(prompt="x", sandbox="wide-open")


# --- credential hygiene ------------------------------------------------------------


def test_ambient_anthropic_credentials_are_filtered_from_the_child(tmp_path, monkeypatch):
    """Wave 1 proved an ambient ANTHROPIC_API_KEY overrides subscription login."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-not-leak")
    cap = {}
    CodexSession(workdir=tmp_path, runner=_runner(cap)).run(prompt="x", sandbox="read-only")
    assert "ANTHROPIC_API_KEY" not in (cap["env"] or {})


# --- success is not process exit ----------------------------------------------------


def test_exit_zero_without_a_terminal_message_is_not_success(tmp_path):
    res = CodexSession(workdir=tmp_path, runner=_runner({}, returncode=0)).run(
        prompt="x", sandbox="read-only", output_file=tmp_path / "missing.txt")
    assert res.exit_code == 0
    assert res.ok is False
    assert "terminal" in res.failure_reason.lower()


def test_a_captured_terminal_message_with_exit_zero_is_success(tmp_path):
    out = tmp_path / "last.txt"

    def runner(argv, **kw):
        out.write_text("FINAL REPORT: all checks passed")
        return _FakeProc(0)

    res = CodexSession(workdir=tmp_path, runner=runner).run(prompt="x", sandbox="read-only",
                                                            output_file=out)
    assert res.ok is True
    assert "FINAL REPORT" in res.terminal_message


def test_a_nonzero_exit_is_not_success(tmp_path):
    out = tmp_path / "last.txt"

    def runner(argv, **kw):
        out.write_text("partial")
        return _FakeProc(1, stderr="usage limit")
    res = CodexSession(workdir=tmp_path, runner=runner).run(prompt="x", sandbox="read-only",
                                                            output_file=out)
    assert res.ok is False


def test_provider_capacity_failure_is_classified_not_counted_as_task_failure(tmp_path):
    """Wave 1: a provider interruption is not a repair failure."""
    def runner(argv, **kw):
        return _FakeProc(1, stderr="You've hit your usage limit. try again at 6:22 PM")
    res = CodexSession(workdir=tmp_path, runner=runner).run(prompt="x", sandbox="read-only")
    assert res.failure_class == "PROVIDER_CAPACITY_INTERRUPTION"


# --- evidence record ----------------------------------------------------------------


def test_the_result_records_the_evidence_the_plan_requires(tmp_path):
    out = tmp_path / "last.txt"

    def runner(argv, **kw):
        out.write_text("done")
        return _FakeProc(0)
    res = CodexSession(workdir=tmp_path, runner=runner).run(
        prompt="x", sandbox="read-only", model="gpt-6-astra", output_file=out,
        prompt_path="prompts/t.md", sha_before="aaa", sha_after="bbb")
    rec = res.as_record()
    for key in ("provider", "model", "prompt_path", "started_at", "ended_at", "exit_code",
                "sandbox", "sha_before", "sha_after", "ok", "token_usage", "cost"):
        assert key in rec, key
    assert rec["token_usage"] == "UNKNOWN" and rec["cost"] == "UNKNOWN"
    assert json.dumps(rec)


def test_a_successful_run_is_not_reclassified_by_a_capacity_warning_in_stderr(tmp_path):
    """Observed live: a run that exited 0 and produced a correct terminal report was
    classified PROVIDER_CAPACITY_INTERRUPTION because a capacity phrase appeared somewhere
    in stderr. Capacity classification must only apply to runs that actually failed."""
    out = tmp_path / "last.txt"

    def runner(argv, **kw):
        out.write_text("BIUS=11\nFIRST_PASS=2\n")
        return _FakeProc(0, stderr="tokens used 10,275\nrate limit: 62% of 5h window remaining")

    res = CodexSession(workdir=tmp_path, runner=runner).run(prompt="x", sandbox="read-only",
                                                            output_file=out)
    assert res.ok is True
    assert res.failure_class is None


def test_capacity_classification_still_applies_when_the_run_actually_failed(tmp_path):
    def runner(argv, **kw):
        return _FakeProc(1, stderr="You've hit your usage limit. try again at 6:22 PM")
    res = CodexSession(workdir=tmp_path, runner=runner).run(prompt="x", sandbox="read-only")
    assert res.ok is False
    assert res.failure_class == "PROVIDER_CAPACITY_INTERRUPTION"
