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
from alienintent.context_assembly.domain.work_identity import GitReadFailed
from alienintent.control_plane.application.operator import LAUNCH_IN_PROGRESS, exclusive_run_work
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator, LAUNCH_KEY, LAUNCH_SCOPE
from alienintent.execution_coordination.domain.closure import receipt
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.domain.plan_authority import PLAN_PATH
from alienintent.composition.work_registry import launch_root
from alienintent.invocation_runtime.adapters import invocation_journal
from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal
from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
from tests.composition.test_work_registry import PLAN_QUOTE, plan_text
from tests.composition.test_worker_launch import FIXED, QUOTE, Closing, Launch, Owners, revision_of
from tests.context_assembly.test_initial_compilation import git
from tests.context_assembly.test_work_identity_service import commit_file

DONE = LifecycleStage.DONE


@pytest.fixture
def closing(tmp_path, monkeypatch) -> Closing:
    fx = Launch(tmp_path / "fx", monkeypatch)
    fx.host.write_text(json.dumps({"wipLimit": 1}))
    return Closing(fx, monkeypatch)


def planned(closing: Closing, *labels: str, scopes: dict[str, str] | None = None):
    """Plan-derived items under one approved fixture plan, READY in the order given, each scoped to its `scopes` file
    (by default launch-candidate.txt for the first, `src/<label>-candidate.txt` for the others, so later landings never
    touch them) and declaring its targeted proof file; main pushed as the landing base."""
    fx = closing.fx
    fx.proof = ["tests/test_launch_proof.py"]
    digest = fx.registry.plan_approval.approve(commit_file(fx.clone, "main", PLAN_PATH, plan_text()),
                                               PLAN_QUOTE).content_digest
    items = [fx.authorized(label, False, **FIXED, release_policy="automatic-on",
                           authority_issuer="plan-authority:" + digest,
                           authority_references=["README.md", f"{PLAN_PATH} obligation:FIXTURE"],
                           authorized_scope=[(scopes or {}).get(label, "launch-candidate.txt" if index == 0
                                                                else f"src/{label.lower()}-candidate.txt")])
             for index, label in enumerate(labels)]
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
    roles. The first landing moved main past the second's release baseline; its scope is disjoint, so its PRODUCER is
    revalidated onto the new main (WORK-PREPARATION-REFILL R2) and it lands too."""
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
    assert closing.state(second.id).stage is DONE and row_done(closing, second.id)
    assert second.id in git(closing.remote, "log", "--format=%s", f"{base}..main").decode()


def test_a_retargeted_candidate_is_built_and_verified_on_its_execution_baseline_and_keeps_its_release_baseline(
        closing):
    """WORK-PREPARATION-REFILL R2 (Founder decisions section 43): after FIRST lands, SECOND (disjoint scope, declared
    proof) is revalidated onto the new main. Its candidate's parent, its VERIFIER's starting revision and diff base and
    the regression gate's baseline are that recorded execution revision; its release baseline is unchanged."""
    first, second = planned(closing, "FIRST", "SECOND")
    release = closing.fx.loaded().context.releases.release_authorization(second.id).baseline

    work_run(closing)

    assert closing.state(second.id).stage is DONE
    producer, verifier = [run for run in closing.fx.runs() if run["package"]["identity"] == second.id][:2]
    execution = producer["package"]["execution_baseline"]
    assert (execution["release_baseline"], execution["kind"]) == (release, "retarget")
    moved = execution["execution_baseline"]
    assert moved != release and producer["package"]["starting_revision"] == moved
    assert git(closing.remote, "rev-parse", f"{verifier['head']}^").decode().strip() == moved
    assert verifier["package"]["starting_revision"] == verifier["package"]["diff"]["base"] == moved
    assert verifier["package"]["execution_baseline"] == execution
    assert verifier["package"]["release_record"]["baseline"] == release
    assert (launch_root(closing.fx.loaded().configuration) / "regression-baselines" / f"{moved}.json").exists()


