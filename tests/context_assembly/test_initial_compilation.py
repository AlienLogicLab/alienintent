"""FX-U8 probes: initial compilation derives the INITIAL candidate from pinned requirements, verified design and proof.

Composed over a real temporary SQLite store, local evidence, the U1 inventory, U2 inspection, U5 design gate, U4 proof
planning and the FactoryCoordinator lifecycle. No test supplies a unit or obligation mapping to the compiler. One
discriminating control per material failure class; the proven-red source mutations are in tools/evidence/fx_u8_evidence.py.
"""
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import inspect
import json
from pathlib import Path

import pytest

from alienintent.composition.compilation import CoordinatorDependencyLifecycle
from alienintent.composition.design_admission import EDGE_AUTHORITY_GAP, RetainedDirectionAuthority
from alienintent.composition.premise_evidence import RetainedDoctorPremiseEvidence
from alienintent.composition.upstream_profile import UpstreamProfile
from alienintent.context_assembly.domain.ambiguity import fields, snapshot_from_document
from alienintent.context_assembly.domain.compilation import INITIAL, CompilationHold, ValidationReport, canonical
from alienintent.context_assembly.domain.design_admission import DESIGN_FIELDS, design_from_document
from alienintent.context_assembly.domain.initial_compilation import (
    DERIVED, CompilationCandidate, compile_initial, is_initial_compilation, items)
from alienintent.context_assembly.domain.inventory import Manifest, assemble
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.domain.proof_plan import (
    MappedPredicate, PredicateKind, PredicateMapping, RequirementRevision)
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.execution_coordination.adapters.local_work_management import LocalWorkManagement
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy
from alienintent.execution_coordination.domain.lifecycle import ExecutionState, LifecycleStage
from tests.context_assembly.test_ambiguity import body, record
from tests.context_assembly.test_design_admission import (
    DESIGN, DESIGN_SHA256, OBSERVABLES, PREMISE, PREMISE_MAPPING, PREMISE_SHA256, PRODUCER, REVIEWERS, _Recorded,
    review)

ROOT = Path(__file__).resolve().parents[2]
PROJECT, PROFILE = "AlienLogicLab/alienintent", "fx-u8"
INVOCATION = "AlienLogicLab/alienintent#117:PRODUCER:13bb35b4-c7a1-4b73-89d0-9813dd64de42"
SCOPE = frozenset({"private"})
R0, R1, R2, R3 = "SF-REQ-910", "SF-REQ-911", "SF-REQ-912", "SF-REQ-913"
DKEY, EXISTING = "SF-DESIGN-911", "WO-990300"
MAPPING_REVIEWER, SUPERSESSION = "JC", "Founder"
DERIVED_FROM = ("docs/evidence/fx-u8/requirements.md",)  # Authority text, never an implementation path.

SOURCES = {
    R0: body(R0, Intent="Record every compiled candidate revision.", Scope="candidate revision history",
             Acceptance=f"{R0}-AC-01: a changed input yields a distinct revision."),
    R1: body(R1, Intent="Derive units from pinned requirements.", Scope="unit derivation; contract fields",
             Acceptance=f"{R1}-AC-01: every unit carries every contract field; "
                        f"{R1}-AC-02: every obligation keeps an explicit extent."),
    R2: body(R2, Intent="Order derived units by dependency.",
             Scope=f"dependency edges after {R1}; external predecessor {R3}",
             Acceptance=f"{R2}-AC-01: each dependency edge names a DONE predicate."),
    R3: body(R3, Intent="Existing decomposed requirement.", Scope="existing work",
             Acceptance=f"{R3}-AC-01: already decomposed."),
}
LIMITS = {
    "authority_issuer": "Founder", "retry_policy": "one replacement per phase", "release_policy": "explicit-human-off",
    "authority_references": ["SWF-19", "SF-REQ-013 amendment 2026-09-22"],
    "candidate_custody_requirements": ["publish the exact candidate SHA"], "required_closure_actions": ["land or park"],
    "stop_escalation_conditions": ["authority gap"], "target_repositories": [PROJECT], "baselines": ["main@d716552b"],
    "required_capabilities": ["python", "sqlite"],
    "budget_policy": {"hard_required_dimensions": ["attempts"], "maximum_attempts": 3, "hard_wall_clock_seconds": 7200,
                      "retry_limit": 1, "concurrency_limit": 1},
    "identity_policy": {"family": "WO", "width": 6},
    "identity_snapshot": {"active": ["WO-000001", "WO-000003", EXISTING], "retired": ["WO-000002"],
                          "reserved": ["WO-000004"]},
    "existing_decomposition": {R3: [EXISTING]}}


