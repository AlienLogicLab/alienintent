"""FX-U9 probes: readiness lint and the retained assessment consumer (SF-REQ-015-AC-01..05).

Composed through UpstreamProfile over a real temporary SQLite store, local evidence, the U5 design gate and the
FactoryCoordinator lifecycle. Every producer here is a scripted double (FIXTURE_PRODUCER_NOT_NATIVE) bound to a
disposable fixture package: it drives routes and refusals and never discharges native-producer proof (U10). MCP
envelopes wrap retained direct objects (SYNTHETIC_MCP_ENVELOPE_FROM_RETAINED_DIRECT); split result sets are
fixture-supplied (FIXTURE_MATERIALIZED_RESULT_SET_NOT_U8_PROOF); the PY-10 records are historical Surrogate
Readiness Assessments (SURROGATE_READINESS_HISTORY_NOT_AGENT_READY), never an Agent Ready sequence.
"""
import ast
from copy import deepcopy
from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess

import pytest

from alienintent.composition.compilation import CoordinatorDependencyLifecycle
from alienintent.composition.design_admission import EDGE_AUTHORITY_GAP, RetainedDirectionAuthority
from alienintent.composition.premise_evidence import RetainedDoctorPremiseEvidence
from alienintent.composition.upstream_profile import UpstreamProfile
from alienintent.context_assembly.application.readiness_service import ReadinessAdmission
from alienintent.context_assembly.domain.compilation import contract_from_payload
from alienintent.context_assembly.domain.readiness import FIXTURE_RESULT_SET, LintHold, SplitResultSet, SplitRouted
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.domain.records import ref_from_document
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.execution_coordination.adapters.assessment_consumer import RETAINED_ASSESSMENT
from alienintent.execution_coordination.adapters.local_work_management import LocalWorkManagement
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
from alienintent.execution_coordination.domain import release as release_domain
from alienintent.execution_coordination.domain.escalation import DecisionSubmission
from alienintent.execution_coordination.domain.lifecycle import ExecutionState, LifecycleStage
from alienintent.execution_coordination.domain.readiness import (
    ATTEMPT_CONFLICT, ATTEMPT_FAILURE, CAPABILITY_PROVENANCE_HOLD, CLARIFY_PENDING_DECISION, CONFLICTING,
    CONTRACT_VERSION, DIRECT, MALFORMED, MCP, MCP_ERROR, NO_TERMINAL_RESULT, PREREQUISITE_PENDING, PROVENANCE,
    PROVIDER_FAILURE, SPLIT_RESULT_SET_NOT_MATERIALIZED, STALE_ASSESSMENT, TIMEOUT, UNKNOWN, UNKNOWN_DISPOSITION,
    AttemptFailure, AttemptMetadata, HistoricalAssessment, Hold, InvocationCustody, ProducerResponse,
    ReadinessEligibility, SemanticAssessment, digest)
from alienintent.execution_coordination.ports.operational_store import VersionConflict
from tests.context_assembly.test_design_admission import (
    DESIGN, DESIGN_SHA256, KEY, PREMISE_MAPPING, PREMISE_SHA256, REVIEWERS, _Recorded, contract, review)

ROOT = Path(__file__).resolve().parents[2]
PROJECT, PROFILE = "AlienLogicLab/alienintent", "fx-u9"
INVOCATION = "AlienLogicLab/alienintent#105:PRODUCER:55583f93-b75f-4ac6-b73c-fbbc1475c8da"
SCOPE = frozenset({"private"})
ACTOR = "Founder"
PLAN = ("FX-U9",)
BASELINE = "04cdd8cddaeb1bc19a34b2fae3d988678aaca28d"
X, P1, O, C1, C2 = "WO-990900", "WO-990901", "WO-990910", "WO-990911", "WO-990912"
FIXTURE_PRODUCER = "FIXTURE_PRODUCER_NOT_NATIVE"
QUESTIONS = ("Which retry budget governs the second phase?", "May the adapter write outside the profile root?")

# Input 4: retained native direct assessments (read by path and digest; never modified).
ASSESSMENTS = "docs/evidence/wave2-readiness-assessments/"
RECORDS = {"ready": ("WO-220207.2026-09-25T001654.663618Z.assessment.json",
                     "2862acb88dec9d240bd2c436cc2aae63ec704c0ef7663beeb5b96240948bd1ff"),
           "hold": ("WO-220102.2026-09-23T041739.192319Z.assessment.json",
                    "e8c6d3da41ee96843e93f6f1149a65874cefc7a9f88eb7be4d1f7f0af98a3a71"),
           "ready_after_hold": ("WO-220102.2026-09-23T053013.882036Z.assessment.json",
                                "4df4717c74b957c6f4b21d527c8ec3c93471ecc64e0db56e70d6352641fcb167"),
           "failure": ("FDH-01.2026-09-24T021848.446095Z.assessment.json",
                       "b4f70369c8066a097b012e45a48c4a3b7f54942d8fc4c45c64bc5d236d6356d6")}
PINNED_CONTRACT = ("5a79622", "docs/work-units/wave2/WO-220207.md",
                   "0e05a12001ee303b5d7eebb4d57afe536def5f2f323c7946a69d1b30390e9525")

# Input 8: PY-10 bootstrap-assessor history, extracted by blob and pinned by raw-blob digest (U-13).
PY10_PATH = "docs/work-units/python/PY-10.assessment.json"
PY10 = (("c32830b931a06562fa12f273d83e55f4b7c1816c", "3c53cd3dc751c76eb167bb142d30f61825d3259a",
         "093a9d2c212593812e67edb5a7b04a36ac075970cfe970c60ade16cb3506c232", "BLOCKED", "e25da1f"),
        ("1f16b816cb0d30681eacbb2ea178eb2cf92ddd02", "fe1e3efe3523f4376b2de66a650dca31fecdbfad",
         "1fc95f25b6c2d928fcb325525b46c1850bb56463c2428f0ea56afc99f181ebb4", "SPLIT_RECOMMENDED",
         "85b606037e144e977c1bc1f7b0aa795d97e19d83"),
        ("693fef995f03ab3eca43cb74ad5692cdcd69ffcf", "30ea7c451505c5f6bfeba5b6496fff2b4fff01e4",
         "9561bf71baaea6d0c6caf26eee87a23ab03beb6c83be68bbc5847447cde6e694", "READY", "93dd8b1"))
PM = ("docs/evidence/wave1-readiness-assessment-provenance.json",
      "a8f977e0bb26bd7f0b599042ccce853ff5d76dd9e00adff033990550408a8f21")
M = ("docs/evidence/wave1-agent-ready-outcome-matrix.json",
     "f9730f9eccf4022e314f74bdf3d3ac257c0e07d00c76d6cf87419e472fe4e145")
PY09B_MERGE = "93dd8b1"


def pinned(path: str, expected: str) -> bytes:
    data = (ROOT / path).read_bytes()
    assert sha256(data).hexdigest() == expected, f"input digest mismatch: {path}"
    return data


@lru_cache(maxsize=None)
def record(role: str) -> dict:
    name, expected = RECORDS[role]
    return json.loads(pinned(ASSESSMENTS + name, expected))


def inputs_dir() -> Path | None:
    directory = os.environ.get("FX_U9_FIXTURE_INPUTS")
    return Path(directory) if directory else None


