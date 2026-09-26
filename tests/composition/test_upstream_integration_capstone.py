"""FX-A capstone (WO-220211, node A): the Wave 2A upstream chain composed end to end.

inventory -> ambiguity -> premise/proof -> design applicability -> compiler-derived initial compilation -> lint and
retained assessment consumption, over one real temporary SQLite store, local evidence, the FactoryCoordinator
lifecycle and LocalWorkManagement (the Project stand-in). Every stage is the unchanged predecessor service; the only
new source is the UpstreamIntegration wiring. The producer is the U9 scripted double bound to a disposable fixture
package (FIXTURE_PRODUCER_NOT_NATIVE); no Agent Ready, provider or model is invoked. One discriminating control per
material failure class is applied by tools/evidence/fx_a_evidence.py.
"""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from alienintent.composition.compilation import CoordinatorDependencyLifecycle
from alienintent.composition.design_admission import EDGE_AUTHORITY_GAP, RetainedDirectionAuthority
from alienintent.composition.premise_evidence import RetainedDoctorPremiseEvidence
from alienintent.composition.upstream_integration import UpstreamIntegration
from alienintent.composition.upstream_profile import UpstreamProfile
from alienintent.context_assembly.domain.ambiguity import (
    SemanticQuestion, SemanticReview, fields, snapshot_from_document)
from alienintent.context_assembly.domain.compilation import CompilationHold
from alienintent.context_assembly.domain.design_admission import (
    MECHANICALLY_HELD, REVIEW_REQUIRED, MechanicalReport, ReviewAdmitted, design_from_document)
from alienintent.context_assembly.domain.initial_compilation import CompilationCandidate, is_initial_compilation, items
from alienintent.context_assembly.domain.inventory import Manifest, assemble
from alienintent.context_assembly.domain.readiness import LintHold
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.domain.proof_plan import PredicateMapping, RequirementRevision
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.execution_coordination.adapters.local_work_management import LocalWorkManagement
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application import factory_coordinator
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
from alienintent.execution_coordination.domain import release as release_domain
from alienintent.execution_coordination.domain.lifecycle import ExecutionState, LifecycleStage
from alienintent.execution_coordination.domain.readiness import (
    CAPABILITY_PROVENANCE_HOLD, STALE_ASSESSMENT, Hold, ReadinessEligibility, digest)
from tests.context_assembly.test_ambiguity import body, record
from tests.context_assembly.test_design_admission import (
    DESIGN, DESIGN_SHA256, PREMISE_MAPPING, PREMISE_SHA256, REVIEWERS, _Recorded, review)
from tests.context_assembly.test_initial_compilation import (
    DKEY, EXISTING, LIMITS, MAPPING_REVIEWER, R1, R2, R3, SOURCES, SUPERSESSION, Mappings, design_document, predicate,
    sha)
from tests.context_assembly.test_readiness_consumer import FixtureProducer, fixture_package, scripted

ROOT = Path(__file__).resolve().parents[2]
PROJECT, PROFILE = "AlienLogicLab/alienintent", "fx-a"
INVOCATION = "AlienLogicLab/alienintent#119:PRODUCER:c35b931d-a6be-43ba-8232-43c960067adb"
SCOPE = frozenset({"private"})
U1, U2 = "WO-000005", "WO-000006"  # The compiler-reserved identities of R1 and R2 (FX-U8 identity snapshot).
DECISION = "decisions/FD-A-integration.md"
DECISIONS = (DECISION,)
# Everything the upstream chain may write; any other aggregate is lifecycle/Project/release state it must not touch.
# decision-inbox holds the questions the ambiguity stage routes to the existing DecisionInbox; it launches no work.
UPSTREAM_NAMESPACES = ("upstream:", "readiness:", "decision-inbox")


def assessment(disposition: str = "READY") -> dict:
    """A fixture-producer body in the retained native READY record's shape (FIXTURE_PRODUCER_NOT_NATIVE)."""
    from tests.context_assembly.test_readiness_consumer import body as fixture_body
    return fixture_body(disposition)


