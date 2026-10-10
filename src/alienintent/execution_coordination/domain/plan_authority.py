"""Plan authority: the scope the live canonical plan grants to the Work Items derived from it. Pure.

Founder 2026-10-10 (PLAN-TIP-AUTHORITY-RUNTIME-FIX): the canonical plan at the tip of canonical main is the live
authority root. A derived contract's `authority_issuer` names the plan revision it was prepared from (provenance and
stale-work detection); it inherits when it is inside the live plan's scope, so an item prepared from an older revision
is revalidated against the live one by the same rules, never by its recorded digest.

The canonical plan holds exactly one block fenced as ```json alienintent-plan-authority: the target repositories,
capabilities and budget caps derived work may use, the protected paths no derived work may touch, and the obligations,
each with its priority, the requirement ids it satisfies and the paths it may change, and (Founder,
2026-10-10) its intent, its acceptance ids, the obligations it depends on and the acceptance ids landed work is recorded
to satisfy, with evidence. The block is part of the plan's
bytes, so the approved content digest covers every limit. A plan-derived contract has `release_policy` automatic-on,
`authority_issuer` `plan-authority:sha256:<64 hex>` and exactly one `authority_references` entry
`<plan path> obligation:<LABEL>`; `outside_authority` answers one `owner-decision-required:` reason per rule it fails.
Paths are compared normalized: relative POSIX, no `.`/`..`/empty part, no leading `/`, no `\\`, no glob character,
any trailing `/` removed; scope paths in their exact case, both sides of a comparison with a protected path
case-folded. `A` is under `B` when they are equal or `A` starts with `B/`.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re

from alienintent.execution_coordination.domain.contract import BiuContract

PLAN_PATH = "docs/decisions/alienintent-v2-canonical-project-plan.md"
ISSUER_PREFIX = "plan-authority:"
ISSUER = re.compile(r"plan-authority:sha256:[0-9a-f]{64}")
OPEN, CLOSE = "```json alienintent-plan-authority", "```"
OBLIGATION = "obligation:"
OWNER_DECISION = "owner-decision-required: "
SCOPE_KEYS = frozenset({"target_repositories", "capabilities", "budget_caps", "protected_paths", "obligations"})
CAP_KEYS = frozenset({"maximum_attempts", "hard_wall_clock_seconds", "cancellation_limit", "retry_limit",
                      "concurrency_limit", "hard_required_dimensions"})
OBLIGATION_KEYS = frozenset({"label", "priority", "satisfied_requirement_ids", "allowed_paths", "intent",
                             "acceptance", "depends_on", "satisfied_by"})
SATISFACTION_KEYS = frozenset({"acceptance_id", "work_item", "landed_commit", "evidence"})
ACCEPTANCE_ID = re.compile(r"[A-Z][A-Z0-9]*-A[1-9][0-9]*")
COMMIT = re.compile(r"[0-9a-f]{40}")
# The priorities an obligation may carry: exactly the scheduler's board set, read as P<n> -> n
# (github_work_management.py), so the plan and the scheduler mean the same thing (Founder, decisions section 41).
PRIORITIES = ("P0", "P1", "P2", "P3", "P4", "P5")
# The budget fields capped by the plan, in the order their reasons are named.
CAPPED = ("maximum_attempts", "hard_wall_clock_seconds", "cancellation_limit", "retry_limit", "concurrency_limit")


class PlanScopeInvalid(ValueError):
    """The plan holds no, more than one, or a malformed plan-authority block."""


def priority_rank(priority: str) -> int:
    """The numeric priority, lower first: `P<n>` -> n over exactly `PRIORITIES`, as the scheduler reads the board."""
    if priority not in PRIORITIES:
        raise ValueError(f"priority {priority!r} is not one of {', '.join(PRIORITIES)}")
    return int(priority[1:])


@dataclass(frozen=True)
class Acceptance:
    id: str
    text: str


@dataclass(frozen=True)
class Satisfaction:
    """An acceptance id recorded as satisfied by an earlier landed Work Item, with its evidence: new acceptance is never
    proven retroactively by DONE alone (Founder, decisions section 39)."""
    acceptance_id: str
    work_item: str
    landed_commit: str
    evidence: str


@dataclass(frozen=True)
class Obligation:
    """One plan obligation: its authority (priority, requirement ids, allowed paths) and its semantics (what it must
    achieve, the acceptance ids that finish it, the obligations it depends on, and the ids landed work satisfies)."""
    label: str
    priority: str
    satisfied_requirement_ids: tuple[str, ...]
    allowed_paths: tuple[str, ...]
    intent: str
    acceptance: tuple[Acceptance, ...]
    depends_on: tuple[str, ...]
    satisfied_by: tuple[Satisfaction, ...]


@dataclass(frozen=True)
class PlanScope:
    target_repositories: tuple[str, ...]
    capabilities: tuple[str, ...]
    budget_caps: tuple[tuple[str, object], ...]  # (name, cap) in CAP_KEYS order; hard_required_dimensions a tuple
    protected_paths: tuple[str, ...]
    obligations: tuple[Obligation, ...]

    def cap(self, name: str) -> object:
        return dict(self.budget_caps)[name]

    def obligation(self, label: str) -> Obligation | None:
        return next((obligation for obligation in self.obligations if obligation.label == label), None)

    def document(self) -> dict[str, object]:
        """The block's JSON value, as `scope_from` reads it back."""
        return {"target_repositories": list(self.target_repositories), "capabilities": list(self.capabilities),
                "budget_caps": {name: list(value) if isinstance(value, tuple) else value
                                for name, value in self.budget_caps},
                "protected_paths": list(self.protected_paths),
                "obligations": [{"label": o.label, "priority": o.priority,
                                 "satisfied_requirement_ids": list(o.satisfied_requirement_ids),
                                 "allowed_paths": list(o.allowed_paths), "intent": o.intent,
                                 "acceptance": [{"id": a.id, "text": a.text} for a in o.acceptance],
                                 "depends_on": list(o.depends_on),
                                 "satisfied_by": [{"acceptance_id": s.acceptance_id, "work_item": s.work_item,
                                                   "landed_commit": s.landed_commit, "evidence": s.evidence}
                                                  for s in o.satisfied_by]} for o in self.obligations]}


