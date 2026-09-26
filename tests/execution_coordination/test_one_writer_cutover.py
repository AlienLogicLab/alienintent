"""FX-E2 (WO-220503) LOCAL probes: one-writer cutover and nonduplicating rollback in an isolated rehearsal.

Real file writer record, checkpoint store and SQLite operational store on disposable roots. The Node
writer is represented by its `dispatcher.mjs` state file (labelled substitution); no Node process runs,
and no live state is read or written. Nothing here is operational acceptance.
"""
from copy import deepcopy
import json
from pathlib import Path
import threading

import pytest

from alienintent.composition.cutover_rehearsal import live_must_not_touch, rehearsal
from alienintent.execution_coordination.domain.cutover import (
    HELD, NODE, PYTHON, RESERVATION_SCOPE, CutoverHold, WriterRejected, pending_lanes,
)
from alienintent.execution_coordination.ports.operational_store import VersionConflict

REPO = "AlienLogicLab/rehearsal"
AT = "2026-09-27T00:00:00.000Z"


def lane(issue, role="PRODUCER"):
    return f"{REPO}#{issue}:{role}"


def resource(issue, role, invocation, lifecycle):
    return {"resourceId": invocation[-3:], "invocationId": invocation, "repository": REPO, "issue": issue,
            "role": role, "path": f"/rehearsal/worktrees/{invocation[-3:]}", "branch": f"b-disp/{invocation[-3:]}",
            "lifecycle": lifecycle, "createdAt": AT}


def node_state():
    """A quiesced Node writer state in the exact dispatcher.mjs shape (src/runtime/dispatcher.mjs)."""
    return {
        "deliveries": {"delivery-1": {"state": "PROCESSED", "at": AT}},
        "active": {
            lane(11): {"invocationId": f"{lane(11)}:aaa", "role": "PRODUCER", "status": "IMPLEMENT",
                       "startedAt": AT, "workerLogin": "worker", "result": "VERIFY"},
            lane(12): {"invocationId": f"{lane(12)}:bbb", "role": "PRODUCER", "status": "READY", "startedAt": AT},
            lane(13, "VERIFIER"): {"invocationId": f"{lane(13, 'VERIFIER')}:ccc", "role": "VERIFIER",
                                   "status": "VERIFY", "startedAt": AT, "pid": 424242, "result": "ACCEPT"},
        },
        "resources": {
            f"{lane(10)}:eee": resource(10, "PRODUCER", f"{lane(10)}:eee", "REMOVED"),
            f"{lane(11)}:aaa": resource(11, "PRODUCER", f"{lane(11)}:aaa", "REMOVED"),
            f"{lane(12)}:bbb": resource(12, "PRODUCER", f"{lane(12)}:bbb", "READY"),
            f"{lane(14)}:ddd": resource(14, "PRODUCER", f"{lane(14)}:ddd", "READY"),
        },
        "closures": {f"{lane(9, 'VERIFIER')}:fff": {"lane": lane(9, "VERIFIER"), "at": AT}},
        "diagnostics": {},
    }


class Observation:
    def __init__(self, live=(), alive=()):
        self.live = tuple(live)
        self.alive = set(alive)

    def live_node_writer(self):
        return self.live

    def pid_alive(self, pid):
        return pid in self.alive


def build(root, *, state=None, canonical_control=True, observation=None, home=None):
    root.mkdir(parents=True, exist_ok=True)
    if state is not None:
        (root / "node-state.json").write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    return rehearsal(root, canonical_control=canonical_control, home=home or root.parent / "home",
                     observation=observation or Observation())


def node_write(root, mutate):
    """Simulate the Node writer's EventRelay.save(): whole-file rewrite through an atomic rename."""
    path = root / "node-state.json"
    state = json.loads(path.read_text())
    mutate(state)
    temporary = path.with_name("node-state.json.4242.uuid.tmp")
    temporary.write_text(json.dumps(state))
    temporary.replace(path)


def reservations(cutover):
    return {r.key: r.owner for r in cutover.store.recovery_reservations(cutover.profile) if r.scope == RESERVATION_SCOPE}


def ledger(cutover):
    return {identity: (status, receipt) for identity, status, receipt in cutover.store.effect_ledger(cutover.profile)}


