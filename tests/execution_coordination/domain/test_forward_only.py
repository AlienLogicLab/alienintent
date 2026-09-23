"""Proven-red controls for the Forward-Only Factory Contract."""

from __future__ import annotations

import pytest

from alienintent.execution_coordination.domain.forward_only import (
    AuthorityQuestion,
    AuthorityRoute,
    FailureClassLedger,
    LessonClosure,
    LessonDisposition,
    RecheckDisposition,
    assess_invalidation,
    route_authority,
)


def test_unrelated_change_reuses_completed_evidence_and_intersection_is_targeted() -> None:
    reused = assess_invalidation(
        completed_evidence="verify:WO-220102:4",
        declared_boundaries=("src/alienintent/execution_coordination", "interface:worker-provider"),
        changed_boundaries=("docs/operations",),
    )
    affected = assess_invalidation(
        completed_evidence="verify:WO-220102:4",
        declared_boundaries=("src/alienintent/execution_coordination", "interface:worker-provider"),
        changed_boundaries=("interface:worker-provider",),
    )
    unbounded = assess_invalidation(
        completed_evidence="verify:WO-220102:4",
        declared_boundaries=("src/alienintent/execution_coordination",),
        changed_boundaries=(),
        impact_bounded=False,
    )

    assert reused.disposition is RecheckDisposition.REUSE
    assert reused.evidence_to_reuse == "verify:WO-220102:4"
    assert affected.disposition is RecheckDisposition.TARGETED_RECHECK
    assert affected.affected_boundaries == ("interface:worker-provider",)
    assert unbounded.disposition is RecheckDisposition.FULL_VALIDATION


@pytest.mark.parametrize(
    "question, expected",
    (
        (AuthorityQuestion.MACHINERY_REPAIR, AuthorityRoute.DELEGATED_ENGINEERING),
        (AuthorityQuestion.TEST_REPAIR, AuthorityRoute.DELEGATED_ENGINEERING),
        (AuthorityQuestion.COMPATIBILITY_REPAIR, AuthorityRoute.DELEGATED_ENGINEERING),
        (AuthorityQuestion.PRODUCT_INTENT, AuthorityRoute.FOUNDER_DECISION),
        (AuthorityQuestion.MATERIAL_ARCHITECTURE, AuthorityRoute.FOUNDER_DECISION),
        (AuthorityQuestion.SECURITY_RISK_ACCEPTANCE, AuthorityRoute.FOUNDER_DECISION),
        (AuthorityQuestion.BUDGET_LIMIT, AuthorityRoute.FOUNDER_DECISION),
        (AuthorityQuestion.EXTERNAL_COMMITMENT, AuthorityRoute.FOUNDER_DECISION),
        (AuthorityQuestion.LIVE_OPERATION, AuthorityRoute.FOUNDER_DECISION),
    ),
)
def test_authority_routing_reuses_existing_engineering_authority(question, expected) -> None:
    assert route_authority(question) is expected


def test_general_lesson_cannot_close_without_a_disposition_and_required_evidence() -> None:
    with pytest.raises(ValueError, match="disposition"):
        LessonClosure("overlapping-mutation", None, ())
    with pytest.raises(ValueError, match="proven-red"):
        LessonClosure("overlapping-mutation", LessonDisposition.MECHANICAL_ENFORCEMENT, ("enforcement:reservation:repository",))
    with pytest.raises(ValueError, match="enforcement"):
        LessonClosure("overlapping-mutation", LessonDisposition.MECHANICAL_ENFORCEMENT, ("proven-red:test_wip_refusal",))
    with pytest.raises(ValueError, match="proven-red"):
        LessonClosure("missing-preflight", LessonDisposition.DETERMINISTIC_PREFLIGHT, ("preflight:worker",))
    with pytest.raises(ValueError, match="owner"):
        LessonClosure("architecture-fit", LessonDisposition.JUDGMENT_ONLY, ("review:42",))
    with pytest.raises(ValueError, match="rationale"):
        LessonClosure("architecture-fit", LessonDisposition.JUDGMENT_ONLY, ("judgment-owner:architecture",))


def test_recurrence_of_mechanized_failure_is_a_durable_regression_not_a_new_lesson(tmp_path) -> None:
    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore

    ledger = FailureClassLedger(SQLiteOperationalStore(tmp_path / "state.sqlite"), "offline")
    ledger.close(LessonClosure(
        "overlapping-mutation",
        LessonDisposition.MECHANICAL_ENFORCEMENT,
        ("enforcement:reservation:repository", "proven-red:test_wip_refusal"),
    ))

    recurrence = FailureClassLedger(SQLiteOperationalStore(tmp_path / "state.sqlite"), "offline").record_recurrence("overlapping-mutation", "review:43")

    assert recurrence.status == "REGRESSION"
    assert recurrence.failure_class == "overlapping-mutation"
    assert recurrence.enforcement_evidence == ("enforcement:reservation:repository", "proven-red:test_wip_refusal")
    _, recorded = SQLiteOperationalStore(tmp_path / "state.sqlite").read_state("offline", "failure-class:overlapping-mutation")
    assert recorded["recurrences"] == [{"evidence": "review:43", "status": "REGRESSION"}]


def test_lesson_ledger_refuses_to_weaken_an_existing_closure(tmp_path) -> None:
    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore

    ledger = FailureClassLedger(SQLiteOperationalStore(tmp_path / "state.sqlite"), "offline")
    ledger.close(LessonClosure(
        "overlapping-mutation",
        LessonDisposition.MECHANICAL_ENFORCEMENT,
        ("enforcement:reservation:repository", "proven-red:test_wip_refusal"),
    ))

    with pytest.raises(ValueError, match="supersession"):
        ledger.close(LessonClosure(
            "overlapping-mutation",
            LessonDisposition.JUDGMENT_ONLY,
            ("judgment-owner:architecture", "judgment-rationale:semantic-fit"),
        ))


def test_preflight_recurrence_is_also_a_durable_regression(tmp_path) -> None:
    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore

    ledger = FailureClassLedger(SQLiteOperationalStore(tmp_path / "state.sqlite"), "offline")
    ledger.close(LessonClosure(
        "missing-identity-preflight",
        LessonDisposition.DETERMINISTIC_PREFLIGHT,
        ("preflight:identity", "proven-red:test_missing_identity"),
    ))

    assert ledger.record_recurrence("missing-identity-preflight", "review:44").status == "REGRESSION"
