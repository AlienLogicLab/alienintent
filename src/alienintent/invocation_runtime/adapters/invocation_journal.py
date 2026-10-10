"""JSONL invocation journal: the durable worker evidence record S0 introduced.

Records are fsynced and read back identically before an append returns, so a
reported record survives a restart of the process that wrote it.

BOUNDED-ROUTINE-LAUNCH: the journal stays the one canonical, append-only history. Beside it, `<journal>.by-work/` is
disposable acceleration state: a copy of each record under its `work_identity` and under its `correlation_id` (one
file per work item and one per correlation, so a record naming this correlation under another work item still reaches
the readers that check correlation), and
`covered`, how far into the journal the copies reach (byte offset, the journal's size, modification time and inode
when last read, and the SHA-256 of the last covered line). A routine reader asks for one work item's records (`work=`):
A routine reader asks for one work item's and one correlation's records (`work=`, `correlation=`):
under an exclusive lock the index first copies the journal lines past `covered` (a crash between a journal line and
its copy loses nothing), then those files are read, in journal order (a copy doubled by a crash is read once).
The index is rebuilt from position 0 whenever it cannot prove it still describes the journal: no index, an unreadable
`covered` or work file, `covered` past the journal's end or no longer ending at the same line, or a journal changed
other than by appending (replaced, or modified at the same size). So the cost of a routine read follows that item's
own history, and an index crash, omission, corruption or absence never hides a journal record. Appends and reads
take the same exclusive lock (`<journal>.lock`, outside the index), so sequences stay distinct across processes and no read sees a
copy being rebuilt; an append reads only the journal's last line, and an index failure after its line is durable does
not fail it (the next read catches up). Only an identical line is read once; two different records always both are.
Only this module writes the index; a single work file deleted by hand is not detected.
"""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
from hashlib import sha256
import json
import os
import shutil
from pathlib import Path
from typing import Callable, Iterator, Mapping

from alienintent.invocation_runtime.domain.runtime import JournalUnreadable
from alienintent.invocation_runtime.ports.invocation_journal import InvocationJournal


