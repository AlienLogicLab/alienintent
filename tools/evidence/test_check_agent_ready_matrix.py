"""Tests for the Agent-Ready Outcome Handling Matrix checker.

Phase 4's required invariant, from the program plan:

    Every Agent-Ready disposition has exactly one defined authority path.
    No non-READY outcome may be silently coerced into READY.
    Resolved prerequisites do not retroactively rewrite an old BLOCKED verdict;
    reassessment is required.

The deterministic prework found that BLOCKED and SPLIT_RECOMMENDED never persist as a
disposition in any assessment file even though Wave 1 produced both, and that PY-09B retained
its non-READY verdict as a dated sibling file while PY-10 did not. So this checker treats the
coercion invariant as the thing most worth enforcing mechanically.

Execution failures are not readiness dispositions. Conflating them is how a provider timeout
becomes a readiness verdict.
"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from check_agent_ready_matrix import CHECKS, check_matrix  # noqa: E402


def _row(**over):
    r = {
        "disposition": "BLOCKED",
        "semantic_meaning": "a prerequisite is unmet and implementation must not start",
        "authority_owner": "SF-REQ-002",
        "lifecycle_effect": "BIU remains pre-IMPLEMENT",
        "next_action": "resolve the prerequisite, then reassess",
        "required_artifact": "a new dated assessment; the prior verdict is retained",
        "attention_behavior": "durable attention item for the coordinator",
        "stale_assessment_rule": "an assessment older than its governing contract is stale",
        "reassessment_trigger": "prerequisite resolution",
        "DAG_effect": "successors remain ineligible",
        "Founder_decision_required": "no",
        "implementation_allowed": False,
    }
    r.update(over)
    return r


def _matrix(rows=None, failures=None):
    return {"dispositions": rows if rows is not None else [_row()],
            "execution_failures": failures if failures is not None else [
                {"mode": "provider_or_tool_failure", "is_readiness_disposition": False,
                 "next_action": "classify as provider failure and retry under policy"},
                {"mode": "timeout", "is_readiness_disposition": False,
                 "next_action": "preserve partial work, reassess"},
                {"mode": "malformed_result", "is_readiness_disposition": False,
                 "next_action": "reject, do not coerce"},
                {"mode": "missing_terminal_result", "is_readiness_disposition": False,
                 "next_action": "treat as DURABLE_RESULT_MISSING"}]}


def test_a_clean_matrix_passes():
    ok, failures = check_matrix(_matrix())
    assert ok, failures


def test_a_missing_field_is_rejected():
    r = _row()
    del r["reassessment_trigger"]
    ok, failures = check_matrix(_matrix([r]))
    assert not ok
    assert any("required_fields" in f for f in failures)


def test_a_non_ready_disposition_that_permits_implementation_is_rejected():
    """The coercion invariant, enforced mechanically."""
    ok, failures = check_matrix(_matrix([_row(implementation_allowed=True)]))
    assert not ok
    assert any("no_silent_coercion" in f for f in failures)


def test_ready_may_permit_implementation():
    ok, failures = check_matrix(_matrix([_row(disposition="READY", implementation_allowed=True)]))
    assert ok, failures


def test_a_non_ready_disposition_without_a_reassessment_trigger_is_rejected():
    """Resolved prerequisites must not retroactively rewrite a verdict; something must say
    what forces a fresh assessment."""
    ok, failures = check_matrix(_matrix([_row(reassessment_trigger="none")]))
    assert not ok
    assert any("reassessment_required" in f for f in failures)


def test_a_disposition_without_exactly_one_authority_owner_is_rejected():
    ok, failures = check_matrix(_matrix([_row(authority_owner="none")]))
    assert not ok
    assert any("one_authority_path" in f for f in failures)


def test_two_rows_for_the_same_disposition_are_rejected():
    """Exactly one authority path means one row, not two that could disagree."""
    ok, failures = check_matrix(_matrix([_row(), _row()]))
    assert not ok
    assert any("one_authority_path" in f for f in failures)


def test_an_execution_failure_classed_as_a_readiness_disposition_is_rejected():
    m = _matrix()
    m["execution_failures"][0]["is_readiness_disposition"] = True
    ok, failures = check_matrix(m)
    assert not ok
    assert any("failures_are_not_dispositions" in f for f in failures)


def test_an_uncovered_execution_failure_mode_is_rejected():
    m = _matrix()
    m["execution_failures"] = m["execution_failures"][:2]
    ok, failures = check_matrix(m)
    assert not ok
    assert any("failure_modes_covered" in f for f in failures)


def test_a_disposition_requiring_improvisation_is_rejected():
    """Exit gate: no supported outcome requires coordinator improvisation."""
    ok, failures = check_matrix(_matrix([_row(next_action="none — coordinator decides")]))
    assert not ok
    assert any("no_improvisation" in f for f in failures)


# --- SWF-24 ---------------------------------------------------------------------------

NEGATIVE_CONTROLS = {
    "required_fields": lambda m: m["dispositions"][0].pop("reassessment_trigger"),
    "no_silent_coercion": lambda m: m["dispositions"][0].__setitem__("implementation_allowed", True),
    "reassessment_required": lambda m: m["dispositions"][0].__setitem__("reassessment_trigger", "none"),
    "one_authority_path": lambda m: m["dispositions"][0].__setitem__("authority_owner", "none"),
    "failures_are_not_dispositions":
        lambda m: m["execution_failures"][0].__setitem__("is_readiness_disposition", True),
    "failure_modes_covered": lambda m: m.__setitem__("execution_failures", []),
    "no_improvisation": lambda m: m["dispositions"][0].__setitem__("next_action", "none"),
}


def test_every_check_has_a_negative_control():
    unkillable = []
    for name, mutate in NEGATIVE_CONTROLS.items():
        m = copy.deepcopy(_matrix())
        mutate(m)
        ok, failures = check_matrix(m)
        if ok or not any(name in f for f in failures):
            unkillable.append(name)
    assert not unkillable, f"checks that could not be made to fail: {unkillable}"
    assert set(NEGATIVE_CONTROLS) == set(CHECKS)