@lru_cache(maxsize=None)
def blob(identity: str) -> bytes:
    """A pinned PY-10 blob from the runner's extracted inputs or Git; never a working-tree path."""
    directory = inputs_dir()
    data = (directory / identity).read_bytes() if directory else subprocess.check_output(
        ["git", "cat-file", "blob", identity], cwd=ROOT)
    return data


def compute_git_facts(root: Path) -> dict:
    """Facts about retained history that only Git can answer; the runner records them for disposable copies."""
    def git(*argv: str) -> str:
        return subprocess.check_output(["git", *argv], cwd=root, text=True).strip()
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", PY09B_MERGE, PY10[2][0]], cwd=root).returncode
    revision, path, _ = PINNED_CONTRACT
    return {"py10_follow_history": git("log", "--follow", "--format=%H", "--", PY10_PATH).split(),
            "py09b_merge_is_ancestor_of_ready": ancestor == 0,
            "py09b_merge_subject": git("log", "-1", "--format=%s", PY09B_MERGE),
            "py10_blob_at_revision": {r: git("rev-parse", f"{r}:{PY10_PATH}") for r, *_ in PY10},
            "pinned_contract_text": subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=root).decode()}


@lru_cache(maxsize=None)
def git_facts() -> dict:
    directory = inputs_dir()
    return json.loads((directory / "git-facts.json").read_text()) if directory else compute_git_facts(ROOT)


def pinned_contract_text() -> str:
    text = git_facts()["pinned_contract_text"]
    assert sha256(text.encode()).hexdigest() == PINNED_CONTRACT[2], "WO-220207.md@5a79622 digest mismatch"
    return text


