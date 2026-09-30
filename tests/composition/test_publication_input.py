"""PY-SELF-00: the assessed task text and contract bound to the latest applicable READY attempt.

Every case runs the FX-A chain (tests/composition/test_upstream_integration_capstone.py) over its real temporary
store, evidence repository and fixture producer, then asks UpstreamIntegration.publication_input for the snapshot.
A changed retained attempt is either produced through the real consumer (a newer attempt, a removed evidence object)
or, where no existing write can produce it, by altering one read of that real consumer. Nothing here needs GitHub,
a worker or a model.
"""
from copy import deepcopy
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass

import pytest

from alienintent.context_assembly.application.publication_input import (
    CHANGED, UNBOUND, AssessedPublicationInput, PinnedInput, pinned)
from alienintent.context_assembly.domain.compilation import contract_from_payload
from alienintent.context_assembly.domain.readiness import LintHold
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy
from alienintent.execution_coordination.domain.readiness import (
    ATTEMPT_FAILURE, NO_ASSESSMENT, AttemptMetadata, Hold, digest)
from alienintent.execution_coordination.ports.operational_store import StoreUnavailable
from tests.composition.test_upstream_integration_capstone import (
    DECISION, DECISIONS, PROFILE, PROJECT, SCOPE, U1, U2, Harness, ready, revise_decision)
from tests.context_assembly.test_initial_compilation import R1

OTHER = "sha256:" + "0" * 64


@pytest.fixture
def make(tmp_path):
    count = iter(range(100))
    return lambda **options: Harness(tmp_path / f"h{next(count)}", **options)


def unit(compiled, identity: str = U1) -> dict:
    return next(u for u in compiled.document()["units"] if u["identity"] == identity)


def bind(h: Harness, compiled, identity=U1):
    return h.integration.publication_input(compiled, identity, DECISIONS)


def refused(result, field: str, reason: str = UNBOUND) -> Hold:
    assert isinstance(result, Hold), result
    assert result.reason_code == reason and result.detail.startswith(field + ":"), result
    return result


class AlteredReads:
    """The real retained consumer with its latest or raw read altered; every other call is the consumer's own."""

    def __init__(self, consumer, latest=None, raw=None):
        self._consumer, self._latest, self._raw = consumer, latest, raw
        self.latest_reads = 0

    def __getattr__(self, name):
        return getattr(self._consumer, name)

    def latest(self, identity):
        self.latest_reads += 1
        entry = self._consumer.latest(identity)
        return self._latest(entry, self.latest_reads) if self._latest else entry

    def raw(self, identity, attempt_id):
        retained = self._consumer.raw(identity, attempt_id)
        return self._raw(retained) if self._raw else retained


def altered(h: Harness, **reads) -> AlteredReads:
    h.profile.readiness_consumer = AlteredReads(h.profile.readiness_consumer, **reads)
    return h.profile.readiness_consumer


def without(name: str):
    return lambda entry, _: {k: v for k, v in entry.items() if k != name}


def replaced(name: str, value):
    return lambda entry, _: {**entry, name: value}


# --- The bound snapshot ------------------------------------------------------------------------------------------


def test_latest_ready_attempt_binds_the_assessed_text_and_contract(make):
    h = make()
    compiled, candidate, plan, outcome = ready(h)
    before = h.outside()
    bound = bind(h, compiled)
    assert type(bound) is AssessedPublicationInput, bound
    latest = h.profile.readiness_consumer.latest(U1)
    assert (bound.identity, bound.text, bound.proof_plan) == (U1, candidate["text"], plan)
    assert bound.contract == contract_from_payload(unit(compiled)["contract"])
    assert bound.text_digest == digest(bound.text) == latest["input_sha256"]
    assert bound.contract.content_digest == outcome.contract_digest == latest["contract_digest"]
    assert (bound.attempt_id, bound.input_fingerprint) == (outcome.attempt_id, outcome.input_fingerprint)
    assert (bound.attempt_id, bound.input_fingerprint) == (latest["attempt_id"], latest["input_fingerprint"])
    assert asdict(bound.raw_ref) == latest["raw_ref"]
    assert bound.raw_ref.logical_id == f"readiness/{U1}/{bound.attempt_id}/raw"
    assert (bound.raw_ref.project, bound.raw_ref.profile) == (PROJECT, PROFILE)
    # The exact raw receipt is retrievable from the evidence repository by that reference.
    assert h.repository.get(bound.raw_ref, SCOPE).value == h.profile.readiness_consumer.raw(U1, bound.attempt_id)[1]
    # Nothing was reassessed, and nothing outside the upstream namespaces moved.
    assert len(h.producer.calls) == 1 and h.outside() == before