@dataclass(frozen=True)
class PlanAuthority:
    """One plan revision as authority: `content_digest` is `sha256:` of the plan file's bytes at `commit`; `record_ref`
    a reference to it (the live authority: `git:<commit>:<plan path>`; a recorded approval: its evidence digest)."""
    plan_path: str
    commit: str
    content_digest: str
    record_ref: str
    approver: str
    quote: str
    scope: PlanScope


def normalized(path: object, fold: bool = False) -> str | None:
    """The comparable form of a path, or None when it is malformed: exact case for scope (a candidate's paths must lie in
    the exact assessed scope), case-folded (`fold`) on both sides of any comparison with a protected path."""
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path or any(c in path for c in "*?["):
        return None
    stripped = path[:-1] if path.endswith("/") else path
    parts = stripped.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None
    return stripped.casefold() if fold else stripped


def under(path: str, ancestor: str) -> bool:
    """`path` equals `ancestor` or lies beneath it; both already normalized."""
    return path == ancestor or path.startswith(ancestor + "/")


def parse_scope(text: str) -> PlanScope:
    """The plan's one plan-authority block; PlanScopeInvalid unless exactly one well-formed block is present."""
    lines = text.split("\n")
    opens = [index for index, line in enumerate(lines) if line == OPEN]
    if len(opens) != 1:
        raise PlanScopeInvalid("no plan-authority block" if not opens else "more than one plan-authority block")
    close = next((index for index in range(opens[0] + 1, len(lines)) if lines[index] == CLOSE), None)
    if close is None:
        raise PlanScopeInvalid("the plan-authority block is not closed")
    try:
        document = json.loads("\n".join(lines[opens[0] + 1:close]))
    except ValueError as error:
        raise PlanScopeInvalid(f"the plan-authority block is not JSON: {error}") from None
    return scope_from(document)