# E2-01
def test_isolation_refuses_live_paths_before_writing(tmp_path):
    guarded = tmp_path / "live"
    guarded.mkdir()
    for root in (guarded / "rehearsal", tmp_path):
        with pytest.raises(CutoverHold) as held:
            rehearsal(root, canonical_control=True, home=tmp_path / "home", observation=Observation(),
                      extra_must_not_touch=(guarded,))
        assert held.value.code == "ISOLATION_VIOLATION"
    assert list(guarded.iterdir()) == [], "a refused rehearsal must not write"
    home = tmp_path / "home"
    (home / ".config/alienintent").mkdir(parents=True)
    (home / ".config/alienintent/self-hosting.json").write_text(
        json.dumps({"paths": {"stateFile": str(tmp_path / "node-live/state.json")}}))
    live = live_must_not_touch(home)
    assert tmp_path / "node-live/state.json" in live and home / ".local/state/alienintent-sandbox" in live
    for root in (home / ".local/state/alienintent-sandbox/run", tmp_path / "node-live"):
        with pytest.raises(CutoverHold) as held:
            rehearsal(root, canonical_control=True, home=home, observation=Observation())
        assert held.value.code == "ISOLATION_VIOLATION"
    assert not (tmp_path / "node-live").exists()


# E2-02
def test_absent_canonical_control_keeps_node(tmp_path):
    cutover = build(tmp_path / "r", state=node_state(), canonical_control=False)
    result = cutover.cutover()
    assert result["disposition"] == "RETURN_TO_EXISTING_AUTHORITY", "absent canonical control must keep Node"
    authority = cutover.current()
    assert (authority.writer, authority.state, authority.epoch) == (NODE, "ACTIVE", 1), \
        "absent canonical control must keep Node"
    assert not (tmp_path / "r/checkpoints").exists() and reservations(cutover) == {} and ledger(cutover) == {}
    with pytest.raises(WriterRejected) as refused:
        cutover.admit(PYTHON, 1)
    assert refused.value.code == "NOT_APPROVED_WRITER"
    cutover.admit(NODE, 1)


# E2-03
def test_each_quiescence_blocker_holds_without_writer_change(tmp_path):
    cases = {
        "WORKER_RUNNING": (lambda s: None, Observation(alive={424242})),
        "PENDING_INTENT": (lambda s: s["active"][lane(12)].update(pendingSignal={"value": "VERIFY"}), Observation()),
        "RESOURCE_IN_FLIGHT": (lambda s: s["resources"][f"{lane(14)}:ddd"].update(lifecycle="RUNNING"), Observation()),
        "DELIVERY_PROCESSING": (lambda s: s["deliveries"]["delivery-1"].update(state="PROCESSING"), Observation()),
        "NODE_WRITER_PROCESS": (lambda s: None, Observation(live=("31337",))),
    }
    for index, (reason, (mutate, observation)) in enumerate(cases.items()):
        state = node_state()
        mutate(state)
        cutover = build(tmp_path / f"q{index}", state=state, observation=observation)
        try:
            cutover.cutover()
        except CutoverHold as held:
            assert held.code == "NOT_QUIESCED" and any(r.startswith(reason) for r in held.reasons)
        else:
            raise AssertionError("a pending intent must block quiescence" if reason == "PENDING_INTENT"
                                 else f"{reason} must block quiescence")
        authority = cutover.current()
        assert (authority.writer, authority.epoch) == (NODE, 1)
        assert not (tmp_path / f"q{index}/checkpoints").exists()
    assert build(tmp_path / "quiet", state=node_state()).cutover()["disposition"] == "CUTOVER"


# E2-04
def test_checkpoint_binds_both_stores_and_tamper_holds(tmp_path):
    cutover = build(tmp_path / "r", state=node_state())
    result = cutover.cutover()
    checkpoint = tmp_path / "r/checkpoints" / result["checkpoint"]
    manifest = cutover.checkpoints.verify(result["checkpoint"])
    assert set(manifest["members"]) == {"node-state.json", "python-store.sqlite"}
    assert json.loads((checkpoint / "node-state.json").read_text()) == node_state()
    tampered = json.loads((checkpoint / "node-state.json").read_text())
    tampered["active"].pop(lane(12))
    (checkpoint / "node-state.json").write_text(json.dumps(tampered))
    for step in (lambda: cutover.checkpoints.verify(result["checkpoint"]), cutover.rollback):
        try:
            step()
        except CutoverHold as held:
            assert held.code == "CHECKPOINT_CORRUPT"
        else:
            raise AssertionError("a tampered checkpoint must hold")
    assert cutover.current().writer != NODE, "a tampered checkpoint must hold"
    (checkpoint / "python-store.sqlite").unlink()
    with pytest.raises(CutoverHold, match="CHECKPOINT_CORRUPT"):
        cutover.checkpoints.verify(result["checkpoint"])


