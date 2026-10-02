"""The contract block of a hand-written packet (READY-view check 3): exactly one marked block, valid JSON accepted
by the existing validator, naming the registered item's id; anything else is CONTRACT_INVALID naming which rule.
Contract-like prose outside the block is never read."""
from __future__ import annotations

import json

import pytest

from alienintent.context_assembly.domain.compilation import contract_from_payload
from alienintent.context_assembly.domain.work_contract import (
    CONTRACT_INVALID, DUPLICATE, INVALID_JSON, MISSING, NOT_TEXT, OTHER_IDENTITY, REFUSED, UNCLOSED, ContractInvalid,
    contract_block)

IDENTITY = "989cb378-a47f-43cd-9056-8775782d1fd8"


def contract_payload(identity: str = IDENTITY, **changes) -> dict:
    value = {"identity": identity, "version": "1", "intent": "fixture", "satisfied_requirement_ids": ["SF-REQ-002"],
             "fixed_decisions": ["FD"], "authorized_scope": ["src"], "excluded_scope": ["none"], "dependencies": [],
             "required_capabilities": ["python"], "budget_policy": {"maximum_attempts": 1}, "retry_policy": "none",
             "completion_criteria": ["tests"], "verification_obligations": ["verifier"],
             "required_evidence": ["verdict"], "non_goals": ["none"], "candidate_custody_requirements": ["merge"],
             "release_policy": "explicit-human-off", "authority_issuer": "Founder",
             "authority_references": ["fixture"], "target_repositories": ["AlienLogicLab/alienintent"],
             "baselines": ["main"], "required_closure_actions": ["merge"], "stop_escalation_conditions": ["scope"]}
    value.update(changes)
    return value


def block(payload: dict | str) -> str:
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=1)
    return f"```json alienintent-contract\n{text}\n```\n"


def packet(*parts: str) -> bytes:
    return ("# Work unit: fixture\n\n" + "\n".join(parts)).encode()


def test_the_one_block_is_the_contract_and_prose_outside_it_changes_nothing():
    expected = contract_from_payload(contract_payload(dependencies=["dep-1"]))
    plain = contract_block(packet(block(contract_payload(dependencies=["dep-1"]))), IDENTITY)
    prose = contract_block(packet(
        "identity: some-other-id\ndependencies: dep-9\nbiu: OTHER\ncontract: biu/OTHER.json\n",
        "```json\n" + json.dumps(contract_payload("other", dependencies=["dep-9"])) + "\n```\n",
        block(contract_payload(dependencies=["dep-1"])),
        "Inline ```json alienintent-contract``` text is not a block.\n"), IDENTITY)
    assert plain == prose == expected
    assert prose.content_digest == expected.content_digest and prose.dependencies == ("dep-1",)


@pytest.mark.parametrize(("data", "which"), [
    (packet("no block here\n", "```json\n" + json.dumps(contract_payload()) + "\n```\n"), MISSING),
    (packet(block(contract_payload()), block(contract_payload())), DUPLICATE),
    (packet("```json alienintent-contract\n" + json.dumps(contract_payload()) + "\n"), UNCLOSED),
    (packet(block('{"identity": "x",')), INVALID_JSON),
    (packet(block(contract_payload(intent=""))), REFUSED),
    (packet(block({k: v for k, v in contract_payload().items() if k != "intent"})), REFUSED),
    (packet(block(contract_payload(budget_policy={"maximum_attempts": "3"}))), REFUSED),
    (packet(block(contract_payload(extra="x"))), REFUSED),
    (packet(block("[1, 2]")), REFUSED),
    (packet(block(contract_payload("another-item"))), OTHER_IDENTITY),
    (b"\xff\xfe not text", NOT_TEXT)])
def test_anything_but_exactly_one_valid_block_naming_the_item_is_contract_invalid(data, which):
    with pytest.raises(ContractInvalid) as refused:
        contract_block(data, IDENTITY)
    assert refused.value.code == CONTRACT_INVALID and refused.value.which == which
    assert str(refused.value).startswith(f"{CONTRACT_INVALID}: {which}")
