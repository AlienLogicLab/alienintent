"""FX-C5 mechanical proof: the supervised monitor host boundary over the real C4/L1/C1 stores.

The service manager is an in-memory model of the per-user systemd manager (transient
`Restart=no` units, cgroups, invocation ids); the real manager is exercised by
`test_monitor_host_systemd.py`. The hosted monitor/scanner runs in-process under an injected
UTC clock with the cgroup the manager assigned. A local PASS is not operational acceptance.
"""
from dataclasses import replace
import json
from pathlib import Path
import shutil
import sys

import pytest

SECOND = 1_000_000
T0 = 1_790_000_000 * SECOND
I = 60 * SECOND
PROFILE = "fixture"
INVOCATION = "fx-c5-monitor"
ACTOR, AUTHORITY = "director", "monitor-host"
MANAGER_CGROUP = "/user.slice/user-1000.slice/user@1000.service"
SESSION_CGROUP = MANAGER_CGROUP + "/app.slice/alienintent-model-session.service"


class Clock:
    def __init__(self, now=T0):
        self.now = now

    def __call__(self):
        return self.now


class FakeManager:
    """Transient units as the user manager keeps them; every mutation is recorded."""

    def __init__(self):
        from alienintent.control_plane.domain.monitor_host import ManagerIdentity
        self.manager = ManagerIdentity(1000, "boot-1", "59846494", MANAGER_CGROUP)
        self.units, self.calls, self.launched, self.available, self.serial = {}, [], [], True, 0

    def identity(self):
        self.calls.append(("identity",))
        if not self.available:
            raise OSError("no user bus")
        return self.manager

    def unit_cgroup(self, manager, binding):
        return f"{manager.cgroup}/app.slice/{binding.unit}"

    def show(self, unit):
        from alienintent.control_plane.domain.monitor_host import UnitState
        return self.units.get(unit, UnitState(False, unit))

    def cgroup_empty(self, cgroup):
        return not any(u.control_group == cgroup and u.active_state == "active" for u in self.units.values())

    def launch(self, binding, argv, environment, stop_seconds, log_path):
        from alienintent.control_plane.domain.monitor_host import UNIT_PROPERTIES, UnitState
        self.calls.append(("launch", binding.unit))
        if self.show(binding.unit).loaded:
            raise RuntimeError("unit exists")
        self.serial += 1
        self.units[binding.unit] = UnitState(True, binding.unit, binding.description, f"{self.serial:032x}",
            self.unit_cgroup(self.manager, binding), "active", "running", "success", 4000 + self.serial,
            tuple(UNIT_PROPERTIES.items()))
        self.launched.append(argv[argv.index("--launch-id") + 1])

    def arm_observer(self, *args):
        raise AssertionError("not used")

    disarm_observer = arm_observer

    def terminate(self, unit):
        """The hosted process dies (SIGKILL); systemd keeps the failed unit loaded."""
        self.units[unit] = replace(self.units[unit], active_state="failed", sub_state="failed", result="signal",
                                   control_group="", main_pid=0)

    def kill(self, unit):
        self.calls.append(("kill", unit))
        self.terminate(unit)

    def stop(self, unit):
        self.calls.append(("stop", unit))
        if self.units[unit].active_state != "failed":
            del self.units[unit]

    def reset_failed(self, unit):
        self.calls.append(("reset_failed", unit))
        del self.units[unit]

    def mutations(self):
        return [c for c in self.calls if c[0] != "identity"]


def config_document(root, **overrides):
    document = {"schema_version": 1, "mode": "systemd", "project": "project", "profile": PROFILE,
        "host_invocation": INVOCATION, "root": str(root), "source_root": str(Path(__file__).resolve().parents[2] / "src"),
        "python": sys.executable, "systemd_run": shutil.which("env"), "systemctl": shutil.which("env"),
        "env": shutil.which("env"),
        "policy": {"grace_seconds": 300, "interval_seconds": 60, "confirmation_seconds": 90, "startup_seconds": 30,
                   "stop_seconds": 5, "observe_seconds": 10},
        "host_actors": [ACTOR], "host_authority": AUTHORITY, "alert_authority": "founder-judgment",
        "judgment_authority": "founder-judgment"}
    document.update(overrides)
    return document


