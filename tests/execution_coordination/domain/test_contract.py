from __future__ import annotations

import pytest

from alienintent.execution_coordination.domain.contract import (
    BudgetPolicy,
    ContractValidationError,
    BiuContract,
)


def valid_contract(**changes: object) -> BiuContract:
    values: dict[str, object] = {
        "identity": "PY-02",
        "version": "1",
        "intent": "Build a deterministic execution kernel",
        "satisfied_requirement_ids": ("SF-REQ-010",),
        "fixed_decisions": ("pure-domain",),
        "authorized_scope": ("execution-coordination",),
        "excluded_scope": ("adapters",),
        "dependencies": (),
        "required_capabilities": ("python",),
        "budget_policy": BudgetPolicy(hard_required_dimensions=("attempts",)),
        "retry_policy": "no automatic retry",
        "completion_criteria": ("tests pass",),
        "verification_obligations": ("unit tests",),
        "required_evidence": ("test output",),
        "non_goals": ("network",),
        "candidate_custody_requirements": ("independent read-back",),
        "release_policy": "explicit-human-off",
        "authority_issuer": "Founder",
        "authority_references": ("SWF-15",),
        "target_repositories": ("AlienLogicLab/alienintent",),
        "baselines": ("main@8a82e563",),
        "required_closure_actions": ("publish candidate",),
        "stop_escalation_conditions": ("authority conflict",),
    }
    values.update(changes)
    return BiuContract(**values)


def test_contract_has_stable_digest_and_changed_payload_changes_it() -> None:
    contract = valid_contract()

    assert contract.content_digest == valid_contract().content_digest
    assert contract.content_digest != valid_contract(intent="Different intent").content_digest


def test_contract_rejects_an_incomplete_required_field() -> None:
    with pytest.raises(ContractValidationError, match="intent"):
        valid_contract(intent="")


def test_budget_policy_rejects_a_blank_hard_required_dimension() -> None:
    with pytest.raises(ContractValidationError, match="budget dimensions"):
        BudgetPolicy(hard_required_dimensions=("", "attempts"))
