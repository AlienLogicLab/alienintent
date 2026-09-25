"""FX-U7 probes: compiler validation of supplied INITIAL candidates and frozen SPLIT_REPLAN proposals.

Composed over a real temporary SQLite store, local evidence, the U5 design gate, U2 open questions and the
FactoryCoordinator lifecycle. Every candidate here is hand-authored or a historical replay: admission proves
validation only (VALIDATION_ONLY), never derivation, split prepare/apply or SF-REQ-013-AC-06..08.
"""
import ast
from copy import deepcopy
from dataclasses import asdict
from functools import lru_cache
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

import pytest

from alienintent.composition.compilation import CoordinatorDependencyLifecycle
from alienintent.composition.design_admission import EDGE_AUTHORITY_GAP, RetainedDirectionAuthority
from alienintent.composition.premise_evidence import RetainedDoctorPremiseEvidence
from alienintent.composition.upstream_profile import UpstreamProfile
from alienintent.context_assembly.adapters.compilation_repository import RETAINED_ASSESSMENT, EvidenceAssessmentHistory
from alienintent.context_assembly.domain.compilation import (
    HISTORICAL_EDGE_SET, INITIAL, PREDICATED, SPLIT_REPLAN, CompilationHold, ValidationReport, canonical,
    graph_revision, original_revision, payload_digest)
from alienintent.context_assembly.domain.design_admission import Stale
from alienintent.context_assembly.domain.inventory import Manifest, assemble
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.domain.records import Header, Observation
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.execution_coordination.adapters.local_work_management import LocalWorkManagement
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
from alienintent.execution_coordination.domain.lifecycle import ExecutionState, LifecycleStage
from tests.context_assembly.test_ambiguity import body, record
from tests.context_assembly.test_design_admission import (
    DESIGN, DESIGN_SHA256, KEY, PREMISE_MAPPING, PREMISE_SHA256, REVIEWERS, _Recorded, contract, review)

ROOT = Path(__file__).resolve().parents[2]
PROJECT, PROFILE = "AlienLogicLab/alienintent", "fx-u7"
INVOCATION = "AlienLogicLab/alienintent#101:PRODUCER:34c025ad-5b9a-401c-a007-a6f2c39fc780"
SCOPE = frozenset({"private"})
API = "D-API: check(design_key, vector)"

# --- family A: the SWF-33 PY-10 / PY-09B historical contract replay (read-only; pinned Git blobs) ------------
P5, P5_SHA256 = "docs/evidence/wave1-biu-split-replan-design.json", \
    "0796f8eb18c853e1c349bc93b4ed8093e56bd2681f7fd968fb518167687bd8d2"
ORIGINAL_PY10, PARENT_PY10 = "4f864b94191705953cf625fd34d203f0313b602e", "b9e246f2c905af7f3c58e3d4c1b97548ce3fc452"
CHILD_PY09B, PRIOR_PY10 = "78b5e01b9aa08bcc0c8977e73768efb62410746f", "fe1e3efe3523f4376b2de66a650dca31fecdbfad"
BLOBS = {ORIGINAL_PY10: "7caa6a3c0b2440691c65ab8e95cfd79b449787435f4db63a239066a61d671ed0",
         PARENT_PY10: "197b05fcc837afbf866bced3c2aaaf849d5d21133935d31f23747c1215b2dbfa",
         CHILD_PY09B: "cfd06a35e7eb65a7dcf9f9e8ca5175fa611666bf0cdabc9d5da6e8923c5a9428",
         PRIOR_PY10: "1fc95f25b6c2d928fcb325525b46c1850bb56463c2428f0ea56afc99f181ebb4"}
SWF33_DECISION, SWF33_DECISION_SHA256 = "docs/decisions/2026-09-21-py10-transport-split.md", \
    "71c2fce2c889551115ecbae8d3912fdde20fdb130a5eff1d2bf64abff10e27e0"
NOT_VERBATIM = ("PY-10-READINESS-PREREQUISITES", "PY-10-SCOPE-01")
WEAKENED_ROW, WEAKENED_CONJUNCT = "PY-10-AC-09", " and resumes"
LIMITS_A, POLICY_A = {"issuers": ["fixture:SWF-33-replay-issuer"]}, {"family": "PY", "width": 2}

# --- family B: synthetic BiuContract split candidates (fixture-only identities) -------------------------------
O, C1, C2, D = "WO-990100", "WO-990101", "WO-990102", "WO-990110"
P1, P2, P3 = "WO-990001", "WO-990002", "WO-990003"
LIMITS_B, POLICY_B = {"issuers": ["fixture:planning-authority"]}, {"family": "WO", "width": 6}
OPERATION = "op-fx-u7-split-1"
AC_O1 = "AC-O-1: the validator refuses every unauthorized split and names each offending edge"
AC_O2 = "AC-O-2: every frozen obligation keeps a destination in the retained integration parent"
VO_O1 = "VO-O-1: pytest over the exact candidate exercises every hold reason"
EV_O1 = "EV-O-1: an immutable observation retains each report and hold"
PRIOR_B = '{"disposition":"SPLIT","work_unit_id":"WO-990100"}'
A, B, C = "WO-990101", "WO-990102", "WO-990103"


def sha(text: str | bytes) -> str:
    return "sha256:" + sha256(text if isinstance(text, bytes) else text.encode()).hexdigest()


@lru_cache(maxsize=None)
def blob(identity: str) -> str:
    """A pinned SWF-33 blob, from the runner's extracted inputs or Git; never a working-tree path."""
    directory = os.environ.get("FX_U7_FIXTURE_INPUTS")
    data = (Path(directory) / identity).read_bytes() if directory else subprocess.check_output(
        ["git", "cat-file", "blob", identity], cwd=ROOT)
    assert sha256(data).hexdigest() == BLOBS[identity], f"SWF-33 input digest mismatch: {identity}"
    return data.decode()


@lru_cache(maxsize=None)
def phase5() -> dict:
    data = (ROOT / P5).read_bytes()
    assert sha256(data).hexdigest() == P5_SHA256, "P5 digest mismatch"
    return json.loads(data)


def edge(source, target, predicate="DONE") -> dict:
    return {"from": source, "to": target, "predicate": predicate}


def unit_contract(identity, dependencies=(), **fields) -> dict:
    document = {
        "identity": identity, "version": "1", "intent": f"Deliver the {identity} validation extent",
        "satisfied_requirement_ids": [KEY], "fixed_decisions": [API], "authorized_scope": ["context_assembly"],
        "excluded_scope": ["adapters"], "dependencies": list(dependencies), "required_capabilities": ["python"],
        "budget_policy": {"hard_required_dimensions": ["attempts"], "maximum_attempts": 3,
                          "hard_wall_clock_seconds": 7200, "retry_limit": 1, "concurrency_limit": 1},
        "retry_policy": "one replacement per phase", "completion_criteria": ["tests pass"],
        "verification_obligations": ["unit tests"], "required_evidence": ["test output"],
        "non_goals": ["live operation"], "candidate_custody_requirements": ["publish the exact candidate SHA"],
        "release_policy": "explicit-human-off", "authority_issuer": "Founder", "authority_references": ["SWF-19"],
        "target_repositories": [PROJECT], "baselines": ["main@7b6e19c4"], "required_closure_actions": ["land or park"],
        "stop_escalation_conditions": ["authority gap"]}
    document.update(fields)
    return document


