"""Live trajectory capture values (B1P, WO-220610): submissions, journal entries and anomalies.

A live source submits trajectory events; the capture assigns each accepted event its identity
(a digest of exactly what was submitted), its order (a gapless `capture_seq`) and its capture
time, and appends it to one durable journal. An event is accepted exactly when its journal
entry is committed; nothing else counts as accepted. Replaying the journal through
`CaptureState.apply` rebuilds the state the live capture had, so a restarted capture
reconciles old and new observations from the journal alone.

Anomalies are detected and recorded as durable entries in the same journal; nothing here
alerts or halts. Events a source emits while the capture is down are not recovered: the next
accepted event shows them as a `SEQUENCE_GAP`. Times are integer UTC microseconds.
"""
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
import math

CAPTURE_SCHEMA = 1
SEQUENCE_GAP, OUT_OF_ORDER, DUPLICATE_IDENTITY = "SEQUENCE_GAP", "OUT_OF_ORDER", "DUPLICATE_IDENTITY"
TIMESTAMP_REGRESSION, CAPTURE_STALL = "TIMESTAMP_REGRESSION", "CAPTURE_STALL"
ANOMALY_KINDS = (SEQUENCE_GAP, OUT_OF_ORDER, DUPLICATE_IDENTITY, TIMESTAMP_REGRESSION, CAPTURE_STALL)
SESSION, EVENT, DUPLICATE, STALL = "SESSION", "EVENT", "DUPLICATE", "STALL"
ENTRY_KINDS = (SESSION, EVENT, DUPLICATE, STALL)


class CaptureHold(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "\0" not in value and "\n" not in value


def _count(value: object, minimum: int) -> bool:
    return type(value) is int and value >= minimum


def canonical(document: object) -> str:
    try:
        return json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError, RecursionError) as error:
        raise CaptureHold("SUBMISSION_INVALID:json") from error


def digest(document: object) -> str:
    return "sha256:" + sha256(canonical(document).encode()).hexdigest()


@dataclass(frozen=True)
class CapturePolicy:
    """`stall_seconds`: longest interval without an accepted event before a stall is recorded."""
    stall_seconds: int | float

    def __post_init__(self) -> None:
        if type(self.stall_seconds) not in (int, float) or not math.isfinite(self.stall_seconds) \
                or self.stall_seconds <= 0:
            raise CaptureHold("CAPTURE_CONFIGURATION_INVALID:stall_seconds")

    @property
    def stall_micros(self) -> int:
        return int(self.stall_seconds * 1_000_000)

    def document(self) -> dict[str, object]:
        return {"stall_seconds": self.stall_seconds}


@dataclass(frozen=True)
class Submission:
    """What a live source hands the capture. `event` is a trajectory event in the shape the
    offline proof writes (`trajectory.jsonl`): it names at least `event_id` and `event_type`.
    `source_seq` is the source's own 1-based order and `observed_at` its own clock."""
    source: str
    source_seq: int
    observed_at: int
    event: Mapping[str, object]

    def __post_init__(self) -> None:
        if not _text(self.source):
            raise CaptureHold("SUBMISSION_INVALID:source")
        if not _count(self.source_seq, 1):
            raise CaptureHold("SUBMISSION_INVALID:source_seq")
        if not _count(self.observed_at, 0):
            raise CaptureHold("SUBMISSION_INVALID:observed_at")
        if not isinstance(self.event, Mapping):
            raise CaptureHold("SUBMISSION_INVALID:event")
        for key in ("event_id", "event_type"):
            if not _text(self.event.get(key)):
                raise CaptureHold("SUBMISSION_INVALID:event." + key)
        canonical(dict(self.event))

    @classmethod
    def from_document(cls, document: object) -> "Submission":
        if not isinstance(document, Mapping) or set(document) != {"source", "source_seq", "observed_at", "event"}:
            raise CaptureHold("SUBMISSION_INVALID:fields")
        return cls(document["source"], document["source_seq"], document["observed_at"], document["event"])

    @property
    def event_id(self) -> str:
        return str(self.event["event_id"])

    def document(self) -> dict[str, object]:
        return {"source": self.source, "source_seq": self.source_seq, "observed_at": self.observed_at,
                "event": json.loads(canonical(dict(self.event)))}

    def identity(self) -> str:
        """The event's content identity: exactly what the source submitted."""
        return digest(self.document())


