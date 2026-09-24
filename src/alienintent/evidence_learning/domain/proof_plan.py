"""Pre-implementation proof plans derived from authority-reviewed predicate mappings.

A plan is derived from a requirement revision, a candidate design revision and a mapping; it
never reads implementation code. Coverage, attribution and repair gaps are typed holds; an
infeasible platform premise is the U3 InfeasibleProof, returned to source authority.
"""
from dataclasses import asdict, dataclass
from enum import StrEnum
from hashlib import sha256
from pathlib import PurePosixPath
from typing import Callable

from alienintent.evidence_learning.domain.premise import InfeasibleProof, PlatformIsolationPremise
from alienintent.evidence_learning.domain.records import canonical_bytes
from alienintent.evidence_learning.domain.refs import Ref

FEASIBLE_PLAN = "FEASIBLE_PLAN"
RETURN_TO_MAPPING_AUTHORITY = "correct the predicate mapping through its reviewing authority"


class PredicateKind(StrEnum):
    MECHANICAL = "MECHANICAL"
    JUDGMENT = "JUDGMENT"
    PLATFORM_ISOLATION = "PLATFORM_ISOLATION"


@dataclass(frozen=True)
class RequirementRevision:
    """The authorized requirement revision is ``ref.revision_digest``."""
    requirement_id: str
    acceptance_ids: tuple[str, ...]
    ref: Ref


@dataclass(frozen=True)
class MappedPredicate:
    acceptance_id: str
    predicate_key: str
    kind: PredicateKind
    statement: str
    derived_from: tuple[str, ...]
    fixture: str = ""
    inputs: tuple[str, ...] = ()
    expected: str = ""
    endpoint: str = ""
    command: str = ""
    evidence_schema: tuple[str, ...] = ()
    guard: str = ""
    reviewer: str = ""
    inspection_inputs: tuple[str, ...] = ()
    decision_record: str = ""
    premise_id: str = ""
    premise_observables: tuple[str, ...] = ()


@dataclass(frozen=True)
class Supersession:
    prior_obligation_id: str
    replacement_obligation_id: str
    authorized_by: str
    authority_ref: Ref
    reason: str


@dataclass(frozen=True)
class PredicateMapping:
    mapping_ref: Ref
    requirement_id: str
    requirement_revision: str
    design_revision: str
    reviewer: str
    review_ref: Ref
    predicates: tuple[MappedPredicate, ...]
    supersessions: tuple[Supersession, ...] = ()


@dataclass(frozen=True)
class Obligation:
    obligation_id: str
    revision: str
    requirement_revision: str
    predicate: MappedPredicate
    premise_refs: tuple[Ref, ...] = ()


@dataclass(frozen=True)
class ProofPlan:
    requirement_ref: Ref
    design_ref: Ref
    mapping_ref: Ref
    obligations: tuple[Obligation, ...]
    superseded: tuple[Supersession, ...] = ()
    prior_plan_digest: str | None = None
    state: str = FEASIBLE_PLAN

    @property
    def requirement_id(self) -> str:
        return self.requirement_ref.logical_id

    @property
    def premise_refs(self) -> tuple[Ref, ...]:
        return tuple(dict.fromkeys(r for o in self.obligations for r in o.premise_refs))

    def obligation(self, obligation_id: str) -> Obligation | None:
        return next((o for o in self.obligations if o.obligation_id == obligation_id), None)

    @property
    def digest(self) -> str:
        return "sha256:" + sha256(canonical_bytes(plan_document(self))).hexdigest()


@dataclass(frozen=True)
class PlanHold:
    reason_code: str
    affected: tuple[str, ...]
    evidence_refs: tuple[Ref, ...] = ()
    required_action: str = RETURN_TO_MAPPING_AUTHORITY


PremiseReader = Callable[[str, frozenset[str]], PlatformIsolationPremise | InfeasibleProof]

