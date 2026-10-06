"""REGRESSION-GATE acceptance checks 1-5: the whole-suite comparison and where it runs.

The recorded junit files under `fixtures/regression_gate/` are the main session's whole-suite runs at `cd5314b` and
`057fbc1` (committed unchanged); `findings.txt` is the exact expected output. Test names, identities and file contents
below are TEST DATA.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path

import pytest

from alienintent.execution_coordination.domain.contract import BudgetPolicy
from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
from alienintent.invocation_runtime.application.regression_gate import (
    SUITE, SUITE_JUNIT, RegressionGate, SuiteUnrunnable, compare, receipt, results, suite)
from alienintent.invocation_runtime.domain.runtime import (
    BudgetRecord, CapabilityGrant, InvocationRole, ProcessResult, ProviderCapabilities)
from alienintent.invocation_runtime.ports.workspace import Workspace

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "regression_gate"
BASE, HEAD = "a" * 40, "b" * 40
INVOCATION = "launch:WORK:1"


def junit(*cases: tuple[str, str]) -> bytes:
    """A junit document with one test case per (identity, outcome)."""
    child = {"passed": "", "failed": "<failure message='x'/>", "error": "<error message='x'/>",
             "skipped": "<skipped message='x'/>"}
    body = "".join(f'<testcase classname="{i.split("::")[0]}" name="{i.split("::")[1]}">{child[o]}</testcase>'
                   for i, o in cases)
    return f'<?xml version="1.0"?><testsuites><testsuite name="pytest">{body}</testsuite></testsuites>'.encode()


# --- check 1: the comparison ----------------------------------------------------------------------------------------

def test_compare_passed_to_failed():
    assert compare({"t::a": "passed"}, {"t::a": "failed"}) == ("regression:t::a:passed->failed",)


def test_compare_passed_to_error():
    assert compare({"t::a": "passed"}, {"t::a": "error"}) == ("regression:t::a:passed->error",)


def test_compare_passed_to_missing():
    assert compare({"t::a": "passed", "t::b": "passed"}, {"t::b": "passed"}) == ("regression:t::a:passed->missing",)


def test_compare_passed_to_skipped():
    assert compare({"t::a": "passed"}, {"t::a": "skipped"}) == ("regression:t::a:passed->skipped",)


def test_compare_new_test_fails():
    assert compare({}, {"t::new": "failed"}) == ("new-test-fails:t::new:failed",)


def test_compare_new_test_errors():
    assert compare({}, {"t::new": "error"}) == ("new-test-fails:t::new:error",)


def test_compare_failed_stays_failed():
    assert compare({"t::a": "failed"}, {"t::a": "failed"}) == ()


def test_compare_error_to_failed():
    assert compare({"t::a": "error"}, {"t::a": "failed"}) == ()


def test_compare_skipped_to_failed():
    assert compare({"t::a": "skipped"}, {"t::a": "failed"}) == ()


def test_compare_passed_stays_passed():
    assert compare({"t::a": "passed"}, {"t::a": "passed"}) == ()


def test_compare_new_test_passes():
    assert compare({"t::a": "passed"}, {"t::a": "passed", "t::new": "passed"}) == ()


# --- check 2: an unrunnable suite -----------------------------------------------------------------------------------

@pytest.mark.parametrize("exit_code", [2, 3, 4, 5])
def test_an_exit_code_other_than_0_or_1_is_unrunnable(exit_code):
    with pytest.raises(SuiteUnrunnable):
        results(junit(("t::a", "passed")), exit_code)


def test_junit_that_cannot_be_parsed_is_unrunnable():
    with pytest.raises(SuiteUnrunnable):
        results(b"<testsuites><testcase", 1)


def test_a_collection_error_with_exit_code_1_is_a_result():
    collection = b'<testsuites><testsuite><testcase classname="" name="tests.broken">' \
                 b'<error message="collection failure"/></testcase></testsuite></testsuites>'
    assert results(collection, 1) == {"::tests.broken": "error"}
    assert results(junit(("t::a", "passed"), ("t::b", "failed"), ("t::c", "skipped")), 0) == {
        "t::a": "passed", "t::b": "failed", "t::c": "skipped"}


def test_the_suite_command_is_the_whole_suite():
    assert suite(Path("/r/j.xml")) == ["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                       "--continue-on-collection-errors", "--junitxml", "/r/j.xml", "tests", "tools"]
    assert len(SUITE) == 11


# --- check 3: the 057fbc1 case, recorded ----------------------------------------------------------------------------

def test_compare_names_the_057fbc1_regressions():
    baseline = results((FIXTURES / "cd5314b.xml").read_bytes(), 1)
    candidate = results((FIXTURES / "057fbc1.xml").read_bytes(), 1)
    expected = tuple((FIXTURES / "findings.txt").read_text().splitlines())
    assert len(expected) == 39
    assert compare(baseline, candidate) == expected


# --- checks 4 and 5: the decision is taken in the control plane, before the session ---------------------------------

class Handover:
    """A worker-user hand-over over a plain `<results>` folder: the candidate clone and the checked read."""

    def __init__(self, root: Path) -> None:
        self.results, self.root = root / "results", root

    def candidate_clone(self, prefix, invocation_id, owner, candidate) -> Workspace:
        path = self.root / "worker" / f"{prefix}-clone"
        path.mkdir(parents=True)
        (self.results / invocation_id).mkdir(parents=True)
        return type("Clone", (), {"path": path})()

    def read_result(self, invocation_id: str, name: str, limit: int = 1 << 20) -> bytes:
        data = (self.results / invocation_id / name).read_bytes()
        if len(data) > limit:
            raise OSError("too large")
        return data


class Session:
    """The VERIFIER session: records that it started and runs `act` in its clone."""

    capabilities = ProviderCapabilities("fake", frozenset({"wall-clock", "cancellation"}))

    def __init__(self, act=None) -> None:
        self.started, self.act = [], act

    def run(self, invocation_id, role, workspace, wall_clock_seconds) -> ProcessResult:
        self.started.append(invocation_id)
        if self.act is not None:
            self.act(workspace)
        return ProcessResult("success", 0, True, BudgetRecord.unknown())


def candidate_ref() -> CandidateRef:
    digest = "sha256:" + sha256(HEAD.encode()).hexdigest()
    return CandidateRef(CandidateKind.SOURCE_REVISION, digest, digest, f"git:origin#candidate/c@{HEAD}", "test")


def provider(tmp_path: Path, session: Session, run, base: str | None = BASE) -> tuple[RealWorkerProvider, Handover]:
    handover = Handover(tmp_path)
    baselines = tmp_path / "regression-baselines"
    gate = RegressionGate(run, lambda path: handover.read_result(path.parent.name, path.name, limit=64 << 20),
                          lambda sha, identity: pytest.fail("the baseline is cached"), baselines, handover.results)
    baselines.mkdir(mode=0o711)
    (baselines / f"{BASE}.json").write_text(json.dumps({"baseline": BASE, "results": {
        "t::a": "passed", "t::b": "passed"}}))
    grant = CapabilityGrant("g", "1", INVOCATION, InvocationRole.VERIFIER, "test", "T", frozenset({"process-control"}),
                            10 ** 12)
    worker = RealWorkerProvider(session, None, tmp_path, "origin", "b", tmp_path / "verifier", grant, "T", None,
                                now=lambda: 0, sleep=lambda _: None, handover=handover, regression_gate=gate,
                                regression_base=lambda invocation: base)
    return worker, handover


def evaluate(worker: RealWorkerProvider):
    invocation = WorkerInvocation("WORK", INVOCATION, role="VERIFIER", candidate=candidate_ref())
    return worker.start(invocation, None, frozenset(), BudgetPolicy(hard_wall_clock_seconds=60))


def test_a_rewritten_junit_file_changes_nothing(tmp_path):
    """Check 4: the suite wrote a regression; the session would rewrite the junit file as all passing and accept."""
    folder = tmp_path / "results" / INVOCATION

    def run(clone: Path, path: Path) -> int:
        path.write_bytes(junit(("t::a", "passed"), ("t::b", "failed")))
        return 1

    def rewrite(clone: Path) -> None:
        (folder / SUITE_JUNIT).write_bytes(junit(("t::a", "passed"), ("t::b", "passed")))
        (folder / "verdict.json").write_text(json.dumps({"revision": HEAD, "verdict": "accept", "findings": []}))

    session = Session(rewrite)
    worker, _ = provider(tmp_path, session, run)
    outcome = evaluate(worker)
    assert (outcome.kind, outcome.findings) == ("reject", ("regression:t::b:passed->failed",))
    assert outcome.receipts[0].startswith("feature-regressions:sha256:") and session.started == []

    # A suite that leaves a verdict in the invocation's results folder: nothing is read as the session's verdict.
    def leaves_a_verdict(clone: Path, path: Path) -> int:
        path.write_bytes(junit(("t::a", "passed"), ("t::b", "passed")))
        (path.parent / "verdict.json").write_text(json.dumps({"revision": HEAD, "verdict": "accept", "findings": []}))
        return 0

    other, session = tmp_path / "other", Session()
    other.mkdir()
    worker, _ = provider(other, session, leaves_a_verdict)
    assert evaluate(worker).kind == "verdict-preexisting" and session.started == []


def test_the_candidate_workspace_does_not_define_the_gate(tmp_path):
    """Check 5: a candidate runner that exits 0, a manifest selecting no pack and a valid worker-written receipt."""
    def run(clone: Path, path: Path) -> int:
        runner = clone / "tools/verification/run_feature_regressions.py"
        runner.parent.mkdir(parents=True)
        runner.write_text("import sys\nsys.exit(0)\n")
        (clone / "tools/verification/feature_regressions.json").write_text(json.dumps({"packs": []}))
        body = {"kind": "FeatureRegressionReceipt", "passed": True, "candidate": HEAD, "packs": []}
        digest = "sha256:" + sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        (path.parent / "feature-regressions.json").write_text(json.dumps(body | {"receipt_digest": digest}))
        path.write_bytes(junit(("t::a", "failed"), ("t::b", "passed")))
        return 1

    session = Session()
    worker, _ = provider(tmp_path, session, run)
    outcome = evaluate(worker)
    assert (outcome.kind, outcome.findings) == ("reject", ("regression:t::a:passed->failed",))
    assert session.started == []


def test_no_findings_runs_the_session_and_the_receipt_is_the_gates(tmp_path):
    """With no findings the session runs as today; the receipt is the gate's, never a worker-written one."""
    cases = {"t::a": "passed", "t::b": "passed"}

    def run(clone: Path, path: Path) -> int:
        path.write_bytes(junit(*cases.items()))
        return 0

    def verdict(clone: Path) -> None:
        (tmp_path / "results" / INVOCATION / "verdict.json").write_text(
            json.dumps({"revision": HEAD, "verdict": "accept", "findings": []}))

    session = Session(verdict)
    worker, _ = provider(tmp_path, session, run)
    outcome = evaluate(worker)
    assert outcome.kind == "accept" and session.started == [INVOCATION]
    assert outcome.receipts == (receipt(BASE, HEAD, cases, cases, ()),)


