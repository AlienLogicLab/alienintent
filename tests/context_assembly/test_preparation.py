"""Work Preparation's deterministic check of a PREPARER packet (WORK-PREPARATION-REFILL R3a, spec 3.3-3.4; WPR-A2: "the
control plane refuses any packet outside the obligation's authority before anything is written"). Plans and packets
are TEST DATA."""
from __future__ import annotations

import json

import pytest

from alienintent.context_assembly.domain.preparation import (
    PENDING, AcceptanceBlockInvalid, check_packet, parse_acceptance)
from alienintent.execution_coordination.domain.plan_authority import PLAN_PATH, PlanAuthority, parse_scope

DIGEST = "sha256:" + "d" * 64
SCOPE = {"target_repositories": ["AlienLogicLab/alienintent"], "capabilities": ["python", "filesystem"],
         "budget_caps": {"maximum_attempts": 3, "hard_wall_clock_seconds": 3600, "cancellation_limit": 1,
                         "retry_limit": 1, "concurrency_limit": 1, "hard_required_dimensions": ["wall-clock"]},
         "protected_paths": ["docs/decisions/", "src/pkg/protected.py"],
         "obligations": [{"label": "FIXTURE", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
                          "allowed_paths": ["src/pkg/", "tests/pkg/"], "intent": "Fixture intent.",
                          "acceptance": [{"id": "FIXTURE-A1", "text": "One."}, {"id": "FIXTURE-A2", "text": "Two."}],
                          "depends_on": [], "satisfied_by": []}]}


def authority() -> PlanAuthority:
    plan = f"# Plan\n\n```json alienintent-plan-authority\n{json.dumps(SCOPE)}\n```\n"
    return PlanAuthority(PLAN_PATH, "c" * 40, DIGEST, f"git:{'c' * 40}:{PLAN_PATH}", "canonical main tip", "",
                         parse_scope(plan))


def contract(**changes) -> dict:
    value = {"identity": PENDING, "version": "revision-1", "intent": "Do the fixture.",
             "satisfied_requirement_ids": ["SF-REQ-002"], "fixed_decisions": ["none"],
             "authorized_scope": ["src/pkg/a.py", "tests/pkg/test_a.py"], "excluded_scope": ["none"],
             "dependencies": [], "required_capabilities": ["python"],
             "budget_policy": {"maximum_attempts": 3, "hard_wall_clock_seconds": 3600, "cancellation_limit": 1},
             "retry_policy": "verifier rejection returns to the PRODUCER", "completion_criteria": ["tests"],
             "verification_obligations": ["independent VERIFIER"],
             "required_evidence": ["independent-verifier-accepted"],
             "non_goals": ["none"], "candidate_custody_requirements": ["exact candidate"],
             "release_policy": "automatic-on", "authority_issuer": "plan-authority:" + DIGEST,
             "authority_references": [f"{PLAN_PATH} obligation:FIXTURE"],
             "target_repositories": ["AlienLogicLab/alienintent"], "baselines": ["main"],
             "required_closure_actions": ["candidate-published", "merged-to-main", "landing-record", "board-updated",
                                          "workspaces-cleaned"],
             "stop_escalation_conditions": ["scope"]}
    return value | changes


def packet(payload: dict | None = None, satisfies=("FIXTURE-A1",), proof=("tests/pkg/test_a.py",), extra="") -> bytes:
    blocks = [f"```json alienintent-contract\n{json.dumps(payload or contract(), indent=1)}\n```"]
    if satisfies is not None:
        blocks.append(f"```json alienintent-acceptance\n{json.dumps({'satisfies': list(satisfies)})}\n```")
    if proof is not None:
        blocks.append(f"```json alienintent-proof\n{json.dumps({'targeted_tests': list(proof)})}\n```")
    return ("# Work unit\n\n" + "\n\n".join(blocks) + "\n" + extra).encode()


def check(data: bytes, label="FIXTURE") -> tuple[str, ...]:
    return check_packet(data, authority(), label)


def test_a_packet_inside_the_obligation_and_the_live_tip_passes():
    assert check(packet()) == ()
    assert check(packet(satisfies=("FIXTURE-A1", "FIXTURE-A2"))) == ()


def test_the_acceptance_block_names_the_ids_a_packet_satisfies():
    assert parse_acceptance(packet().decode()) == ("FIXTURE-A1",)
    assert parse_acceptance(packet(satisfies=None).decode()) is None
    with pytest.raises(AcceptanceBlockInvalid):
        parse_acceptance(packet(extra="```json alienintent-acceptance\n{\"satisfies\": []}\n```\n").decode())


@pytest.mark.parametrize("case, data, reason", [
    pytest.param("not-a-contract", b"# no contract\n", "contract:", id="not-a-contract"),
    pytest.param("registered-identity", packet(contract(identity="0" * 8)), "contract:", id="registered-identity"),
    pytest.param("other-obligation", packet(contract(authority_references=[f"{PLAN_PATH} obligation:OTHER"])),
                 "obligation:", id="other-obligation"),
    pytest.param("older-issuer", packet(contract(authority_issuer="plan-authority:sha256:" + "e" * 64)), "issuer:",
                 id="older-issuer"),
    pytest.param("explicit", packet(contract(release_policy="explicit-human-off")), "release_policy:",
                 id="explicit-release"),
    pytest.param("outside", packet(contract(authorized_scope=["src/other/a.py"])), "owner-decision-required:",
                 id="scope-outside-the-obligation"),
    pytest.param("protected", packet(contract(authorized_scope=["src/pkg/protected.py"])), "owner-decision-required:",
                 id="scope-on-a-protected-path"),
    pytest.param("budget", packet(contract(budget_policy={"maximum_attempts": 9, "hard_wall_clock_seconds": 3600,
                                                          "cancellation_limit": 1})), "owner-decision-required:",
                 id="budget-above-the-cap"),
    pytest.param("no-acceptance", packet(satisfies=None), "acceptance:", id="no-acceptance-block"),
    pytest.param("foreign-id", packet(satisfies=("OTHER-A1",)), "acceptance:", id="acceptance-id-not-the-obligations"),
    pytest.param("no-proof", packet(proof=None), "proof:", id="no-proof-block"),
    pytest.param("bad-proof", packet(proof=("src/pkg/a.py",)), "proof:", id="proof-not-a-test-file"),
])
def test_a_packet_outside_the_obligation_or_the_tip_is_refused_with_its_reason(case, data, reason):
    reasons = check(data)
    assert reasons and any(r.startswith(reason) for r in reasons), reasons


def test_a_packet_for_an_obligation_the_tip_does_not_hold_is_refused():
    assert any(r.startswith("obligation:") for r in check(packet(), label="GONE"))