def test_unchanged_inputs_bind_the_same_value(make):
    h = make()
    compiled, *_ = ready(h)
    first = bind(h, compiled)
    assert type(first) is AssessedPublicationInput
    assert bind(h, compiled) == first
    assert h.profile.readiness_consumer.history(U1)[-1]["attempt_id"] == first.attempt_id


def test_bound_value_is_frozen(make):
    h = make()
    compiled, *_ = ready(h)
    bound = bind(h, compiled)
    with pytest.raises(FrozenInstanceError):
        bound.text = "rewritten"
    with pytest.raises(FrozenInstanceError):
        bound.contract.intent = "rewritten"


def members(value) -> list:
    """Every value reachable from a bound snapshot, through its frozen values and tuples."""
    if is_dataclass(value):
        assert value.__dataclass_params__.frozen, value
        return [value, *(m for f in fields(value) for m in members(getattr(value, f.name)))]
    return [value, *(m for v in value for m in members(v))] if type(value) is tuple else [value]


def test_bound_value_shares_nothing_mutable_with_the_compiled_candidate(make):
    h = make()
    compiled, *_ = ready(h)
    bound, before = bind(h, compiled), deepcopy(unit(compiled)["contract"])
    reachable = members(bound)
    assert {type(m) for m in reachable} <= {AssessedPublicationInput, BiuContract, BudgetPolicy, Ref, tuple, str,
                                            int, type(None)}, reachable
    digests = (bound.contract.content_digest, bound.text_digest)
    contract = unit(compiled)["contract"]  # Every mutable member of the source is rewritten in place.
    for value in contract.values():
        if isinstance(value, list):
            value.append("a later clause")
    contract["budget_policy"]["hard_required_dimensions"].append("a later dimension")
    contract["budget_policy"]["maximum_attempts"] += 1
    assert bound.contract == contract_from_payload(before) and bound.text_digest == digest(bound.text)
    assert (bound.contract.content_digest, bound.text_digest) == digests
    assert bound.contract != contract_from_payload(contract)


NOT_CONTRACT_VALUES = {
    "nested clause": ({"non_goals": [{"clause": "before"}]}, "non_goals"),
    "nested clause list": ({"completion_criteria": [["tests pass"]]}, "completion_criteria"),
    "numeric clause": ({"authorized_scope": [7]}, "authorized_scope"),
    "clauses as a mapping": ({"non_goals": {"clause": "before"}}, "non_goals"),
    "clauses as text": ({"baselines": "main@04cdd8c"}, "baselines"),
    "dependency mapping": ({"dependencies": [{"identity": "WO-000001"}]}, "dependencies"),
    "intent mapping": ({"intent": {"statement": "before"}}, "intent"),
    "policy list": ({"retry_policy": ["one replacement"]}, "retry_policy"),
    "numeric version": ({"version": 1}, "version"),
    "nested dimension": ({"budget_policy": {"hard_required_dimensions": [{"dimension": "attempts"}]}},
                         "budget_policy.hard_required_dimensions"),
    "boolean limit": ({"budget_policy": {"maximum_attempts": True}}, "budget_policy.maximum_attempts"),
    "fractional limit": ({"budget_policy": {"hard_wall_clock_seconds": 7200.5}},
                         "budget_policy.hard_wall_clock_seconds"),
}


@pytest.mark.parametrize("case", list(NOT_CONTRACT_VALUES))
def test_contract_value_that_is_not_its_declared_text_or_number_holds(make, case):
    """A nested value would stay mutable inside the frozen contract while its content digest stayed the same."""
    h = make()
    compiled, candidate, plan, _ = ready(h)
    changes, field = NOT_CONTRACT_VALUES[case]
    assert type(pinned(U1, deepcopy(candidate), plan)) is PinnedInput
    document = deepcopy(candidate["contract"])
    for name, value in changes.items():
        document[name] = {**document[name], **value} if name == "budget_policy" else value
    held = refused(pinned(U1, {**candidate, "contract": document}, plan), "contract")
    assert field + " is not" in held.detail
    # The same value in the compiled candidate is refused before any readiness read or retained record.
    unit(compiled)["contract"].update(deepcopy(document))
    records = len(h.evidence())
    assert field + " is not" in refused(bind(h, compiled), "contract").detail
    assert len(h.evidence()) == records