class Harness:
    """One disposable profile with every Wave 2A stage composed through UpstreamProfile and the integration."""

    def __init__(self, root: Path, executable: str | None = "package"):
        root.mkdir(mode=0o700)
        self.store = SQLiteOperationalStore(root / "operational.sqlite")
        self.repository = LocalEvidenceRepository(root / "evidence", PROJECT, PROFILE)
        self.work = LocalWorkManagement(root / "work", PROFILE, PROJECT, (), clock=lambda: 0.0)
        self.coordinator = FactoryCoordinator(self.store, self.work, None, LocalArtifactStore(root / "p", root / "v"),
                                              PROFILE)
        self.decisions = root / "governing"
        (self.decisions / "decisions").mkdir(parents=True)
        (self.decisions / DECISION).write_text("# FD-A\n\nIntegration consumes the proven providers unchanged.\n")
        self.mappings = Mappings()
        self.producer = FixtureProducer(scripted({}, default=assessment()))
        self.definition = Ref(PROJECT, PROFILE, "FX-A-contract", sha("FX-A"), "repository:WO-220211.md")
        self.profile = UpstreamProfile(
            self.repository, self.store, PROJECT, PROFILE, self.definition, INVOCATION, "Founder", SCOPE,
            premise_evidence=RetainedDoctorPremiseEvidence(ROOT, Path(PREMISE_MAPPING), PREMISE_SHA256, PROJECT,
                                                           PROFILE),
            premise_target="AlienLogicLab/alienintent-sandbox", proof_mappings=self.mappings,
            mapping_reviewer=MAPPING_REVIEWER, supersession_authority=SUPERSESSION, design_checks=_Recorded(),
            design_authority=RetainedDirectionAuthority(ROOT, DESIGN, DESIGN_SHA256, EDGE_AUTHORITY_GAP, PROJECT,
                                                        PROFILE),
            design_reviewers=REVIEWERS, dependency_lifecycle=CoordinatorDependencyLifecycle(self.coordinator),
            readiness_producer=self.producer,
            readiness_executable=fixture_package(root) if executable == "package" else None)
        self.producer.binding, self.producer.consumer = self.profile.readiness_binding, self.profile.readiness_consumer
        self.integration = UpstreamIntegration(self.profile, self.decisions)

    # Stage 1 and 2: inventory publication and ambiguity inspection.
    def requirements(self, sources: dict) -> dict[str, str]:
        records = tuple(record(r, r + ".md", lines, authority=authority) for r, (lines, authority) in
                        sorted(sources.items()))
        version, previous = self.profile.inventory.read()
        self.profile.inventory.publish(Manifest(PROJECT, tuple(r.spec for r in records), "fx-a"),
                                       assemble(PROJECT, records, snapshot_from_document(previous) if previous else None),
                                       version)
        self.profile.ambiguity.inspect(self.profile.ambiguity.read()[0])
        return {r.requirement_id: r.revision for r in snapshot_from_document(self.profile.inventory.read()[1]).current}

    # Stage 3 and 4: premise evidence under design admission, then independent review of that exact revision.
    def design(self, document: dict):
        report = self.profile.design.inspect(document, self.profile.design.read(document["design_key"])[0])
        assert isinstance(report, MechanicalReport), report
        reviewed = self.profile.design.record_review(document["design_key"], review(report),
                                                     self.profile.design.read(document["design_key"])[0])
        return report, reviewed

    # Stage 3: proof plans derived from reviewed mappings before implementation, bound to the design revision.
    def plan(self, rid: str, revision: str, document: dict) -> None:
        design = design_from_document(document)
        semantic = next(r.semantic for r in snapshot_from_document(self.profile.inventory.read()[1]).current
                        if r.requirement_id == rid)
        acceptance = tuple(c.split(":", 1)[0] for c in items(fields(semantic)["Acceptance"]))
        requirement_ref = Ref(PROJECT, PROFILE, rid, "sha256:" + revision, "inventory:" + rid)
        self.mappings.entries[rid] = PredicateMapping(
            Ref(PROJECT, PROFILE, "mapping/" + rid, sha("mapping/" + rid + design.digest), "fixture:mapping/" + rid),
            rid, requirement_ref.revision_digest, design.digest, MAPPING_REVIEWER,
            Ref(PROJECT, PROFILE, "review/" + rid, sha("review/" + rid), "fixture:review/" + rid),
            tuple(predicate(a) for a in acceptance))
        self.profile.proofs.derive(RequirementRevision(rid, acceptance, requirement_ref),
                                   Ref(PROJECT, PROFILE, design.design_key, design.digest, "design:" + design.design_key),
                                   self.profile.proofs.read(rid)[0])

    def lifecycle(self, identity: str, stage: str) -> None:
        """Fixture setup only: the existing decomposed predecessor is DONE before the chain runs."""
        version, _ = self.store.read_state(PROFILE, "factory:" + identity)
        self.store.commit(PROFILE, "factory:" + identity, version,
                          FactoryCoordinator._encode(ExecutionState(stage=LifecycleStage(stage))))

    def outside(self) -> dict:
        """Lifecycle, release, Project and every other aggregate outside the upstream chain's own namespaces."""
        return {"states": [(a, v, json.dumps(s, sort_keys=True)) for a, v, s in self.store.list_states(PROFILE)
                           if not a.startswith(UPSTREAM_NAMESPACES)],
                "project_receipts": self.work.receipts(), "reservations": self.store.recovery_reservations(PROFILE)}

    def evidence(self) -> list[dict]:
        return [json.loads(p.read_text())["payload"] for p in sorted((self.repository.root / "objects").iterdir())]


