#!/usr/bin/env python3
"""Non-cognizant supervision for bounded Factory Director episodes (FDH-01).

This is intentionally infrastructure, not a second Director: it only evaluates a
closed activation predicate, keeps one durable lease, and starts a fresh,
provider-neutral (Claude or Codex) episode.  The episode reconstructs and decides
from authoritative state; the host re-evaluates after every episode exit.

Runtime contract: docs/operations/factory-director-runtime-contract.md
"""
from __future__ import annotations

import fcntl
import argparse
import json
import os
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Callable


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


@dataclass(frozen=True)
class DirectorInputs:
    authoritative_state: bool
    eligible_authorized_work: bool
    executable_capacity: bool
    attention_required: bool
    pending_director_inbox: bool
    lifecycle_requires_selection: bool
    wip_intentionally_full: bool
    founder_decision_pending: bool
    explicit_pause: bool

    def control_required(self) -> bool:
        return any((self.eligible_authorized_work, self.attention_required,
                    self.pending_director_inbox, self.lifecycle_requires_selection))

    def director_only_control(self) -> bool:
        """Control work that needs Director cognition but no worker WIP slot."""
        return any((self.attention_required, self.pending_director_inbox, self.lifecycle_requires_selection))


class JsonDirectorInputs:
    """Strict reader for a published nine-boolean projection.

    The host does not infer missing authority from a queue or process list.  Malformed,
    incomplete, or absent data deliberately becomes ``authoritative_state=False``.
    """
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def __call__(self) -> DirectorInputs:
        try:
            raw = json.loads(self.path.read_text())
            fields = set(DirectorInputs.__dataclass_fields__)
            if set(raw) != fields or not all(isinstance(raw[key], bool) for key in fields):
                raise ValueError("incomplete or non-boolean state projection")
            return DirectorInputs(**raw)
        except (OSError, ValueError, json.JSONDecodeError, TypeError):
            return DirectorInputs(False, False, False, False, False, False, False, False, False)


@dataclass(frozen=True)
class Episode:
    episode_id: str
    pid: int | None
    started_at: str
    process_start_ticks: str | None = None
    provider: str | None = None
    model: str | None = None


class HostState(Enum):
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    REFUSED = "REFUSED"


class AmbiguousLease(Exception):
    pass


@dataclass(frozen=True)
class Reconciliation:
    state: HostState
    reason: str
    episode_id: str | None = None


@dataclass(frozen=True)
class Inspection:
    state: HostState
    episode_active: bool
    lease_owner: str | None
    episode_id: str | None
    last_activation_reason: str | None
    last_exit_reason: str | None
    last_reason: str | None


# Legitimate terminal conditions (runtime contract, chat record §15) idle the host.
IDLE_REASONS = frozenset({"FACTORY_PAUSED", "FOUNDER_DECISION_PENDING", "WIP_INTENTIONALLY_FULL",
                          "NO_ELIGIBLE_AUTHORIZED_WORK"})
ACTIVATION_REASONS = frozenset({"DIRECTOR_CONTINUITY_FAULT", "PRIOR_EPISODE_EXITED_CONTROL_REMAINS"})


class InMemoryDirectorLauncher:
    """Test-only launch port; production uses a process launcher."""
    def __init__(self, provider: str = "memory", model: str = "memory-model") -> None:
        self.provider, self.model = provider, model
        self.launched: list[Episode] = []
        self._active: dict[str, bool] = {}
        self._exits: dict[str, int] = {}
        self._next_pid = 10_000

    def launch(self, episode_id: str, on_spawned: Callable[[Episode], None] | None = None) -> Episode:
        pid = self._next_pid
        self._next_pid += 1
        episode = Episode(episode_id, pid, _now(), f"memory-{pid}", self.provider, self.model)
        self.launched.append(episode)
        self._active[episode_id] = True
        if on_spawned is not None:
            on_spawned(episode)
        return episode

    def is_active(self, episode: Episode) -> bool:
        return self._active.get(episode.episode_id, False)

    def exit_reason(self, episode: Episode) -> str | None:
        code = self._exits.get(episode.episode_id)
        return None if code is None else f"EXIT_{code}"

    def usage(self, episode: Episode) -> dict:
        return {"measured": False, "reason": "IN_MEMORY_LAUNCHER"}

    def finish(self, episode_id: str, exit_code: int = 0) -> None:
        self._active[episode_id] = False
        self._exits[episode_id] = exit_code


