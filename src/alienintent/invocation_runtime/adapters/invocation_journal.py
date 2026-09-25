"""JSONL invocation journal: the durable worker evidence record S0 introduced.

Records are fsynced and read back identically before an append returns, so a
reported record survives a restart of the process that wrote it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, Mapping

from alienintent.invocation_runtime.domain.runtime import JournalUnreadable
from alienintent.invocation_runtime.ports.invocation_journal import InvocationJournal


def journal_records(path: Path) -> tuple[dict[str, object], ...]:
    """Every record of the durable JSONL worker journal at ``path``."""
    if not path.exists():
        return ()
    return tuple(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def journal_append(path: Path, clock: Callable[[], float], record: Mapping[str, object]) -> dict[str, object]:
    """Append one record and read it back before reporting it; the journal is append-only."""
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = dict(record) | {"sequence": len(journal_records(path)), "at": clock()}
    line = json.dumps(entry, sort_keys=True)
    with path.open("a", encoding="utf-8") as sink:
        sink.write(line + "\n")
        sink.flush()
        os.fsync(sink.fileno())
    read_back = journal_records(path)
    if not read_back or read_back[-1] != json.loads(line):
        raise JournalUnreadable("journal append did not read back identically")
    return entry


class JsonlInvocationJournal(InvocationJournal):
    def __init__(self, path: Path, clock: Callable[[], float]) -> None:
        self.path, self._clock = Path(path), clock

    def append(self, record: Mapping[str, object]) -> dict[str, object]:
        return journal_append(self.path, self._clock, record)

    def records(self) -> tuple[dict[str, object], ...]:
        try:
            return journal_records(self.path)
        except (OSError, ValueError) as error:
            raise JournalUnreadable("journal cannot be read back") from error
