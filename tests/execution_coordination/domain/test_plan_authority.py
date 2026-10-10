"""PLAN-AUTHORITY-INHERITANCE acceptance checks 1 and 7: the pure plan-authority rule and the canonical plan's block.

`outside_authority` answers nothing for a contract inside a sample obligation and exactly one owner-decision reason
for each single change; `parse_scope` refuses a missing, duplicate or malformed block and wrong keys. Sample plans,
labels and digests are TEST DATA.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from alienintent.context_assembly.domain.compilation import contract_from_payload
from alienintent.execution_coordination.domain.plan_authority import (
    PLAN_PATH, PlanAuthority, PlanScopeInvalid, outside_authority, parse_scope)
from tests.context_assembly.test_work_contract import satisfiable_payload

ROOT = Path(__file__).resolve().parents[3]
DIGEST = "sha256:" + "a" * 64
SCOPE = {"target_repositories": ["AlienLogicLab/alienintent"], "capabilities": ["python", "filesystem"],
         "budget_caps": {"maximum_attempts": 3, "hard_wall_clock_seconds": 3600, "cancellation_limit": 1,
                         "retry_limit": 1, "concurrency_limit": 1, "hard_required_dimensions": ["wall-clock"]},
         "protected_paths": ["docs/decisions/", "src/alienintent/execution_coordination/domain/release.py"],
         "obligations": [{"label": "SAMPLE", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
                          "allowed_paths": ["docs/", "src/", "tests/"]}]}


def plan(scope: object = SCOPE, blocks: int = 1) -> str:
    block = f"```json alienintent-plan-authority\n{scope if isinstance(scope, str) else json.dumps(scope)}\n```\n"
    return "# Sample plan\n\n" + block * blocks


AUTHORITY = PlanAuthority(PLAN_PATH, "c" * 40, DIGEST, "sha256:" + "b" * 64, "Founder", "approved", parse_scope(plan()))


def contract(**changes):
    return contract_from_payload(satisfiable_payload(**({
        "release_policy": "automatic-on", "authority_issuer": "plan-authority:" + DIGEST,
        "authority_references": [f"{PLAN_PATH} obligation:SAMPLE", "README.md"],
        "authorized_scope": ["src/alienintent/composition/", "tests/composition/test_x.py"]} | changes)))


def test_a_contract_inside_its_obligation_inherits():
    assert outside_authority(contract(), AUTHORITY) == ()


def test_a_contract_prepared_under_an_older_plan_revision_is_revalidated_against_the_live_one():
    """PLAN-TIP-AUTHORITY-RUNTIME-FIX: the issuer digest records where the item was prepared (provenance); authority is
    the live plan, so an item from an older revision inherits exactly when it is inside the live plan's scope."""
    older = contract(authority_issuer="plan-authority:sha256:" + "f" * 64)
    assert outside_authority(older, AUTHORITY) == ()
    [reason] = outside_authority(contract(authority_issuer="plan-authority:sha256:" + "f" * 64,
                                          authority_references=[f"{PLAN_PATH} obligation:OTHER"]), AUTHORITY)
    assert "obligation OTHER is not in the approved plan" in reason


BUDGET = {"maximum_attempts": 1, "hard_wall_clock_seconds": 60, "cancellation_limit": 1}