class Harness:
    """One disposable profile: store, evidence, work-management receipts, coordinator lifecycle, composed profile."""

    def __init__(self, root: Path):
        root.mkdir(mode=0o700)
        self.store = SQLiteOperationalStore(root / "operational.sqlite")
        self.repository = LocalEvidenceRepository(root / "evidence", PROJECT, PROFILE)
        self.work = LocalWorkManagement(root / "work", PROFILE, PROJECT, (), clock=lambda: 0.0)
        coordinator = FactoryCoordinator(self.store, self.work, None, LocalArtifactStore(root / "p", root / "v"),
                                         PROFILE)
        self.definition = Ref(PROJECT, PROFILE, "FX-U7-contract", sha("FX-U7"), "repository:WO-220207.md")
        self.profile = UpstreamProfile(
            self.repository, self.store, PROJECT, PROFILE, self.definition, INVOCATION, "Founder", SCOPE,
            premise_evidence=RetainedDoctorPremiseEvidence(ROOT, Path(PREMISE_MAPPING), PREMISE_SHA256, PROJECT,
                                                           PROFILE),
            premise_target="AlienLogicLab/alienintent-sandbox", design_checks=_Recorded(),
            design_authority=RetainedDirectionAuthority(ROOT, DESIGN, DESIGN_SHA256, EDGE_AUTHORITY_GAP, PROJECT,
                                                        PROFILE),
            design_reviewers=REVIEWERS, dependency_lifecycle=CoordinatorDependencyLifecycle(coordinator))
        self.service = self.profile.compilation
        self.history = EvidenceAssessmentHistory(self.repository, SCOPE)
        self.priors: list[dict] = []

    def design(self, state="verified") -> dict:
        """The U5 design aggregate in one of four states; the returned vector is what the candidate carries."""
        if state == "absent":
            return {"design": sha("absent"), "requirements": {KEY: sha("absent")}}
        report = self.profile.design.inspect(contract(), 0)
        if state == "unreviewed":
            return report.vector
        self.profile.design.record_review(KEY, review(report), 1)
        if state == "stale":
            moved = {**deepcopy(report.vector), "requirements": {KEY: "sha256:" + "b" * 64}}
            assert isinstance(self.profile.design.check(KEY, moved), Stale)  # Invalidated before any snapshot.
        return report.vector

    def lifecycle(self, identity: str, stage: str) -> None:
        version, _ = self.store.read_state(PROFILE, "factory:" + identity)
        self.store.commit(PROFILE, "factory:" + identity, version,
                          FactoryCoordinator._encode(ExecutionState(stage=LifecycleStage(stage))))

    def open_question(self, requirement: str) -> str:
        records = (record(requirement, requirement + ".md", body(requirement, Intent=None)),)
        version, _ = self.profile.inventory.read()
        self.profile.inventory.publish(Manifest(PROJECT, tuple(r.spec for r in records), "fx-u7"),
                                       assemble(PROJECT, records, None), version)
        report = self.profile.ambiguity.inspect(self.profile.ambiguity.read()[0])
        return next(f.finding_id for f in report.findings if f.requirement_id == requirement)

    def retain_assessment(self, text: str) -> dict:
        value_digest = sha256(text.encode()).hexdigest()
        ref = self.repository.put(Observation(
            Header(PROJECT, PROFILE, "prior-assessment/" + value_digest, value_digest, (self.definition,)),
            self.definition, RETAINED_ASSESSMENT, "retained-readiness-assessment/v1", (), text, None, "fixture",
            INVOCATION))
        self.priors.append(asdict(ref))
        return asdict(ref)

    def snapshot(self) -> dict:
        """Everything a hold must leave unchanged: all non-compilation aggregates, lifecycle, release, receipts,
        reservations and the prior-assessment digests."""
        return {"states": [(a, v, canonical(s)) for a, v, s in self.store.list_states(PROFILE)
                           if not a.startswith("upstream:compilation:")],
                "factory": [(a, v, canonical(s)) for a, v, s in self.store.list_states(PROFILE, "factory:")],
                "release": [(a, v, canonical(s)) for a, v, s in self.store.list_states(PROFILE, "release:")],
                "receipts": self.work.receipts(), "reservations": self.store.recovery_reservations(PROFILE),
                "priors": [self.history.digest(r) for r in self.priors]}


# --- candidate builders -----------------------------------------------------------------------------------


def initial(vector: dict) -> dict:
    a = unit_contract(A, [P1], completion_criteria=["tests pass", f"{KEY}-AC-01"],
                      verification_obligations=["unit tests", "VO-900-01"])
    b = unit_contract(B, [A], completion_criteria=["tests pass", f"{KEY}-AC-02"],
                      required_evidence=["test output", "EV-900-01"])
    c = unit_contract(C, [B], satisfied_requirement_ids=[KEY, "SF-REQ-903"])
    return {"mode": INITIAL, "design_key": KEY, "design_vector": vector, "requirements": [KEY],
            "obligations": [{"id": KEY, "category": "requirement"}, {"id": "SF-REQ-903", "category": "requirement"},
                            {"id": f"{KEY}-AC-01", "category": "acceptance"},
                            {"id": f"{KEY}-AC-02", "category": "acceptance"},
                            {"id": "VO-900-01", "category": "verification"},
                            {"id": "EV-900-01", "category": "evidence"}],
            "units": [{"unit_key": "u-" + x["identity"], "contract": x} for x in (a, b, c)],
            "edges": [edge(P1, A), edge(A, B), edge(B, C)],
            "projection": {P1: "OPEN", P2: "CLOSED"}}


def unit(document: dict, identity: str) -> dict:
    for entry in document.get("units", []):
        if entry["contract"]["identity"] == identity:
            return entry["contract"]
    return next(r for r in document["results"] if r["identity"] == identity).get("contract")


def original_b() -> dict:
    return {"identity": O, "contract": unit_contract(
        O, [P1, P2], intent="Deliver compiler validation", completion_criteria=[AC_O1, AC_O2],
        verification_obligations=[VO_O1], required_evidence=[EV_O1], required_capabilities=["python", "sqlite"],
        authorized_scope=["context_assembly", "composition"])}


