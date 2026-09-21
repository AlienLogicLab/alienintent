"""Tests for the local Program Director: routing, risk, program state, restart.

The Director orchestrates the post-Wave-1 program. It is **not** AlienIntent product
execution authority and never touches BIU lifecycle state.

Routing follows the Intelligent Routing policy: deterministic tooling before any model,
cheapest capable model after that, independent review only where risk justifies it.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from director import (  # noqa: E402
    FIVE_QUESTIONS,
    ProgramState,
    RiskClass,
    Tier,
    classify_risk,
    route,
)


# --- Tier 0: never spend intelligence on what tooling settles --------------------


def test_a_fact_establishable_by_tooling_routes_to_no_model():
    d = route(task_type="verify_sha_reachability", risk=RiskClass.LOW,
              deterministic_possible=True)
    assert d.tier is Tier.DETERMINISTIC
    assert d.actor == "deterministic-tooling"
    assert d.model is None


def test_counting_and_schema_validation_need_no_model():
    for t in ("compare_counts", "validate_schema", "regenerate_deterministic_report"):
        assert route(task_type=t, risk=RiskClass.LOW, deterministic_possible=True).tier is Tier.DETERMINISTIC


def test_deterministic_wins_even_for_high_risk_when_it_can_settle_the_question():
    """Risk raises review requirements, not the need for a model to count things."""
    d = route(task_type="compare_counts", risk=RiskClass.HIGH, deterministic_possible=True)
    assert d.tier is Tier.DETERMINISTIC


# --- Tier 1/2: cheapest capable ---------------------------------------------------


def test_narrow_bounded_extraction_routes_to_the_cheap_tier():
    d = route(task_type="extract_fields", risk=RiskClass.LOW, deterministic_possible=False,
              bounded_input=True)
    assert d.tier is Tier.CHEAP_MODEL


def test_substantial_technical_analysis_routes_to_codex_primary():
    d = route(task_type="evidence_reconciliation", risk=RiskClass.MEDIUM,
              deterministic_possible=False)
    assert d.tier is Tier.CODEX_PRIMARY
    assert d.actor == "codex-fresh"
    assert d.model == "gpt-6-astra"


def test_design_and_decomposition_route_to_codex_primary():
    for t in ("design_contract", "biu_decomposition", "dependency_dag"):
        assert route(task_type=t, risk=RiskClass.HIGH, deterministic_possible=False).tier is Tier.CODEX_PRIMARY


# --- Tier 3: the bootstrap coordinator only for what only it can do ---------------


def test_historical_cross_check_routes_to_the_bootstrap_coordinator():
    d = route(task_type="historical_cross_check", risk=RiskClass.HIGH,
              deterministic_possible=False)
    assert d.tier is Tier.CLAUDE_COORDINATOR
    assert d.actor == "claude-bootstrap-coordinator"


def test_bootstrap_retirement_review_uses_the_coordinator_that_witnessed_it():
    assert route(task_type="bootstrap_retirement_review", risk=RiskClass.HIGH,
                 deterministic_possible=False).tier is Tier.CLAUDE_COORDINATOR


def test_the_coordinator_is_not_used_as_primary_author_merely_for_convenience():
    """Its history is a locator, not a licence to author primary artifacts."""
    d = route(task_type="learning_consolidation", risk=RiskClass.HIGH, deterministic_possible=False)
    assert d.actor != "claude-bootstrap-coordinator"
    assert d.tier is Tier.CODEX_PRIMARY


# --- Tier 4 and review policy ------------------------------------------------------


def test_high_risk_design_verification_uses_a_fresh_independent_reviewer():
    d = route(task_type="design_verification", risk=RiskClass.HIGH, deterministic_possible=False)
    assert d.tier is Tier.FRESH_REVIEWER
    assert d.review_required is True


def test_low_risk_work_does_not_pay_for_a_second_model():
    d = route(task_type="extract_fields", risk=RiskClass.LOW, deterministic_possible=False,
              bounded_input=True)
    assert d.review_required is False


def test_high_risk_work_requires_review():
    assert route(task_type="evidence_reconciliation", risk=RiskClass.HIGH,
                 deterministic_possible=False).review_required is True


# --- the five questions are a gate, not decoration ---------------------------------


def test_every_model_routing_answers_all_five_questions():
    d = route(task_type="evidence_reconciliation", risk=RiskClass.MEDIUM, deterministic_possible=False)
    assert set(d.questions) == set(FIVE_QUESTIONS)
    assert all(str(v).strip() for v in d.questions.values())


def test_a_routing_decision_records_why_that_actor_is_cheapest_capable():
    d = route(task_type="design_contract", risk=RiskClass.HIGH, deterministic_possible=False)
    assert d.rationale and len(d.rationale) > 10


def test_risk_classification_follows_the_documented_taxonomy():
    assert classify_risk("metadata_index_update") is RiskClass.LOW
    assert classify_risk("learning_consolidation") is RiskClass.MEDIUM
    assert classify_risk("design_contract") is RiskClass.HIGH
    assert classify_risk("bootstrap_retirement_review") is RiskClass.HIGH


# --- program state and restart reconstruction --------------------------------------


def test_state_round_trips_through_disk(tmp_path):
    s = ProgramState(tmp_path / "program-state.json")
    s.upsert_task("POSTW1-REVIEW-001", phase="1R", title="Independent review",
                  actor="claude-bootstrap-coordinator", status="DONE", risk="HIGH")
    assert ProgramState(tmp_path / "program-state.json").task("POSTW1-REVIEW-001")["status"] == "DONE"


def test_a_restarted_director_reconstructs_phase_and_tasks(tmp_path):
    p = tmp_path / "program-state.json"
    s = ProgramState(p)
    s.set_phase("1R")
    s.upsert_task("T-1", phase="1R", title="x", actor="claude", status="RUNNING", risk="HIGH")
    reborn = ProgramState(p)
    assert reborn.current_phase() == "1R"
    assert reborn.task("T-1")["status"] == "RUNNING"


def test_next_task_skips_completed_and_blocked_work(tmp_path):
    s = ProgramState(tmp_path / "program-state.json")
    s.upsert_task("A", phase="1R", title="done", actor="x", status="DONE", risk="LOW")
    s.upsert_task("B", phase="2", title="blocked", actor="x", status="BLOCKED", risk="LOW")
    s.upsert_task("C", phase="2", title="ready", actor="x", status="READY", risk="LOW")
    assert s.next_task()["task_id"] == "C"


def test_a_founder_decision_blocks_its_branch_and_is_surfaced(tmp_path):
    s = ProgramState(tmp_path / "program-state.json")
    s.upsert_task("D", phase="6", title="retire?", actor="x",
                  status="FOUNDER_DECISION_REQUIRED", risk="HIGH")
    assert [t["task_id"] for t in s.founder_decisions_required()] == ["D"]
    assert s.next_task() is None


def test_program_states_are_never_biu_lifecycle_states(tmp_path):
    """The plan is explicit: program states must not be confused with BIU lifecycle."""
    s = ProgramState(tmp_path / "program-state.json")
    for lifecycle in ("IMPLEMENT", "VERIFY", "ACCEPT", "CAPTURE", "TASKS"):
        with pytest.raises(ValueError):
            s.upsert_task("X", phase="2", title="t", actor="a", status=lifecycle, risk="LOW")


def test_state_records_no_private_chain_of_thought(tmp_path):
    s = ProgramState(tmp_path / "program-state.json")
    s.upsert_task("E", phase="2", title="t", actor="a", status="READY", risk="LOW",
                  prompt_path="prompts/e.md", artifact_refs=["docs/evidence/x.md"])
    raw = json.loads((tmp_path / "program-state.json").read_text())
    text = json.dumps(raw).lower()
    for banned in ("reasoning", "chain_of_thought", "thinking"):
        assert banned not in text


def test_a_later_phase_is_not_offered_while_an_earlier_phase_is_still_in_repair(tmp_path):
    """Observed in live use: with Phase 2 in REPAIR after review, next_task() offered the
    Phase 6 task. An operator following it would start a later phase over an open repair."""
    st = ProgramState(tmp_path / "s.json")
    st.upsert_task("A", phase="2", title="earlier", actor="x", status="REPAIR", risk="MEDIUM")
    st.upsert_task("B", phase="6", title="later", actor="x", status="PLANNED", risk="HIGH")
    assert st.next_task() is None


def test_work_still_flows_when_the_earlier_phase_is_complete(tmp_path):
    st = ProgramState(tmp_path / "s.json")
    st.upsert_task("A", phase="2", title="earlier", actor="x", status="DONE", risk="MEDIUM")
    st.upsert_task("B", phase="6", title="later", actor="x", status="PLANNED", risk="HIGH")
    assert st.next_task()["task_id"] == "B"
