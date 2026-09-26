"""File-backed writer-authority record and checkpoint store for the isolated cutover rehearsal."""

from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path
import time
from typing import Callable, Iterator, Mapping

from alienintent.execution_coordination.domain.cutover import CutoverHold
from alienintent.execution_coordination.ports.cutover import CheckpointStore, NodeWriterObservation, WriterAuthorityStore
from alienintent.execution_coordination.ports.operational_store import VersionConflict


def _digest(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(data)
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


class FileWriterAuthority(WriterAuthorityStore):
    """One JSON record; every change is compare-and-set on epoch under an exclusive lock file."""

    def __init__(self, path: Path, *, lock_timeout: float = 5.0) -> None:
        self.path = path
        self.lock_timeout = lock_timeout

    @contextmanager
    def _locked(self) -> Iterator[None]:
        lock = self.path.with_name(self.path.name + ".lock")
        deadline = time.monotonic() + self.lock_timeout
        while True:
            try:
                descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                break
            except FileExistsError:
                if time.monotonic() > deadline:
                    raise CutoverHold("WRITER_RECORD_LOCKED")
                time.sleep(0.01)
        try:
            yield
        finally:
            os.close(descriptor)
            lock.unlink()

    def read(self) -> Mapping[str, object] | None:
        try:
            return json.loads(self.path.read_bytes())
        except FileNotFoundError:
            return None
        except ValueError as error:
            raise CutoverHold("WRITER_RECORD_INVALID") from error

    def create(self, record: Mapping[str, object]) -> None:
        with self._locked():
            if self.path.exists():
                raise VersionConflict("writer record already exists")
            _atomic_write(self.path, json.dumps(record, sort_keys=True).encode())

    def replace(self, expected_epoch: int, record: Mapping[str, object]) -> None:
        with self._locked():
            current = self.read()
            if current is None or current.get("epoch") != expected_epoch:
                raise VersionConflict(f"expected writer epoch {expected_epoch}")
            _atomic_write(self.path, json.dumps(record, sort_keys=True).encode())


class FileCheckpointStore(CheckpointStore):
    """Checkpoint = Node state bytes + SQLite online backup of the Python store + a digest manifest."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def create(self, node_state: Path, python_store: Path, backup: Callable[[Path], None]) -> str:
        node_bytes = node_state.read_bytes()
        identity = "checkpoint-" + sha256(node_bytes + python_store.read_bytes()).hexdigest()[:16]
        target = self.root / identity
        target.mkdir(parents=True, exist_ok=False)
        (target / "node-state.json").write_bytes(node_bytes)
        backup(target / "python-store.sqlite")  # the store owner's online backup
        members = {name: _digest((target / name).read_bytes()) for name in ("node-state.json", "python-store.sqlite")}
        manifest = {"schema_version": 1, "checkpoint": identity, "members": members,
                    "source": {"node_state": str(node_state), "python_store": str(python_store)}}
        (target / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        return identity

    def verify(self, checkpoint: str) -> Mapping[str, object]:
        target = self.root / checkpoint
        try:
            manifest = json.loads((target / "manifest.json").read_text())
            members = manifest["members"]
            bad = tuple(name for name, digest in sorted(members.items()) if _digest((target / name).read_bytes()) != digest)
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise CutoverHold("CHECKPOINT_CORRUPT", (checkpoint,)) from error
        if bad or set(members) != {"node-state.json", "python-store.sqlite"}:
            raise CutoverHold("CHECKPOINT_CORRUPT", bad or (checkpoint,))
        return manifest

    def node_state(self, checkpoint: str) -> bytes:
        self.verify(checkpoint)
        return (self.root / checkpoint / "node-state.json").read_bytes()


class ProcNodeWriterObservation(NodeWriterObservation):
    """Observe a Node writer bound to the rehearsal: a Node process whose argv names one of its markers.

    The rehearsal passes its own root as the marker, so the unrelated live Node writer is neither
    counted nor touched; in a live cutover the marker would be that writer's own entry and profile.
    """

    def __init__(self, entry_markers: tuple[str, ...], proc: Path = Path("/proc")) -> None:
        self.entry_markers = entry_markers
        self.proc = proc

    def live_node_writer(self) -> tuple[str, ...]:
        found = []
        for entry in self.proc.glob("[0-9]*/cmdline"):
            try:
                argv = entry.read_bytes().split(b"\0")
            except OSError:
                continue
            text = [part.decode(errors="replace") for part in argv if part]
            if text and Path(text[0]).name.startswith("node") and any(m in part for part in text for m in self.entry_markers):
                found.append(entry.parent.name)
        return tuple(sorted(found))

    def pid_alive(self, pid: int) -> bool:
        return (self.proc / str(pid)).exists()
