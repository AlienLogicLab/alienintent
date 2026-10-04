"""Linux ``/proc`` observation of invocation ownership (WO-220404 AC-08).

Two questions, both answered from the kernel rather than from any caller claim:

- whether the control-plane process that journaled an invocation has
  conclusively ended. A process is identified by pid, its kernel start time and
  the boot it ran in, so a reused pid or a later boot never reads as the owner
  still running;
- which live processes still carry an invocation's marker. Every worker child
  is launched with ``ALIENINTENT_INVOCATION_ID`` and ``ALIENINTENT_INVOCATION_OWNER``
  in its stated environment and every descendant inherits them, including work
  that detached into its own session or redirected its output away from the
  supervisor. The owner marker binds the work to the process that started it,
  since an invocation identity alone repeats across profiles.

With a worker user (unit WORKER-CREDENTIAL-BOUNDARY) the worker's environment cannot be read by the control
plane, so owned work is every live process of that real uid in the launched session (``/proc/<pid>/status`` and
``/proc/<pid>/stat``, both readable across users), and any process of that uid outside the session that cannot be
read answers ``None`` (alive, not known). Another user's process is never the worker's.

Anything that cannot be read is ``unknown`` (or ``None``), never ``terminated``.
A descendant that clears its environment, or makes itself unreadable, is not
observed: a missing marker is not proof of absence beyond that boundary.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from alienintent.invocation_runtime.domain.runtime import INVOCATION_MARKER, INVOCATION_OWNER_MARKER
from alienintent.invocation_runtime.ports.process_ownership import ProcessOwnership

ALIVE, TERMINATED, UNKNOWN = "alive", "terminated", "unknown"


class ProcOwnership(ProcessOwnership):
    def __init__(self, proc: Path = Path("/proc"), *, worker_uid: int | None = None) -> None:
        self._proc = Path(proc)
        self._worker_uid = worker_uid

    def _real_uid(self, pid: int) -> int | None:
        """The real uid of ``pid`` from ``/proc/<pid>/status`` (world-readable), or None."""
        try:
            for line in (self._proc / str(pid) / "status").read_text(encoding="ascii", errors="replace").splitlines():
                if line.startswith("Uid:"):
                    return int(line.split()[1])
        except (OSError, ValueError, IndexError):
            return None
        return None

    def _session(self, pid: int) -> tuple[str, int]:
        """(state, session id) of ``pid`` from ``/proc/<pid>/stat``."""
        raw = (self._proc / str(pid) / "stat").read_text(encoding="ascii", errors="replace")
        fields = raw[raw.rindex(")") + 2:].split()
        return fields[0], int(fields[3])

    def _worker_owned(self, invocation_id: str, owner: str | None, session: int | None,
                      candidates: list[Path]) -> tuple[int, ...] | None:
        marker = f"{INVOCATION_MARKER}={invocation_id}".encode()
        prefix = f"{INVOCATION_OWNER_MARKER}=".encode()
        owned, unreadable = [], False
        for entry in candidates:
            pid = int(entry.name)
            if self._real_uid(pid) != self._worker_uid:
                continue  # another user's process (root's included) is never the worker's
            try:
                state, sid = self._session(pid)
            except (OSError, ValueError, IndexError):
                continue  # gone meanwhile
            if state in {"Z", "X"}:
                continue
            if session is not None and sid == session:
                owned.append(pid)
                continue
            try:
                variables = (entry / "environ").read_bytes().split(b"\0")
            except OSError:
                unreadable = True  # a worker process outside the session that cannot be read: alive, not known
                continue
            if marker not in variables:
                continue
            if owner is not None:
                started_by = next((v[len(prefix):].decode(errors="replace") for v in variables if v.startswith(prefix)), None)
                if started_by is None or (started_by != owner and not started_by.startswith(owner + "/")):
                    continue
            owned.append(pid)
        return None if unreadable else tuple(sorted(owned))

    def _boot(self) -> str | None:
        try:
            return (self._proc / "sys/kernel/random/boot_id").read_text(encoding="ascii").strip() or None
        except OSError:
            return None

    def _stat(self, pid: int) -> tuple[str, int] | None:
        """(state, start time in clock ticks since boot) of ``pid``, or None when it does not exist."""
        raw = (self._proc / str(pid) / "stat").read_text(encoding="ascii", errors="replace")
        fields = raw[raw.rindex(")") + 2:].split()
        return fields[0], int(fields[19])

    def _pid_namespace(self) -> int | None:
        try:
            return (self._proc / "self/ns/pid").stat().st_ino
        except OSError:
            return None

    def current(self) -> Mapping[str, object] | None:
        pid, boot, namespace = os.getpid(), self._boot(), self._pid_namespace()
        try:
            _, start = self._stat(pid)  # type: ignore[misc]
        except (OSError, ValueError, IndexError):
            return None
        return None if boot is None or namespace is None else {"pid": pid, "start": start, "boot": boot, "pidns": namespace}

    def owner_state(self, owner: Mapping[str, object]) -> str:
        pid, start, boot = owner.get("pid"), owner.get("start"), owner.get("boot")
        if type(pid) is not int or type(start) is not int or not isinstance(boot, str) or pid <= 0:
            return UNKNOWN
        current = self._boot()
        if current is None:
            return UNKNOWN
        if current != boot:
            # Every process of an earlier boot has ended.
            return TERMINATED
        if owner.get("pidns") != self._pid_namespace():
            # Another pid namespace's pids cannot be observed from here.
            return UNKNOWN
        try:
            state, started = self._stat(pid)  # type: ignore[misc]
        except FileNotFoundError:
            return TERMINATED
        except (OSError, ValueError, IndexError):
            return UNKNOWN
        if started != start or state in {"Z", "X"}:
            return TERMINATED
        return ALIVE

    def owned_work(self, invocation_id: str, owner: str | None = None, *,
                   session: int | None = None) -> tuple[int, ...] | None:
        """Live processes carrying this invocation's marker (and, given ``owner``, started under that owner).

        ``owner`` is either one supervisor's exact owner marker or an owner
        token, which matches every supervisor that owner process ran. With a
        worker uid: the worker's processes in ``session`` (the launched sudo
        pid) and its readable marked processes elsewhere; None when one of its
        processes outside the session cannot be read.
        """
        marker = f"{INVOCATION_MARKER}={invocation_id}".encode()
        prefix = f"{INVOCATION_OWNER_MARKER}=".encode()
        try:
            candidates = [entry for entry in self._proc.iterdir() if entry.name.isdigit()]
        except OSError:
            return None
        if self._worker_uid is not None:
            return self._worker_owned(invocation_id, owner, session, candidates)
        owned = []
        for entry in candidates:
            try:
                variables = (entry / "environ").read_bytes().split(b"\0")
                if marker not in variables:
                    continue
                if owner is not None:
                    started_by = next((v[len(prefix):].decode(errors="replace") for v in variables if v.startswith(prefix)), None)
                    if started_by is None or (started_by != owner and not started_by.startswith(owner + "/")):
                        continue
                state, _ = self._stat(int(entry.name))  # type: ignore[misc]
            except (OSError, ValueError, IndexError):
                # Gone meanwhile, or another user's process that cannot carry our marker.
                continue
            if state not in {"Z", "X"}:
                owned.append(int(entry.name))
        return tuple(sorted(owned))
