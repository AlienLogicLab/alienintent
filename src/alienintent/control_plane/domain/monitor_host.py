"""Supervised monitor host values (C5): configuration, binding, ownership, grants and detection.

The supervisor is external to both the model session and the monitored host: the host is a
supervisor-owned unit, and an independent observer reads the durable C4 health record and
the unit state. No value here runs, waits, restarts or alerts. Restart is explicit and
granted (no nonterminal retry, no budget reset). Times are integer UTC microseconds.
"""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
import re

from alienintent.control_plane.domain.monitor_health import HealthReport, HealthStatus, MonitorPolicy

HOST_RECORD_SCHEMA = 1
# Unit properties the supervisor launches with and re-verifies on every observation.
UNIT_PROPERTIES = {"Type": "exec", "Restart": "no", "KillMode": "control-group", "SendSIGKILL": "yes"}
_UNIT = re.compile(r"^alienintent-monitor-[0-9a-f]{32}\.service$")
_INVOCATION_ID = re.compile(r"^[0-9a-f]{32}$")


class HostHold(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _text(*values: object) -> bool:
    return all(isinstance(v, str) and v.strip() and "\0" not in v and "\n" not in v for v in values)


def _executable(value: object) -> bool:
    return _text(value) and str(value).startswith("/")


def _duration(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def digest(document: object) -> str:
    body = json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "sha256:" + sha256(body.encode()).hexdigest()


@dataclass(frozen=True)
class HostPolicy:
    """G, I and C for the hosted monitor/scanner, plus the supervisor's startup, stop and
    observation periods. All are configurable positive finite durations in seconds."""
    grace_seconds: int | float
    interval_seconds: int | float
    confirmation_seconds: int | float
    startup_seconds: int | float
    stop_seconds: int | float
    observe_seconds: int | float

    def __post_init__(self) -> None:
        for key, value in asdict(self).items():
            if not _duration(value):
                raise HostHold("SUPERVISION_CONFIGURATION_INVALID:policy." + key)

    @property
    def monitor(self) -> MonitorPolicy:
        return MonitorPolicy(self.interval_seconds)

    @property
    def startup_micros(self) -> int:
        return int(self.startup_seconds * 1_000_000)


@dataclass(frozen=True)
class SupervisionConfig:
    """The supervisor's own configuration. Missing or invalid values hold before any launch or
    restart. Doctor configuration stays with SF-REQ-037/038; this is only what supervision reads."""
    project: str
    profile: str
    host_invocation: str
    root: str
    source_root: str
    python: str
    systemd_run: str
    systemctl: str
    env: str
    policy: HostPolicy
    host_actors: tuple[str, ...]
    host_authority: str
    alert_authority: str
    judgment_authority: str

    @classmethod
    def from_document(cls, document: object) -> "SupervisionConfig":
        if not isinstance(document, dict):
            raise HostHold("SUPERVISION_CONFIGURATION_MISSING")
        if document.get("schema_version") != 1 or document.get("mode") != "systemd":
            raise HostHold("SUPERVISION_CONFIGURATION_INVALID:mode")
        policy = document.get("policy")
        if not isinstance(policy, dict) or set(policy) != set(HostPolicy.__dataclass_fields__):
            raise HostHold("SUPERVISION_CONFIGURATION_INVALID:policy")
        actors = document.get("host_actors")
        if not isinstance(actors, list):
            raise HostHold("SUPERVISION_CONFIGURATION_INVALID:host_actors")
        fields = [f for f in cls.__dataclass_fields__ if f not in ("policy", "host_actors")]
        missing = [f for f in fields if f not in document]
        if missing:
            raise HostHold("SUPERVISION_CONFIGURATION_INVALID:" + missing[0])
        return cls(**{f: document[f] for f in fields}, policy=HostPolicy(**policy), host_actors=tuple(actors))

    def __post_init__(self) -> None:
        for key in ("project", "profile", "host_invocation", "host_authority", "alert_authority",
                    "judgment_authority"):
            if not _text(getattr(self, key)):
                raise HostHold("SUPERVISION_CONFIGURATION_INVALID:" + key)
        for key in ("root", "source_root", "python", "systemd_run", "systemctl", "env"):
            if not _executable(getattr(self, key)):
                raise HostHold("SUPERVISION_CONFIGURATION_INVALID:" + key)
        if not isinstance(self.policy, HostPolicy):
            raise HostHold("SUPERVISION_CONFIGURATION_INVALID:policy")
        if (not self.host_actors or not all(_text(a) for a in self.host_actors)
                or len(set(self.host_actors)) != len(self.host_actors)):
            raise HostHold("SUPERVISION_CONFIGURATION_INVALID:host_actors")

    def document(self) -> dict[str, object]:
        body = asdict(self)
        body["host_actors"] = list(self.host_actors)
        return {"schema_version": 1, "mode": "systemd", **body}

    def digest(self) -> str:
        return digest(self.document())

    def binding(self) -> "HostBinding":
        return HostBinding.derive(self.profile, self.host_invocation)


@dataclass(frozen=True)
class HostBinding:
    """The intended monitor/scanner invocation and the one unit name that may host it."""
    profile: str
    host_invocation: str
    unit: str
    description: str

    @classmethod
    def derive(cls, profile: str, host_invocation: str) -> "HostBinding":
        key = digest([profile, host_invocation]).removeprefix("sha256:")[:32]
        return cls(profile, host_invocation, f"alienintent-monitor-{key}.service", f"AlienIntent monitor host {key}")

    def __post_init__(self) -> None:
        if not _text(self.profile, self.host_invocation, self.description) or not _UNIT.match(self.unit):
            raise HostHold("BINDING_INVALID")


@dataclass(frozen=True)
class ManagerIdentity:
    """The service manager instance that owns the unit; a different manager is not ours."""
    uid: int
    boot_id: str
    started_at_monotonic: str
    cgroup: str


@dataclass(frozen=True)
class UnitState:
    """What the manager reports for a unit name. `loaded` False means no such unit."""
    loaded: bool
    unit: str
    description: str = ""
    invocation_id: str = ""
    control_group: str = ""
    active_state: str = ""
    sub_state: str = ""
    result: str = ""
    main_pid: int = 0
    properties: tuple[tuple[str, str], ...] = ()

    @property
    def running(self) -> bool:
        return self.loaded and (self.active_state, self.sub_state) == ("active", "running")


@dataclass(frozen=True)
class HostGrant:
    """An authorized launch (`replaces` None) or restart of one exact launch after one alert."""
    actor: str
    authority: str
    profile: str
    unit: str
    host_invocation: str
    replaces: str | None = None
    alert: str | None = None

    def __post_init__(self) -> None:
        if not _text(self.actor, self.authority, self.profile, self.unit, self.host_invocation) or (
                (self.replaces is None) != (self.alert is None)) or (
                self.replaces is not None and not _text(self.replaces, self.alert)):
            raise HostHold("GRANT_INVALID")

    def digest(self) -> str:
        return digest(asdict(self))


@dataclass(frozen=True)
class HostOwnership:
    """The durable `monitor-host:<profile>` record, written only by the supervisor.

    `launch_id` is also the monitor instance id the hosted process must start with, so the
    C4 generation it writes is attributable to exactly this supervised launch.
    """
    binding: HostBinding
    manager: ManagerIdentity
    cgroup: str
    config_digest: str
    state: str  # LAUNCHING | RUNNING | ALERTED | RESTARTING
    launch_id: str
    launched_at: int
    predecessor_generation: int
    grant_digest: str
    systemd_invocation_id: str | None = None
    alert: str | None = None
    alert_reason: str | None = None
    restart_of: str | None = None

    STATES = frozenset({"LAUNCHING", "RUNNING", "ALERTED", "RESTARTING"})

    def __post_init__(self) -> None:
        if (self.state not in self.STATES or not _text(self.launch_id, self.cgroup, self.config_digest, self.grant_digest)
                or type(self.launched_at) is not int or self.launched_at < 0
                or type(self.predecessor_generation) is not int or self.predecessor_generation < 0
                or self.systemd_invocation_id is not None and not _INVOCATION_ID.match(self.systemd_invocation_id)
                or (self.state in ("ALERTED", "RESTARTING")) != (self.alert is not None)
                or (self.state == "RESTARTING") != (self.restart_of is not None)):
            raise HostHold("OWNERSHIP_INVALID")

    def document(self) -> dict[str, object]:
        return {"schema_version": HOST_RECORD_SCHEMA, **asdict(self)}

    @classmethod
    def from_document(cls, body: dict[str, object]) -> "HostOwnership":
        if body.get("schema_version") != HOST_RECORD_SCHEMA:
            raise HostHold("OWNERSHIP_SCHEMA_INCOMPATIBLE")
        try:
            values = {k: v for k, v in body.items() if k != "schema_version"}
            values["binding"] = HostBinding(**values["binding"])
            values["manager"] = ManagerIdentity(**values["manager"])
            return cls(**values)
        except (KeyError, TypeError) as error:
            raise HostHold("OWNERSHIP_INVALID") from error


@dataclass(frozen=True)
class Detection:
    """One external observation of the supervised host. `alert` names a failure needing a
    granted restart; `refused` means the observed unit or instance is not the owned one."""
    status: str  # RUNNING | STARTING | FAILED | REFUSED
    reason: str
    health: str
    health_reason: str
    alert: bool
    refused: bool = False


def owned_unit(ownership: HostOwnership, unit: UnitState) -> str | None:
    """Why this unit is not the owned host, or None when it is."""
    if not unit.loaded:
        return None
    if unit.unit != ownership.binding.unit or unit.description != ownership.binding.description:
        return "UNIT_BINDING_MISMATCH"
    if not _INVOCATION_ID.match(unit.invocation_id):
        return "UNIT_INVOCATION_UNKNOWN"
    if ownership.systemd_invocation_id is not None and unit.invocation_id != ownership.systemd_invocation_id:
        return "UNIT_INVOCATION_MISMATCH"
    if unit.control_group not in (ownership.cgroup, ""):
        return "UNIT_CGROUP_MISMATCH"
    if unit.control_group == "" and unit.active_state not in ("inactive", "failed"):
        return "UNIT_CGROUP_MISMATCH"
    if any(dict(unit.properties).get(k) != v for k, v in UNIT_PROPERTIES.items()):
        return "UNIT_PROPERTIES_MISMATCH"
    return None


def detect(ownership: HostOwnership, unit: UnitState, report: HealthReport, now: int, startup_micros: int) -> Detection:
    """Ordered: identity refusal, dead unit, startup window, instance attribution, health.

    A running unit is not health: a stalled host keeps its unit active while its durable
    ticks stop, so only the C4 record, read externally, can show it (self-heartbeats alone
    cannot detect a dead host).
    """
    health, health_reason = str(report.status), report.reason
    mismatch = owned_unit(ownership, unit)
    if mismatch:
        return Detection("REFUSED", mismatch, health, health_reason, alert=True, refused=True)
    if not unit.running:
        state = "UNIT_MISSING" if not unit.loaded else f"UNIT_{unit.active_state}_{unit.sub_state}_{unit.result}".upper()
        return Detection("FAILED", state, health, health_reason, alert=True)
    record = report.record
    ours = record is not None and record.instance_id == ownership.launch_id
    if not ours:
        within = now - ownership.launched_at <= startup_micros
        if within and (record is None or record.generation <= ownership.predecessor_generation):
            return Detection("STARTING", "AWAITING_OWNED_GENERATION", health, health_reason, alert=False)
        reason = "STARTUP_TIMEOUT" if record is None or record.generation <= ownership.predecessor_generation \
            else "INSTANCE_NOT_OWNED"
        return Detection("REFUSED" if reason == "INSTANCE_NOT_OWNED" else "FAILED", reason, health, health_reason,
                         alert=True, refused=reason == "INSTANCE_NOT_OWNED")
    if record.generation != ownership.predecessor_generation + 1:
        return Detection("REFUSED", "GENERATION_NOT_CONTINUOUS", health, health_reason, alert=True, refused=True)
    if report.status in (HealthStatus.STALE, HealthStatus.UNVERIFIED):
        return Detection("FAILED", "HEALTH_" + health + ":" + health_reason, health, health_reason, alert=True)
    return Detection("RUNNING", "OWNED_" + health, health, health_reason, alert=False)
