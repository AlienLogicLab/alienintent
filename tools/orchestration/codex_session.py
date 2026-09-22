#!/usr/bin/env python3
"""Bounded fresh Codex session launcher for the local Program Director.

Invocation shape was **discovered** from the installed CLI (codex-cli 0.155.1,
`codex exec --help`), not guessed:

    codex exec --cd <dir> --ephemeral --sandbox <mode> --model <model>
               --output-last-message <file> -   (prompt on stdin)

Sandbox modes offered by the CLI are `read-only`, `workspace-write` and
`danger-full-access`. This launcher permits the first two and **refuses the third**: never
silently escalate for convenience. Read-only is the default.

The model is resolved from `~/.codex/config.toml` (`model = "gpt-6-astra"`) rather than
hardcoded, and the resolved value is recorded with the run.

Success is never inferred from process exit alone. A structured terminal message must be
captured, or the run is not `ok`. A provider capacity interruption is classified as such —
Wave 1 established that a provider failure is not a task failure.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

CODEX = str(Path.home() / ".local/bin/codex")
ALLOWED_SANDBOXES = ("read-only", "workspace-write")
REFUSED_SANDBOXES = ("danger-full-access",)

# Ambient credentials that must not leak into a child session.
FILTERED_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN")

# "session limit" is Claude's own phrasing for a usage window, seen live in FACT-DV-005 round 2.
_CAPACITY_MARKERS = ("usage limit", "session limit", "quota", "rate limit", "insufficient credits")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _classify_failure(stderr: str, default_reason: str, default_class: str) -> tuple[str, str]:
    """Explain a run that has already been determined to have failed.

    Wave 1 established that a provider capacity interruption is not a task failure, so it gets
    its own class — but only for runs that actually failed.
    """
    blob = (stderr or "").lower()
    if any(m in blob for m in _CAPACITY_MARKERS):
        return ("PROVIDER_CAPACITY_INTERRUPTION",
                f"provider reported a capacity limit; not a task failure ({default_reason})")
    return (default_class, default_reason)


@dataclass
class SessionResult:
    provider: str = "codex"
    model: str | None = None
    prompt_path: str | None = None
    sandbox: str = "read-only"
    started_at: str = ""
    ended_at: str = ""
    exit_code: int | None = None
    terminal_message: str = ""
    stdout: str = ""
    stderr: str = ""
    sha_before: str | None = None
    sha_after: str | None = None
    ok: bool = False
    failure_reason: str = ""
    failure_class: str | None = None
    argv: list = field(default_factory=list)

    def as_record(self) -> dict:
        return {
            "provider": self.provider, "model": self.model, "prompt_path": self.prompt_path,
            "sandbox": self.sandbox, "started_at": self.started_at, "ended_at": self.ended_at,
            "exit_code": self.exit_code, "ok": self.ok,
            "failure_reason": self.failure_reason, "failure_class": self.failure_class,
            "sha_before": self.sha_before, "sha_after": self.sha_after,
            "terminal_message_chars": len(self.terminal_message),
            # Not reported by this invocation path; never recorded as zero (SWF-09).
            "token_usage": "UNKNOWN", "cost": "UNKNOWN",
            "invocation": " ".join(self.argv),
        }


class CodexSession:
    def __init__(self, workdir: Path | str, runner=subprocess.run, codex_path: str = CODEX) -> None:
        self.workdir = Path(workdir)
        self.runner = runner
        self.codex_path = codex_path

    def run(self, prompt: str, sandbox: str = "read-only", model: str | None = None,
            output_file: Path | str | None = None, prompt_path: str | None = None,
            sha_before: str | None = None, sha_after: str | None = None,
            timeout_s: int = 1800) -> SessionResult:
        if sandbox in REFUSED_SANDBOXES:
            raise ValueError(
                f"sandbox {sandbox!r} is refused: never silently use danger-full-access for convenience")
        if sandbox not in ALLOWED_SANDBOXES:
            raise ValueError(f"unknown sandbox mode {sandbox!r}; allowed: {ALLOWED_SANDBOXES}")

        if model is None:
            from director import resolved_codex_model
            model = resolved_codex_model()
        out = Path(output_file) if output_file else self.workdir / ".codex-last-message.txt"

        argv = [self.codex_path, "exec", "--cd", str(self.workdir), "--ephemeral",
                "--sandbox", sandbox, "--model", model, "--output-last-message", str(out), "-"]

        env = {k: v for k, v in os.environ.items() if k not in FILTERED_ENV}
        result = SessionResult(model=model, prompt_path=prompt_path, sandbox=sandbox,
                               started_at=_now(), sha_before=sha_before, argv=argv)
        try:
            proc = self.runner(argv, input=prompt, capture_output=True, text=True,
                               env=env, timeout=timeout_s)
            result.exit_code = proc.returncode
            result.stdout = (proc.stdout or "")[-4000:]
            result.stderr = (proc.stderr or "")[-4000:]
        except Exception as exc:
            result.exit_code = None
            result.failure_reason = f"launch failed: {exc}"
            result.failure_class = "LAUNCH_FAILURE"
            result.ended_at = _now()
            return result

        result.ended_at = _now()
        result.sha_after = sha_after
        result.terminal_message = out.read_text() if out.exists() else ""

        # Decide success FIRST, then explain a failure. Capacity markers describe *why* a run
        # failed; they never decide *whether* it failed. The CLI prints a rate-limit/usage
        # banner on healthy runs too, so matching stderr ahead of the outcome once rejected a
        # run that exited 0 with a correct terminal report.
        if result.exit_code != 0:
            result.failure_class, result.failure_reason = _classify_failure(
                result.stderr + "\n" + result.stdout[-2000:],
                f"non-zero exit {result.exit_code}", "NONZERO_EXIT")
            return result
        if not result.terminal_message.strip():
            result.failure_class, result.failure_reason = _classify_failure(
                result.stderr,
                "exit 0 but no structured terminal message was captured; "
                "success is not inferred from process exit alone",
                "MISSING_TERMINAL_RESULT")
            return result

        result.ok = True
        return result