def sources(**changes) -> dict:
    """The FX-A requirement sources (the FX-U8 set), each with its inventory authority status."""
    value = {r: (SOURCES[r], "approved") for r in (R1, R2, R3)}
    value.update(changes)
    return value


def upstream(h: Harness, source_set=None, document_changes=None) -> tuple[dict, dict]:
    """Stages 1-4: inventory, inspection, premise-checked verified design and its proof plans."""
    revisions = h.requirements(source_set or sources())
    document = design_document({r: revisions[r] for r in (R1, R2) if r in revisions}, **(document_changes or {}))
    h.design(document)
    for rid in (R1, R2):
        if rid in revisions:
            h.plan(rid, revisions[rid], document)
    h.lifecycle(EXISTING, "DONE")
    return revisions, document


def ready(h: Harness):
    """The whole chain to readiness eligibility for R1's derived unit."""
    upstream(h)
    compiled = h.integration.compile(DKEY, deepcopy(LIMITS))
    assert isinstance(compiled, CompilationCandidate), getattr(compiled, "findings", compiled)
    candidate = h.integration.candidate(compiled, U1, DECISIONS)
    plan = h.integration.proof_plan(compiled, U1)
    outcome = h.integration.assess(candidate, plan)
    assert isinstance(outcome, ReadinessEligibility), outcome
    return compiled, candidate, plan, outcome


def no_release_asserted(h: Harness, *outputs) -> None:
    for payload in h.evidence():
        value = payload.get("value")
        document = json.loads(value) if isinstance(value, str) and value.startswith("{") else {}
        assert "Release" not in str(document.get("record_kind", "")), document
        assert not any(document.get(k) for k in ("released", "release_authorized", "release_admitted")), document
    for output in outputs:
        assert not isinstance(output, release_domain.ReleaseRequest)
        assert type(output).__name__ not in ("ReleaseAdmitted", "Released")


@pytest.fixture
def make(tmp_path):
    count = iter(range(100))
    return lambda **options: Harness(tmp_path / f"h{next(count)}", **options)


# --- The ordered chain, positive path ---------------------------------------------------------------------------