def _strings(value: object, name: str, *, paths: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or not all(isinstance(entry, str) and entry for entry in value) \
            or len(set(value)) != len(value) or (paths and any(normalized(entry) is None for entry in value)):
        kind = "well-formed paths" if paths else "strings"
        raise PlanScopeInvalid(f"{name} must be a non-empty list of distinct {kind}")
    return tuple(value)


def _acceptance(value: object, label: str) -> tuple[Acceptance, ...]:
    if not isinstance(value, list) or not value or not all(
            isinstance(a, dict) and set(a) == {"id", "text"} and isinstance(a["id"], str)
            and ACCEPTANCE_ID.fullmatch(a["id"]) and isinstance(a["text"], str) and a["text"].strip() for a in value):
        raise PlanScopeInvalid(f"{label}: acceptance must be a non-empty list of {{id: <LABEL>-A<n>, text}}")
    return tuple(Acceptance(a["id"], a["text"]) for a in value)


def _depends(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(entry, str) and entry for entry in value) \
            or len(set(value)) != len(value):
        raise PlanScopeInvalid(f"{label}: depends_on must be a list of distinct labels")
    return tuple(value)


def _satisfied(value: object, label: str, ids: set[str]) -> tuple[Satisfaction, ...]:
    if not isinstance(value, list) or not all(
            isinstance(s, dict) and set(s) == SATISFACTION_KEYS
            and isinstance(s["acceptance_id"], str) and s["acceptance_id"] in ids
            and isinstance(s["work_item"], str) and s["work_item"].strip()
            and isinstance(s["landed_commit"], str) and COMMIT.fullmatch(s["landed_commit"])
            and isinstance(s["evidence"], str) and s["evidence"].strip() for s in value) \
            or len({s["acceptance_id"] for s in value}) != len(value):
        raise PlanScopeInvalid(f"{label}: satisfied_by must map each of its own acceptance ids at most once, with a "
                               "work item, a 40-hex landed commit and evidence")
    return tuple(Satisfaction(s["acceptance_id"], s["work_item"], s["landed_commit"], s["evidence"]) for s in value)


def _acyclic(obligations: list[Obligation]) -> None:
    """PlanScopeInvalid when `depends_on` names an unknown label or the obligation itself, or closes a cycle."""
    edges = {obligation.label: obligation.depends_on for obligation in obligations}
    for label, dependencies in edges.items():
        if any(dependency == label or dependency not in edges for dependency in dependencies):
            raise PlanScopeInvalid(f"{label}: depends_on names itself or an obligation not in the block")
    finished: set[str] = set()
    active: set[str] = set()

    def visit(label: str) -> None:
        if label in active:
            raise PlanScopeInvalid(f"depends_on has a cycle through {label}")
        if label in finished:
            return
        active.add(label)
        for dependency in edges[label]:
            visit(dependency)
        active.discard(label)
        finished.add(label)
    for label in edges:
        visit(label)


def scope_from(document: object) -> PlanScope:
    """A PlanScope from the block's JSON value, with exactly the keys of the block."""
    if not isinstance(document, dict) or set(document) != SCOPE_KEYS:
        raise PlanScopeInvalid(f"the block needs exactly the keys {', '.join(sorted(SCOPE_KEYS))}")
    caps = document["budget_caps"]
    if not isinstance(caps, dict) or set(caps) != CAP_KEYS \
            or not all(type(caps[name]) is int and caps[name] >= 1 for name in CAPPED):
        raise PlanScopeInvalid(f"budget_caps needs exactly {', '.join(sorted(CAP_KEYS))}, each cap a positive integer")
    dimensions = _strings(caps["hard_required_dimensions"], "hard_required_dimensions")
    listed = document["obligations"]
    if not isinstance(listed, list) or not listed:
        raise PlanScopeInvalid("obligations must be a non-empty list")
    obligations = []
    for entry in listed:
        if not isinstance(entry, dict) or set(entry) != OBLIGATION_KEYS or not isinstance(entry["label"], str) \
                or not entry["label"]:
            raise PlanScopeInvalid(f"each obligation needs exactly {', '.join(sorted(OBLIGATION_KEYS))}")
        label = entry["label"]
        if entry["priority"] not in PRIORITIES:
            raise PlanScopeInvalid(f"{label}: priority must be one of {', '.join(PRIORITIES)}")
        if not isinstance(entry["intent"], str) or not entry["intent"].strip():
            raise PlanScopeInvalid(f"{label}: intent must be a non-empty string")
        acceptance = _acceptance(entry["acceptance"], label)
        obligations.append(Obligation(label, entry["priority"],
                                      _strings(entry["satisfied_requirement_ids"], "satisfied_requirement_ids"),
                                      _strings(entry["allowed_paths"], "allowed_paths", paths=True),
                                      entry["intent"], acceptance, _depends(entry["depends_on"], label),
                                      _satisfied(entry["satisfied_by"], label, {a.id for a in acceptance})))
    if len({obligation.label for obligation in obligations}) != len(obligations):
        raise PlanScopeInvalid("obligation labels must be distinct")
    ids = [acceptance.id for obligation in obligations for acceptance in obligation.acceptance]
    if len(set(ids)) != len(ids):
        raise PlanScopeInvalid("acceptance ids must be distinct across the block")
    _acyclic(obligations)
    return PlanScope(_strings(document["target_repositories"], "target_repositories"),
                     _strings(document["capabilities"], "capabilities"),
                     tuple((name, dimensions if name == "hard_required_dimensions" else caps[name])
                           for name in (*CAPPED, "hard_required_dimensions")),
                     _strings(document["protected_paths"], "protected_paths", paths=True), tuple(obligations))


def obligation_labels(contract: BiuContract) -> tuple[str, ...]:
    """The labels of every `<plan path> obligation:<LABEL>` entry of the contract's authority references."""
    labels = []
    for entry in contract.authority_references:
        words = entry.split()
        if len(words) == 2 and words[0] == PLAN_PATH and words[1].startswith(OBLIGATION):
            labels.append(words[1][len(OBLIGATION):])
    return tuple(labels)


def outside_authority(contract: BiuContract, authority: PlanAuthority) -> tuple[str, ...]:
    """One `owner-decision-required:` reason per failing rule, in rule order; empty when the contract inherits the
    live authority, its priority then the obligation's. The issuer must name a plan revision by its digest; which
    revision it names is provenance, so an item prepared from an older revision is revalidated by every other rule."""
    scope, reasons = authority.scope, []
    if ISSUER.fullmatch(contract.authority_issuer or "") is None:
        reasons.append(f"authority_issuer: not the approved form {ISSUER_PREFIX}sha256:<64 hex>")
    labels = obligation_labels(contract)
    obligation = scope.obligation(labels[0]) if len(labels) == 1 else None
    if len(labels) != 1:
        reasons.append(f"authority_references: exactly one '{PLAN_PATH} {OBLIGATION}<LABEL>' entry is required")
    elif obligation is None:
        reasons.append(f"authority_references: obligation {labels[0]} is not in the approved plan")
    foreign = sorted(set(contract.target_repositories) - set(scope.target_repositories))
    if foreign:
        reasons.append(f"target_repositories: outside the plan: {', '.join(foreign)}")
    capabilities = sorted(set(contract.required_capabilities) - set(scope.capabilities))
    if capabilities:
        reasons.append(f"required_capabilities: outside the plan: {', '.join(capabilities)}")
    if obligation is not None:
        requirements = sorted(set(contract.satisfied_requirement_ids) - set(obligation.satisfied_requirement_ids))
        if requirements:
            reasons.append(f"satisfied_requirement_ids: outside obligation {obligation.label}: "
                           f"{', '.join(requirements)}")
    budget, details = contract.budget_policy, []
    for name in CAPPED:
        value = getattr(budget, name)
        if value is None and name in ("hard_wall_clock_seconds", "cancellation_limit"):
            details.append(f"{name} is required")
        elif value is not None and value > scope.cap(name):
            details.append(f"{name} {value} above the cap {scope.cap(name)}")
    dimensions = set(budget.hard_required_dimensions) - set(scope.cap("hard_required_dimensions"))
    details.extend(f"dimension {name} outside the cap list" for name in sorted(dimensions))
    if details:
        reasons.append(f"budget_policy: {', '.join(details)}")
    entries = [(entry, normalized(entry)) for entry in contract.authorized_scope]
    if obligation is not None:
        allowed = [normalized(path) for path in obligation.allowed_paths]
        refused = [f"{entry} is malformed" if path is None else f"{entry} is outside obligation {obligation.label}"
                   for entry, path in entries if path is None or not any(under(path, a) for a in allowed)]
        if refused:
            reasons.append(f"authorized_scope: {'; '.join(refused)}")
    # The plan itself is always protected: an item that changed it would widen every later item's authority.
    protected = [normalized(path, fold=True) for path in (*scope.protected_paths, PLAN_PATH)]
    crossing = [entry for entry, path in entries if path is not None
                and any(under(path.casefold(), p) or under(p, path.casefold()) for p in protected)]
    if crossing:
        reasons.append(f"authorized_scope: crosses a protected path: {', '.join(crossing)}")
    return tuple(OWNER_DECISION + reason for reason in reasons)
