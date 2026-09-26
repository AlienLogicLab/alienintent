"""The per-user systemd manager as the monitor host's external supervisor.

The same manager-identity and cgroup discipline as `src/runtime/systemd-supervision.mjs`:
the manager is identified by boot, start time and cgroup; the host runs as a transient
`Restart=no` unit under `app.slice` with `env -i`, so it inherits nothing from the caller.
"""
from collections.abc import Callable
import os
from pathlib import Path
import re
import subprocess

from alienintent.control_plane.domain.monitor_host import (
    UNIT_PROPERTIES, HostBinding, HostHold, ManagerIdentity, UnitState,
)
from alienintent.control_plane.ports.monitor_host import HostManager

FIELDS = ("Id", "LoadState", "Description", "InvocationID", "ControlGroup", "ActiveState", "SubState", "Result",
          "MainPID", *UNIT_PROPERTIES)
_MANAGER_CGROUP = re.compile(r"^/user\.slice/user-[0-9]+\.slice/user@[0-9]+\.service$")


def observer_unit(binding: HostBinding) -> str:
    return binding.unit.removesuffix(".service").replace("alienintent-monitor-", "alienintent-monitor-observer-")


def parse(text: str) -> dict[str, str]:
    return dict(line.split("=", 1) for line in text.strip().splitlines() if "=" in line)


class SystemdHostManager(HostManager):
    def __init__(self, *, systemctl: str, systemd_run: str, env: str, environment: dict[str, str],
                 read_file: Callable[[str], str] | None = None, uid: Callable[[], int] = os.getuid) -> None:
        self.systemctl, self.systemd_run, self.env = systemctl, systemd_run, env
        # Only manager-connection variables reach the client, never the hosted process.
        self.environment = {k: environment[k] for k in ("HOME", "USER", "LOGNAME", "XDG_RUNTIME_DIR",
                                                         "DBUS_SESSION_BUS_ADDRESS") if k in environment}
        self.read_file = read_file or (lambda path: Path(path).read_text())
        self.uid = uid

    def _run(self, argv: list[str]) -> str:
        try:
            result = subprocess.run(argv, env=self.environment, capture_output=True, text=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise HostHold("MANAGER_UNAVAILABLE") from error
        if result.returncode != 0:
            raise HostHold("MANAGER_COMMAND_FAILED")
        return result.stdout

    def identity(self) -> ManagerIdentity:
        try:
            self.read_file("/sys/fs/cgroup/cgroup.controllers")
            boot = self.read_file("/proc/sys/kernel/random/boot_id").strip()
        except OSError as error:
            raise HostHold("MANAGER_UNAVAILABLE") from error
        values = parse(self._run([self.systemctl, "--user", "show", "--no-pager",
                                  "--property=UserspaceTimestampMonotonic,ControlGroup"]))
        started, cgroup = values.get("UserspaceTimestampMonotonic", ""), values.get("ControlGroup", "")
        if not re.fullmatch(r"[1-9][0-9]*", started) or not _MANAGER_CGROUP.match(cgroup):
            raise HostHold("MANAGER_IDENTITY_REQUIRED")
        return ManagerIdentity(self.uid(), boot, started, cgroup)

    def unit_cgroup(self, manager: ManagerIdentity, binding: HostBinding) -> str:
        return f"{manager.cgroup}/app.slice/{binding.unit}"

    def show(self, unit: str) -> UnitState:
        argv = [self.systemctl, "--user", "show", "--no-pager", "--property=" + ",".join(FIELDS), "--", unit]
        try:
            result = subprocess.run(argv, env=self.environment, capture_output=True, text=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise HostHold("MANAGER_UNAVAILABLE") from error
        values = parse(result.stdout)
        if values.get("LoadState") == "not-found":
            return UnitState(False, unit)
        if result.returncode != 0 or values.get("LoadState") != "loaded":
            raise HostHold("MANAGER_UNAVAILABLE")
        return UnitState(True, values.get("Id", ""), values.get("Description", ""), values.get("InvocationID", ""),
                         values.get("ControlGroup", ""), values.get("ActiveState", ""), values.get("SubState", ""),
                         values.get("Result", ""), int(values.get("MainPID", "0") or 0),
                         tuple((k, values.get(k, "")) for k in UNIT_PROPERTIES))

    def cgroup_empty(self, cgroup: str) -> bool:
        try:
            text = self.read_file(f"/sys/fs/cgroup{cgroup}/cgroup.events")
        except FileNotFoundError:
            return True
        except OSError as error:
            raise HostHold("CGROUP_UNAVAILABLE") from error
        if not re.search(r"^populated [01]$", text, re.MULTILINE):
            raise HostHold("CGROUP_UNAVAILABLE")
        return re.search(r"^populated 0$", text, re.MULTILINE) is not None

    def launch(self, binding: HostBinding, argv: tuple[str, ...], environment: dict[str, str],
               stop_seconds: int | float, log_path: str) -> None:
        properties = {**UNIT_PROPERTIES, "TimeoutStopSec": f"{int(stop_seconds * 1000)}ms",
                      "StandardOutput": "append:" + log_path, "StandardError": "append:" + log_path}
        self._run([self.systemd_run, "--user", "--unit=" + binding.unit, "--slice=app.slice",
                   "--description=" + binding.description, "--expand-environment=no",
                   *(f"--property={k}={v}" for k, v in properties.items()), "--",
                   self.env, "-i", *(f"{k}={v}" for k, v in sorted(environment.items())), *argv])

    def arm_observer(self, binding: HostBinding, argv: tuple[str, ...], environment: dict[str, str],
                     period_seconds: int | float, log_path: str) -> str:
        """A manager-owned timer runs one external observation per period; it never restarts."""
        unit = observer_unit(binding)
        period = f"{int(period_seconds * 1000)}ms"
        self._run([self.systemd_run, "--user", "--unit=" + unit, "--slice=app.slice",
                   "--description=AlienIntent monitor observer " + binding.description.rsplit(" ", 1)[-1],
                   "--expand-environment=no", "--on-active=" + period, "--on-unit-active=" + period,
                   "--timer-property=AccuracySec=10ms", "--property=Type=oneshot",
                   "--property=StandardOutput=append:" + log_path, "--property=StandardError=append:" + log_path,
                   "--", self.env, "-i", *(f"{k}={v}" for k, v in sorted(environment.items())), *argv])
        return unit

    def disarm_observer(self, binding: HostBinding) -> None:
        unit = observer_unit(binding)
        for name in (unit + ".timer", unit + ".service"):
            if self.show(name).loaded:
                self._run([self.systemctl, "--user", "stop", "--", name])

    def kill(self, unit: str) -> None:
        self._run([self.systemctl, "--user", "kill", "--signal=SIGKILL", "--kill-whom=all", "--", unit])

    def stop(self, unit: str) -> None:
        self._run([self.systemctl, "--user", "stop", "--", unit])

    def reset_failed(self, unit: str) -> None:
        self._run([self.systemctl, "--user", "reset-failed", "--", unit])
