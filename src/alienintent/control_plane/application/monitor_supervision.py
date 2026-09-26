"""Independent supervision of the monitor/scanner host (C5, SF-REQ-053 under SWF-27).

The supervisor launches the host as a manager-owned unit bound to one monitor invocation,
observes it externally (unit state plus the durable C4 health record, never a self-report),
raises a durable alert on failure and restarts it only under an explicit grant naming the
exact failed launch and alert. Restart reopens the same stores, so the C4 generation
continues (n -> n+1) and pending state is kept; nothing here waits, polls or retries.
"""
from collections.abc import Callable
from dataclasses import replace

from alienintent.control_plane.domain.monitor_health import HealthReport
from alienintent.control_plane.domain.monitor_host import (
    Detection, HostGrant, HostHold, HostOwnership, ManagerIdentity, SupervisionConfig, detect, owned_unit,
)
from alienintent.control_plane.ports.monitor_host import HostAlerts, HostManager, HostRecords

# Builds the hosted process for one launch id: (argv, environment, log path).
HostCommand = Callable[[str], tuple[tuple[str, ...], dict[str, str], str]]


class MonitorHostSupervisor:
    def __init__(self, config: SupervisionConfig | None, *, manager: HostManager, records: HostRecords,
                 alerts: HostAlerts, health: Callable[[], HealthReport], clock: Callable[[], int],
                 next_id: Callable[[], str], command: HostCommand) -> None:
        self.config, self.manager, self.records, self.alerts = config, manager, records, alerts
        self.health, self.clock, self.next_id, self.command = health, clock, next_id, command

    # ---- preconditions: every one holds before any unit or record mutation ----------------

    def _config(self) -> SupervisionConfig:
        if self.config is None:
            raise HostHold("SUPERVISION_CONFIGURATION_MISSING")
        if not isinstance(self.config, SupervisionConfig):
            raise HostHold("SUPERVISION_CONFIGURATION_INVALID")
        return self.config

    def _identity(self) -> ManagerIdentity:
        try:
            return self.manager.identity()
        except HostHold:
            raise
        except Exception as error:
            raise HostHold("MANAGER_UNAVAILABLE") from error

    @staticmethod
    def _authorize(config: SupervisionConfig, grant: HostGrant) -> None:
        if not isinstance(grant, HostGrant):
            raise HostHold("GRANT_REQUIRED")
        if grant.actor not in config.host_actors or grant.authority != config.host_authority:
            raise HostHold("GRANT_UNAUTHORIZED")
        binding = config.binding()
        if (grant.profile, grant.unit, grant.host_invocation) != (binding.profile, binding.unit,
                                                                   binding.host_invocation):
            raise HostHold("GRANT_IDENTITY_MISMATCH")

    def _owned(self, config: SupervisionConfig) -> tuple[int, HostOwnership]:
        version, ownership = self.records.read(config.profile)
        if ownership is None:
            raise HostHold("NOT_LAUNCHED")
        if ownership.binding != config.binding():
            raise HostHold("BINDING_MISMATCH")
        return version, ownership

    def _now(self) -> int:
        now = self.clock()
        if type(now) is not int or now < 0:
            raise HostHold("CLOCK_INVALID")
        return now

    def _generation(self) -> int:
        """The latest persisted monitor generation; an unreadable store holds, never counts as 0."""
        report = self.health()
        if report.record is not None:
            return report.record.generation
        if report.reason == "NO_RECORD":
            return 0
        raise HostHold("MONITOR_STATE_UNAVAILABLE:" + report.reason)

    # ---- operations -------------------------------------------------------------------------

    def launch(self, grant: HostGrant) -> HostOwnership:
        """First launch of the profile's host. An existing owner or unit is never duplicated."""
        config = self._config()
        self._authorize(config, grant)
        if grant.replaces is not None:
            raise HostHold("GRANT_IS_RESTART")
        identity = self._identity()
        version, current = self.records.read(config.profile)
        if current is not None:
            raise HostHold("HOST_ALREADY_OWNED")
        binding = config.binding()
        if self.manager.show(binding.unit).loaded:
            raise HostHold("UNIT_COLLISION")
        ownership = HostOwnership(binding, identity, self.manager.unit_cgroup(identity, binding), config.digest(),
                                  "LAUNCHING", self.next_id(), self._now(), self._generation(), grant.digest())
        version = self.records.save(version, ownership, {"action": "LAUNCH_INTENT", "grant": grant.digest()})
        return self._start(config, version, ownership)

    def _start(self, config: SupervisionConfig, version: int, ownership: HostOwnership) -> HostOwnership:
        argv, environment, log_path = self.command(ownership.launch_id)
        self.manager.launch(ownership.binding, argv, environment, config.policy.stop_seconds, log_path)
        running = replace(ownership, state="RUNNING", alert=None, alert_reason=None, restart_of=None)
        self.records.save(version, running, {"action": "LAUNCHED", "launch_id": ownership.launch_id,
                                             "restart_of": ownership.restart_of})
        return running

    def observe(self) -> tuple[Detection, HostOwnership]:
        """One external observation. A failure raises one durable alert per launch."""
        config = self._config()
        identity = self._identity()
        version, ownership = self._owned(config)
        if ownership.state in ("LAUNCHING", "RESTARTING"):
            raise HostHold("LAUNCH_IN_PROGRESS")
        if identity != ownership.manager:
            unit = self.manager.show(ownership.binding.unit)
            detection = Detection("FAILED", "MANAGER_CHANGED", "UNOBSERVED", "MANAGER_CHANGED", alert=True)
        else:
            unit = self.manager.show(ownership.binding.unit)
            if ownership.systemd_invocation_id is None and unit.loaded and owned_unit(ownership, unit) is None:
                # Bind the manager's invocation of this launch; later observations must match it.
                ownership = replace(ownership, systemd_invocation_id=unit.invocation_id)
                version = self.records.save(version, ownership, {"action": "BOUND", "invocation_id": unit.invocation_id})
            detection = detect(ownership, unit, self.health(), self._now(), config.policy.startup_micros)
        if detection.alert and ownership.state != "ALERTED":
            observation = {"action": "ALERTED", "reason": detection.reason, "health": detection.health,
                           "health_reason": detection.health_reason, "refused": detection.refused,
                           "unit": {"loaded": unit.loaded, "active_state": unit.active_state,
                                    "sub_state": unit.sub_state, "result": unit.result,
                                    "invocation_id": unit.invocation_id}}
            alert = self.alerts.raise_alert(ownership, detection.reason, observation)
            ownership = replace(ownership, state="ALERTED", alert=alert, alert_reason=detection.reason)
            self.records.save(version, ownership, observation | {"alert": alert})
        return detection, ownership

    def restart(self, grant: HostGrant) -> HostOwnership:
        """Replace exactly the alerted launch named by the grant; the stores are reopened, not reset."""
        config = self._config()
        self._authorize(config, grant)
        if grant.replaces is None:
            raise HostHold("GRANT_IS_LAUNCH")
        identity = self._identity()
        version, ownership = self._owned(config)
        if ownership.state == "RESTARTING":
            if ownership.grant_digest != grant.digest():
                raise HostHold("RESTART_IN_PROGRESS")
            return self._resume(config, version, ownership)
        if ownership.state != "ALERTED":
            raise HostHold("RESTART_NOT_ALERTED")
        if grant.replaces != ownership.launch_id:
            raise HostHold("RESTART_LAUNCH_MISMATCH")
        if grant.alert != ownership.alert:
            raise HostHold("RESTART_ALERT_MISMATCH")
        self._take_down(ownership)
        restarting = replace(ownership, manager=identity, cgroup=self.manager.unit_cgroup(identity, ownership.binding),
                             config_digest=config.digest(), state="RESTARTING", launch_id=self.next_id(),
                             launched_at=self._now(), predecessor_generation=self._generation(),
                             grant_digest=grant.digest(), systemd_invocation_id=None, restart_of=ownership.launch_id)
        if restarting.launch_id == ownership.launch_id:
            raise HostHold("LAUNCH_ID_REUSED")
        version = self.records.save(version, restarting, {"action": "RESTART_INTENT", "grant": grant.digest(),
                                                          "alert": ownership.alert, "replaces": ownership.launch_id})
        return self._start(config, version, restarting)

    def _resume(self, config: SupervisionConfig, version: int, ownership: HostOwnership) -> HostOwnership:
        """A restart interrupted after its intent: launch once, or adopt the unit it already launched."""
        unit = self.manager.show(ownership.binding.unit)
        if not unit.loaded:
            return self._start(config, version, ownership)
        if owned_unit(ownership, unit) is not None:
            raise HostHold("RESTART_REFUSED:" + str(owned_unit(ownership, unit)))
        running = replace(ownership, state="RUNNING", alert=None, alert_reason=None, restart_of=None)
        self.records.save(version, running, {"action": "LAUNCHED", "launch_id": ownership.launch_id, "resumed": True})
        return running

    def _take_down(self, ownership: HostOwnership) -> None:
        """Kill and remove only the owned unit, then confirm it and its cgroup are gone."""
        unit_name = ownership.binding.unit
        unit = self.manager.show(unit_name)
        if unit.loaded:
            mismatch = owned_unit(ownership, unit)
            if mismatch:
                raise HostHold("RESTART_REFUSED:" + mismatch)
            if unit.active_state not in ("inactive", "failed"):
                # SIGKILL reaches a stalled (SIGSTOPped) host too; stop then removes the unit.
                self.manager.kill(unit_name)
            self.manager.stop(unit_name)
            unit = self.manager.show(unit_name)
            if unit.loaded and unit.active_state == "failed":
                self.manager.reset_failed(unit_name)
                unit = self.manager.show(unit_name)
        if unit.loaded or not self.manager.cgroup_empty(ownership.cgroup):
            raise HostHold("TAKEDOWN_UNCONFIRMED")