def test_chain_runs_in_order_to_eligibility(make):
    h = make()
    compiled, candidate, plan, outcome = ready(h)
    document = compiled.document()
    assert is_initial_compilation(document) and document["admitted_for_assessment"]
    # Each stage's output is the next stage's pinned input.
    assert document["inputs"]["inventory"] == snapshot_from_document(h.profile.inventory.read()[1]).digest
    assert document["inputs"]["inspection"] == h.profile.ambiguity.report().digest
    assert set(document["inputs"]["proof_plans"]) == {R1, R2} and plan == (document["inputs"]["proof_plans"][R1],)
    assert candidate["design_vector"] == h.integration.current_vector(DKEY)
    assert h.profile.design_readiness.admit(DKEY, candidate["design_vector"]).admitted
    # The eligibility binds the compiled contract, and one attributable attempt was persisted before launch.
    assert outcome.identity == U1 and len(h.producer.calls) == 1 and h.producer.opened_before_call == [True]
    unit = next(u for u in document["units"] if u["identity"] == U1)
    assert outcome.contract_digest == unit["content_digest"]
    assert h.integration.current(candidate, plan) == outcome  # Unchanged upstream: the retained READY applies.
    # R2's unit depends on R1's not-yet-materialized unit: the edge flows into lint and nothing is launched.
    dependent = h.integration.assess(h.integration.candidate(compiled, U2, DECISIONS),
                                     h.integration.proof_plan(compiled, U2))
    assert isinstance(dependent, LintHold) and (dependent.duty, dependent.field) == ("dependency", "dependencies")
    assert U1 in dependent.detail and len(h.producer.calls) == 1


def test_composition_requires_every_stage():
    with pytest.raises(ValueError, match="initial compilation and readiness"):
        UpstreamIntegration(type("Partial", (), {"initial_compilation": None, "readiness": None})(), Path("."))


# --- Class 1: inventory, ambiguity and premise evidence gate design applicability and compilation ---------------


FAILED_UPSTREAM = {
    # An unapproved source is inventoried but never eligible: design applicability is not current.
    "inventory": (dict(source_set=sources(**{R1: (SOURCES[R1], "proposed")})), "STALE"),
    # A requirement without an authority line is held by the inspection: design applicability is not current.
    "ambiguity": (dict(source_set=sources(**{R1: (body(R1, Intent="Derive units from pinned requirements.",
                                                         Scope="unit derivation", Authority=None,
                                                         Acceptance=f"{R1}-AC-01: every unit carries every field."),
                                                    "approved")})), "STALE"),
    # A design premise asks for an observable the retained evidence cannot supply.
    "premise": ({}, MECHANICALLY_HELD),
}


@pytest.mark.parametrize("stage", list(FAILED_UPSTREAM))
def test_failed_upstream_evidence_stops_before_design_and_compilation(make, stage):
    h = make()
    options, design_status = FAILED_UPSTREAM[stage]
    if stage == "premise":  # The operator runs every stage; review is attempted on whatever admission reported.
        revisions = h.requirements(sources())
        document = design_document({r: revisions[r] for r in (R1, R2)})
        document["premises"] = [{**document["premises"][0],
                                 "requested": [*document["premises"][0]["requested"], "PLATFORM_CREDENTIAL_DENIAL"]}]
        report, reviewed = h.design(document)
        for rid in (R1, R2):
            h.plan(rid, revisions[rid], document)
        h.lifecycle(EXISTING, "DONE")
    else:
        upstream(h, **options)
    compiled = h.integration.compile(DKEY, deepcopy(LIMITS))
    assert isinstance(compiled, CompilationHold), "failed upstream evidence must not compile"
    assert (compiled.reason_code, compiled.detail) == ("DESIGN_HOLD", design_status), compiled.findings
    assert not h.profile.design_readiness.admit(DKEY, h.integration.current_vector(DKEY)).admitted
    assert h.profile.initial_compilation.reservations() == {} and h.producer.calls == []
    if stage == "premise":
        assert report.status == design_status and not isinstance(reviewed, ReviewAdmitted)


# --- Class 2: a source, decision or design revision invalidates downstream applicability/readiness ---------------


