"""Admission consumes pinned authority values; it cannot author normative authority."""
from dataclasses import dataclass
from typing import Mapping

from alienintent.evidence_learning.domain.records import Definition, Kind, Observation, Record, Verdict, kind_of, record_document, record_ref
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref


@dataclass(frozen=True)
class DefinitionGrant:
    ref: Ref
    issuer: str
    authority_ref: Ref


@dataclass(frozen=True)
class SourceGrant:
    observer: str
    source_ref: Ref
    trusted: bool


@dataclass(frozen=True)
class EvaluatorGrant:
    evaluator: str
    authority_ref: Ref
    policy_ref: Ref


@dataclass(frozen=True)
class AuthoritySnapshot:
    definitions: tuple[DefinitionGrant, ...]
    sources: tuple[SourceGrant, ...]
    evaluators: tuple[EvaluatorGrant, ...]
    external_refs: frozenset[Ref]

    def __post_init__(self) -> None:
        object.__setattr__(self, "definitions", tuple(self.definitions))
        object.__setattr__(self, "sources", tuple(self.sources))
        object.__setattr__(self, "evaluators", tuple(self.evaluators))
        object.__setattr__(self, "external_refs", frozenset(self.external_refs))


@dataclass(frozen=True)
class Admissible:
    ref: Ref


def require_kind(record: Record, kind: Kind) -> None:
    if kind_of(record) != kind:
        raise EvidenceHold("LINK_KIND", (record_ref(record),))


def require_revision(actual: Ref, expected: Ref | None) -> None:
    if actual != expected:
        raise EvidenceHold("STALE_DEFINITION", (actual,))


def require_definition_authority(record: Definition, authority: AuthoritySnapshot) -> None:
    grant = DefinitionGrant(record_ref(record), record.issuer, record.authority_ref)
    if grant not in authority.definitions:
        raise EvidenceHold("DEFINITION_AUTHORITY", (grant.ref,), required_action="obtain exact versioned definition authorization from its issuer")


def require_evaluator(evaluator: str, authority_ref: Ref, policy_ref: Ref, authority: AuthoritySnapshot) -> None:
    if EvaluatorGrant(evaluator, authority_ref, policy_ref) not in authority.evaluators:
        raise EvidenceHold("EVALUATOR_AUTHORITY", (authority_ref, policy_ref))


def observation_trusted(record: Observation, authority: AuthoritySnapshot) -> bool:
    grants = [g for g in authority.sources if g.observer == record.observer and g.source_ref in record.header.source_refs]
    return bool(grants) and all(g.trusted is True for g in grants)


def validate(record: Record, authority: AuthoritySnapshot, records: Mapping[Ref, Record], current: Mapping[str, Ref]) -> Admissible:
    record_document(record)
    ref = record_ref(record)
    h = record.header
    def link(target: Ref, kind: Kind | None = None) -> Record:
        if (target.project, target.profile) != (h.project, h.profile):
            raise EvidenceHold("REF_SCOPE", (target,))
        if target not in records:
            raise EvidenceHold("MISSING_LINK", (target,))
        linked = records[target]
        if kind is not None:
            require_kind(linked, kind)
        return linked
    for target in h.source_refs:
        if target not in authority.external_refs:
            link(target)
    for target in h.preceding_refs:
        previous = link(target, kind_of(record))
        if previous.header.logical_id != h.logical_id:
            raise EvidenceHold("PREDECESSOR_IDENTITY", (target,))
    if isinstance(record, Definition):
        require_definition_authority(record, authority)
        previous = current.get(h.logical_id)
        if previous is not None and previous != ref and previous not in h.preceding_refs:
            raise EvidenceHold("DEFINITION_REVISION_CONFLICT", (previous, ref))
    else:
        definition = link(record.definition_ref, Kind.DEFINITION)
        if isinstance(definition, Definition):
            require_revision(record.definition_ref, current.get(definition.header.logical_id))
        if isinstance(record, Observation):
            for target in record.input_refs:
                if target not in authority.external_refs:
                    link(target)
            if not any(g.observer == record.observer and g.source_ref in h.source_refs for g in authority.sources):
                raise EvidenceHold("SOURCE_ATTRIBUTION", (ref,))
        elif isinstance(record, Verdict):
            require_evaluator(record.evaluator, record.authority_ref, record.policy_ref, authority)
            for target in record.observation_refs:
                observed = link(target, Kind.OBSERVATION)
                if isinstance(observed, Observation):
                    require_revision(observed.definition_ref, record.definition_ref)
    return Admissible(ref)