def split_b(vector: dict, prior: dict, prior_digest: str) -> tuple[dict, dict]:
    original = original_b()
    parent = deepcopy(original["contract"])
    parent["dependencies"] = [P1, P2, C1, C2]
    child = {"budget_policy": {"hard_required_dimensions": ["attempts"], "maximum_attempts": 2,
                               "hard_wall_clock_seconds": 3600, "retry_limit": 1, "concurrency_limit": 1},
             "verification_obligations": [VO_O1], "required_evidence": [EV_O1]}
    obligations = [{"id": KEY, "kind": "requirement", "text": KEY},
                   {"id": "AC-O-1", "kind": "acceptance", "text": AC_O1},
                   {"id": "AC-O-2", "kind": "acceptance", "text": AC_O2},
                   {"id": "VO-O-1", "kind": "verification", "text": VO_O1},
                   {"id": "EV-O-1", "kind": "evidence", "text": EV_O1}]
    mapping = [{"obligation_id": KEY, "maps_to": [O, C1, C2]}, {"obligation_id": "AC-O-1", "maps_to": [O, C1]},
               {"obligation_id": "AC-O-2", "maps_to": [O, C2]}, {"obligation_id": "VO-O-1", "maps_to": [O, C1, C2]},
               {"obligation_id": "EV-O-1", "maps_to": [O, C1, C2]}]
    proposal = {
        "mode": SPLIT_REPLAN, "design_key": KEY, "design_vector": vector, "requirements": [KEY],
        "operation_id": OPERATION, "graph_semantics": PREDICATED, "integration_parent": O,
        "original_edges": [edge(P1, O), edge(P2, O), edge(O, D)],
        "original_obligations": obligations,
        "results": [
            {"identity": O, "role": "INTEGRATION_PARENT", "children": [C1, C2], "contract": parent},
            {"identity": C1, "role": "CHILD", "split_from": O, "operation_id": OPERATION,
             "contract": unit_contract(C1, [P1, P2], completion_criteria=[AC_O1], **deepcopy(child))},
            {"identity": C2, "role": "CHILD", "split_from": O, "operation_id": OPERATION,
             "contract": unit_contract(C2, [P1, P2], completion_criteria=[AC_O2], **deepcopy(child))}],
        "result_edges": [edge(P1, O), edge(P2, O), edge(O, D), edge(P1, C1), edge(P2, C1), edge(P1, C2),
                         edge(P2, C2), edge(C1, O), edge(C2, O)],
        "authorized_edges": [], "destination_bindings": {}, "mapping": mapping,
        "reverse": [{"destination": d, "obligation_id": m["obligation_id"], "origin": m["obligation_id"]}
                    for m in mapping for d in m["maps_to"]],
        "identity_snapshot": {"active": [P1, P2, O, D], "retired": ["WO-990098"], "reserved": ["WO-990099"]},
        "invalidation": [C1, C2, O],
        "prior_assessments": [{"unit": O, "ref": prior, "digest": prior_digest, "disposition": "SPLIT",
                               "applicability": "INAPPLICABLE"}],
        "elaboration_approvals": []}
    return proposal, original


def split_a(vector: dict, prior: dict, bound: bool) -> tuple[dict, dict]:
    design = phase5()
    rows, graph = design["conservation_mapping"], design["reference_graph"]
    bindings = {k: v["biu"] for k, v in design["destination_bindings"].items()}
    original = {"identity": "PY-10", "body": blob(ORIGINAL_PY10)}
    proposal = {
        "mode": SPLIT_REPLAN, "design_key": KEY, "design_vector": vector, "requirements": [KEY],
        "operation_id": "SWF-33", "graph_semantics": HISTORICAL_EDGE_SET, "integration_parent": "PY-10",
        "original_edges": [edge(s, t, None) for s, t in graph["preserved_edges"]],
        "original_obligations": [{"id": r["obligation_id"], "kind": r["kind"], "text": r["obligation_text"]}
                                 for r in rows],
        "results": [{"identity": "PY-10", "role": "INTEGRATION_PARENT", "children": ["PY-09B"],
                     "body": blob(PARENT_PY10)},
                    {"identity": "PY-09B", "role": "CHILD", "split_from": "PY-10", "operation_id": "SWF-33",
                     "body": blob(CHILD_PY09B)}],
        "result_edges": [edge(s, t, None) for s, t in graph["preserved_edges"] + graph["added_edges"]],
        "authorized_edges": [], "destination_bindings": bindings,
        "mapping": [{"obligation_id": r["obligation_id"], "maps_to": list(r["maps_to"])} for r in rows],
        "reverse": [{"destination": d, "obligation_id": r["obligation_id"], "origin": r["obligation_id"]}
                    for r in rows for d in r["maps_to"]],
        "identity_snapshot": {"active": list(graph["original_predecessors"]) + ["PY-10"], "retired": [],
                              "reserved": []},
        "invalidation": ["PY-09B", "PY-10"],
        "prior_assessments": [{"unit": "PY-10", "ref": prior, "digest": "sha256:" + BLOBS[PRIOR_PY10],
                               "disposition": "SPLIT_RECOMMENDED", "applicability": "INAPPLICABLE"}],
        "elaboration_approvals": [{"obligation_id": row, "decision_ref": SWF33_DECISION,
                                   "decision_digest": "sha256:" + SWF33_DECISION_SHA256}
                                  for row in NOT_VERBATIM] if bound else []}
    return proposal, original


def authority(proposal: dict, original: dict, issuer: str) -> dict:
    """The fixture's synthetic issuer binds the exact payload and frozen revisions (N-5); it proves binding only."""
    return {"issuer": issuer, "operation_id": proposal["operation_id"], "payload_digest": payload_digest(proposal),
            "original_revision": original_revision(original),
            "graph_revision": graph_revision(proposal["original_edges"]),
            "expected_versions": {original["identity"]: 0}}


def rename(proposal: dict, old: str, new: str) -> dict:
    return json.loads(json.dumps(proposal).replace(json.dumps(old), json.dumps(new)))


# --- scenarios: (setup(h) -> run(), expected reason, expected refs) ----------------------------------------


def permuted(document: dict) -> dict:
    """The same candidate with every top-level enumeration reversed."""
    return {k: list(reversed(v)) if isinstance(v, list) else v for k, v in document.items()}


def run_initial(change=None, design="verified", stages=((P1, "DONE"), (P2, "IMPLEMENT")), question=None):
    def setup(h: Harness, permute=False):
        candidate = initial(h.design(design))
        for identity, stage in stages:
            h.lifecycle(identity, stage)
        if question:
            h.open_question(question)
        if change:
            change(candidate)
        candidate = permuted(candidate) if permute else candidate
        return lambda: h.service.validate(candidate)
    return setup


def run_split_b(change=None, after=None, design="verified", issuer="fixture:planning-authority", prior=None,
                stages=((P1, "DONE"), (P2, "DONE")), authorize=True):
    def setup(h: Harness, permute=False):
        for identity, stage in stages:
            h.lifecycle(identity, stage)
        ref = h.retain_assessment(prior or PRIOR_B)
        proposal, original = split_b(h.design(design), ref, sha(PRIOR_B))
        if change:
            proposal = change(proposal) or proposal
        if authorize:
            proposal["authority"] = authority(proposal, original, issuer)
        if after:
            after(proposal, original)
        proposal = permuted(proposal) if permute else proposal
        return lambda: h.service.validate_split(proposal, original, LIMITS_B, POLICY_B)
    return setup


def run_split_a(change=None, bound=True, prior=None, design="verified"):
    def setup(h: Harness):
        for identity in phase5()["reference_graph"]["original_predecessors"]:
            h.lifecycle(identity, "DONE")
        ref = h.retain_assessment(prior or blob(PRIOR_PY10))
        proposal, original = split_a(h.design(design), ref, bound)
        if change:
            change(proposal)
        proposal["authority"] = authority(proposal, original, LIMITS_A["issuers"][0])
        return lambda: h.service.validate_split(proposal, original, LIMITS_A, POLICY_A)
    return setup


def _set(path_fn, value):
    def change(document):
        target, key = path_fn(document)
        target[key] = value
    return change


def add_edge(e, dependent=None, dependency=None):
    def change(document):
        document["result_edges" if "result_edges" in document else "edges"].append(e)
        if dependent:
            unit(document, dependent)["dependencies"].append(dependency)
    return change


def drop_edge(source, target, dependent_drop=True):
    def change(document):
        name = "result_edges" if "result_edges" in document else "edges"
        document[name] = [e for e in document[name] if (e["from"], e["to"]) != (source, target)]
        contract_ = unit(document, target) if dependent_drop else None
        if contract_:
            contract_["dependencies"].remove(source)
    return change


def both(*changes):
    def change(document):
        for c in changes:
            document = c(document) or document
        return document
    return change


