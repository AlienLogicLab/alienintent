"""Deterministic context reconstruction from a pinned manifest; conversation is never an input."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
import json
from typing import Iterable, Mapping

from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
from alienintent.execution_coordination.domain.lifecycle import ExecutionState, LifecycleError, LifecycleStage, transition
from alienintent.execution_coordination.domain.verdict import Verdict, VerdictKind

DERIVATION_RULE = "LABELLED_DERIVATION_RULE_v1"
EPISODE_SUBSTITUTE = "LOCAL_PROCESS_BOUNDARY_SUBSTITUTE_FOR_EPISODE"
RULE_TEXT = (
    "LABELLED_DERIVATION_RULE_v1: for each factory:/release: item, authorized_next_action_set holds the "
    "actions execution_coordination.domain.lifecycle.transition accepts from the item's current "
    "ExecutionState, probed on the pure value (never committed) with each action's own admission witness; "
    "items with an open DecisionInbox entry, a PENDING/SEEN attention item or an authority block go to "
    "blocked_set with typed reasons instead; terminal items (FactoryCoordinator.guard_account) have "
    "neither. Output is canonically sorted."
)
FIELDS = ("authorized_next_action_set", "blocked_set", "current_work", "unresolved_decisions",
          "pending_attention", "evidence_refs", "lifecycle")
POINTER_PREFIX = "context:manifest:"
RECORD_PREFIXES = ("factory:", "release:", "attention:")
SINGLE_RECORDS = ("decision-inbox", "upstream:requirements:current")
INVENTORY = "upstream:requirements:current"
# The complete action vocabulary of lifecycle.transition; "authority-block"
# and "cancel" always raise there, so the probe never accepts them.
LIFECYCLE_ACTIONS = ("accept", "authority-block", "cancel", "close", "review", "rework", "verify")
# Outcome classes as FactoryCoordinator applies them; no new predicate.
TERMINAL_OUTCOMES = frozenset({"cancelled-by-operator", "cancelled-by-decision", "failure", "timeout"})
AUTHORITY_OUTCOMES = frozenset({"authority-block", "blocked-by-authority"})
ESCALATION_FIELDS = frozenset({"profile", "project", "work_item", "biu_version", "decision", "reason", "options",
                               "tradeoffs", "recommendation", "affected_requirements", "affected_architecture",
                               "cost_of_waiting", "authorizations"})
ATTENTION_STATUSES = frozenset({"PENDING", "SEEN", "RESOLVED"})
_WITNESS_CANDIDATE = CandidateRef.local_artifact("sha256:" + "0" * 64, "witness:lifecycle-probe").with_independent_read_back()
_WITNESS_VERDICT = Verdict(VerdictKind.ACCEPT, "admission witness for a non-committing lifecycle probe")


class HoldReason(StrEnum):
    MISSING_RECORD = "MISSING_RECORD"
    VERSION_DRIFT = "VERSION_DRIFT"
    DIGEST_MISMATCH = "DIGEST_MISMATCH"
    EVIDENCE_UNAVAILABLE = "EVIDENCE_UNAVAILABLE"
    STORE_UNAVAILABLE = "STORE_UNAVAILABLE"
    MALFORMED_DECISION_INBOX = "MALFORMED_DECISION_INBOX"
    INVENTORY_UNAVAILABLE = "INVENTORY_UNAVAILABLE"
    MALFORMED_RECORD = "MALFORMED_RECORD"
    INVALID_MANIFEST = "INVALID_MANIFEST"


@dataclass(frozen=True)
class ContextHold(Exception):
    """A typed refusal to reconstruct; never an empty or guessed action set."""
    reason: HoldReason
    affected_refs: tuple[str, ...] = ()
    detail: str = ""

    def __str__(self) -> str:
        return f"{self.reason}: {', '.join(self.affected_refs)} {self.detail}".strip()

    def document(self) -> dict[str, object]:
        return {"status": "HOLD", "reason": str(self.reason), "affected_refs": list(self.affected_refs),
                "detail": self.detail}


@dataclass(frozen=True)
class ReconstructedContext:
    manifest_ref: str
    manifest_digest: str
    manifest_observation: Mapping[str, str]
    document: Mapping[str, object]
    digest: str


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()


def digest(value: object) -> str:
    return "sha256:" + sha256(canonical(value)).hexdigest()


def _hold(reason: HoldReason, *refs: str, detail: str = "") -> ContextHold:
    return ContextHold(reason, tuple(refs), detail)


def _enumerated(aggregate: str) -> bool:
    return aggregate.startswith(RECORD_PREFIXES) or aggregate in SINGLE_RECORDS


def referenced_evidence(aggregate: str, state: Mapping[str, object]) -> Mapping[str, object] | None:
    """The evidence body a pinned pointer references, if its record class has one."""
    if not state:
        return None
    key = "history_ref" if aggregate.startswith("attention:") else "snapshot_ref" if aggregate == INVENTORY else None
    if key is None:
        return None
    ref = state.get(key)
    if not isinstance(ref, dict):
        reason = HoldReason.INVENTORY_UNAVAILABLE if aggregate == INVENTORY else HoldReason.MALFORMED_RECORD
        raise _hold(reason, aggregate, detail=f"pointer lacks {key}")
    return ref


def pin_manifest(project: str, profile: str, records: Iterable[tuple[str, int, Mapping[str, object]]]) -> dict[str, object]:
    """Pin every enumerated record class by version and digest, plus the evidence they reference."""
    entries, evidence = [], []
    for aggregate, version, state in records:
        if not _enumerated(aggregate):
            raise _hold(HoldReason.INVALID_MANIFEST, aggregate, detail="record class is not enumerated")
        entries.append({"aggregate": aggregate, "version": version, "digest": digest(state)})
        ref = referenced_evidence(aggregate, state)
        if ref is not None:
            evidence.append({"owner": aggregate, "ref": dict(ref)})
    entries = sorted(entries, key=lambda entry: entry["aggregate"])
    evidence = sorted(evidence, key=lambda entry: canonical(entry))
    return {"schema_version": 1, "project": project, "profile": profile, "rule": DERIVATION_RULE,
            "entries": entries, "evidence": evidence}


def validate_manifest(manifest: object, project: str, profile: str) -> dict[str, object]:
    if (not isinstance(manifest, dict) or set(manifest) != {"schema_version", "project", "profile", "rule", "entries", "evidence"}
            or manifest["schema_version"] != 1 or manifest["rule"] != DERIVATION_RULE
            or not isinstance(manifest["entries"], list) or not isinstance(manifest["evidence"], list)):
        raise _hold(HoldReason.INVALID_MANIFEST, detail="manifest shape")
    if (manifest["project"], manifest["profile"]) != (project, profile):
        raise _hold(HoldReason.INVALID_MANIFEST, detail="manifest scope")
    aggregates = set()
    for entry in manifest["entries"]:
        if (not isinstance(entry, dict) or set(entry) != {"aggregate", "version", "digest"}
                or not isinstance(entry["aggregate"], str) or not _enumerated(entry["aggregate"])
                or type(entry["version"]) is not int or entry["version"] < 0 or not isinstance(entry["digest"], str)
                or entry["aggregate"] in aggregates):
            raise _hold(HoldReason.INVALID_MANIFEST, detail="manifest entry")
        aggregates.add(entry["aggregate"])
    if any(not isinstance(e, dict) or set(e) != {"owner", "ref"} or e["owner"] not in aggregates
           or not isinstance(e["ref"], dict) for e in manifest["evidence"]):
        raise _hold(HoldReason.INVALID_MANIFEST, detail="manifest evidence")
    return manifest


def _valid_inbox(raw: Mapping[str, object]) -> bool:
    if not raw:
        return True
    entries = raw.get("open")
    return (set(raw) == {"open"} and isinstance(entries, dict)
            and all(isinstance(key, str) and isinstance(value, dict) and set(value) == ESCALATION_FIELDS
                    and value["work_item"] == key and type(value["biu_version"]) is int
                    and isinstance(value["options"], list) for key, value in entries.items()))


def decode_decision_inbox(raw: Mapping[str, object]) -> tuple[dict[str, object], ...]:
    """Validate the raw DecisionInbox aggregate itself; DecisionInbox.list_open is unchanged."""
    if not _valid_inbox(raw):
        raise _hold(HoldReason.MALFORMED_DECISION_INBOX, "decision-inbox")
    entries = raw.get("open", {})
    return tuple({"work_item": key, "biu_version": value["biu_version"], "decision": value["decision"],
                  "reason": value["reason"], "options": sorted(value["options"])}
                 for key, value in sorted(entries.items()))


def decode_attention(aggregate: str, version: int, body: object) -> dict[str, object]:
    if (not isinstance(body, dict) or body.get("status") not in ATTENTION_STATUSES
            or not isinstance(body.get("origin"), dict)
            or not all(isinstance(body["origin"].get(k), str) for k in ("work_ref", "kind", "required_authority"))):
        raise _hold(HoldReason.MALFORMED_RECORD, aggregate, detail="attention history body")
    origin = body["origin"]
    return {"identity": aggregate, "version": version, "status": body["status"], "work_ref": origin["work_ref"],
            "kind": origin["kind"], "required_authority": origin["required_authority"]}


def decode_state(aggregate: str, raw: Mapping[str, object]) -> ExecutionState:
    try:
        record = raw.get("candidate")
        candidate = None if record is None else CandidateRef(
            CandidateKind(str(record["kind"])), str(record["identity"]), str(record["content_digest"]),
            str(record["locator"]), str(record["provenance"]), bool(record["independent_read_back_proven"]))
        if type(raw["version"]) is not int or not isinstance(raw["closure"], list):
            raise TypeError("version/closure")
        return ExecutionState(LifecycleStage(str(raw["stage"])), raw["version"], candidate, bool(raw["accepted"]),
                              frozenset(raw["closure"]), None)
    except (KeyError, TypeError, ValueError) as error:
        raise _hold(HoldReason.MALFORMED_RECORD, aggregate, detail="execution state") from error


def accepts(state: ExecutionState, action: str) -> bool:
    """Probe the existing lifecycle on the pure value; nothing is committed."""
    try:
        transition(state, state.version, action, candidate=_WITNESS_CANDIDATE, verdict=_WITNESS_VERDICT,
                   completed_closure_actions=state.completed_closure_actions)
    except LifecycleError:
        return False
    return True


def _matches(work_ref: str, identity: str) -> bool:
    return work_ref in {identity, "factory:" + identity}


def derive(manifest: Mapping[str, object], records: Mapping[str, Mapping[str, object]],
           attention: Iterable[dict[str, object]]) -> dict[str, object]:
    """Apply LABELLED_DERIVATION_RULE_v1 to validated, pinned records."""
    decisions = decode_decision_inbox(records.get("decision-inbox", {}))
    pending = sorted((a for a in attention if a["status"] != "RESOLVED"), key=lambda a: a["identity"])
    identities = sorted({aggregate.split(":", 1)[1] for aggregate in records
                         if aggregate.startswith(("factory:", "release:"))})
    actions, blocked, current, lifecycle = [], [], [], {}
    for identity in identities:
        raw = records.get("factory:" + identity, {})
        state = decode_state("factory:" + identity, raw) if raw else ExecutionState()
        outcome = raw.get("outcome") if isinstance(raw.get("outcome"), str) else None
        release = records.get("release:" + identity, {})
        lifecycle[identity] = {"stage": state.stage.value, "version": state.version, "accepted": state.accepted,
                               "outcome": outcome, "released": release.get("source") if release else None}
        if state.stage is LifecycleStage.DONE or outcome in TERMINAL_OUTCOMES:
            continue
        current.append({"work": identity, "stage": state.stage.value, "version": state.version, "outcome": outcome,
                        "candidate": None if state.candidate is None else state.candidate.identity})
        reasons = [{"code": "AUTHORITY_BLOCK", "ref": "factory:" + identity}] if outcome in AUTHORITY_OUTCOMES else []
        reasons += [{"code": "OPEN_DECISION", "ref": "decision-inbox:" + identity}
                    for d in decisions if d["work_item"] == identity]
        reasons += [{"code": "PENDING_ATTENTION:" + a["status"], "ref": a["identity"]}
                    for a in pending if _matches(a["work_ref"], identity)]
        if reasons:
            blocked.append({"work": identity, "reasons": sorted(reasons, key=canonical)})
            continue
        for action in LIFECYCLE_ACTIONS:
            if accepts(state, action):
                actions.append({"work": identity, "action": action, "from_stage": state.stage.value,
                                "expected_version": state.version})
    return {
        "authorized_next_action_set": sorted(actions, key=canonical),
        "blocked_set": sorted(blocked, key=canonical),
        "current_work": sorted(current, key=canonical),
        "unresolved_decisions": list(decisions),
        "pending_attention": pending,
        "evidence_refs": list(manifest["evidence"]),
        "lifecycle": lifecycle,
    }


def compare(documents: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    """Equality of canonical documents; any differing field is a failure, not a started process."""
    labels = sorted(documents)
    first = documents[labels[0]]
    rest = [documents[label] for label in labels[1:]]
    differing = sorted(f for f in FIELDS if any(canonical(d.get(f)) != canonical(first.get(f)) for d in rest))
    return {"verdict": "MISMATCH" if differing else "EQUAL", "differing_fields": differing,
            "digests": {label: digest(documents[label]) for label in labels}}
