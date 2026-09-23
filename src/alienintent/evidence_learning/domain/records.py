"""Version-1 immutable discriminated records with canonical JSON scalar values."""
from dataclasses import asdict, dataclass
from enum import StrEnum
from hashlib import sha256
import json
import math
from typing import TypeAlias

from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.execution_coordination.ports.operational_store import SchemaIncompatible


class Kind(StrEnum):
    DEFINITION = "Definition"
    OBSERVATION = "Observation"
    VERDICT = "Verdict"


class Outcome(StrEnum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    UNVERIFIED = "UNVERIFIED"


def _immutable_refs(values: tuple[Ref, ...]) -> tuple[Ref, ...]:
    if not isinstance(values, (tuple, list)) or any(not isinstance(r, Ref) for r in values):
        raise EvidenceHold("INVALID_LINKS")
    return tuple(values)


@dataclass(frozen=True)
class Header:
    project: str
    profile: str
    logical_id: str
    revision: str
    source_refs: tuple[Ref, ...]
    access_label: str = "private"
    preceding_refs: tuple[Ref, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_refs", _immutable_refs(self.source_refs))
        object.__setattr__(self, "preceding_refs", _immutable_refs(self.preceding_refs))


@dataclass(frozen=True)
class Definition:
    header: Header
    issuer: str
    authority_ref: Ref
    required_ids: frozenset[str]

    def __post_init__(self) -> None:
        if not isinstance(self.required_ids, (set, frozenset, tuple, list)) or any(not isinstance(v, str) for v in self.required_ids):
            raise EvidenceHold("INVALID_REQUIRED_IDS")
        object.__setattr__(self, "required_ids", frozenset(self.required_ids))


@dataclass(frozen=True)
class Observation:
    header: Header
    definition_ref: Ref
    evidence_id: str
    method: str
    input_refs: tuple[Ref, ...]
    value: str | int | float | bool | None
    uncertainty: str | None
    observer: str
    invocation_id: str
    raw_digest: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_refs", _immutable_refs(self.input_refs))
        if type(self.value) not in (str, int, float, bool, type(None)):
            raise EvidenceHold("INVALID_SCALAR")


@dataclass(frozen=True)
class Verdict:
    header: Header
    definition_ref: Ref
    observation_refs: tuple[Ref, ...]
    evaluator: str
    authority_ref: Ref
    policy_ref: Ref
    outcome: Outcome
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "observation_refs", _immutable_refs(self.observation_refs))


Record: TypeAlias = Definition | Observation | Verdict


def kind_of(record: Record) -> Kind:
    kinds = {Definition: Kind.DEFINITION, Observation: Kind.OBSERVATION, Verdict: Kind.VERDICT}
    if type(record) not in kinds:
        raise EvidenceHold("INVALID_KIND")
    return kinds[type(record)]


def canonical_bytes(document: object) -> bytes:
    try:
        return json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as error:
        raise EvidenceHold("INVALID_JSON") from error


def record_document(record: Record) -> dict:
    kind = kind_of(record)
    payload = asdict(record)
    header = payload.pop("header")
    if isinstance(record, Definition):
        payload["required_ids"] = sorted(record.required_ids)
    document = json.loads(canonical_bytes({"schema_version": 1, "kind": kind, "header": header, "payload": payload}))
    record_from_document(document)
    return document


def record_ref(record: Record) -> Ref:
    digest = sha256(canonical_bytes(record_document(record))).hexdigest()
    return Ref(record.header.project, record.header.profile, record.header.logical_id,
               "sha256:" + digest, "objects/" + digest)


def _keys(value: object, keys: set[str]) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise EvidenceHold("INVALID_RECORD_FIELDS")
    return value


def _text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceHold("INVALID_TEXT")
    return value


def ref_from_document(value: object) -> Ref:
    return Ref(**_keys(value, {"project", "profile", "logical_id", "revision_digest", "locator"}))


def _refs(value: object) -> tuple[Ref, ...]:
    if not isinstance(value, list):
        raise EvidenceHold("INVALID_LINKS")
    return tuple(ref_from_document(v) for v in value)


def record_from_document(value: object) -> Record:
    d = _keys(value, {"schema_version", "kind", "header", "payload"})
    if type(d["schema_version"]) is not int or d["schema_version"] != 1:
        raise SchemaIncompatible("evidence object requires schema_version=1")
    h = _keys(d["header"], {"project", "profile", "logical_id", "revision", "source_refs", "access_label", "preceding_refs"})
    header = Header(*(_text(h[k]) for k in ("project", "profile", "logical_id", "revision")),
                    _refs(h["source_refs"]), _text(h["access_label"]), _refs(h["preceding_refs"]))
    if not header.source_refs or header.access_label not in {"public", "private"}:
        raise EvidenceHold("INVALID_PROVENANCE_OR_ACCESS")
    p = d["payload"]
    if d["kind"] == Kind.DEFINITION:
        _keys(p, {"issuer", "authority_ref", "required_ids"})
        ids = p["required_ids"]
        if not isinstance(ids, list) or not ids or any(not isinstance(i, str) or not i.strip() for i in ids) or ids != sorted(set(ids)):
            raise EvidenceHold("INVALID_REQUIRED_IDS")
        return Definition(header, _text(p["issuer"]), ref_from_document(p["authority_ref"]), frozenset(ids))
    if d["kind"] == Kind.OBSERVATION:
        _keys(p, {"definition_ref", "evidence_id", "method", "input_refs", "value", "uncertainty", "observer", "invocation_id", "raw_digest"})
        scalar = p["value"]
        if type(scalar) not in (str, int, float, bool, type(None)) or (isinstance(scalar, float) and not math.isfinite(scalar)):
            raise EvidenceHold("INVALID_SCALAR")
        uncertainty = p["uncertainty"]
        if uncertainty is not None:
            _text(uncertainty)
        if scalar is None and uncertainty is None:
            raise EvidenceHold("UNKNOWN_WITHOUT_REASON")
        if p["raw_digest"] is not None:
            Ref(header.project, header.profile, header.logical_id, p["raw_digest"], "raw")
        return Observation(header, ref_from_document(p["definition_ref"]), _text(p["evidence_id"]),
                           _text(p["method"]), _refs(p["input_refs"]), scalar, uncertainty,
                           _text(p["observer"]), _text(p["invocation_id"]), p["raw_digest"])
    if d["kind"] == Kind.VERDICT:
        _keys(p, {"definition_ref", "observation_refs", "evaluator", "authority_ref", "policy_ref", "outcome", "reason"})
        try:
            outcome = Outcome(p["outcome"])
        except (ValueError, TypeError) as error:
            raise EvidenceHold("INVALID_OUTCOME") from error
        refs = _refs(p["observation_refs"])
        if not refs:
            raise EvidenceHold("MISSING_OBSERVATIONS")
        return Verdict(header, ref_from_document(p["definition_ref"]), refs, _text(p["evaluator"]),
                       ref_from_document(p["authority_ref"]), ref_from_document(p["policy_ref"]), outcome, _text(p["reason"]))
    raise EvidenceHold("INVALID_KIND")