# E2-05
def test_reconciliation_maps_every_record_once_and_is_durable(tmp_path):
    cutover = build(tmp_path / "r", state=node_state())
    result = cutover.cutover()
    record = cutover.reconciliation(result["epoch"] - 1)
    assert record == result["reconciliation"]
    assert {tuple(r) for r in record["reservations"]} == {(lane(12), f"{lane(12)}:bbb"), (lane(14), f"{lane(14)}:ddd")}
    assert {e[0] for e in record["effects"]} == {f"node-effect:{lane(11)}:aaa", f"node-effect:{lane(13, 'VERIFIER')}:ccc",
                                                 f"node-closure:{lane(9, 'VERIFIER')}:fff"}
    assert sorted(record["terminal"]) == [f"{lane(10)}:eee", f"{lane(11)}:aaa"] and record["ambiguous"] == []
    assert all(ledger(cutover)[e[0]] == ("confirmed", e[2]) for e in record["effects"])
    assert len(ledger(cutover)) == 3
    fresh = build(tmp_path / "r")
    assert fresh.reconciliation(result["epoch"] - 1) == record and reservations(fresh) == reservations(cutover)
    ambiguous = node_state()
    ambiguous["active"][lane(15)] = {"invocationId": f"{lane(15)}:ggg", "role": "PRODUCER", "status": "IMPLEMENT",
                                     "startedAt": AT, "pid": 5150}
    held = build(tmp_path / "a", state=ambiguous)
    with pytest.raises(CutoverHold) as refused:
        held.cutover()
    assert refused.value.code == "RECONCILIATION_AMBIGUOUS" and refused.value.reasons == (lane(15),)
    assert held.current().writer == NODE and reservations(held) == {}


# E2-06
def test_pending_reservations_retained_through_cutover_and_rollback(tmp_path):
    original = node_state()
    cutover = build(tmp_path / "r", state=original)
    result = cutover.cutover()
    assert reservations(cutover) == {lane(12): f"node-migrated:{lane(12)}:bbb",
                                     lane(14): f"node-migrated:{lane(14)}:ddd"}, "every pending reservation must be retained"
    cutover.rollback()
    restored = json.loads((tmp_path / "r/node-state.json").read_text())
    assert set(pending_lanes(restored)) == {lane(12), lane(14)}, "every pending reservation must be retained"
    assert restored == original


# E2-07
def test_one_writer_admission_race_and_node_writer_detection(tmp_path):
    cutover = build(tmp_path / "r", state=node_state())
    epoch = cutover.cutover()["epoch"]
    for writer, at in ((NODE, epoch), (NODE, 1)):
        try:
            cutover.admit(writer, at)
        except WriterRejected as refused:
            assert refused.code == "NOT_APPROVED_WRITER"
        else:
            raise AssertionError("the non-approved writer must be refused")
    cutover.admit(PYTHON, epoch)
    with pytest.raises(WriterRejected, match="STALE_EPOCH"):
        cutover.admit(PYTHON, epoch - 1)

    racers = [build(tmp_path / "race", state=node_state())]
    racers.append(build(tmp_path / "race"))
    barrier, outcomes = threading.Barrier(2), []

    def race(controller):
        barrier.wait()
        try:
            outcomes.append(controller.cutover()["disposition"])
        except (VersionConflict, CutoverHold, FileExistsError) as error:
            outcomes.append(type(error).__name__)
    threads = [threading.Thread(target=race, args=(r,)) for r in racers]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert outcomes.count("CUTOVER") == 1, outcomes
    assert racers[0].current().writer == PYTHON

    node_write(tmp_path / "r", lambda s: s["active"].update({lane(16): {"invocationId": f"{lane(16)}:hhh"}}))
    with pytest.raises(WriterRejected, match="HELD"):
        cutover.admit(PYTHON, epoch)
    authority = cutover.current()
    assert authority.state == HELD and authority.writer is None and "NODE_STATE_CHANGED" in authority.reason
    for writer, at in ((PYTHON, epoch), (NODE, authority.epoch), (PYTHON, authority.epoch)):
        with pytest.raises(WriterRejected, match="HELD"):
            cutover.admit(writer, at)