def sha(text: str) -> str:
    return "sha256:" + sha256(text.encode()).hexdigest()


def design_document(requirements: dict, key=DKEY, capabilities=("python", "sqlite")) -> dict:
    values = {f: {"value": [f.replace("_", " ") + " for the U8 fixture"]} for f in DESIGN_FIELDS}
    values.update({"satisfied_requirements": {"value": sorted(requirements)}, "capabilities": {"value": list(capabilities)},
                   "evidence": {"value": ["an immutable observation retains each compilation record"]},
                   "non_goals": {"value": ["live release"]}})
    return {"schema_version": 1, "record_kind": "DesignContract", "design_key": key, "requirements": requirements,
            "producer": {"actor": PRODUCER[0], "invocation": PRODUCER[1]}, "fields": values,
            "decisions": [{"id": "D-UNITS", "category": "BEHAVIOR", "status": "FIXED",
                           "statement": "one unit per specified requirement", "bound": ""},
                          {"id": "D-LOCAL", "category": "IMPLEMENTATION_LOCAL", "status": "OPEN",
                           "statement": "private helper names", "bound": "private helpers inside context_assembly"}],
            "interface_manifest": [{"port": "InitialCompilation.compile", "producer": "context_assembly",
                                    "consumer": "readiness", "provides": ["candidate"], "requires": ["candidate"]}],
            "premises": [{"premise_id": PREMISE, "criterion": "four-part sandbox isolation",
                          "requested": list(OBSERVABLES)}],
            "dependency_edges": []}


class Mappings:
    """Reviewed predicate mappings, keyed by requirement; the design revision is bound when the plan is derived."""

    def __init__(self) -> None:
        self.entries: dict[str, PredicateMapping] = {}

    def load(self, requirement_id: str):
        return self.entries[requirement_id]


def predicate(acceptance_id: str, key="P1", kind=PredicateKind.MECHANICAL) -> MappedPredicate:
    if kind is PredicateKind.JUDGMENT:
        return MappedPredicate(acceptance_id, key, kind, f"{acceptance_id} is judged by an independent reviewer",
                               DERIVED_FROM, reviewer="JC", inspection_inputs=("candidate",),
                               decision_record="an attributable review record")
    return MappedPredicate(acceptance_id, key, kind, f"{acceptance_id} holds for the composed fixture", DERIVED_FROM,
                           fixture="FX-U8", inputs=("inventory", "design"), expected="admitted", endpoint="compile",
                           command="pytest tests/context_assembly/test_initial_compilation.py",
                           evidence_schema=("observation_ref", "exit_status"), guard="disposable profile")


