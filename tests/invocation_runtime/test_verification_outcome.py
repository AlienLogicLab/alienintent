"""VERIFICATION-OUTCOME-INTEGRITY: where the mutation harness and verdict admission run in a VERIFIER invocation.

Only an admitted REJECT (the gate's, the harness's or a session's whose every finding reproduced) is a `reject`; every
failure of the verification machinery is a VERIFIER_INFRASTRUCTURE kind, which keeps the candidate at VERIFY. The
gate, the harness and the session are fakes that record the order they ran in. Names are TEST DATA.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess

import pytest

from alienintent.execution_coordination.domain.contract import BudgetPolicy
from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
from alienintent.invocation_runtime.domain.mutation_spec import MutationSpecInvalid, parse_mutations
from alienintent.invocation_runtime.domain.verdict_admission import Reproduction
from alienintent.execution_coordination.ports.worker_provider import VERIFIER_INFRASTRUCTURE, WorkerInvocation
from alienintent.invocation_runtime.application.mutation_harness import (
    KILLED, SPEC_INVALID, SURVIVED, MutationResult)
from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
from alienintent.invocation_runtime.application.regression_gate import SuiteUnrunnable
from alienintent.invocation_runtime.domain.diagnostics import cause
from alienintent.invocation_runtime.domain.runtime import (
    BudgetRecord, CandidateUnavailable, CapabilityGrant, InvocationRole, ProcessResult, ProviderCapabilities)

BASE, HEAD = "a" * 40, "b" * 40
INVOCATION = "launch:WORK:3"
GATE_RECEIPT, HARNESS_RECEIPT = "feature-regressions:sha256:" + "1" * 64, "mutation-harness:sha256:" + "2" * 64
SPEC = parse_mutations('```json alienintent-mutations\n[{"name": "drop-check", "path": "src/rule.py", '
                       '"edits": [{"old": "if ok:", "new": "if True:"}], "tests": ["tests/t.py::test_a"]}]\n```\n')
TYPED = {"finding": "the refusal is missing", "evidence": {"type": "pytest", "node_ids": ["tests/t.py::test_a"]}}


class Fixture:
    """The gate, the harness, the session and the preparation hook, each recording into `ran`."""

    def __init__(self, root: Path, verdict: dict | None = None, mutated=None, reproduced=(), spec=SPEC) -> None:
        self.ran, self.results, self.verdict, self.spec = [], root / "results", verdict, spec
        self.mutated = mutated or (MutationResult("drop-check", KILLED, "test_a fails"),)
        self.reproduced, self.told = tuple(reproduced), []

    # the REGRESSION-GATE
    gate_findings: tuple[str, ...] = ()
    stands: tuple[str, ...] = ()

    def check(self, invocation_id, workspace, baseline_sha, candidate_sha):
        self.ran.append("gate")
        return self.gate_findings, GATE_RECEIPT

    def standing(self, invocation_id, candidate, base, identities, *, proven=frozenset()):
        self.ran.append("control")
        assert base == BASE and list(identities) == ["t::n", "t::a", "t::b"] and proven == {"t::a", "t::b"}
        return self.stands

    # the mutation harness
    def run(self, invocation_id, candidate, spec, base):
        self.ran.append("mutations")
        if isinstance(self.mutated, Exception):
            raise self.mutated
        return self.mutated, HARNESS_RECEIPT

    def reproduce(self, invocation_id, candidate, claims, base):
        self.ran.append("reproduce")
        assert candidate.locator.endswith(f"@{HEAD}")
        return self.reproduced

    def mutations(self, invocation):
        if isinstance(self.spec, Exception):
            raise self.spec
        return self.spec

    # the hand-over, the preparation hook and the session
    def candidate_clone(self, prefix, invocation_id, owner, candidate):
        path = self.results.parent / "worker" / prefix
        path.mkdir(parents=True)
        (self.results / invocation_id).mkdir(parents=True)
        return type("Clone", (), {"path": path})()

    def read_result(self, invocation_id, name, limit=1 << 20):
        return (self.results / invocation_id / name).read_bytes()

    def prepare(self, invocation, clone):
        return BASE

    def gated(self, invocation, baseline, revision, receipt):
        self.told.append(("gated", receipt))

    def mutations_run(self, invocation, results, receipt):
        self.told.append(("mutations", tuple(r.result for r in results), receipt))

    capabilities = ProviderCapabilities("fake", frozenset({"wall-clock", "cancellation"}))

    def run_session(self, invocation_id, role, workspace, wall_clock_seconds):
        self.ran.append("session")
        if self.verdict is not None:
            (self.results / invocation_id / "verdict.json").write_text(json.dumps({"revision": HEAD} | self.verdict))
        return ProcessResult("success", 0, True, BudgetRecord.unknown())


class Session:
    def __init__(self, fixture: Fixture) -> None:
        self.capabilities, self.run = fixture.capabilities, fixture.run_session


def evaluate(fixture: Fixture):
    grant = CapabilityGrant("g", "1", INVOCATION, InvocationRole.VERIFIER, "test", "T", frozenset({"process-control"}),
                            10 ** 12)
    preparation = type("Preparation", (), {"prepare": fixture.prepare, "gated": fixture.gated,
                                           "mutated": fixture.mutations_run})()
    worker = RealWorkerProvider(Session(fixture), None, fixture.results.parent, "origin", "b",
                                fixture.results.parent / "verifier", grant, "T", None, now=lambda: 0,
                                sleep=lambda _: None, handover=fixture, regression_gate=fixture,
                                regression_base=lambda invocation: BASE, preparation=preparation,
                                mutation_harness=fixture, mutations=fixture.mutations)
    digest = "sha256:" + sha256(HEAD.encode()).hexdigest()
    candidate = CandidateRef(CandidateKind.SOURCE_REVISION, digest, digest, f"git:origin#candidate/c@{HEAD}", "test")
    invocation = WorkerInvocation("WORK", INVOCATION, role="VERIFIER", candidate=candidate)
    return worker.start(invocation, None, frozenset(), BudgetPolicy(hard_wall_clock_seconds=60))


def test_the_harness_runs_after_the_gate_and_before_the_session_and_an_accept_carries_both_receipts(tmp_path):
    fixture = Fixture(tmp_path, {"verdict": "accept", "findings": []})
    outcome = evaluate(fixture)
    assert fixture.ran == ["gate", "mutations", "session"]
    assert (outcome.kind, outcome.receipts) == ("accept", (GATE_RECEIPT, HARNESS_RECEIPT))
    assert fixture.told == [("gated", GATE_RECEIPT), ("mutations", (KILLED,), HARNESS_RECEIPT)]
    # A packet without a spec runs no harness.
    fixture = Fixture(tmp_path / "no-spec", {"verdict": "accept", "findings": []}, spec=None)
    assert evaluate(fixture).receipts == (GATE_RECEIPT,) and fixture.ran == ["gate", "session"]


def test_a_surviving_mutation_is_a_control_plane_reject_with_the_harness_receipt_and_no_session(tmp_path):
    fixture = Fixture(tmp_path, mutated=(MutationResult("drop-check", SURVIVED, "pass with the mutation: x"),))
    outcome = evaluate(fixture)
    assert outcome.kind == "reject" and fixture.ran == ["gate", "mutations"]
    assert outcome.receipts == (GATE_RECEIPT, HARNESS_RECEIPT)
    assert outcome.findings == ("mutation-survived:drop-check: pass with the mutation: x",)


@pytest.mark.parametrize("spec, mutated, kind", [
    (MutationSpecInvalid("more than one mutations block"), None, "verification-evidence-invalid"),
    (SPEC, (MutationResult("drop-check", SPEC_INVALID, "'if ok:' occurs 2 times"),), "verification-evidence-invalid"),
    (SPEC, SuiteUnrunnable("the run outran its wall clock"), "mutation-harness-unavailable"),
])
def test_a_harness_that_cannot_judge_keeps_the_candidate_for_a_fresh_verify(tmp_path, spec, mutated, kind):
    fixture = Fixture(tmp_path, spec=spec, mutated=mutated)
    outcome = evaluate(fixture)
    assert (outcome.kind, outcome.candidate) == (kind, None) and "session" not in fixture.ran
    assert kind in VERIFIER_INFRASTRUCTURE and cause(kind, None) == kind


@pytest.mark.parametrize("findings, reproduced", [
    (["a plain finding"], [None]),
    ([TYPED], [Reproduction(False, "no named test fails")]),
    ([TYPED, "a plain finding"], [Reproduction(True, "failed: tests/t.py::test_a"), None]),
])
def test_a_session_reject_that_is_not_reproduced_is_not_admitted(tmp_path, findings, reproduced):
    fixture = Fixture(tmp_path, {"verdict": "reject", "findings": findings}, reproduced=reproduced)
    outcome = evaluate(fixture)
    assert (outcome.kind, outcome.candidate) == ("verification-evidence-invalid", None)
    assert outcome.findings and all(text.startswith("not-admitted:") for text in outcome.findings)


def test_a_session_reject_whose_every_finding_reproduces_is_admitted(tmp_path):
    fixture = Fixture(tmp_path, {"verdict": "reject", "findings": [TYPED]},
                      reproduced=[Reproduction(True, "failed: tests/t.py::test_a")])
    outcome = evaluate(fixture)
    assert outcome.kind == "reject" and fixture.ran == ["gate", "mutations", "session", "reproduce"]
    [finding] = outcome.findings
    assert finding.startswith("the refusal is missing") and "failed: tests/t.py::test_a" in finding
    assert outcome.receipts[:2] == (GATE_RECEIPT, HARNESS_RECEIPT)
    assert outcome.receipts[2].startswith("reject-reproduced:sha256:")


def test_a_reproduction_that_cannot_run_is_no_result_never_a_rejection(tmp_path):
    fixture = Fixture(tmp_path, {"verdict": "reject", "findings": [TYPED]})
    fixture.reproduce = lambda *args: (_ for _ in ()).throw(SuiteUnrunnable("the run outran its wall clock"))
    assert evaluate(fixture).kind == "mutation-harness-unavailable"


@pytest.mark.parametrize("failure", [subprocess.TimeoutExpired(["sudo"], 300), CandidateUnavailable("worker workspace "
                                     "operation failed"), OSError("the results folder exists")])
@pytest.mark.parametrize("stage", ["mutations", "reproduce"])
def test_a_harness_timeout_or_workspace_failure_is_unavailable_with_its_cause(tmp_path, failure, stage):
    """Never an escaping exception and never a judgment on the candidate: the typed outcome names what failed."""
    fixture = Fixture(tmp_path, {"verdict": "reject", "findings": [TYPED]})

    def fails(*args):
        raise failure
    setattr(fixture, "run" if stage == "mutations" else "reproduce", fails)
    outcome = evaluate(fixture)
    assert (outcome.kind, outcome.candidate) == ("mutation-harness-unavailable", None)
    assert outcome.findings and type(failure).__name__ in outcome.findings[0]


GATE_FINDINGS = ("new-test-fails:t::n:failed", "regression:t::a:passed->error", "regression:t::b:passed->skipped")


@pytest.mark.parametrize("standing, findings", [
    (("t::a",), ("regression:t::a:passed->error",)),
    (("t::n", "t::b"), ("new-test-fails:t::n:failed", "regression:t::b:passed->skipped")),
])
def test_a_gate_regression_is_a_reject_only_where_the_control_run_stands(tmp_path, standing, findings):
    """Gate regressions and failing new tests are rerun now at the candidate and the starting revision; the ones the
    control does not stand are dropped (a new test that errors from the environment keeps the candidate)."""
    fixture = Fixture(tmp_path)
    fixture.gate_findings, fixture.stands = GATE_FINDINGS, standing
    outcome = evaluate(fixture)
    assert (outcome.kind, outcome.findings, outcome.receipts) == ("reject", findings, (GATE_RECEIPT,))
    assert fixture.ran == ["gate", "control"]


def test_gate_regressions_the_environment_decided_keep_the_candidate(tmp_path):
    fixture = Fixture(tmp_path)
    fixture.gate_findings = GATE_FINDINGS
    outcome = evaluate(fixture)
    assert (outcome.kind, outcome.candidate) == ("mutation-harness-unavailable", None)
    assert "environment" in outcome.findings[0] and "session" not in fixture.ran