_MECHANICAL_FIELDS = ("statement", "fixture", "inputs", "expected", "endpoint", "command", "evidence_schema", "guard")
_JUDGMENT_FIELDS = ("statement", "reviewer", "inspection_inputs", "decision_record")


def obligation_id(requirement_id: str, predicate: MappedPredicate) -> str:
    return f"{requirement_id}/{predicate.acceptance_id}/{predicate.predicate_key}"


def predicate_document(predicate: MappedPredicate) -> dict:
    document = asdict(predicate)
    document["premise_observables"] = sorted(predicate.premise_observables)  # A set of observables.
    return document


def obligation_revision(predicate: MappedPredicate) -> str:
    """Hash of every predicate and expected-result input; reviewer inputs are part of it."""
    return "sha256:" + sha256(canonical_bytes(predicate_document(predicate))).hexdigest()


def plan_document(plan: ProofPlan) -> dict:
    return {"schema_version": 1, "state": plan.state, "requirement_ref": asdict(plan.requirement_ref),
            "design_ref": asdict(plan.design_ref), "mapping_ref": asdict(plan.mapping_ref),
            "obligations": [{"obligation_id": o.obligation_id, "revision": o.revision,
                             "requirement_revision": o.requirement_revision,
                             "predicate": predicate_document(o.predicate),
                             "premise_refs": [asdict(r) for r in o.premise_refs]} for o in plan.obligations],
            "superseded": [{**asdict(s), "authority_ref": asdict(s.authority_ref)} for s in plan.superseded],
            "prior_plan_digest": plan.prior_plan_digest}


def _blank(value: object) -> bool:
    return not isinstance(value, str) or not value.strip()


def _missing(predicate: MappedPredicate, fields: tuple[str, ...]) -> list[str]:
    """A field is missing when blank; a list field is missing when empty or when any item is blank."""
    missing = []
    for name in fields:
        value = getattr(predicate, name)
        if isinstance(value, tuple) and value and not any(_blank(v) for v in value):
            continue
        if not isinstance(value, tuple) and not _blank(value):
            continue
        missing.append(name)
    return missing


def _implementation_derived(source: object, roots: tuple[str, ...]) -> bool:
    """A source must be a repository-relative authority path outside every implementation root.

    Blank, absolute, escaping and locator-prefixed forms are normalized or refused, so
    ``repository:src/x.py``, ``docs/../src/x.py`` or ``SRC/x.py`` cannot disguise code as authority.
    """
    if _blank(source):
        return True
    path = source.split("#", 1)[0].strip()
    if path.startswith("repository:"):
        path = path[len("repository:"):]
    if not path or "\\" in path or "\x00" in path or ":" in path or PurePosixPath(path).is_absolute():
        return True
    parts: list[str] = []
    for part in PurePosixPath(path).parts:
        if part == "..":
            if not parts:
                return True  # Escapes the repository: not an authority source.
            parts.pop()
        elif part != ".":
            parts.append(part)
    return not parts or parts[0].casefold() in {r.strip("/").casefold() for r in roots}