# --- Text only: the readiness fingerprint does not include the text ----------------------------------------------


def test_changed_text_with_unchanged_contract_and_fingerprint_holds(make):
    h = make()
    compiled, candidate, plan, outcome = ready(h)
    contract = deepcopy(unit(compiled)["contract"])
    unit(compiled)["unit_key"] += ":reworded"  # Task text only: the contract is untouched.
    changed = h.integration.candidate(compiled, U1, DECISIONS)
    assert changed["text"] != candidate["text"] and changed["contract"] == contract
    # Existing readiness still finds the retained READY applicable: only the text comparison can refuse this.
    assert h.integration.current(changed, plan) == outcome
    held = refused(bind(h, compiled), "text_digest")
    assert held.attempt_id == outcome.attempt_id
    assert digest(changed["text"]) in held.detail and digest(candidate["text"]) in held.detail


# --- Work identity, proof plan, text and contract ---------------------------------------------------------------


@pytest.mark.parametrize("identity", ["WO-999999", "", None])
def test_absent_work_identity_holds(make, identity):
    h = make()
    compiled, *_ = ready(h)
    refused(bind(h, compiled, identity), "identity")


def test_contract_of_another_identity_holds(make):
    h = make()
    compiled, *_ = ready(h)
    unit(compiled)["contract"]["identity"] = U2
    held = refused(bind(h, compiled), "identity")
    assert U1 in held.detail and U2 in held.detail


def test_contract_without_identity_holds_with_its_cause(make):
    h = make()
    compiled, *_ = ready(h)
    del unit(compiled)["contract"]["identity"]
    assert "identity is required" in refused(bind(h, compiled), "contract").detail


def test_malformed_contract_holds_with_its_cause(make):
    h = make()
    compiled, *_ = ready(h)
    unit(compiled)["contract"]["budget_policy"] = "unbounded"
    assert "budget_policy is required" in refused(bind(h, compiled), "contract").detail


def test_unreadable_compiled_document_holds_with_its_cause(make):
    h = make()
    compiled, *_ = ready(h)
    del compiled.document()["inputs"]
    assert "KeyError" in refused(bind(h, compiled), "compiled").detail


@pytest.mark.parametrize("plan", [None, "", 7])
def test_absent_or_malformed_proof_plan_holds(make, plan):
    h = make()
    compiled, *_ = ready(h)
    compiled.document()["inputs"]["proof_plans"][R1] = plan
    refused(bind(h, compiled), "proof_plan")


def test_changed_proof_plan_holds_as_the_existing_lint_hold(make):
    h = make()
    compiled, *_ = ready(h)
    compiled.document()["inputs"]["proof_plans"][R1] = OTHER
    held = bind(h, compiled)
    assert isinstance(held, LintHold) and (held.duty, held.field) == ("verification", "proof_plan")


@pytest.mark.parametrize("text", ["", None, b"text", 7])
def test_text_that_is_not_a_nonempty_string_holds(make, text):
    h = make()
    compiled, candidate, plan, _ = ready(h)
    refused(pinned(U1, {**candidate, "text": text}, plan), "text")
    refused(pinned(U1, {k: v for k, v in candidate.items() if k != "text"}, plan), "text")


def test_current_readiness_hold_is_propagated(make):
    h = make()
    compiled, *_ = ready(h)
    revise_decision(h)
    held = bind(h, compiled)
    assert isinstance(held, Hold) and held.reason_code == "STALE_ASSESSMENT", held
    (h.decisions / DECISION).unlink()
    held = bind(h, compiled)
    assert isinstance(held, LintHold) and (held.duty, held.field) == ("decision", "governing_decisions")


# --- The latest retained attempt --------------------------------------------------------------------------------


