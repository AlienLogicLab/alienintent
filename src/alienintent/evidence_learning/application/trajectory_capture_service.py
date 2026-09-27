"""Live trajectory capture (B1P, WO-220610): one writer per launch over one durable journal.

`start` reopens the journal, replays every committed entry to rebuild the capture state and
records the launch's `SESSION` entry naming what it reconciled. `submit` acknowledges an event
only after its entry is committed, so an acknowledged event survives any later kill. A retry
of an event whose acknowledgement was lost is recorded as a duplicate, never captured twice.
Nothing here waits, alerts or halts on an anomaly.
"""
from collections.abc import Callable, Mapping

from alienintent.evidence_learning.domain.trajectory_capture import (
    DUPLICATE, CaptureHold, CapturePolicy, CaptureState, Submission, admit, session, stall,
)
from alienintent.evidence_learning.ports.trajectory_journal import TrajectoryJournal


def replay(entries: tuple[Mapping[str, object], ...]) -> CaptureState:
    state = CaptureState()
    for entry in entries:
        state.apply(entry)
    return state


def acknowledgement(entry: Mapping[str, object], state: CaptureState) -> dict[str, object]:
    anomalies = [a["kind"] for a in entry["anomalies"]]
    if entry["kind"] == DUPLICATE:
        original = entry["duplicate"]["original_capture_seq"]
        anomaly = entry["anomalies"][0]
        return {"status": "DUPLICATE", "entry_seq": entry["entry_seq"], "capture_seq": original,
                "event_id": anomaly["event_id"], "identity": state.event_ids[(anomaly["source"], anomaly["event_id"])][1],
                "anomalies": anomalies}
    event = entry["event"]
    return {"status": "CAPTURED", "entry_seq": entry["entry_seq"], "capture_seq": event["capture_seq"],
            "event_id": event["event_id"], "identity": event["identity"], "captured_at": event["captured_at"],
            "anomalies": anomalies}


class TrajectoryCaptureService:
    def __init__(self, journal: TrajectoryJournal, policy: CapturePolicy, *, launch_id: str,
                 clock: Callable[[], int]) -> None:
        self.journal, self.policy, self.launch_id, self.clock = journal, policy, launch_id, clock
        self.state: CaptureState | None = None
        self.version = 0

    def _now(self) -> int:
        now = self.clock()
        if type(now) is not int or now < 0:
            raise CaptureHold("CLOCK_INVALID")
        return now

    def _state(self) -> CaptureState:
        if self.state is None:
            raise CaptureHold("CAPTURE_NOT_STARTED")
        return self.state

    def _commit(self, entry: dict[str, object]) -> dict[str, object]:
        state = self._state()
        self.version = self.journal.append(self.version, entry)
        state.apply(entry)
        return entry

    def start(self) -> dict[str, object]:
        """Reconcile from the committed journal, then open this launch's session."""
        if self.state is not None:
            raise CaptureHold("CAPTURE_ALREADY_STARTED")
        entries = self.journal.entries()
        state = replay(entries)
        self.version = self.journal.version()
        if self.version != state.entries:
            raise CaptureHold("JOURNAL_VERSION_MISMATCH")
        self.state = state
        return self._commit(session(state, self.launch_id, self._now(), self.policy))

    def submit(self, submission: Submission) -> dict[str, object]:
        state = self._state()
        entry = self._commit(admit(state, submission, self.launch_id, self._now()))
        return acknowledgement(entry, state)

    def check_stall(self) -> dict[str, object] | None:
        state = self._state()
        entry = stall(state, self.launch_id, self._now(), self.policy)
        return None if entry is None else self._commit(entry)
