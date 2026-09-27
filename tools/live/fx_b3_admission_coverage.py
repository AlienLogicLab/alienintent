#!/usr/bin/env python3
"""FX-B3 pre-execution coverage probe (WO-220506, Issue #126) — LOCAL, labelled FX-L1-equivalent.

The BIU's own proof order requires pinning the fixture against the node predicate *before* any
operational write. This probe runs every pinned FX-B3/FX-B4 case (WO-220506.md steps 2-8) plus the
six DAG B3 release preconditions (`docs/evidence/wave2-dependency-dag.json`, node B3
`release_preconditions`) through the real canonical prelaunch call site:
`FactoryCoordinator._run` -> `admit_release` (`factory_coordinator.py:255-268`), composed over the real
`SQLiteOperationalStore` and `GitHubProjectsWorkManagement`. Only two things are local: the Project
snapshot rows (the upstream read, which the operational phases would take from GitHub) and the worker
(a counting double that returns `authority-block`, so no lifecycle progresses and no process starts).

It touches no network, no GitHub repository/Project, no provider and no credential. Its result is
NOT operational evidence and cannot satisfy FX-B3/FX-B4 acceptance; it only establishes, before any
Project #1 write, whether the pinned expected outcomes are reachable at that call site.

    python3 tools/live/fx_b3_admission_coverage.py [--out result.json]

Exit 0 when every case's observed launch count equals its expected count; exit 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

from alienintent.execution_coordination.adapters.github_work_management import GitHubProjectsWorkManagement
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation, WorkerOutcome

REPOSITORY = "AlienLogicLab/alienintent"
PROFILE = "fx-b3-local-coverage"
LABEL = "LOCAL_FX_L1_EQUIVALENT — not operational evidence; cannot satisfy FX-B3/FX-B4 acceptance"
DENIAL = "Implementation is **not** authorized by this Issue. Release remains an explicit authority step."
UNRESOLVABLE_BASELINE = "0" * 40


class CountingWorker:
    """A WorkerProvider double: records every start and answers a correlated authority-block."""

    def __init__(self) -> None:
        self.starts: list[str] = []
        self._outcomes: dict[str, WorkerOutcome] = {}

    def start(self, invocation: WorkerInvocation, contract: BiuContract, capabilities, budget) -> WorkerOutcome:
        self.starts.append(invocation.correlation_id)
        self._outcomes[invocation.correlation_id] = WorkerOutcome("authority-block")
        return self._outcomes[invocation.correlation_id]

    def read_back(self, invocation: WorkerInvocation) -> WorkerOutcome | None:
        return self._outcomes.get(invocation.correlation_id)

    def cancel(self, identity: str, reason: str) -> None:  # pragma: no cover - never reached
        raise AssertionError("the probe never cancels")


def contract(identity: str, **overrides) -> BiuContract:
    values = dict(
        identity=identity, version="1", intent="FX-B3 coverage probe scaffolding; never executed",
        satisfied_requirement_ids=("SF-REQ-015",), fixed_decisions=("FX-B3",), authorized_scope=("none",),
        excluded_scope=("everything",), dependencies=(), required_capabilities=("python",),
        budget_policy=BudgetPolicy(hard_required_dimensions=("attempts",)), retry_policy="no-retry",
        completion_criteria=("none",), verification_obligations=("none",), required_evidence=("artifact-verified",),
        non_goals=("everything",), candidate_custody_requirements=("none",), release_policy="automatic-on",
        authority_issuer="FX-B3 coverage probe", authority_references=("WO-220506",), target_repositories=(REPOSITORY,),
        baselines=("main",), required_closure_actions=("none",), stop_escalation_conditions=("any",),
    )
    values.update(overrides)
    return BiuContract(**values)


def row(item: BiuContract, *, digest: str | None = None) -> dict:
    return {
        "identity": item.identity, "repository": REPOSITORY, "membership": True, "complete": True, "status": "READY",
        "priority": "P5", "dependencies": list(item.dependencies), "contract": f"probe/{item.identity}.json",
        "contract_digest": digest or item.content_digest, "readiness": "local snapshot row", "wave": "2",
        "source_version": "local",
    }


def run_case(root: Path, name: str, item: BiuContract, *, digest: str | None = None, automatic: bool = True,
             explicit_release: bool = False, replay: bool = False) -> dict:
    """One case on a fresh store: import the row, drive the coordinator, count worker starts."""
    case_root = root / name
    case_root.mkdir(parents=True)
    rows = (row(item, digest=digest),)
    work = GitHubProjectsWorkManagement(PROFILE, REPOSITORY, {"READY": "READY"}, {}, lambda: rows, lambda _row: item)
    worker = CountingWorker()
    store = SQLiteOperationalStore(case_root / "state.sqlite")
    coordinator = FactoryCoordinator(store, work, worker, LocalArtifactStore(case_root / "a", case_root / "v"), PROFILE,
                                     automatic_release=automatic)
    first = coordinator.release_and_start(item.identity) if explicit_release else coordinator.start()
    launches_before_replay = len(worker.starts)
    second = coordinator.start() if replay else None
    observed = coordinator.state(item.identity) if _has_state(coordinator, item.identity) else None
    correlation = None if observed is None else (observed.record or {}).get("correlation")
    if correlation == "release":
        guard = "admit_release refusal (factory_coordinator.py:264-268)"
    elif not worker.starts:
        guard = "not selected: FactoryCoordinator._eligible (release/dependency eligibility)"
    elif replay and len(worker.starts) == launches_before_replay:
        guard = "replay not re-dispatched: FactoryCoordinator._eligible recorded-outcome guard (release.py:59-61 not reached; admit_release is called with an empty ledger)"
    else:
        guard = "none: admitted and launched"
    return {
        "case": name,
        "observed_worker_starts": len(worker.starts),
        "observed_worker_starts_before_replay": launches_before_replay if replay else None,
        "stop_reason": str((second or first).stop_reason),
        "dispatched": list(first.dispatched) + (list(second.dispatched) if second else []),
        "authority_blocked": list((second or first).authority_blocked),
        "observed_guard": guard,
        "recorded_correlation": correlation,
        "recorded_outcome": None if observed is None else observed.outcome,
    }


def _has_state(coordinator: FactoryCoordinator, identity: str) -> bool:
    try:
        coordinator.state(identity)
        return True
    except KeyError:
        return False


# expected: the launch count the pinned fixture / DAG predicate requires at the prelaunch boundary.
# guard: the refusing mechanism the pinned fixture names (WO-220506.md FX-B3 steps 2-8) or the DAG names.
CASES = (
    ("fxb3-2-positive-control", "WO-220506.md FX-B3 step 2", "admit_release admits", 1,
     dict(item=contract("FXB3-POS"))),
    ("fxb3-3-identity-replay", "WO-220506.md FX-B3 step 3", "release.py:59-61 replay/fingerprint refusal", 1,
     dict(item=contract("FXB3-REPLAY"), replay=True)),
    ("fxb3-4-policy-source-mismatch", "WO-220506.md FX-B3 step 4", "release.py:63-68 policy/source refusal", 0,
     dict(item=contract("FXB3-POLICY"), automatic=False, explicit_release=True)),
    ("fxb3-5-readiness-digest-mismatch", "WO-220506.md FX-B3 step 5", "release.py:69-70 stale readiness refusal", 0,
     dict(item=contract("FXB3-DIGEST"), digest="sha256:" + "f" * 64)),
    ("fxb3-6-unsatisfied-dependency", "WO-220506.md FX-B3 step 6", "release.py:71-73 unsatisfied dependency refusal", 0,
     dict(item=contract("FXB3-DEP", dependencies=("FXB3-ABSENT",)))),
    ("fxb3-7-missing-capability", "WO-220506.md FX-B3 step 7", "release.py:74-75 missing capability refusal", 0,
     dict(item=contract("FXB3-CAP", required_capabilities=("python", "fx-b3-absent-capability")))),
    ("fxb3-8-missing-budget-dimension", "WO-220506.md FX-B3 step 8", "release.py:76-78 absent budget dimension refusal", 0,
     dict(item=contract("FXB3-BUDGET", budget_policy=BudgetPolicy(hard_required_dimensions=("fx-b3-unallocated-dimension",))))),
    ("eligibility-not-released", "DAG B3 'plus eligibility' (explicit-human profile, no release)", "FactoryCoordinator._eligible", 0,
     dict(item=contract("FXB3-UNRELEASED", release_policy="explicit-human-off"), automatic=False)),
    ("dag-b3-p1-p2-no-release-record-no-named-baseline", "DAG B3 release_preconditions[0..1]", "durable release record authorizes IMPLEMENT; exact baseline named", 0,
     dict(item=contract("FXB3-NORECORD", baselines=("main",)))),
    ("dag-b3-p3-p4-baseline-unresolvable", "DAG B3 release_preconditions[2..3]", "baseline resolves to a real commit reachable from the release point", 0,
     dict(item=contract("FXB3-BASELINE", baselines=(UNRESOLVABLE_BASELINE,)))),
    ("dag-b3-p5-unsuperseded-denial-wording", "DAG B3 release_preconditions[4]", "no stale denial wording without a superseding record", 0,
     dict(item=contract("FXB3-DENIAL", intent=DENIAL, authority_references=(DENIAL,)))),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    results = []
    with tempfile.TemporaryDirectory(prefix="fx-b3-coverage-") as temporary:
        for name, source, guard, expected, spec in CASES:
            observed = run_case(Path(temporary), name, **spec)
            results.append({"source": source, "required_guard": guard, "expected_worker_starts": expected, **observed,
                            "matches_expected": observed["observed_worker_starts"] == expected})
    record = {
        "fixture": "FX-B3 pre-execution coverage probe", "work_unit": "WO-220506", "issue": 126, "label": LABEL,
        "call_site": "src/alienintent/execution_coordination/application/factory_coordinator.py:FactoryCoordinator._run",
        "cases": results,
        "all_match": all(case["matches_expected"] for case in results),
    }
    text = json.dumps(record, indent=2) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0 if record["all_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
