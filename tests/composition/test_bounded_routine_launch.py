"""BOUNDED-ROUTINE-LAUNCH: one `work run` takes every eligible READY work item through PRODUCER, VERIFIER and CLOSURE to
DONE and admits the next, with no launch per role; it resumes after a crash from recorded state; a DONE is settled
(its WIP slot released) only once its registry row is projected; and it reads open work only, never the history.

Over the launch fixture of test_worker_launch (fake providers, a local bare remote, the Landing Authority), with a WIP
limit of 1 and plan-derived (`automatic-on`) items. Labels are TEST DATA.
"""
from __future__ import annotations

from dataclasses import asdict
import json

import pytest

from alienintent.composition import work_registry
from alienintent.control_plane.application.operator import LAUNCH_IN_PROGRESS, exclusive_run_work
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator, LAUNCH_KEY, LAUNCH_SCOPE
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.domain.plan_authority import PLAN_PATH
from alienintent.composition.work_registry import launch_root
from alienintent.invocation_runtime.adapters import invocation_journal
from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal
from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
from tests.composition.test_work_registry import PLAN_QUOTE, plan_text
from tests.composition.test_worker_launch import FIXED, QUOTE, Closing, Launch, Owners
from tests.context_assembly.test_initial_compilation import git
from tests.context_assembly.test_work_identity_service import commit_file

DONE = LifecycleStage.DONE


@pytest.fixture
def closing(tmp_path, monkeypatch) -> Closing:
    fx = Launch(tmp_path / "fx", monkeypatch)
    fx.host.write_text(json.dumps({"wipLimit": 1}))
    return Closing(fx, monkeypatch)


def planned(closing: Closing, *labels: str):
    """Plan-derived items under one approved fixture plan, READY in the order given; main pushed as the landing base."""
    fx = closing.fx
    digest = fx.registry.plan_approval.approve(commit_file(fx.clone, "main", PLAN_PATH, plan_text()),
                                               PLAN_QUOTE).content_digest
    items = [fx.authorized(label, False, **FIXED, release_policy="automatic-on",
                           authority_issuer="plan-authority:" + digest,
                           authority_references=["README.md", f"{PLAN_PATH} obligation:FIXTURE"],
                           authorized_scope=["launch-candidate.txt"]) for label in labels]
    for item in items:  # every release baseline is the same main, after every packet
        [entry] = [a for a in fx.registry.assessment.consumer.history(item.id)
                   if a["raw_ref"] == asdict(item.assessment_ref)]
        assert fx.registry.authorization.authorize(item.id, item.pointer.commit, entry["attempt_id"], fx.main(),
                                                   QUOTE).answer is None
    git(fx.clone, "push", "-q", "origin", "main")  # the landing base: the release baseline
    return [fx.stored(label) for label in labels]


def work_run(closing: Closing, ownership=None, pause=lambda: None) -> dict:
    registry = closing.fx.loaded(ownership if ownership is not None else Owners("terminated"))
    return exclusive_run_work(registry.launcher, registry.store, registry.ownership, pause=pause)


def roles(closing: Closing) -> list[str]:
    return [run["env"]["ALIENINTENT_ROLE"] for run in closing.fx.runs()]


def verifier_plan(closing: Closing, steps: list[str]) -> None:
    closing.fx.plan.with_name("verifier-plan.json").write_text(json.dumps(steps))


def row_done(closing: Closing, identity: str) -> bool:
    return closing.fx.loaded().identities.find(identity).state == work_registry.DONE


