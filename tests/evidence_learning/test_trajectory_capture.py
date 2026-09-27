"""FX-B1P mechanical proof: live trajectory capture over the real journal stores.

Each capture runs under an injected UTC clock over a real SQLite head pointer and a real
content-addressed evidence directory. A "kill" drops every in-memory object; a restart opens
fresh store objects over the same root, so only durably committed entries can survive it.
"""
from pathlib import Path

import pytest

from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.adapters.trajectory_journal import DurableTrajectoryJournal
from alienintent.evidence_learning.application.trajectory_capture_service import TrajectoryCaptureService, replay
from alienintent.evidence_learning.domain.trajectory_capture import (
    ANOMALY_KINDS, CAPTURE_STALL, DUPLICATE_IDENTITY, OUT_OF_ORDER, SEQUENCE_GAP, TIMESTAMP_REGRESSION, CaptureHold,
    CapturePolicy, CaptureState, Submission,
)
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.ports.operational_store import StoreUnavailable

SECOND = 1_000_000
T0 = 1_790_000_000 * SECOND
POLICY = CapturePolicy(stall_seconds=30)


class Clock:
    def __init__(self, now=T0):
        self.now = now

    def __call__(self):
        return self.now


def journal(root, store=None):
    return DurableTrajectoryJournal(store or SQLiteOperationalStore(Path(root) / "trajectory-capture.sqlite"),
                                    LocalEvidenceRepository(Path(root) / "evidence", "project", "fixture"),
                                    project="project", name="fixture", stream="fx-b1p", invocation="fx-b1p-test")


def capture(root, launch_id, clock, store=None):
    service = TrajectoryCaptureService(journal(root, store), POLICY, launch_id=launch_id, clock=clock)
    service.start()
    return service


def submission(seq, observed_at=None, source="agent-1", event_id=None, **event):
    return Submission(source, seq, T0 + seq * SECOND if observed_at is None else observed_at,
                      {"schema_version": "1.0", "event_id": event_id or f"{source}-{seq:03d}",
                       "event_type": "TOOL_CALL", **event})


def entries(root):
    return journal(root).entries()


def captured(root):
    return [e["event"] for e in entries(root) if e["kind"] == "EVENT"]


def anomalies(root):
    return [a for e in entries(root) for a in e["anomalies"]]


@pytest.fixture
def root(tmp_path):
    path = tmp_path / "capture"
    path.mkdir(mode=0o700)
    return path


# ---- (a) identity, order and timestamp assignment ----------------------------------------

def test_capture_assigns_identity_order_and_time(root):
    clock = Clock()
    service = capture(root, "launch-1", clock)
    acks = []
    for seq in (1, 2, 3):
        clock.now += SECOND
        acks.append(service.submit(submission(seq)))
    assert [(a["status"], a["capture_seq"], a["entry_seq"], a["anomalies"]) for a in acks] == [
        ("CAPTURED", 1, 2, []), ("CAPTURED", 2, 3, []), ("CAPTURED", 3, 4, [])]
    events = captured(root)
    assert [e["capture_seq"] for e in events] == [1, 2, 3]
    assert [e["captured_at"] for e in events] == [T0 + SECOND, T0 + 2 * SECOND, T0 + 3 * SECOND]
    assert [e["identity"] for e in events] == [submission(s).identity() for s in (1, 2, 3)]
    assert {e["launch_id"] for e in events} == {"launch-1"}
    assert [e["kind"] for e in entries(root)] == ["SESSION", "EVENT", "EVENT", "EVENT"]
    assert anomalies(root) == []


def test_invalid_submission_holds_without_writing(root):
    service = capture(root, "launch-1", Clock())
    for document in ({"source": "a", "source_seq": 0, "observed_at": 1, "event": {"event_id": "e", "event_type": "t"}},
                     {"source": "a", "source_seq": 1, "observed_at": 1, "event": {"event_type": "t"}},
                     {"source": "", "source_seq": 1, "observed_at": 1, "event": {"event_id": "e", "event_type": "t"}},
                     {"source": "a", "source_seq": 1, "event": {"event_id": "e", "event_type": "t"}}):
        with pytest.raises(CaptureHold) as held:
            service.submit(Submission.from_document(document))
        assert held.value.reason.startswith("SUBMISSION_INVALID")
    assert [e["kind"] for e in entries(root)] == ["SESSION"]


# ---- (c) every seeded anomaly class is a durable record -----------------------------------