def test_an_item_whose_scope_main_changed_is_held_for_re_preparation_not_retargeted(closing):
    """FIRST lands a change to the one file SECOND is scoped to: SECOND's PRODUCER is never started on the new main;
    it is held `baseline-revalidation-required` and nothing is published for it."""
    first, second = planned(closing, "FIRST", "SECOND", scopes={"SECOND": "launch-candidate.txt"})

    summary = work_run(closing)

    assert closing.state(first.id).stage is DONE
    assert [run["package"]["identity"] for run in closing.fx.runs("PRODUCER")] == [first.id]
    assert second.id in summary["authority_blocked"]
    assert closing.state(second.id).outcome == "authority-block"
    assert "baseline-revalidation-required: scope-proof-references-untouched: launch-candidate.txt" in json.dumps(
        closing.fx.store.read_state("registry", "decision-inbox")[1]["open"][second.id])
    assert second.id not in git(closing.remote, "for-each-ref", "--format=%(refname)", "refs/heads/").decode()


def _flaky_revalidation(monkeypatch, failures: int | None) -> list[str]:
    """Baseline revalidation that cannot fetch canonical main for its first `failures` calls (None: every call)."""
    calls: list[str] = []
    real = work_registry.WorkRegistry._revalidate

    def flaky(self, identity):
        calls.append(identity)
        return None if failures is None or len(calls) <= failures else real(self, identity)
    monkeypatch.setattr(work_registry.WorkRegistry, "_revalidate", flaky)
    return calls


def test_a_producer_that_cannot_fetch_canonical_main_is_retried_and_lands_with_no_founder_decision(
        closing, monkeypatch):
    """WORK-PREPARATION-REFILL R2 (Founder decisions section 44): canonical main cannot be fetched at the first
    PRODUCER revalidation. The same work item gets no Founder decision and uses no attempt; the run retries it after
    its pause and, canonical main reachable again, takes it to DONE."""
    [item] = planned(closing, "ONLY")
    calls = _flaky_revalidation(monkeypatch, 1)
    pauses = []

    summary = work_run(closing, pause=lambda: pauses.append(closing.state(item.id).outcome))

    assert pauses == ["producer-retry"] and calls == [item.id, item.id]
    assert closing.state(item.id).stage is DONE and summary["authority_blocked"] == ()
    assert not closing.fx.store.read_state("registry", "decision-inbox")[1].get("open")
    assert closing.state(item.id).record.get("rejections", 0) == 0


def test_canonical_main_unreachable_past_the_retries_holds_as_infrastructure_and_the_next_run_lands_it(
        closing, monkeypatch):
    """Past the bounded retries: a typed infrastructure hold, no Decision Inbox item, no authority block; the next
    `work run`, canonical main reachable, takes the same work item to DONE."""
    [item] = planned(closing, "ONLY")
    real = work_registry.WorkRegistry._revalidate
    _flaky_revalidation(monkeypatch, None)

    summary = work_run(closing)

    state = closing.state(item.id)
    assert (state.outcome, state.record["hold_reason"]) == (
        "infrastructure-hold", "producer-infrastructure-exhausted:canonical-main-unavailable")
    assert summary["authority_blocked"] == () and roles(closing) == []
    assert not closing.fx.store.read_state("registry", "decision-inbox")[1].get("open")
    monkeypatch.setattr(work_registry.WorkRegistry, "_revalidate", real)  # canonical main reachable again
    work_run(closing)
    assert closing.state(item.id).stage is DONE


def test_a_closure_that_cannot_fetch_canonical_main_is_retried_and_lands_with_no_founder_decision(
        closing, monkeypatch):
    """CLOSURE cannot fetch the landing remote, then cannot fetch the live plan authority (WORK-PREPARATION-REFILL R2,
    Founder decisions section 44): each is typed infrastructure on the same accepted candidate, retried after a pause
    with no Founder decision; once canonical main is reachable it lands, still under the live authority."""
    [item] = planned(closing, "ONLY")
    fetch, canonical = work_registry.RegistryClosure._fetch, work_registry.WorkRegistry._fetch
    gate = work_registry.RegistryClosure._scope_violations
    failures, inside = {"landing": 1, "authority": 1}, []

    def landing_fetch(self, clone, candidate):
        if failures["landing"]:
            failures["landing"] -= 1
            return None
        return fetch(self, clone, candidate)

    def live_main(self, repository):
        if inside and inside[-1]:  # the landing gate's fetch of the live authority, in one outage
            raise GitReadFailed("git fetch", repository, "network unreachable")
        return canonical(self, repository)

    def landing_gate(self, *args):
        inside.append(bool(failures["authority"]))
        try:
            return gate(self, *args)
        finally:
            if inside.pop():
                failures["authority"] -= 1
    monkeypatch.setattr(work_registry.RegistryClosure, "_fetch", landing_fetch)
    monkeypatch.setattr(work_registry.RegistryClosure, "_scope_violations", landing_gate)
    monkeypatch.setattr(work_registry.WorkRegistry, "_fetch", live_main)
    pauses = []

    summary = work_run(closing, pause=lambda: pauses.append(closing.state(item.id).outcome))

    assert pauses == ["closure-retry", "closure-retry"] and failures == {"landing": 0, "authority": 0}
    assert closing.state(item.id).stage is DONE and summary["authority_blocked"] == ()
    assert closing.state(item.id).record["closure_infrastructure_retries"] == 0  # "in a row": reset by the landing
    assert not closing.fx.store.read_state("registry", "decision-inbox")[1].get("open")