def test_one_run_takes_the_first_item_to_done_then_runs_the_next_with_no_launch_per_role(closing):
    """The first VERIFIER ends without a verdict, so the run pauses and retries it on the next pass; meanwhile the
    second item cannot take the one WIP slot. The first lands; the run then admits the second and runs each of its
    roles. (Its CLOSURE answers base-moved: a PRODUCER starts from its release baseline, which the first landing moved
    on; that is WORK-PREPARATION-REFILL's to change, so only that the second item's roles ran is checked here.)"""
    first, second = planned(closing, "FIRST", "SECOND")
    verifier_plan(closing, ["exit"])
    base, pauses = closing.head(), []

    summary = work_run(closing, pause=lambda: pauses.append(closing.state(first.id).outcome))

    assert pauses == ["verifier-retry"]
    assert closing.state(first.id).stage is DONE and row_done(closing, first.id)
    assert roles(closing) == ["PRODUCER", "VERIFIER", "VERIFIER", "CLOSURE", "PRODUCER", "VERIFIER", "CLOSURE"]
    assert list(summary["ran"]) == [first.id] * 4 + [second.id] * 3
    assert list(summary["dispatched"]) == [first.id, second.id]
    assert summary["stop_reason"] == "eligible-backlog-exhausted" and "projection_diagnostics" not in summary
    assert not closing.fx.wip_held(first.id) and not closing.fx.wip_held(second.id)
    assert first.id in git(closing.remote, "log", "--format=%s", f"{base}..main").decode()


class Crash(BaseException):
    """The process dying: nothing after it runs, and no `except Exception` catches it."""


def test_a_run_that_crashed_mid_verify_resumes_from_recorded_state_on_the_next_run(closing, monkeypatch):
    """The VERIFIER's outcome is durable but the process dies before it is recorded. The next run recovers that
    outcome (no second VERIFIER), finds the started item by its WIP slot although its card has moved on, and
    continues to DONE and to the next item."""
    first, second = planned(closing, "FIRST", "SECOND")
    advance = FactoryCoordinator._advance

    def dies(self, item, current, prior, invocation, outcome):
        if invocation.role == "VERIFIER":
            raise Crash()
        return advance(self, item, current, prior, invocation, outcome)
    monkeypatch.setattr(FactoryCoordinator, "_advance", dies)
    with pytest.raises(Crash):
        work_run(closing)
    monkeypatch.setattr(FactoryCoordinator, "_advance", advance)
    assert closing.state(first.id).stage is LifecycleStage.VERIFY and closing.fx.wip_held(first.id)
    closing.fx.loaded().project_cards()
    assert closing.card(first.id) == "VERIFY"  # not on the READY board any more

    summary = work_run(closing)

    assert closing.state(first.id).stage is DONE
    assert roles(closing) == ["PRODUCER", "VERIFIER", "CLOSURE", "PRODUCER", "VERIFIER", "CLOSURE"]
    assert list(summary["ran"]) == [first.id] + [second.id] * 3


def test_a_done_is_settled_only_once_its_row_is_projected_and_the_next_run_repairs_it(closing, monkeypatch):
    """Projecting the first DONE fails: the item keeps its WIP slot, so the second is not admitted and the run stops,
    naming the projection still owed. The next run projects it from the slot, then runs the second item."""
    first, second = planned(closing, "FIRST", "SECOND")
    project = work_registry.WorkRegistry._project_completed

    def refused(self, identity):
        raise RuntimeError("fixture refusal")
    monkeypatch.setattr(work_registry.WorkRegistry, "_project_completed", refused)

    summary = work_run(closing)

    assert closing.state(first.id).stage is DONE and not row_done(closing, first.id)
    assert closing.fx.wip_held(first.id) and roles(closing) == ["PRODUCER", "VERIFIER", "CLOSURE"]
    assert summary["stop_reason"] == "capacity-unavailable"
    assert list(summary["projection_diagnostics"]) == [first.id]

    monkeypatch.setattr(work_registry.WorkRegistry, "_project_completed", project)
    work_run(closing)

    assert row_done(closing, first.id) and not closing.fx.wip_held(first.id)
    assert roles(closing) == ["PRODUCER", "VERIFIER", "CLOSURE"] * 2


@pytest.mark.parametrize(("answer", "settled"), [("NOT_RECORDABLE", True), ("LANDING_UNVERIFIED", False)])
def test_a_permanent_projection_refusal_settles_the_done_and_a_transient_one_keeps_its_slot(
        closing, monkeypatch, answer, settled):
    """The registry row refuses the first DONE: a permanent refusal (here NOT_RECORDABLE, a retired row) settles it
    with the refusal named, so the next item runs; a transient one (the remote unreadable) keeps the slot for a retry."""
    from alienintent.context_assembly.application.work_completion import CompletionResult, WorkCompletion
    first, second = planned(closing, "FIRST", "SECOND")
    monkeypatch.setattr(WorkCompletion, "record_coordinated",
                        lambda self, identity, order: CompletionResult(identity, answer, detail="fixture"))

    summary = work_run(closing)

    assert closing.state(first.id).stage is DONE and not row_done(closing, first.id)
    assert closing.fx.wip_held(first.id) is not settled
    assert roles(closing) == ["PRODUCER", "VERIFIER", "CLOSURE"] * (2 if settled else 1)
    assert summary["projection_diagnostics"][first.id].startswith(f"{first.id}: " + ("refused: " if settled else ""))
    assert answer in summary["projection_diagnostics"][first.id]


