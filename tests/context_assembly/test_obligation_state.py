"""WORK-PREPARATION-REFILL R1 (spec 3.2, decisions sections 39-41): obligation state from plain data. An acceptance id
is satisfied only by a verified satisfied_by mapping or a DONE item naming it; an unmapped legacy DONE satisfies nothing;
dependencies need finished obligations; the next obligation is eligible by numeric priority, then plan order. Labels and
items are TEST DATA."""
from __future__ import annotations

from alienintent.context_assembly.domain.obligation_state import DerivedItem, next_obligation, obligation_states
from alienintent.execution_coordination.domain.plan_authority import scope_from


def ob(label, ids, depends=(), mapped=(), priority="P0"):
    return {"label": label, "priority": priority, "satisfied_requirement_ids": ["SF-REQ-002"],
            "allowed_paths": ["src/"], "intent": label, "depends_on": list(depends),
            "acceptance": [{"id": f"{label}-A{n}", "text": "t"} for n in ids],
            "satisfied_by": [{"acceptance_id": f"{label}-A{n}", "work_item": "w", "landed_commit": "a" * 40,
                              "evidence": "e"} for n in mapped]}


def scope(*obligations):
    return scope_from({"target_repositories": ["r"], "capabilities": ["python"],
                       "budget_caps": {"maximum_attempts": 3, "hard_wall_clock_seconds": 3600,
                                       "cancellation_limit": 1, "retry_limit": 1, "concurrency_limit": 1,
                                       "hard_required_dimensions": ["wall-clock"]},
                       "protected_paths": ["docs/decisions/"], "obligations": list(obligations)})


def status(states):
    return {state.label: state.status for state in states}


PLAN = scope(ob("A", [1, 2], mapped=[1, 2]), ob("B", [1, 2], depends=["A"]), ob("C", [1], depends=["B"]),
             ob("D", [1]))


def test_a_mapped_obligation_is_finished_only_when_its_mappings_hold():
    assert status(obligation_states(PLAN, [], lambda s: True, ()))["A"] == "finished"
    states = obligation_states(PLAN, [], lambda s: s.acceptance_id != "A-A2", ())
    assert status(states)["A"] == "eligible" and (states[0].satisfied, states[0].missing) == (("A-A1",), ("A-A2",))
    assert status(states)["B"] == "waiting"


def test_an_unmapped_legacy_done_item_satisfies_nothing():
    assert status(obligation_states(PLAN, [DerivedItem("D", "x", "DONE", ())], lambda s: True, ()))["D"] == "eligible"


def test_done_items_cover_ids_and_finish_the_obligation_together():
    one = DerivedItem("B", "x", "DONE", ("B-A1",))
    assert status(obligation_states(PLAN, [one], lambda s: True, ()))["B"] == "eligible"
    both = [one, DerivedItem("B", "y", "DONE", ("B-A2",))]
    assert status(obligation_states(PLAN, both, lambda s: True, ())) == {
        "A": "finished", "B": "finished", "C": "eligible", "D": "eligible"}


def test_an_item_of_another_obligation_or_a_failed_item_covers_nothing():
    items = [DerivedItem("D", "x", "DONE", ("B-A1", "B-A2")), DerivedItem("B", "y", "failure", ("B-A1", "B-A2"))]
    assert status(obligation_states(PLAN, items, lambda s: True, ()))["B"] == "eligible"


def test_a_live_item_is_in_progress_and_a_stopped_label_is_stopped():
    items = [DerivedItem("B", "x", None, ("B-A1",)), DerivedItem("D", "y", "failure", ("D-A1",))]
    states = status(obligation_states(PLAN, items, lambda s: True, {"D"}))
    assert (states["B"], states["D"]) == ("in-progress", "stopped")


def test_the_next_obligation_is_eligible_by_numeric_priority_then_plan_order():
    plan = scope(ob("A", [1], priority="P2"), ob("B", [1], priority="P1"), ob("C", [1], priority="P1"))
    assert next_obligation(plan, obligation_states(plan, [], lambda s: True, ())) == "B"
    done = [DerivedItem("B", "x", "DONE", ("B-A1",))]
    assert next_obligation(plan, obligation_states(plan, done, lambda s: True, ())) == "C"
    everything = done + [DerivedItem("C", "y", "DONE", ("C-A1",)), DerivedItem("A", "z", "DONE", ("A-A1",))]
    assert next_obligation(plan, obligation_states(plan, everything, lambda s: True, ())) is None


def test_a_dependency_finished_only_by_a_failing_mapping_keeps_its_dependent_waiting():
    states = obligation_states(PLAN, [], lambda s: False, ())
    assert status(states)["B"] == "waiting" and next_obligation(PLAN, states) == "A"
