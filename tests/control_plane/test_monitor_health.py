"""FX-C4: real durable store/evidence, injected UTC clock, fake scanner, no provider calls."""
from dataclasses import asdict
import gc
from hashlib import sha256
from itertools import count
import json

import pytest

LOCAL_EPISODE_END_STAND_IN = "LOCAL_EPISODE_END_STAND_IN"
SECOND = 1_000_000
T0 = 1_790_000_000 * SECOND
I = 60 * SECOND


class Clock:
    """Injected UTC microsecond clock; `None` is absent and `unreadable` raises."""

    def __init__(self, now=T0):
        self.now, self.unreadable = now, False

    def __call__(self):
        if self.unreadable:
            raise OSError("FX-C4 injected unreadable clock")
        return self.now


class LaunchSpy:
    count = 0

    def launch(self, item):
        self.count += 1
        raise AssertionError("no model launch permitted")


class FakeScanner:
    """Stand-in for the L1 scan owner; it only reports progress through the port."""

    def __init__(self, progress):
        self.progress = progress

    def run(self, clock, outcome, *, started_at=None, finished_at=None):
        if started_at is not None:
            clock.now = started_at
        self.progress.scan_started()
        if outcome is not None:
            if finished_at is not None:
                clock.now = finished_at
            self.progress.scan_finished(outcome)


def ids():
    counter = count(1)
    return lambda: f"instance-{next(counter)}"


def build(root, clock, *, interval=60, policy=..., next_id=None):
    from alienintent.composition.control_plane_profile import MonitorProfile
    from alienintent.control_plane.domain.monitor_health import MonitorPolicy
    return MonitorProfile(root, project="project", name="fixture", invocation="fx-c4",
        policy=MonitorPolicy(interval) if policy is ... else policy, clock=clock,
        next_id=next_id or ids())


def outcome(status="COMPLETE", error=None, active_work=0):
    from alienintent.execution_coordination.ports.scan_progress import ScanOutcome
    return ScanOutcome(status, error, active_work)


def started(root, clock, **options):
    """t0 = T0 is both the last tick and the last completed scan."""
    p = build(root, clock, **options)
    clock.now = T0
    p.monitor.start()
    p.monitor.tick()
    FakeScanner(p.monitor).run(clock, outcome())
    return p


def status_at(p, clock, now):
    from alienintent.control_plane.domain.monitor_health import HealthStatus
    clock.now = now
    report = p.monitor.inspect()
    assert isinstance(report.status, HealthStatus)
    return report


def actions(p):
    return [entry["observation"]["action"] for entry in p.repository.history("fixture")]


def pointer(p):
    return p.store.read_state("fixture", "monitor:fixture")


def episode(root, spy):
    """Episode-owned attention service with a model-launch spy; it never owns the monitor."""
    from alienintent.composition.control_plane_profile import AttentionProfile
    from alienintent.control_plane.domain.attention import AttentionOrigin, ResolverGrant
    from alienintent.evidence_learning.domain.refs import Ref
    root.mkdir(exist_ok=True)
    profile = AttentionProfile(root, project="project", name="fixture", invocation="fx-c4-episode",
        clock=lambda: "2026-09-25T00:00:00Z", next_id=lambda: "attempt-1",
        resolvers=(ResolverGrant("director", "authority-1", "issue:96", "rev-1", "product"),),
        activation=spy)
    profile.attention.ensure(AttentionOrigin("issue:96", "invocation:outcome-1", "DONE", "rev-1", "product",
        "authority-1", "observer", Ref("project", "fixture", "outcome-1",
        "sha256:" + sha256(b"outcome-1").hexdigest(), "fixture:outcome-1")))
    return profile


@pytest.mark.parametrize(("offset", "expected", "message"), [
    (2 * I - 1, "HEALTHY", "below 2*I the monitor stays in bound"),
    (2 * I, "HEALTHY", "at exactly 2*I the monitor stays in bound"),
    (2 * I + 1, "STALE", "above 2*I the monitor is STALE"),
], ids=["below", "at", "above"])
def test_tick_age_boundary(tmp_path, offset, expected, message):
    clock = Clock()
    p = started(tmp_path, clock)
    assert status_at(p, clock, T0 + offset).status == expected, message


def test_interval_from_policy(tmp_path):
    clock = Clock()
    p = started(tmp_path, clock, interval=7)
    assert status_at(p, clock, T0 + 14 * SECOND).status == "HEALTHY", "the 2*I bound comes from the persisted policy interval"
    assert status_at(p, clock, T0 + 14 * SECOND + 1).status == "STALE", "the 2*I bound comes from the persisted policy interval"