def test_each_seeded_anomaly_class_is_recorded_durably(root):
    clock = Clock()
    service = capture(root, "launch-1", clock)

    def at(seconds, item):
        clock.now = T0 + seconds * SECOND
        return service.submit(item)

    at(1, submission(1))
    at(2, submission(2))
    gap = at(3, submission(5))                                        # 3 and 4 never arrive in order
    late = at(4, submission(3, observed_at=T0 + 5 * SECOND))          # arrives after 5
    duplicate = at(5, submission(2))                                   # same event identity again
    regressed = at(6, submission(6, observed_at=T0 + 1 * SECOND))      # source clock goes back
    clock.now = T0 + 5 * SECOND                                        # capture clock goes back
    capture_clock = service.submit(submission(7))
    clock.now = T0 + 6 * SECOND + POLICY.stall_micros + 1              # nothing arrives for > stall
    stalled = service.check_stall()
    assert service.check_stall() is None, "one stall record per idle interval"

    assert gap["anomalies"] == [SEQUENCE_GAP] and late["anomalies"] == [OUT_OF_ORDER]
    assert (duplicate["status"], duplicate["capture_seq"], duplicate["anomalies"]) == ("DUPLICATE", 2,
                                                                                       [DUPLICATE_IDENTITY])
    assert regressed["anomalies"] == [TIMESTAMP_REGRESSION] and capture_clock["anomalies"] == [TIMESTAMP_REGRESSION]
    assert capture_clock["captured_at"] == T0 + 6 * SECOND, "capture time never runs backwards"
    assert stalled["kind"] == "STALL"

    # Read back from fresh store objects: every class is durable, append-only evidence.
    durable = anomalies(root)
    assert sorted({a["kind"] for a in durable}) == sorted(ANOMALY_KINDS)
    by_kind = {a["kind"]: a for a in durable if a["kind"] != TIMESTAMP_REGRESSION}
    assert by_kind[SEQUENCE_GAP]["detail"] == {"expected_source_seq": 3, "source_seq": 5, "missing": 2}
    assert by_kind[OUT_OF_ORDER]["detail"] == {"high_source_seq": 5, "source_seq": 3}
    assert by_kind[DUPLICATE_IDENTITY]["detail"] == {"original_capture_seq": 2, "same_content": True, "source_seq": 2}
    assert by_kind[CAPTURE_STALL]["detail"]["idle_since"] == T0 + 6 * SECOND
    assert [a["detail"]["clock"] for a in durable if a["kind"] == TIMESTAMP_REGRESSION] == ["source", "capture"]
    assert len({a["anomaly_id"] for a in durable}) == len(durable)
    # The duplicate is detected and recorded, not captured twice; anomalous events are still captured.
    assert [e["source_seq"] for e in captured(root)] == [1, 2, 5, 3, 6, 7]


# ---- (b) and (d): no loss or duplication across a restart ---------------------------------

def test_restart_reconciles_accepted_events_without_loss_or_duplication(root):
    clock = Clock()
    first = capture(root, "launch-1", clock)
    acks = []
    for seq in (1, 2, 3, 4):
        clock.now += SECOND
        acks.append(first.submit(submission(seq)))
    before = captured(root)
    del first  # killed: nothing in memory survives

    clock.now += 10 * SECOND
    second = capture(root, "launch-2", clock)
    opened = entries(root)[-1]
    assert opened["kind"] == "SESSION" and opened["session"]["reconciled"] == {
        "entries": 5, "events": 4, "sessions": ["launch-1"],
        "sources": {"agent-1": {"high_seq": 4, "high_observed_at": T0 + 4 * SECOND}}}
    # The source never saw the ack for 4 and retries it: recorded, not captured again.
    retry = second.submit(submission(4))
    assert (retry["status"], retry["capture_seq"], retry["identity"]) == ("DUPLICATE", 4, acks[3]["identity"])
    clock.now += SECOND
    fresh = second.submit(submission(5))
    assert (fresh["capture_seq"], fresh["anomalies"]) == (5, [])

    after = captured(root)
    assert after[:4] == before, "accepted events keep identity, order and capture time across the restart"
    assert [e["source_seq"] for e in after] == [1, 2, 3, 4, 5]
    assert len({e["event_id"] for e in after}) == len(after) == 5
    assert [e["launch_id"] for e in after] == ["launch-1"] * 4 + ["launch-2"]
    assert replay(entries(root)).sessions == ["launch-1", "launch-2"]


class CommitFails:
    """The head pointer store dies after the entry object is installed."""

    def __init__(self, store):
        self.store = store

    def read_state(self, *arguments):
        return self.store.read_state(*arguments)

    def commit(self, *arguments):
        raise StoreUnavailable("killed before the pointer commit")


def test_an_unacknowledged_submission_was_never_accepted(root):
    clock = Clock()
    store = SQLiteOperationalStore(root / "trajectory-capture.sqlite")
    service = capture(root, "launch-1", clock, store)
    clock.now += SECOND
    service.submit(submission(1))
    service.journal.store = CommitFails(store)
    clock.now += SECOND
    with pytest.raises(CaptureHold) as held:
        service.submit(submission(2))
    assert held.value.reason == "JOURNAL_STORE_UNAVAILABLE"

    restarted = capture(root, "launch-2", clock)
    assert [e["source_seq"] for e in captured(root)] == [1], "an entry the pointer never named is not accepted"
    ack = restarted.submit(submission(2))
    assert (ack["status"], ack["capture_seq"]) == ("CAPTURED", 2), "the resubmission is captured once, not a duplicate"


