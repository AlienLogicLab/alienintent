"""Obligation state: which canonical plan obligations are finished, in progress, stopped, eligible or waiting, and
which one Work Preparation prepares next (WORK-PREPARATION-REFILL spec 3.2). Pure.

An acceptance id is satisfied only by a plan `satisfied_by` entry the caller verifies (`mapping_holds`: its work item is
DONE with that landed commit on main) or by a DONE Work Item derived from the same obligation that names the id. New
acceptance is never proven retroactively by DONE alone: a DONE item naming no id satisfies nothing (Founder, decisions
section 39). The next obligation is the eligible one with the lowest numeric priority, then plan order (section 41).
"""
from __future__ import annotations

from collections.abc import Callable, Collection, Iterable, Sequence
from dataclasses import dataclass

from alienintent.execution_coordination.domain.plan_authority import PlanScope, Satisfaction, priority_rank

DONE = "DONE"
FINISHED, IN_PROGRESS, STOPPED, ELIGIBLE, WAITING = "finished", "in-progress", "stopped", "eligible", "waiting"


@dataclass(frozen=True)
class DerivedItem:
    """A Work Item derived from plan obligation `obligation`: `final` is None while it is live, else DONE or its final
    outcome; `satisfies` the acceptance ids its contract names."""
    obligation: str
    identity: str
    final: str | None
    satisfies: tuple[str, ...]


@dataclass(frozen=True)
class ObligationState:
    label: str
    status: str
    satisfied: tuple[str, ...]  # acceptance ids satisfied, in plan order
    missing: tuple[str, ...]  # acceptance ids not yet satisfied, in plan order


def obligation_states(scope: PlanScope, items: Iterable[DerivedItem], mapping_holds: Callable[[Satisfaction], bool],
                      stopped: Collection[str]) -> tuple[ObligationState, ...]:
    """Every obligation's state, in plan order."""
    items = tuple(items)
    satisfied: dict[str, set[str]] = {}
    for obligation in scope.obligations:
        ids = {entry.acceptance_id for entry in obligation.satisfied_by if mapping_holds(entry)}
        ids |= {identity for item in items if item.obligation == obligation.label and item.final == DONE
                for identity in item.satisfies}
        satisfied[obligation.label] = ids
    finished = {obligation.label for obligation in scope.obligations
                if all(acceptance.id in satisfied[obligation.label] for acceptance in obligation.acceptance)}
    states = []
    for obligation in scope.obligations:
        label = obligation.label
        if label in finished:
            status = FINISHED
        elif any(item.obligation == label and item.final is None for item in items):
            status = IN_PROGRESS
        elif label in stopped:
            status = STOPPED
        elif all(dependency in finished for dependency in obligation.depends_on):
            status = ELIGIBLE
        else:
            status = WAITING
        states.append(ObligationState(label, status,
                                      tuple(a.id for a in obligation.acceptance if a.id in satisfied[label]),
                                      tuple(a.id for a in obligation.acceptance if a.id not in satisfied[label])))
    return tuple(states)


def next_obligation(scope: PlanScope, states: Sequence[ObligationState]) -> str | None:
    """The eligible obligation with the lowest numeric priority, then plan order; None when none is eligible."""
    eligible = {state.label for state in states if state.status == ELIGIBLE}
    ranked = [(priority_rank(obligation.priority), index, obligation.label)
              for index, obligation in enumerate(scope.obligations) if obligation.label in eligible]
    return min(ranked)[2] if ranked else None
