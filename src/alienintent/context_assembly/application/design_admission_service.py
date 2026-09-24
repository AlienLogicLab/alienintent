"""Persist design admission over the shared store and evidence; readiness consumes only a current verdict.

No Project lifecycle state or transition is read or written here: MECHANICALLY_HELD, REVIEW_REQUIRED,
VERIFIED and STALE are internal SWF-25 gate states of one upstream:design aggregate per design key.
"""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from alienintent.context_assembly.domain.design_admission import (
    MECHANICALLY_HELD, REJECTED, REVIEW_REQUIRED, STALE, VERIFIED, CurrentVerified, DesignContract, DesignInvalid,
    Held, MechanicalReport, ReviewAdmitted, ReviewRefused, Stale, admit_review, applicability, canonical,
    design_from_document, inspect_design, report_from_document, review_from_document)
from alienintent.context_assembly.ports.design_admission import ArchitectureChecks, DirectionAuthoritySource, PremiseCheck
from alienintent.evidence_learning.domain.records import Header, Observation, ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.ports.operational_store import OperationalStore, VersionConflict

DESIGN_EVIDENCE = "design.revision"
EVENTS = {MECHANICALLY_HELD: "design.mechanical_held", REVIEW_REQUIRED: "design.review_required",
          VERIFIED: "design.verified", REJECTED: "design.review_rejected", STALE: "design.stale",
          "REFUSED": "design.review_refused"}
_STATE_KEYS = {"schema_version", "design_key", "status", "design_ref", "report_ref", "report_digest", "review_digest",
               "last_review", "history"}


class DesignStateInvalid(Exception):
    pass


