#!/usr/bin/env python3
"""Temporary non-cognizant supervision for bounded Factory Director episodes.

This is intentionally infrastructure, not a second Director: it only evaluates a
closed activation predicate, keeps one durable lease, and starts a fresh Codex
episode.  The episode reconstructs and decides from authoritative state.
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
from datetime import datetime, timezone
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


class JsonDirectorInputs:
    """Strict adapter for a durable, externally-produced factory state projection.

    The host does not infer missing authority from a queue or process list.  An operator
    or existing control-plane adapter must publish every predicate atomically; malformed,
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


class InMemoryDirectorLauncher:
    """Test-only launch port; production uses a process launcher."""
    def __init__(self) -> None:
        self.launched: list[Episode] = []
        self._active: dict[str, bool] = {}
        self._exits: dict[str, int] = {}
        self._next_pid = 10_000

    def launch(self, episode_id: str, on_spawned: Callable[[Episode], None] | None = None) -> Episode:
        pid = self._next_pid
        self._next_pid += 1
        episode = Episode(episode_id, pid, _now(), f"memory-{pid}")
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

    def finish(self, episode_id: str, exit_code: int = 0) -> None:
        self._active[episode_id] = False
        self._exits[episode_id] = exit_code


class ProcessDirectorLauncher:
    """Starts a fresh bounded Codex episode; no conversation is resumed or inherited."""
    def __init__(self, workdir: Path | str, prompt_file: Path | str,
                 codex: str | None = None, model: str | None = None,
                 require_isolated: bool = False) -> None:
        self.workdir, self.prompt_file = Path(workdir), Path(prompt_file)
        self.codex, self.model = codex or str(Path.home() / ".local/bin/codex"), model
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

    def launch(self, episode_id: str, on_spawned: Callable[[Episode], None] | None = None) -> Episode:
        from codex_session import FILTERED_ENV
        from director import resolved_codex_model
        output = self.workdir / ".factory-director-host" / f"{episode_id}.last-message.txt"
        output.parent.mkdir(parents=True, exist_ok=True)
        model = self.model or resolved_codex_model()
        prompt = self.prompt_file.read_text().replace("{{EPISODE_ID}}", episode_id)
        argv = [self.codex, "exec", "--cd", str(self.workdir), "--ephemeral",
                "--sandbox", "workspace-write", "--model", model,
                "--output-last-message", str(output), "-"]
        env = {k: v for k, v in os.environ.items() if k not in FILTERED_ENV}
        child = subprocess.Popen(argv, stdin=subprocess.PIPE, text=True, env=env)
        episode = Episode(episode_id, child.pid, _now(), self._process_start_ticks(child.pid))
        if on_spawned is not None:
            if not isinstance(episode.process_start_ticks, str) or not episode.process_start_ticks:
                raise RuntimeError("spawned child process identity is unavailable")
            on_spawned(episode)
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
        return "PROCESS_EXITED" if not self.is_active(episode) else None


