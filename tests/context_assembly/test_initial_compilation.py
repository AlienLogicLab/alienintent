"""FX-U8 probes: initial compilation derives the INITIAL candidate from pinned requirements, verified design and proof.

Composed over a real temporary SQLite store, local evidence, the U1 inventory, U2 inspection, U5 design gate, U4 proof
planning, the FactoryCoordinator lifecycle and the project work registry (a temporary project database, a local Git
clone with a local bare remote). No test supplies a unit or obligation mapping to the compiler. Identities come from
the work identity service: fixture requirements are registered as service-issued UUIDs. One discriminating control per
material failure class.
"""
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import inspect
import json
from pathlib import Path
import sqlite3
import subprocess

import pytest

from alienintent.composition.compilation import CoordinatorDependencyLifecycle
from alienintent.composition.design_admission import EDGE_AUTHORITY_GAP, RetainedDirectionAuthority
from alienintent.composition.premise_evidence import RetainedDoctorPremiseEvidence
from alienintent.composition.upstream_profile import UpstreamProfile
from alienintent.composition.work_registry import WorkRegistry, project_configuration
from alienintent.context_assembly.domain.ambiguity import fields, snapshot_from_document
from alienintent.context_assembly.domain.compilation import INITIAL, CompilationHold, ValidationReport, canonical
from alienintent.context_assembly.domain.design_admission import DESIGN_FIELDS, design_from_document
from alienintent.context_assembly.domain.initial_compilation import (
    DERIVED, CompilationCandidate, compile_initial, is_initial_compilation, items, packet_bytes, unit_key)
from alienintent.context_assembly.domain.inventory import Manifest, assemble
from alienintent.context_assembly.domain.work_identity import RESERVATIONS, is_uuid
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
REPO, PACKETS_BRANCH, PACKETS_DIR = "alienintent", "alienintent/work-packets", "work-packets"
# Fixed identities for domain-level calls of compile_initial, standing in for the map the service returns.
FIXED = {R0: "00000000-0000-4000-8000-000000000000", R1: "00000000-0000-4000-8000-000000000001",
         R2: "00000000-0000-4000-8000-000000000002"}

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


def git(cwd: Path, *args: str, data: bytes | None = None) -> bytes:
    return subprocess.run(["git", *args], cwd=cwd, input=data, capture_output=True, check=True).stdout


def project_clone(root: Path) -> tuple[Path, Path]:
    """A fixture project: one clone with a baseline commit on main, published to a local bare remote."""
    clone, remote = root / "clone", root / "remote.git"
    git(root, "init", "-q", "--bare", "-b", "main", str(remote))
    git(root, "init", "-q", "-b", "main", str(clone))
    (clone / "README.md").write_text("fixture project\n")
    git(clone, "add", "README.md")
    git(clone, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false",
        "commit", "-qm", "fixture baseline")
    git(clone, "remote", "add", "origin", str(remote))
    git(clone, "push", "-q", "origin", "main")
    return clone, remote


def registry_configuration(root: Path, clone: Path, profiles: dict[str, Path]):
    return project_configuration({"schema_version": 1, "projects": {PROJECT: {
        "database": str(root / "work.sqlite"),
        "repositories": {REPO: {"clone": str(clone), "remote": "origin", "default_branch": "main",
                                "packets_branch": PACKETS_BRANCH}},
        "packets": {"repository": REPO, "directory": PACKETS_DIR},
        "profiles": {name: str(path) for name, path in profiles.items()}}}}, PROJECT)


def all_rows(database: Path) -> list[dict]:
    """Every work_item row, read directly from the project database file (test inspection only)."""
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in connection.execute("SELECT * FROM work_item ORDER BY id")]
    finally:
        connection.close()


class Project:
    """One fixture project: its database, its one clone (with a local bare remote) and its configured profiles."""

    def __init__(self, root: Path, profiles: dict[str, Path]):
        root.mkdir(mode=0o700, exist_ok=True)
        self.root, self.profiles = root, profiles
        self.clone, self.remote = project_clone(root)
        self.configuration = registry_configuration(root, self.clone, profiles)
        self.database = self.configuration.database