class Harness:
    def __init__(self, root: Path):
        root.mkdir(mode=0o700)
        self.store = SQLiteOperationalStore(root / "operational.sqlite")
        self.repository = LocalEvidenceRepository(root / "evidence", PROJECT, PROFILE)
        self.work = LocalWorkManagement(root / "work", PROFILE, PROJECT, (), clock=lambda: 0.0)
        self.coordinator = FactoryCoordinator(self.store, self.work, None, LocalArtifactStore(root / "p", root / "v"),
                                              PROFILE)
        self.mappings = Mappings()
        self.definition = Ref(PROJECT, PROFILE, "FX-U8-contract", sha("FX-U8"), "repository:WO-220208.md")
        self.profile = UpstreamProfile(
            self.repository, self.store, PROJECT, PROFILE, self.definition, INVOCATION, "Founder", SCOPE,
            premise_evidence=RetainedDoctorPremiseEvidence(ROOT, Path(PREMISE_MAPPING), PREMISE_SHA256, PROJECT,
                                                           PROFILE),
            premise_target="AlienLogicLab/alienintent-sandbox", proof_mappings=self.mappings,
            mapping_reviewer=MAPPING_REVIEWER, supersession_authority=SUPERSESSION, design_checks=_Recorded(),
            design_authority=RetainedDirectionAuthority(ROOT, DESIGN, DESIGN_SHA256, EDGE_AUTHORITY_GAP, PROJECT,
                                                        PROFILE),
            design_reviewers=REVIEWERS, dependency_lifecycle=CoordinatorDependencyLifecycle(self.coordinator))
        self.service = self.profile.initial_compilation
        self.vectors: dict[str, dict] = {}

    def requirements(self, sources: dict) -> dict[str, str]:
        """Publish the inventory, inspect it and return each current requirement revision."""
        records = tuple(record(r, r + ".md", lines) for r, lines in sorted(sources.items()))
        version, previous = self.profile.inventory.read()
        self.profile.inventory.publish(Manifest(PROJECT, tuple(r.spec for r in records), "fx-u8"),
                                       assemble(PROJECT, records, snapshot_from_document(previous) if previous else None),
                                       version)
        self.profile.ambiguity.inspect(self.profile.ambiguity.read()[0])
        return {r.requirement_id: r.revision for r in self.snapshot_value().current}

    def snapshot_value(self):
        return snapshot_from_document(self.profile.inventory.read()[1])

    def design(self, requirements: dict, state="verified", **changes) -> dict:
        document = design_document(requirements, **changes)
        key = document["design_key"]
        report = self.profile.design.inspect(document, self.profile.design.read(key)[0])
        if state == "verified":
            self.profile.design.record_review(key, review(report), self.profile.design.read(key)[0])
        self.vectors[key] = report.vector
        return document

    def plan(self, rid: str, revision: str, document: dict, predicates=None) -> None:
        design = design_from_document(document)
        semantic = next(r.semantic for r in self.snapshot_value().current if r.requirement_id == rid)
        acceptance = tuple(c.split(":", 1)[0] for c in items(fields(semantic)["Acceptance"]))
        design_ref = Ref(PROJECT, PROFILE, design.design_key, design.digest, "design:" + design.design_key)
        requirement_ref = Ref(PROJECT, PROFILE, rid, "sha256:" + revision, "inventory:" + rid)
        self.mappings.entries[rid] = PredicateMapping(
            Ref(PROJECT, PROFILE, "mapping/" + rid, sha("mapping/" + rid + design.digest), "fixture:mapping/" + rid),
            rid, requirement_ref.revision_digest, design.digest, MAPPING_REVIEWER,
            Ref(PROJECT, PROFILE, "review/" + rid, sha("review/" + rid), "fixture:review/" + rid),
            tuple(predicates if predicates is not None else (predicate(a) for a in acceptance)))
        self.profile.proofs.derive(RequirementRevision(rid, acceptance, requirement_ref), design_ref,
                                   self.profile.proofs.read(rid)[0])

    def lifecycle(self, identity: str, stage: str) -> None:
        version, _ = self.store.read_state(PROFILE, "factory:" + identity)
        self.store.commit(PROFILE, "factory:" + identity, version,
                          FactoryCoordinator._encode(ExecutionState(stage=LifecycleStage(stage))))

    def compile(self, key=DKEY, limits=None):
        return self.service.compile(key, self.vectors[key], deepcopy(LIMITS if limits is None else limits))

    def state(self) -> dict:
        """Everything outside the compiler's own upstream: records: lifecycle, release, receipts, other aggregates."""
        return {"states": [(a, v, canonical(s)) for a, v, s in self.store.list_states(PROFILE)
                           if not a.startswith(("upstream:initial-compilation:", "upstream:identity-reservations"))],
                "receipts": self.work.receipts(), "reservations": self.store.recovery_reservations(PROFILE)}


def prepared(h: Harness, sources=None, in_scope=(R1, R2), state="verified") -> dict:
    """The pinned upstream: inventory + inspection, a verified design over in_scope, and each proof plan."""
    revisions = h.requirements(sources or {r: SOURCES[r] for r in (R1, R2, R3)})
    document = h.design({r: revisions[r] for r in in_scope}, state=state)
    for rid in in_scope:
        h.plan(rid, revisions[rid], document)
    h.lifecycle(EXISTING, "DONE")
    return revisions


def inputs(h: Harness) -> dict:
    """The exact values the service pins, for domain-level controls over one changed input."""
    decision = h.profile.design_readiness.admit(DKEY, h.vectors[DKEY])
    design = h.service.designs.design(DKEY, decision.applicability.design_digest)
    return {"inventory": h.snapshot_value(), "inspection": h.profile.ambiguity.report(), "design": design,
            "review_digest": decision.applicability.review_digest,
            "plans": {r: h.service.proofs.document(r) for r in design.requirements},
            "authority_limits": deepcopy(LIMITS), "reservations": {}, "stages": {EXISTING: "DONE"}}