ALTERED_ATTEMPTS = {
    "attempt changed": (replaced("attempt_id", "00000000-0000-4000-8000-000000000000"), "attempt_id"),
    "attempt removed": (without("attempt_id"), "attempt_id"),
    "fingerprint changed": (replaced("input_fingerprint", OTHER), "input_fingerprint"),
    "fingerprint removed": (without("input_fingerprint"), "input_fingerprint"),
    "contract digest changed": (replaced("contract_digest", OTHER), "contract_digest"),
    "contract digest removed": (without("contract_digest"), "contract_digest"),
    "text digest changed": (replaced("input_sha256", OTHER), "text_digest"),
    "text digest removed": (without("input_sha256"), "text_digest"),
    "text digest not text": (replaced("input_sha256", None), "text_digest"),
    "outcome not READY": (lambda e, _: {**e, "outcome": {**e["outcome"], "disposition": "HOLD"}}, "outcome"),
    "outcome failed": (lambda e, _: {**e, "outcome": {**e["outcome"], "failure_class": "MALFORMED"}}, "outcome"),
    "outcome without disposition": (lambda e, _: {**e, "outcome": {"raw_digest": e["outcome"]["raw_digest"]}},
                                    "outcome"),
    "outcome open": (replaced("outcome", None), "outcome"),
    "outcome removed": (without("outcome"), "outcome"),
    "raw reference absent": (replaced("raw_ref", None), "raw_ref"),
    "raw reference removed": (without("raw_ref"), "raw_ref"),
    "raw reference changed": (lambda e, _: {**e, "raw_ref": {**e["raw_ref"], "revision_digest": OTHER}}, "raw_ref"),
    "no attempt": (lambda e, _: None, "latest"),
}


@pytest.mark.parametrize("case", list(ALTERED_ATTEMPTS))
def test_latest_attempt_that_is_not_the_assessed_one_holds(make, case):
    h = make()
    compiled, *_ = ready(h)
    assert type(bind(h, compiled)) is AssessedPublicationInput
    change, field = ALTERED_ATTEMPTS[case]
    altered(h, latest=change)
    refused(bind(h, compiled), field)


def newer_attempt(h: Harness) -> str:
    """A later attempt of the same unit and inputs, opened through the real consumer and not yet observed."""
    consumer, latest = h.profile.readiness_consumer, h.profile.readiness_consumer.latest(U1)
    attempt = consumer.open(U1, latest["input_fingerprint"], latest["input_sha256"], latest["contract_digest"],
                            {"identity": U1, "attempt_id": latest["attempt_id"]}, None, h.profile.readiness_binding)
    assert isinstance(attempt, str) and attempt != latest["attempt_id"]
    return attempt


def test_older_ready_attempt_never_substitutes_for_a_later_open_attempt(make):
    h = make()
    compiled, _, _, outcome = ready(h)
    attempt = newer_attempt(h)
    held = bind(h, compiled)
    assert isinstance(held, Hold) and (held.reason_code, held.attempt_id) == (NO_ASSESSMENT, attempt), held
    assert h.profile.readiness_consumer.history(U1)[0]["attempt_id"] == outcome.attempt_id


def test_older_ready_attempt_never_substitutes_for_a_later_failed_attempt(make):
    h = make()
    compiled, *_ = ready(h)
    attempt, latest = newer_attempt(h), h.profile.readiness_consumer.history(U1)[0]
    h.profile.readiness_consumer.observe(None, AttemptMetadata(
        U1, attempt, latest["input_fingerprint"], latest["input_sha256"], 1, False, None,
        h.profile.readiness_binding), "direct")
    held = bind(h, compiled)
    assert isinstance(held, Hold) and (held.reason_code, held.attempt_id) == (ATTEMPT_FAILURE, attempt), held


# --- The retained raw receipt -----------------------------------------------------------------------------------


def test_inaccessible_raw_receipt_holds_with_its_cause(make):
    h = make()
    compiled, *_ = ready(h)
    bound = bind(h, compiled)
    (h.repository.root / bound.raw_ref.locator).unlink()
    held = refused(bind(h, compiled), "raw_ref")
    assert "MISSING_OBJECT" in held.detail and held.attempt_id == bound.attempt_id


def raising(_):
    raise EvidenceHold("ACCESS_DENIED")


def unavailable(_):
    raise StoreUnavailable("immutable evidence read failed")


def relocated(name: str, value: str):
    """The latest entry and the retrieved receipt agree on a reference that is not this attempt's raw receipt."""
    def reference(ref: dict) -> dict:
        return {**ref, name: value}
    return dict(latest=lambda e, _: {**e, "raw_ref": reference(e["raw_ref"])},
                raw=lambda retained: (reference(retained[0]), retained[1]))


