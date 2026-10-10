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
    PLAN_PATH, Acceptance, PlanAuthority, PlanScopeInvalid, Satisfaction, outside_authority, parse_scope,
    priority_rank, scope_from)
from tests.context_assembly.test_work_contract import satisfiable_payload

ROOT = Path(__file__).resolve().parents[3]
DIGEST = "sha256:" + "a" * 64
SCOPE = {"target_repositories": ["AlienLogicLab/alienintent"], "capabilities": ["python", "filesystem"],
         "budget_caps": {"maximum_attempts": 3, "hard_wall_clock_seconds": 3600, "cancellation_limit": 1,
                         "retry_limit": 1, "concurrency_limit": 1, "hard_required_dimensions": ["wall-clock"]},
         "protected_paths": ["docs/decisions/", "src/alienintent/execution_coordination/domain/release.py"],
         "obligations": [{"label": "SAMPLE", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
                          "allowed_paths": ["docs/", "src/", "tests/"], "intent": "Sample intent.",
                          "acceptance": [{"id": "SAMPLE-A1", "text": "It works."}], "depends_on": [],
                          "satisfied_by": []}]}


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
                                                    "EVENT-TRIGGERED-CONTINUATION", "AUTONOMY-PROOF"]
    # REFILL R1 (decisions section 40): the approved dependencies, and only VOI and BRL mapped to landed work.
    assert {o.label: o.depends_on for o in scope.obligations} == {
        "VERIFICATION-OUTCOME-INTEGRITY": (), "BOUNDED-ROUTINE-LAUNCH": (),
        "WORK-PREPARATION-REFILL": ("VERIFICATION-OUTCOME-INTEGRITY", "BOUNDED-ROUTINE-LAUNCH"),
        "TERMINAL-BOARD-STATUSES": ("BOUNDED-ROUTINE-LAUNCH",), "STORE-SCHEMA-HARDENING": (),
        "EVENT-TRIGGERED-CONTINUATION": ("BOUNDED-ROUTINE-LAUNCH",),
        "AUTONOMY-PROOF": ("WORK-PREPARATION-REFILL", "TERMINAL-BOARD-STATUSES", "STORE-SCHEMA-HARDENING",
                           "EVENT-TRIGGERED-CONTINUATION")}
    mapped = {o.label: {s.acceptance_id for s in o.satisfied_by} for o in scope.obligations}
    assert {label: ids for label, ids in mapped.items() if ids} == {
        "VERIFICATION-OUTCOME-INTEGRITY": {"VOI-A1", "VOI-A2", "VOI-A3", "VOI-A4"},
        "BOUNDED-ROUTINE-LAUNCH": {"BRL-A1", "BRL-A2", "BRL-A3", "BRL-A4", "BRL-A5"}}
    assert all((ROOT / s.evidence).is_file() for o in scope.obligations for s in o.satisfied_by)
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


def two(*changes):
    """SCOPE with a second obligation OTHER, each (index, change) merged into obligation `index` (TEST DATA)."""
    other = {"label": "OTHER", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"],
             "allowed_paths": ["docs/"], "intent": "Other.", "acceptance": [{"id": "OTHER-A1", "text": "x"}],
             "depends_on": [], "satisfied_by": []}
    obligations = [dict(SCOPE["obligations"][0]), other]
    for index, change in changes:
        obligations[index] |= change
    return dict(SCOPE, obligations=obligations)


SATISFIED = {"acceptance_id": "SAMPLE-A1", "work_item": "e73a603e-2cb7-4827-b691-8e0f36d5129a",
             "landed_commit": "2ac6d0c" + "0" * 33, "evidence": "docs/evidence/x.md"}