def assert_hold(result, code, refs=None):
    assert isinstance(result, CompilationHold), result
    assert result.reason_code == code, result.findings
    if refs is not None:
        assert result.affected_refs == tuple(refs), result.affected_refs


@pytest.fixture
def harness(tmp_path):
    count = iter(range(100))
    return lambda: Harness(tmp_path / f"h{next(count)}")


# --- Class 1: derived from pinned requirements, reviewed design and proof, with no supplied mapping ------------


def test_derives_initial_candidate_from_pinned_inputs(harness):
    h = harness()
    revisions = prepared(h)
    before = h.state()
    result = h.compile()
    assert isinstance(result, CompilationCandidate), getattr(result, "findings", result)
    document = result.document()
    assert is_initial_compilation(document) and document["provenance"] == DERIVED
    assert list(inspect.signature(h.service.compile).parameters) == ["design_key", "design_vector", "authority_limits"]
    units = {u["unit_key"]: u for u in document["units"]}
    assert {k: u["identity"] for k, u in units.items()} == {"requirement:" + R1: "WO-000005",
                                                            "requirement:" + R2: "WO-000006"}
    one, two = units["requirement:" + R1]["contract"], units["requirement:" + R2]["contract"]
    # AC-01: every SF-REQ-010 field through the existing BiuContract constructor, linked to exact revisions.
    for unit in units.values():
        payload = dict(unit["contract"])
        budget = payload.pop("budget_policy")
        contract = BiuContract(**{k: tuple(v) if isinstance(v, list) else v for k, v in payload.items()},
                               budget_policy=BudgetPolicy(**{**budget, "hard_required_dimensions": tuple(
                                   budget["hard_required_dimensions"])}))
        assert contract.content_digest == unit["content_digest"]
    design_digest = document["inputs"]["design"]["design_digest"]
    assert f"requirement:{R1}@{revisions[R1]}" in one["authority_references"]
    assert f"design:{DKEY}@{design_digest}" in one["authority_references"]
    assert one["completion_criteria"] == [f"{R1}-AC-01: every unit carries every contract field",
                                          f"{R1}-AC-02: every obligation keeps an explicit extent"]
    assert one["fixed_decisions"] == ["D-UNITS: one unit per specified requirement"]
    assert (one["intent"], one["authorized_scope"]) == ("Derive units from pinned requirements.",
                                                        ["unit derivation", "contract fields"])
    # Dependencies come from the requirement text: an in-scope unit and an existing, immutable decomposition.
    assert two["dependencies"] == ["WO-000005", EXISTING] and one["dependencies"] == []
    assert document["edges"] == [{"from": "WO-000005", "to": "WO-000006", "predicate": "DONE"},
                                 {"from": EXISTING, "to": "WO-000006", "predicate": "DONE"}]
    # AC-02: four-category coverage of compiler-derived extents, forward and reverse; never satisfaction.
    assert document["coverage"] == {"requirement": {"total": 2, "covered": 2},
                                    "acceptance": {"total": 3, "covered": 3},
                                    "verification": {"total": 3, "covered": 3},
                                    "evidence": {"total": 4, "covered": 4}}
    assert all(row["extents"] for row in document["mapping"]) and document["coverage_is_not_satisfaction"]
    assert len(document["reverse"]) == len(document["mapping"])
    assert "VALIDATION_ONLY" in document["validation"]["labels"]
    # One record and one reservation commit; nothing else written, released or projected.
    assert h.state() == before
    assert h.service.reservations() == {"requirement:" + R1: "WO-000005", "requirement:" + R2: "WO-000006"}
    version, state = h.service.read(result.input_digest)
    observation = h.service.retained(Ref(**state["result_ref"]))
    assert (version, state["status"], observation.evidence_id) == (1, "DERIVED", "compilation.derived")
    assert json.loads(observation.value) == document and h.service.completed(result.input_digest)


def test_unverified_design_holds_without_candidate(harness):
    h = harness()
    prepared(h, state="unreviewed")
    before = h.state()
    result = h.compile()
    assert_hold(result, "DESIGN_HOLD", (DKEY,))
    assert result.detail == "REVIEW_REQUIRED"
    assert h.state() == before and h.service.reservations() == {}
    assert not h.service.completed(result.candidate_digest)