def derive_plan(requirement: RequirementRevision, design_ref: Ref, mapping: PredicateMapping | PlanHold | None,
                premise_reader: PremiseReader | None, prior: ProofPlan | None, mapping_reviewer: str,
                supersession_authority: str, implementation_roots: tuple[str, ...]
                ) -> ProofPlan | PlanHold | InfeasibleProof:
    if isinstance(mapping, PlanHold):
        return mapping
    if mapping is None:
        return PlanHold("MAPPING_UNAVAILABLE", ("predicate-mapping",))
    refs = (mapping.mapping_ref, mapping.review_ref)
    rid = requirement.requirement_id
    if requirement.ref.logical_id != rid:
        return PlanHold("REVISION_MISMATCH", (requirement.ref.logical_id,), refs)
    if not requirement.acceptance_ids or not mapping.predicates:
        return PlanHold("COVERAGE_HOLD", tuple(requirement.acceptance_ids) or (rid,), refs)
    if mapping.requirement_id != rid or mapping.requirement_revision != requirement.ref.revision_digest:
        return PlanHold("REVISION_MISMATCH", (mapping.requirement_id, mapping.requirement_revision), refs)
    if mapping.design_revision != design_ref.revision_digest:
        return PlanHold("DESIGN_MISMATCH", (mapping.design_revision,), refs)
    if not mapping_reviewer or mapping.reviewer != mapping_reviewer:
        return PlanHold("UNREVIEWED_MAPPING", (mapping.reviewer,), refs)
    circular = [obligation_id(rid, p) for p in mapping.predicates
                if not p.derived_from or any(_implementation_derived(s, implementation_roots) for s in p.derived_from)]
    if circular:
        return PlanHold("CIRCULAR_ORACLE", tuple(circular), refs)
    unknown = sorted({p.acceptance_id for p in mapping.predicates} - set(requirement.acceptance_ids))
    if unknown:
        return PlanHold("UNKNOWN_ACCEPTANCE", tuple(unknown), refs)
    ids = [obligation_id(rid, p) for p in mapping.predicates]
    duplicated = sorted({i for i in ids if ids.count(i) > 1})
    if duplicated:
        return PlanHold("DUPLICATE_OBLIGATION", tuple(duplicated), refs)
    incomplete, unattributed, claims_pass = [], [], []
    for predicate in mapping.predicates:
        oid = obligation_id(rid, predicate)
        if predicate.kind is PredicateKind.JUDGMENT:
            if _missing(predicate, _JUDGMENT_FIELDS):
                unattributed.append(oid)
            if predicate.command.strip() or predicate.expected.strip():
                claims_pass.append(oid)
        else:
            gaps = _missing(predicate, _MECHANICAL_FIELDS)
            if predicate.kind is PredicateKind.PLATFORM_ISOLATION:
                gaps += _missing(predicate, ("premise_id", "premise_observables"))
            if gaps:
                incomplete.append(oid + ":" + ",".join(gaps))
    if incomplete:
        return PlanHold("INCOMPLETE_OBLIGATION", tuple(incomplete), refs)
    if unattributed:
        return PlanHold("UNATTRIBUTED_JUDGMENT", tuple(unattributed), refs)
    if claims_pass:
        return PlanHold("JUDGMENT_CLAIMS_MECHANICAL_PASS", tuple(claims_pass), refs)
    uncovered = sorted(set(requirement.acceptance_ids) - {p.acceptance_id for p in mapping.predicates})
    if uncovered:
        return PlanHold("COVERAGE_HOLD", tuple(uncovered), refs)
    revisions = {obligation_id(rid, p): obligation_revision(p) for p in mapping.predicates}
    superseded = []
    for supersession in mapping.supersessions:
        if (supersession.authorized_by != supersession_authority or not supersession_authority
                or supersession.replacement_obligation_id not in revisions):
            return PlanHold("UNAUTHORIZED_SUPERSESSION", (supersession.prior_obligation_id,), refs)
        superseded.append(supersession)
    # A superseded obligation must be gone: a live one is replayed, never exempted by a supersession.
    live = [s.prior_obligation_id for s in (*(prior.superseded if prior is not None else ()), *superseded)
            if s.prior_obligation_id in revisions or s.prior_obligation_id == s.replacement_obligation_id]
    if live:
        return PlanHold("INVALID_SUPERSESSION", tuple(dict.fromkeys(live)), refs)
    if prior is not None:
        if prior.requirement_id != rid:
            return PlanHold("REVISION_MISMATCH", (prior.requirement_id,), refs)
        replaced = {s.prior_obligation_id for s in superseded}
        changed = [o.obligation_id for o in prior.obligations if o.obligation_id not in replaced
                   and o.obligation_id in revisions and revisions[o.obligation_id] != o.revision]
        if changed:
            return PlanHold("PRIOR_OBLIGATION_CHANGED", tuple(changed), refs)
        dropped = [o.obligation_id for o in prior.obligations
                   if o.obligation_id not in replaced and o.obligation_id not in revisions]
        if dropped:
            return PlanHold("PRIOR_OBLIGATION_DROPPED", tuple(dropped), refs)
        # Earlier authorized supersessions remain part of the preserved history.
        superseded = list(dict.fromkeys((*prior.superseded, *superseded)))
    obligations = []
    for predicate in mapping.predicates:
        premise_refs: tuple[Ref, ...] = ()
        if predicate.kind is PredicateKind.PLATFORM_ISOLATION:
            if premise_reader is None:
                return PlanHold("PREMISE_EVIDENCE_UNAVAILABLE", (obligation_id(rid, predicate),), refs)
            premise = premise_reader(predicate.premise_id, frozenset(predicate.premise_observables))
            if isinstance(premise, InfeasibleProof):
                return premise
            premise_refs = tuple(dict.fromkeys((premise.mapping_ref, premise.doctor_ref,
                                                *(o.source_ref for o in premise.observations))))
        obligations.append(Obligation(obligation_id(rid, predicate), revisions[obligation_id(rid, predicate)],
                                      requirement.ref.revision_digest, predicate, premise_refs))
    return ProofPlan(requirement.ref, design_ref, mapping.mapping_ref, tuple(obligations), tuple(superseded),
                     prior.digest if prior is not None else None)