PROVIDERS = ("claude", "codex")
# Values each CLI accepts (claude --permission-mode, codex exec --sandbox); a mismatch would
# fail every launch at once, so it is refused at configuration time instead.
PERMISSION_MODES = {"claude": frozenset({"acceptEdits", "auto", "bypassPermissions", "manual", "dontAsk", "plan"}),
                    "codex": frozenset({"read-only", "workspace-write", "danger-full-access"})}
FAST_EXIT_SECONDS = 60
BACKOFF_BASE_SECONDS = 60
BACKOFF_CAP_SECONDS = 3600


class ProcessDirectorLauncher:
    """Starts a fresh bounded Factory Director episode with the configured provider.

    Every launch is a new process with no resumed or inherited conversation:
    ``claude -p --no-session-persistence`` or ``codex exec --ephemeral`` (the same
    fresh-session flags the Node runtime uses for workers).  Switching provider is a
    configuration change.  The prompt goes on stdin; provider output is retained under
    the host state root, never in the Director worktree.
    """
    def __init__(self, workdir: Path | str, prompt_file: Path | str, *, provider: str,
                 executable: str, model: str, permission_mode: str,
                 output_dir: Path | str, require_isolated: bool = False) -> None:
        if provider not in PROVIDERS:
            raise ValueError(f"unsupported Factory Director provider {provider!r}")
        for label, value in (("executable", executable), ("model", model), ("permission_mode", permission_mode)):
            if not isinstance(value, str) or not value:
                raise ValueError(f"Factory Director launcher {label} must be configured explicitly")
        if permission_mode not in PERMISSION_MODES[provider]:
            raise ValueError(f"permission mode {permission_mode!r} is not valid for {provider}")
        self.workdir, self.prompt_file, self.output_dir = Path(workdir), Path(prompt_file), Path(output_dir)
        self.provider, self.executable, self.model, self.permission_mode = provider, executable, model, permission_mode
        self._children: dict[str, subprocess.Popen] = {}
        if require_isolated and not self._is_linked_worktree():
            raise ValueError("Factory Director workspace must be an isolated linked worktree")

    def _is_linked_worktree(self) -> bool:
        try:
            git_dir = subprocess.run(["git", "-C", str(self.workdir), "rev-parse", "--absolute-git-dir"],
                                     capture_output=True, text=True, check=True).stdout.strip()
            common = subprocess.run(["git", "-C", str(self.workdir), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                    capture_output=True, text=True, check=True).stdout.strip()
            return bool(git_dir and common and Path(git_dir).resolve() != Path(common).resolve())
        except (OSError, subprocess.SubprocessError):
            return False

    def command(self) -> list[str]:
        if self.provider == "claude":
            return [self.executable, "-p", "--no-session-persistence", "--output-format", "json",
                    "--permission-mode", self.permission_mode, "--model", self.model]
        return [self.executable, "exec", "--ephemeral", "--json", "--sandbox", self.permission_mode,
                "-C", str(self.workdir), "--model", self.model, "-"]

    def environment(self) -> dict[str, str]:
        if self.provider == "codex":
            from codex_session import FILTERED_ENV
            return {k: v for k, v in os.environ.items() if k not in FILTERED_ENV}
        return dict(os.environ)

    def _output(self, episode_id: str, stream: str) -> Path:
        return self.output_dir / f"{episode_id}.{stream}"

    def launch(self, episode_id: str, on_spawned: Callable[[Episode], None] | None = None) -> Episode:
        prompt = self.prompt_file.read_text().replace("{{EPISODE_ID}}", episode_id)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with self._output(episode_id, "stdout").open("w") as stdout, \
                self._output(episode_id, "stderr").open("w") as stderr:
            child = subprocess.Popen(self.command(), cwd=str(self.workdir), stdin=subprocess.PIPE,
                                     stdout=stdout, stderr=stderr, text=True, env=self.environment())
        self._children[episode_id] = child
        try:
            episode = Episode(episode_id, child.pid, _now(), self._process_start_ticks(child.pid),
                              self.provider, self.model)
            if on_spawned is not None:
                if not isinstance(episode.process_start_ticks, str) or not episode.process_start_ticks:
                    raise RuntimeError("spawned child process identity is unavailable")
                on_spawned(episode)
        except BaseException:
            # Never bound to the lease: an unleased child must not survive to run unsupervised.
            self._children.pop(episode_id, None)
            child.kill()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            raise
        assert child.stdin is not None
        child.stdin.write(prompt)
        child.stdin.close()
        return episode

    @staticmethod
    def _process_start_ticks(pid: int) -> str | None:
        """Stable /proc start identity; PID alone is unsafe after a restart."""
        try:
            # comm may contain spaces/parentheses, so split only after its final ')'.
            fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
            return fields[19]  # Linux proc stat field 22, after state (field 3).
        except (OSError, IndexError):
            return None

    def is_active(self, episode: Episode) -> bool:
        return self.liveness(episode) is True

    def liveness(self, episode: Episode) -> bool | None:
        child = self._children.get(episode.episode_id)
        if child is not None:
            return child.poll() is None  # poll() also reaps the exited child.
        if episode.pid is None:
            return False
        try:
            fields = Path(f"/proc/{episode.pid}/stat").read_text().rsplit(")", 1)[1].split()
            if fields[0] == "Z":  # A zombie has exited even though kill(pid, 0) succeeds.
                return False
            current_start = fields[19]
            return episode.process_start_ticks is not None and current_start == episode.process_start_ticks
        except FileNotFoundError:
            return False
        except (OSError, IndexError):
            return None

    def exit_reason(self, episode: Episode) -> str | None:
        if self.is_active(episode):
            return None
        child = self._children.get(episode.episode_id)
        if child is None or child.returncode is None:
            return "PROCESS_EXITED"  # Launched before a host restart; the status is not ours to read.
        return f"EXIT_{child.returncode}" if child.returncode >= 0 else f"SIGNAL_{-child.returncode}"

    def usage(self, episode: Episode) -> dict:
        """Tokens, cost and model as reported by the provider; never assumed."""
        try:
            text = self._output(episode.episode_id, "stdout").read_text()
        except OSError:
            return {"measured": False, "reason": "PROVIDER_OUTPUT_UNAVAILABLE"}
        return (claude_usage if episode.provider == "claude" else codex_usage)(text)


def claude_usage(text: str) -> dict:
    try:
        result = json.loads(text)
        usage = result["usage"]
        observed = sorted(result.get("modelUsage") or {}) or None
        return {"measured": True, "observed_models": observed,
                "model_evidence": "PROVIDER_REPORTED" if observed else "NOT_EXPOSED_BY_PROVIDER",
                "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
                "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
                "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
                "cost_usd": result.get("total_cost_usd")}
    except (ValueError, KeyError, TypeError, AttributeError):
        return {"measured": False, "reason": "PROVIDER_DID_NOT_EXPOSE_USAGE"}


def codex_usage(text: str) -> dict:
    totals = {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}
    turns = 0
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            turns += 1
            for key in totals:
                if isinstance(event["usage"].get(key), int):
                    totals[key] += event["usage"][key]
    if not turns:
        return {"measured": False, "reason": "PROVIDER_DID_NOT_EXPOSE_USAGE"}
    # Codex JSON events carry token counts only: model and cost are recorded as not exposed.
    # The requested model (--model) is intent, not evidence of the model actually used, so it
    # is never copied here (runtime contract section 10).
    return {"measured": True, "turns": turns, **totals, "observed_models": None,
            "model_evidence": "NOT_EXPOSED_BY_PROVIDER", "cost_usd": None}


def _parse_time(value) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


class FactoryDirectorHost:
    def __init__(self, state_root: Path | str, inputs: Callable[[], DirectorInputs], launcher,
                 clock: Callable[[], datetime] | None = None) -> None:
        self.root, self.inputs, self.launcher = Path(state_root), inputs, launcher
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.host_id = f"fdh-{uuid.uuid4().hex}"
        self._lock_file = None
        self._last_recorded: tuple | None = None

    @property
    def _lease_path(self) -> Path: return self.root / "lease.json"
    @property
    def _history_path(self) -> Path: return self.root / "history.jsonl"
    @property
    def _lock_path(self) -> Path: return self.root / "host.lock"

    def start(self) -> bool:
        if self._lock_file is not None:
            return True
        self.root.mkdir(parents=True, exist_ok=True)
        candidate = self._lock_path.open("a+")
        try:
            fcntl.flock(candidate.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            candidate.close()
            return False
        self._lock_file = candidate
        return True

    def shutdown(self) -> None:
        if self._lock_file is not None:
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
            self._lock_file.close()
            self._lock_file = None

    def _lease(self) -> dict | None:
        try:
            value = json.loads(self._lease_path.read_text())
            required = {"host_id", "episode_id", "pid", "started_at", "process_start_ticks", "status"}
            # Containment, not strict subset: a real lease carries extra metadata beside the required keys.
            if not isinstance(value, dict) or not required <= set(value):
                raise ValueError("lease schema is incomplete")
            if not isinstance(value["host_id"], str) or not isinstance(value["episode_id"], str):
                raise ValueError("lease identity is invalid")
            if value["pid"] is not None and not isinstance(value["pid"], int):
                raise ValueError("lease pid is invalid")
            if value["status"] not in {"ACTIVATING", "ACTIVE", "EXITED", "LAUNCH_FAILED"}:
                raise ValueError("lease status is invalid")
            if value["status"] == "ACTIVE":
                if isinstance(value["pid"], bool) or not isinstance(value["pid"], int) or value["pid"] <= 0:
                    raise ValueError("active lease pid is invalid")
                if not isinstance(value["process_start_ticks"], str) or not value["process_start_ticks"]:
                    raise ValueError("active lease process identity is invalid")
            return value
        except FileNotFoundError:
            return None
        except (OSError, ValueError, TypeError) as exc:
            raise AmbiguousLease("lease cannot be read") from exc

    def _episode(self, lease: dict) -> Episode:
        return Episode(lease["episode_id"], lease.get("pid"), lease["started_at"],
                       lease.get("process_start_ticks"), lease.get("provider"), lease.get("model"))

    def _liveness(self, episode: Episode) -> bool | None:
        return (self.launcher.liveness(episode) if hasattr(self.launcher, "liveness")
                else self.launcher.is_active(episode))

    def _record(self, reconciliation: Reconciliation, *, exit_reason: str | None = None, **details) -> None:
        # Unchanged polls are not new evidence; launches, exits and changes of reason or cause are.
        key = (reconciliation.reason, reconciliation.state, reconciliation.episode_id,
               json.dumps(details, sort_keys=True, default=str))
        if key == self._last_recorded and exit_reason is None:
            return
        self._last_recorded = key
        record = {"at": self.clock().isoformat(), "reason": reconciliation.reason, "state": reconciliation.state.value,
                  "episode_id": reconciliation.episode_id, "exit_reason": exit_reason, **details}
        self._history_path.parent.mkdir(parents=True, exist_ok=True)
        with self._history_path.open("a") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")

    def _idle_reason(self, values: DirectorInputs) -> str | None:
        """Idle-reason precedence; documented in the runtime contract."""
        if not values.authoritative_state: return "AUTHORITATIVE_STATE_UNAVAILABLE"
        if values.explicit_pause: return "FACTORY_PAUSED"
        if values.founder_decision_pending: return "FOUNDER_DECISION_PENDING"
        if values.wip_intentionally_full and not values.director_only_control():
            return "WIP_INTENTIONALLY_FULL"
        if not values.control_required(): return "NO_ELIGIBLE_AUTHORIZED_WORK"
        # Attention, inbox and selection need Director cognition, not a worker WIP slot.
        # Unreachable for adapter-derived inputs: executable_capacity and wip_intentionally_full are
        # exact complements there (FDH-92), so no capacity means full WIP, which matched above. Kept
        # as a recognised reason because history.jsonl persists it; it applies only to other inputs.
        if not values.executable_capacity and not values.director_only_control():
            return "EXECUTION_CAPACITY_UNAVAILABLE"
        return None

    def _retry_not_before(self, streak: int, now: datetime) -> str | None:
        """Crash-loop guard: the first failure retries at once; each further consecutive one
        doubles the wait from BACKOFF_BASE_SECONDS up to BACKOFF_CAP_SECONDS."""
        if streak < 2:
            return None
        return (now + timedelta(seconds=min(BACKOFF_BASE_SECONDS * 2 ** (streak - 2), BACKOFF_CAP_SECONDS))).isoformat()

    def _observe_exit(self, values: DirectorInputs | None = None) -> None:
        """Record a leased episode's exit, provider, model and usage once, whatever happens next."""
        try:
            lease = self._lease()
            if not lease or lease["status"] != "ACTIVE":
                return
            episode = self._episode(lease)
        except (AmbiguousLease, KeyError):
            return  # Left for reconcile to refuse if control is required.
        if self._liveness(episode) is not False:
            return
        exit_reason = self.launcher.exit_reason(episode) or "PROCESS_EXITED"
        usage = self.launcher.usage(episode) if hasattr(self.launcher, "usage") else {
            "measured": False, "reason": "LAUNCHER_DOES_NOT_REPORT_USAGE"}
        observed = self.clock()
        started = _parse_time(lease["started_at"])
        runtime = (observed - started).total_seconds() if started else 0.0
        # A failed episode is a non-zero or signalled exit, or a fast exit that left the durable
        # state fingerprint exactly as it was at launch. A fast exit that advanced durable state
        # (it handled something) is progress, not a crash. Unavailable state proves nothing.
        current = self._fingerprint(values) if values is not None else None
        unchanged = current is None or current == lease.get("launch_fingerprint")
        failed = ((exit_reason.startswith(("EXIT_", "SIGNAL_")) and exit_reason != "EXIT_0")
                  or (runtime < FAST_EXIT_SECONDS and unchanged))
        streak = int(lease.get("failure_streak") or 0) + 1 if failed else 0
        retry = self._retry_not_before(streak, observed)
        _atomic_json(self._lease_path, {**lease, "status": "EXITED", "exit_reason": exit_reason,
                                        "exited_observed_at": observed.isoformat(), "runtime_seconds": runtime,
                                        "failure_streak": streak, "retry_not_before": retry})
        self._record(Reconciliation(HostState.IDLE, "DIRECTOR_EPISODE_EXITED", episode.episode_id),
                     exit_reason=exit_reason, provider=episode.provider, requested_model=episode.model,
                     usage=usage, runtime_seconds=runtime, failure_streak=streak)

    def _fingerprint(self, values: DirectorInputs) -> str | None:
        if not values.authoritative_state:
            return None
        published = getattr(self.inputs, "last_fingerprint", None)
        return published if published is not None else json.dumps(asdict(values), sort_keys=True)

    def _reset_failure_streak(self) -> None:
        """A legitimate idle after any pending back-off ends a failure run; a brief idle inside the
        back-off window does not."""
        try:
            lease = self._lease()
        except AmbiguousLease:
            return
        retry = _parse_time(lease.get("retry_not_before")) if lease and lease.get("retry_not_before") else None
        if retry and self.clock() < retry:
            return
        if lease and lease["status"] in {"EXITED", "LAUNCH_FAILED"} and lease.get("failure_streak"):
            _atomic_json(self._lease_path, {**lease, "failure_streak": 0, "retry_not_before": None})

    def _refuse(self, reason: str, episode_id: str | None = None, **details) -> Reconciliation:
        result = Reconciliation(HostState.REFUSED, reason, episode_id)
        self._record(result, **details)
        return result

    def reconcile(self) -> Reconciliation:
        if not self.start():
            return self._refuse("CONFLICTING_HOST_OWNERSHIP")
        values = self.inputs()
        self._observe_exit(values)
        idle = self._idle_reason(values)
        if idle:
            result = Reconciliation(HostState.IDLE if idle in IDLE_REASONS else HostState.REFUSED, idle)
            if idle in IDLE_REASONS:
                self._reset_failure_streak()
            failure = getattr(self.inputs, "last_failure", None) if idle == "AUTHORITATIVE_STATE_UNAVAILABLE" else None
            self._record(result, **({"failure": failure} if failure else {}))
            return result
        try:
            lease = self._lease()
        except AmbiguousLease:
            return self._refuse("AMBIGUOUS_LEASE")
        if lease and lease.get("status") == "ACTIVATING":
            return self._refuse("AMBIGUOUS_LEASE")
        if lease and lease.get("status") == "ACTIVE":
            try:
                prior = self._episode(lease)
            except KeyError:
                return self._refuse("AMBIGUOUS_LEASE")
            if prior.pid is not None and prior.process_start_ticks is None:
                return self._refuse("AMBIGUOUS_LEASE")
            liveness = self._liveness(prior)
            if liveness is None:
                return self._refuse("EPISODE_LIVENESS_AMBIGUOUS", prior.episode_id)
            if liveness:
                result = Reconciliation(HostState.ACTIVE, "DIRECTOR_EPISODE_ACTIVE", prior.episode_id)
                self._record(result)
                return result
            # It exited after this reconcile's observation: record and count it like any exit.
            self._observe_exit(values)
            try:
                lease = self._lease()
            except AmbiguousLease:
                return self._refuse("AMBIGUOUS_LEASE")
            if not lease or lease.get("status") != "EXITED":
                return self._refuse("EPISODE_LIVENESS_AMBIGUOUS", prior.episode_id)
        streak = int(lease.get("failure_streak") or 0) if lease else 0
        prior_exit = None
        if lease:
            retry = _parse_time(lease.get("retry_not_before")) if lease.get("retry_not_before") else None
            if retry and self.clock() < retry:
                return self._refuse("DIRECTOR_EPISODE_CRASH_LOOP", lease["episode_id"],
                                    failure_streak=streak, retry_not_before=lease["retry_not_before"])
            # LAUNCH_FAILED: its child was killed at failure, so nothing is leased.
            prior_exit = (lease.get("exit_reason") or "PROCESS_EXITED") if lease["status"] == "EXITED" \
                else "LAUNCH_FAILED"
        episode_id = f"factory-director-{uuid.uuid4().hex}"
        launch_inputs, launch_fingerprint = asdict(values), self._fingerprint(values)
        # Reserve before spawning. A crash in the hand-off window stays visibly
        # ambiguous rather than creating an unleased child and a duplicate successor.
        _atomic_json(self._lease_path, {"host_id": self.host_id, "episode_id": episode_id,
                                        "pid": None, "started_at": _now(), "process_start_ticks": None,
                                        "status": "ACTIVATING", "keep_until_replaced": True,
                                        "retirement": "KEEP_UNTIL_REPLACED", "failure_streak": streak})
        bound_episode: Episode | None = None

        def bind_spawned(spawned: Episode) -> None:
            nonlocal bound_episode
            if (isinstance(spawned.pid, bool) or not isinstance(spawned.pid, int) or spawned.pid <= 0
                    or not isinstance(spawned.process_start_ticks, str) or not spawned.process_start_ticks):
                raise AmbiguousLease("spawned episode identity is invalid")
            _atomic_json(self._lease_path, {"host_id": self.host_id, **asdict(spawned),
                                            "status": "ACTIVE", "keep_until_replaced": True,
                                            "retirement": "KEEP_UNTIL_REPLACED", "failure_streak": streak,
                                            "launch_inputs": launch_inputs, "launch_fingerprint": launch_fingerprint})
            bound_episode = spawned

        try:
            episode = self.launcher.launch(episode_id, on_spawned=bind_spawned)
        except Exception as exc:
            if bound_episode is not None:
                return self._refuse("DIRECTOR_LAUNCH_HANDOFF_AMBIGUOUS", episode_id,
                                    provider=bound_episode.provider, requested_model=bound_episode.model)
            _atomic_json(self._lease_path, {"host_id": self.host_id, "episode_id": episode_id,
                                            "pid": None, "started_at": _now(), "process_start_ticks": None,
                                            "status": "LAUNCH_FAILED", "failure": str(exc)[:240],
                                            "keep_until_replaced": True, "retirement": "KEEP_UNTIL_REPLACED",
                                            "failure_streak": streak + 1,
                                            "retry_not_before": self._retry_not_before(streak + 1, self.clock())})
            return self._refuse("DIRECTOR_LAUNCH_FAILED", episode_id, failure=str(exc)[:240])
        reason = "PRIOR_EPISODE_EXITED_CONTROL_REMAINS" if lease else "DIRECTOR_CONTINUITY_FAULT"
        _atomic_json(self._lease_path, {"host_id": self.host_id, **asdict(episode),
                                        "status": "ACTIVE", "keep_until_replaced": True,
                                        "retirement": "KEEP_UNTIL_REPLACED", "failure_streak": streak,
                                        "launch_inputs": launch_inputs, "launch_fingerprint": launch_fingerprint})
        result = Reconciliation(HostState.ACTIVE, reason, episode.episode_id)
        self._record(result, exit_reason=prior_exit, provider=episode.provider, requested_model=episode.model,
                     inputs=launch_inputs)
        return result

    def wait_for_change(self, interval: float, poll: float = 1.0,
                        sleep: Callable[[float], None] = time.sleep) -> str:
        """Sleep up to ``interval``, returning early when the leased episode exits.

        This is what makes re-evaluation immediate after an episode exit without
        polling GitHub every second: only the cheap local liveness check repeats.
        """
        try:
            lease = self._lease()
            episode = self._episode(lease) if lease and lease.get("status") == "ACTIVE" else None
        except (AmbiguousLease, KeyError):
            episode = None
        liveness = self._liveness(episode) if episode is not None else None
        if liveness is False and self._lock_file is not None:
            # It exited before the wait began: reconcile at once. Crash-loop back-off is
            # enforced by reconcile, not by this wait. Only the lock holder can record the
            # exit, so any other host waits the interval rather than spinning.
            return "EPISODE_EXITED"
        if liveness is not True:
            # No leased episode, liveness unknown (reconcile refuses it), or not ours to record.
            sleep(interval)
            return "INTERVAL_ELAPSED"
        waited = 0.0
        while waited < interval:
            step = min(poll, interval - waited)
            sleep(step)
            waited += step
            if self._liveness(episode) is not True:
                return "EPISODE_EXITED"
        return "INTERVAL_ELAPSED"

    def inspect(self) -> Inspection:
        try:
            lease = self._lease()
        except AmbiguousLease:
            return Inspection(HostState.REFUSED, False, None, None, None, None, "AMBIGUOUS_LEASE")
        history = []
        if self._history_path.exists():
            for line in self._history_path.read_text().splitlines():
                try: history.append(json.loads(line))
                except json.JSONDecodeError: pass
        if lease and lease.get("status") == "ACTIVATING":
            return Inspection(HostState.REFUSED, False, lease.get("host_id"), lease.get("episode_id"),
                              None, None, "AMBIGUOUS_LEASE")
        try:
            liveness = (self._liveness(self._episode(lease)) if lease and lease.get("status") == "ACTIVE"
                        else False)
        except KeyError:
            return Inspection(HostState.REFUSED, False, None, None, None, None, "AMBIGUOUS_LEASE")
        if liveness is None:
            return Inspection(HostState.REFUSED, False, lease.get("host_id"), lease.get("episode_id"),
                              None, None, "EPISODE_LIVENESS_AMBIGUOUS")
        active = bool(liveness)
        latest = history[-1] if history else {}
        activation = next((r["reason"] for r in reversed(history) if r["reason"] in ACTIVATION_REASONS), None)
        exit_reason = next((r.get("exit_reason") for r in reversed(history) if r.get("exit_reason")), None)
        return Inspection(HostState.ACTIVE if active else HostState.IDLE, active,
                          lease.get("host_id") if lease else None, lease.get("episode_id") if lease else None,
                          activation, exit_reason, latest.get("reason"))


def load_launcher(config_path: Path | str, workdir: Path | str, prompt: Path | str,
                  state_root: Path | str) -> ProcessDirectorLauncher:
    raw = json.loads(Path(config_path).read_text())
    launcher = raw.get("launcher") if isinstance(raw, dict) else None
    if not isinstance(launcher, dict):
        raise ValueError("host configuration has no launcher section")
    return ProcessDirectorLauncher(workdir, prompt, provider=launcher.get("provider"),
                                   executable=launcher.get("executable"), model=launcher.get("model"),
                                   permission_mode=launcher.get("permissionMode"),
                                   output_dir=Path(state_root) / "episodes", require_isolated=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="non-cognizant Factory Director Host")
    parser.add_argument("--state-root", required=True, help="durable host state directory")
    parser.add_argument("--config", required=True, help="Factory Director Host configuration JSON")
    parser.add_argument("--workdir", required=True, help="dedicated linked Factory Director worktree")
    parser.add_argument("--prompt", required=True, help="Factory Director episode prompt")
    parser.add_argument("--interval-seconds", type=float, default=60.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--inspect", action="store_true")
    args = parser.parse_args(argv)
    from factory_director_inputs import AuthoritativeDirectorInputs
    inputs = AuthoritativeDirectorInputs(args.config, Path(args.state_root) / "inputs.json")
    host = FactoryDirectorHost(args.state_root, inputs,
                               load_launcher(args.config, args.workdir, args.prompt, args.state_root))
    if args.inspect:
        print(json.dumps(asdict(host.inspect()), default=lambda value: value.value, sort_keys=True))
        return 0
    try:
        while True:
            result = host.reconcile()
            print(json.dumps(asdict(result), default=lambda value: value.value, sort_keys=True), flush=True)
            if args.once:
                return 0
            host.wait_for_change(args.interval_seconds)
    finally:
        host.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