@pytest.mark.parametrize(("offset", "expected", "message"), [
    (2 * I, "HEALTHY", "at exactly 2*I the scan completion stays in bound"),
    (2 * I + 1, "STALE", "an overdue last scan completion is STALE"),
], ids=["at", "above"])
def test_scan_overdue_boundary(tmp_path, offset, expected, message):
    clock = Clock()
    p = started(tmp_path, clock)
    for now in range(T0 + I, T0 + offset + 1, I // 2):
        clock.now = now
        p.monitor.tick()
    clock.now = T0 + offset
    p.monitor.tick()
    report = status_at(p, clock, T0 + offset)
    assert report.record.last_monitor_tick == T0 + offset
    assert report.status == expected, message


def test_tick_overdue_with_recent_scan(tmp_path):
    clock = Clock()
    p = started(tmp_path, clock)
    FakeScanner(p.monitor).run(clock, outcome(), started_at=T0 + 2 * I, finished_at=T0 + 2 * I + 1)
    report = status_at(p, clock, T0 + 2 * I + 1)
    assert (report.status, report.reason) == ("STALE", "TICK_OVERDUE"), "a frozen tick is STALE even with a recent scan"


def test_quiet_work_is_not_health(tmp_path):
    clock = Clock()
    p = started(tmp_path, clock)
    scanner = FakeScanner(p.monitor)
    for step in range(1, 6):
        clock.now = T0 + step * I
        p.monitor.tick()
        scanner.run(clock, outcome(active_work=0))
    report = status_at(p, clock, T0 + 5 * I + 2 * I)
    assert report.status == "HEALTHY", "quiet work must not stop monitor ticks"
    assert report.record.last_monitor_tick == T0 + 5 * I, "quiet work must not stop monitor ticks"
    assert actions(p).count("TICK") == 6


def test_frozen_monitor_while_work_quiet(tmp_path):
    clock = Clock()
    p = started(tmp_path, clock)
    assert status_at(p, clock, T0 + 2 * I + 1).status == "STALE", "a frozen monitor is STALE even while work is quiet"


@pytest.mark.parametrize("case", ["failed", "evidence_hold", "started_only"])
def test_failed_or_incomplete_scan(tmp_path, case):
    clock = Clock()
    p = started(tmp_path, clock)
    result = {"failed": outcome("FAILED", "scan error: injected"),
              "evidence_hold": outcome("EVIDENCE_HOLD", "EvidenceHold: MISSING_OBJECT"),
              "started_only": None}[case]
    FakeScanner(p.monitor).run(clock, result, started_at=T0 + SECOND, finished_at=T0 + 2 * SECOND)
    report = status_at(p, clock, T0 + 3 * SECOND)
    assert report.status == "DEGRADED", "a failed or incomplete latest scan is DEGRADED"
    assert report.record.last_scan_completed_at == T0, "an incomplete scan must not advance last_scan_completed_at"
    assert report.record.last_scan_started_at == T0 + SECOND
    assert report.record.last_error == (None if result is None else result.error)


def test_stale_precedes_degraded(tmp_path):
    clock = Clock()
    p = started(tmp_path, clock)
    FakeScanner(p.monitor).run(clock, outcome("FAILED", "scan error: injected"),
                               started_at=T0 + SECOND, finished_at=T0 + 2 * SECOND)
    clock.now = T0 + 2 * I + SECOND
    p.monitor.tick()
    report = status_at(p, clock, T0 + 2 * I + SECOND)
    assert report.record.last_scan_outcome == "FAILED"
    assert report.status == "STALE", "STALE takes precedence over DEGRADED"


def test_no_record(tmp_path):
    clock = Clock()
    p = build(tmp_path, clock)
    report = status_at(p, clock, T0)
    assert report.status == "UNVERIFIED", "a missing record is UNVERIFIED"
    assert report.reason == "NO_RECORD" and report.record is None
    assert p.health.read("fixture") is None and p.store.list_states("fixture") == ()


@pytest.mark.parametrize("case", ["absent", "unreadable", "regressing", "regressing_across_restart"])
def test_clock(tmp_path, case):
    from alienintent.control_plane.domain.monitor_health import MonitorHold
    clock = Clock()
    p = started(tmp_path, clock)
    clock.now = T0 + 10 * SECOND
    p.monitor.tick()
    before = pointer(p)
    if case == "absent":
        clock.now = None
        assert p.monitor.inspect().status == "UNVERIFIED", "an absent clock is UNVERIFIED"
        reason = "CLOCK_ABSENT"
    elif case == "unreadable":
        clock.unreadable = True
        assert p.monitor.inspect().status == "UNVERIFIED", "an unreadable clock is UNVERIFIED"
        reason = "CLOCK_UNREADABLE"
    elif case == "regressing":
        clock.now = T0 + 5 * SECOND
        with pytest.raises(MonitorHold, match="CLOCK_REGRESSION"):
            p.monitor.tick()
        assert p.monitor.inspect().status == "UNVERIFIED", "a regressing clock is UNVERIFIED"
        reason = "CLOCK_REGRESSION"
    else:
        restarted_clock = Clock(T0 + 5 * SECOND)
        p = build(tmp_path, restarted_clock, next_id=lambda: "instance-restarted")
        assert p.monitor.inspect().status == "UNVERIFIED", "a clock earlier than the persisted observation is UNVERIFIED"
        clock = restarted_clock
        with pytest.raises(MonitorHold, match="CLOCK_REGRESSION"):
            p.monitor.start()
        reason = "CLOCK_REGRESSION"
    assert p.monitor.inspect().reason == reason
    with pytest.raises(MonitorHold, match="NOT_STARTED" if case == "regressing_across_restart" else reason):
        p.monitor.tick()
    assert pointer(p) == before, "a rejected clock reading must not write an observation"
    assert p.monitor.inspect().record.last_monitor_tick == T0 + 10 * SECOND


@pytest.mark.parametrize("reading", [1.5, -1, True, "2026-09-25T00:00:00Z"])
def test_clock_invalid_reading(tmp_path, reading):
    from alienintent.control_plane.domain.monitor_health import MonitorHold
    clock = Clock()
    p = started(tmp_path, clock)
    clock.now = reading
    assert (p.monitor.inspect().status, p.monitor.inspect().reason) == ("UNVERIFIED", "CLOCK_INVALID")
    with pytest.raises(MonitorHold, match="CLOCK_INVALID"):
        p.monitor.tick()


@pytest.mark.parametrize("case", ["unavailable", "schema"])
def test_store_unavailable(tmp_path, case):
    from alienintent.control_plane.domain.monitor_health import MonitorHold, Unavailable
    clock = Clock()
    p = started(tmp_path, clock)
    if case == "unavailable":
        (tmp_path / "monitor.sqlite").write_bytes(b"FX-C4 unreadable health store " * 256)
        reason = "STORE_UNAVAILABLE"
    else:
        version, _ = pointer(p)
        p.store.commit("fixture", "monitor:fixture", version, {"schema_version": 2})
        reason = "SCHEMA_INCOMPATIBLE"
    report = status_at(p, clock, T0 + SECOND)
    assert report.status == "UNVERIFIED", "an unreadable health store is UNVERIFIED"
    assert report.reason == reason and report.record is None
    assert p.health.read("fixture") == Unavailable(reason)
    with pytest.raises(MonitorHold, match=reason):
        p.monitor.tick()


def test_restart_new_generation(tmp_path):
    clock = Clock()
    first = started(tmp_path, clock).monitor.inspect().record
    clock.now = T0 + 5 * SECOND
    restarted = build(tmp_path, clock, next_id=lambda: "instance-2")
    record = restarted.monitor.start()
    assert record.generation == first.generation + 1, "restart must allocate a new generation"
    assert record.instance_id != first.instance_id, "restart must allocate a new instance"
    assert record.started_at == T0 + 5 * SECOND and record.last_monitor_tick is None
    history = restarted.repository.history("fixture")
    assert [h["record"]["generation"] for h in history] == [1, 1, 1, 1, 2]
    assert history[-2]["record"] == asdict(first), "prior generation observations stay readable"


def test_episode_end_preserves_monitor(tmp_path):
    spy = LaunchSpy()
    clock = Clock()
    p = started(tmp_path, clock)
    active = episode(tmp_path / "episode", spy)
    clock.now = T0 + 20 * SECOND
    p.monitor.tick()
    before, history = pointer(p), p.repository.history("fixture")
    record = p.monitor.inspect().record
    # LOCAL_EPISODE_END_STAND_IN: C3 EpisodeControl is not a C4 dependency, so the
    # episode ends by discarding every service/activation object and reopening.
    del p, active
    gc.collect()
    clock.now = T0 + 30 * SECOND
    reopened = build(tmp_path, clock)
    assert pointer(reopened) == before, "episode end must not reset monitor state"
    assert reopened.repository.history("fixture") == history, "episode end must not reset monitor state"
    report = reopened.monitor.inspect()
    assert report.record == record and report.status == "HEALTHY"
    assert spy.count == 0


def test_independent_of_model_and_workload(tmp_path):
    spy = LaunchSpy()
    clock = Clock()
    p = started(tmp_path, clock)
    episode(tmp_path / "episode", spy)
    scanner = FakeScanner(p.monitor)
    for step, work in enumerate((3, 0, 5, 0), start=1):
        clock.now = T0 + step * I
        p.monitor.tick()
        scanner.run(clock, outcome(active_work=work))
    report = status_at(p, clock, T0 + 4 * I + 1)
    assert report.status == "HEALTHY", "ticks and scans persist whatever the workload"
    assert actions(p) == ["STARTED"] + ["TICK", "SCAN_STARTED", "SCAN_FINISHED"] * 5
    assert [h["observation"].get("active_work") for h in p.repository.history("fixture")
            if h["observation"]["action"] == "SCAN_FINISHED"] == [0, 3, 0, 5, 0]
    assert spy.count == 0


def test_concurrent_writer_cas(tmp_path):
    from alienintent.execution_coordination.ports.operational_store import VersionConflict
    clock = Clock()
    a = started(tmp_path, clock)

    class Interleaved:
        """The scan-progress writer commits between the ticker's read and its commit."""
        fired = False

        def __call__(self):
            if not self.fired:
                self.fired = True
                a.monitor.scan_started()
            return T0 + 2 * SECOND

    a.monitor.clock = Interleaved()
    conflicts = 0
    for _ in range(2):
        try:
            a.monitor.tick()
            break
        except VersionConflict:
            conflicts += 1
    assert conflicts == 1, "a concurrent stale writer must receive exactly one VersionConflict"
    observed = [(h["observation"]["action"], h["observation"]["at"]) for h in a.repository.history("fixture")]
    assert observed[-3:] == [("SCAN_FINISHED", T0), ("SCAN_STARTED", T0 + 2 * SECOND), ("TICK", T0 + 2 * SECOND)], \
        "no monitor observation may be lost"
    assert a.monitor.inspect().record.last_scan_outcome == "STARTED"


def test_stale_instance_cannot_write(tmp_path):
    from alienintent.control_plane.domain.monitor_health import MonitorHold
    clock = Clock()
    old = started(tmp_path, clock)
    clock.now = T0 + SECOND
    build(tmp_path, clock, next_id=lambda: "instance-new").monitor.start()
    before = pointer(old)
    for write in (old.monitor.tick, old.monitor.scan_started):
        with pytest.raises(MonitorHold, match="STALE_INSTANCE"):
            write()
    assert pointer(old) == before, "a superseded instance must not write"
    assert old.monitor.inspect().record.instance_id == "instance-new"


def test_malformed_pointer_unverified(tmp_path):
    clock = Clock()
    p = started(tmp_path, clock)
    version, _ = pointer(p)
    p.store.commit("fixture", "monitor:fixture", version, {"schema_version": 1})
    report = status_at(p, clock, T0 + SECOND)
    assert (report.status, report.reason) == ("UNVERIFIED", "INVALID_MONITOR_POINTER")


@pytest.mark.parametrize("policy", ["missing", "zero", "nan"])
def test_policy_invalid_blocks_start(tmp_path, policy):
    from alienintent.control_plane.domain.monitor_health import MonitorHold, MonitorPolicy
    value = {"missing": None, "zero": 0, "nan": float("nan")}[policy]
    chosen = None
    if value is not None:
        with pytest.raises(MonitorHold, match="POLICY_INVALID"):
            MonitorPolicy(value)
        # Bypass construction so start() itself must refuse the invalid interval.
        chosen = MonitorPolicy(60)
        object.__setattr__(chosen, "interval_seconds", value)
    p = build(tmp_path, Clock(), policy=chosen)
    with pytest.raises(MonitorHold, match="POLICY_(MISSING|INVALID)"):
        p.monitor.start()
    assert p.store.list_states("fixture") == (), "a refused policy writes nothing"
    assert [o for o in p.evidence.objects.iterdir()] == []


def test_scan_finish_requires_started_attempt(tmp_path):
    from alienintent.control_plane.domain.monitor_health import MonitorHold
    from alienintent.execution_coordination.ports.scan_progress import ScanOutcomeInvalid
    clock = Clock()
    p = started(tmp_path, clock)
    with pytest.raises(MonitorHold, match="SCAN_NOT_STARTED"):
        p.monitor.scan_finished(outcome())
    for invalid in (("COMPLETE", "error"), ("FAILED", None), ("STARTED", None), ("COMPLETE", None, -1)):
        with pytest.raises(ScanOutcomeInvalid):
            outcome(*invalid)


def test_monitor_profile_composed(tmp_path):
    from alienintent.control_plane.domain.monitor_health import MonitorHealth, MonitorPolicy
    from alienintent.evidence_learning.domain.records import ref_from_document
    clock = Clock()
    p = started(tmp_path, clock)
    report = status_at(p, clock, T0 + SECOND)
    assert report.record == p.health.read("fixture"), "inspect must read the composed monitor record"
    version, stored_pointer = pointer(p)
    stored = p.evidence.get(ref_from_document(stored_pointer["history_ref"]), frozenset({"private"}))
    stored_record = MonitorHealth(**json.loads(stored.value)["record"])
    assert report.record == stored_record, "inspect must read the composed monitor record"
    assert report.status == "HEALTHY" and stored.method == "monitor-history"
    assert pointer(p) == (version, stored_pointer), "inspection is read-only"
    assert stored_record.policy_digest == MonitorPolicy(60).digest()
