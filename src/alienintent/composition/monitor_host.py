"""C5 supervised monitor host composition (WO-220305): the hosted monitor/scanner process, its
external supervisor and the manager-timer observer. Local/composed only.

- `host` is the monitor/scanner process. It runs only as the supervisor-owned unit for its exact
  launch id: it refuses to write if the ownership record names another launch or if its own
  cgroup is not the owned unit's (a session or shell background process cannot host it). It
  reopens the profile stores, starts C4 generation n+1 with the launch id as instance id, starts
  the L1 reconciler (reopening pending state) and ticks and scans every I.
- `launch`, `observe` and `restart` are the supervisor. `arm-observer` installs a manager-owned
  timer that runs `observe` every period, independent of the model session and of the host.
- Nothing here claims operational replacement, bootstrap retirement, live G+I or cutover.
"""
from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from itertools import count
import json
import os
from pathlib import Path
import signal
import sys
import time
import uuid

from alienintent.composition.control_plane_profile import AttentionProfile, MonitorProfile
from alienintent.composition.liveness_profile import LivenessProfile
from alienintent.control_plane.adapters.monitor_host_alerts import AttentionHostAlerts
from alienintent.control_plane.adapters.monitor_host_repository import DurableHostRecords
from alienintent.control_plane.adapters.systemd_host_manager import SystemdHostManager
from alienintent.control_plane.application.monitor_supervision import MonitorHostSupervisor
from alienintent.control_plane.domain.monitor_health import MonitorHold
from alienintent.control_plane.domain.monitor_host import HostGrant, HostHold, SupervisionConfig
from alienintent.control_plane.ports.monitor_host import HostManager
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.domain.liveness import LivenessPolicy

MODULE = "alienintent.composition.monitor_host"
EXIT_HOLD, EXIT_REFUSED, EXIT_SUPERSEDED = 2, 3, 4


def utc_micros() -> int:
    return time.time_ns() // 1_000


def load_config(path: Path | str | None) -> SupervisionConfig:
    """Missing or invalid configuration holds before anything is launched, restarted or written."""
    if path is None:
        raise HostHold("SUPERVISION_CONFIGURATION_MISSING")
    try:
        document = json.loads(Path(path).read_text())
    except FileNotFoundError as error:
        raise HostHold("SUPERVISION_CONFIGURATION_MISSING") from error
    except (OSError, ValueError) as error:
        raise HostHold("SUPERVISION_CONFIGURATION_INVALID") from error
    config = SupervisionConfig.from_document(document)
    for key in ("root", "source_root"):
        if not Path(getattr(config, key)).is_dir():
            raise HostHold("SUPERVISION_CONFIGURATION_INVALID:" + key)
    for key in ("python", "systemd_run", "systemctl", "env"):
        if not os.access(getattr(config, key), os.X_OK):
            raise HostHold("SUPERVISION_CONFIGURATION_INVALID:" + key)
    return config


def host_records(config: SupervisionConfig, invocation: str) -> DurableHostRecords:
    root = Path(config.root)
    return DurableHostRecords(SQLiteOperationalStore(root / "monitor-host.sqlite"),
                              LocalEvidenceRepository(root / "monitor-host-evidence", config.project, config.profile),
                              project=config.project, name=config.profile, invocation=invocation)


def attention(config: SupervisionConfig, invocation: str, clock: Callable[[], int]) -> AttentionProfile:
    attempts = count(1)
    return AttentionProfile(Path(config.root), project=config.project, name=config.profile, invocation=invocation,
        clock=lambda: datetime.fromtimestamp(clock() / 1_000_000, UTC).isoformat(),
        next_id=lambda: f"{invocation}:attempt-{next(attempts)}", resolvers=())


def manager_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    return environment


def systemd_manager(config: SupervisionConfig) -> SystemdHostManager:
    return SystemdHostManager(systemctl=config.systemctl, systemd_run=config.systemd_run, env=config.env,
                              environment=manager_environment())


def module_argv(config: SupervisionConfig, config_path: Path, *arguments: str) -> tuple[str, ...]:
    return (config.python, "-B", "-m", MODULE, *arguments, "--config", str(config_path))


def module_environment(config: SupervisionConfig) -> dict[str, str]:
    return {"PYTHONPATH": config.source_root, "PYTHONDONTWRITEBYTECODE": "1"}


class MonitorHostProfile:
    """Supervisor composition. Constructing it launches, observes and restarts nothing."""

    def __init__(self, config: SupervisionConfig | None, config_path: Path, *, manager: HostManager | None = None,
                 clock: Callable[[], int] = utc_micros, next_id: Callable[[], str] = lambda: uuid.uuid4().hex,
                 invocation: str = "monitor-host-supervisor") -> None:
        if config is None:
            raise HostHold("SUPERVISION_CONFIGURATION_MISSING")
        self.config, self.config_path = config, Path(config_path)
        self.manager = manager if manager is not None else systemd_manager(config)
        self.records = host_records(config, invocation)
        self.attention = attention(config, invocation, clock)
        # A never-started C4 service: inspection only, it can never write a monitor observation.
        self.monitor = MonitorProfile(Path(config.root), project=config.project, name=config.profile,
                                      invocation=invocation, policy=config.policy.monitor, clock=clock,
                                      next_id=lambda: "read-only")
        self.alerts = AttentionHostAlerts(self.attention.attention, project=config.project, profile=config.profile,
                                          required_authority=config.alert_authority)
        self.supervisor = MonitorHostSupervisor(config, manager=self.manager, records=self.records,
            alerts=self.alerts, health=self.monitor.monitor.inspect, clock=clock, next_id=next_id,
            command=self.command)

    def command(self, launch_id: str) -> tuple[tuple[str, ...], dict[str, str], str]:
        argv = module_argv(self.config, self.config_path, "host", "--launch-id", launch_id)
        return argv, module_environment(self.config), str(Path(self.config.root) / "monitor-host.log")

    def arm_observer(self) -> str:
        argv = module_argv(self.config, self.config_path, "observe")
        environment = module_environment(self.config) | {"XDG_RUNTIME_DIR": manager_environment()["XDG_RUNTIME_DIR"]}
        return self.manager.arm_observer(self.config.binding(), argv, environment, self.config.policy.observe_seconds,
                                         str(Path(self.config.root) / "monitor-observer.log"))