def weaken_parent_a(proposal):
    parent = proposal["results"][0]
    text = next(o["text"] for o in proposal["original_obligations"] if o["id"] == WEAKENED_ROW)
    assert parent["body"].count(text) == 1 and text.find(WEAKENED_CONJUNCT) > 20
    parent["body"] = parent["body"].replace(text, text.replace(WEAKENED_CONJUNCT, ""))


def weaken_parent_b(proposal):
    criteria = unit(proposal, O)["completion_criteria"]
    criteria[criteria.index(AC_O1)] = AC_O1.replace(" and names each offending edge", "")


def remap(row, maps_to):
    def change(proposal):
        next(m for m in proposal["mapping"] if m["obligation_id"] == row)["maps_to"] = maps_to
    return change


def drop_row(row):
    def change(proposal):
        proposal["mapping"] = [m for m in proposal["mapping"] if m["obligation_id"] != row]
    return change


def invent(destination, row):
    def change(proposal):
        proposal["reverse"].append({"destination": destination, "obligation_id": row, "origin": row})
    return change


def rename_parent(proposal):
    renamed = rename(proposal, O, "WO-990120")
    renamed["original_edges"] = proposal["original_edges"]
    return renamed


def child_budget(**changes):
    def change(proposal):
        unit(proposal, C1)["budget_policy"].update(changes)
    return change


def stale_original(proposal, original):
    older = deepcopy(original)
    older["contract"]["version"] = "0"
    proposal["authority"]["original_revision"] = original_revision(older)


def child_field(field, value):
    def change(proposal):
        unit(proposal, C1)[field] = value
    return change


def set_result(identity, key, value):
    def change(proposal):
        result = next(r for r in proposal["results"] if r["identity"] == identity)
        if value is None:
            result.pop(key, None)
        else:
            result[key] = value
    return change


def suffixed_child(proposal):
    """A suffixed child with no split_from: ancestry must not be inferred from the trailing A."""
    renamed = rename(proposal, C2, "WO-990100A")
    set_result("WO-990100A", "split_from", None)(renamed)
    return renamed


def omit_original_prerequisite(proposal):
    """P2 removed consistently from the proposal's own original graph, results and contracts."""
    for name in ("original_edges", "result_edges"):
        proposal[name] = [e for e in proposal[name] if e["from"] != P2]
    for result in proposal["results"]:
        result["contract"]["dependencies"].remove(P2)


def omit_original_obligation(proposal):
    """EV-O-1 removed consistently from the frozen inventory, mapping and reverse mapping."""
    proposal["original_obligations"] = [o for o in proposal["original_obligations"] if o["id"] != "EV-O-1"]
    proposal["mapping"] = [m for m in proposal["mapping"] if m["obligation_id"] != "EV-O-1"]
    proposal["reverse"] = [r for r in proposal["reverse"] if r["obligation_id"] != "EV-O-1"]


def truncate_frozen_clause(proposal):
    """The frozen clause is a truncation of the original's, and the parent is weakened to match."""
    short = AC_O1.replace(" and names each offending edge", "")
    next(o for o in proposal["original_obligations"] if o["id"] == "AC-O-1")["text"] = short
    weaken_parent_b(proposal)


def child_contract_as_body(proposal):
    """C2 carries its clauses as an unvalidated body instead of a BiuContract (review R2, B1)."""
    result = next(r for r in proposal["results"] if r["identity"] == C2)
    del result["contract"]
    result["body"] = "\n".join((AC_O2, KEY, VO_O1, EV_O1))


def child_contract_absent(proposal):
    """C2 carries no contract at all and is removed from the mapping (review R2, B1)."""
    del next(r for r in proposal["results"] if r["identity"] == C2)["contract"]
    for m in proposal["mapping"]:
        m["maps_to"] = [d for d in m["maps_to"] if d != C2]
    proposal["reverse"] = [r for r in proposal["reverse"] if r["destination"] != C2]


def absent_operation_id(proposal):
    proposal["operation_id"] = ""
    for result in proposal["results"]:
        if result["role"] == "CHILD":
            result["operation_id"] = ""


def invalidation(units):
    def change(proposal):
        proposal["invalidation"] = list(units)
    return change


def authorize_downstream(proposal):
    proposal["authorized_edges"].append(edge(C1, D))
    proposal["result_edges"].append(edge(C1, D))


def prior_current(proposal):
    proposal["prior_assessments"][0].update(disposition="READY", applicability="CURRENT")