class CaptureState:
    """The fold of one capture journal. `apply` is the only transition, live and on replay."""

    def __init__(self) -> None:
        self.entries = 0
        self.events = 0
        self.last_captured_at: int | None = None
        self.idle_since: int | None = None
        self.stalled_since: int | None = None
        self.sessions: list[str] = []
        self.sources: dict[str, dict[str, int]] = {}
        # (source, event_id) -> (capture_seq, identity): an event id is unique within its source.
        self.event_ids: dict[tuple[str, str], tuple[int, str]] = {}

    def apply(self, entry: Mapping[str, object]) -> None:
        """Fold one committed entry; an entry that does not continue this state holds."""
        try:
            self._apply(entry)
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            raise CaptureHold("JOURNAL_ENTRY_INVALID") from error

    def _apply(self, entry: Mapping[str, object]) -> None:
        if not isinstance(entry, Mapping) or entry.get("schema_version") != CAPTURE_SCHEMA or entry.get("kind") not in ENTRY_KINDS:
            raise CaptureHold("JOURNAL_ENTRY_INVALID")
        if entry.get("entry_seq") != self.entries + 1:
            raise CaptureHold("JOURNAL_ENTRY_OUT_OF_SEQUENCE")
        recorded_at, kind = entry.get("recorded_at"), entry["kind"]
        if not _count(recorded_at, 0) or not _text(entry.get("launch_id")):
            raise CaptureHold("JOURNAL_ENTRY_INVALID")
        if kind != SESSION and (not self.sessions or entry["launch_id"] != self.sessions[-1]):
            raise CaptureHold("JOURNAL_ENTRY_NOT_IN_SESSION")
        if kind == SESSION:
            self.sessions.append(str(entry["launch_id"]))
            self.idle_since = recorded_at if self.idle_since is None else max(self.idle_since, recorded_at)
        elif kind == EVENT:
            event = entry.get("event")
            if not isinstance(event, Mapping) or event.get("capture_seq") != self.events + 1:
                raise CaptureHold("JOURNAL_EVENT_OUT_OF_SEQUENCE")
            key = (str(event["source"]), str(event["event_id"]))
            if key in self.event_ids:
                raise CaptureHold("JOURNAL_EVENT_DUPLICATED")
            captured_at = event.get("captured_at")
            if not _count(captured_at, 0) or (self.last_captured_at is not None and captured_at < self.last_captured_at):
                raise CaptureHold("JOURNAL_EVENT_TIME_REGRESSED")
            self.events += 1
            self.last_captured_at = captured_at
            self.idle_since = captured_at if self.idle_since is None else max(self.idle_since, captured_at)
            self.event_ids[key] = (self.events, str(event["identity"]))
            cursor = self.sources.setdefault(key[0], {"high_seq": 0, "high_observed_at": 0})
            cursor["high_seq"] = max(cursor["high_seq"], int(event["source_seq"]))
            cursor["high_observed_at"] = max(cursor["high_observed_at"], int(event["observed_at"]))
        elif kind == STALL:
            anomalies = entry.get("anomalies")
            if not isinstance(anomalies, list) or len(anomalies) != 1 or anomalies[0].get("kind") != CAPTURE_STALL:
                raise CaptureHold("JOURNAL_ENTRY_INVALID")
            self.stalled_since = anomalies[0]["detail"]["idle_since"]
        self.entries += 1


def _anomaly(entry_seq: int, index: int, kind: str, now: int, detail: dict[str, object],
             source: str | None = None, event_id: str | None = None) -> dict[str, object]:
    return {"anomaly_id": f"anomaly:{entry_seq}:{index}", "kind": kind, "detected_at": now, "source": source,
            "event_id": event_id, "detail": detail}