@pytest.mark.parametrize(("change", "words"), [
    ({"authority_issuer": "plan-authority:sha256:" + "f" * 63}, "authority_issuer: not the approved"),
    ({"authority_references": ["README.md"]}, "exactly one"),
    ({"authority_references": [f"{PLAN_PATH} obligation:SAMPLE", f"{PLAN_PATH} obligation:SAMPLE"]}, "exactly one"),
    ({"authority_references": [f"{PLAN_PATH} obligation:OTHER"]}, "obligation OTHER is not in the approved plan"),
    ({"target_repositories": ["AlienLogicLab/other"]}, "target_repositories: outside the plan"),
    ({"required_capabilities": ["process-control"]}, "required_capabilities: outside the plan"),
    ({"satisfied_requirement_ids": ["SF-REQ-009"]}, "satisfied_requirement_ids: outside obligation SAMPLE"),
    ({"budget_policy": BUDGET | {"maximum_attempts": 4}}, "maximum_attempts 4 above the cap 3"),
    ({"budget_policy": BUDGET | {"hard_wall_clock_seconds": 3601}}, "hard_wall_clock_seconds 3601 above"),
    ({"budget_policy": BUDGET | {"cancellation_limit": 2}}, "cancellation_limit 2 above"),
    ({"budget_policy": BUDGET | {"retry_limit": 2}}, "retry_limit 2 above"),
    ({"budget_policy": BUDGET | {"concurrency_limit": 2}}, "concurrency_limit 2 above"),
    ({"budget_policy": {"maximum_attempts": 1, "cancellation_limit": 1}}, "hard_wall_clock_seconds is required"),
    ({"budget_policy": BUDGET | {"hard_required_dimensions": ["tokens"]}}, "dimension tokens outside the cap list"),
    ({"authorized_scope": ["config/x.json"]}, "config/x.json is outside obligation SAMPLE"),
    ({"authorized_scope": ["docs/decisions"]}, "crosses a protected path: docs/decisions"),
    ({"authorized_scope": ["src/alienintent/execution_coordination/"]}, "crosses a protected path: src/alienintent"),
    ({"authorized_scope": ["src/alienintent/execution_coordination/domain/Release.py"]},
     "crosses a protected path: src/alienintent/execution_coordination/domain/Release.py"),
    ({"authorized_scope": ["SRC/x.py"]}, "SRC/x.py is outside obligation SAMPLE"),
    ({"authorized_scope": ["src/*.py"]}, "src/*.py is malformed"),
    ({"authorized_scope": ["a/../docs/decisions/x"]}, "a/../docs/decisions/x is malformed"),
    ({"authorized_scope": ["/src/x.py"]}, "/src/x.py is malformed"),
    ({"authority_issuer": "Founder"}, "authority_issuer: not the approved form"),
], ids=lambda value: value if isinstance(value, str) else None)
def test_each_single_change_is_exactly_one_owner_decision(change, words):
    [reason] = outside_authority(contract(**change), AUTHORITY)
    assert reason.startswith("owner-decision-required: ") and words in reason


@pytest.mark.parametrize("text", [
    "# no block\n", plan(blocks=2), plan("{not json"), plan(dict(SCOPE, extra=1)),
    plan({key: value for key, value in SCOPE.items() if key != "protected_paths"}),
    plan(dict(SCOPE, obligations=[dict(SCOPE["obligations"][0], allowed_paths=["../x"])]))],
    ids=["missing", "duplicate", "malformed", "extra-key", "missing-key", "malformed-path"])
def test_parse_scope_refuses_a_missing_duplicate_or_malformed_block(text):
    with pytest.raises(PlanScopeInvalid):
        parse_scope(text)


def test_check7_the_canonical_plan_states_the_rule_and_holds_one_block():
    text = (ROOT / PLAN_PATH).read_text(encoding="utf-8")
    assert "After the Founder approves canonical product intent/plan authority, derived Work Items advance without " \
           "additional Founder approval unless they cross a new owner-decision boundary." in text
    assert "After the Founder approves a queue item" not in text
    headings = [line for line in text.splitlines() if line.startswith("## 2.")]
    assert headings[headings.index("## 2.2.1 Plan authority") - 1].startswith("## 2.2 ")
    assert headings[headings.index("## 2.2.1 Plan authority") + 1].startswith("## 2.3 One work identity")
    scope = parse_scope(text)
    assert [o.label for o in scope.obligations] == ["VERIFICATION-OUTCOME-INTEGRITY", "BOUNDED-ROUTINE-LAUNCH",
                                                    "WORK-PREPARATION-REFILL",
                                                    "TERMINAL-BOARD-STATUSES", "STORE-SCHEMA-HARDENING",
                                                    "AUTONOMY-PROOF"]
    assert {"conftest.py", "pyproject.toml", "config/", "tools/fitness/",
            "src/alienintent/execution_coordination/domain/scope_containment.py",
            "tests/execution_coordination/test_containment_wiring.py"} <= set(scope.protected_paths)


def test_the_plan_itself_is_protected_whatever_the_live_block_says():
    """PLAN-TIP-AUTHORITY-RUNTIME-FIX: with the tip as the live authority, a derived item that changed the plan would
    widen every later item's authority, so the canonical plan is a protected path even when the block omits it."""
    scope = dict(SCOPE, protected_paths=["config/"],
                 obligations=[dict(SCOPE["obligations"][0], allowed_paths=["docs/", "src/"])])
    authority = PlanAuthority(PLAN_PATH, "c" * 40, DIGEST, "git:x", "canonical main tip", "", parse_scope(plan(scope)))
    [reason] = outside_authority(contract(authorized_scope=[PLAN_PATH]), authority)
    assert f"crosses a protected path: {PLAN_PATH}" in reason