@pytest.mark.parametrize("base", [None, "main", "a" * 39])
def test_a_missing_or_short_baseline_is_feature_regressions_missing(tmp_path, base):
    session = Session()
    worker, _ = provider(tmp_path, session, lambda clone, path: pytest.fail("no suite runs"), base)
    assert evaluate(worker).kind == "feature-regressions-missing" and session.started == []


def test_an_unrunnable_candidate_suite_is_feature_regressions_missing(tmp_path):
    session = Session()
    worker, _ = provider(tmp_path, session, lambda clone, path: (path.write_bytes(b"<x/>"), 5)[1])
    assert evaluate(worker).kind == "feature-regressions-missing" and session.started == []


def test_an_uncached_baseline_runs_in_its_own_checkout_and_is_cached_before_cleanup(tmp_path):
    """The baseline runs once, at a fresh checkout named for the SHA and the invocation; the cache is written before
    the checkout is cleaned up and serves the next invocation."""
    events, results_root, baselines = [], tmp_path / "results", tmp_path / "regression-baselines"

    @contextmanager
    def checkout(sha: str, identity: str):
        events.append(("checkout", sha, identity))
        path = tmp_path / identity
        path.mkdir()
        (results_root / identity).mkdir(parents=True)
        yield path
        events.append(("cleanup", (baselines / f"{sha}.json").exists()))

    def run(folder: Path, path: Path) -> int:
        events.append(("run", folder.name))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(junit(("t::a", "passed")))
        return 0

    gate = RegressionGate(run, Path.read_bytes, checkout, baselines, results_root)
    workspace = tmp_path / "candidate"
    workspace.mkdir()
    assert gate.check(INVOCATION, workspace, BASE, HEAD)[0] == ()
    identity = f"baseline-{BASE}-{INVOCATION}"
    assert events == [("checkout", BASE, identity), ("run", identity), ("cleanup", True), ("run", "candidate")]
    assert json.loads((baselines / f"{BASE}.json").read_text()) == {"baseline": BASE, "results": {"t::a": "passed"}}
    assert baselines.stat().st_mode & 0o777 == 0o711
    assert gate.check("launch:WORK:2", workspace, BASE, HEAD)[0] == () and len(events) == 5  # cached: one more run
