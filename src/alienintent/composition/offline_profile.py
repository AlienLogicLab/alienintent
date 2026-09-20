"""Composition root for the PY-04 offline walking-skeleton profile."""
from __future__ import annotations

from pathlib import Path

from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
from alienintent.execution_coordination.ports.work_management import WorkManagement
from alienintent.execution_coordination.ports.worker_provider import WorkerProvider


class OfflineProfile:
    def __init__(self, database: Path, work: WorkManagement, worker: WorkerProvider, artifact_root: Path, *, name: str = "offline") -> None:
        self.coordinator = FactoryCoordinator(SQLiteOperationalStore(database), work, worker, LocalArtifactStore(artifact_root), name)
