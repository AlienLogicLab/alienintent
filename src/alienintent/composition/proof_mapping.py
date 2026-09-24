"""Composition-owned readers for the pinned predicate mapping and the specified requirement revision.

The mapping is authority-reviewed data read under a digest pin; nothing here inspects
implementation code. Unreadable or malformed input is a typed hold, never an exception.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from alienintent.composition.premise_evidence import _ABSENT, _json, _read_retained, _repository_path
from alienintent.evidence_learning.domain.proof_plan import (
    MappedPredicate, PlanHold, PredicateKind, PredicateMapping, RequirementRevision, Supersession)
from alienintent.evidence_learning.domain.records import canonical_bytes
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.evidence_learning.ports.proof_planning import PredicateMappingSource

_TEXT = ("acceptance_id", "predicate_key", "kind", "statement", "fixture", "expected", "endpoint", "command", "guard",
         "reviewer", "decision_record", "premise_id")
_LISTS = ("derived_from", "inputs", "evidence_schema", "inspection_inputs", "premise_observables")
_REQUIRED = {"acceptance_id", "predicate_key", "kind", "statement", "derived_from"}


def _digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _predicate(entry: object) -> MappedPredicate | None:
    if not isinstance(entry, dict) or not _REQUIRED <= set(entry) or not set(entry) <= set(_TEXT) | set(_LISTS):
        return None
    if any(not isinstance(entry.get(k, ""), str) for k in _TEXT):
        return None
    if any(not isinstance(entry.get(k, []), list) or not all(isinstance(i, str) for i in entry.get(k, [])) for k in _LISTS):
        return None
    if entry["kind"] not in {k.value for k in PredicateKind}:
        return None
    return MappedPredicate(**{k: tuple(v) if isinstance(v, list) else v for k, v in entry.items()}
                           | {"kind": PredicateKind(entry["kind"])})


class RetainedPredicateMapping(PredicateMappingSource):
    def __init__(self, repository_root: Path, mapping_path: Path, mapping_sha256: str, project: str, profile: str) -> None:
        if not all(isinstance(v, str) and v.strip() for v in (project, profile, mapping_sha256)):
            raise ValueError("project, profile and the pinned mapping sha256 must be configured")
        self._root, self._path, self._sha256 = Path(repository_root), str(mapping_path), mapping_sha256
        self._project, self._profile = project, profile

    def load(self, requirement_id: str) -> PredicateMapping | PlanHold:
        def unavailable(detail: str) -> PlanHold:
            return PlanHold("MAPPING_UNAVAILABLE", ("mapping:" + self._path, detail))

        body = _read_retained(self._root, self._path) if _repository_path(self._path) else None
        if body is None:
            return unavailable("unreadable")
        if sha256(body).hexdigest() != self._sha256:
            return unavailable("digest mismatch")
        document = _json(body)
        try:
            mapping_ref = Ref(self._project, self._profile, "proof-predicate-mapping:" + requirement_id,
                              "sha256:" + self._sha256, "repository:" + self._path)
            return self._mapping(document, mapping_ref, requirement_id) or unavailable("schema")
        except (EvidenceHold, KeyError, TypeError, ValueError):
            return unavailable("schema")

    def _mapping(self, document: object, mapping_ref: Ref, requirement_id: str) -> PredicateMapping | None:
        if document is _ABSENT or not isinstance(document, dict) or type(document.get("schema_version")) is not int \
                or document.get("schema_version") != 1 \
                or document.get("record_kind") != "ProofPredicateMapping":
            return None
        requirement, design, review = document.get("requirement"), document.get("design"), document.get("review")
        if not all(isinstance(v, dict) for v in (requirement, design, review)):
            return None
        # A mapping for another requirement is still read, so the domain reports REVISION_MISMATCH.
        if not all(isinstance(requirement.get(k), str) for k in ("requirement_id", "revision_digest")) \
                or not isinstance(review.get("reviewer"), str):
            return None
        if not _digest(design.get("sha256")) or not self._pinned(review):
            return None
        predicates = [_predicate(p) for p in document.get("predicates") or []]
        if not predicates or any(p is None for p in predicates) or not isinstance(document.get("supersessions"), list):
            return None
        supersessions = []
        for entry in document["supersessions"]:
            if not isinstance(entry, dict) or set(entry) != {"prior_obligation_id", "replacement_obligation_id",
                                                             "authorized_by", "authority", "reason"}:
                return None
            authority = entry["authority"]
            if not self._pinned(authority) or any(
                    not isinstance(entry[k], str) or not entry[k].strip()
                    for k in ("prior_obligation_id", "replacement_obligation_id", "authorized_by", "reason")):
                return None
            supersessions.append(Supersession(entry["prior_obligation_id"], entry["replacement_obligation_id"],
                                              entry["authorized_by"],
                                              Ref(self._project, self._profile, "supersession-authority",
                                                  "sha256:" + authority["sha256"], "repository:" + authority["path"]),
                                              entry["reason"]))
        review_ref = Ref(self._project, self._profile, "predicate-mapping-review", "sha256:" + review["sha256"],
                         "repository:" + review["path"])
        return PredicateMapping(mapping_ref, requirement["requirement_id"], requirement["revision_digest"],
                                "sha256:" + design["sha256"], review["reviewer"], review_ref, tuple(predicates),
                                tuple(supersessions))


    def _pinned(self, record: object) -> bool:
        """A cited authority record must exist in the repository with exactly the pinned digest."""
        if not isinstance(record, dict) or not _repository_path(record.get("path")) or not _digest(record.get("sha256")):
            return False
        body = _read_retained(self._root, record["path"])
        return body is not None and sha256(body).hexdigest() == record["sha256"]


def retained_requirement_revision(repository_root: Path, path: str, requirement_id: str, project: str,
                                  profile: str) -> RequirementRevision | None:
    """The revision is the sha256 of the requirement's canonical specification entry."""
    body = _read_retained(Path(repository_root), path) if _repository_path(path) else None
    document = _json(body) if body is not None else _ABSENT
    candidates = document.get("candidates") if isinstance(document, dict) else None
    found = [c for c in candidates if isinstance(c, dict) and c.get("requirement_id") == requirement_id] \
        if isinstance(candidates, list) else []
    if len(found) != 1 or not isinstance(found[0].get("acceptance_criteria"), list):
        return None
    try:
        ids = tuple(c["id"] for c in found[0]["acceptance_criteria"])
        digest = "sha256:" + sha256(canonical_bytes(found[0])).hexdigest()
        ref = Ref(project, profile, requirement_id, digest, f"repository:{path}#candidates[requirement_id={requirement_id}]")
    except (EvidenceHold, KeyError, TypeError):
        return None
    if not ids or any(not isinstance(i, str) or not i for i in ids):
        return None
    return RequirementRevision(requirement_id, ids, ref)


def retained_design_ref(repository_root: Path, path: str, requirement_id: str, project: str, profile: str) -> Ref | None:
    body = _read_retained(Path(repository_root), path) if _repository_path(path) else None
    if body is None:
        return None
    return Ref(project, profile, "design:" + requirement_id, "sha256:" + sha256(body).hexdigest(),
               f"repository:{path}#contracts[requirement_id={requirement_id}]")