BUDGET = {"maximum_attempts": 4, "hard_wall_clock_seconds": 9000, "retry_limit": 2, "concurrency_limit": 2}
C2_OWN = unit_contract(C2)["intent"]
SCENARIOS = {
    # P02 / P03: graph refusal names the offending edge.
    "initial:cycle": (run_initial(add_edge(edge(C, A), A, C)), "CYCLE", (f"{A}->{B}", f"{B}->{C}", f"{C}->{A}")),
    "initial:missing_endpoint": (run_initial(add_edge(edge(C, "WO-990199"))), "MISSING_ENDPOINT",
                                 (f"{C}->WO-990199",)),
    "initial:no_predicate": (run_initial(lambda d: d["edges"][1].update(predicate="")), "UNSPECIFIED_PREDICATE",
                             (f"{A}->{B}",)),
    "split:cycle": (run_split_b(add_edge(edge(O, C1), C1, O)), "CYCLE", (f"{O}->{C1}", f"{C1}->{O}")),
    "split:missing_endpoint": (run_split_b(add_edge(edge(C1, "WO-990199"))), "MISSING_ENDPOINT",
                               (f"{C1}->WO-990199",)),
    "split:no_predicate": (run_split_b(lambda p: next(e for e in p["result_edges"] if (e["from"], e["to"]) == (C2, O))
                                       .update(predicate="")), "UNSPECIFIED_PREDICATE", (f"{C2}->{O}",)),
    # P04 / P05
    "initial:incomplete_contract": (run_initial(lambda d: unit(d, B).pop("required_evidence")),
                                    "INCOMPLETE_CONTRACT", (f"{B}:required_evidence",)),
    "initial:uncovered_requirement": (run_initial(lambda d: unit(d, C)["satisfied_requirement_ids"].remove(
        "SF-REQ-903")), "UNMAPPED_OBLIGATION", ("SF-REQ-903",)),
    "initial:uncovered_acceptance": (run_initial(lambda d: unit(d, B)["completion_criteria"].remove(
        f"{KEY}-AC-02")), "UNMAPPED_OBLIGATION", (f"{KEY}-AC-02",)),
    "initial:uncovered_verification": (run_initial(lambda d: unit(d, A)["verification_obligations"].remove(
        "VO-900-01")), "UNMAPPED_OBLIGATION", ("VO-900-01",)),
    "initial:uncovered_evidence": (run_initial(lambda d: unit(d, B)["required_evidence"].remove("EV-900-01")),
                                   "UNMAPPED_OBLIGATION", ("EV-900-01",)),
    # P06 (both modes): the U5 reason code is carried verbatim.
    "initial:design_stale": (run_initial(design="stale"), "DESIGN_HOLD", (KEY,)),
    "initial:design_unreviewed": (run_initial(design="unreviewed"), "DESIGN_HOLD", (KEY,)),
    "initial:design_absent": (run_initial(design="absent"), "DESIGN_HOLD", (KEY,)),
    "split:design_stale": (run_split_b(design="stale"), "DESIGN_HOLD", (KEY,)),
    "split:design_unreviewed": (run_split_b(design="unreviewed"), "DESIGN_HOLD", (KEY,)),
    "split:design_absent": (run_split_b(design="absent"), "DESIGN_HOLD", (KEY,)),
    # P07 / P08
    "initial:unresolved_authority": (run_initial(lambda d: d["requirements"].append("SF-REQ-901"),
                                                 question="SF-REQ-901"), "UNRESOLVED_AUTHORITY", None),
    "initial:decision_conflict": (run_initial(lambda d: unit(d, B).update(
        fixed_decisions=["D-API: check(design_key)", "D-NEW: invented decision"])), "DECISION_CONFLICT",
        (f"{B}:D-API: check(design_key) <> design:D-API: check(design_key, vector)",
         f"{B}:D-NEW: invented decision <> design:ABSENT")),
    # P11 / P12 (013-dependency-authority)
    "initial:closed_nonterminal_predecessor": (run_initial(both(add_edge(edge(P2, A), A, P2))),
                                               "DEPENDENCY_UNSATISFIED", (P2,)),
    "initial:declared_edge_disagreement": (run_initial(lambda d: unit(d, A)["dependencies"].append(P3)),
                                           "EDGE_DISAGREEMENT", (f"{A}:{P3}",)),
    # P13 [unbound] and P14 family A
    "swf33:unbound": (run_split_a(bound=False), "CLAUSE_NOT_VERBATIM", NOT_VERBATIM),
    "swf33:omission": (run_split_a(drop_row("SF-REQ-001")), "OBLIGATION_LOST", ("SF-REQ-001",)),
    "swf33:weakened_clause": (run_split_a(weaken_parent_a), "CLAUSE_NOT_VERBATIM", (WEAKENED_ROW,)),
    "swf33:invented_obligation": (run_split_a(invent("retained_integration_parent", "PY-10-INVENTED-01")),
                                  "OBLIGATION_INVENTED", ("PY-10-INVENTED-01",)),
    "swf33:partial_mapping": (run_split_a(remap("SF-REQ-001", ["retained_integration_parent", "child_b"])),
                              "PARTIAL_MAPPING", ("SF-REQ-001",)),
    "swf33:integration_duty_dropped": (run_split_a(remap("SF-REQ-005", ["child_a"])), "INTEGRATION_DUTY_DROPPED",
                                       ("SF-REQ-005",)),
    "swf33:history_bytes_altered": (run_split_a(prior=blob(PRIOR_PY10) + " "), "ASSESSMENT_HISTORY_MUTATED",
                                    None),
    # P14 family B analogues
    "split:omission": (run_split_b(drop_row("EV-O-1")), "OBLIGATION_LOST", ("EV-O-1",)),
    "split:weakened_clause": (run_split_b(weaken_parent_b), "CLAUSE_NOT_VERBATIM", ("AC-O-1",)),
    "split:invented_obligation": (run_split_b(invent(C1, "AC-C1-9")), "OBLIGATION_INVENTED", ("AC-C1-9",)),
    "split:partial_mapping": (run_split_b(remap("AC-O-1", [O, C1, "UNKNOWN"])), "PARTIAL_MAPPING", ("AC-O-1",)),
    "split:integration_duty_dropped": (run_split_b(remap("AC-O-1", [C1])), "INTEGRATION_DUTY_DROPPED",
                                       ("AC-O-1",)),
    # P15
    "split:bounds_capability": (run_split_b(child_field("required_capabilities", ["python", "network"])),
                                "BOUNDS_WIDENED", (f"{C1}:required_capabilities:['python', 'sqlite']->['network']",)),
    "split:bounds_budget_dimension": (run_split_b(child_budget(**BUDGET)), "BOUNDS_WIDENED",
                                      tuple(sorted(f"{C1}:budget_policy.{k}:{v}->{BUDGET[k]}" for k, v in
                                                   (("maximum_attempts", 3), ("hard_wall_clock_seconds", 7200),
                                                    ("retry_limit", 1), ("concurrency_limit", 1))))),
    "split:bounds_repository_scope": (run_split_b(child_field("target_repositories",
                                                              [PROJECT, "AlienLogicLab/alienintent-sandbox"])),
                                      "BOUNDS_WIDENED",
                                      (f"{C1}:target_repositories:['{PROJECT}']->['AlienLogicLab/alienintent-sandbox']",)),
    # P16
    "split:authority_absent": (run_split_b(authorize=False), "SPLIT_UNAUTHORIZED", ("issuer:None",)),
    "split:payload_digest_mismatch": (run_split_b(after=lambda p, o: unit(p, C1).update(intent="changed payload")),
                                      "SPLIT_AUTHORITY_STALE", None),
    "split:stale_original_revision": (run_split_b(after=stale_original), "SPLIT_AUTHORITY_STALE", None),
    "split:issuer_outside_limits": (run_split_b(issuer="fixture:unlisted-issuer"), "SPLIT_UNAUTHORIZED",
                                    ("issuer:fixture:unlisted-issuer",)),
    # P17
    "split:done_original": (run_split_b(stages=((P1, "DONE"), (P2, "DONE"), (O, "DONE"))), "DONE_ORIGINAL", (O,)),
    # P19
    "split:weakened_predicate": (run_split_b(lambda p: next(e for e in p["result_edges"] if (e["from"], e["to"]) ==
                                                            (P1, C1)).update(predicate="STARTED")),
                                 "PREDICATE_WEAKENED", (f"{P1}->{C1}",)),
    "split:prerequisite_not_copied": (run_split_b(drop_edge(P2, C2)), "PREREQUISITE_NOT_COPIED", (f"{P2}->{C2}",)),
    "split:downstream_redirected": (run_split_b(both(drop_edge(O, D, False), add_edge(edge(C1, D)))),
                                    "EDGE_REDIRECTED", (f"{O}->{D}",)),
    "split:edge_pruned": (run_split_b(drop_edge(P2, O)), "EDGE_PRUNED", (f"{P2}->{O}",)),
    "split:unauthorized_inter_child_edge": (run_split_b(add_edge(edge(C1, C2), C2, C1)),
                                            "INTER_CHILD_EDGE_UNAUTHORIZED", (f"{C1}->{C2}",)),
    "split:missing_child_parent_done_edge": (run_split_b(drop_edge(C2, O)), "CHILD_PARENT_EDGE_MISSING",
                                             (f"{C2}->{O}",)),
    # P20
    "split:grammar_short": (run_split_b(lambda p: rename(p, C2, "WO-99010")), "IDENTITY_GRAMMAR", ("WO-99010",)),
    "split:grammar_suffix": (run_split_b(lambda p: rename(p, C2, "WO-990101AA")), "IDENTITY_GRAMMAR",
                             ("WO-990101AA",)),
    "split:collision_active": (run_split_b(lambda p: both(lambda q: rename(q, C2, "WO-990103"), lambda q: q[
        "identity_snapshot"]["active"].append("WO-990103"))(p)), "IDENTITY_COLLISION", ("WO-990103:active",)),
    "split:collision_retired": (run_split_b(lambda p: rename(p, C2, "WO-990098")), "IDENTITY_COLLISION",
                                ("WO-990098:retired",)),
    "split:collision_reserved": (run_split_b(lambda p: rename(p, C2, "WO-990099")), "IDENTITY_COLLISION",
                                 ("WO-990099:reserved",)),
    "split:existing_identity_rewritten": (run_split_b(rename_parent), "IDENTITY_REWRITTEN", (O,)),
    # P21
    "split:missing_split_from": (run_split_b(set_result(C2, "split_from", None)), "LINEAGE_MISSING", (C2,)),
    "split:suffix_only_lineage": (run_split_b(suffixed_child), "LINEAGE_MISSING", ("WO-990100A",)),
    "split:operation_id_mismatch": (run_split_b(set_result(C2, "operation_id", "op-other")),
                                    "LINEAGE_INCONSISTENT", (C2,)),
    "split:parent_missing_child": (run_split_b(set_result(O, "children", [C1])), "LINEAGE_INCONSISTENT", (C2,)),
    # P22
    "split:invalidation_missing_parent": (run_split_b(invalidation([C1, C2])), "INVALIDATION_INCOMPLETE", (O,)),
    "split:invalidation_missing_changed_dependent": (run_split_b(authorize_downstream), "INVALIDATION_INCOMPLETE",
                                                     (D,)),
    "split:history_bytes_altered": (run_split_b(prior=PRIOR_B.replace("SPLIT", "READY")),
                                    "ASSESSMENT_HISTORY_MUTATED", None),
    "split:stale_ready_as_current": (run_split_b(prior_current), "STALE_ASSESSMENT_AS_CURRENT", (O,)),
    # Review R1 repairs (independent pre-candidate review): each was admitted before its repair.
    "split:duplicate_edge": (run_split_b(add_edge(edge(P1, C1, "STARTED"))), "INVALID_CANDIDATE", None),
    "initial:unresolved_authority_via_contract": (run_initial(
        lambda d: d.update(obligations=[o for o in d["obligations"] if o["id"] != "SF-REQ-903"]),
        question="SF-REQ-903"), "UNRESOLVED_AUTHORITY", None),
    "split:original_graph_omitted": (run_split_b(omit_original_prerequisite), "ORIGINAL_GRAPH_MISMATCH",
                                     (f"{O}:{P2}",)),
    "split:original_obligation_omitted": (run_split_b(omit_original_obligation), "OBLIGATION_LOST",
                                          (f"{O}:{EV_O1}",)),
    "split:frozen_clause_truncated": (run_split_b(truncate_frozen_clause), "OBLIGATION_LOST", (f"{O}:{AC_O1}",)),
    "initial:dependencies_omitted": (run_initial(lambda d: unit(d, B).pop("dependencies")), "EDGE_DISAGREEMENT",
                                     (f"{B}:{A}",)),
    "split:operation_id_absent": (run_split_b(absent_operation_id), "INVALID_CANDIDATE", ("operation_id",)),
    # Review R2 repair: with a contract original, every result must carry a BiuContract.
    "split:result_contract_as_body": (run_split_b(child_contract_as_body), "INCOMPLETE_CONTRACT",
                                      (f"{C2}:contract",)),
    "split:result_contract_absent": (run_split_b(child_contract_absent), "INCOMPLETE_CONTRACT",
                                     (f"{C2}:contract",)),
}