def revise_source(h: Harness):
    h.requirements(sources(**{R1: (body(R1, Intent="Derive units from revised requirements.",
                                         Scope="unit derivation; contract fields",
                                         Acceptance=f"{R1}-AC-01: every unit carries every contract field; "
                                                    f"{R1}-AC-02: every obligation keeps an explicit extent."),
                                    "approved")}))


def withdraw_approval(h: Harness):
    """The same text, no longer approved: the revision digest is unchanged, eligibility is not."""
    h.requirements(sources(**{R1: (SOURCES[R1], "proposed")}))


def hold_by_inspection(h: Harness):
    """An independent semantic question holds R1 at its unchanged revision."""
    revision = h.integration.current_vector(DKEY)["requirements"][R1]
    question = SemanticQuestion("Does 'every unit' include deferred units?", ((R1 + ".md", 2, 2),))
    h.profile.ambiguity.inspect(h.profile.ambiguity.read()[0],
                                (SemanticReview("reviewer-jc", "review:jc-a", R1, revision, (question,)),))


def revise_decision(h: Harness):
    (h.decisions / DECISION).write_text("# FD-A\n\nRevised: integration consumes the proven providers unchanged.\n")


def revise_design(h: Harness):
    document = design_document({r: h.integration.current_vector(DKEY)["requirements"][r] for r in (R1, R2)})
    document["decisions"][0] = {**document["decisions"][0], "statement": "one unit per specified requirement, revised"}
    report = h.profile.design.inspect(document, h.profile.design.read(DKEY)[0])
    assert isinstance(report, MechanicalReport) and report.status == REVIEW_REQUIRED


REVISIONS = {"source": (revise_source, LintHold, "STALE"), "approval": (withdraw_approval, LintHold, "STALE"),
             "ambiguity": (hold_by_inspection, LintHold, "STALE"),
             "decision": (revise_decision, Hold, STALE_ASSESSMENT), "design": (revise_design, LintHold, REVIEW_REQUIRED)}


@pytest.mark.parametrize("revision", list(REVISIONS))
def test_revision_mismatch_invalidates_downstream_readiness(make, revision):
    h = make()
    compiled, candidate, plan, outcome = ready(h)
    retained = h.profile.readiness_consumer.history(U1)
    before = h.outside()
    change, kind, reason = REVISIONS[revision]
    change(h)
    current = h.integration.current(candidate, plan)
    assert not isinstance(current, ReadinessEligibility), "a stale READY must never be reused after a revision"
    assert isinstance(current, kind), current
    assert (current.detail if kind is LintHold else current.reason_code) == reason, current
    if kind is LintHold:  # The design gate is what refuses: applicability, then compilation, both hold.
        assert (current.duty, current.field) == ("architecture", "design_applicability")
        recompiled = h.integration.compile(DKEY, deepcopy(LIMITS))
        assert isinstance(recompiled, CompilationHold) and recompiled.reason_code == "DESIGN_HOLD"
    # Nothing was relaunched, the retained assessment is unchanged, and nothing outside upstream moved.
    assert len(h.producer.calls) == 1 and h.profile.readiness_consumer.history(U1) == retained
    assert h.outside() == before


def test_superseded_proof_plan_invalidates_readiness(make):
    """A re-derived proof plan (a revised reviewed mapping) leaves the pinned plan stale: lint holds, nothing launches."""
    h = make()
    compiled, candidate, plan, _ = ready(h)
    vector = h.integration.current_vector(DKEY)
    mapping = h.mappings.entries[R1]
    h.mappings.entries[R1] = replace(mapping, mapping_ref=replace(mapping.mapping_ref,
                                                                  revision_digest=sha("revised mapping/" + R1)))
    derived = h.profile.proofs.derive(
        RequirementRevision(R1, tuple(p.acceptance_id for p in mapping.predicates),
                            Ref(PROJECT, PROFILE, R1, "sha256:" + vector["requirements"][R1], "inventory:" + R1)),
        Ref(PROJECT, PROFILE, DKEY, vector["design"], "design:" + DKEY), h.profile.proofs.read(R1)[0])
    assert derived.digest not in plan
    for result in (h.integration.current(candidate, plan), h.integration.assess(candidate, plan)):
        assert isinstance(result, LintHold), "a superseded proof plan must not keep the READY"
        assert (result.duty, result.field) == ("verification", "proof_plan")
    assert len(h.producer.calls) == 1


