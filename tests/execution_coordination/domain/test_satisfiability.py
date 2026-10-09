"""The eight deterministic lifecycle gates and the coordinator's shared vocabulary."""

from __future__ import annotations

import ast
from pathlib import Path
import subprocess

import pytest

from alienintent.composition.sandbox_run_profile import PROVIDER_DIMENSIONS
from alienintent.context_assembly.domain.compilation import contract_from_payload
from alienintent.context_assembly.domain.work_contract import contract_block
from alienintent.execution_coordination.domain.closure import ACTIONS
from alienintent.execution_coordination.domain.satisfiability import unsatisfiable
from tests.context_assembly.test_work_contract import contract_payload

ROOT = Path(__file__).resolve().parents[3]
R5_ID = "8427eb3d-401e-4f4a-8d7c-12abd979c211"


def valid_contract():
    return contract_from_payload(contract_payload(
        required_evidence=["independent-verifier-accepted"],
        budget_policy={"maximum_attempts": 1, "hard_wall_clock_seconds": 60, "cancellation_limit": 1},
        authority_references=["docs/known.md instruction"], required_closure_actions=list(ACTIONS)))


def reasons(contract, *, landing=True, present=lambda _: True, registered=lambda _: True):
    return unsatisfiable(contract, landing=landing, present_at_pointer=present, registered=registered,
                         provider_dimensions=PROVIDER_DIMENSIONS)


def test_valid_contract_has_a_path_to_done():
    assert reasons(valid_contract()) == ()


@pytest.mark.parametrize(("change", "field"), [
    ({"required_evidence": ("not-an-observation",)}, "required_evidence"),
    ({"release_policy": "automatic-on"}, "release_policy"),
    ({"required_capabilities": ("git",)}, "required_capabilities"),
    ({"budget_policy": {"maximum_attempts": 1, "cancellation_limit": 1}}, "budget_policy"),
    ({"budget_policy": {"maximum_attempts": 1, "hard_wall_clock_seconds": 60, "cancellation_limit": 1,
                        "hard_required_dimensions": ("unknown-dimension",)}}, "budget_policy"),
    ({"required_closure_actions": ("merged-to-main",)}, "required_closure_actions"),
    ({"authority_references": ("docs/missing.md instruction",)}, "authority_references"),
    ({"dependencies": ("missing-item",)}, "dependencies"),
])
def test_each_contract_rule_fails_alone(change, field):
    base = valid_contract().canonical_payload()
    base.update(change)
    contract = contract_from_payload(base)
    answer = reasons(contract, present=lambda path: path != "docs/missing.md",
                     registered=lambda item: item != "missing-item")
    assert len(answer) == 1 and answer[0].startswith(field + ":")


def test_automatic_on_passes_only_through_an_approved_plan_authority():
    base = valid_contract().canonical_payload()
    base.update(release_policy="automatic-on")
    contract = contract_from_payload(base)
    assert reasons(contract) == ("release_policy: automatic-on requires an approved plan authority",)
    outside = ("owner-decision-required: one", "owner-decision-required: two")
    for answer in (outside, ()):
        assert unsatisfiable(contract, landing=True, present_at_pointer=lambda _: True, registered=lambda _: True,
                             provider_dimensions=PROVIDER_DIMENSIONS, plan_authority=lambda _: answer) == answer


def test_landing_rule_fails_alone():
    assert len(answer := reasons(valid_contract(), landing=False)) == 1
    assert answer[0].startswith("landing:") and "ready-to-land" in answer[0]


def test_all_failing_fields_are_reported_in_gate_order():
    base = valid_contract().canonical_payload()
    base.update(required_evidence=("unknown",), required_capabilities=("git",),
                authority_references=("missing",), dependencies=("missing",))
    answer = reasons(contract_from_payload(base), present=lambda _: False, registered=lambda _: False, landing=False)
    assert tuple(reason.split(":", 1)[0] for reason in answer) == (
        "required_evidence", "required_capabilities", "authority_references", "dependencies", "landing")


def test_real_r5_packet_exposes_only_the_evidence_and_capability_failures():
    packet = subprocess.check_output(["git", "show", "HEAD:docs/work-units/python/worker-runtime-doc-correction-r5.md"],
                                     cwd=ROOT)
    answer = reasons(contract_block(packet, R5_ID))
    assert tuple(reason.split(":", 1)[0] for reason in answer) == ("required_evidence", "required_capabilities")
    assert "git" in answer[1]


def test_coordinator_imports_the_one_vocabulary_without_literal_copies():
    source = (ROOT / "src/alienintent/execution_coordination/application/factory_coordinator.py").read_text()
    module = ast.parse(source)
    imported = {name.name for node in ast.walk(module) if isinstance(node, ast.ImportFrom)
                and node.module == "alienintent.execution_coordination.domain.satisfiability"
                for name in node.names}
    assert {"VERIFIER_EVIDENCE", "ARTIFACT_VERIFIED", "BASE_CAPABILITIES"} <= imported
    literals = {node.value for node in ast.walk(module) if isinstance(node, ast.Constant)
                and isinstance(node.value, str)}
    assert not {"artifact-verified", "independent-verifier-accepted", "process-control"} & literals
