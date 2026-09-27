"""FX-B1P composed proof on the real per-user systemd manager (no model, provider or network).

The capture host is the C5-supervised transient unit and the C5 observer timer watches it. The
test process is the synthetic live source (it connects to the capture socket), the fault
injector (SIGKILL) and the authorized operator (the restart grant). Every value asserted is
read back from the durable journal by a fresh reader. It is skipped where no user manager is
reachable (for example a CI runner); the FX-B1P harness records such a skip as a HOLD.
"""
from dataclasses import asdict
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

import pytest

from tests.control_plane.test_monitor_host_systemd import ENVIRONMENT, SRC, manager_available, systemctl, until

PROFILE = "fixture"
ACTOR, AUTHORITY = "director", "trajectory-capture-host"
STALL_SECONDS = 2
KINDS = ("SEQUENCE_GAP", "OUT_OF_ORDER", "DUPLICATE_IDENTITY", "TIMESTAMP_REGRESSION", "CAPTURE_STALL")

pytestmark = pytest.mark.skipif(not manager_available(), reason="FX-B1P: no reachable per-user systemd manager")


def cli(config, *arguments):
    result = subprocess.run([sys.executable, "-B", "-m", "alienintent.composition.trajectory_capture", *arguments,
                             "--config", str(config)], env=ENVIRONMENT, capture_output=True, text=True, timeout=60)
    return result.returncode, json.loads(result.stdout.strip().splitlines()[-1])


def event(seq, observed=None, source="agent-1"):
    return {"source": source, "source_seq": seq, "observed_at": 1_790_000_000_000_000 + (observed or seq) * 1_000_000,
            "event": {"schema_version": "1.0", "event_id": f"{source}-{seq:03d}", "event_type": "TOOL_CALL",
                      "actor_role": "FACTORY", "description": f"synthetic FX-B1P event {seq}"}}