@pytest.fixture
def run(tmp_path):
    count = iter(range(1000))

    def execute(name, check_snapshot=True):
        setup, _, _ = SCENARIOS[name]
        h = Harness(tmp_path / f"s{next(count)}")
        call = setup(h)
        before = h.snapshot()
        result = call()
        if check_snapshot:
            assert h.snapshot() == before
        return result, h
    return execute


def assert_hold(result, name):
    _, code, refs = SCENARIOS[name]
    assert isinstance(result, CompilationHold), result
    assert result.reason_code == code, result.findings
    if refs is not None:
        assert result.affected_refs == tuple(refs), result.affected_refs


def assert_admitted(result, mode):
    assert isinstance(result, ValidationReport), getattr(result, "findings", result)
    document = result.document()
    assert (document["mode"], document["admitted_for_assessment"]) == (mode, True)
    assert "VALIDATION_ONLY" in document["labels"]
    return document


def pointer(h: Harness, result) -> tuple[int, dict, Observation]:
    version, state = h.service.read(result.candidate_digest)
    return version, state, h.service.retained(Ref(**state["result_ref"]))


# --- P01 / P02 / P03 / P04 / P05 ---------------------------------------------------------------------------


def test_valid_initial_graph_admitted_for_assessment(tmp_path):
    h = Harness(tmp_path / "s")
    candidate = initial(h.design())
    h.lifecycle(P1, "DONE")
    before = h.snapshot()
    result = h.service.validate(candidate)
    document = assert_admitted(result, INITIAL)
    assert document["provenance"] == "SUPPLIED_CANDIDATE_NOT_DERIVED" and "INITIAL_DERIVATION" in document["non_claims"]
    assert [u["identity"] for u in document["units"]] == [A, B, C]
    assert document["obligation_coverage"]["evidence"] == {"total": 1, "covered": 1}
    assert document["coverage_is_not_satisfaction"] is True
    version, state, observation = pointer(h, result)
    assert (version, state["status"], state["mode"], observation.evidence_id) == (1, "VALIDATED", INITIAL,
                                                                                  "compilation.validated")
    assert json.loads(observation.value) == document
    assert h.snapshot() == before  # No factory:/release: write, receipt, reservation or history change.
    assert not h.store.list_states(PROFILE, "release:") and h.work.receipts() == ()


@pytest.mark.parametrize("variant", ["cycle", "missing_endpoint", "no_predicate"])
def test_graph_refusal_names_edge(run, variant):
    result, _ = run("initial:" + variant)
    assert_hold(result, "initial:" + variant)


@pytest.mark.parametrize("variant", ["cycle", "missing_endpoint", "no_predicate"])
def test_split_graph_refusal_names_edge(run, variant):
    result, _ = run("split:" + variant)
    assert_hold(result, "split:" + variant)


def test_incomplete_contract_refused(run):
    result, _ = run("initial:incomplete_contract")
    assert_hold(result, "initial:incomplete_contract")


@pytest.mark.parametrize("category", ["requirement", "acceptance", "verification", "evidence"])
def test_uncovered_obligation_refused(run, category):
    result, _ = run("initial:uncovered_" + category)
    assert_hold(result, "initial:uncovered_" + category)


# --- P06 / P07 / P08 / P09 ---------------------------------------------------------------------------------


@pytest.mark.parametrize("state,reason", [("stale", "STALE"), ("unreviewed", "REVIEW_REQUIRED"),
                                          ("absent", "NO_DESIGN")])
def test_design_gate_holds(run, state, reason):
    for mode in ("initial", "split"):
        result, _ = run(f"{mode}:design_{state}")
        assert_hold(result, f"{mode}:design_{state}")
        assert result.detail == reason  # The U5 ReadinessDecision.reason_code, verbatim.


def test_unresolved_authority_holds(run):
    result, h = run("initial:unresolved_authority")
    assert_hold(result, "initial:unresolved_authority")
    finding = h.profile.ambiguity.show(result.affected_refs[0])[0]
    assert (finding.requirement_id, finding.rule_code) == ("SF-REQ-901", "MISSING_INTENT")


def test_conflicting_decisions_hold(run):
    result, _ = run("initial:decision_conflict")
    assert_hold(result, "initial:decision_conflict")


def test_hold_writes_no_transition(tmp_path):
    """Every hold of P02-P08 and P12-P22 leaves all non-compilation state byte-equal (no READY/IMPLEMENT)."""
    for index, (name, (setup, code, _)) in enumerate(sorted(SCENARIOS.items())):
        h = Harness(tmp_path / f"s{index}")
        call = setup(h)
        before = h.snapshot()
        result = call()
        assert isinstance(result, CompilationHold) and result.reason_code == code, (name, result)
        assert h.snapshot() == before, name
        version, state, observation = pointer(h, result)
        assert (version, state["status"], observation.evidence_id) == (1, "HELD", "compilation.held"), name
        assert json.loads(observation.value)["transition"] == "NONE"