class World:
    """One profile root: supervisor composition, the fake manager and the in-process host."""

    def __init__(self, tmp_path, **overrides):
        from alienintent.composition.monitor_host import MonitorHostProfile, load_config
        self.root = tmp_path / "profile"
        self.root.mkdir(exist_ok=True)
        self.path = tmp_path / "monitor-host.json"
        self.path.write_text(json.dumps(config_document(self.root, **overrides)))
        self.config = load_config(self.path)
        self.clock, self.manager, self.ids = Clock(), FakeManager(), iter(f"launch-{n}" for n in range(1, 100))
        self.profile = MonitorHostProfile(self.config, self.path, manager=self.manager, clock=self.clock,
                                          next_id=lambda: next(self.ids))
        self.supervisor, self.hosts = self.profile.supervisor, {}

    def grant(self, **changes):
        from alienintent.control_plane.domain.monitor_host import HostGrant
        binding = self.config.binding()
        values = dict(actor=ACTOR, authority=AUTHORITY, profile=binding.profile, unit=binding.unit,
                      host_invocation=binding.host_invocation)
        values.update(changes)
        return HostGrant(**values)

    def ownership(self):
        return self.profile.records.read(PROFILE)[1]

    def host(self, launch_id=None, cgroup=None):
        """The process the manager launched: it runs inside the owned unit's cgroup."""
        from alienintent.composition.monitor_host import HostedMonitor
        launch_id = launch_id or self.manager.launched[-1]
        owned = self.ownership().cgroup
        hosted = HostedMonitor(self.config, launch_id, clock=self.clock, cgroup=lambda: cgroup or owned)
        hosted.start()
        self.hosts[launch_id] = hosted
        return hosted

    def run(self, hosted, until):
        """The host's service loop under fake time: one tick and one scan every I."""
        while self.clock.now + I <= until:
            self.clock.now += I
            hosted.cycle()

    def seed_pending(self):
        """The canonical lifecycle stand-in records known-active work the scanner must keep."""
        from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
        from alienintent.execution_coordination.adapters.liveness_observations import StoreLifecycleJournal
        from alienintent.execution_coordination.domain.liveness import KnownActive
        store = SQLiteOperationalStore(self.root / "liveness.sqlite")
        StoreLifecycleJournal(store, profile=PROFILE).enter(
            KnownActive("item-verify", "repo:alienintent", "sha256:" + "c" * 64, "VERIFY", 1, T0, "authority:dispatch",
                        True, "candidate:item-verify"))

    def pending_state(self):
        from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
        store = SQLiteOperationalStore(self.root / "liveness.sqlite")
        return (store.list_states(PROFILE, "liveness-active:"), store.read_state(PROFILE, "liveness-policy:" + PROFILE))

    def monitor_history(self):
        return self.profile.monitor.repository.history(PROFILE)

    def running(self):
        """Launch, start the hosted process in its unit and let the observer bind it."""
        self.seed_pending()
        self.supervisor.launch(self.grant())
        hosted = self.host()
        self.run(hosted, T0 + 2 * I)
        detection, _ = self.supervisor.observe()
        assert (detection.status, detection.reason) == ("RUNNING", "OWNED_HEALTHY"), detection
        return hosted


def refusal(call):
    """The hold reason of a refused call, or None when the call was (wrongly) accepted."""
    from alienintent.control_plane.domain.monitor_host import HostHold
    try:
        call()
    except HostHold as hold:
        return hold.reason
    return None


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


# ---- class 1: supervisor external to the model session, attributable to the intended invocation ----

