"""Every static lifecycle refusal has one field-specific answer."""
from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

from alienintent.composition.sandbox_run_profile import PROVIDER_DIMENSIONS
from alienintent.context_assembly.domain.compilation import contract_from_payload
from alienintent.context_assembly.domain.work_contract import contract_block
from alienintent.execution_coordination.domain.closure import ACTIONS
from alienintent.execution_coordination.domain.satisfiability import unsatisfiable
from tests.context_assembly.test_work_contract import contract_payload

ROOT = Path(__file__).resolve().parents[3]


def valid():
    return contract_from_payload(contract_payload(
        required_evidence=["independent-verifier-accepted"],
        budget_policy={"maximum_attempts": 1, "hard_wall_clock_seconds": 60, "cancellation_limit": 1},
        authority_references=["README.md design authority"], required_closure_actions=list(ACTIONS)))


def check(contract, *, landing=True, present=lambda path: True, registered=lambda identity: True):
    return unsatisfiable(contract, landing=landing, present_at_pointer=present, registered=registered,
                         provider_dimensions=PROVIDER_DIMENSIONS)


def test_each_rule_alone_names_its_field():
    contract = valid()
    assert check(contract) == ()
    cases = (
        (replace(contract, required_evidence=("unobservable",)), "required_evidence:"),
        (replace(contract, release_policy="automatic-on"), "release_policy:"),
        (replace(contract, required_capabilities=("git",)), "required_capabilities:"),
        (replace(contract, budget_policy=replace(contract.budget_policy, cancellation_limit=None)), "budget_policy:"),
        (replace(contract, budget_policy=replace(contract.budget_policy,
                                                 hard_required_dimensions=("not-a-provider-dimension",))), "budget_policy:"),
        (replace(contract, required_closure_actions=("merged-to-main",)), "required_closure_actions:"),
    )
    for changed, field in cases:
        reasons = check(changed)
        assert len(reasons) == 1 and reasons[0].startswith(field), reasons
    assert len(check(contract, present=lambda path: False)) == 1
    assert check(contract, present=lambda path: False)[0].startswith("authority_references:")
    assert check(replace(contract, dependencies=("missing",)), registered=lambda identity: False)[0].startswith(
        "dependencies:")
    assert check(contract, landing=False) == (
        "landing: DONE is unreachable; the item would end at ready-to-land",)


def test_all_failures_are_reported_in_rule_order():
    contract = replace(valid(), required_evidence=("unknown",), release_policy="automatic-on",
                       required_capabilities=("git",), dependencies=("missing",))
    reasons = check(contract, landing=False, present=lambda path: False, registered=lambda identity: False)
    assert tuple(reason.split(":", 1)[0] for reason in reasons) == (
        "required_evidence", "release_policy", "required_capabilities", "authority_references", "dependencies",
        "landing")


def test_real_r5_packet_has_the_two_known_refusals():
    packet = (ROOT / "docs/work-units/python/worker-runtime-doc-correction-r5.md").read_bytes()
    contract = contract_block(packet, "8427eb3d-401e-4f4a-8d7c-12abd979c211")
    assert tuple(reason.split(":", 1)[0] for reason in check(contract)) == (
        "required_evidence", "required_capabilities")


def test_coordinator_imports_the_one_vocabulary():
    source = (ROOT / "src/alienintent/execution_coordination/application/factory_coordinator.py").read_text()
    tree = ast.parse(source)
    imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
               and node.module == "alienintent.execution_coordination.domain.satisfiability"]
    assert len(imports) == 1
    assert {name.name for name in imports[0].names} >= {
        "VERIFIER_EVIDENCE", "ARTIFACT_VERIFIED", "BASE_CAPABILITIES"}
    literals = {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    assert not {"artifact-verified", "independent-verifier-accepted", "process-control"} & literals