class FactoryDirectorHost:
    def __init__(self, state_root: Path | str, inputs: Callable[[], DirectorInputs], launcher) -> None:
        self.root, self.inputs, self.launcher = Path(state_root), inputs, launcher
        self.host_id = f"fdh-{uuid.uuid4().hex}"
        self._lock_file = None

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
            if not isinstance(value, dict) or set(value) < required:
                raise ValueError("lease schema is incomplete")
            if not isinstance(value["host_id"], str) or not isinstance(value["episode_id"], str):
                raise ValueError("lease identity is invalid")
            if value["pid"] is not None and not isinstance(value["pid"], int):
                raise ValueError("lease pid is invalid")
            if value["status"] not in {"ACTIVATING", "ACTIVE", "LAUNCH_FAILED"}:
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
                       lease.get("process_start_ticks"))

    def _record(self, reconciliation: Reconciliation, *, exit_reason: str | None = None) -> None:
        record = {"at": _now(), "reason": reconciliation.reason, "state": reconciliation.state.value,
                  "episode_id": reconciliation.episode_id, "exit_reason": exit_reason}
        self._history_path.parent.mkdir(parents=True, exist_ok=True)
        with self._history_path.open("a") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")

    def _idle_reason(self, values: DirectorInputs) -> str | None:
        if not values.authoritative_state: return "AUTHORITATIVE_STATE_UNAVAILABLE"
        if values.explicit_pause: return "FACTORY_PAUSED"
        if values.founder_decision_pending: return "FOUNDER_DECISION_PENDING"
        if values.wip_intentionally_full and not any((values.attention_required, values.pending_director_inbox,
                                                       values.lifecycle_requires_selection)):
            return "WIP_INTENTIONALLY_FULL"
        if not values.control_required(): return "NO_ELIGIBLE_AUTHORIZED_WORK"
        if not values.executable_capacity: return "EXECUTION_CAPACITY_UNAVAILABLE"
        return None

    def reconcile(self) -> Reconciliation:
        if not self.start():
            result = Reconciliation(HostState.REFUSED, "CONFLICTING_HOST_OWNERSHIP")
            self._record(result)
            return result
        values = self.inputs()
        idle = self._idle_reason(values)
        if idle:
            result = Reconciliation(HostState.IDLE if idle in {"FACTORY_PAUSED", "FOUNDER_DECISION_PENDING", "WIP_INTENTIONALLY_FULL", "NO_ELIGIBLE_AUTHORIZED_WORK"} else HostState.REFUSED, idle)
            self._record(result)
            return result
        try:
            lease = self._lease()
        except AmbiguousLease:
            result = Reconciliation(HostState.REFUSED, "AMBIGUOUS_LEASE")
            self._record(result)
            return result
        prior_exit = None
        if lease:
            if lease.get("status") == "ACTIVATING":
                result = Reconciliation(HostState.REFUSED, "AMBIGUOUS_LEASE")
                self._record(result)
                return result
            try:
                prior = self._episode(lease)
            except KeyError:
                result = Reconciliation(HostState.REFUSED, "AMBIGUOUS_LEASE")
                self._record(result)
                return result
            if prior.pid is not None and prior.process_start_ticks is None:
                result = Reconciliation(HostState.REFUSED, "AMBIGUOUS_LEASE")
                self._record(result)
                return result
            liveness = self.launcher.liveness(prior) if hasattr(self.launcher, "liveness") else self.launcher.is_active(prior)
            if liveness is None:
                result = Reconciliation(HostState.REFUSED, "EPISODE_LIVENESS_AMBIGUOUS", prior.episode_id)
                self._record(result)
                return result
            if liveness:
                result = Reconciliation(HostState.ACTIVE, "DIRECTOR_EPISODE_ACTIVE", prior.episode_id)
                self._record(result)
                return result
            prior_exit = self.launcher.exit_reason(prior) or "EPISODE_LIVENESS_AMBIGUOUS"
        episode_id = f"factory-director-{uuid.uuid4().hex}"
        # Reserve before spawning. A crash in the hand-off window stays visibly
        # ambiguous rather than creating an unleased child and a duplicate successor.
        _atomic_json(self._lease_path, {"host_id": self.host_id, "episode_id": episode_id,
                                        "pid": None, "started_at": _now(), "process_start_ticks": None,
                                        "status": "ACTIVATING", "keep_until_replaced": True,
                                        "retirement": "KEEP_UNTIL_REPLACED"})
        bound_episode: Episode | None = None

        def bind_spawned(spawned: Episode) -> None:
            nonlocal bound_episode
            if (isinstance(spawned.pid, bool) or not isinstance(spawned.pid, int) or spawned.pid <= 0
                    or not isinstance(spawned.process_start_ticks, str) or not spawned.process_start_ticks):
                raise AmbiguousLease("spawned episode identity is invalid")
            _atomic_json(self._lease_path, {"host_id": self.host_id, **asdict(spawned),
                                            "status": "ACTIVE", "keep_until_replaced": True,
                                            "retirement": "KEEP_UNTIL_REPLACED"})
            bound_episode = spawned

        try:
            episode = self.launcher.launch(episode_id, on_spawned=bind_spawned)
        except Exception as exc:
            if bound_episode is not None:
                result = Reconciliation(HostState.REFUSED, "DIRECTOR_LAUNCH_HANDOFF_AMBIGUOUS", episode_id)
                self._record(result)
                return result
            _atomic_json(self._lease_path, {"host_id": self.host_id, "episode_id": episode_id,
                                            "pid": None, "started_at": _now(), "process_start_ticks": None,
                                            "status": "LAUNCH_FAILED", "failure": str(exc)[:240],
                                            "keep_until_replaced": True, "retirement": "KEEP_UNTIL_REPLACED"})
            result = Reconciliation(HostState.REFUSED, "DIRECTOR_LAUNCH_FAILED", episode_id)
            self._record(result)
            return result
        reason = "PRIOR_EPISODE_EXITED_CONTROL_REMAINS" if lease else "DIRECTOR_CONTINUITY_FAULT"
        _atomic_json(self._lease_path, {"host_id": self.host_id, **asdict(episode),
                                        "status": "ACTIVE", "keep_until_replaced": True,
                                        "retirement": "KEEP_UNTIL_REPLACED"})
        result = Reconciliation(HostState.ACTIVE, reason, episode.episode_id)
        self._record(result, exit_reason=prior_exit)
        return result

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
        try:
            liveness = (self.launcher.liveness(self._episode(lease)) if lease and hasattr(self.launcher, "liveness")
                        else self.launcher.is_active(self._episode(lease)) if lease else False)
        except KeyError:
            return Inspection(HostState.REFUSED, False, None, None, None, None, "AMBIGUOUS_LEASE")
        if liveness is None:
            return Inspection(HostState.REFUSED, False, lease.get("host_id"), lease.get("episode_id"),
                              None, None, "EPISODE_LIVENESS_AMBIGUOUS")
        active = bool(liveness)
        latest = history[-1] if history else {}
        activation = next((r["reason"] for r in reversed(history) if r["reason"] in {"DIRECTOR_CONTINUITY_FAULT", "PRIOR_EPISODE_EXITED_CONTROL_REMAINS"}), None)
        exit_reason = next((r.get("exit_reason") for r in reversed(history) if r.get("exit_reason")), None)
        return Inspection(HostState.ACTIVE if active else HostState.IDLE, active,
                          lease.get("host_id") if lease else None, lease.get("episode_id") if lease else None,
                          activation, exit_reason, latest.get("reason"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="temporary non-cognizant Factory Director Host")
    parser.add_argument("--state-root", required=True, help="durable host state directory")
    parser.add_argument("--inputs", required=True, help="atomic authoritative predicate projection")
    parser.add_argument("--workdir", required=True, help="canonical AlienIntent checkout")
    parser.add_argument("--prompt", required=True, help="Factory Director episode prompt")
    parser.add_argument("--interval-seconds", type=float, default=2.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--inspect", action="store_true")
    args = parser.parse_args(argv)
    host = FactoryDirectorHost(args.state_root, JsonDirectorInputs(args.inputs),
                               ProcessDirectorLauncher(args.workdir, args.prompt, require_isolated=True))
    if args.inspect:
        print(json.dumps(asdict(host.inspect()), default=lambda value: value.value, sort_keys=True))
        return 0
    try:
        while True:
            result = host.reconcile()
            print(json.dumps(asdict(result), default=lambda value: value.value, sort_keys=True), flush=True)
            if args.once:
                return 0
            time.sleep(args.interval_seconds)
    finally:
        host.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