def test_a_done_whose_work_item_is_unknown_is_settled_with_the_refusal_named(closing, monkeypatch):
    """No registry identity for the DONE: permanent, so the slot is released and the next item runs."""
    first, second = planned(closing, "FIRST", "SECOND")
    identities = type(closing.fx.loaded().identities)
    find, project, projecting = identities.find, work_registry.WorkRegistry._project_completed, []

    def projected(self, identity):
        projecting.append(identity)
        try:
            return project(self, identity)
        finally:
            projecting.pop()
    monkeypatch.setattr(work_registry.WorkRegistry, "_project_completed", projected)
    monkeypatch.setattr(identities, "find",  # the identity is unknown only to the DONE projection
                        lambda self, identity: None if projecting and identity == first.id else find(self, identity))

    summary = work_run(closing)

    assert closing.state(first.id).stage is DONE and not closing.fx.wip_held(first.id)
    assert roles(closing) == ["PRODUCER", "VERIFIER", "CLOSURE"] * 2
    assert summary["projection_diagnostics"][first.id] == f"{first.id}: refused: no work item"


@pytest.mark.parametrize("history", [10, 100, 1000])
def test_a_run_reads_open_work_only_whatever_the_history(closing, monkeypatch, history):
    """`history` earlier DONE work items are recorded and journaled; a run reads none of their records, lists no work
    item records and never reads the whole journal."""
    path = launch_root(closing.fx.loaded().configuration) / "invocation-journal.jsonl"
    journal = JsonlInvocationJournal(path, lambda: 1.0)
    for number in range(history):
        closing.fx.store.commit("registry", f"factory:history-{number}", 0, {
            "stage": "DONE", "version": 4, "accepted": True, "closure": [], "candidate": None})
        journal.append({"event": "invocation-started", "work_identity": f"history-{number}",
                        "correlation_id": f"launch:history-{number}:0"})
    [item] = planned(closing, "ONLY")
    listed, read = [], []
    list_states, read_state = SQLiteOperationalStore.list_states, SQLiteOperationalStore.read_state

    def listing(self, profile, prefix=""):
        listed.append(prefix)
        return list_states(self, profile, prefix)

    def reading(self, profile, aggregate):
        read.append(aggregate)
        return read_state(self, profile, aggregate)
    whole = invocation_journal.Path.read_text

    def journal_read(self, *args, **kwargs):
        assert self != path, "the whole journal was read"
        return whole(self, *args, **kwargs)
    monkeypatch.setattr(SQLiteOperationalStore, "list_states", listing)
    monkeypatch.setattr(SQLiteOperationalStore, "read_state", reading)
    monkeypatch.setattr(invocation_journal.Path, "read_text", journal_read)

    work_run(closing)

    assert closing.state(item.id).stage is DONE
    assert not [prefix for prefix in listed if "factory:".startswith(prefix)]
    assert not [aggregate for aggregate in read if aggregate.startswith("factory:history-")]


def test_a_run_never_overlaps_a_live_launch(closing):
    """The one registry-wide launch reservation, held by a live process: the run answers LAUNCH_IN_PROGRESS and
    starts nothing."""
    planned(closing, "ONLY")
    owner = "launcher:" + json.dumps(dict(ProcOwnership().current()), sort_keys=True, separators=(",", ":"))
    closing.fx.store.acquire("registry", LAUNCH_SCOPE, LAUNCH_KEY, owner)

    assert work_run(closing, Owners("alive")) == {"answer": LAUNCH_IN_PROGRESS, "owner_state": "alive"}
    assert closing.fx.runs() == []