def test_unresolved_authority_holds(harness):
    """AC-04: a requirement the U2 inspection holds is never compiled."""
    h = harness()
    sources = {r: SOURCES[r] for r in (R1, R2, R3)}
    sources[R1] = body(R1, Intent="Derive units from pinned requirements.", Scope="unit derivation", Authority=None,
                       Acceptance=f"{R1}-AC-01: every unit carries every contract field.")
    prepared(h, sources=sources)
    result = h.compile()
    assert_hold(result, "UNRESOLVED_AUTHORITY")
    assert result.affected_refs[0] == R1


# --- Class 2: every frozen obligation is conserved with explicit extent and reverse trace ----------------------


def test_obligation_omission_holds(harness):
    h = harness()
    prepared(h)
    values = inputs(h)
    plan = values["plans"][R1]
    plan["obligations"] = [o for o in plan["obligations"] if o["predicate"]["acceptance_id"] != f"{R1}-AC-02"]
    assert_hold(compile_initial(**values), "UNMAPPED_OBLIGATION", (f"{R1}-AC-02:verification",))


def test_obligation_invention_holds(harness):
    h = harness()
    prepared(h)
    values = inputs(h)
    other = values["plans"][R2]["obligations"][0]
    values["plans"][R1]["obligations"].append(other)
    assert_hold(compile_initial(**values), "OBLIGATION_INVENTED", (other["obligation_id"],))


def test_missing_proof_plan_holds(harness):
    h = harness()
    prepared(h)
    values = inputs(h)
    values["plans"][R2] = None
    assert_hold(compile_initial(**values), "UNMAPPED_OBLIGATION", (f"{R2}:proof_plan",))


# --- Class 3: identity, dependencies and custody/budget fields are deterministic and valid ---------------------


def permuted(values: dict) -> dict:
    """The same pinned values with every set-valued enumeration reversed (digest-bound documents unchanged)."""
    result = deepcopy(values)
    design = values["design"]
    result["design"] = replace(design, requirements=dict(reversed(list(design.requirements.items()))))
    result["plans"] = {r: {**p, "obligations": list(reversed(p["obligations"]))}
                       for r, p in reversed(list(values["plans"].items()))}
    limits = result["authority_limits"]
    limits["identity_snapshot"] = {k: list(reversed(v)) for k, v in reversed(list(limits["identity_snapshot"].items()))}
    result["authority_limits"] = dict(reversed(list(limits.items())))
    return result


def semantic(candidate: CompilationCandidate) -> tuple:
    document = candidate.document()
    return ({u["unit_key"]: u["identity"] for u in document["units"]}, document["edges"],
            {(m["obligation_id"], m["unit_key"]): [e["identity"] for e in m["extents"]] for m in document["mapping"]},
            document["coverage"])


def test_derivation_is_deterministic_under_permutation(harness):
    """AC-06: permuted enumeration yields the same candidate; permuted sources the same mapping and identities."""
    h = harness()
    prepared(h)
    values = inputs(h)
    first, second = compile_initial(**values), compile_initial(**permuted(values))
    assert isinstance(first, CompilationCandidate) and isinstance(second, CompilationCandidate)
    assert (first.candidate_digest, canonical(first.document())) == (second.candidate_digest,
                                                                      canonical(second.document()))
    # At the composed boundary: sources, predicates and design requirements enumerated in reverse.
    g = harness()
    revisions = g.requirements(dict(reversed([(r, SOURCES[r]) for r in (R1, R2, R3)])))
    document = g.design(dict(reversed([(r, revisions[r]) for r in (R1, R2)])))
    for rid in (R2, R1):
        semantic_text = next(r.semantic for r in g.snapshot_value().current if r.requirement_id == rid)
        acceptance = [c.split(":", 1)[0] for c in items(fields(semantic_text)["Acceptance"])]
        g.plan(rid, revisions[rid], document, [predicate(a) for a in reversed(acceptance)])
    g.lifecycle(EXISTING, "DONE")
    limits = deepcopy(LIMITS)
    limits["identity_snapshot"] = {k: list(reversed(v)) for k, v in limits["identity_snapshot"].items()}
    third = g.compile(limits=limits)
    assert isinstance(third, CompilationCandidate), getattr(third, "findings", third)
    assert semantic(third) == semantic(first)


