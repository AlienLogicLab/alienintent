"""FX-C5 composed proof on the real per-user systemd manager (no model, provider or network).

The host is a transient manager-owned unit, the observer is a manager-owned timer running
`observe` every period, and every value asserted is read back from the durable stores. The
test process only seeds pending state, injects faults (SIGSTOP, SIGKILL) and issues grants, as
the lifecycle stand-in and the authorized operator. It is skipped where no user manager is
reachable (for example a CI runner); the FX-C5 harness records such a skip as a HOLD.
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

SRC = Path(__file__).resolve().parents[2] / "src"
PROFILE = "fixture"
ACTOR, AUTHORITY = "director", "monitor-host"
ENVIRONMENT = {**os.environ, "XDG_RUNTIME_DIR": os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"),
               "PYTHONPATH": str(SRC), "PYTHONDONTWRITEBYTECODE": "1"}


def manager_available():
    systemctl = shutil.which("systemctl")
    if not systemctl or not shutil.which("systemd-run"):
        return False
    probe = subprocess.run([systemctl, "--user", "show", "--property=ControlGroup"], env=ENVIRONMENT,
                           capture_output=True, text=True, check=False)
    return probe.returncode == 0 and probe.stdout.strip().startswith("ControlGroup=/user.slice/")


pytestmark = pytest.mark.skipif(not manager_available(), reason="FX-C5: no reachable per-user systemd manager")


def cli(config, *arguments):
    result = subprocess.run([sys.executable, "-B", "-m", "alienintent.composition.monitor_host", *arguments,
                             "--config", str(config)], env=ENVIRONMENT, capture_output=True, text=True, timeout=60)
    return result.returncode, json.loads(result.stdout.strip().splitlines()[-1])


def systemctl(*arguments):
    return subprocess.run(["systemctl", "--user", *arguments], env=ENVIRONMENT, capture_output=True, text=True,
                          check=False)


def until(predicate, timeout=30.0, what="condition"):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.1)
    raise AssertionError("timed out waiting for " + what)


class Stores:
    """Read-only views of the durable stores, opened fresh for every read."""

    def __init__(self, config):
        sys.path.insert(0, str(SRC))
        from alienintent.composition.monitor_host import MonitorHostProfile, load_config

        class Refuse:  # the reader never touches the manager
            def __getattr__(self, name):
                raise AssertionError("read-only view called the manager: " + name)

        self.profile = MonitorHostProfile(load_config(config), config, manager=Refuse())

    def ownership(self):
        return self.profile.records.read(PROFILE)[1]

    def monitor(self):
        return self.profile.monitor.repository.read(PROFILE)

    def pending(self):
        from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
        store = SQLiteOperationalStore(Path(self.profile.config.root) / "liveness.sqlite")
        return store.list_states(PROFILE, "liveness-active:"), store.read_state(PROFILE, "liveness-policy:" + PROFILE)


def seed_pending(root):
    sys.path.insert(0, str(SRC))
    from alienintent.execution_coordination.adapters.liveness_observations import StoreLifecycleJournal
    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
    from alienintent.execution_coordination.domain.liveness import KnownActive
    StoreLifecycleJournal(SQLiteOperationalStore(root / "liveness.sqlite"), profile=PROFILE).enter(
        KnownActive("item-verify", "repo:alienintent", "sha256:" + "c" * 64, "VERIFY", 1, time.time_ns() // 1000,
                    "authority:dispatch", True, "candidate:item-verify"))


def test_real_manager_supervises_detects_and_restarts_the_monitor_host(tmp_path):
    root = tmp_path / "profile"
    root.mkdir()
    config = tmp_path / "monitor-host.json"
    invocation = "fx-c5-systemd-" + uuid.uuid4().hex
    config.write_text(json.dumps({"schema_version": 1, "mode": "systemd", "project": "project", "profile": PROFILE,
        "host_invocation": invocation, "root": str(root), "source_root": str(SRC), "python": sys.executable,
        "systemd_run": shutil.which("systemd-run"), "systemctl": shutil.which("systemctl"), "env": shutil.which("env"),
        "policy": {"grace_seconds": 300, "interval_seconds": 1, "confirmation_seconds": 90, "startup_seconds": 15,
                   "stop_seconds": 5, "observe_seconds": 0.5},
        "host_actors": [ACTOR], "host_authority": AUTHORITY, "alert_authority": "founder-judgment",
        "judgment_authority": "founder-judgment"}))
    seed_pending(root)
    stores = Stores(config)
    unit = stores.profile.config.binding().unit
    observer = unit.removesuffix(".service").replace("alienintent-monitor-", "alienintent-monitor-observer-")
    readback = {"invocation": invocation, "unit": unit, "observer": observer, "stages": []}
    try:
        code, launched = cli(config, "launch", "--actor", ACTOR, "--authority", AUTHORITY)
        assert code == 0, launched
        assert cli(config, "arm-observer")[0] == 0

        def bound(generation, launch_id):
            ownership, record = stores.ownership(), stores.monitor()
            return (ownership.state == "RUNNING" and ownership.systemd_invocation_id is not None
                    and record is not None and (record.instance_id, record.generation) == (launch_id, generation)
                    and ownership.launch_id == launch_id)

        until(lambda: bound(1, launched["launch_id"]), what="the observer to bind generation 1")
        first, pending = stores.ownership(), stores.pending()
        assert len(pending[0]) == 1 and pending[1][0] == 1, pending
        readback["stages"].append({"stage": "launched", "ownership": asdict(first), "monitor": asdict(stores.monitor()),
                                   "unit": systemctl("show", unit, "-p", "ActiveState,SubState,InvocationID,ControlGroup").stdout})
        assert first.systemd_invocation_id == systemctl("show", unit, "-p", "InvocationID", "--value").stdout.strip()

        # Class 1: the same command from this (session) process is not the owned unit and refuses.
        code, outside = cli(config, "host", "--launch-id", first.launch_id)
        assert (code, outside) == (3, {"host": "REFUSED", "reason": "HOST_OUTSIDE_OWNED_UNIT"})

        # Class 2 (stall): SIGSTOP keeps the unit active; only the durable health record shows it.
        assert systemctl("kill", "--signal=SIGSTOP", "--kill-whom=all", unit).returncode == 0
        stalled = until(lambda: (o := stores.ownership()).state == "ALERTED" and o, what="stall alert")
        alerted = stores.profile.records.history(PROFILE)[-1]["observation"]
        assert stalled.alert_reason == "HEALTH_STALE:TICK_OVERDUE", stalled
        assert (alerted["unit"]["active_state"], alerted["unit"]["sub_state"]) == ("active", "running")
        readback["stages"].append({"stage": "stall_alerted", "ownership": asdict(stalled), "observation": alerted})

        # Class 3: a restart naming another launch is refused and the stalled unit is untouched.
        code, refused = cli(config, "restart", "--actor", ACTOR, "--authority", AUTHORITY,
                            "--replaces", "not-" + stalled.launch_id, "--alert", stalled.alert)
        assert (code, refused) == (2, {"hold": "RESTART_LAUNCH_MISMATCH"})
        assert systemctl("show", unit, "-p", "InvocationID", "--value").stdout.strip() == first.systemd_invocation_id
        readback["stages"].append({"stage": "wrong_identity_refused", "result": refused})

        code, second = cli(config, "restart", "--actor", ACTOR, "--authority", AUTHORITY,
                           "--replaces", stalled.launch_id, "--alert", stalled.alert)
        assert code == 0, second
        until(lambda: bound(2, second["launch_id"]), what="the observer to bind generation 2")
        readback["stages"].append({"stage": "restarted_after_stall", "ownership": asdict(stores.ownership()),
                                   "monitor": asdict(stores.monitor())})

        # Class 2 (terminate): the manager reports the dead unit before health can go stale.
        assert systemctl("kill", "--signal=SIGKILL", "--kill-whom=main", unit).returncode == 0
        killed = until(lambda: (o := stores.ownership()).state == "ALERTED" and o, what="termination alert")
        assert killed.alert_reason == "UNIT_FAILED_FAILED_SIGNAL", killed
        code, third = cli(config, "restart", "--actor", ACTOR, "--authority", AUTHORITY,
                          "--replaces", killed.launch_id, "--alert", killed.alert)
        assert code == 0, third
        until(lambda: bound(3, third["launch_id"]), what="the observer to bind generation 3")

        # Preservation: generations continue, earlier observations and pending state are kept.
        history = stores.profile.monitor.repository.history(PROFILE)
        starts = [(h["record"]["instance_id"], h["record"]["generation"]) for h in history
                  if h["observation"]["action"] == "STARTED"]
        assert starts == [(first.launch_id, 1), (second["launch_id"], 2), (third["launch_id"], 3)]
        assert stores.pending() == pending, "pending known-active work must survive both restarts"
        alerts = [stores.profile.attention.attention.show(a) for a in (stalled.alert, killed.alert)]
        assert [a.status for a in alerts] == ["PENDING", "PENDING"], "a restart never resolves its alert"
        actions = [h["observation"]["action"] for h in stores.profile.records.history(PROFILE)]
        readback["stages"].append({"stage": "final", "ownership": asdict(stores.ownership()), "monitor_starts": starts,
            "pending_state": pending, "alerts": [asdict(a) for a in alerts], "host_actions": actions,
            "observer_timer": systemctl("show", observer + ".timer", "-p", "ActiveState,Result").stdout})
        assert actions.count("ALERTED") == 2 and actions.count("RESTART_INTENT") == 2
    finally:
        systemctl("stop", observer + ".timer", observer + ".service")
        systemctl("kill", "--signal=SIGKILL", "--kill-whom=all", unit)
        systemctl("stop", unit)
        systemctl("reset-failed", unit, observer + ".service")
        readback["cleanup"] = systemctl("list-units", "--all", "--no-legend", unit, observer + ".*").stdout
        if os.environ.get("FX_C5_READBACK"):
            Path(os.environ["FX_C5_READBACK"]).write_text(json.dumps(readback, indent=2, default=str) + "\n")
    assert readback["cleanup"].strip() == ""
