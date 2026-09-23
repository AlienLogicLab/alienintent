"""One explicit evidence repository and access/authority policy per profile."""
from pathlib import Path
from hashlib import sha256

from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.application.evidence_service import EvidenceService
from alienintent.evidence_learning.domain.admission import AuthoritySnapshot
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.execution_coordination.adapters.evidence_verdict_bridge import EvidenceVerdictBridge
from alienintent.execution_coordination.domain import verdict as execution_policy
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.ports.operational_store import OperationalStore


class EvidenceProfile:
    def __init__(self, evidence_root: Path, *, permitted_root: Path, project: str, name: str,
                 authority: AuthoritySnapshot, database: Path | None = None,
                 store: OperationalStore | None = None, access_scope: frozenset[str] = frozenset({"public", "private"}),
                 max_bytes: int = 10 * 1024 * 1024) -> None:
        root, permitted = Path(evidence_root), Path(permitted_root).resolve()
        if not root.resolve().is_relative_to(permitted) or root.resolve() == permitted:
            raise EvidenceHold("UNSAFE_ROOT", required_action="choose evidence_root beneath the declared permitted external root")
        if (database is None) == (store is None):
            raise EvidenceHold("STORE_CONFIGURATION", required_action="supply exactly one database or existing OperationalStore")
        self.name, self.project, self.authority, self.access_scope = name, project, authority, access_scope
        self.store = store if store is not None else SQLiteOperationalStore(database)
        self.repository = LocalEvidenceRepository(root, project, name, max_bytes=max_bytes)
        self.service = EvidenceService(self.repository, self.store, project, name, authority, access_scope)
        policy_ref = Ref(project, name, "execution-verdict", "sha256:" + sha256(Path(execution_policy.__file__).read_bytes()).hexdigest(),
                         "python:alienintent.execution_coordination.domain.verdict")
        self.verdict = EvidenceVerdictBridge(self.service, authority, policy_ref, execution_policy.evaluate_verdict)
        # Admission checks use the already-read catalog value, never a recursive read.
        self.service.verdict_admission = self.verdict