def _entry(state: CaptureState, kind: str, launch_id: str, now: int, **body: object) -> dict[str, object]:
    return {"schema_version": CAPTURE_SCHEMA, "entry_seq": state.entries + 1, "kind": kind, "launch_id": launch_id,
            "recorded_at": now, "event": None, "anomalies": [], **body}


def session(state: CaptureState, launch_id: str, now: int, policy: CapturePolicy) -> dict[str, object]:
    """The first entry of every hosted launch: what it reconciled from the journal it reopened."""
    if launch_id in state.sessions:
        raise CaptureHold("SESSION_ALREADY_STARTED")
    reconciled = {"entries": state.entries, "events": state.events, "sessions": list(state.sessions),
                  "sources": {k: dict(v) for k, v in sorted(state.sources.items())}}
    return _entry(state, SESSION, launch_id, now, session={"policy": policy.document(), "reconciled": reconciled})


def admit(state: CaptureState, submission: Submission, launch_id: str, now: int) -> dict[str, object]:
    """The entry that accepts `submission`, with every anomaly it shows.

    A submission naming an `event_id` its source already had captured is never captured twice: it becomes a
    `DUPLICATE` entry that points at the original. Otherwise the event is captured even when
    anomalous, so no observation is dropped by detection.
    """
    entry_seq = state.entries + 1
    anomalies: list[dict[str, object]] = []

    def flag(kind: str, **detail: object) -> None:
        anomalies.append(_anomaly(entry_seq, len(anomalies), kind, now, detail, submission.source,
                                  submission.event_id))

    identity = submission.identity()
    original = state.event_ids.get((submission.source, submission.event_id))
    if original is not None:
        flag(DUPLICATE_IDENTITY, original_capture_seq=original[0], same_content=original[1] == identity,
             source_seq=submission.source_seq)
        return _entry(state, DUPLICATE, launch_id, now, anomalies=anomalies,
                      duplicate={"original_capture_seq": original[0], "identity": identity})
    cursor = state.sources.get(submission.source)
    high_seq = 0 if cursor is None else cursor["high_seq"]
    if submission.source_seq > high_seq + 1:
        flag(SEQUENCE_GAP, expected_source_seq=high_seq + 1, source_seq=submission.source_seq,
             missing=submission.source_seq - high_seq - 1)
    elif submission.source_seq <= high_seq:
        flag(OUT_OF_ORDER, high_source_seq=high_seq, source_seq=submission.source_seq)
    # An event advancing the source's order must not be older than anything the source already
    # reported; a late (out-of-order) event is expected to be older and is not a regression.
    high_observed = None if cursor is None else cursor["high_observed_at"]
    if submission.source_seq > high_seq and high_observed is not None and submission.observed_at < high_observed:
        flag(TIMESTAMP_REGRESSION, clock="source", previous=high_observed, observed=submission.observed_at)
    captured_at = now
    if state.last_captured_at is not None and now < state.last_captured_at:
        # Capture order stays monotonic in time; the regressed reading is kept as evidence.
        flag(TIMESTAMP_REGRESSION, clock="capture", previous=state.last_captured_at, observed=now)
        captured_at = state.last_captured_at
    event = {"capture_seq": state.events + 1, "event_id": submission.event_id, "identity": identity,
             "captured_at": captured_at, "launch_id": launch_id, **submission.document()}
    return _entry(state, EVENT, launch_id, now, event=event, anomalies=anomalies)


def stall(state: CaptureState, launch_id: str, now: int, policy: CapturePolicy) -> dict[str, object] | None:
    """One `CAPTURE_STALL` per idle interval longer than the policy, measured from the later of
    the last accepted event and the current session's start."""
    since = state.idle_since
    if since is None or now - since <= policy.stall_micros or state.stalled_since == since:
        return None
    detail = {"idle_since": since, "idle_micros": now - since, "stall_micros": policy.stall_micros}
    return _entry(state, STALL, launch_id, now, anomalies=[_anomaly(state.entries + 1, 0, CAPTURE_STALL, now, detail)])
