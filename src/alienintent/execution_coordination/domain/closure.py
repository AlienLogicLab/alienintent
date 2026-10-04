"""The fixed closure action names, their exact receipts, the bounded closure request and the control-plane findings.

Five names in a fixed order. A receipt is `<action>:<work item id>:<full candidate revision>`. The CLOSURE session's
only output is a request over these names; its findings are always carried behind `SESSION_FINDING`, so they can
never look like a receipt or a control-plane finding (`ready-to-land:`, `closure-rework:`, `closure-hold:`). Pure.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import json
import re

CANDIDATE_PUBLISHED, MERGED_TO_MAIN, LANDING_RECORD = "candidate-published", "merged-to-main", "landing-record"
BOARD_UPDATED, WORKSPACES_CLEANED = "board-updated", "workspaces-cleaned"
ACTIONS = (CANDIDATE_PUBLISHED, MERGED_TO_MAIN, LANDING_RECORD, BOARD_UPDATED, WORKSPACES_CLEANED)
SESSION_FINDING = "closure-finding: "
READY_TO_LAND, CLOSURE_REWORK, CLOSURE_HOLD = "ready-to-land", "closure-rework", "closure-hold"
REQUEST_KEYS = frozenset({"identity", "revision", "actions", "findings"})
MAX_FINDINGS, MAX_FINDING_LENGTH = 20, 500
REVISION = re.compile(r"[0-9a-f]{40}")
_FACT = re.compile(r"[0-9a-f]{40}|unreadable")


def is_fixed(required_closure_actions: Iterable[str]) -> bool:
    """Exactly the five fixed names, each once."""
    actions = tuple(required_closure_actions)
    return len(actions) == len(ACTIONS) and set(actions) == set(ACTIONS)


def receipt(action: str, identity: str, revision: str) -> str:
    if action not in ACTIONS or not identity or ":" in identity or REVISION.fullmatch(revision) is None:
        raise ValueError("a receipt names one fixed action, the work item and the full candidate revision")
    return f"{action}:{identity}:{revision}"


def parse_receipt(text: str) -> tuple[str, str, str] | None:
    """(action, identity, revision) of an exact receipt; None for anything else, a bare name included."""
    parts = text.split(":") if isinstance(text, str) else []
    if len(parts) != 3 or parts[0] not in ACTIONS or not parts[1] or REVISION.fullmatch(parts[2]) is None:
        return None
    return parts[0], parts[1], parts[2]


@dataclass(frozen=True)
class ClosureRequest:
    actions: tuple[str, ...]
    findings: tuple[str, ...]


def parse_request(document: bytes | str | None, identity: str, revision: str) -> ClosureRequest | str:
    """The requested actions and findings, or a fixed refusal reason."""
    if document is None:
        return "request-missing"
    try:
        value = json.loads(document)
    except (ValueError, UnicodeDecodeError):
        return "request-malformed"
    if not isinstance(value, dict) or set(value) != REQUEST_KEYS:
        return "request-keys"
    if value["identity"] != identity:
        return "request-identity"
    if value["revision"] != revision:
        return "request-revision"
    actions, findings = value["actions"], value["findings"]
    if not isinstance(actions, list) or not all(isinstance(a, str) and a in ACTIONS for a in actions) \
            or len(set(actions)) != len(actions):
        return "request-actions"
    if not isinstance(findings, list) or len(findings) > MAX_FINDINGS or not all(
            isinstance(f, str) and len(f) <= MAX_FINDING_LENGTH for f in findings):
        return "request-findings"
    return ClosureRequest(tuple(actions), tuple(findings))


def performable(requested: Iterable[str]) -> tuple[str, ...]:
    """`candidate-published`, then each later name in the fixed order up to the first one the request left out."""
    asked, kept = set(requested), [CANDIDATE_PUBLISHED]
    for action in ACTIONS[1:]:
        if action not in asked:
            break
        kept.append(action)
    return tuple(kept)


def session_finding(text: str) -> str:
    return SESSION_FINDING + text


def ready_to_land(merge: str) -> str:
    return f"{READY_TO_LAND}:{_fact(merge)}"


def rework(base: str, head: str) -> str:
    return f"{CLOSURE_REWORK}:base-moved:{_fact(base)}:{_fact(head)}"


def hold(reason: str, *facts: str) -> str:
    if not re.fullmatch(r"[a-z][a-z-]*", reason):
        raise ValueError("a hold reason is a fixed lower-case word")
    return ":".join((CLOSURE_HOLD, reason, *(_fact(fact) for fact in facts)))


def parse_finding(text: str) -> tuple[str, tuple[str, ...]] | None:
    """(kind, parts) of a control-plane finding; None for anything else (a session finding included)."""
    if not isinstance(text, str):
        return None
    kind, _, rest = text.partition(":")
    parts = tuple(rest.split(":")) if rest else ()
    if kind == READY_TO_LAND and len(parts) == 1 and REVISION.fullmatch(parts[0]):
        return kind, parts
    if kind == CLOSURE_REWORK and len(parts) == 3 and parts[0] == "base-moved" and all(
            REVISION.fullmatch(p) for p in parts[1:]):
        return kind, parts
    if kind == CLOSURE_HOLD and parts and re.fullmatch(r"[a-z][a-z-]*", parts[0]) and all(
            _FACT.fullmatch(p) for p in parts[1:]):
        return kind, parts
    return None


def _fact(value: str) -> str:
    if not isinstance(value, str) or _FACT.fullmatch(value) is None:
        raise ValueError("a control-plane finding carries full SHAs only")
    return value