def looks_native_agent_ready(artifact: object) -> bool:
    """Negative shape evidence from the existing programme checker; never positive producer authentication."""
    spec = importlib.util.spec_from_file_location("check_assessment_producer",
                                                  ROOT / "tools" / "evidence" / "check_assessment_producer.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.looks_native_agent_ready(artifact)


def encode(value: object) -> bytes:
    return json.dumps(value, sort_keys=True).encode()


def body(disposition: str, **changes) -> dict:
    """A fixture-producer body: the retained READY object with the named fields replaced (FIXTURE_PRODUCER)."""
    document = deepcopy(record("ready")["assessment"])
    document.update(disposition=disposition, **changes)
    return document


def envelope(obj: object, mode: str = "both", is_error: bool = False) -> dict:
    """A known MCP envelope around the byte-identical retained object (SYNTHETIC_MCP_ENVELOPE_FROM_RETAINED_DIRECT)."""
    document = {"content": [{"type": "text", "text": json.dumps(obj, sort_keys=True)}] if mode != "structured" else [],
                "isError": is_error}
    if mode != "text":
        document["structuredContent"] = obj
    return document


def unit_contract(identity: str, dependencies=(), **fields) -> dict:
    document = {
        "identity": identity, "version": "1", "intent": f"Deliver the {identity} readiness extent",
        "satisfied_requirement_ids": [KEY], "fixed_decisions": ["D-API: check(design_key, vector)"],
        "authorized_scope": ["context_assembly"], "excluded_scope": ["adapters"], "dependencies": list(dependencies),
        "required_capabilities": ["python"],
        "budget_policy": {"hard_required_dimensions": ["attempts"], "maximum_attempts": 3,
                          "hard_wall_clock_seconds": 7200, "retry_limit": 1, "concurrency_limit": 1},
        "retry_policy": "one replacement per phase", "completion_criteria": ["tests pass"],
        "verification_obligations": ["unit tests"], "required_evidence": ["test output"],
        "non_goals": ["live operation"], "candidate_custody_requirements": ["publish the exact candidate SHA"],
        "release_policy": "explicit-human-off", "authority_issuer": "Founder", "authority_references": ["SWF-19"],
        "target_repositories": [PROJECT], "baselines": ["main@04cdd8c"], "required_closure_actions": ["land or park"],
        "stop_escalation_conditions": ["authority gap"]}
    document.update(fields)
    return document


def candidate(vector: dict, identity: str = X, dependencies=(P1,), text: str | None = None, baseline: str = BASELINE,
              decisions=(), edges=None, drop=(), **fields) -> dict:
    document = unit_contract(identity, dependencies, **fields)
    for name in drop:
        document.pop(name)
    return {"contract": document, "text": text if text is not None else f"# {identity}\n\npinned candidate text\n",
            "baseline": baseline, "design_key": KEY, "design_vector": vector,
            "dependency_edges": list(dependencies if edges is None else edges), "governing_decisions": list(decisions)}


def fixture_package(root: Path, name: str = "agent-ready", version: str = "0.1.0rc1", metadata: bool = True) -> Path:
    """A disposable local distribution with the product name, labelled; its script is never executed (U-7)."""
    environment = root / "fixture-agent-ready"
    executable = environment / "bin" / "agent-ready"
    executable.parent.mkdir(parents=True)
    executable.write_text("# FIXTURE_PACKAGE_NOT_AGENT_READY: never executed by FX-U9\n")
    executable.chmod(0o600)
    if metadata:
        info = environment / "lib" / "python3.12" / "site-packages" / f"{name.replace('-', '_')}-{version}.dist-info"
        info.mkdir(parents=True)
        (info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n")
        (info / "entry_points.txt").write_text("[console_scripts]\nagent-ready = fixture_only:main\n")
    return executable


class FixtureProducer:
    """FIXTURE_PRODUCER_NOT_NATIVE: a scripted ReadinessAssessment double that counts launches."""
    label = FIXTURE_PRODUCER

    def __init__(self, script):
        self.script, self.calls, self.opened_before_call = script, [], []
        self.binding = self.consumer = None

    def assess(self, unit):
        self.calls.append(unit)
        latest = self.consumer.latest(unit.identity) if self.consumer is not None else None
        self.opened_before_call.append(bool(latest) and latest["attempt_id"] == unit.attempt_id
                                       and latest["outcome"] is None)
        return self.script(self, unit)


def custody(binding, unit, provider_evidence=None, **changes) -> InvocationCustody:
    value = InvocationCustody(unit.attempt_id, digest(unit.text), binding.product, binding.product_version,
                              binding.executable, (binding.executable, "assess", f"<pinned:{unit.identity}>",
                                                   "--provider", "claude", "--json"), "claude",
                              "2026-09-25T00:00:00+00:00", "2026-09-25T00:00:01+00:00", provider_evidence)
    return replace(value, **changes)


def respond(producer, unit, result, shape=DIRECT, exit_status=0, timed_out=False, bound=True) -> ProducerResponse:
    raw = result if isinstance(result, (bytes, type(None))) else encode(result)
    inner = result.get("structuredContent", result) if isinstance(result, dict) else None
    evidence = inner.get("provider_evidence") if isinstance(inner, dict) else None
    return ProducerResponse(raw, exit_status, timed_out, shape,
                            custody(producer.binding, unit, evidence) if bound else None)


def scripted(results: dict, default=None):
    """Per-identity response sequences; the last entry repeats."""
    def script(producer, unit):
        sequence = results.get(unit.identity, [default if default is not None else body("READY")])
        seen = sum(1 for c in producer.calls if c.identity == unit.identity)
        entry = sequence[min(seen, len(sequence)) - 1]
        return entry(producer, unit) if callable(entry) else respond(producer, unit, entry)
    return script


class RecordingSplit:
    """Consumer side of U8's SplitTransaction port: records each handoff; returns case (a) None or case (b) a set."""

    def __init__(self, result: SplitResultSet | None = None):
        self.result, self.handoffs = result, []

    def handoff(self, identity, attempt_id, assessment_ref, raw_assessment, recommended_boundaries):
        self.handoffs.append({"identity": identity, "attempt_id": attempt_id, "assessment_ref": assessment_ref,
                              "raw_assessment": raw_assessment, "boundaries": recommended_boundaries})
        return self.result


class Harness:
    """One disposable profile: store, evidence, coordinator lifecycle and the composed UpstreamProfile."""

    def __init__(self, root: Path, producer=None, executable="package", split=None, package=None):
        root.mkdir(mode=0o700)
        self.store = SQLiteOperationalStore(root / "operational.sqlite")
        self.repository = LocalEvidenceRepository(root / "evidence", PROJECT, PROFILE)
        self.work = LocalWorkManagement(root / "work", PROFILE, PROJECT, (), clock=lambda: 0.0)
        coordinator = FactoryCoordinator(self.store, self.work, None, LocalArtifactStore(root / "p", root / "v"),
                                         PROFILE)
        self.executable = fixture_package(root, **(package or {})) if executable == "package" else executable
        self.definition = Ref(PROJECT, PROFILE, "FX-U9-contract", digest("FX-U9"), "repository:WO-220209.md")
        self.producer = producer
        self.profile = UpstreamProfile(
            self.repository, self.store, PROJECT, PROFILE, self.definition, INVOCATION, ACTOR, SCOPE,
            premise_evidence=RetainedDoctorPremiseEvidence(ROOT, Path(PREMISE_MAPPING), PREMISE_SHA256, PROJECT,
                                                           PROFILE),
            premise_target="AlienLogicLab/alienintent-sandbox", design_checks=_Recorded(),
            design_authority=RetainedDirectionAuthority(ROOT, DESIGN, DESIGN_SHA256, EDGE_AUTHORITY_GAP, PROJECT,
                                                        PROFILE),
            design_reviewers=REVIEWERS, dependency_lifecycle=CoordinatorDependencyLifecycle(coordinator),
            readiness_producer=producer, readiness_executable=self.executable, split_handoff=split)
        self.service = self.profile.readiness
        self.consumer = self.profile.readiness_consumer
        if producer is not None:
            producer.binding, producer.consumer = self.profile.readiness_binding, self.consumer

    def design(self, state: str = "verified") -> dict:
        if state == "absent":
            return {"design": digest("absent"), "requirements": {KEY: digest("absent")}}
        report = self.profile.design.inspect(contract(), 0)
        if state == "unreviewed":
            return report.vector
        self.profile.design.record_review(KEY, review(report), 1)
        return report.vector

    def lifecycle(self, identity: str, stage: str) -> None:
        version, _ = self.store.read_state(PROFILE, "factory:" + identity)
        self.store.commit(PROFILE, "factory:" + identity, version,
                          FactoryCoordinator._encode(ExecutionState(stage=LifecycleStage(stage))))

    def guarded(self) -> dict:
        """Lifecycle and release state U9 must never write."""
        return {prefix: [(a, v, json.dumps(s, sort_keys=True)) for a, v, s in self.store.list_states(PROFILE, prefix)]
                for prefix in ("factory:", "release:")}

    def outcome(self, identity: str, index: int = -1) -> dict:
        entry = self.consumer.history(identity)[index]
        return json.loads(self.repository.get(ref_from_document(entry["outcome_ref"]), SCOPE).value)

    def raw(self, entry: dict) -> str:
        return self.repository.get(ref_from_document(entry["raw_ref"]), SCOPE).value

    def evidence(self, event: str) -> list[dict]:
        """Every retained observation of one event, read from the immutable object store."""
        payloads = [json.loads(p.read_text())["payload"] for p in (self.repository.root / "objects").iterdir()]
        return [p for p in payloads if p.get("evidence_id") == event]


@pytest.fixture
def make(tmp_path):
    count = iter(range(1000))

    def factory(producer=None, **options):
        h = Harness(tmp_path / f"h{next(count)}", producer, **options)
        h.lifecycle(P1, "DONE")
        return h, h.design("verified")
    return factory


def ready_producer(**results):
    return FixtureProducer(scripted(results))


# --- SF-REQ-015-AC-01: lint before assessment ------------------------------------------------------------------


def test_complete_candidate_proceeds_to_assessment(make):
    producer = ready_producer()
    h, vector = make(producer)
    report, _ = h.service.lint(candidate(vector), PLAN)
    assert report.holds == () and report.contract_digest.startswith("sha256:")
    result = h.service.assess(candidate(vector), PLAN)
    assert isinstance(result, ReadinessEligibility)
    assert len(producer.calls) == 1 and producer.opened_before_call == [True]  # Persisted before invocation.
    opened = json.loads(h.repository.get(ref_from_document(h.consumer.latest(X)["opened_ref"]), SCOPE).value)
    assert opened["attempt_id"] == producer.calls[0].attempt_id and opened["record_kind"] == "AssessmentAttempt"


MISSING_DUTIES = {
    "decision": (dict(drop=("fixed_decisions",)), "decision", "fixed_decisions"),
    "boundary": (dict(excluded_scope=[]), "boundary", "excluded_scope"),
    "verification": (dict(drop=("verification_obligations",)), "verification", "verification_obligations"),
    "proof_plan": ({}, "verification", "proof_plan"),
    "architecture": ({}, "architecture", "design_applicability"),
    "dependency": (dict(dependencies=(P1, "WO-990999")), "dependency", "dependencies"),
    "dependency_edges": (dict(edges=["WO-990998"]), "dependency", "dependency_edges"),
}


@pytest.mark.parametrize("duty", list(MISSING_DUTIES))
def test_missing_duty_lint_hold(make, duty):
    producer = ready_producer()
    h, vector = make(producer)
    change, expected_duty, field = MISSING_DUTIES[duty]
    if duty == "architecture":
        vector = {**vector, "design": digest("moved")}  # The verified design no longer matches: STALE.
    before = h.guarded()
    result = h.service.assess(candidate(vector, **change), () if duty == "proof_plan" else PLAN)
    assert isinstance(result, LintHold), result
    assert (result.duty, result.field) == (expected_duty, field)
    if duty == "architecture":
        assert result.detail == "STALE"  # The U5 reason code verbatim.
    assert producer.calls == [] and h.consumer.history(X) == ()  # Zero assess calls, no attempt.
    assert h.guarded() == before
    assert [e["value"] for e in h.evidence("readiness.lint_held")]


def test_incomplete_contract_lint_hold(make):
    producer = ready_producer()
    h, vector = make(producer)
    result = h.service.assess(candidate(vector, drop=("intent",)), PLAN)
    assert isinstance(result, LintHold) and (result.duty, result.field) == ("contract", "intent")
    assert producer.calls == []


def test_lint_hold_is_not_agent_ready_hold(make):
    h, vector = make(ready_producer())
    h.service.assess(candidate(vector, drop=("fixed_decisions",)), PLAN)
    [held] = h.evidence("readiness.lint_held")
    document = json.loads(held["value"])
    assert document["record_kind"] == "LintHold" and document["reason_code"] == "LINT_HOLD"
    assert "disposition" not in document and all("disposition" not in d for d in document["holds"])


# --- SF-REQ-015-AC-02: the four routes up to their handoff boundaries ------------------------------------------


def test_ready_yields_eligibility_only(make, monkeypatch):
    calls = []
    original = release_domain.admit_release
    monkeypatch.setattr(release_domain, "admit_release", lambda *a: calls.append(a) or original(*a))
    h, vector = make(ready_producer())
    before = h.guarded()
    result = h.service.assess(candidate(vector), PLAN)
    assert isinstance(result, ReadinessEligibility)
    assert calls == [] and h.guarded() == before  # No release and no lifecycle write by U9.
    contract_value = contract_from_payload(candidate(vector)["contract"])
    request = release_domain.ReleaseRequest(X, contract_value, result.contract_digest, frozenset({P1}),
                                            frozenset({"python"}), {"attempts": 3, "wall-clock": 1,
                                                                    "concurrency": 1}, "fixture release authority")
    assert release_domain.admit_release({}, request).identity == X  # Only the separate gate admits release.
    with pytest.raises(ValueError, match="stale readiness reference"):
        release_domain.admit_release({}, replace(request, readiness_digest=digest("other")))


def test_clarify_routes_to_decision_inbox_then_reassess(make):
    producer = ready_producer(**{X: [body("CLARIFY", owner_clarifications=list(QUESTIONS)), body("READY")]})
    h, vector = make(producer)
    held = h.service.assess(candidate(vector), PLAN)
    assert isinstance(held, Hold) and held.reason_code == CLARIFY_PENDING_DECISION
    entries = h.profile.inbox.list_open()
    assert [e.decision for e in entries] == list(QUESTIONS)
    assert all(e.options == ("resolve", "defer") and "no default answer" in e.recommendation for e in entries)
    clarify = h.consumer.latest(X)
    clarify_bytes = h.raw(clarify)
    again = h.service.assess(candidate(vector), PLAN)
    assert isinstance(again, Hold) and again.reason_code == CLARIFY_PENDING_DECISION and len(producer.calls) == 1
    for index, entry in enumerate(entries[:1]):
        h.profile.inbox.submit(DecisionSubmission(ACTOR, "fixture owner answer", entry.work_item, 0, 0,
                                                  f"clarify-{index}", "resolve"))
    partial = h.service.assess(candidate(vector), PLAN)
    assert isinstance(partial, Hold) and len(producer.calls) == 1  # Every question needs its own decision.
    h.profile.inbox.submit(DecisionSubmission(ACTOR, "fixture owner answer", entries[1].work_item, 0, 0,
                                              "clarify-1", "resolve"))
    fresh = h.service.assess(candidate(vector), PLAN)
    assert isinstance(fresh, ReadinessEligibility) and len(producer.calls) == 2
    latest = h.consumer.latest(X)
    assert latest["attempt_id"] != clarify["attempt_id"]
    assert latest["predecessor"] == {"identity": X, "attempt_id": clarify["attempt_id"]}
    assert h.raw(h.consumer.history(X)[0]) == clarify_bytes and h.outcome(X, 0)["disposition"] == "CLARIFY"


def split_body() -> dict:
    return body("SPLIT", semantic_split_recommendation=[{"unit": "C1", "boundary": "lint"},
                                                        {"unit": "C2", "boundary": "consumer"}])


def test_split_without_result_set_refuses(make):
    split = RecordingSplit(None)
    producer = ready_producer(**{X: [split_body()]})
    h, vector = make(producer, split=split)
    before = h.guarded()
    result = h.service.assess(candidate(vector), PLAN)
    assert isinstance(result, Hold) and result.reason_code == SPLIT_RESULT_SET_NOT_MATERIALIZED
    assert len(split.handoffs) == 1, "no handoff to the SplitTransaction port was recorded"
    handoff = split.handoffs[0]
    assert handoff["attempt_id"] == h.consumer.latest(X)["attempt_id"]
    assert handoff["raw_assessment"] == h.raw(h.consumer.latest(X)) == encode(split_body()).decode()
    assert len(producer.calls) == 1 and h.guarded() == before
    again = h.service.assess(candidate(vector), PLAN)
    assert isinstance(again, Hold) and again.reason_code == SPLIT_RESULT_SET_NOT_MATERIALIZED
    assert len(producer.calls) == 1 and len(split.handoffs) == 1


def test_split_result_set_linted_and_reassessed_each(make):
    producer = ready_producer(**{X: [split_body()]})
    split = RecordingSplit()
    h, vector = make(producer, split=split)
    assert isinstance(h.service.assess(candidate(vector, identity=O, dependencies=()), PLAN), ReadinessEligibility)
    prior = h.consumer.latest(O)
    prior_bytes = h.raw(prior)
    split.result = SplitResultSet(
        (candidate(vector, identity=C1, dependencies=()), candidate(vector, identity=C2, dependencies=())),
        candidate(vector, identity=O, dependencies=(), intent="Integrate C1 and C2 into the retained parent"),
        (O,), FIXTURE_RESULT_SET)
    result = h.service.assess(candidate(vector), PLAN)
    assert isinstance(result, SplitRouted)
    assert [i for i, _ in result.outcomes] == [C1, C2, O]
    assert all(isinstance(r, ReadinessEligibility) for _, r in result.outcomes)
    assert [c.identity for c in producer.calls] == [O, X, C1, C2, O]
    split_attempt = h.consumer.latest(X)["attempt_id"]
    for identity in (C1, C2, O):
        assert h.consumer.latest(identity)["predecessor"] == {"identity": X, "attempt_id": split_attempt}
    _, state = h.consumer.read(O)
    assert prior["attempt_id"] in state["invalidated"]  # Stale applicability invalidated, not kept current.
    assert h.raw(h.consumer.history(O)[0]) == prior_bytes and len(h.consumer.history(O)) == 2


def test_hold_requires_prerequisite_then_reassess(make):
    hold_object = record("hold")["assessment"]
    producer = ready_producer(**{X: [hold_object, body("READY")]})
    h, vector = make(producer)
    h.lifecycle(P1, "IMPLEMENT")
    first = h.service.assess(candidate(vector), PLAN)
    assert isinstance(first, Hold) and first.reason_code == PREREQUISITE_PENDING
    held = h.consumer.latest(X)
    again = h.service.assess(candidate(vector), PLAN)
    assert isinstance(again, Hold) and again.reason_code == PREREQUISITE_PENDING and len(producer.calls) == 1
    h.lifecycle(P1, "DONE")
    fresh = h.service.assess(candidate(vector), PLAN)
    assert isinstance(fresh, ReadinessEligibility) and len(producer.calls) == 2
    assert h.consumer.latest(X)["predecessor"] == {"identity": X, "attempt_id": held["attempt_id"]}


NON_READY = {"clarify": lambda: body("CLARIFY", owner_clarifications=[QUESTIONS[0]]),
             "split": split_body, "hold": lambda: record("hold")["assessment"],
             "attempt_failure": lambda: {"content": [], "isError": True}}


@pytest.mark.parametrize("case", [*NON_READY, "lint_hold"])
def test_no_non_ready_authorizes_implementation(make, case):
    shape = MCP if case == "attempt_failure" else DIRECT
    producer = FixtureProducer(lambda p, u: respond(p, u, NON_READY[case](), shape))
    h, vector = make(producer, split=RecordingSplit(None))
    unit = candidate(vector, drop=("fixed_decisions",)) if case == "lint_hold" else candidate(vector)
    before = h.guarded()
    result = h.service.assess(unit, PLAN)
    assert not isinstance(result, ReadinessEligibility)
    current = h.service.current(unit, PLAN)
    assert not isinstance(current, ReadinessEligibility), current
    assert h.guarded() == before


# --- SF-REQ-015-AC-03: stale inputs and immutable predecessors -------------------------------------------------


FINGERPRINT_CHANGES = {
    "contract": lambda v: candidate(v, intent="A materially different intent"),
    "baseline": lambda v: candidate(v, baseline="0" * 40),
    "decision": lambda v: candidate(v, decisions=("DEC-2026-09-25-01",)),
    "prerequisite": None,
    "design": None,
}


@pytest.mark.parametrize("component", list(FINGERPRINT_CHANGES))
def test_fingerprint_change_invalidates_ready(make, component):
    h, vector = make(ready_producer())
    assert isinstance(h.service.assess(candidate(vector), PLAN), ReadinessEligibility)
    ready = h.consumer.latest(X)
    ready_record = h.outcome(X)
    if component == "prerequisite":
        h.lifecycle(P1, "IMPLEMENT")
        result = h.service.current(candidate(vector), PLAN)
    elif component == "design":
        report, _ = h.service.lint(candidate(vector), PLAN)
        moved = replace(report, review_digest=digest("another independent review"))
        result = h.consumer.consume(X, ReadinessAdmission.fingerprint(candidate(vector), moved))
    else:
        result = h.service.current(FINGERPRINT_CHANGES[component](vector), PLAN)
    assert isinstance(result, Hold) and result.reason_code == STALE_ASSESSMENT
    _, state = h.consumer.read(X)
    assert state["applicability"]["status"] == "INAPPLICABLE" and state["applicability"]["attempt_id"] == \
        ready["attempt_id"]
    assert h.outcome(X) == ready_record and h.consumer.latest(X) == ready  # The old READY is unchanged.
    assert h.evidence("readiness.stale")


def test_fresh_assessment_links_predecessor(make):
    producer = ready_producer()
    h, vector = make(producer)
    h.service.assess(candidate(vector), PLAN)
    first = h.consumer.latest(X)
    version_before, _ = h.consumer.read(X)
    changed = candidate(vector, intent="A materially different intent")
    assert isinstance(h.service.current(changed, PLAN), Hold)
    assert isinstance(h.service.assess(changed, PLAN), ReadinessEligibility)
    history = h.consumer.history(X)
    assert [a["attempt_id"] for a in history] == [first["attempt_id"], h.consumer.latest(X)["attempt_id"]]
    assert history[1]["attempt_id"] != first["attempt_id"]
    assert history[1]["predecessor"] == {"identity": X, "attempt_id": first["attempt_id"]}
    assert history[0] == first and h.consumer.read(X)[0] > version_before
    opened = json.loads(h.repository.get(ref_from_document(history[1]["opened_ref"]), SCOPE).value)
    assert opened["predecessor_ref"] == first["opened_ref"]


def test_pointer_commit_is_compare_and_swap(make):
    h, vector = make(ready_producer())
    commit = h.store.commit

    def racing(profile, aggregate, expected, state):
        if aggregate.startswith("readiness:"):
            raise VersionConflict("moved")
        return commit(profile, aggregate, expected, state)
    h.store.commit = racing
    result = h.service.assess(candidate(vector), PLAN)
    assert isinstance(result, Hold) and result.reason_code == "PERSISTENCE_CONFLICT"


def test_resolved_blocker_cannot_rewrite_verdict(make):
    hold_object, ready_object = record("hold")["assessment"], record("ready_after_hold")["assessment"]
    producer = ready_producer(**{X: [hold_object, ready_object]})
    h, vector = make(producer)
    h.lifecycle(P1, "IMPLEMENT")
    h.service.assess(candidate(vector), PLAN)
    hold_entry, hold_record = h.consumer.latest(X), h.outcome(X)
    hold_bytes = h.raw(hold_entry)
    h.lifecycle(P1, "DONE")
    assert isinstance(h.service.assess(candidate(vector), PLAN), ReadinessEligibility)
    history = h.consumer.history(X)
    assert history[0] == hold_entry and h.outcome(X, 0) == hold_record and hold_record["disposition"] == "HOLD"
    assert h.raw(history[0]) == hold_bytes == encode(hold_object).decode()
    assert history[1]["attempt_id"] != hold_entry["attempt_id"] and h.outcome(X, 1)["disposition"] == "READY"


def test_duplicate_and_conflicting_response(make):
    h, vector = make(ready_producer())
    report, lint_ref = h.service.lint(candidate(vector), PLAN)
    fingerprint = ReadinessAdmission.fingerprint(candidate(vector), report)
    attempt = h.consumer.open(X, fingerprint, digest("text"), report.contract_digest, None, lint_ref,
                              h.profile.readiness_binding)
    unit = type("Unit", (), {"attempt_id": attempt, "text": "text", "identity": X})()
    metadata = AttemptMetadata(X, attempt, fingerprint, digest("text"), 0, False,
                               custody(h.profile.readiness_binding, unit), h.profile.readiness_binding)
    first = h.consumer.observe(encode(body("READY")), metadata, DIRECT)
    version, _ = h.consumer.read(X)
    assert h.consumer.observe(encode(body("READY")), metadata, DIRECT) == first
    assert h.consumer.read(X)[0] == version  # Identical duplicate: no-op.
    conflict = h.consumer.observe(encode(body("HOLD")), metadata, DIRECT)
    assert isinstance(conflict, Hold) and conflict.reason_code == ATTEMPT_CONFLICT
    assert h.outcome(X)["disposition"] == "READY" and h.consumer.read(X)[0] == version


# --- SF-REQ-015-AC-04 / 015-envelope-applicability: direct and known-MCP parity --------------------------------


def observe_once(h, raw, shape, exit_status=0, timed_out=False, identity=X, bound=True):
    report, lint_ref = h.service.lint(candidate(h.vector, identity=identity), PLAN)
    fingerprint = ReadinessAdmission.fingerprint(candidate(h.vector, identity=identity), report)
    attempt = h.consumer.open(identity, fingerprint, digest("text"), report.contract_digest, None, lint_ref,
                              h.profile.readiness_binding)
    unit = type("Unit", (), {"attempt_id": attempt, "text": "text", "identity": identity})()
    metadata = AttemptMetadata(identity, attempt, fingerprint, digest("text"), exit_status, timed_out,
                               custody(h.profile.readiness_binding, unit) if bound else None,
                               h.profile.readiness_binding)
    return h.consumer.observe(raw, metadata, shape), h.consumer.latest(identity)


@pytest.mark.parametrize("mode", ["structured", "text", "both"])
@pytest.mark.parametrize("role", ["ready", "hold"])
def test_direct_mcp_parity(make, role, mode):
    obj = record(role)["assessment"]
    direct_bytes, mcp_bytes = encode(obj), encode(envelope(obj, mode))
    h, h.vector = make(ready_producer())
    direct, direct_entry = observe_once(h, direct_bytes, DIRECT, identity=C1)
    wrapped, wrapped_entry = observe_once(h, mcp_bytes, MCP, identity=C2)
    assert isinstance(direct, SemanticAssessment) and isinstance(wrapped, SemanticAssessment), (direct, wrapped)
    assert direct == wrapped and direct.disposition == obj["disposition"]
    assert (direct.shape, wrapped.shape) == (DIRECT, MCP)
    assert h.raw(direct_entry).encode() == direct_bytes and h.raw(wrapped_entry).encode() == mcp_bytes
    assert direct.raw_digest == digest(direct_bytes) and wrapped.raw_digest == digest(mcp_bytes)
    routes = []
    for shape, raw in ((DIRECT, direct_bytes), (MCP, mcp_bytes)):
        producer = FixtureProducer(lambda p, u, shape=shape, raw=raw: respond(p, u, raw, shape))
        g, vector = make(producer)
        result = g.service.assess(candidate(vector), PLAN)
        routes.append((type(result).__name__, getattr(result, "reason_code", None)))
    assert routes[0] == routes[1]


MCP_FAILURES = {
    "is_error": (lambda: envelope(body("READY"), is_error=True), MCP_ERROR),
    "conflict_struct_text": (lambda: {**envelope(body("READY"), "structured"),
                                      "content": [{"type": "text", "text": json.dumps(body("HOLD"))}]}, CONFLICTING),
    "conflict_two_texts": (lambda: {"content": [{"type": "text", "text": json.dumps(body("READY"))},
                                                {"type": "text", "text": json.dumps(body("HOLD"))}],
                                    "isError": False}, CONFLICTING),
    "unknown_disposition": (lambda: envelope(body("BLOCKED")), UNKNOWN_DISPOSITION),
    "malformed_text": (lambda: {"content": [{"type": "text", "text": "{\"disposition\": \"READY\""}],
                                "isError": False}, MALFORMED),
    "no_terminal": (lambda: {"content": [], "isError": False}, NO_TERMINAL_RESULT),
}


@pytest.mark.parametrize("exit_status", [0, 1])
@pytest.mark.parametrize("variant", list(MCP_FAILURES))
def test_mcp_failure_cases(make, variant, exit_status):
    build, expected = MCP_FAILURES[variant]
    raw = encode(build())
    producer = FixtureProducer(lambda p, u: respond(p, u, raw, MCP, exit_status))
    h, vector = make(producer)
    result = h.service.assess(candidate(vector), PLAN)
    assert isinstance(result, Hold) and result.reason_code == ATTEMPT_FAILURE
    outcome = h.outcome(X)
    assert outcome["record_kind"] == "AttemptFailure" and outcome["failure_class"] == expected, outcome
    assert "disposition" not in outcome and h.raw(h.consumer.latest(X)).encode() == raw  # Raw envelope retained.
    assert not isinstance(h.service.current(candidate(vector), PLAN), ReadinessEligibility)


TIMEOUTS = {"timeout_no_bytes": (None, None, True, TIMEOUT),
            "timeout_with_ready_bytes": (lambda: encode(body("READY")), None, True, TIMEOUT),
            "provider_failure": (lambda: b"", 1, False, PROVIDER_FAILURE)}


@pytest.mark.parametrize("case", list(TIMEOUTS))
def test_timeout_and_provider_failure_hold(make, case):
    raw, exit_status, timed_out, expected = TIMEOUTS[case]
    assert record("failure")["provenance"]["exit_code"] == 1  # FDH-01: the retained provider failure class.
    failing = lambda p, u: respond(p, u, raw() if raw else None, DIRECT, exit_status, timed_out)
    producer = ready_producer(**{X: [body("READY"), failing]})
    h, vector = make(producer)
    h.service.assess(candidate(vector), PLAN)
    predecessor, predecessor_record = h.consumer.latest(X), h.outcome(X)
    changed = candidate(vector, intent="A materially different intent")
    result = h.service.assess(changed, PLAN)
    assert isinstance(result, Hold) and result.reason_code == ATTEMPT_FAILURE and result.detail == expected
    assert h.outcome(X)["failure_class"] == expected and "disposition" not in h.outcome(X)
    assert h.consumer.history(X)[0] == predecessor and h.outcome(X, 0) == predecessor_record
    assert not isinstance(h.service.current(changed, PLAN), ReadinessEligibility)


@pytest.mark.parametrize("case", ["empty_stdout", "no_disposition"])
def test_zero_exit_without_semantic_result_fails(make, case):
    raw = b"" if case == "empty_stdout" else encode({"summary": "a result object with no disposition"})
    producer = FixtureProducer(lambda p, u: respond(p, u, raw, DIRECT, 0))
    h, vector = make(producer)
    result = h.service.assess(candidate(vector), PLAN)
    assert isinstance(result, Hold) and result.reason_code == ATTEMPT_FAILURE
    assert h.outcome(X)["failure_class"] == NO_TERMINAL_RESULT


def _appended(document: dict, suffix: str) -> str:
    """The JSON text of document with one more member appended verbatim (duplicate keys, bare constants)."""
    return json.dumps(document, sort_keys=True)[:-1] + suffix + "}"


AMBIGUOUS = {  # Review R1 repairs: payloads whose bytes carry an ambiguous or malformed terminal result.
    "direct_duplicate_key": (DIRECT, lambda: _appended(body("HOLD"), ', "disposition": "READY"').encode(), MALFORMED),
    "text_duplicate_key": (MCP, lambda: encode({"content": [{"type": "text", "text": _appended(
        body("HOLD"), ', "disposition": "READY"')}], "isError": False}), MALFORMED),
    "is_error_string": (MCP, lambda: encode({**envelope(body("READY"), "structured"), "isError": "true"}), MALFORMED),
    "is_error_int": (MCP, lambda: encode({**envelope(body("READY"), "structured"), "isError": 1}), MALFORMED),
    "nan_constant": (DIRECT, lambda: _appended(body("READY"), ', "x": NaN').encode(), MALFORMED),
    "body_conflict": (MCP, lambda: encode({**envelope(body("CLARIFY", owner_clarifications=["A?"]), "structured"),
                                            "content": [{"type": "text", "text": json.dumps(
                                                body("CLARIFY", owner_clarifications=["B?"]))}]}), CONFLICTING),
}


@pytest.mark.parametrize("variant", list(AMBIGUOUS))
def test_ambiguous_payload_fails(make, variant):
    shape, build, expected = AMBIGUOUS[variant]
    raw = build()
    producer = FixtureProducer(lambda p, u: respond(p, u, raw, shape, 0))
    h, vector = make(producer)
    result = h.service.assess(candidate(vector), PLAN)
    assert isinstance(result, Hold) and result.reason_code == ATTEMPT_FAILURE, result
    assert h.outcome(X)["failure_class"] == expected and h.raw(h.consumer.latest(X)).encode() == raw
    assert not isinstance(h.service.current(candidate(vector), PLAN), ReadinessEligibility)


def test_raising_producer_records_attempt_failure(make):
    def raising(p, u):
        if len(p.calls) == 1:
            raise RuntimeError("adapter crashed after launch")
        return respond(p, u, body("READY"))
    producer = FixtureProducer(raising)
    h, vector = make(producer)
    try:
        result = h.service.assess(candidate(vector), PLAN)
    except RuntimeError as error:  # Escaping would leave the opened attempt without an outcome.
        result = error
    assert isinstance(result, Hold) and (result.reason_code, result.detail) == (ATTEMPT_FAILURE, PROVIDER_FAILURE)
    assert h.consumer.latest(X)["outcome"]["failure_class"] == PROVIDER_FAILURE  # Never left open.
    assert isinstance(h.service.assess(candidate(vector), PLAN), ReadinessEligibility)  # A fresh attempt may follow.


def test_mcp_without_process_exit_is_recognized(make):
    producer = FixtureProducer(lambda p, u: respond(p, u, envelope(body("READY")), MCP, None))
    h, vector = make(producer)
    assert isinstance(h.service.assess(candidate(vector), PLAN), ReadinessEligibility)
    cli = FixtureProducer(lambda p, u: respond(p, u, body("READY"), DIRECT, None))
    g, vector = make(cli)
    result = g.service.assess(candidate(vector), PLAN)
    assert isinstance(result, Hold) and result.detail == PROVIDER_FAILURE  # A CLI result needs its exit status.


def test_clarify_annotation_survives_one_pointer_conflict(make):
    producer = ready_producer(**{X: [body("CLARIFY", owner_clarifications=list(QUESTIONS))]})
    h, vector = make(producer)
    commit, raced = h.store.commit, []

    def racing(profile, aggregate, expected, state):
        if aggregate.startswith("readiness:") and any("clarifications" in a for a in state.get("attempts", [])) \
                and not raced:
            raced.append(aggregate)
            commit(profile, aggregate, expected, {**h.consumer.read(X)[1]})  # Another writer moves the pointer.
            raise VersionConflict("moved")
        return commit(profile, aggregate, expected, state)
    h.store.commit = racing
    result = h.service.assess(candidate(vector), PLAN)
    assert raced and isinstance(result, Hold) and result.reason_code == CLARIFY_PENDING_DECISION, result
    assert len(h.consumer.latest(X).get("clarifications") or []) == 2


# --- SF-REQ-015-AC-05: PY-10 bootstrap-assessor history replay -------------------------------------------------


def py10_history(corrupt: bool = False) -> tuple[HistoricalAssessment, ...]:
    manifest = json.loads(pinned(*PM))
    [entry] = [e for e in manifest["entries"] if e.get("path") == PY10_PATH]
    items = []
    for index, (revision, identity, expected, _, _) in enumerate(PY10):
        raw = blob(identity) + (b"\n" if corrupt and index == 1 else b"")
        items.append(HistoricalAssessment(revision, PY10_PATH, identity, expected, raw, entry["producer"]))
    return tuple(items)


def test_py10_history_replay(make):
    h, h.vector = make(ready_producer())
    manifest = json.loads(pinned(*PM))
    [declared] = [e for e in manifest["entries"] if e.get("path") == PY10_PATH]
    assert (declared["producer"], declared["native_agent_ready"], declared["disposition_vocabulary"]) == \
        ("surrogate-bootstrap-assessor", False, "alienintent-bootstrap-assessor")
    records = h.profile.readiness_history.replay(py10_history())
    assert [r["disposition"] for r in records] == ["BLOCKED", "SPLIT_RECOMMENDED", "READY"]  # Verbatim.
    assert all(r["record_kind"] == "SurrogateReadinessAssessment" and r["native_agent_ready"] is False
               and r["producer"] == "surrogate-bootstrap-assessor"
               and r["label"] == "SURROGATE_READINESS_HISTORY_NOT_AGENT_READY" for r in records)
    assert [r["assessed_baseline"] for r in records] == [b for *_, b in PY10]
    facts = git_facts()
    assert facts["py10_follow_history"] == [r for r, *_ in reversed(PY10)]  # The complete retained history.
    assert facts["py10_blob_at_revision"] == {r: b for r, b, *_ in PY10}
    assert facts["py09b_merge_is_ancestor_of_ready"] and "PY-09B" in facts["py09b_merge_subject"]
    ready = records[2]
    assert (ready["revision"], ready["blob"]) not in {(r["revision"], r["blob"]) for r in records[:2]}
    history = json.loads(blob(PY10[2][1]))["provider_evidence"]["assessment_history"]
    assert "e25da1f" in json.dumps(history) and "85b6060" in json.dumps(history)
    matrix = json.loads(pinned(*M))["coercion_finding"]["historical_assessments"][:3]
    for (revision, identity, expected, disposition, _), stripped, record_ in zip(PY10, matrix, records):
        raw = h.repository.get(ref_from_document(record_["raw_ref"]), SCOPE).value.encode()
        assert sha256(raw).hexdigest() == expected == sha256(blob(identity)).hexdigest()
        assert sha256(raw.decode().strip().encode()).hexdigest() == stripped["sha256_of_stripped_text"]
        assert (stripped["revision"], stripped["disposition"]) == (revision, disposition)
    second = h.repository.get(ref_from_document(records[1]["ref"]), SCOPE)
    assert second.header.preceding_refs[0] == ref_from_document(records[0]["ref"])
    for index, (_, identity, _, disposition, _) in enumerate(PY10):
        document = json.loads(blob(identity))
        assert not looks_native_agent_ready(document)  # Negative shape evidence only.
        result, _ = observe_once(h, blob(identity), DIRECT, identity=f"WO-99098{index}", bound=False)
        assert isinstance(result, AttemptFailure)
        assert result.failure_class == (PROVENANCE if disposition == "READY" else UNKNOWN_DISPOSITION)


def test_py10_history_digest_mismatch_holds(make):
    h, _ = make(ready_producer())
    before = sorted(p.name for p in (h.repository.root / "objects").iterdir())
    result = h.profile.readiness_history.replay(py10_history(corrupt=True))
    assert isinstance(result, Hold) and result.reason_code == "HISTORY_DIGEST_MISMATCH"
    assert sorted(p.name for p in (h.repository.root / "objects").iterdir()) == before


# --- 015-composed-authority: provenance at the actual profile boundary ------------------------------------------


@pytest.mark.parametrize("variant", ["unbound", "version_unknown", "wrong_package"])
def test_unbound_or_unestablished_provenance_holds_before_launch(make, variant):
    producer = ready_producer()
    options = {"unbound": {"executable": None}, "version_unknown": {"package": {"metadata": False}},
               "wrong_package": {"package": {"name": "agent-ready-surrogate"}}}[variant]
    h, vector = make(producer, **options)
    before = h.guarded()
    result = h.service.assess(candidate(vector), PLAN)
    assert isinstance(result, Hold) and result.reason_code == CAPABILITY_PROVENANCE_HOLD, result
    assert result.detail == {"unbound": "UNBOUND", "version_unknown": "PRODUCT_VERSION_UNKNOWN",
                             "wrong_package": "WRONG_PACKAGE"}[variant]
    assert producer.calls == [] and h.consumer.history(X) == ()  # Refused before launch; no attempt.
    assert h.guarded() == before
    [held] = h.evidence("readiness.provenance_held")
    assert json.loads(held["value"])["launched"] is False


def test_unknown_product_version_holds(make):
    producer = ready_producer()
    h, vector = make(producer, package={"version": UNKNOWN})
    result = h.service.assess(candidate(vector), PLAN)
    assert (result.reason_code, result.detail) == (CAPABILITY_PROVENANCE_HOLD, "PRODUCT_VERSION_UNKNOWN")
    assert producer.calls == []


def test_no_producer_configured_holds(make):
    h, vector = make(None)
    result = h.service.assess(candidate(vector), PLAN)
    assert (result.reason_code, result.detail) == (CAPABILITY_PROVENANCE_HOLD, "UNBOUND")


def surrogate(p, u):
    document = {k: v for k, v in body("READY").items() if k != "provider_evidence"}
    return ProducerResponse(encode(document), 0, False, DIRECT, None)


def copied(p, u):
    saved = record("ready")["provenance"]
    document = body("READY")
    forged = InvocationCustody(u.attempt_id, digest(u.text), "agent-ready", saved["agent_ready_version"],
                               saved["executable"], tuple(saved["invocation"]), saved["provider"],
                               saved["started_at"], saved["ended_at"], saved["provider_evidence"])
    return ProducerResponse(encode(document), 0, False, DIRECT, forged)


def disconnected(p, u):
    document = body("READY")
    other = custody(p.binding, u, document["provider_evidence"], attempt_id="00000000-0000-4000-8000-000000000000")
    return ProducerResponse(encode(document), 0, False, DIRECT, other)


REFUSALS = {"schema_perfect_surrogate": (surrogate, "NO_INVOCATION_CUSTODY"),
            "copied_provider_evidence": (copied, "PRODUCER_NOT_BOUND"),
            "disconnected_response": (disconnected, "RESPONSE_NOT_CORRELATED")}


@pytest.mark.parametrize("variant", list(REFUSALS))
def test_surrogate_and_copied_evidence_refused(make, variant):
    script, reason = REFUSALS[variant]
    producer = FixtureProducer(script)
    h, vector = make(producer)
    before = h.guarded()
    result = h.service.assess(candidate(vector), PLAN)
    assert isinstance(result, Hold) and (result.reason_code, result.detail) == (ATTEMPT_FAILURE, PROVENANCE), result
    outcome = h.outcome(X)
    assert outcome["failure_class"] == PROVENANCE and outcome["detail"] == reason
    assert looks_native_agent_ready(json.loads(h.raw(h.consumer.latest(X))))  # The shape alone looked native.
    assert not isinstance(h.service.current(candidate(vector), PLAN), ReadinessEligibility)
    assert h.guarded() == before


PROVENANCE_FIELDS = {"producer", "product_version", "version_source", "editable_revision", "executable", "transport",
                     "schema_binding", "contract_version", "binding_refusal", "provider", "provider_evidence", "model",
                     "input_fingerprint", "input_sha256", "invocation", "exit_status", "timed_out"}


def intact(p, u):
    return respond(p, u, encode(record("ready")["assessment"]))


def test_intact_binding_reaches_consumer_without_release_bypass(make, monkeypatch):
    calls = []
    monkeypatch.setattr(release_domain, "admit_release", lambda *a: calls.append(a))
    producer = FixtureProducer(intact)
    h, vector = make(producer)
    assert h.service is not None, "UpstreamProfile composes no readiness consumer"
    before = h.guarded()
    text = pinned_contract_text()
    result = h.service.assess(candidate(vector, text=text), PLAN)
    assert isinstance(result, ReadinessEligibility), result
    retained = record("ready")
    entry, outcome = h.consumer.latest(X), h.outcome(X)
    provenance = outcome["provenance"]
    assert set(provenance) == PROVENANCE_FIELDS
    assert provenance["contract_version"] == CONTRACT_VERSION == \
        "package-release-bound; no result-level identifier (agent-ready#1)"
    assert (provenance["producer"], provenance["product_version"]) == ("agent-ready", "0.1.0rc1")
    assert provenance["version_source"].startswith("importlib.metadata:") and provenance["model"] == UNKNOWN
    assert provenance["executable"] == str(h.executable) and provenance["binding_refusal"] is None
    assert provenance["provider_evidence"] == retained["assessment"]["provider_evidence"]  # Unmodified.
    assert provenance["input_sha256"] == "sha256:" + retained["provenance"]["input_sha256"]
    assert provenance["invocation"]["attempt_id"] == entry["attempt_id"] == result.attempt_id
    assert entry["raw_ref"] != entry["outcome_ref"]  # Raw bytes and provenance are distinct evidence.
    assert h.raw(entry).encode() == encode(retained["assessment"])
    raw_record = h.repository.get(ref_from_document(entry["raw_ref"]), SCOPE)
    assert raw_record.evidence_id == RETAINED_ASSESSMENT and raw_record.method == "raw-bytes/utf-8"
    assert calls == [] and h.guarded() == before  # Eligibility only; no release bypass.


def test_composition_path_executed(make):
    producer = FixtureProducer(intact)
    h, vector = make(producer)
    assert h.service is not None, "UpstreamProfile composes no readiness consumer"
    assert isinstance(h.service, ReadinessAdmission)
    assert h.service.consumer is h.profile.readiness_consumer and h.service.binding is h.profile.readiness_binding
    assert h.service.producer is producer and h.service.design is h.profile.design_readiness
    h.service.assess(candidate(vector), PLAN)
    _, state = h.store.read_state(PROFILE, "readiness:" + X)  # The composed store holds the attempt.
    assert state["attempts"][0]["attempt_id"] == producer.calls[0].attempt_id


# --- U-4 binding condition and release separation ---------------------------------------------------------------

READINESS_MODULES = ("src/alienintent/context_assembly/domain/readiness.py",
                     "src/alienintent/context_assembly/ports/readiness.py",
                     "src/alienintent/context_assembly/application/readiness_service.py",
                     "src/alienintent/context_assembly/adapters/readiness_clarification.py",
                     "src/alienintent/execution_coordination/domain/readiness.py",
                     "src/alienintent/execution_coordination/ports/readiness.py",
                     "src/alienintent/execution_coordination/adapters/assessment_consumer.py",
                     "src/alienintent/composition/readiness.py")
# (importing group.layer, imported group.layer) pairs measured at baseline 04cdd8c for the two affected groups.
BASELINE_PAIRS = {
    "context_assembly.adapters": {"control_plane.application", "evidence_learning.domain", "evidence_learning.ports",
                                  "execution_coordination.domain"},
    "context_assembly.application": {"evidence_learning.domain", "evidence_learning.ports",
                                     "execution_coordination.domain", "execution_coordination.ports"},
    "context_assembly.domain": {"evidence_learning.domain", "execution_coordination.domain"},
    "context_assembly.ports": {"execution_coordination.domain"},
    "execution_coordination.adapters": {"evidence_learning.domain", "evidence_learning.ports", "installation.domain",
                                        "installation.ports"},
    "execution_coordination.application": {"control_plane.application", "control_plane.ports",
                                           "invocation_runtime.domain"},
    "execution_coordination.domain": set(),
    "execution_coordination.ports": {"evidence_learning.domain"},
}


def imported_modules(path: Path) -> list[str]:
    modules = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(a.name for a in node.names)
    return modules


def test_no_new_cross_group_import_pair():
    """U-4 (FX-U7 D-1 precedent): no new cross-group module pair; execution_coordination never imports context_assembly."""
    source = ROOT / "src" / "alienintent"
    observed: dict[str, set[str]] = {}
    for path in source.rglob("*.py"):
        parts = path.relative_to(source).parts
        if len(parts) < 3 or parts[0] not in ("context_assembly", "execution_coordination"):
            continue
        key = f"{parts[0]}.{parts[1]}"
        for module in imported_modules(path):
            names = module.split(".")
            if names[0] == "alienintent" and len(names) > 2 and names[1] != parts[0]:
                observed.setdefault(key, set()).add(".".join(names[1:3]))
    for key, pairs in observed.items():
        assert pairs <= BASELINE_PAIRS[key], (key, pairs - BASELINE_PAIRS[key])
    assert not any(p.startswith("context_assembly") for k, v in observed.items()
                   if k.startswith("execution_coordination") for p in v)


def test_readiness_modules_never_release_or_import_agent_ready():
    for path in READINESS_MODULES:
        text = (ROOT / path).read_text()
        assert "admit_release" not in text and "ReleaseRequest" not in text, path
        assert not any(m.split(".")[0] == "agent_ready" for m in imported_modules(ROOT / path)), path
