"""Compose the isolated one-writer cutover rehearsal (WO-220503, FX-E2); no live writer is reachable from it."""

from __future__ import annotations

import json
from pathlib import Path

from alienintent.execution_coordination.adapters.cutover_files import (
    FileCheckpointStore, FileWriterAuthority, ProcNodeWriterObservation,
)
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.cutover import OneWriterCutover
from alienintent.execution_coordination.ports.cutover import NodeWriterObservation

PROFILE = "cutover-rehearsal"


def live_must_not_touch(home: Path) -> tuple[Path, ...]:
    """The live Node writer's configuration and state, and the live Python sandbox profile and store."""
    guarded = [home / ".config/alienintent", home / ".config/alienintent-sandbox",
               home / ".local/state/alienintent-sandbox"]
    try:
        state_file = json.loads((home / ".config/alienintent/self-hosting.json").read_text())["paths"]["stateFile"]
        guarded.append(Path(state_file).expanduser())
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return tuple(guarded)


def rehearsal(root: Path, *, canonical_control: bool, home: Path | None = None,
              observation: NodeWriterObservation | None = None,
              extra_must_not_touch: tuple[Path, ...] = ()) -> OneWriterCutover:
    """Bind a rehearsal on `root`: `node-state.json` (a Node state copy) and `python-store.sqlite`."""
    guarded = live_must_not_touch(home or Path.home()) + extra_must_not_touch
    cutover = OneWriterCutover(
        scope=f"rehearsal:{root}", root=root, node_state=root / "node-state.json",
        python_store_path=root / "python-store.sqlite", store=None,  # type: ignore[arg-type]
        profile=PROFILE, authority=FileWriterAuthority(root / "writer-authority.json"),
        checkpoints=FileCheckpointStore(root / "checkpoints"),
        observation=observation or ProcNodeWriterObservation((str(root),)),
        must_not_touch=guarded, canonical_control=canonical_control)
    cutover.check_isolation()  # before the store file is created
    cutover.store = SQLiteOperationalStore(root / "python-store.sqlite")
    return cutover