# --- P10 / P11 / P12 (013-dependency-authority) ------------------------------------------------------------


def test_open_done_predecessor_satisfied(tmp_path):
    h = Harness(tmp_path / "s")
    candidate = initial(h.design())
    h.lifecycle(P1, "DONE")
    assert candidate["projection"][P1] == "OPEN"
    document = assert_admitted(h.service.validate(candidate), INITIAL)
    assert document["external_predecessors"] == [{"identity": P1, "stage": "DONE"}]


def test_closed_nonterminal_predecessor_unsatisfied(run):
    result, h = run("initial:closed_nonterminal_predecessor")
    assert_hold(result, "initial:closed_nonterminal_predecessor")
    assert h.store.read_state(PROFILE, "factory:" + P2)[1]["stage"] == "IMPLEMENT"


def test_declared_edge_disagreement_refused(run):
    result, _ = run("initial:declared_edge_disagreement")
    assert_hold(result, "initial:declared_edge_disagreement")


# --- P13 / P14: SWF-33 replay and nonconserving splits -----------------------------------------------------


@pytest.mark.parametrize("binding", ["unbound", "bound"])
def test_swf33_replay(run, tmp_path, binding):
    if binding == "unbound":
        result, _ = run("swf33:unbound")
        assert_hold(result, "swf33:unbound")
        assert [c for c, _ in result.findings] == ["CLAUSE_NOT_VERBATIM"]
        return
    h = Harness(tmp_path / "bound")
    call = run_split_a()(h)
    document = assert_admitted(call(), SPLIT_REPLAN)
    conservation = document["conservation"]
    assert conservation["forward"] == {"mapped": 69, "total": 69}
    assert conservation["reverse"] == {"entries": 72, "complete": True}
    assert conservation["shared_rows"] == ["SF-REQ-005", "SF-REQ-007", "SF-REQ-038"]
    assert conservation["shared_rule"] == "ALL_EXTENTS_REQUIRED" and conservation["comparison"] == "BYTE_EXACT"
    assert [e["obligation_id"] for e in conservation["elaboration_bound"]] == list(NOT_VERBATIM)
    assert document["graph_semantics"] == HISTORICAL_EDGE_SET
    assert document["prior_assessments"] == [{
        "unit": "PY-10", "locator": h.priors[0]["locator"], "digest": "sha256:" + BLOBS[PRIOR_PY10],
        "unchanged": True, "disposition": "SPLIT_RECOMMENDED", "applicability": "INAPPLICABLE",
        "inapplicable_to": ["PY-09B", "PY-10"]}]
    assert document["identity_bounds"]["checked"] == ["PY-09B", "PY-10"]
    assert "PHASE5_CANDIDATE_MECHANISMS_NOT_INDEPENDENTLY_DESIGN_VERIFIED" in document["labels"]


@pytest.mark.parametrize("variant", ["omission", "weakened_clause", "invented_obligation", "partial_mapping",
                                     "integration_duty_dropped"])
def test_split_nonconserving_refused(run, variant):
    for family in ("swf33", "split"):
        result, _ = run(f"{family}:{variant}")
        assert_hold(result, f"{family}:{variant}")


# --- P15 / P16 / P17 / P18 ---------------------------------------------------------------------------------


@pytest.mark.parametrize("variant", ["capability", "budget_dimension", "repository_scope"])
def test_split_bounds_expansion_refused(run, variant):
    result, _ = run("split:bounds_" + variant)
    assert_hold(result, "split:bounds_" + variant)


@pytest.mark.parametrize("variant", ["absent", "payload_digest_mismatch", "stale_original_revision",
                                     "issuer_outside_limits"])
def test_split_authority_refused(run, variant):
    result, _ = run(("split:authority_absent" if variant == "absent" else "split:" + variant))
    assert_hold(result, "split:authority_absent" if variant == "absent" else "split:" + variant)
    if variant == "payload_digest_mismatch":
        assert [r.split(":expected=")[0] for r in result.affected_refs] == ["payload_digest"]
    if variant == "stale_original_revision":
        assert [r.split(":expected=")[0] for r in result.affected_refs] == ["original_revision"]


def test_split_of_done_original_refused(run):
    result, _ = run("split:done_original")
    assert_hold(result, "split:done_original")


def test_valid_split_candidate_admitted_for_assessment(tmp_path):
    h = Harness(tmp_path / "s")
    call = run_split_b()(h)
    before = h.snapshot()
    result = call()
    document = assert_admitted(result, SPLIT_REPLAN)
    rewrites = {(r["rule"], r["source_edge"], r["result_edge"], r["predicate"]) for r in document["identity_rewrites"]}
    assert rewrites == {
        ("PRESERVED", f"{P1}->{O}", f"{P1}->{O}", "DONE"), ("PRESERVED", f"{P2}->{O}", f"{P2}->{O}", "DONE"),
        ("PRESERVED", f"{O}->{D}", f"{O}->{D}", "DONE"),
        ("COPIED_TO_CHILD", f"{P1}->{O}", f"{P1}->{C1}", "DONE"), ("COPIED_TO_CHILD", f"{P2}->{O}", f"{P2}->{C1}", "DONE"),
        ("COPIED_TO_CHILD", f"{P1}->{O}", f"{P1}->{C2}", "DONE"), ("COPIED_TO_CHILD", f"{P2}->{O}", f"{P2}->{C2}", "DONE"),
        ("CHILD_TO_PARENT", None, f"{C1}->{O}", "DONE"), ("CHILD_TO_PARENT", None, f"{C2}->{O}", "DONE")}
    assert document["lineage"] == [{"child": C1, "split_from": O, "operation_id": OPERATION},
                                   {"child": C2, "split_from": O, "operation_id": OPERATION}]
    assert document["identity_bounds"]["result"] == "PASS" and document["invalidation"] == [O, C1, C2]
    assert document["bounds"] == "WITHIN_ORIGINAL" and document["graph_semantics"] == PREDICATED
    assert "SPLIT_PREPARE_OR_APPLY" in document["non_claims"]
    version, state, observation = pointer(h, result)
    assert (version, state["status"], observation.evidence_id) == (1, "VALIDATED", "compilation.validated")
    assert h.snapshot() == before


# --- P19 / P20 / P21 / P22 ---------------------------------------------------------------------------------


@pytest.mark.parametrize("variant", ["weakened_predicate", "prerequisite_not_copied", "downstream_redirected",
                                     "edge_pruned", "unauthorized_inter_child_edge", "missing_child_parent_done_edge"])
def test_dependency_rewrite_refused(run, variant):
    result, _ = run("split:" + variant)
    assert_hold(result, "split:" + variant)


@pytest.mark.parametrize("variant", ["grammar_invalid", "collision_active", "collision_retired", "collision_reserved",
                                     "existing_identity_rewritten"])
def test_identity_bounds_refused(run, tmp_path, variant):
    names = ("split:grammar_short", "split:grammar_suffix") if variant == "grammar_invalid" else ("split:" + variant,)
    for name in names:
        result, _ = run(name)
        assert_hold(result, name)
    if variant == "grammar_invalid":
        h = Harness(tmp_path / "family-a")
        report = run_split_a()(h)().document()
        assert report["identity_bounds"] == {"policy": POLICY_A, "checked": ["PY-09B", "PY-10"], "result": "PASS"}


