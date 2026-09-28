#!/usr/bin/env python3
"""FX-B3P — canonical release-admission precondition gate (WO-220611, Issue #141) — LOCAL, real stack.

Derived from, and attributed to, PRODUCER Morty's FX-B3 pre-execution coverage probe
(`tools/live/fx_b3_admission_coverage.py`, WO-220506/Issue #126, evidence branch
`b-disp/760ff8cd-68a8-40b8-99cd-2d0a8b09cbf6` @ `a11e1dd716fef312698c32ba390ff10c722bf649`). That
probe found the six SWF-21 release preconditions and a reachable budget refusal absent at the
canonical call site; this fixture asserts the now-fixed behaviour at that same call site:
`FactoryCoordinator._run` -> `ReleasePreconditionGate.check` -> `admit_release`, composed over the
real `SQLiteOperationalStore`, `GitHubProjectsWorkManagement`, the store-held release records and a
real local git repository for baseline resolution and reachability. Only the Project snapshot rows
and the worker (a counting double answering `authority-block`, so no process starts) are local.

It touches no network, no GitHub repository/Project, no provider and no credential. It does not
re-pin FX-B3/FX-B4 (WO-220506's own scope) and is not operational evidence for them.

    python3 tools/live/fx_b3p_release_preconditions.py [--out result.json]

Exit 0 when every case's observed worker starts and refusing check equal their pinned expectation.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from alienintent.execution_coordination.adapters.github_work_management import GitHubProjectsWorkManagement
from alienintent.execution_coordination.adapters.release_admission import GitRevisionResolver, StoredReleaseAuthorizations
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
from alienintent.execution_coordination.application.release_admission import BiuLimitAllocation, ReleasePreconditionGate
from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy
from alienintent.execution_coordination.domain.release import ReleaseAuthorization
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation, WorkerOutcome

REPOSITORY = "AlienLogicLab/alienintent"
PROFILE = "fx-b3p-local"
RELEASE_POINT = "main"
LABEL = "LOCAL_REAL_STACK — FX-B3P for WO-220611; not FX-B3/FX-B4 operational evidence"
DENIAL = "Implementation is **not** authorized by this Issue. Release remains an explicit authority step."
NULL_REVISION = "0" * 40


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
        raise AssertionError("the fixture never cancels")


def contract(identity: str, **overrides) -> BiuContract:
    values = dict(
        identity=identity, version="1", intent="FX-B3P fixture scaffolding; never executed",
        satisfied_requirement_ids=("SF-REQ-002",), fixed_decisions=("FX-B3P",), authorized_scope=("none",),
        excluded_scope=("everything",), dependencies=(), required_capabilities=("python",),
        budget_policy=BudgetPolicy(hard_required_dimensions=("attempts",)), retry_policy="no-retry",
        completion_criteria=("none",), verification_obligations=("none",), required_evidence=("artifact-verified",),
        non_goals=("everything",), candidate_custody_requirements=("none",), release_policy="automatic-on",
        authority_issuer="FX-B3P fixture", authority_references=("WO-220611",), target_repositories=(REPOSITORY,),
        baselines=("main",), required_closure_actions=("none",), stop_escalation_conditions=("any",),
    )
    values.update(overrides)
    return BiuContract(**values)


def row(item: BiuContract) -> dict:
    return {
        "identity": item.identity, "repository": REPOSITORY, "membership": True, "complete": True, "status": "READY",
        "priority": "P5", "dependencies": list(item.dependencies), "contract": f"fixture/{item.identity}.json",
        "contract_digest": item.content_digest, "readiness": "local snapshot row", "wave": "2", "source_version": "local",
    }


def _git(checkout: Path, *args: str) -> str:
    env = {**os.environ, "GIT_AUTHOR_NAME": "fx-b3p", "GIT_AUTHOR_EMAIL": "fx-b3p@example.invalid",
           "GIT_COMMITTER_NAME": "fx-b3p", "GIT_COMMITTER_EMAIL": "fx-b3p@example.invalid"}
    return subprocess.run(["git", *args], cwd=checkout, env=env, check=True, capture_output=True, text=True).stdout.strip()


def target_repository(root: Path) -> dict[str, str]:
    """``baseline`` is an ancestor of ``main``; ``diverged`` is a real commit ``main`` cannot reach."""
    checkout = root / "target"
    checkout.mkdir()
    _git(checkout, "init", "--quiet", "--initial-branch=main")
    _git(checkout, "commit", "--quiet", "--allow-empty", "-m", "baseline")
    baseline = _git(checkout, "rev-parse", "HEAD")
    _git(checkout, "commit", "--quiet", "--allow-empty", "-m", "release point")
    _git(checkout, "checkout", "--quiet", "-b", "side", baseline)
    _git(checkout, "commit", "--quiet", "--allow-empty", "-m", "diverged")
    diverged = _git(checkout, "rev-parse", "HEAD")
    _git(checkout, "checkout", "--quiet", "main")
    return {"checkout": str(checkout), "baseline": baseline, "diverged": diverged}


def run_case(root: Path, repository: dict[str, str], name: str, item: BiuContract, *, record: dict | None,
             allocation: dict | None = None, gated: bool = True) -> dict:
    """One case on a fresh store: record the release (if any), import the row, drive the coordinator."""
    case_root = root / name
    case_root.mkdir(parents=True)
    rows = (row(item),)
    work = GitHubProjectsWorkManagement(PROFILE, REPOSITORY, {"READY": "READY"}, {}, lambda: rows, lambda _row: item)
    worker = CountingWorker()
    store = SQLiteOperationalStore(case_root / "state.sqlite")
    records = StoredReleaseAuthorizations(store, PROFILE)
    authorization = None
    if record is not None:
        values = {"identity": item.identity, "record_ref": f"fixture:{item.identity}:release-record", "authorizes_implement": True,
                  "baseline": "baseline", "text": "IMPLEMENT is authorized."} | record
        values["baseline"] = repository.get(values["baseline"], values["baseline"])
        authorization = ReleaseAuthorization(**values)
        records.record(authorization)
    gate = ReleasePreconditionGate(records, GitRevisionResolver({REPOSITORY: Path(repository["checkout"])}), RELEASE_POINT) if gated else None
    coordinator = FactoryCoordinator(store, work, worker, LocalArtifactStore(case_root / "a", case_root / "v"), PROFILE,
                                     release_gate=gate, allocation=None if allocation is None else BiuLimitAllocation(allocation))
    summary = coordinator.start()
    try:
        record_state = coordinator.state(item.identity).record or {}
    except KeyError:
        record_state = {}
    correlation = record_state.get("correlation")
    hold = record_state.get("hold_reason")
    if correlation == "release":
        refused_by = hold.removeprefix("release-precondition:") if isinstance(hold, str) else "admit_release"
    else:
        refused_by = None
    return {
        "case": name,
        "release_record": None if authorization is None else {**authorization.__dict__},
        "allocation": allocation,
        "gate_configured": gated,
        "observed_worker_starts": len(worker.starts),
        "observed_refused_by": refused_by,
        "stop_reason": str(summary.stop_reason),
        "authority_blocked": list(summary.authority_blocked),
        "recorded_correlation": correlation,
        "recorded_outcome": record_state.get("outcome"),
    }


# (case, acceptance criterion, expected worker starts, expected refusing check or None, spec)
CASES = (
    ("positive-control", "valid release admits (one launch)", 1, None,
     dict(item=contract("FXB3P-POS"), record={})),
    ("p1-no-release-record", "no durable release authorization record", 0, "implementation-authorized",
     dict(item=contract("FXB3P-NORECORD"), record=None)),
    ("p1-record-does-not-authorize", "record does not explicitly authorize IMPLEMENT", 0, "implementation-authorized",
     dict(item=contract("FXB3P-NOAUTH"), record={"authorizes_implement": False})),
    ("p2-no-exact-baseline", "record names no exact baseline (symbolic 'main')", 0, "baseline-named",
     dict(item=contract("FXB3P-NOBASE"), record={"baseline": "main"})),
    ("p3-null-baseline", "baseline does not resolve (the null revision)", 0, "baseline-resolves",
     dict(item=contract("FXB3P-NULL"), record={"baseline": NULL_REVISION})),
    ("p3-absent-baseline", "baseline does not resolve (well-formed but absent)", 0, "baseline-resolves",
     dict(item=contract("FXB3P-ABSENT"), record={"baseline": "b" * 40})),
    ("p4-unreachable-baseline", "baseline not reachable from the intended release point", 0, "baseline-reachable",
     dict(item=contract("FXB3P-DIVERGED"), record={"baseline": "diverged"})),
    ("p5-unsuperseded-denial", "explicit unsuperseded denial wording, other fields valid", 0, "authority-wording-consistent",
     dict(item=contract("FXB3P-DENIAL", intent=DENIAL, authority_references=(DENIAL,)), record={})),
    ("p5-superseded-denial", "denial wording with an explicit superseding record admits", 1, None,
     dict(item=contract("FXB3P-SUPERSEDED", intent=DENIAL), record={"superseding_record": "fixture:FXB3P-SUPERSEDED:superseding"})),
    ("budget-exhausted", "attributable allocation exhausted for a required dimension", 0, "admit_release",
     dict(item=contract("FXB3P-EXHAUSTED"), record={}, allocation={"FXB3P-EXHAUSTED": {"attempts": 0}})),
    ("budget-unallocated", "no attributable allocation for this BIU", 0, "admit_release",
     dict(item=contract("FXB3P-UNALLOCATED"), record={}, allocation={"FXB3P-OTHER": {"attempts": 3}})),
    ("budget-allocated", "attributable allocation available admits", 1, None,
     dict(item=contract("FXB3P-ALLOCATED"), record={}, allocation={"FXB3P-ALLOCATED": {"attempts": 1}})),
    ("budget-dimension-unallocated", "allocation lacks one required dimension (FX-B3 step 8 shape)", 0, "admit_release",
     dict(item=contract("FXB3P-DIMENSION", budget_policy=BudgetPolicy(hard_required_dimensions=("attempts", "fx-b3-unallocated-dimension"))),
          record={}, allocation={"FXB3P-DIMENSION": {"attempts": 1}})),
    # Contrast: the same invalid inputs in a profile that configures neither input keep the prior
    # behaviour the FX-B3 coverage probe observed (one launch), so the refusals above are the gate's.
    ("contrast-ungated-no-record", "contrast: no release gate configured, no record", 1, None,
     dict(item=contract("FXB3P-UNGATED"), record=None, gated=False)),
    ("contrast-unmetered-dimension", "contrast: no allocation configured, FX-B3 step 8 shape", 1, None,
     dict(item=contract("FXB3P-UNMETERED", budget_policy=BudgetPolicy(hard_required_dimensions=("fx-b3-unallocated-dimension",))),
          record={})),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    results = []
    with tempfile.TemporaryDirectory(prefix="fx-b3p-") as temporary:
        root = Path(temporary)
        repository = target_repository(root)
        for name, criterion, expected, refused_by, spec in CASES:
            observed = run_case(root, repository, name, **spec)
            for key in ("baseline",):
                if observed["release_record"] and observed["release_record"][key] in {repository["baseline"], repository["diverged"]}:
                    observed["release_record"][key] = "<fixture:" + ("baseline" if observed["release_record"][key] == repository["baseline"] else "diverged") + ">"
            results.append({"criterion": criterion, "expected_worker_starts": expected, "expected_refused_by": refused_by, **observed,
                            "matches_expected": observed["observed_worker_starts"] == expected and observed["observed_refused_by"] == refused_by})
    record = {
        "fixture": "FX-B3P", "work_unit": "WO-220611", "issue": 141, "label": LABEL,
        "call_site": "src/alienintent/execution_coordination/application/factory_coordinator.py:FactoryCoordinator._run",
        "release_point": RELEASE_POINT,
        "attribution": "derived from tools/live/fx_b3_admission_coverage.py @ a11e1dd716fef312698c32ba390ff10c722bf649 (WO-220506, Issue #126)",
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
