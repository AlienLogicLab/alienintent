#!/usr/bin/env python3
"""Fresh Claude session launcher — the Tier 4 independent reviewer.

Built for Phase 10, which requires "fresh Claude independent context for major design
verification". Fresh means independent of both the author (a Codex session) and the resident
participant (this coordinator): the reviewer inherits no conversation and is given the artifact,
not the conclusion.

Read-only by default. A verifier that can edit the artifact it verifies is not a verifier, so
`--permission-mode plan` is the default and `bypassPermissions` is refused outright rather than
offered — the same rule `codex_session.py` applies to `danger-full-access`.

Wave 1 established that an ambient `ANTHROPIC_API_KEY` silently overrides subscription login and
produced a 401 when subscription auth was intended, so filtering it is a correctness property
rather than hygiene.

Success is never inferred from process exit. Capacity markers explain a run that already failed;
they never decide whether it failed — the precedence defect found during the bootstrap, carried
forward here as a test rather than as a comment.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

CLAUDE = str(Path.home() / ".local/bin/claude")

# Read-only planning mode is the default; acceptEdits must be asked for; bypass is refused.
ALLOWED_MODES = ("plan", "acceptEdits", "default")
REFUSED_MODES = ("bypassPermissions",)

FILTERED_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")

# "session limit" is Claude's own phrasing for a usage window, seen live in FACT-DV-005 round 2.
_CAPACITY_MARKERS = ("usage limit", "session limit", "quota", "rate limit", "insufficient credits")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _classify_failure(stderr: str, default_reason: str, default_class: str) -> tuple[str, str]:
    blob = (stderr or "").lower()
    if any(m in blob for m in _CAPACITY_MARKERS):
        return ("PROVIDER_CAPACITY_INTERRUPTION",
                f"provider reported a capacity limit; not a task failure ({default_reason})")
    return (default_class, default_reason)


@dataclass
class ClaudeResult:
    provider: str = "claude"
    permission_mode: str = "plan"
    prompt_path: str | None = None
    started_at: str = ""
    ended_at: str = ""
    exit_code: int | None = None
    terminal_message: str = ""
    stdout: str = ""
    stderr: str = ""
    ok: bool = False
    failure_reason: str = ""
    failure_class: str | None = None
    argv: list = field(default_factory=list)

    def as_record(self) -> dict:
        return {"provider": self.provider, "permission_mode": self.permission_mode,
                "prompt_path": self.prompt_path, "started_at": self.started_at,
                "ended_at": self.ended_at, "exit_code": self.exit_code, "ok": self.ok,
                "failure_reason": self.failure_reason, "failure_class": self.failure_class,
                "terminal_message_chars": len(self.terminal_message),
                # Not reported by this invocation path; never recorded as zero (SF-REQ-030).
                "token_usage": "UNKNOWN", "cost": "UNKNOWN",
                "invocation": " ".join(self.argv)}


class ClaudeSession:
    def __init__(self, workdir: Path | str, runner=subprocess.run,
                 claude_path: str = CLAUDE) -> None:
        self.workdir = Path(workdir)
        self.runner = runner
        self.claude_path = claude_path

    def run(self, prompt: str, permission_mode: str = "plan",
            output_file: Path | str | None = None, prompt_path: str | None = None,
            timeout_s: int = 3600) -> ClaudeResult:
        if permission_mode in REFUSED_MODES:
            raise ValueError(
                f"permission mode {permission_mode!r} is refused: a verifier must not be able to "
                "edit what it verifies")
        if permission_mode not in ALLOWED_MODES:
            raise ValueError(f"unknown permission mode {permission_mode!r}; allowed {ALLOWED_MODES}")

        argv = [self.claude_path, "-p", "--permission-mode", permission_mode]
        env = {k: v for k, v in os.environ.items() if k not in FILTERED_ENV}
        result = ClaudeResult(permission_mode=permission_mode, prompt_path=prompt_path,
                              started_at=_now(), argv=argv)
        out = Path(output_file) if output_file else None

        try:
            proc = self.runner(argv, input=prompt, capture_output=True, text=True,
                               env=env, cwd=str(self.workdir), timeout=timeout_s)
            result.exit_code = proc.returncode
            result.stdout = (proc.stdout or "")
            result.stderr = (proc.stderr or "")[-4000:]
        except Exception as exc:
            result.exit_code = None
            result.failure_reason = f"launch failed: {exc}"
            result.failure_class = "LAUNCH_FAILURE"
            result.ended_at = _now()
            return result

        result.ended_at = _now()
        # `claude -p` writes its answer to stdout; an output file is written by the session when
        # the prompt asks for one. Prefer the file, fall back to stdout.
        if out is not None and out.exists():
            result.terminal_message = out.read_text()
        else:
            result.terminal_message = result.stdout
            # A plan-mode reviewer cannot write files, so the launcher owns persistence: the
            # review must outlive the process object that captured it (found live, FACT-DV-005).
            if out is not None and result.terminal_message.strip():
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(result.terminal_message)

        if result.exit_code != 0:
            result.failure_class, result.failure_reason = _classify_failure(
                result.stderr + "\n" + result.stdout[-2000:],
                f"non-zero exit {result.exit_code}", "NONZERO_EXIT")
            return result
        if not result.terminal_message.strip():
            result.failure_class, result.failure_reason = _classify_failure(
                result.stderr,
                "exit 0 but no structured terminal report was captured; success is not inferred "
                "from process exit alone", "MISSING_TERMINAL_RESULT")
            return result

        result.ok = True
        return result
