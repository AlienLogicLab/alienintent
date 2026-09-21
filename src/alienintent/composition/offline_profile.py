"""Composition root for the PY-04 offline profile."""

from pathlib import Path
from typing import TYPE_CHECKING

from alienintent.control_plane.adapters.decision_notifier import NoOpDecisionNotifier
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
from alienintent.execution_coordination.ports.work_management import WorkManagement
from alienintent.execution_coordination.ports.worker_provider import WorkerProvider

if TYPE_CHECKING:
    from alienintent.installation.application.doctor import DoctorService


class OfflineProfile:
    def __init__(self, database: Path, work: WorkManagement, worker: WorkerProvider, artifact_root: Path, verifier_root: Path | None = None, *, name: str = "offline", automatic_release: bool = True, doctor: "DoctorService | None" = None) -> None:
        self.name = name
        self.store = SQLiteOperationalStore(database)
        self.work = work
        self.coordinator = FactoryCoordinator(self.store, work, worker, LocalArtifactStore(artifact_root, verifier_root or artifact_root / "verifier-evidence"), name, automatic_release=automatic_release, notifier=NoOpDecisionNotifier())
        self.doctor = doctor

    def readiness(self) -> bool:
        """PY-09 owns substantive doctor checks; PY-08 supplies this injected gate."""
        return self.doctor is not None and self.doctor.run().ready