def own_cgroup() -> str:
    for line in Path("/proc/self/cgroup").read_text().splitlines():
        if line.startswith("0::"):
            return line[3:]
    raise HostHold("CGROUP_UNAVAILABLE")


class HostedMonitor:
    """The monitor/scanner process body; the supervisor owns its lifecycle."""

    def __init__(self, config: SupervisionConfig, launch_id: str, *, clock: Callable[[], int] = utc_micros,
                 cgroup: Callable[[], str] = own_cgroup) -> None:
        self.config, self.launch_id, self.clock = config, launch_id, clock
        if not (Path(config.root) / "monitor-host.sqlite").is_file():
            raise HostHold("HOST_NOT_OWNED")
        _, ownership = host_records(config, "monitor-host:" + launch_id).read(config.profile)
        # Refusals happen before any store other than the read-only ownership record is opened.
        if ownership is None or ownership.launch_id != launch_id or ownership.binding != config.binding():
            raise HostHold("HOST_NOT_OWNED")
        if cgroup() != ownership.cgroup:
            raise HostHold("HOST_OUTSIDE_OWNED_UNIT")
        invocation = config.host_invocation
        root = Path(config.root)
        self.attention = attention(config, invocation, clock)
        self.monitor = MonitorProfile(root, project=config.project, name=config.profile, invocation=invocation,
                                      policy=config.policy.monitor, clock=clock, next_id=lambda: launch_id)
        policy = config.policy
        self.liveness = LivenessProfile(root, project=config.project, name=config.profile,
            policy=LivenessPolicy(policy.grace_seconds, policy.interval_seconds, policy.confirmation_seconds),
            clock=clock, attention=self.attention, monitor=self.monitor, required_authority=config.judgment_authority)

    def start(self) -> None:
        self.monitor.monitor.start()
        self.liveness.reconciler.start()

    def cycle(self) -> None:
        self.monitor.monitor.tick()
        self.liveness.reconciler.scan()


def run_host(config: SupervisionConfig, launch_id: str, stop: Callable[[], bool],
             sleep: Callable[[float], None] = time.sleep, monotonic: Callable[[], float] = time.monotonic) -> int:
    try:
        hosted = HostedMonitor(config, launch_id)
    except HostHold as hold:
        print(json.dumps({"host": "REFUSED", "reason": hold.reason}), flush=True)
        return EXIT_REFUSED
    hosted.start()
    print(json.dumps({"host": "STARTED", "launch_id": launch_id}), flush=True)
    while not stop():
        try:
            hosted.cycle()
        except MonitorHold as hold:
            if hold.reason == "STALE_INSTANCE":
                print(json.dumps({"host": "SUPERSEDED", "launch_id": launch_id}), flush=True)
                return EXIT_SUPERSEDED
            raise
        deadline = monotonic() + config.policy.interval_seconds
        while not stop() and (remaining := deadline - monotonic()) > 0:
            sleep(min(remaining, 0.2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=MODULE, description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("host", "launch", "observe", "restart", "arm-observer", "show"))
    parser.add_argument("--config", type=Path)
    parser.add_argument("--launch-id")
    parser.add_argument("--actor")
    parser.add_argument("--authority")
    parser.add_argument("--replaces")
    parser.add_argument("--alert")
    arguments = parser.parse_args(argv)
    try:
        config = load_config(arguments.config)
        if arguments.command == "host":
            stopping = []
            signal.signal(signal.SIGTERM, lambda *_: stopping.append(True))
            return run_host(config, arguments.launch_id or "", lambda: bool(stopping))
        profile = MonitorHostProfile(config, arguments.config)
        binding = config.binding()
        if arguments.command in ("launch", "restart"):
            grant = HostGrant(arguments.actor or "", arguments.authority or "", binding.profile, binding.unit,
                              binding.host_invocation, arguments.replaces, arguments.alert)
            action = profile.supervisor.launch if arguments.command == "launch" else profile.supervisor.restart
            result: object = asdict(action(grant))
        elif arguments.command == "observe":
            detection, ownership = profile.supervisor.observe()
            result = {"detection": asdict(detection), "ownership": asdict(ownership)}
        elif arguments.command == "arm-observer":
            result = {"observer": profile.arm_observer()}
        else:
            _, ownership = profile.records.read(config.profile)
            result = {"ownership": None if ownership is None else asdict(ownership)}
    except HostHold as hold:
        print(json.dumps({"hold": hold.reason}), flush=True)
        return EXIT_HOLD
    print(json.dumps(result, default=str), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
