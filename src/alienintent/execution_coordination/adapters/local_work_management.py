"""Local, fixture-contained Work Management transport for the offline proof substrate (S0).

The seeded READY view and every projection the kernel makes are durable under
the fixture root: the seed is written once and a reopened root that disagrees
with it is refused, and each receipt is appended and read back before it is
reported as confirmed. Nothing here decides lifecycle; it records what the
coordinator projects, exactly as the GitHub transport would.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, Mapping, Sequence

from alienintent.execution_coordination.domain.escalation import HumanDecisionRequired
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.ports.project_directory import ProjectSchema
from alienintent.execution_coordination.ports.work_management import ProjectionReceipt, ReadyWorkItem, WorkManagement, WorkRejected

SEED_FILE = "ready-snapshot.json"
RECEIPTS_FILE = "receipts.jsonl"


def seed_of(profile: str, repository: str, items: Sequence[ReadyWorkItem]) -> dict[str, object]:
    return {
        "profile": profile, "repository": repository,
        "items": [
            {
                "identity": item.identity, "fifo": item.fifo, "priority": item.priority, "dependencies": list(item.dependencies),
                "contract_digest": item.contract.content_digest, "readiness_digest": item.readiness_digest,
                "automatic_release": item.automatic_release,
            }
            for item in items
        ],
    }


class LocalWorkManagement(WorkManagement):
    def __init__(self, root: Path, profile: str, repository: str, items: Sequence[ReadyWorkItem], clock: Callable[[], float]) -> None:
        self.root, self.profile, self.repository = root, profile, repository
        self._items = tuple(items)
        self._clock = clock
        self.root.mkdir(parents=True, exist_ok=True)
        self.seed_path, self.receipts_path = self.root / SEED_FILE, self.root / RECEIPTS_FILE
        seed = seed_of(profile, repository, self._items)
        if self.seed_path.exists():
            if json.loads(self.seed_path.read_text(encoding="utf-8")) != seed:
                raise WorkRejected("reopened work-management root was seeded with different work")
            self.reopened = True
        else:
            self.seed_path.write_text(json.dumps(seed, indent=1, sort_keys=True) + "\n", encoding="utf-8")
            self.reopened = False

    # --- port ------------------------------------------------------------------

    def resolve_project(self) -> ProjectSchema:
        return ProjectSchema(
            f"local:{self.profile}", 0, f"{self.profile} local work management", "status",
            {stage.value: stage.value for stage in LifecycleStage}, "priority", {},
        )

    def import_ready_snapshot(self) -> tuple[ReadyWorkItem, ...]:
        return self._items

    def propose_release(self, item: ReadyWorkItem) -> None:
        self._append({"receipt": "release-proposed", "identity": item.identity, "contract_digest": item.contract.content_digest, "readiness_digest": item.readiness_digest})

    def project_execution_state(self, identity: str, state: str, revision: int = 0) -> ProjectionReceipt:
        entry = self._append({"receipt": "execution-state-projected", "identity": identity, "state": str(state), "revision": revision})
        confirmed = self.receipts()[-1] == entry
        return ProjectionReceipt(identity, revision, confirmed, f"receipt {entry['sequence']} read back from {self.receipts_path.name}")

    def project_decision_request(self, escalation: HumanDecisionRequired) -> ProjectionReceipt:
        entry = self._append({
            "receipt": "decision-requested", "identity": escalation.work_item, "biu_version": escalation.biu_version,
            "decision": escalation.decision, "reason": escalation.reason, "options": list(escalation.options),
            "recommendation": escalation.recommendation,
        })
        confirmed = self.receipts()[-1] == entry
        return ProjectionReceipt(escalation.work_item, escalation.biu_version, confirmed, f"receipt {entry['sequence']} read back from {self.receipts_path.name}")

    # --- durable receipts -----------------------------------------------------

    def receipts(self) -> tuple[dict[str, object], ...]:
        if not self.receipts_path.exists():
            return ()
        return tuple(json.loads(line) for line in self.receipts_path.read_text(encoding="utf-8").splitlines() if line.strip())

    def _append(self, record: Mapping[str, object]) -> dict[str, object]:
        entry = dict(record) | {"sequence": len(self.receipts()), "at": self._clock()}
        with self.receipts_path.open("a", encoding="utf-8") as sink:
            sink.write(json.dumps(entry, sort_keys=True) + "\n")
            sink.flush()
            os.fsync(sink.fileno())
        return entry