def test_real_manager_capture_survives_kill_and_restart(tmp_path):
    sys.path.insert(0, str(SRC))
    from alienintent.composition.monitor_host import load_config
    from alienintent.composition.trajectory_capture import (
        TrajectoryCaptureProfile, read_journal, socket_path, submit,
    )

    root = tmp_path / "p"
    root.mkdir(mode=0o700)
    config = tmp_path / "capture.json"
    invocation = "fx-b1p-systemd-" + uuid.uuid4().hex
    config.write_text(json.dumps({"schema_version": 1, "mode": "systemd", "project": "project", "profile": PROFILE,
        "host_invocation": invocation, "root": str(root), "source_root": str(SRC), "python": sys.executable,
        "systemd_run": shutil.which("systemd-run"), "systemctl": shutil.which("systemctl"), "env": shutil.which("env"),
        "policy": {"grace_seconds": 300, "interval_seconds": 1, "confirmation_seconds": 90, "startup_seconds": 15,
                   "stop_seconds": 5, "observe_seconds": 0.5},
        "host_actors": [ACTOR], "host_authority": AUTHORITY, "alert_authority": "founder-judgment",
        "judgment_authority": "founder-judgment", "capture": {"stall_seconds": STALL_SECONDS}}))

    class Refuse:  # the reader never touches the manager
        def __getattr__(self, name):
            raise AssertionError("read-only view called the manager: " + name)

    loaded = load_config(config)
    profile = TrajectoryCaptureProfile(loaded, config, manager=Refuse())
    unit = loaded.binding().unit
    observer = unit.removesuffix(".service").replace("alienintent-monitor-", "alienintent-monitor-observer-")
    sock = socket_path(loaded)
    readback = {"invocation": invocation, "unit": unit, "observer": observer, "stages": [], "acks": []}

    def ownership():
        return profile.records.read(PROFILE)[1]

    def journal():
        return read_journal(loaded)

    def session_of(launch_id):
        try:
            return any(e["kind"] == "SESSION" and e["launch_id"] == launch_id for e in journal()["entries"]) \
                and sock.exists()
        except Exception:
            return False

    def send(document):
        ack = submit(sock, document)
        readback["acks"].append({"submitted": document["event"]["event_id"], "source_seq": document["source_seq"],
                                 "ack": ack})
        return ack

    try:
        code, launched = cli(config, "launch", "--actor", ACTOR, "--authority", AUTHORITY)
        assert code == 0, launched
        until(lambda: session_of(launched["launch_id"]), what="the capture session of launch 1")
        until(lambda: (o := ownership()).state == "RUNNING" and o.systemd_invocation_id, what="launch bound")

        # Outside its owned unit the capture host refuses before opening the journal.
        code, outside = cli(config, "host", "--launch-id", launched["launch_id"])
        assert (code, outside) == (3, {"host": "REFUSED", "reason": "HOST_OUTSIDE_OWNED_UNIT"})

        # Seeded stream: in order, gap, out of order, duplicate identity, source timestamp regression.
        acks = [send(event(s)) for s in (1, 2, 3)]
        acks.append(send(event(6)))                       # SEQUENCE_GAP (4, 5 missing)
        acks.append(send(event(4, observed=6)))           # OUT_OF_ORDER
        acks.append(send(event(2)))                       # DUPLICATE_IDENTITY, not captured again
        acks.append(send(event(7, observed=1)))           # TIMESTAMP_REGRESSION (source clock)
        assert [a["anomalies"] for a in acks] == [[], [], [], ["SEQUENCE_GAP"], ["OUT_OF_ORDER"],
                                                  ["DUPLICATE_IDENTITY"], ["TIMESTAMP_REGRESSION"]], acks
        # CAPTURE_STALL: the source goes quiet for longer than the configured interval.
        stall = until(lambda: [a for e in journal()["entries"] for a in e["anomalies"] if a["kind"] == "CAPTURE_STALL"],
                      timeout=STALL_SECONDS * 5, what="the capture stall record")
        assert len(stall) == 1 and stall[0]["detail"]["stall_micros"] == STALL_SECONDS * 1_000_000
        before = journal()
        readback["stages"].append({"stage": "seeded", "ownership": asdict(ownership()), "journal": before})

        # Fault: SIGKILL the capture process. The manager reports it dead; the observer alerts.
        assert systemctl("kill", "--signal=SIGKILL", "--kill-whom=main", unit).returncode == 0
        killed = until(lambda: (o := ownership()).state == "ALERTED" and o, what="the termination alert")
        assert killed.alert_reason == "UNIT_FAILED_FAILED_SIGNAL", killed
        try:
            submit(sock, event(8))
            down = "ACCEPTED"
        except OSError as error:
            down = type(error).__name__  # nothing is accepted, or buffered, while the capture is down
        assert down != "ACCEPTED"
        readback["stages"].append({"stage": "killed", "ownership": asdict(killed), "submission_while_down": down})

        code, restarted = cli(config, "restart", "--actor", ACTOR, "--authority", AUTHORITY,
                              "--replaces", killed.launch_id, "--alert", killed.alert)
        assert code == 0, restarted
        until(lambda: session_of(restarted["launch_id"]), what="the capture session of launch 2")

        retry = send(event(7, observed=1))                # the source retries its last event
        fresh = send(event(9))                            # 8 was emitted while the capture was down
        assert (retry["status"], retry["capture_seq"], retry["identity"]) == (
            "DUPLICATE", acks[-1]["capture_seq"], acks[-1]["identity"])
        assert (fresh["status"], fresh["anomalies"]) == ("CAPTURED", ["SEQUENCE_GAP"])

        after = journal()
        captured_before = [e["event"] for e in before["entries"] if e["kind"] == "EVENT"]
        captured_after = [e["event"] for e in after["entries"] if e["kind"] == "EVENT"]
        # (a) identity, order and capture time of every accepted event are unchanged by the restart.
        assert captured_after[:len(captured_before)] == captured_before
        assert [e["capture_seq"] for e in captured_after] == list(range(1, len(captured_after) + 1))
        assert all(x["captured_at"] <= y["captured_at"] for x, y in zip(captured_after, captured_after[1:]))
        # (b) every acknowledged event is present exactly once, with its acknowledged identity.
        accepted = {a["ack"]["event_id"]: a["ack"] for a in readback["acks"] if a["ack"]["status"] == "CAPTURED"}
        by_id = {e["event_id"]: e for e in captured_after}
        assert len(by_id) == len(captured_after), "no event is captured twice"
        assert set(by_id) == set(accepted)
        assert all((by_id[k]["capture_seq"], by_id[k]["identity"], by_id[k]["captured_at"]) ==
                   (v["capture_seq"], v["identity"], v["captured_at"]) for k, v in accepted.items())
        # (c) + (d) every seeded anomaly class is a durable record, readable after the restart.
        kinds = {a["kind"] for e in after["entries"] for a in e["anomalies"]}
        assert set(KINDS) <= kinds, kinds
        sessions = [e for e in after["entries"] if e["kind"] == "SESSION"]
        assert [s["launch_id"] for s in sessions] == [launched["launch_id"], restarted["launch_id"]]
        assert sessions[1]["session"]["reconciled"]["events"] == len(captured_before)
        assert sessions[1]["session"]["reconciled"]["entries"] == len(before["entries"])
        starts = [(h["record"]["instance_id"], h["record"]["generation"])
                  for h in profile.monitor.repository.history(PROFILE) if h["observation"]["action"] == "STARTED"]
        assert starts == [(launched["launch_id"], 1), (restarted["launch_id"], 2)]
        readback["stages"].append({"stage": "restarted", "ownership": asdict(ownership()), "journal": after,
                                   "monitor_starts": starts, "anomaly_kinds": sorted(kinds)})
    finally:
        systemctl("stop", observer + ".timer", observer + ".service")
        systemctl("kill", "--signal=SIGKILL", "--kill-whom=all", unit)
        systemctl("stop", unit)
        systemctl("reset-failed", unit, observer + ".service")
        readback["cleanup"] = systemctl("list-units", "--all", "--no-legend", unit, observer + ".*").stdout
        if os.environ.get("FX_B1P_READBACK"):
            Path(os.environ["FX_B1P_READBACK"]).write_text(json.dumps(readback, indent=2, default=str) + "\n")
    assert readback["cleanup"].strip() == ""