def journal_records(path: Path, work: str | None = None,
                    correlation: str | None = None) -> tuple[dict[str, object], ...]:
    """Every record of the durable JSONL worker journal at ``path``, or with ``work`` and/or ``correlation`` only the
    records naming that work item or that correlation, in journal order."""
    if work is None and correlation is None:
        if not path.exists():
            return ()
        return tuple(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    if not path.exists():
        return ()
    keys = [key for key in (_key("work", work), _key("correlation", correlation)) if key is not None]
    try:
        with _locked(path):
            try:
                _sync_index(path)
                lines = [line for key in keys for line in _work_lines(path, key)]
            except (OSError, ValueError):  # the index cannot be used as it is: rebuilt from the journal and read again
                _sync_index(path, rebuild=True)
                lines = [line for key in keys for line in _work_lines(path, key)]
        records = [json.loads(line) for line in dict.fromkeys(lines)]  # a crash-doubled copy is the identical line
        return tuple(sorted(records, key=lambda record: record.get("sequence", -1)))  # stable: file order on a tie
    except (OSError, ValueError, TypeError):
        # The index is disposable and the journal canonical: whatever is wrong with the index, the journal answers (and
        # a journal that cannot be read as records raises, as the full read does).
        every = journal_records(path)
        if not all(isinstance(record, dict) for record in every):
            raise ValueError("a journal line that is not a record")
        return tuple(record for record in every
                     if (work and record.get("work_identity") == work)
                     or (correlation and record.get("correlation_id") == correlation))


def _key(kind: str, value: object) -> str | None:
    return f"{kind}:{value}" if isinstance(value, str) and value else None


def _work_lines(path: Path, work: str) -> list[str]:
    """That work item's copied lines, each checked to parse; none when it has no file."""
    try:
        lines = [line for line in _work_file(path, work).read_text(encoding="utf-8").splitlines() if line.strip()]
    except FileNotFoundError:
        return []
    for line in lines:
        if not isinstance(json.loads(line), dict):
            raise ValueError("an index line that is not a record")
    return lines


def journal_append(path: Path, clock: Callable[[], float], record: Mapping[str, object]) -> dict[str, object]:
    """Append one record and read it back before reporting it; the journal is append-only."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with _locked(path):
        try:  # first notice any change made since the last sync, before this line moves the journal's size
            _sync_index(path)
        except (OSError, ValueError):
            pass  # the index is caught up by the next read
        last = _last_record(path)
        entry = dict(record) | {"sequence": 0 if last is None else int(last["sequence"]) + 1, "at": clock()}
        line = json.dumps(entry, sort_keys=True)
        with path.open("a", encoding="utf-8") as sink:
            sink.write(line + "\n")
            sink.flush()
            os.fsync(sink.fileno())
        if _last_record(path) != json.loads(line):
            raise JournalUnreadable("journal append did not read back identically")
        try:
            _sync_index(path)
        except (OSError, ValueError):
            pass  # the record is durable; the next read catches the index up
    return entry


@contextmanager
def _locked(path: Path) -> Iterator[None]:
    """The journal's one exclusive lock (`<journal>.lock`, outside the disposable index), held by every append and
    every work read."""
    with path.with_name(path.name + ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


# The index layout; an index written in any other layout is rebuilt from position 0.
INDEX_FORMAT = 2


def _index(path: Path) -> Path:
    return path.with_name(path.name + ".by-work")


def _work_file(path: Path, work: str) -> Path:
    return _index(path) / (sha256(work.encode("utf-8", "surrogatepass")).hexdigest() + ".jsonl")


def _last_record(path: Path) -> dict[str, object] | None:
    """The journal's last record, read from its end only."""
    try:
        handle = path.open("rb")
    except FileNotFoundError:
        return None
    with handle:
        size = handle.seek(0, os.SEEK_END)
        if size == 0:
            return None
        chunk = 4096
        while True:
            start = max(0, size - chunk)
            handle.seek(start)
            tail = handle.read(size - start).rstrip(b"\n")
            if b"\n" in tail or start == 0:
                return json.loads(tail.rpartition(b"\n")[2].decode("utf-8"))
            chunk *= 2


def _sync_index(path: Path, rebuild: bool = False) -> None:
    """Copy every journal line past `covered` into its work item's file and move `covered` to the last complete line;
    rebuild from position 0 when asked or when the index cannot prove it still describes the journal. Called only
    under `_locked`."""
    index = _index(path)
    if index.exists() and not index.is_dir():
        _remove(index)
    index.mkdir(exist_ok=True)
    with path.open("rb") as journal:
        seen = os.fstat(journal.fileno())
        state = _covered(index)
        if rebuild or state is None or not _describes(journal, seen, state):
            _clear(index)
            state = {"offset": 0, "last": None}
        offset = int(state["offset"])
        journal.seek(offset)
        new = journal.read(seen.st_size - offset)
    end = new.rfind(b"\n") + 1
    if new[end:].strip():  # every append is whole under the lock: a torn last line is a damaged journal
        raise ValueError("the journal's last line is incomplete")
    by_work: dict[str, list[bytes]] = {}
    for line in new[:end].splitlines():
        if line.strip():
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError("a journal line that is not a record")
            for key in {_key("work", record.get("work_identity")), _key("correlation", record.get("correlation_id"))}:
                if key is not None:
                    by_work.setdefault(key, []).append(line + b"\n")
    for work, copied in by_work.items():
        with _work_file(path, work).open("ab") as sink:
            sink.write(b"".join(copied))
            sink.flush()
            os.fsync(sink.fileno())
    last = state["last"] if end == 0 else sha256(new[:end - 1].rpartition(b"\n")[2]).hexdigest()
    temporary = index / "covered.tmp"
    _remove(temporary)
    temporary.write_text(json.dumps({"format": INDEX_FORMAT, "offset": offset + end, "size": seen.st_size, "mtime_ns": seen.st_mtime_ns,
                                     "inode": seen.st_ino, "last": last}))
    os.replace(temporary, index / "covered")


def _covered(index: Path) -> dict[str, object] | None:
    """The recorded `covered` state, or None when there is none or it cannot be read."""
    try:
        state = json.loads((index / "covered").read_text())
    except (OSError, ValueError):
        return None
    if not isinstance(state, dict) or state.get("format") != INDEX_FORMAT or type(state.get("offset")) is not int \
            or state["offset"] < 0:
        return None  # an index in another format is rebuilt; any other malformed field fails the sync, which rebuilds
    return state


def _describes(journal, seen: os.stat_result, state: Mapping[str, object]) -> bool:
    """Whether the index still describes this journal: the same file, never shorter, unchanged when its size is
    unchanged, and its covered prefix still ending, at `offset`, with the same last line."""
    offset = int(state["offset"])
    if state.get("inode") != seen.st_ino or seen.st_size < offset or seen.st_size < int(state.get("size") or 0):
        return False
    if seen.st_size == state.get("size") and seen.st_mtime_ns != state.get("mtime_ns"):
        return False
    if offset == 0:
        return state.get("last") is None
    journal.seek(offset - 1)
    if journal.read(1) != b"\n":
        return False
    return state.get("last") == sha256(_line_before(journal, offset - 1)).hexdigest()


def _line_before(journal, end: int) -> bytes:
    """The bytes of the line that ends at `end` (its newline excluded), read backwards from there only."""
    chunk = 4096
    while True:
        start = max(0, end - chunk)
        journal.seek(start)
        block = journal.read(end - start)
        if b"\n" in block or start == 0:
            return block.rpartition(b"\n")[2]
        chunk *= 2


def _clear(index: Path) -> None:
    """`covered` removed first (so an interrupted clear never vouches for removed copies), then every copy: the index
    is rebuilt from position 0."""
    _remove(index / "covered")
    for stale in index.glob("*.jsonl"):
        _remove(stale)


def _remove(path: Path) -> None:
    """Whatever is at `path` removed, file or folder (the index holds nothing worth keeping)."""
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


class JsonlInvocationJournal(InvocationJournal):
    def __init__(self, path: Path, clock: Callable[[], float]) -> None:
        self.path, self._clock = Path(path), clock

    def append(self, record: Mapping[str, object]) -> dict[str, object]:
        return journal_append(self.path, self._clock, record)

    def records(self, work: str | None = None, correlation: str | None = None) -> tuple[dict[str, object], ...]:
        """Every record, or with `work` and/or `correlation` only the records naming them (the routine read)."""
        try:
            return journal_records(self.path, work, correlation)
        except (OSError, ValueError) as error:
            raise JournalUnreadable("journal cannot be read back") from error
