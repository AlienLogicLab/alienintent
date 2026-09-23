"""Translate admitted neutral records into the existing execution acceptance policy."""
from typing import Callable

from alienintent.evidence_learning.domain.admission import AuthoritySnapshot, observation_trusted, require_evaluator, require_kind, require_revision, validate
from alienintent.evidence_learning.domain.catalog import Catalog
from alienintent.evidence_learning.domain.records import Header, Kind, Outcome, Verdict
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceCatalog, VerdictAdmission
from alienintent.execution_coordination.domain.verdict import EvidenceDefinition, Observation, Verdict as PolicyVerdict, VerdictKind
from alienintent.execution_coordination.ports.evidence_verdict import ExecutionVerdict


class EvidenceVerdictBridge(ExecutionVerdict, VerdictAdmission):
    def __init__(self, catalog: EvidenceCatalog, authority: AuthoritySnapshot, policy_ref: Ref, policy: Callable[..., PolicyVerdict]) -> None:
        self.catalog, self.authority, self.policy_ref, self.policy = catalog, authority, policy_ref, policy

    def evaluate(self, *, header: Header, definition_ref: Ref, observation_refs: tuple[Ref, ...],
                 evaluator: str, authority_ref: Ref, policy_ref: Ref, worker_claimed_success: bool = False) -> Verdict:
        return self._evaluate(self.catalog.read(), header=header, definition_ref=definition_ref, observation_refs=observation_refs,
                              evaluator=evaluator, authority_ref=authority_ref, policy_ref=policy_ref, worker_claimed_success=worker_claimed_success)

    def check(self, record: Verdict, catalog: Catalog) -> None:
        expected = self._evaluate(catalog, header=record.header, definition_ref=record.definition_ref,
                                  observation_refs=record.observation_refs, evaluator=record.evaluator,
                                  authority_ref=record.authority_ref, policy_ref=record.policy_ref)
        if record.outcome not in (Outcome.UNVERIFIED, expected.outcome):
            raise EvidenceHold("VERDICT_POLICY_MISMATCH", (record.definition_ref,), record.observation_refs)

    def _evaluate(self, state: Catalog, *, header: Header, definition_ref: Ref, observation_refs: tuple[Ref, ...],
                  evaluator: str, authority_ref: Ref, policy_ref: Ref, worker_claimed_success: bool = False) -> Verdict:
        require_evaluator(evaluator, authority_ref, policy_ref, self.authority)
        if policy_ref != self.policy_ref:
            raise EvidenceHold("POLICY_REVISION", (policy_ref,))
        records = dict(zip(state.refs, state.records))
        if definition_ref not in records:
            raise EvidenceHold("MISSING_LINK", (definition_ref,))
        definition = records[definition_ref]
        require_kind(definition, Kind.DEFINITION)
        require_revision(definition_ref, state.current_definitions().get(definition.header.logical_id))
        if definition_ref in state.held_definitions:
            raise EvidenceHold("CONFLICTING_OBSERVATIONS", (definition_ref,), state.refs,
                               "retain competing evidence; obtain policy/authority disposition before acceptance")
        # Validate all evaluator/revision/role links before calling execution policy.
        provisional = Verdict(header, definition_ref, observation_refs, evaluator, authority_ref, policy_ref, Outcome.UNVERIFIED, "pending evaluation")
        validate(provisional, self.authority, records, state.current_definitions())
        observations = tuple(Observation(records[ref].evidence_id,
                                         observation_trusted(records[ref], self.authority),
                                         records[ref].value is True and records[ref].uncertainty is None)
                             for ref in observation_refs)
        result = self.policy(EvidenceDefinition(definition.required_ids), observations,
                             worker_claimed_success=worker_claimed_success)
        outcome = Outcome.ACCEPT if result.kind == VerdictKind.ACCEPT else Outcome.REJECT
        return Verdict(header, definition_ref, observation_refs, evaluator, authority_ref, policy_ref, outcome, result.reason)