class DesignAdmission:
    """DesignAdmission.inspect / record_review and DesignApplicability.check for one store/profile."""

    def __init__(self, repository: EvidenceRepository, store: OperationalStore, project: str, profile: str,
                 definition_ref: Ref, invocation: str, access_scope: frozenset[str],
                 architecture: ArchitectureChecks | None, premises: PremiseCheck | None,
                 authority: DirectionAuthoritySource | None, reviewers: frozenset[str]) -> None:
        self.repository, self.store, self.project, self.profile = repository, store, project, profile
        self.definition_ref, self.invocation, self.access_scope = definition_ref, invocation, access_scope
        self.architecture, self.premises, self.authority = architecture, premises, authority
        self.reviewers = frozenset(reviewers)

    @staticmethod
    def aggregate(design_key: str) -> str:
        return "upstream:design:" + design_key

    def read(self, design_key: str) -> tuple[int, dict]:
        version, state = self.store.read_state(self.profile, self.aggregate(design_key))
        if (version, state) != (0, {}) and not self._valid(design_key, version, state):
            raise DesignStateInvalid("INCOMPATIBLE_DESIGN_STATE")
        return version, state

    def _valid(self, design_key: str, version: int, state: object) -> bool:
        """Exactly one retained event per committed version, each chained to the event before it."""
        if not isinstance(state, dict) or set(state) != _STATE_KEYS or state["schema_version"] != 1 \
                or state["design_key"] != design_key or not isinstance(state["history"], list) \
                or len(state["history"]) != version \
                or state["status"] not in (MECHANICALLY_HELD, REVIEW_REQUIRED, VERIFIED, STALE):
            return False
        previous = None
        for event in state["history"]:
            try:
                ref = ref_from_document(event["ref"])
                record = self.repository.get(ref, self.access_scope)
            except (EvidenceHold, KeyError, TypeError, ValueError):
                return False
            if not isinstance(record, Observation) or record.evidence_id != event["event"] \
                    or record.header.preceding_refs != ((previous,) if previous else ()):
                return False
            previous = ref
        return True

    def history(self, design_key: str) -> tuple[tuple[str, Ref], ...] | Held:
        try:
            _, state = self.read(design_key)
        except DesignStateInvalid as error:
            return Held(str(error), (design_key,))
        return tuple((e["event"], ref_from_document(e["ref"])) for e in state.get("history", []))

    def retained(self, ref: Ref) -> dict:
        record = self.repository.get(ref, self.access_scope)
        if not isinstance(record, Observation):
            raise EvidenceHold("NOT_DESIGN_EVIDENCE", (ref,))
        return json.loads(record.value)

    def inspect(self, document: object, expected_version: int) -> MechanicalReport | Held:
        try:
            design = design_from_document(document)
        except DesignInvalid as error:
            return Held("INVALID_DESIGN", (str(error),))
        try:
            version, state = self.read(design.design_key)
        except DesignStateInvalid as error:
            return Held(str(error), (design.design_key,))
        if version != expected_version:
            return Held("STALE_INPUT", (design.design_key,))
        # Existing approved checks first; no store transaction is held across them.
        architecture = self.architecture.run() if self.architecture is not None else None
        authority = self.authority.read() if self.authority is not None else None
        premises = (tuple(self.premises.check(p["premise_id"], frozenset(p["requested"])) for p in design.premises)
                    if self.premises is not None else None)
        report = inspect_design(design, architecture, authority, premises)
        if state and state["status"] != STALE and state["report_digest"] == report.digest:
            return report  # The identical design and inputs were already inspected.
        previous = self._previous(state)
        design_ref = self._put(DESIGN_EVIDENCE, "design/" + design.design_key, design.document, ())
        event = EVENTS[report.status]
        ref = self._put(event, "design-event/" + design.design_key,
                        {"report": asdict(report), "design_ref": asdict(design_ref)},
                        (previous,) if previous else (), (design_ref,))
        committed = self._commit(design.design_key, version, state, event, ref, status=report.status,
                                 design_ref=asdict(design_ref), report_ref=asdict(ref), report_digest=report.digest,
                                 review_digest=None, last_review=None)
        return committed if isinstance(committed, Held) else report

    def record_review(self, design_key: str, document: object, expected_version: int) -> ReviewAdmitted | ReviewRefused:
        try:
            version, state = self.read(design_key)
        except DesignStateInvalid as error:
            return ReviewRefused(str(error), (design_key,))
        if version != expected_version:
            return ReviewRefused("STALE_INPUT", (design_key,))
        review = review_from_document(document)
        if isinstance(review, ReviewRefused):
            return self._refused(design_key, version, state, review, document)
        current = self._current(state) if state else (None, None)
        if current is None:
            return ReviewRefused("PERSISTED_DESIGN_INVALID", (design_key,))
        if state and state["status"] == VERIFIED and state["review_digest"] == review.digest:
            return ReviewAdmitted(review, VERIFIED)  # Identical admitted review replayed at the same revision.
        result = admit_review(*current, review, self.reviewers)
        if isinstance(result, ReviewAdmitted) and state["status"] == STALE:
            # Invalidation lasts until re-inspection: a stale report is never re-verified in place.
            result = ReviewRefused("STALE_REVIEW", ("design-state",))
        elif isinstance(result, ReviewAdmitted) and result.decision == VERIFIED and state["last_review"] == REJECTED:
            # An attributed rejection of this revision stands until a repaired design is inspected.
            result = ReviewRefused("BLOCKING_FINDINGS", ("prior-rejection",))
        if isinstance(result, ReviewRefused):
            return self._refused(design_key, version, state, result, document)
        event = EVENTS[result.decision]
        previous = self._previous(state)
        ref = self._put(event, "design-event/" + design_key,
                        {"review": review.document, "review_digest": review.digest, "report_ref": state["report_ref"]},
                        (previous,) if previous else (), (ref_from_document(state["report_ref"]),))
        committed = self._commit(design_key, version, state, event, ref,
                                 status=VERIFIED if result.decision == VERIFIED else REVIEW_REQUIRED,
                                 review_digest=review.digest, last_review=result.decision)
        return ReviewRefused(committed.reason_code, committed.affected) if isinstance(committed, Held) else result

    def check(self, design_key: str, current_vector: dict) -> CurrentVerified | Held | Stale:
        """DesignApplicability.check: only the exact verified revision vector is current."""
        try:
            version, state = self.read(design_key)
        except DesignStateInvalid as error:
            return Held(str(error), (design_key,))
        current = self._current(state) if state else (None, None)
        if current is None:
            return Held("PERSISTED_DESIGN_INVALID", (design_key,))
        report = current[1]
        result = applicability(state.get("status"), report, state.get("review_digest"), state.get("last_review"),
                               current_vector)
        if isinstance(result, Stale) and state["status"] == VERIFIED:
            previous = self._previous(state)
            ref = self._put(EVENTS[STALE], "design-event/" + design_key,
                            {"changed": list(result.changed), "verified_vector": report.vector,
                             "current_vector": current_vector, "review_digest": state["review_digest"]},
                            (previous,), (ref_from_document(state["report_ref"]),))
            committed = self._commit(design_key, version, state, EVENTS[STALE], ref, status=STALE)
            if isinstance(committed, Held):
                return committed
        return result

    def _refused(self, design_key: str, version: int, state: dict, refusal: ReviewRefused,
                 document: object) -> ReviewRefused:
        """A refused review is retained as history and changes no applicability."""
        if not state:
            return refusal
        previous = self._previous(state)
        ref = self._put(EVENTS["REFUSED"], "design-event/" + design_key,
                        {"reason_code": refusal.reason_code, "affected": list(refusal.affected),
                         "submitted": document if isinstance(document, dict) else None},
                        (previous,), ())
        committed = self._commit(design_key, version, state, EVENTS["REFUSED"], ref)
        return ReviewRefused(committed.reason_code, committed.affected) if isinstance(committed, Held) else refusal

    def _current(self, state: dict) -> tuple[DesignContract, MechanicalReport] | None:
        """The current design and report, read back and digest-checked; unreadable evidence is None."""
        try:
            value = self.retained(ref_from_document(state["report_ref"]))
            report = report_from_document(value["report"])
            design = design_from_document(self.retained(ref_from_document(value["design_ref"])))
        except (EvidenceHold, DesignInvalid, KeyError, TypeError, ValueError):
            return None
        if report.digest != state["report_digest"] or design.digest != report.design_digest:
            return None
        return design, report

    @staticmethod
    def _previous(state: dict) -> Ref | None:
        return ref_from_document(state["history"][-1]["ref"]) if state else None

    def _commit(self, design_key: str, version: int, state: dict, event: str, ref: Ref, **fields) -> dict | Held:
        base = state or {"schema_version": 1, "design_key": design_key, "status": None, "design_ref": None,
                         "report_ref": None, "report_digest": None, "review_digest": None, "last_review": None,
                         "history": []}
        committed = {**base, **fields, "history": [*base["history"], {"event": event, "ref": asdict(ref)}]}
        try:
            self.store.commit(self.profile, self.aggregate(design_key), version, committed)
        except VersionConflict:
            return Held("STALE_INPUT", (design_key,))  # Never blindly retry a decision.
        return committed

    def _put(self, evidence_id: str, logical_id: str, body: dict, preceding: tuple[Ref, ...],
             inputs: tuple[Ref, ...] = ()) -> Ref:
        value = canonical(body)
        body_digest = sha256(value.encode()).hexdigest()
        record = Observation(Header(self.project, self.profile, logical_id, body_digest, (self.definition_ref,),
                                    "private", preceding), self.definition_ref, evidence_id, "design_admission/v1",
                             inputs, value, None, "design-admission", self.invocation, "sha256:" + body_digest)
        ref = self.repository.put(record)
        self.repository.get(ref, self.access_scope)  # Read back before any pointer can reference it.
        return ref


@dataclass(frozen=True)
class ReadinessDecision:
    admitted: bool
    reason_code: str
    applicability: CurrentVerified | Held | Stale


class DesignReadiness:
    """The design gate of readiness processing: it refuses, and never mutates a Project item."""

    def __init__(self, admission: DesignAdmission) -> None:
        self._admission = admission

    def admit(self, design_key: str, current_vector: dict) -> ReadinessDecision:
        result = self._admission.check(design_key, current_vector)
        admitted = isinstance(result, CurrentVerified)
        reason = "CURRENT_VERIFIED" if admitted else ("STALE" if isinstance(result, Stale) else result.reason_code)
        return ReadinessDecision(admitted, reason, result)