def test_launch_binds_the_owned_unit_to_the_monitor_invocation(world):
    from alienintent.control_plane.domain.monitor_host import HostBinding
    world.running()
    ownership = world.ownership()
    binding = HostBinding.derive(PROFILE, INVOCATION)
    record = world.profile.monitor.repository.read(PROFILE)
    assert ownership.binding == binding and ownership.cgroup == f"{MANAGER_CGROUP}/app.slice/{binding.unit}"
    assert ownership.systemd_invocation_id == world.manager.units[binding.unit].invocation_id
    # The C4 generation is attributable to exactly this supervised launch.
    assert (record.instance_id, record.generation) == (ownership.launch_id, 1)
    actions = [h["observation"]["action"] for h in world.profile.records.history(PROFILE)]
    assert actions == ["LAUNCH_INTENT", "LAUNCHED", "BOUND"]


def test_host_refuses_to_run_outside_its_owned_unit(world):
    world.seed_pending()
    world.supervisor.launch(world.grant())
    launch = world.manager.launched[-1]
    assert refusal(lambda: world.host(launch, cgroup=SESSION_CGROUP)) == "HOST_OUTSIDE_OWNED_UNIT", \
        "a process outside the owned unit (a session or shell background process) must not host the monitor"
    assert refusal(lambda: world.host("launch-not-granted")) == "HOST_NOT_OWNED"
    assert world.profile.monitor.repository.read(PROFILE) is None, \
        "a process outside the owned unit must not host the monitor"


def test_constructing_the_supervisor_launches_nothing(world):
    assert world.manager.mutations() == [] and world.ownership() is None
    assert world.profile.monitor.repository.read(PROFILE) is None


# ---- class 2: terminate or stall -> external detection/alert -> granted restart keeps state ----

def test_stalled_host_is_detected_externally_and_restart_preserves_generation_and_pending_state(world):
    hosted = world.running()
    stalled_at = world.clock.now
    before_history, before_pending = world.monitor_history(), world.pending_state()
    # Stall: the unit stays active/running, but the hosted loop makes no further progress.
    world.clock.now = stalled_at + 2 * I
    detection, ownership = world.supervisor.observe()
    assert (detection.status, ownership.state) == ("RUNNING", "RUNNING"), "exactly 2*I is still in bound"
    world.clock.now += 1
    detection, ownership = world.supervisor.observe()
    assert world.manager.show(ownership.binding.unit).running
    assert (detection.status, detection.reason) == ("FAILED", "HEALTH_STALE:TICK_OVERDUE"), \
        "a stalled host with a running unit must be detected from the durable health record"
    alert = world.profile.attention.attention.show(ownership.alert)
    assert (ownership.state, alert.status, alert.origin.kind) == ("ALERTED", "PENDING", "JUDGMENT")
    # A repeated observation of the same failure names the same alert.
    assert world.supervisor.observe()[1].alert == ownership.alert
    world.supervisor.restart(world.grant(replaces=ownership.launch_id, alert=ownership.alert))
    restarted = world.host()
    world.run(restarted, world.clock.now + I)
    record, after = world.profile.monitor.repository.read(PROFILE), world.ownership()
    assert (record.instance_id, record.generation) == (after.launch_id, 2), \
        "restart must continue the generation, not fabricate a clean start"
    detection, after = world.supervisor.observe()
    history = world.monitor_history()
    assert (detection.status, after.restart_of, after.predecessor_generation) == ("RUNNING", None, 1)
    assert history[:len(before_history)] == before_history and history[len(before_history)]["observation"]["action"] == "STARTED"
    assert world.pending_state() == before_pending, "pending known-active work must survive the restart"
    assert world.profile.attention.attention.show(ownership.alert).status == "PENDING", "restart does not resolve the alert"
    # The superseded process cannot keep writing.
    from alienintent.control_plane.domain.monitor_health import MonitorHold
    with pytest.raises(MonitorHold, match="STALE_INSTANCE"):
        hosted.cycle()