def test_a_candidate_fetch_failure_at_closure_is_retried_never_reworked(closing, monkeypatch):
    """CLOSURE fetches main, but the remote cannot be reached for the candidate branch (its fetch and the remote's
    answer both fail): infrastructure (`remote-unreadable`), retried on the same accepted candidate; never a rework, so
    no rejection and no attempt is used."""
    [item] = planned(closing, "ONLY")
    git_call, failing = work_registry.RegistryClosure._git, {"candidate-fetch": 1, "ls-remote": 1}

    def flaky(clone, *args, check=False):
        kind = "ls-remote" if "ls-remote" in args else \
            "candidate-fetch" if any("refs/remotes/landing/candidate" in arg for arg in args) else None
        if kind and failing[kind]:
            failing[kind] -= 1
            return False if check else ""
        return git_call(clone, *args, check=check)
    monkeypatch.setattr(work_registry.RegistryClosure, "_git", staticmethod(flaky))
    pauses = []

    work_run(closing, pause=lambda: pauses.append(closing.state(item.id).outcome))

    assert failing == {"candidate-fetch": 0, "ls-remote": 0}
    assert pauses == ["closure-retry"] and closing.state(item.id).stage is DONE
    assert closing.state(item.id).record.get("rejections", 0) == 0


def test_a_candidate_the_remote_still_advertises_but_that_did_not_arrive_is_retried(closing, monkeypatch):
    """The candidate fetch fails part way but the remote still advertises the branch at exactly the candidate:
    infrastructure, retried; never a rework."""
    [item] = planned(closing, "ONLY")
    git_call, failing = work_registry.RegistryClosure._git, [1]

    def partial(clone, *args, check=False):
        if failing and any("refs/remotes/landing/candidate" in arg for arg in args):
            failing.pop()
            return False if check else ""
        return git_call(clone, *args, check=check)
    monkeypatch.setattr(work_registry.RegistryClosure, "_git", staticmethod(partial))
    pauses = []

    work_run(closing, pause=lambda: pauses.append(closing.state(item.id).outcome))

    assert not failing and pauses == ["closure-retry"] and closing.state(item.id).stage is DONE
    assert closing.state(item.id).record.get("rejections", 0) == 0


def test_one_remote_answer_decides_an_absent_candidate(closing, monkeypatch):
    """The candidate fetch fails and the remote then answers exactly one question before it drops: that one answer
    (the branch still at the candidate) decides; a second question, going unanswered, could otherwise read as
    "answered without the candidate" and turn a transient failure into a rework."""
    [item] = planned(closing, "ONLY")
    git_call, calls = work_registry.RegistryClosure._git, []

    def fetch_fails_then_remote_drops(clone, *args, check=False):
        if any("refs/remotes/landing/candidate" in arg for arg in args) and not calls:
            calls.append("fetch")
            return False if check else ""
        if "ls-remote" in args and calls and calls[0] == "fetch" and len(calls) < 3:
            calls.append("ls-remote")
            if len(calls) == 3:  # the second question in this CLOSURE: the remote has dropped
                return False if check else ""
        return git_call(clone, *args, check=check)
    monkeypatch.setattr(work_registry.RegistryClosure, "_git", staticmethod(fetch_fails_then_remote_drops))
    pauses = []

    work_run(closing, pause=lambda: pauses.append(closing.state(item.id).outcome))

    assert calls[:2] == ["fetch", "ls-remote"] and pauses == ["closure-retry"]
    assert closing.state(item.id).stage is DONE and closing.state(item.id).record.get("rejections", 0) == 0