@pytest.mark.parametrize("variant", ["missing_split_from", "suffix_only_lineage", "operation_id_mismatch",
                                     "parent_missing_child"])
def test_lineage_refused(run, variant):
    result, _ = run("split:" + variant)
    assert_hold(result, "split:" + variant)


@pytest.mark.parametrize("variant", ["invalidation_missing_parent", "invalidation_missing_changed_dependent",
                                     "history_bytes_altered", "stale_ready_as_current"])
def test_stale_assessment_history_refused(run, tmp_path, variant):
    names = ["split:" + variant] + (["swf33:history_bytes_altered"] if variant == "history_bytes_altered" else [])
    for name in names:
        result, h = run(name)
        assert_hold(result, name)
        if variant == "history_bytes_altered":
            assert result.affected_refs[0].startswith(h.priors[0]["locator"] + ":expected=")
    if variant == "invalidation_missing_changed_dependent":
        # The same authorized dependency change is admitted once the changed dependent is invalidated too.
        h = Harness(tmp_path / "complete")
        call = run_split_b(both(authorize_downstream, invalidation([C1, C2, O, D])))(h)
        document = assert_admitted(call(), SPLIT_REPLAN)
        assert document["dependency_semantics_changed"] == [D]


# --- P23 / D-1 ---------------------------------------------------------------------------------------------


def test_validation_deterministic_under_permutation(tmp_path):
    cases = {"initial-valid": run_initial(), "initial-held": SCENARIOS["initial:cycle"][0],
             "split-valid": run_split_b(), "split-held": SCENARIOS["split:unauthorized_inter_child_edge"][0]}
    for index, (name, setup) in enumerate(cases.items()):
        outputs = []
        for permute in (False, True):
            h = Harness(tmp_path / f"{index}-{permute}")
            result = setup(h, permute=permute)()
            outputs.append((canonical(result.document()), result.candidate_digest))
        assert outputs[0] == outputs[1], name


def test_context_assembly_adds_no_cross_group_import_pair():
    """Director condition D-1: context_assembly imports no group beyond its baseline pairs."""
    baseline = {"control_plane.application", "evidence_learning.domain", "evidence_learning.ports",
                "execution_coordination.domain", "execution_coordination.ports"}
    observed = set()
    for path in (ROOT / "src" / "alienintent" / "context_assembly").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            modules = ([node.module] if isinstance(node, ast.ImportFrom) and node.module else
                       [a.name for a in node.names] if isinstance(node, ast.Import) else [])
            for module in modules:
                parts = module.split(".")
                if parts[0] == "alienintent" and parts[1] != "context_assembly":
                    observed.add(".".join(parts[1:3]))
    assert observed <= baseline, observed - baseline
    assert not {"execution_coordination.application", "execution_coordination.adapters"} & observed


# --- Review R1 repairs --------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["split:duplicate_edge", "initial:unresolved_authority_via_contract",
                                  "split:original_graph_omitted", "split:original_obligation_omitted",
                                  "split:frozen_clause_truncated", "initial:dependencies_omitted",
                                  "split:operation_id_absent"])
def test_review_r1_refusals(run, name):
    result, h = run(name)
    assert_hold(result, name)
    if name == "split:frozen_clause_truncated":
        # The truncated frozen text is also not a whole clause of the original contract.
        assert ("CLAUSE_NOT_VERBATIM", ("AC-O-1",)) in result.findings
    if name == "initial:unresolved_authority_via_contract":
        assert h.profile.ambiguity.show(result.affected_refs[0])[0].requirement_id == "SF-REQ-903"


@pytest.mark.parametrize("name", ["split:result_contract_as_body", "split:result_contract_absent"])
def test_review_r2_result_without_contract_refused(run, name):
    """A contract original anchors bounds and declared edges; a result without a BiuContract cannot be admitted."""
    result, _ = run(name)
    assert_hold(result, name)


def test_duplicate_edge_refused_in_any_order(tmp_path):
    """A duplicate (from,to) pair is refused whichever copy comes first; never last-writer-wins."""
    outputs = []
    for index, first in enumerate((False, True)):
        def change(proposal, first=first):
            duplicate = edge(P1, C1, "STARTED")
            proposal["result_edges"] = ([duplicate] + proposal["result_edges"] if first
                                        else proposal["result_edges"] + [duplicate])
        result = run_split_b(change)(Harness(tmp_path / str(index)))()
        assert isinstance(result, CompilationHold) and result.reason_code == "INVALID_CANDIDATE", result
        outputs.append(canonical(result.document()))
    assert outputs[0] == outputs[1]


def test_split_does_not_require_done_predecessors(tmp_path):
    """Splitting is planning, not execution eligibility: an in-progress prerequisite does not hold the split."""
    result = run_split_b(stages=((P1, "DONE"), (P2, "IMPLEMENT")))(Harness(tmp_path / "s"))()
    assert_admitted(result, SPLIT_REPLAN)


MALFORMED = {
    "mapping_id_list": lambda p: p["mapping"][0].update(obligation_id=["x"]),
    "reverse_origin_list": lambda p: p["reverse"][0].update(origin=["x"]),
    "obligation_id_list": lambda p: p["original_obligations"][0].update(id=["x"]),
    "invalidation_item_list": lambda p: p["invalidation"].append(["x"]),
    "active_snapshot_string": lambda p: p["identity_snapshot"].update(active="WO-990100"),
    "children_item_list": lambda p: p["results"][0].update(children=[["x"]]),
    "dependencies_item_list": lambda p: p["results"][1]["contract"]["dependencies"].append(["x"]),
    "prior_ref_string": lambda p: p["prior_assessments"][0].update(ref="objects/x"),
    "not_a_number": lambda p: p["results"][1]["contract"].update(version=float("nan")),
    "elaboration_id_list": lambda p: p["elaboration_approvals"].append(
        {"obligation_id": ["x"], "decision_ref": "d", "decision_digest": "sha256:" + "0" * 64}),
}


@pytest.mark.parametrize("variant", sorted(MALFORMED))
def test_malformed_split_is_a_typed_hold(tmp_path, variant):
    result = run_split_b(after=lambda proposal, original: MALFORMED[variant](proposal))(Harness(tmp_path / "s"))()
    assert isinstance(result, CompilationHold) and result.reason_code == "INVALID_CANDIDATE", result


@pytest.mark.parametrize("variant", ["edges_scalar", "requirements_scalar", "category_list"])
def test_malformed_initial_is_a_typed_hold(tmp_path, variant):
    changes = {"edges_scalar": lambda d: d.update(edges=5), "requirements_scalar": lambda d: d.update(requirements=5),
               "category_list": lambda d: d["obligations"][0].update(category=["requirement"])}
    result = run_initial(changes[variant])(Harness(tmp_path / "s"))()
    assert isinstance(result, CompilationHold) and result.reason_code == "INVALID_CANDIDATE", result


def test_malformed_original_and_policy_are_typed_holds(tmp_path):
    def broken_original(proposal, original):
        original["contract"]["required_evidence"] = []
    result = run_split_b(after=broken_original)(Harness(tmp_path / "a"))()
    assert isinstance(result, CompilationHold) and result.reason_code == "INVALID_CANDIDATE", result
    h, captured = Harness(tmp_path / "b"), {}
    run_split_b(after=lambda proposal, original: captured.update(proposal=proposal, original=original))(h)
    result = h.service.validate_split(captured["proposal"], captured["original"], LIMITS_B, {"family": "WO"})
    assert isinstance(result, CompilationHold) and result.reason_code == "INVALID_CANDIDATE", result