def test_terminated_host_is_detected_from_the_unit_before_health_goes_stale(world):
    world.running()
    unit = world.ownership().binding.unit
    world.manager.terminate(unit)
    detection, ownership = world.supervisor.observe()
    assert (detection.status, detection.reason, detection.health) == ("FAILED", "UNIT_FAILED_FAILED_SIGNAL", "HEALTHY"), \
        "a dead host is detected externally even while its last self-reported health is in bound"
    world.supervisor.restart(world.grant(replaces=ownership.launch_id, alert=ownership.alert))
    assert [c[0] for c in world.manager.mutations()[-3:]] == ["stop", "reset_failed", "launch"]
    world.host()
    assert world.profile.monitor.repository.read(PROFILE).generation == 2


# ---- class 3: wrong unit/invocation identity refused; no duplicate host or silent substitution ----

@pytest.mark.parametrize("change,reason", [
    ({"unit": "alienintent-monitor-" + "0" * 32 + ".service"}, "GRANT_IDENTITY_MISMATCH"),
    ({"host_invocation": "another-monitor"}, "GRANT_IDENTITY_MISMATCH"),
    ({"replaces": "launch-99"}, "RESTART_LAUNCH_MISMATCH"),
    ({"alert": "attention:" + "0" * 64}, "RESTART_ALERT_MISMATCH"),
    ({"actor": "worker"}, "GRANT_UNAUTHORIZED"),
    ({"authority": "other"}, "GRANT_UNAUTHORIZED"),
])
def test_restart_with_wrong_identity_is_refused(world, change, reason):
    world.running()
    world.manager.terminate(world.ownership().binding.unit)
    _, ownership = world.supervisor.observe()
    before, calls = world.profile.records.read(PROFILE), len(world.manager.mutations())
    grant = world.grant(**{"replaces": ownership.launch_id, "alert": ownership.alert, **change})
    assert refusal(lambda: world.supervisor.restart(grant)) == reason, \
        "a restart naming another unit, invocation, launch, alert or actor must be refused"
    assert world.profile.records.read(PROFILE) == before and len(world.manager.mutations()) == calls


def test_restart_of_a_healthy_host_or_duplicate_launch_is_refused(world):
    from alienintent.control_plane.domain.monitor_host import HostHold
    world.running()
    ownership = world.ownership()
    with pytest.raises(HostHold, match="RESTART_NOT_ALERTED"):
        world.supervisor.restart(world.grant(replaces=ownership.launch_id, alert="attention:" + "0" * 64))
    with pytest.raises(HostHold, match="HOST_ALREADY_OWNED"):
        world.supervisor.launch(world.grant())
    assert world.manager.mutations() == [("launch", ownership.binding.unit)]


def test_observation_of_a_substituted_unit_or_instance_is_refused(world):
    from alienintent.control_plane.domain.monitor_host import HostHold
    world.running()
    unit = world.ownership().binding.unit
    # Another process under the same unit name: a new manager invocation the supervisor never launched.
    world.manager.units[unit] = replace(world.manager.units[unit], invocation_id="f" * 32)
    detection, ownership = world.supervisor.observe()
    assert (detection.status, detection.reason, detection.refused) == ("REFUSED", "UNIT_INVOCATION_MISMATCH", True)
    with pytest.raises(HostHold, match="RESTART_REFUSED:UNIT_INVOCATION_MISMATCH"):
        world.supervisor.restart(world.grant(replaces=ownership.launch_id, alert=ownership.alert))
    assert ("kill", unit) not in world.manager.mutations(), "the supervisor never kills a unit it does not own"


def test_monitor_instance_not_launched_by_the_supervisor_is_refused(tmp_path):
    from alienintent.composition.control_plane_profile import MonitorProfile
    world = World(tmp_path)
    world.running()
    # A monitor started outside supervision takes over the record (silent process substitution).
    rogue = MonitorProfile(world.root, project="project", name=PROFILE, invocation="rogue",
                           policy=world.config.policy.monitor, clock=world.clock, next_id=lambda: "rogue-instance")
    rogue.monitor.start()
    detection, ownership = world.supervisor.observe()
    assert (detection.status, detection.reason, ownership.state) == ("REFUSED", "INSTANCE_NOT_OWNED", "ALERTED")


# ---- class 4: missing/invalid supervision configuration holds before launch or restart ----

