"""FX-B1P composed proof under the unchanged C5 supervisor, with the C5 in-memory manager.

The capture host runs in-process with the cgroup the manager assigned and an injected clock;
submissions travel over a real socket pair through the same `serve` the hosted process runs.
The real per-user manager is exercised by `test_trajectory_capture_systemd.py`.
"""
import json
import socket

import pytest

from tests.control_plane.test_monitor_host import (
    ACTOR, AUTHORITY, I, PROFILE, SECOND, SESSION_CGROUP, T0, Clock, FakeManager, config_document,
)

MODULE = "alienintent.composition.trajectory_capture"


class World:
    def __init__(self, tmp_path):
        from alienintent.composition.monitor_host import load_config
        from alienintent.composition.trajectory_capture import TrajectoryCaptureProfile, load_policy
        self.root = tmp_path / "profile"
        self.root.mkdir()
        self.path = tmp_path / "trajectory-capture.json"
        self.path.write_text(json.dumps(config_document(self.root, host_invocation="fx-b1p-capture")
                                        | {"capture": {"stall_seconds": 30}}))
        self.config, self.policy = load_config(self.path), load_policy(self.path)
        self.clock, self.manager, self.ids = Clock(), FakeManager(), iter(f"launch-{n}" for n in range(1, 100))
        self.profile = TrajectoryCaptureProfile(self.config, self.path, manager=self.manager, clock=self.clock,
                                                next_id=lambda: next(self.ids))
        self.supervisor = self.profile.supervisor

    def grant(self, **changes):
        from alienintent.control_plane.domain.monitor_host import HostGrant
        binding = self.config.binding()
        return HostGrant(**dict(actor=ACTOR, authority=AUTHORITY, profile=binding.profile, unit=binding.unit,
                                host_invocation=binding.host_invocation) | changes)

    def ownership(self):
        return self.profile.records.read(PROFILE)[1]

    def host(self, cgroup=None):
        from alienintent.composition.trajectory_capture import HostedCapture
        owned = self.ownership().cgroup
        hosted = HostedCapture(self.config, self.policy, self.manager.launched[-1], clock=self.clock,
                               cgroup=lambda: cgroup or owned)
        hosted.start()
        return hosted

    def run(self, hosted, seconds):
        until = self.clock.now + seconds * SECOND
        while self.clock.now + I <= until:
            self.clock.now += I
            hosted.cycle()

    def journal(self):
        from alienintent.composition.trajectory_capture import read_journal
        return read_journal(self.config)


def send(hosted, document):
    """One submission through the hosted `serve`, as a source connected to the socket sends it."""
    from alienintent.composition.trajectory_capture import serve
    source, capture = socket.socketpair()
    with source:
        source.sendall(json.dumps(document).encode() + b"\n")
        serve(hosted.capture, capture)
        return json.loads(source.makefile().readline())


def event(seq, source="agent-1"):
    return {"source": source, "source_seq": seq, "observed_at": T0 + seq * SECOND,
            "event": {"schema_version": "1.0", "event_id": f"{source}-{seq:03d}", "event_type": "TOOL_CALL"}}


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def test_the_c5_supervisor_launches_and_observes_the_capture_host(world):
    launched = world.supervisor.launch(world.grant())
    host_argv = [c for c in world.manager.calls if c[0] == "launch"]
    assert host_argv and launched.state == "RUNNING" and launched.observer
    hosted = world.host()
    world.run(hosted, 120)
    detection, _ = world.supervisor.observe()
    assert (detection.status, detection.reason) == ("RUNNING", "OWNED_HEALTHY"), detection
    argv, _, log = world.profile.command(launched.launch_id)
    assert argv[argv.index("-m") + 1: argv.index("-m") + 5] == (MODULE, "host", "--launch-id", launched.launch_id)
    observer, _, _ = world.profile.command(None)
    assert observer[observer.index("-m") + 1: observer.index("-m") + 3] == (MODULE, "observe")
    assert log.endswith("trajectory-capture.log")


def test_the_capture_host_refuses_outside_its_owned_unit_before_opening_the_journal(world):
    from alienintent.composition.trajectory_capture import HostedCapture
    from alienintent.control_plane.domain.monitor_host import HostHold
    world.supervisor.launch(world.grant())
    for launch_id, cgroup, reason in ((world.manager.launched[-1], SESSION_CGROUP, "HOST_OUTSIDE_OWNED_UNIT"),
                                      ("launch-other", world.ownership().cgroup, "HOST_NOT_OWNED")):
        with pytest.raises(HostHold) as held:
            HostedCapture(world.config, world.policy, launch_id, clock=world.clock, cgroup=lambda c=cgroup: c)
        assert held.value.reason == reason
    assert not (world.root / "trajectory-capture.sqlite").exists()
    assert not (world.root / "trajectory-capture-evidence").exists()


def test_a_killed_capture_is_detected_and_its_granted_restart_loses_and_duplicates_nothing(world):
    world.supervisor.launch(world.grant())
    first = world.host()
    acks = [send(first, event(seq)) for seq in (1, 2, 3)]
    assert [(a["status"], a["capture_seq"]) for a in acks] == [("CAPTURED", 1), ("CAPTURED", 2), ("CAPTURED", 3)]
    world.run(first, 120)
    before = [e["event"] for e in world.journal()["entries"] if e["kind"] == "EVENT"]

    unit = world.config.binding().unit
    world.manager.terminate(unit)                                  # SIGKILL of the hosted process
    detection, alerted = world.supervisor.observe()
    assert (detection.status, detection.reason, alerted.state) == ("FAILED", "UNIT_FAILED_FAILED_SIGNAL", "ALERTED")
    restarted = world.supervisor.restart(world.grant(replaces=alerted.launch_id, alert=alerted.alert))
    second = world.host()
    world.run(second, 120)
    detection, _ = world.supervisor.observe()
    assert detection.status == "RUNNING" and restarted.launch_id != alerted.launch_id

    assert send(second, event(3))["status"] == "DUPLICATE", "a retried, already-accepted event is not captured again"
    assert send(second, event(4))["capture_seq"] == 4
    journal = world.journal()
    events = [e["event"] for e in journal["entries"] if e["kind"] == "EVENT"]
    assert events[:3] == before
    assert [e["source_seq"] for e in events] == [1, 2, 3, 4]
    assert journal["state"]["sessions"] == [alerted.launch_id, restarted.launch_id]
    sessions = [e for e in journal["entries"] if e["kind"] == "SESSION"]
    assert sessions[1]["session"]["reconciled"]["events"] == 3
    starts = [(h["record"]["instance_id"], h["record"]["generation"])
              for h in world.profile.monitor.repository.history(PROFILE) if h["observation"]["action"] == "STARTED"]
    assert starts == [(alerted.launch_id, 1), (restarted.launch_id, 2)], "the C4 generation continues"


def test_an_invalid_submission_is_answered_with_a_hold_and_writes_nothing(world):
    world.supervisor.launch(world.grant())
    hosted = world.host()
    assert send(hosted, {"source": "agent-1"}) == {"hold": "SUBMISSION_INVALID:fields"}
    assert send(hosted, event(1) | {"source_seq": 0}) == {"hold": "SUBMISSION_INVALID:source_seq"}
    assert [e["kind"] for e in world.journal()["entries"]] == ["SESSION"]