def _ref(value: object) -> Ref:
    if not isinstance(value, dict) or set(value) != {"project", "profile", "logical_id", "revision_digest", "locator"}:
        raise ValueError("invalid ref")
    return Ref(**value)


def _predicate(value: object) -> MappedPredicate:
    fields = MappedPredicate.__dataclass_fields__
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError("invalid predicate")
    values = {k: tuple(v) if isinstance(v, list) else v for k, v in value.items()}
    if any(not isinstance(v, str) for k, v in values.items() if not isinstance(v, tuple)) or any(
            not all(isinstance(i, str) for i in v) for v in values.values() if isinstance(v, tuple)):
        raise ValueError("invalid predicate field")
    return MappedPredicate(**{**values, "kind": PredicateKind(values["kind"])})


def plan_from_document(document: object) -> ProofPlan:
    """Rebuild a persisted plan; any deviation raises ValueError, which callers treat as a hold."""
    keys = {"schema_version", "state", "requirement_ref", "design_ref", "mapping_ref", "obligations",
            "superseded", "prior_plan_digest"}
    if not isinstance(document, dict) or set(document) != keys or document["schema_version"] != 1 \
            or document["state"] != FEASIBLE_PLAN or not isinstance(document["obligations"], list) \
            or not isinstance(document["superseded"], list):
        raise ValueError("invalid plan document")
    obligations = []
    for entry in document["obligations"]:
        if not isinstance(entry, dict) or set(entry) != {"obligation_id", "revision", "requirement_revision",
                                                         "predicate", "premise_refs"} \
                or not isinstance(entry["premise_refs"], list):
            raise ValueError("invalid obligation")
        predicate = _predicate(entry["predicate"])
        if entry["revision"] != obligation_revision(predicate):
            raise ValueError("obligation revision does not match its predicate")
        obligations.append(Obligation(entry["obligation_id"], entry["revision"], entry["requirement_revision"],
                                      predicate, tuple(_ref(r) for r in entry["premise_refs"])))
    superseded = []
    for entry in document["superseded"]:
        if not isinstance(entry, dict) or set(entry) != set(Supersession.__dataclass_fields__):
            raise ValueError("invalid supersession")
        superseded.append(Supersession(**{**entry, "authority_ref": _ref(entry["authority_ref"])}))
    prior = document["prior_plan_digest"]
    if prior is not None and not isinstance(prior, str):
        raise ValueError("invalid prior plan digest")
    return ProofPlan(_ref(document["requirement_ref"]), _ref(document["design_ref"]), _ref(document["mapping_ref"]),
                     tuple(obligations), tuple(superseded), prior)