def test_stall_is_measured_from_the_later_of_last_event_and_session_and_not_repeated(root):
    clock = Clock()
    first = capture(root, "launch-1", clock)
    clock.now += SECOND
    first.submit(submission(1))
    clock.now += POLICY.stall_micros                   # exactly the bound: not yet a stall
    assert first.check_stall() is None
    clock.now += 1
    assert first.check_stall()["anomalies"][0]["detail"]["idle_since"] == T0 + SECOND
    assert first.check_stall() is None

    clock.now += SECOND
    second = capture(root, "launch-2", clock)          # a new session restarts the idle interval
    assert second.check_stall() is None
    clock.now += POLICY.stall_micros + 1
    assert second.check_stall()["anomalies"][0]["detail"]["idle_since"] == clock.now - POLICY.stall_micros - 1
    assert [a["kind"] for a in anomalies(root)] == [CAPTURE_STALL, CAPTURE_STALL]


# ---- one writer and an intact journal ------------------------------------------------------

def test_a_second_writer_is_refused(root):
    clock = Clock()
    first = capture(root, "launch-1", clock)
    second = capture(root, "launch-2", clock)
    with pytest.raises(CaptureHold) as held:
        first.submit(submission(1))
    assert held.value.reason == "JOURNAL_VERSION_CONFLICT"
    assert second.submit(submission(1))["capture_seq"] == 1
    with pytest.raises(CaptureHold):
        capture(root, "launch-2", clock)  # a launch id opens one session only


def test_a_broken_or_inconsistent_journal_holds(root):
    clock = Clock()
    service = capture(root, "launch-1", clock)
    for seq in (1, 2):
        service.submit(submission(seq))
    objects = sorted((root / "evidence" / "objects").iterdir())
    target = next(p for p in objects if '"revision":"2"' in p.read_text())
    target.unlink()
    with pytest.raises(CaptureHold) as held:
        capture(root, "launch-2", clock)
    assert held.value.reason == "JOURNAL_ENTRY_UNREADABLE:MISSING_OBJECT"

    state = CaptureState()
    good = [e for e in (
        {"schema_version": 1, "entry_seq": 1, "kind": "SESSION", "launch_id": "l", "recorded_at": 1, "event": None,
         "anomalies": []},
        {"schema_version": 1, "entry_seq": 2, "kind": "EVENT", "launch_id": "l", "recorded_at": 2, "anomalies": [],
         "event": {"capture_seq": 1, "event_id": "e", "identity": "sha256:x", "captured_at": 2, "source": "s",
                   "source_seq": 1, "observed_at": 1}})]
    for entry in good:
        state.apply(entry)
    for bad, reason in ((good[1] | {"entry_seq": 3, "event": good[1]["event"] | {"capture_seq": 2}},
                         "JOURNAL_EVENT_DUPLICATED"),
                        (good[1] | {"entry_seq": 3, "event": good[1]["event"] | {"capture_seq": 3}},
                         "JOURNAL_EVENT_OUT_OF_SEQUENCE"),
                        (good[1], "JOURNAL_ENTRY_OUT_OF_SEQUENCE"),
                        (good[1] | {"entry_seq": 3, "launch_id": "other"}, "JOURNAL_ENTRY_NOT_IN_SESSION")):
        with pytest.raises(CaptureHold) as held:
            state.apply(bad)
        assert held.value.reason == reason


def test_source_clock_regression_is_measured_against_the_highest_reported_time(root):
    clock = Clock()
    service = capture(root, "launch-1", clock)
    kinds = [service.submit(submission(seq, observed_at=T0 + at))["anomalies"]
             for seq, at in ((1, 100), (3, 300), (2, 200), (4, 250), (5, 400))]
    # 2 is late and expected to be older (out of order only); 4 advances the order yet is older than 3.
    assert kinds == [[], [SEQUENCE_GAP], [OUT_OF_ORDER], [TIMESTAMP_REGRESSION], []]


def test_event_ids_are_unique_within_their_source_only(root):
    service = capture(root, "launch-1", Clock())
    service.submit(submission(1, source="agent-a", event_id="shared-1"))
    other = service.submit(submission(1, source="agent-b", event_id="shared-1"))
    follow = service.submit(submission(2, source="agent-b"))
    assert (other["status"], other["capture_seq"], other["anomalies"]) == ("CAPTURED", 2, [])
    assert follow["anomalies"] == [], "the other source's cursor exists; no false gap"
    assert [(e["source"], e["event_id"]) for e in captured(root)] == [
        ("agent-a", "shared-1"), ("agent-b", "shared-1"), ("agent-b", "agent-b-002")]