def test_a_candidate_branch_the_remote_no_longer_has_is_judged_never_retried_as_infrastructure(closing, monkeypatch):
    """The remote answers but no longer has the candidate branch: not infrastructure, so no `remote-unreadable` loop;
    CLOSURE reworks as before (this contract allows one attempt, so the rework ends it as a judged failure)."""
    [item] = planned(closing, "ONLY")
    fetch, deleted = work_registry.RegistryClosure._fetch, []

    def branch_gone(self, clone, candidate):
        if not deleted:
            reference = candidate.locator.rpartition("#")[2].rpartition("@")[0]
            git(closing.remote, "update-ref", "-d", f"refs/heads/{reference}")
            deleted.append(reference)
        return fetch(self, clone, candidate)
    monkeypatch.setattr(work_registry.RegistryClosure, "_fetch", branch_gone)
    pauses = []

    work_run(closing, pause=lambda: pauses.append(closing.state(item.id).outcome))

    state = closing.state(item.id)
    assert deleted and "closure-retry" not in pauses
    assert (state.outcome, state.record["hold_reason"], state.record["rejections"]) == (
        "failure", "attempt-budget-exhausted", 1)  # judged: reworked, and this contract allows one attempt


def test_a_closure_whose_remote_stays_unreadable_holds_as_infrastructure_visibly_and_never_for_the_founder(
        closing, monkeypatch):
    """Past the bounded CLOSURE retries: INFRASTRUCTURE_HOLD on the same accepted candidate, named by the run summary,
    no Decision Inbox item; the next run, the remote readable again, lands it."""
    [item] = planned(closing, "ONLY")
    fetch = work_registry.RegistryClosure._fetch
    monkeypatch.setattr(work_registry.RegistryClosure, "_fetch", lambda self, clone, candidate: None)

    summary = work_run(closing)

    state = closing.state(item.id)
    assert (state.stage.value, state.outcome, state.record["hold_reason"]) == (
        "ACCEPT", "infrastructure-hold", "closure-infrastructure-exhausted:remote-unreadable")
    assert summary["authority_blocked"] == () and summary["infrastructure_held"] == (item.id,)
    assert not closing.fx.store.read_state("registry", "decision-inbox")[1].get("open")
    monkeypatch.setattr(work_registry.RegistryClosure, "_fetch", fetch)
    work_run(closing)
    assert closing.state(item.id).stage is DONE


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


def test_one_run_cleans_the_workspaces_of_its_own_earlier_roles_and_settles_done(closing):
    """Founder 2026-10-10 (decisions section 34): one long-lived `work run` process runs PRODUCER, VERIFIER and CLOSURE
    in turn, so every earlier role's journaled owner is this live process. That process being alive is not an earlier
    role still owning its workspace: CLOSURE removes the VERIFIER clone, reads back `workspaces-cleaned` and the item
    settles DONE. Over the real process ownership: this test process is the run's owner and is alive."""
    [item] = planned(closing, "ONLY")
    verifier = launch_root(closing.fx.loaded().configuration) / "verifier"

    work_run(closing, ownership=Owners())

    state = closing.state(item.id)
    assert state.stage is DONE and row_done(closing, item.id), state.record.get("hold_reason")
    assert receipt("workspaces-cleaned", item.id, revision_of(state)) in state.record["receipts"]
    assert [p.name for p in verifier.iterdir() if p.name.startswith("verifier-")] == []


def test_an_earlier_role_of_the_same_run_whose_marked_process_is_alive_keeps_its_workspace(closing, monkeypatch):
    """The other half of the section 34 invariant: the run process being its owner does not free an earlier role's
    workspace while a marked process of that role is still alive (stated here for the cleanup only): the VERIFIER
    clone is kept, no `workspaces-cleaned` reads back and the item is not DONE."""
    [item] = planned(closing, "ONLY")
    verifier = launch_root(closing.fx.loaded().configuration) / "verifier"
    ownership = Owners()
    cleanup = work_registry.RegistryClosure._cleanup
    monkeypatch.setattr(work_registry.RegistryClosure, "_cleanup", lambda self, invocation: (
        setattr(ownership, "work", (1,)), cleanup(self, invocation))[1])

    work_run(closing, ownership=ownership)

    state = closing.state(item.id)
    assert (state.stage, state.record.get("hold_reason")) == (LifecycleStage.ACCEPT, "closure-receipts-incomplete")
    assert receipt("workspaces-cleaned", item.id, revision_of(state)) not in state.record["receipts"]
    assert [p.name for p in verifier.iterdir() if p.name.startswith("verifier-launch-")] != []

