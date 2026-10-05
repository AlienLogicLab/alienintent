from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from alienintent.composition.sandbox_run_profile import PROVIDER_DIMENSIONS
from alienintent.context_assembly.domain.work_contract import contract_block
from alienintent.execution_coordination.domain.closure import ACTIONS
from alienintent.execution_coordination.domain.contract import BudgetPolicy
from alienintent.execution_coordination.domain.satisfiability import unsatisfiable
from tests.execution_coordination.domain.test_contract import valid_contract


def good_contract():
    return valid_contract(required_evidence=("independent-verifier-accepted",),
                          budget_policy=BudgetPolicy(hard_wall_clock_seconds=10, cancellation_limit=1),
                          authority_references=("docs/reference.md explanation",),
                          required_closure_actions=ACTIONS)


def check(contract=None, *, landing=True, present_at_pointer=lambda path: True,
          registered=lambda identity: True):
    return unsatisfiable(contract or good_contract(), landing=landing, present_at_pointer=present_at_pointer,
                         registered=registered, provider_dimensions=PROVIDER_DIMENSIONS)


def test_valid_contract_has_a_path_to_done():
    assert check() == ()


@pytest.mark.parametrize(("change", "field"), [
    ({"required_evidence": ("unobservable",)}, "required_evidence"),
    ({"release_policy": "automatic-on"}, "release_policy"),
    ({"required_capabilities": ("git",)}, "required_capabilities"),
    ({"budget_policy": BudgetPolicy(cancellation_limit=1)}, "budget_policy"),
    ({"budget_policy": BudgetPolicy(hard_wall_clock_seconds=10, cancellation_limit=1,
                                     hard_required_dimensions=("unprovided",))}, "budget_policy"),
    ({"required_closure_actions": ("merged-to-main",)}, "required_closure_actions"),
])
def test_each_contract_rule_refuses_alone(change, field):
    reasons = check(replace(good_contract(), **change))
    assert len(reasons) == 1 and reasons[0].startswith(field + ":")


def test_pointer_dependency_and_landing_rules_refuse_alone():
    assert len(check(present_at_pointer=lambda path: False)) == 1
    assert check(present_at_pointer=lambda path: False)[0].startswith("authority_references:")
    assert check(replace(good_contract(), dependencies=("other",)), registered=lambda identity: False)[0].startswith(
        "dependencies:")
    assert len(check(replace(good_contract(), dependencies=("other",)), registered=lambda identity: False)) == 1
    assert check(landing=False) == ("landing: DONE is unreachable; item ends at ready-to-land",)


def test_all_failing_fields_are_reported_in_rule_order():
    contract = replace(good_contract(), required_evidence=("unobservable",), release_policy="automatic-on",
                       required_capabilities=("git",), budget_policy=BudgetPolicy(),
                       required_closure_actions=("merge",), dependencies=("unknown",))
    reasons = check(contract, landing=False, present_at_pointer=lambda path: False,
                    registered=lambda identity: False)
    assert tuple(reason.split(":", 1)[0] for reason in reasons) == (
        "required_evidence", "release_policy", "required_capabilities", "budget_policy",
        "required_closure_actions", "authority_references", "dependencies", "landing")


def test_real_r5_packet_has_only_the_two_known_unreachable_fields():
    path = Path(__file__).resolve().parents[3] / "docs/work-units/python/worker-runtime-doc-correction-r5.md"
    contract = contract_block(path.read_bytes(), "8427eb3d-401e-4f4a-8d7c-12abd979c211")
    reasons = check(contract)
    assert len(reasons) == 2
    assert reasons[0].startswith("required_evidence:")
    assert reasons[1].startswith("required_capabilities:") and "git" in reasons[1]


def test_coordinator_imports_one_vocabulary():
    path = Path(__file__).resolve().parents[3] / "src/alienintent/execution_coordination/application/factory_coordinator.py"
    tree = ast.parse(path.read_text())
    imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
               and node.module == "alienintent.execution_coordination.domain.satisfiability"]
    assert len(imports) == 1
    assert {node.name for node in imports[0].names} >= {
        "VERIFIER_EVIDENCE", "ARTIFACT_VERIFIED", "BASE_CAPABILITIES"}
    strings = {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    assert not strings.intersection({"artifact-verified", "independent-verifier-accepted", "process-control"})