def test_unavailable_governing_decision_holds_before_assessment(make):
    h = make()
    compiled, candidate, plan, _ = ready(h)
    (h.decisions / DECISION).unlink()
    held = h.integration.assess(candidate, plan)
    assert isinstance(held, LintHold) and (held.duty, held.field) == ("decision", "governing_decisions")
    assert len(h.producer.calls) == 1


# --- Class 3: compilation and retained assessment consumption stay separate typed boundaries --------------------


def test_compilation_and_assessment_stay_separate_boundaries(make):
    h = make()
    upstream(h)
    compiled = h.integration.compile(DKEY, deepcopy(LIMITS))
    assert isinstance(compiled, CompilationCandidate)
    candidate = h.integration.candidate(compiled, U1, DECISIONS)
    plan = h.integration.proof_plan(compiled, U1)
    # A compiled candidate is admitted for assessment only; no retained assessment means no eligibility.
    unassessed = h.integration.current(candidate, plan)
    assert isinstance(unassessed, Hold) and unassessed.reason_code == "NO_ASSESSMENT"
    whole = h.profile.readiness.assess(compiled.document(), plan)
    assert isinstance(whole, LintHold), "a compilation document is not a readiness candidate"
    # A caller bypassing the integration with a stale pinned vector is still refused by the design gate in lint.
    revise_design(h)
    bypass = h.profile.readiness.assess(candidate, plan)
    assert isinstance(bypass, LintHold), "readiness must not bypass design applicability"
    assert (bypass.duty, bypass.field) == ("architecture", "design_applicability")
    assert h.producer.calls == [] and h.profile.readiness_consumer.history(U1) == ()


def test_unbound_producer_holds_before_launch(make):
    h = make(executable=None)
    upstream(h)
    compiled = h.integration.compile(DKEY, deepcopy(LIMITS))
    held = h.integration.assess(h.integration.candidate(compiled, U1, DECISIONS), h.integration.proof_plan(compiled, U1))
    assert isinstance(held, Hold) and held.reason_code == CAPABILITY_PROVENANCE_HOLD
    assert h.producer.calls == [] and h.profile.readiness_consumer.history(U1) == ()


# --- Class 4: no lifecycle/Project mutation, and no output asserts release ---------------------------------------


def test_integration_mutates_no_lifecycle_or_project_state(make, monkeypatch):
    admitted = []
    original = release_domain.admit_release
    spy = lambda *a: admitted.append(a) or original(*a)  # noqa: E731
    monkeypatch.setattr(release_domain, "admit_release", spy)
    monkeypatch.setattr(factory_coordinator, "admit_release", spy)  # The coordinator's own imported name.
    h = make()
    upstream(h)
    before = h.outside()
    compiled = h.integration.compile(DKEY, deepcopy(LIMITS))
    candidate = h.integration.candidate(compiled, U1, DECISIONS)
    plan = h.integration.proof_plan(compiled, U1)
    outcome = h.integration.assess(candidate, plan)
    revise_source(h)
    held = h.integration.current(candidate, plan)
    recompiled = h.integration.compile(DKEY, deepcopy(LIMITS))
    assert isinstance(outcome, ReadinessEligibility) and isinstance(held, LintHold)
    assert h.outside() == before, "the integration must not write lifecycle, release or Project state"
    assert admitted == []
    no_release_asserted(h, compiled, outcome, held, recompiled)
    assert "release" not in json.dumps(compiled.document()["labels"]).lower()
    assert digest(json.dumps(h.work.receipts(), sort_keys=True)) == digest(json.dumps(before["project_receipts"],
                                                                                    sort_keys=True))