def test_reservation_is_stable_and_not_sort_derived(harness):
    """A persisted reservation never moves: a later requirement that sorts first takes the next free number."""
    h = harness()
    revisions = prepared(h)
    first = h.compile()
    assert isinstance(first, CompilationCandidate)
    version = h.store.read_state(PROFILE, "upstream:identity-reservations")[0]
    again = h.compile()  # Regeneration from identical input: same candidate, nothing newly reserved.
    assert again.candidate_digest == first.candidate_digest
    assert h.store.read_state(PROFILE, "upstream:identity-reservations")[0] == version
    revisions = h.requirements({r: SOURCES[r] for r in (R0, R1, R2, R3)})
    document = h.design({r: revisions[r] for r in (R0, R1, R2)}, key="SF-DESIGN-910")
    for rid in (R0, R1, R2):
        h.plan(rid, revisions[rid], document)
    later = h.compile("SF-DESIGN-910")
    assert isinstance(later, CompilationCandidate), getattr(later, "findings", later)
    assert {u["unit_key"]: u["identity"] for u in later.document()["units"]} == {
        "requirement:" + R0: "WO-000007", "requirement:" + R1: "WO-000005", "requirement:" + R2: "WO-000006"}
    assert later.candidate_digest != first.candidate_digest  # Changed inputs: an attributable distinct revision.


def test_changed_input_is_a_distinct_revision(harness):
    h = harness()
    prepared(h)
    values = inputs(h)
    changed = deepcopy(values)
    changed["authority_limits"]["baselines"] = ["main@0000000"]
    one, two = compile_initial(**values), compile_initial(**changed)
    assert one.candidate_digest != two.candidate_digest and one.input_digest != two.input_digest
    assert one.document()["units"][0]["contract"]["version"] != two.document()["units"][0]["contract"]["version"]


@pytest.mark.parametrize("variant", ["collision", "foreign_unit", "foreign_unreserved", "foreign_new", "exhausted",
                                     "capability", "endpoint", "existing"])
def test_identity_dependency_and_bound_violations_hold(harness, variant):
    h = harness()
    prepared(h)
    values = inputs(h)
    limits = values["authority_limits"]
    if variant == "collision":
        values["reservations"] = {"requirement:" + R1: "WO-000003"}
        expected = ("IDENTITY_COLLISION", ("requirement:" + R1 + ":WO-000003",))
    elif variant == "foreign_unit":  # Reserved number later materialized for another requirement (review R1-B1).
        values["reservations"] = {"requirement:" + R1: EXISTING}
        expected = ("IDENTITY_COLLISION", ("requirement:" + R1 + ":" + EXISTING,))
    elif variant == "foreign_unreserved":  # Review R2-B1: an existing unit absent from the snapshot is still taken.
        limits["existing_decomposition"] = {R3: ["WO-000009"]}
        values["stages"], values["reservations"] = {"WO-000009": "DONE"}, {"requirement:" + R1: "WO-000009"}
        expected = ("IDENTITY_COLLISION", ("requirement:" + R1 + ":WO-000009",))
    elif variant == "foreign_new":  # Review R2-B1: a new number never lands on an existing unit's identity.
        limits["existing_decomposition"] = {R3: ["WO-000005"]}
        values["stages"] = {"WO-000005": "DONE"}
        result = compile_initial(**values)
        assert isinstance(result, CompilationCandidate), getattr(result, "findings", result)
        assert {u["identity"] for u in result.document()["units"]} == {"WO-000006", "WO-000007"}
        return
    elif variant == "exhausted":
        limits["identity_policy"] = {"family": "PY", "width": 2}
        limits["identity_snapshot"]["active"] += [f"PY-{n:02d}" for n in range(1, 100)]
        expected = ("IDENTITY_EXHAUSTED", ("requirement:" + R1 + ":PY/2", "requirement:" + R2 + ":PY/2"))
    elif variant == "capability":
        limits["required_capabilities"] = ["python"]
        expected = ("BOUNDS_WIDENED", ("WO-000005:required_capabilities:sqlite",
                                       "WO-000006:required_capabilities:sqlite"))
    elif variant == "endpoint":
        limits["existing_decomposition"] = {}
        expected = ("MISSING_ENDPOINT", (f"{R2}:{R3}",))
    else:
        limits["existing_decomposition"][R1] = ["WO-000001"]
        expected = ("EXISTING_DECOMPOSITION", (f"{R1}:WO-000001",))
    assert_hold(compile_initial(**values), *expected)