ALTERED_RECEIPTS = {
    "not retained": (dict(raw=lambda retained: None), "no retained raw receipt"),
    "access denied": (dict(raw=raising), "ACCESS_DENIED"),
    "store unavailable": (dict(raw=unavailable), "immutable evidence read failed"),
    "another reference": (dict(raw=lambda r: ({**r[0], "revision_digest": OTHER}, r[1])), "latest raw_ref"),
    "value is bytes": (dict(raw=lambda r: (r[0], r[1].encode())), "not text"),
    "malformed reference": (dict(latest=lambda e, _: {**e, "raw_ref": {"locator": e["raw_ref"]["locator"]}},
                                 raw=lambda r: ({"locator": r[0]["locator"]}, r[1])), "INVALID_RECORD_FIELDS"),
    "invalid digest": (relocated("revision_digest", "sha256:unknown"), "INVALID_DIGEST"),
    "another logical identity": (relocated("logical_id", f"readiness/{U2}/attempt/raw"), "logical_id"),
    "outcome record": (relocated("logical_id", f"readiness/{U1}/attempt/outcome"), "logical_id"),
    "another project": (relocated("project", "AlienLogicLab/elsewhere"), "project"),
    "another profile": (relocated("profile", "fx-b"), "profile"),
}


@pytest.mark.parametrize("case", list(ALTERED_RECEIPTS))
def test_raw_receipt_that_is_not_the_retained_one_holds(make, case):
    h = make()
    compiled, *_ = ready(h)
    reads, cause = ALTERED_RECEIPTS[case]
    altered(h, **reads)
    assert cause in refused(bind(h, compiled), "raw_ref").detail


# --- Changes between the first and the last read ----------------------------------------------------------------


def during(h: Harness, change) -> None:
    """Run change once the raw receipt has been retrieved: after the first reads, before the last."""
    def raw(retained):
        change()
        return retained
    altered(h, raw=raw)


def test_text_changed_in_memory_between_reads_holds(make):
    h = make()
    compiled, candidate, plan, outcome = ready(h)

    def reword():
        unit(compiled)["unit_key"] += ":reworded"
    during(h, reword)
    held = refused(bind(h, compiled), "text", CHANGED)
    assert held.attempt_id == outcome.attempt_id
    assert h.integration.current(h.integration.candidate(compiled, U1, DECISIONS), plan) == outcome


def test_contract_changed_in_memory_between_reads_holds(make):
    h = make()
    compiled, *_ = ready(h)
    during(h, lambda: unit(compiled)["contract"]["non_goals"].append("a later non-goal"))
    held = bind(h, compiled)  # The contract digest is in the readiness fingerprint: existing readiness refuses.
    assert isinstance(held, Hold) and held.reason_code == "STALE_ASSESSMENT", held


def test_unit_removed_in_memory_between_reads_holds(make):
    h = make()
    compiled, *_ = ready(h)
    during(h, lambda: compiled.document()["units"].remove(unit(compiled)))
    refused(bind(h, compiled), "identity")


def test_newer_attempt_opened_between_reads_holds(make):
    h = make()
    compiled, *_ = ready(h)
    opened = []
    during(h, lambda: opened.append(newer_attempt(h)))
    held = bind(h, compiled)
    assert isinstance(held, Hold) and (held.reason_code, held.attempt_id) == (NO_ASSESSMENT, opened[0]), held


@pytest.mark.parametrize("name, value", [("attempt_id", "00000000-0000-4000-8000-000000000000"),
                                         ("outcome", None), ("raw_ref", None), ("input_sha256", OTHER)])
def test_latest_attempt_changed_at_the_last_read_holds(make, name, value):
    h = make()
    compiled, *_ = ready(h)
    consumer = altered(h, latest=lambda entry, read: {**entry, name: value} if read > 1 else entry)
    held = refused(bind(h, compiled), "latest", CHANGED)
    assert name in held.detail and consumer.latest_reads == 2


def test_decision_revised_between_reads_holds(make):
    h = make()
    compiled, *_ = ready(h)
    during(h, lambda: revise_decision(h))
    held = bind(h, compiled)
    assert isinstance(held, Hold) and held.reason_code == "STALE_ASSESSMENT", held


def test_raw_reference_is_a_neutral_evidence_reference(make):
    h = make()
    compiled, *_ = ready(h)
    assert type(bind(h, compiled).raw_ref) is Ref