@pytest.mark.parametrize("mutate,reason", [
    (lambda path, doc: path.unlink(), "SUPERVISION_CONFIGURATION_MISSING"),
    (lambda path, doc: path.write_text("{"), "SUPERVISION_CONFIGURATION_INVALID"),
    (lambda path, doc: path.write_text(json.dumps({**doc, "mode": "shell"})), "SUPERVISION_CONFIGURATION_INVALID:mode"),
    (lambda path, doc: path.write_text(json.dumps({k: v for k, v in doc.items() if k != "host_invocation"})),
     "SUPERVISION_CONFIGURATION_INVALID:host_invocation"),
    (lambda path, doc: path.write_text(json.dumps({**doc, "policy": {**doc["policy"], "interval_seconds": 0}})),
     "SUPERVISION_CONFIGURATION_INVALID:policy.interval_seconds"),
    (lambda path, doc: path.write_text(json.dumps({**doc, "host_actors": []})),
     "SUPERVISION_CONFIGURATION_INVALID:host_actors"),
    (lambda path, doc: path.write_text(json.dumps({**doc, "systemd_run": "systemd-run"})),
     "SUPERVISION_CONFIGURATION_INVALID:systemd_run"),
    (lambda path, doc: path.write_text(json.dumps({**doc, "root": doc["root"] + "-absent"})),
     "SUPERVISION_CONFIGURATION_INVALID:root"),
])
def test_missing_or_invalid_configuration_holds_before_launch(tmp_path, mutate, reason):
    from alienintent.composition.monitor_host import load_config, main
    root, path = tmp_path / "profile", tmp_path / "monitor-host.json"
    root.mkdir()
    document = config_document(root)
    path.write_text(json.dumps(document))
    load_config(path)
    mutate(path, document)
    assert refusal(lambda: load_config(path)) == reason, \
        "a missing or invalid supervision configuration must hold before launch"
    assert main(["launch", "--config", str(path), "--actor", ACTOR, "--authority", AUTHORITY]) == 2
    assert list(root.iterdir()) == [], "nothing is launched or recorded under a held configuration"


def test_supervisor_without_configuration_or_manager_holds_before_any_mutation(world):
    from alienintent.control_plane.application.monitor_supervision import MonitorHostSupervisor
    from alienintent.control_plane.domain.monitor_host import HostHold
    unconfigured = MonitorHostSupervisor(None, manager=world.manager, records=world.profile.records,
        alerts=world.profile.alerts, health=world.profile.monitor.monitor.inspect, clock=world.clock,
        next_id=lambda: "launch-x", command=world.profile.command)
    with pytest.raises(HostHold, match="SUPERVISION_CONFIGURATION_MISSING"):
        unconfigured.launch(world.grant())
    world.manager.available = False
    with pytest.raises(HostHold, match="MANAGER_UNAVAILABLE"):
        world.supervisor.launch(world.grant())
    assert world.manager.mutations() == [] and world.ownership() is None


def test_restart_under_a_changed_configuration_holds(tmp_path):
    """A configuration naming another monitor invocation cannot restart (or observe) this host."""
    from alienintent.composition.monitor_host import MonitorHostProfile, load_config
    from alienintent.control_plane.domain.monitor_host import HostGrant, HostHold
    world = World(tmp_path)
    world.running()
    world.manager.terminate(world.ownership().binding.unit)
    _, ownership = world.supervisor.observe()
    world.path.write_text(json.dumps(config_document(world.root, host_invocation="another-monitor")))
    changed = MonitorHostProfile(load_config(world.path), world.path, manager=world.manager, clock=world.clock)
    binding = changed.config.binding()
    grant = HostGrant(ACTOR, AUTHORITY, binding.profile, binding.unit, binding.host_invocation,
                      ownership.launch_id, ownership.alert)
    with pytest.raises(HostHold, match="BINDING_MISMATCH"):
        changed.supervisor.restart(grant)
    with pytest.raises(HostHold, match="BINDING_MISMATCH"):
        changed.supervisor.observe()
    assert world.ownership() == ownership