@pytest.mark.parametrize("limits_change", [
    {"identity_snapshot": {"active": ["WO-000001", 1]}}, {"existing_decomposition": {R3: [EXISTING, None]}},
    {"existing_decomposition": ["x"]}, {"existing_decomposition": {R3: [["nested"]]}}, {"budget_policy": []},
    {"budget_policy": {**LIMITS["budget_policy"], "hard_wall_clock_seconds": float("inf")}},
    {"existing_decomposition": {R3: [EXISTING], 5: ["WO-000001"]}}, {"budget_policy": {"x": {1}}},
    {"extra": float("nan")}])
def test_malformed_limits_is_a_typed_hold(harness, limits_change):
    """Review R1-B2: a malformed caller value is INVALID_CANDIDATE, retained, never an exception."""
    h = harness()
    prepared(h)
    limits = {**deepcopy(LIMITS), **limits_change}
    result = h.compile(limits=limits)
    assert_hold(result, "INVALID_CANDIDATE")
    assert h.service.read(result.candidate_digest)[1]["status"] == "HELD" and h.service.reservations() == {}


@pytest.mark.parametrize("stale", ["design", "requirement", "inspection"])
def test_unpinned_input_holds(harness, stale):
    h = harness()
    prepared(h)
    values = inputs(h)
    if stale == "design":
        values["plans"][R1]["design_ref"]["revision_digest"] = sha("another design revision")
        expected = (f"{R1}:proof_plan:design",)
    elif stale == "requirement":
        values["plans"][R1]["requirement_ref"]["revision_digest"] = sha("another requirement revision")
        expected = (f"{R1}:proof_plan:requirement",)
    else:
        values["inspection"] = replace(values["inspection"], inventory_digest="0" * 64)
        expected = None
    assert_hold(compile_initial(**values), "INPUT_UNPINNED", expected)


def test_malformed_proof_plan_is_a_typed_hold(harness):
    h = harness()
    prepared(h)
    values = inputs(h)
    values["plans"][R1] = {"digest": sha("x")}
    assert_hold(compile_initial(**values), "INVALID_CANDIDATE", (f"{R1}:proof_plan",))


def test_regeneration_keeps_one_pointer(harness):
    """Same pinned input twice: one pointer aggregate, two history entries, still completed (review note 2)."""
    h = harness()
    prepared(h)
    first, again = h.compile(), h.compile()
    assert first.input_digest == again.input_digest and first.candidate_digest == again.candidate_digest
    version, state = h.service.read(first.input_digest)
    assert (version, state["status"], len(state["history"])) == (2, "DERIVED", 2)
    assert h.service.completed(first.input_digest)


def test_hold_reserves_and_transitions_nothing(harness):
    h = harness()
    prepared(h)
    limits = deepcopy(LIMITS)
    limits["existing_decomposition"][R1] = ["WO-000001"]
    before = h.state()
    result = h.compile(limits=limits)
    assert_hold(result, "EXISTING_DECOMPOSITION")
    assert h.state() == before and h.service.reservations() == {}
    version, state = h.service.read(result.candidate_digest)
    assert (version, state["status"]) == (1, "HELD")
    assert json.loads(h.service.retained(Ref(**state["result_ref"])).value)["transition"] == "NONE"


# --- Class 4: a validator-only path over a supplied INITIAL mapping cannot satisfy completion -------------------


def test_validator_only_supplied_mapping_cannot_complete(harness):
    h = harness()
    prepared(h)
    derived = h.compile()
    document = derived.document()
    # Hand the compiler's own units to the U7 validator as a supplied mapping: it is admitted, but VALIDATION_ONLY.
    supplied = {"mode": INITIAL, "design_key": DKEY, "design_vector": h.vectors[DKEY],
                "requirements": sorted(document["inputs"]["requirements"]),
                "obligations": [{"id": o["text"], "category": o["category"]} for o in document["obligations"]],
                "units": [{"unit_key": u["unit_key"], "contract": u["contract"]} for u in document["units"]],
                "edges": document["edges"]}
    report = h.profile.compilation.validate(supplied)
    assert isinstance(report, ValidationReport), getattr(report, "findings", report)
    assert report.document()["provenance"] == "SUPPLIED_CANDIDATE_NOT_DERIVED"
    assert not is_initial_compilation(report.document())
    assert not h.service.completed(report.candidate_digest)
    assert h.service.completed(derived.input_digest)
