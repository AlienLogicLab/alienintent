"""Bounded, durable diagnostics of one worker process, and the cause they show. Pure.

A worker process's exit status, the ends of its output streams and its provider command are kept with the invocation's
outcome in the invocation journal, so the reason a worker ended survives the launcher. The cause is read from those
facts only; it is a label for a person diagnosing, never a verdict, and `unknown` when nothing matches. Every kept
text is redacted first: token-like text becomes [REDACTED] (the rule the live worker-boundary proof already used).
"""
from __future__ import annotations

from pathlib import Path
import re
from typing import Sequence

TAIL = 4000  # characters kept from the end of each stream
ARGUMENT = 200  # characters kept of each command argument
CAUSES = ("success", "closed", "accept", "reject", "timeout", "network-or-provider", "authentication",
          "launcher-or-runtime", "malformed-verdict", "cancellation", "unknown")
_RESULTS = frozenset({"success", "closed", "accept", "reject", "verification-evidence-invalid",
                      "mutation-harness-unavailable"})
_AUTHENTICATION = re.compile(r"unauthori[sz]ed|forbidden|not logged in|log ?in required|authentication failed|"
                             r"invalid api key|token (?:has )?expired", re.I)
_SESSION = re.compile(r"session[ _]id\"?\s*[:=]\s*\"?([0-9A-Za-z]{8}(?:-[0-9A-Za-z]{4,12}){1,4})", re.I)
_NETWORK = re.compile(r"error sending request|timed out|EAI_AGAIN|could not resolve|name resolution|"
                      r"connection (?:refused|reset|closed)|routing discovery failed|reconnecting|rate limit|overloaded|"
                      r"service unavailable|bad gateway|gateway timeout|internal server error", re.I)
_VERDICT = frozenset({"verdict-missing", "verdict-malformed", "verdict-miscorrelated"})
_SECRETS = (re.compile(r"(?i)\b(authorization|bearer|token|password|secret|api[_-]?key)\b([\s:=]+)(?:(?:bearer|basic|token)\s+)?\S+"),
            re.compile(r"\b(sk-[\w-]{8,}|gh[pousr]_\w{16,}|github_pat_\w+|eyJ[\w-]+\.[\w-]+\.[\w-]+)"),
            re.compile(r"(?=[\w+/=-]{48,})(?![0-9a-f]+\b)[\w+/=-]{48,}"))


def redact(text: str) -> str:
    """`text` with token-like text replaced by [REDACTED]; a 40- or 64-hex object name stays readable."""
    text = _SECRETS[0].sub(lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]", text)
    for pattern in _SECRETS[1:]:
        text = pattern.sub("[REDACTED]", text)
    return text


def process_diagnostics(provider: str, command: Sequence[str], kind: str, exit_status: int | None, stdout: str,
                        stderr: str) -> dict[str, object]:
    """The bounded, redacted record of one process: its provider and executable, the provider's session id when its
    output names one, its command, its result kind and exit status, and the last TAIL characters of each stream."""
    session = _SESSION.search(f"{stderr}\n{stdout}")
    return {"provider": provider, "executable": Path(command[0]).name if command else None,
            "session_id": None if session is None else redact(session.group(1)),
            "command": [redact(argument)[:ARGUMENT] for argument in command],
            "process_kind": kind, "exit_status": exit_status,
            "stdout_tail": redact(stdout)[-TAIL:], "stderr_tail": redact(stderr)[-TAIL:]}


def cause(outcome_kind: str, diagnostics: dict[str, object] | None) -> str:
    """The cause of an invocation's outcome, from its kind and its last process's diagnostics. A process ended by a
    signal (a negative exit status: an operator kill, a shutdown) is a cancellation."""
    if outcome_kind in _RESULTS:
        return outcome_kind
    if outcome_kind in {"cancelled", "cancellation"}:
        return "cancellation"
    if outcome_kind == "timeout":
        return "timeout"
    exit_status = None if diagnostics is None else diagnostics.get("exit_status")
    if isinstance(exit_status, int) and exit_status < 0:
        return "cancellation"
    if outcome_kind in _VERDICT and exit_status == 0:
        return "malformed-verdict"
    if exit_status == 0:
        return "unknown"  # the process succeeded: its text says nothing about why the outcome failed
    text = "" if diagnostics is None else f"{diagnostics.get('stdout_tail', '')}\n{diagnostics.get('stderr_tail', '')}"
    if _AUTHENTICATION.search(text):
        return "authentication"
    if _NETWORK.search(text):
        return "network-or-provider"
    if exit_status in {126, 127}:
        return "launcher-or-runtime"
    return "unknown"