class Harness:
    def __init__(self, root: Path, profile: str = PROFILE, project: Project | None = None, source_control=None):
        root.mkdir(mode=0o700, exist_ok=True)
        self.root, self.name = root, profile
        self.store = SQLiteOperationalStore(root / "operational.sqlite")
        self.project = project if project is not None else Project(root, {profile: root / "operational.sqlite"})
        self.clone = self.project.clone
        self.registry = WorkRegistry(self.project.configuration, source_control)
        self.repository = LocalEvidenceRepository(root / "evidence", PROJECT, self.name)
        self.work = LocalWorkManagement(root / "work", self.name, PROJECT, (), clock=lambda: 0.0)
        self.coordinator = FactoryCoordinator(self.store, self.work, None, LocalArtifactStore(root / "p", root / "v"),
                                              self.name)
        self.mappings = Mappings()
        self.definition = Ref(PROJECT, self.name, "FX-U8-contract", sha("FX-U8"), "repository:WO-220208.md")
        self.profile = UpstreamProfile(
            self.repository, self.store, PROJECT, self.name, self.definition, INVOCATION, "Founder", SCOPE,
            premise_evidence=RetainedDoctorPremiseEvidence(ROOT, Path(PREMISE_MAPPING), PREMISE_SHA256, PROJECT,
                                                           self.name),
            premise_target="AlienLogicLab/alienintent-sandbox", proof_mappings=self.mappings,
            mapping_reviewer=MAPPING_REVIEWER, supersession_authority=SUPERSESSION, design_checks=_Recorded(),
            design_authority=RetainedDirectionAuthority(ROOT, DESIGN, DESIGN_SHA256, EDGE_AUTHORITY_GAP, PROJECT,
                                                        self.name),
            design_reviewers=REVIEWERS, dependency_lifecycle=CoordinatorDependencyLifecycle(self.coordinator),
            work_registry=self.registry)
        self.service = self.profile.initial_compilation
        self.identities = self.registry.identities
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
        design_ref = Ref(PROJECT, self.name, design.design_key, design.digest, "design:" + design.design_key)
        requirement_ref = Ref(PROJECT, self.name, rid, "sha256:" + revision, "inventory:" + rid)
        self.mappings.entries[rid] = PredicateMapping(
            Ref(PROJECT, self.name, "mapping/" + rid, sha("mapping/" + rid + design.digest), "fixture:mapping/" + rid),
            rid, requirement_ref.revision_digest, design.digest, MAPPING_REVIEWER,
            Ref(PROJECT, self.name, "review/" + rid, sha("review/" + rid), "fixture:review/" + rid),
            tuple(predicates if predicates is not None else (predicate(a) for a in acceptance)))
        self.profile.proofs.derive(RequirementRevision(rid, acceptance, requirement_ref), design_ref,
                                   self.profile.proofs.read(rid)[0])

    def lifecycle(self, identity: str, stage: str) -> None:
        version, _ = self.store.read_state(self.name, "factory:" + identity)
        self.store.commit(self.name, "factory:" + identity, version,
                          FactoryCoordinator._encode(ExecutionState(stage=LifecycleStage(stage))))

    def compile(self, key=DKEY, limits=None):
        return self.service.compile(key, self.vectors[key], deepcopy(LIMITS if limits is None else limits))

    def state(self) -> dict:
        """Everything outside the compiler's own upstream: records: lifecycle, release, receipts, other aggregates
        (the retired reservation aggregate included: it is never written again)."""
        return {"states": [(a, v, canonical(s)) for a, v, s in self.store.list_states(self.name)
                           if not a.startswith("upstream:initial-compilation:")],
                "receipts": self.work.receipts(), "reservations": self.store.recovery_reservations(self.name)}

    def rows(self) -> list[dict]:
        return all_rows(self.registry.configuration.database)

    def id(self, requirement: str) -> str:
        return self.registry.items.find_request(unit_key(requirement)).id

    def packets_head(self) -> str | None:
        result = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{PACKETS_BRANCH}"],
                                cwd=self.clone, capture_output=True, text=True)
        return result.stdout.strip() or None

    def show(self, commit: str, path: str) -> bytes:
        return git(self.clone, "show", f"{commit}:{path}")

    def remote_refs(self) -> dict[str, str]:
        lines = git(self.clone, "ls-remote", "origin").decode().splitlines()
        return {name: commit for commit, name in (line.split("\t") for line in lines)}


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
            "authority_limits": deepcopy(LIMITS),
            "reservations": {unit_key(r): FIXED[r] for r in design.requirements}, "stages": {EXISTING: "DONE"}}


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
    # Identities are exactly what the work identity service registered: new UUIDs, no number derived anywhere.
    u1, u2 = h.id(R1), h.id(R2)
    assert {k: u["identity"] for k, u in units.items()} == {"requirement:" + R1: u1, "requirement:" + R2: u2}
    assert is_uuid(u1) and is_uuid(u2) and document["reservations"] == {"requirement:" + R1: u1,
                                                                         "requirement:" + R2: u2}
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
    assert two["dependencies"] == sorted([u1, EXISTING]) and one["dependencies"] == []
    assert document["edges"] == sorted([{"from": u1, "to": u2, "predicate": "DONE"},
                                        {"from": EXISTING, "to": u2, "predicate": "DONE"}],
                                       key=lambda e: (e["from"], e["to"]))
    # AC-02: four-category coverage of compiler-derived extents, forward and reverse; never satisfaction.
    assert document["coverage"] == {"requirement": {"total": 2, "covered": 2},
                                    "acceptance": {"total": 3, "covered": 3},
                                    "verification": {"total": 3, "covered": 3},
                                    "evidence": {"total": 4, "covered": 4}}
    assert all(row["extents"] for row in document["mapping"]) and document["coverage_is_not_satisfaction"]
    assert len(document["reverse"]) == len(document["mapping"])
    assert "VALIDATION_ONLY" in document["validation"]["labels"]
    # One record; the reservation aggregate is never written; nothing else written, released or projected.
    assert h.state() == before and h.store.read_state(h.name, RESERVATIONS) == (0, {})
    # Each unit's compiled packet is on the packets branch and its row points at exactly that commit.
    for unit in document["units"]:
        row = h.identities.find(unit["identity"])
        assert (row.state, row.pointer.repo, row.pointer.path) == ("CAPTURE", REPO, f"{PACKETS_DIR}/{row.id}.json")
        assert h.show(row.pointer.commit, row.pointer.path) == packet_bytes(unit)
        assert row.pointer.commit not in document["inputs"]["design"].values()
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
    assert h.state() == before and h.rows() == [] and h.packets_head() is None
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
    """The candidate's meaning with each registered identity written as its unit_key (registrations differ)."""
    document = candidate.document()
    name = {u["identity"]: u["unit_key"] for u in document["units"]}
    named = lambda i: name.get(i, i)  # noqa: E731
    return (sorted(name.values()), sorted((named(e["from"]), named(e["to"]), e["predicate"]) for e in document["edges"]),
            {(m["obligation_id"], m["unit_key"]): [named(e["identity"]) for e in m["extents"]]
             for m in document["mapping"]},
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
    """A registered identity never moves: a later requirement that sorts first is registered as a new row."""
    h = harness()
    revisions = prepared(h)
    first = h.compile()
    assert isinstance(first, CompilationCandidate)
    rows = h.rows()
    again = h.compile()  # Regeneration from identical input: same candidate, nothing newly registered.
    assert again.candidate_digest == first.candidate_digest and h.rows() == rows
    revisions = h.requirements({r: SOURCES[r] for r in (R0, R1, R2, R3)})
    document = h.design({r: revisions[r] for r in (R0, R1, R2)}, key="SF-DESIGN-910")
    for rid in (R0, R1, R2):
        h.plan(rid, revisions[rid], document)
    later = h.compile("SF-DESIGN-910")
    assert isinstance(later, CompilationCandidate), getattr(later, "findings", later)
    ids = {u["unit_key"]: u["identity"] for u in later.document()["units"]}
    assert (ids["requirement:" + R1], ids["requirement:" + R2]) == (h.id(R1), h.id(R2))
    assert is_uuid(ids["requirement:" + R0]) and len(h.rows()) == 3
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


@pytest.mark.parametrize("variant", ["unregistered", "grammar", "migrated", "capability", "endpoint", "existing"])
def test_identity_dependency_and_bound_violations_hold(harness, variant):
    h = harness()
    prepared(h)
    values = inputs(h)
    limits = values["authority_limits"]
    if variant == "unregistered":  # A key the registered map lacks is never numbered or invented.
        del values["reservations"]["requirement:" + R2]
        expected = ("IDENTITY_GRAMMAR", ("requirement:" + R2 + ":None",))
    elif variant == "grammar":  # A malformed identity in the map holds; it is never repaired.
        values["reservations"]["requirement:" + R1] = "PY-SELF-00"
        expected = ("IDENTITY_GRAMMAR", ("requirement:" + R1 + ":PY-SELF-00",))
    elif variant == "migrated":  # A migrated name of the configured family is taken exactly as registered.
        values["reservations"]["requirement:" + R1] = "WO-000005"
        result = compile_initial(**values)
        assert isinstance(result, CompilationCandidate), getattr(result, "findings", result)
        assert {u["identity"] for u in result.document()["units"]} == {"WO-000005", FIXED[R2]}
        return
    elif variant == "capability":
        limits["required_capabilities"] = ["python"]
        expected = ("BOUNDS_WIDENED", (f"{FIXED[R1]}:required_capabilities:sqlite",
                                       f"{FIXED[R2]}:required_capabilities:sqlite"))
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
    assert h.service.read(result.candidate_digest)[1]["status"] == "HELD"
    assert all(row["commit"] is None for row in h.rows()) and h.packets_head() is None


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
    # Requirements were registered before the compile (rows at CAPTURE, no pointer); no packet, nothing else.
    assert h.state() == before and all(row["commit"] is None for row in h.rows()) and h.packets_head() is None
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



# --- Class 5: the compiler obtains identities from the work identity service and points rows at Git (check 3) ----

THREE = "SF-DESIGN-910"


def prepared_three(h: Harness) -> dict:
    """A three-unit candidate (R0, R1, R2)."""
    revisions = h.requirements({r: SOURCES[r] for r in (R0, R1, R2, R3)})
    document = h.design({r: revisions[r] for r in (R0, R1, R2)}, key=THREE)
    for rid in (R0, R1, R2):
        h.plan(rid, revisions[rid], document)
    h.lifecycle(EXISTING, "DONE")
    return revisions


def changed(limits=None) -> dict:
    """Changed authority limits: every unit's contract (and so its packet bytes) changes."""
    value = deepcopy(LIMITS if limits is None else limits)
    value["baselines"] = ["main@0000000"]
    return value


def pointers(h: Harness) -> dict[str, tuple]:
    return {row["id"]: (row["repo"], row["path"], row["commit"], row["state"]) for row in h.rows()}


def branch_commits(h: Harness) -> list[str]:
    head = h.packets_head()
    return git(h.clone, "rev-list", head).decode().split() if head else []


def persisted(h: Harness, result) -> tuple[int, dict]:
    return h.service.read(getattr(result, "input_digest", None) or result.candidate_digest)


def test_every_unit_points_at_the_commit_holding_its_packet(harness):
    h = harness()
    prepared_three(h)
    result = h.compile(THREE)
    assert isinstance(result, CompilationCandidate), getattr(result, "findings", result)
    commits = branch_commits(h)
    baseline = git(h.clone, "rev-parse", "main").decode().strip()
    seen = set()
    for unit in result.document()["units"]:
        row = h.identities.find(unit["identity"])
        assert row.pointer.commit in commits and row.pointer.commit != baseline
        assert h.show(row.pointer.commit, row.pointer.path) == packet_bytes(unit)
        seen.add(row.pointer.commit)
    assert len(seen) == 3 and len(commits) == 4  # One commit per unit on top of main; not one shared head.


def test_fault_after_registration_leaves_rows_without_pointers_and_rerun_converges(harness, monkeypatch):
    from alienintent.context_assembly.application.initial_compilation_service import InitialCompilation
    h = harness()
    prepared(h)
    original = InitialCompilation._point_and_publish
    monkeypatch.setattr(InitialCompilation, "_point_and_publish", lambda self, c: (_ for _ in ()).throw(
        RuntimeError("process died before the pointer transaction")))
    with pytest.raises(RuntimeError):
        h.compile()
    rows = h.rows()
    assert len(rows) == 2 and all(r["commit"] is None for r in rows) and h.packets_head() is None
    assert [a for a, _, _ in h.store.list_states(h.name) if a.startswith("upstream:initial-compilation:")] == []
    monkeypatch.setattr(InitialCompilation, "_point_and_publish", original)
    result = h.compile()
    assert isinstance(result, CompilationCandidate) and [r["id"] for r in h.rows()] == [r["id"] for r in rows]
    assert persisted(h, result)[0] == 1


def test_fault_after_pointer_transaction_reruns_through_equal_bytes(harness, monkeypatch):
    from alienintent.context_assembly.application.initial_compilation_service import InitialCompilation
    h = harness()
    prepared(h)
    original = InitialCompilation._persist
    monkeypatch.setattr(InitialCompilation, "_persist", lambda self, r: (_ for _ in ()).throw(
        RuntimeError("process died before _persist")))
    with pytest.raises(RuntimeError):
        h.compile()
    before, commits = pointers(h), branch_commits(h)
    assert all(v[2] for v in before.values())
    monkeypatch.setattr(InitialCompilation, "_persist", original)
    result = h.compile()
    assert isinstance(result, CompilationCandidate)
    assert pointers(h) == before and branch_commits(h) == commits and persisted(h, result)[0] == 1


def test_commit_packet_never_walks_history(harness, monkeypatch):
    from alienintent.context_assembly.adapters import work_item_repository as adapter
    h = harness()
    prepared(h)
    base = git(h.clone, "rev-parse", "main").decode().strip()
    stream = b"".join(b"commit refs/heads/%s\ncommitter F <f@x.invalid> now\ndata 2\nn\n%sM 100644 inline n%d\n"
                      b"data 1\nx\n\n" % (PACKETS_BRANCH.encode(), (b"from %s\n" % base.encode()) if n == 0 else b"",
                                           n) for n in range(60))
    git(h.clone, "fast-import", "--quiet", "--date-format=now", data=stream)
    calls = []
    original = adapter.SQLiteWorkItemRepository.commit_packet
    real_run = subprocess.run

    active = []

    def counted(self, *args):
        calls.append([])
        active.append(True)
        try:
            return original(self, *args)
        finally:
            active.pop()

    def recording(argv, *rest, **options):
        if active:
            calls[-1].append(list(argv))
        return real_run(argv, *rest, **options)

    monkeypatch.setattr(adapter.SQLiteWorkItemRepository, "commit_packet", counted)
    monkeypatch.setattr(adapter.subprocess, "run", recording)
    for _ in range(2):  # A first compile writes; the second finds the row's own commit.
        assert isinstance(h.compile(), CompilationCandidate)
    assert len(calls) == 4
    for unit_calls in calls:
        assert sum(1 for c in unit_calls if c[1:3] == ["cat-file", "blob"]) <= 1
        assert not any(c[1] in ("log", "rev-list", "for-each-ref") for c in unit_calls)


def test_recompile_at_capture_moves_the_pointer_and_its_published_tag(harness):
    h = harness()
    prepared(h)
    first = h.compile()
    before = pointers(h)
    second = h.compile(limits=changed())
    assert isinstance(second, CompilationCandidate) and second.candidate_digest != first.candidate_digest
    after = pointers(h)
    remote = h.remote_refs()
    for unit in second.document()["units"]:
        identity = unit["identity"]
        assert after[identity][2] != before[identity][2] and after[identity][3] == "CAPTURE"
        assert h.show(after[identity][2], after[identity][1]) == packet_bytes(unit)
        assert remote["refs/tags/work/" + identity] == after[identity][2]
    assert remote["refs/heads/" + PACKETS_BRANCH] == h.packets_head()


def test_recompile_past_capture_holds_pointer_present_and_changes_nothing(harness):
    h = harness()
    prepared_three(h)
    h.compile(THREE)
    h.identities.set_state(h.id(R1), "SPECIFY")
    before, commits = pointers(h), branch_commits(h)
    result = h.compile(THREE, limits=changed())
    assert_hold(result, "POINTER_PRESENT", (h.id(R1),))
    assert pointers(h) == before and branch_commits(h) == commits and persisted(h, result) == (0, {})
    # The same bytes past CAPTURE pass through unchanged.
    assert isinstance(h.compile(THREE), CompilationCandidate) and pointers(h) == before


def test_state_change_waits_for_the_pointer_transaction(harness, monkeypatch):
    """A concurrent set_state lands after the compiler's single transaction: all three pointers are written."""
    import os
    import sys
    from alienintent.context_assembly.adapters import work_item_repository as adapter
    h = harness()
    prepared_three(h)
    h.compile(THREE)
    target = h.id(R1)
    code = ("import sys; from pathlib import Path; "
            "from alienintent.context_assembly.adapters.work_item_repository import SQLiteWorkItemRepository; "
            "items = SQLiteWorkItemRepository(Path(sys.argv[1]), {}); print('ready', flush=True); "
            "print(items.set_state(sys.argv[2], 'SPECIFY').state, flush=True)")
    original = adapter.SQLiteWorkItemRepository.commit_packet
    started = []

    def racing(self, *args):
        if not started:
            started.append(subprocess.Popen(
                [sys.executable, "-c", code, str(h.registry.configuration.database), target], text=True,
                stdout=subprocess.PIPE, env={**os.environ, "PYTHONPATH": str(ROOT / "src")}))
            assert started[0].stdout.readline().strip() == "ready"
            subprocess.run(["sleep", "0.5"], check=True)  # The writer is now waiting on the compiler's lock.
            assert started[0].poll() is None
        return original(self, *args)

    monkeypatch.setattr(adapter.SQLiteWorkItemRepository, "commit_packet", racing)
    before = pointers(h)
    result = h.compile(THREE, limits=changed())
    assert isinstance(result, CompilationCandidate), getattr(result, "findings", result)
    assert started[0].communicate(timeout=30)[0].strip() == "SPECIFY"
    after = pointers(h)
    assert all(after[i][2] != before[i][2] for i in before) and after[target][3] == "SPECIFY"


def test_fault_mid_transaction_keeps_commits_and_rerun_writes_all_pointers(harness, monkeypatch):
    from alienintent.context_assembly.adapters import work_item_repository as adapter
    h = harness()
    prepared_three(h)
    original = adapter.SQLiteWorkItemRepository.commit_packet
    made = []

    def dying(self, *args):
        if len(made) == 2:
            raise RuntimeError("process died after the second commit_packet")
        made.append(original(self, *args))
        return made[-1]

    monkeypatch.setattr(adapter.SQLiteWorkItemRepository, "commit_packet", dying)
    with pytest.raises(RuntimeError):
        h.compile(THREE)
    assert all(row["commit"] is None for row in h.rows()) and len(branch_commits(h)) == 3
    monkeypatch.setattr(adapter.SQLiteWorkItemRepository, "commit_packet", original)
    result = h.compile(THREE)
    assert isinstance(result, CompilationCandidate)
    commits = {v[2] for v in pointers(h).values()}
    assert len(branch_commits(h)) == 4 and len(commits & set(made)) >= 1 and all(c for c in commits)


def test_migrated_requirement_keeps_its_name_and_retired_holds(tmp_path):
    root = tmp_path / "m"
    h = Harness(root)
    py = {**deepcopy(LIMITS), "identity_policy": {"family": "PY", "width": 2}}
    h.store.commit(h.name, RESERVATIONS, 0, {"schema_version": 1, "history": [],
                                             "reservations": {"requirement:" + R1: "PY-10"}})  # TEST DATA
    h.identities.migrate({"active": [], "retired": [], "reserved": ["PY-10"]}, [h.name])
    prepared(h)
    result = h.compile(limits=py)
    assert isinstance(result, CompilationCandidate), getattr(result, "findings", result)
    assert h.id(R1) == "PY-10" and len(h.rows()) == 2
    h.identities.retire("PY-10")
    assert_hold(h.compile(limits=py), "IDENTITY_RETIRED", (f"{R1}:PY-10",))


def test_partial_migration_holds_in_every_profile_until_migrated(tmp_path):
    B = "fx-u8-b"
    (tmp_path / "a").mkdir(mode=0o700)
    (tmp_path / "b").mkdir(mode=0o700)
    SQLiteOperationalStore(tmp_path / "b" / "operational.sqlite")
    project = Project(tmp_path / "project", {PROFILE: tmp_path / "a" / "operational.sqlite",
                                             B: tmp_path / "b" / "operational.sqlite"})
    a = Harness(tmp_path / "a", PROFILE, project)
    b = Harness(tmp_path / "b", B, project)
    b.store.commit(B, RESERVATIONS, 0, {"schema_version": 1, "history": [],
                                         "reservations": {"requirement:" + R2: "PY-09"}})  # TEST DATA, profile B
    a.identities.migrate({"active": [], "retired": [], "reserved": []}, [PROFILE])  # Profile A migrated only.
    py = {**deepcopy(LIMITS), "identity_policy": {"family": "PY", "width": 2}}
    revisions = {}
    for h in (a, b):
        revisions = prepared(h)
        assert_hold(h.compile(limits=py), "MIGRATION_INCOMPLETE", (f"{R2}:{B}",))
        assert a.rows() == []
    solo = a.design({R1: revisions[R1]}, key="SF-DESIGN-SOLO")
    a.plan(R1, revisions[R1], solo)
    assert isinstance(a.compile("SF-DESIGN-SOLO", limits=py), CompilationCandidate)  # R1 is mapped by no record.
    a.plan(R1, revisions[R1], design_document({r: revisions[r] for r in (R1, R2)}))  # Back to the two-unit design.
    a.identities.migrate({"active": [], "retired": [], "reserved": []}, [PROFILE, B])
    for h in (a, b):
        result = h.compile(limits=py)
        assert isinstance(result, CompilationCandidate), getattr(result, "findings", result)
        assert h.id(R2) == "PY-09"
    assert len(a.rows()) == 2


def test_clone_write_failure_holds_clone_unavailable(harness, monkeypatch):
    from alienintent.context_assembly.adapters import work_item_repository as adapter
    h = harness()
    prepared(h)
    original = adapter.SQLiteWorkItemRepository._git

    def full(self, location, *args, **options):
        if args[0] == "fast-import":
            return subprocess.CompletedProcess(["git", *args], 128, b"", b"fatal: No space left on device")
        return original(self, location, *args, **options)

    monkeypatch.setattr(adapter.SQLiteWorkItemRepository, "_git", full)
    result = h.compile()
    assert_hold(result, "CLONE_UNAVAILABLE")
    assert str(h.clone) in result.affected_refs and "git fast-import" in result.affected_refs
    assert all(r["commit"] is None for r in h.rows()) and persisted(h, result) == (0, {})
    assert (h.clone / "README.md").exists() and h.packets_head() is None


# --- Class 6: the packets branch and work tags are published before _persist (check 10) ---------------------------


def test_compile_publishes_exactly_its_refs_before_persist(harness, monkeypatch):
    from alienintent.invocation_runtime.adapters import git_source_control as publisher
    h = harness()
    prepared(h)
    git(h.clone, "tag", "unrelated-local-tag")
    pushes = []
    real_run = subprocess.run

    def recording(argv, *rest, **options):
        if list(argv[:2]) == ["git", "push"]:
            pushes.append(list(argv))
        return real_run(argv, *rest, **options)

    monkeypatch.setattr(publisher.subprocess, "run", recording)
    result = h.compile()
    assert isinstance(result, CompilationCandidate)
    remote = h.remote_refs()
    assert remote["refs/heads/" + PACKETS_BRANCH] == h.packets_head()
    expected = {"refs/tags/work/" + i: v[2] for i, v in pointers(h).items()}
    assert {k: v for k, v in remote.items() if k.startswith("refs/tags/")} == expected
    specs = [p[-1] for p in pushes]
    assert sorted(specs) == sorted([f"{h.packets_head()}:refs/heads/{PACKETS_BRANCH}"]
                                   + [f"+{c}:{ref}" for ref, c in expected.items()])
    assert not any(a in ("--tags", "--mirror", "--all") or "*" in a for p in pushes for a in p)


def test_rejected_publication_holds_before_persist_and_rerun_publishes(harness):
    h = harness()
    prepared(h)
    hook = h.project.remote / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    result = h.compile()
    assert_hold(result, "PUBLICATION_FAILED")
    assert persisted(h, result) == (0, {}) and not h.service.completed(result.candidate_digest)
    assert "refs/heads/" + PACKETS_BRANCH not in h.remote_refs()
    hook.unlink()
    again = h.compile()
    assert isinstance(again, CompilationCandidate) and h.service.completed(again.input_digest)
    assert h.remote_refs()["refs/heads/" + PACKETS_BRANCH] == h.packets_head()