# E2-08
def test_rollback_never_redispatches_python_completed_work(tmp_path):
    original = node_state()
    cutover = build(tmp_path / "r", state=original)
    epoch = cutover.cutover()["epoch"]
    effect = cutover.python_dispatch(lane(12), epoch)
    assert ledger(cutover)[effect] == ("confirmed", f"outcome:{lane(12)}")
    result = cutover.rollback()
    restored_bytes = (tmp_path / "r/node-state.json").read_bytes()
    restored = json.loads(restored_bytes)
    assert lane(12) not in pending_lanes(restored), "a lane Python completed must not be re-dispatchable after rollback"
    assert lane(12) not in restored["active"], "a lane Python completed must not be re-dispatchable after rollback"
    assert result["disposition"] == "ROLLED_BACK" and result["rollback"]["completed_by_python"] == {lane(12): effect}
    assert restored["resources"][f"{lane(12)}:bbb"]["lifecycle"] == "REMOVED"
    assert effect in restored["resources"][f"{lane(12)}:bbb"]["cleanupDiagnostic"]
    assert pending_lanes(restored) == (lane(14),)
    assert restored["resources"][f"{lane(14)}:ddd"] == original["resources"][f"{lane(14)}:ddd"]
    for key in (lane(11), lane(13, "VERIFIER")):
        assert restored["active"][key] == original["active"][key]
    assert restored["closures"] == original["closures"] and restored["deliveries"] == original["deliveries"]
    python_effects = [e for e in ledger(cutover) if e.startswith("python-effect:")]
    assert python_effects == [effect]
    authority = cutover.current()
    assert (authority.writer, authority.state) == (NODE, "ACTIVE")
    cutover.admit(NODE, authority.epoch)
    again = cutover.rollback()
    assert again["disposition"] == "NODE_ALREADY_ACTIVE" and (tmp_path / "r/node-state.json").read_bytes() == restored_bytes
    assert cutover.current() == authority and reservations(cutover) == {}


# E2-09
def test_rollback_stops_python_first_and_holds_on_unreconciled_effects(tmp_path):
    cutover = build(tmp_path / "r", state=node_state())
    epoch = cutover.cutover()["epoch"]
    unknown = cutover.python_dispatch(lane(12), epoch, confirm=False)
    before = (tmp_path / "r/node-state.json").read_bytes()
    try:
        cutover.rollback()
    except CutoverHold as held:
        assert held.code == "PYTHON_EFFECTS_UNRECONCILED" and unknown in held.reasons
    else:
        raise AssertionError("Node must stay disabled while Python effects are unreconciled")
    authority = cutover.current()
    assert (authority.state, authority.writer, authority.epoch) == (HELD, None, epoch + 1), \
        "Node must stay disabled while Python effects are unreconciled"
    assert (tmp_path / "r/node-state.json").read_bytes() == before
    for writer in (NODE, PYTHON):
        with pytest.raises(WriterRejected, match="HELD"):
            cutover.admit(writer, authority.epoch)
    cutover.store.confirm_effect(cutover.profile, unknown, f"outcome:{lane(12)}")
    reservation = [r for r in cutover.store.recovery_reservations(cutover.profile) if r.key == lane(12)][0]
    cutover.store.release(cutover.profile, RESERVATION_SCOPE, lane(12), reservation.owner, reservation.fence)
    result = cutover.rollback()
    assert result["disposition"] == "ROLLED_BACK" and result["epoch"] == epoch + 2

    second = build(tmp_path / "p", state=node_state())
    epoch = second.cutover()["epoch"]
    second.python_reserve(lane(20), epoch)
    with pytest.raises(CutoverHold, match="PYTHON_EFFECTS_UNRECONCILED"):
        second.rollback()
    assert second.current().writer is None


# E2-10
def test_fresh_controller_reads_identical_durable_state(tmp_path):
    cutover = build(tmp_path / "r", state=node_state())
    result = cutover.cutover()
    fresh = build(tmp_path / "r")
    assert fresh.current() == cutover.current()
    assert fresh.current().checkpoint == result["checkpoint"]
    assert fresh.reconciliation(result["epoch"] - 1) == result["reconciliation"]
    assert ledger(fresh) == ledger(cutover) and reservations(fresh) == reservations(cutover)
    fresh.admit(PYTHON, result["epoch"])
    snapshot = deepcopy(fresh.current())
    fresh.rollback()
    assert build(tmp_path / "r").current() == fresh.current() != snapshot