@pytest.mark.parametrize("scope", [
    two((0, {"intent": ""})),
    two((0, {"acceptance": []})),
    two((0, {"acceptance": [{"id": "SAMPLE-A1"}]})),
    two((0, {"acceptance": [{"id": "sample-1", "text": "x"}]})),
    two((0, {"acceptance": [{"id": "SAMPLE-A1", "text": "x"}, {"id": "SAMPLE-A1", "text": "y"}]})),
    two((1, {"acceptance": [{"id": "SAMPLE-A1", "text": "x"}]})),
    two((0, {"depends_on": ["MISSING"]})),
    two((0, {"depends_on": ["SAMPLE"]})),
    two((0, {"depends_on": ["OTHER"]}), (1, {"depends_on": ["SAMPLE"]})),
    two((0, {"depends_on": ["OTHER", "OTHER"]})),
    two((0, {"satisfied_by": [dict(SATISFIED, acceptance_id="OTHER-A1")]})),
    two((0, {"satisfied_by": [SATISFIED, SATISFIED]})),
    two((0, {"satisfied_by": [dict(SATISFIED, landed_commit="2ac6d0c")]})),
    two((0, {"satisfied_by": [dict(SATISFIED, evidence="")]})),
    two((0, {"satisfied_by": [dict(SATISFIED, extra=1)]})),
    two((0, {"priority": "p0"})),
    two((0, {"priority": "P01"})),
    two((0, {"priority": "P6"})),
    two((0, {"priority": "high"})),
    two((0, {"satisfied_by": [dict(SATISFIED, acceptance_id=["SAMPLE-A1"])]})),
    two((0, {"satisfied_by": [dict(SATISFIED, work_item="  ")]})),
], ids=["empty-intent", "no-acceptance", "acceptance-keys", "acceptance-id-form", "duplicate-id",
        "id-across-obligations", "unknown-dependency", "self-dependency", "two-cycle", "duplicate-dependency",
        "mapping-other-obligation", "mapping-twice", "mapping-short-commit", "mapping-no-evidence",
        "mapping-extra-key", "priority-lowercase", "priority-leading-zero", "priority-off-board", "priority-word",
        "mapping-unhashable-id", "mapping-blank-work-item"])
def test_the_obligation_semantics_are_validated(scope):
    """REFILL R1 (decisions sections 39-41): intent, acceptance (ids LABEL-A<n>, distinct across the block),
    depends_on (known labels, acyclic), the explicit satisfied_by mapping and a priority of the scheduler's set are
    validated; any defect leaves no plan authority."""
    with pytest.raises(PlanScopeInvalid):
        scope_from(scope)


def test_a_three_obligation_dependency_cycle_is_refused():
    third = {"label": "THIRD", "priority": "P0", "satisfied_requirement_ids": ["SF-REQ-002"], "allowed_paths": ["x/"],
             "intent": "t", "acceptance": [{"id": "THIRD-A1", "text": "t"}], "depends_on": ["SAMPLE"],
             "satisfied_by": []}
    scope = two((0, {"depends_on": ["OTHER"]}), (1, {"depends_on": ["THIRD"]}))
    scope["obligations"].append(third)
    with pytest.raises(PlanScopeInvalid, match="cycle"):
        scope_from(scope)


def test_the_obligation_semantics_round_trip_through_the_document():
    scope = scope_from(two((0, {"depends_on": ["OTHER"], "satisfied_by": [SATISFIED]})))
    sample = scope.obligation("SAMPLE")
    assert (sample.intent, sample.acceptance, sample.depends_on) == (
        "Sample intent.", (Acceptance("SAMPLE-A1", "It works."),), ("OTHER",))
    assert sample.satisfied_by == (Satisfaction("SAMPLE-A1", SATISFIED["work_item"], SATISFIED["landed_commit"],
                                                "docs/evidence/x.md"),)
    assert scope_from(scope.document()) == scope


def test_a_priority_is_its_number_as_the_scheduler_reads_it():
    """Founder (decisions section 41): P<n> -> n over exactly the board set P0-P5, never compared as text."""
    assert [priority_rank(p) for p in ("P0", "P1", "P5")] == [0, 1, 5]
    for malformed in ("P6", "P01", "p1", "P", "high"):
        with pytest.raises(ValueError):
            priority_rank(malformed)

