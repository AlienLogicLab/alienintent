"""Design admission: existing architecture checks first, then an independent review bound to exact revisions.

Mechanical results are named observations, never approval. Directional module policy is an open
Founder authority question (R2-GAP-051-EDGE-AUTHORITY): direction-dependent admission holds, and the
descriptive observed_edges graph is never read as a permission table.
"""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from alienintent.evidence_learning.domain.refs import Ref

MECHANICALLY_HELD, REVIEW_REQUIRED, VERIFIED, STALE = "MECHANICALLY_HELD", "REVIEW_REQUIRED", "VERIFIED", "STALE"
REJECTED = "REJECTED"
EXISTING_CHECKS = ("layering", "vendor-signature", "port-contract", "configuration", "determinism")
DESIGN_FIELDS = ("satisfied_requirements", "affected_behavior", "ownership", "interfaces", "persistence", "invariants",
                 "failures_recovery", "security", "capabilities", "evidence", "non_goals")
MATERIAL = frozenset({"BEHAVIOR", "PUBLIC_API", "PERSISTENCE", "SECURITY"})
LOCAL = "IMPLEMENTATION_LOCAL"
DISPOSED = "FOUNDER_DISPOSED"
VECTOR_KEYS = ("design", "requirements", "architecture", "premises", "authority")


class DesignInvalid(ValueError):
    """The submitted design or review document does not have the pinned schema."""


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: object) -> str:
    return "sha256:" + sha256(canonical(value).encode()).hexdigest()


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _texts(value: object) -> bool:
    return isinstance(value, list) and all(_text(v) for v in value)


def _keys(value: object, required: set[str], optional: set[str] = frozenset()) -> dict:
    if not isinstance(value, dict) or not required <= set(value) or not set(value) <= required | optional:
        raise DesignInvalid("fields")
    return value


@dataclass(frozen=True)
class DesignContract:
    design_key: str
    requirements: dict
    producer: dict
    fields: dict
    decisions: tuple
    interface_manifest: tuple
    premises: tuple
    dependency_edges: tuple
    document: dict

    @property
    def digest(self) -> str:
        return digest(self.document)


def design_from_document(document: object) -> DesignContract:
    d = _keys(document, {"schema_version", "record_kind", "design_key", "requirements", "producer", "fields", "decisions",
                         "interface_manifest", "premises", "dependency_edges"})
    if type(d["schema_version"]) is not int or d["schema_version"] != 1 or d["record_kind"] != "DesignContract":
        raise DesignInvalid("schema")
    if not _text(d["design_key"]) or not isinstance(d["requirements"], dict) or not d["requirements"] \
            or not all(_text(k) and _text(v) for k, v in d["requirements"].items()):
        raise DesignInvalid("requirements")
    producer = _keys(d["producer"], {"actor", "invocation"})
    if not all(_text(v) for v in producer.values()) or not isinstance(d["fields"], dict):
        raise DesignInvalid("producer")
    for name, entry in d["fields"].items():
        if name not in DESIGN_FIELDS or not isinstance(entry, dict) or len(entry) != 1 \
                or not ("value" in entry and _texts(entry["value"]) or "inapplicable" in entry
                        and isinstance(entry["inapplicable"], str)):
            raise DesignInvalid("field " + str(name))
    for entry in d["decisions"] if isinstance(d["decisions"], list) else [None]:
        e = _keys(entry, {"id", "category", "status", "statement", "bound"})
        if e["category"] not in MATERIAL | {LOCAL} or e["status"] not in ("FIXED", "OPEN") \
                or not _text(e["id"]) or not _text(e["statement"]) or not isinstance(e["bound"], str):
            raise DesignInvalid("decision")
    for entry in d["interface_manifest"] if isinstance(d["interface_manifest"], list) else [None]:
        e = _keys(entry, {"port", "producer", "consumer", "provides", "requires"})
        if not all(_text(e[k]) for k in ("port", "producer", "consumer")) or not _texts(e["provides"]) \
                or not _texts(e["requires"]):
            raise DesignInvalid("interface")
    for entry in d["premises"] if isinstance(d["premises"], list) else [None]:
        e = _keys(entry, {"premise_id", "criterion", "requested"})
        if not _text(e["premise_id"]) or not _text(e["criterion"]) or not _texts(e["requested"]) or not e["requested"]:
            raise DesignInvalid("premise")
    for entry in d["dependency_edges"] if isinstance(d["dependency_edges"], list) else [None]:
        e = _keys(entry, {"source", "target"})
        if not _text(e["source"]) or not _text(e["target"]):
            raise DesignInvalid("dependency edge")
    return DesignContract(d["design_key"], dict(d["requirements"]), dict(producer), dict(d["fields"]),
                          tuple(d["decisions"]), tuple(d["interface_manifest"]), tuple(d["premises"]),
                          tuple(d["dependency_edges"]), json.loads(canonical(d)))


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    violations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ArchitectureReport:
    """Results of the existing approved checks and the digest of the baseline they ran over."""
    baseline: str
    results: tuple[CheckResult, ...]


@dataclass(frozen=True)
class PremiseResult:
    premise_id: str
    feasible: bool
    reason: str | None
    missing: tuple[str, ...]
    evidence_refs: tuple[Ref, ...]


@dataclass(frozen=True)
class DirectionAuthority:
    """The authority snapshot for directional module policy; observed_edges is descriptive only."""
    gap_id: str
    status: str
    resolution_actor: str
    source_ref: Ref | None
    observed_edges: dict

    @property
    def digest(self) -> str:
        return digest({"gap_id": self.gap_id, "status": self.status, "resolution_actor": self.resolution_actor,
                       "source_ref": asdict(self.source_ref) if self.source_ref else None})


@dataclass(frozen=True)
class Hold:
    check: str
    reason_code: str
    affected: tuple[str, ...]


@dataclass(frozen=True)
class MechanicalReport:
    design_key: str
    design_digest: str
    status: str
    checks: tuple[dict, ...]
    holds: tuple[Hold, ...]
    premises: tuple[dict, ...]
    vector: dict

    @property
    def digest(self) -> str:
        return digest(asdict(self))


def report_from_document(document: dict) -> MechanicalReport:
    return MechanicalReport(document["design_key"], document["design_digest"], document["status"],
                            tuple(document["checks"]), tuple(Hold(h["check"], h["reason_code"], tuple(h["affected"]))
                                                             for h in document["holds"]),
                            tuple(document["premises"]), document["vector"])


def _architecture(architecture: ArchitectureReport | None) -> list[Hold]:
    if architecture is None:
        return [Hold("existing-architecture", "ARCHITECTURE_BASELINE_MISSING", ("architecture-baseline",))]
    names = {r.name for r in architecture.results}
    absent = tuple(c for c in EXISTING_CHECKS if c not in names)
    if absent:
        return [Hold("existing-architecture", "ARCHITECTURE_CHECK_UNAVAILABLE", absent)]
    failed = tuple(f"{r.name}: {v}" for r in architecture.results if not r.passed for v in (r.violations or ("failed",)))
    if failed:
        return [Hold("existing-architecture", "ARCHITECTURE_CHECK_FAILED", failed)]
    return []


def _interfaces(design: DesignContract) -> list[Hold]:
    provided: dict[str, set[str]] = {}
    for entry in design.interface_manifest:
        provided.setdefault(entry["port"], set()).update(entry["provides"])
    unmet = tuple(f"{e['port']}: {e['consumer']} requires {r}" for e in design.interface_manifest for r in e["requires"]
                  if r not in provided[e["port"]])
    if unmet:
        return [Hold("interface-compatibility", "INCOMPATIBLE_INTERFACE", unmet)]
    return []


def _completeness(design: DesignContract) -> list[Hold]:
    holds = []
    absent = tuple(f for f in DESIGN_FIELDS if f not in design.fields)
    if absent:
        holds.append(Hold("contract-completeness", "INCOMPLETE_DESIGN", absent))
    unexplained = tuple(f for f, e in sorted(design.fields.items()) if "inapplicable" in e and not _text(e["inapplicable"]))
    if unexplained:
        holds.append(Hold("contract-completeness", "UNEXPLAINED_INAPPLICABILITY", unexplained))
    satisfied = design.fields.get("satisfied_requirements", {})
    if satisfied and sorted(satisfied.get("value") or ()) != sorted(design.requirements):
        holds.append(Hold("contract-completeness", "REQUIREMENT_LINK_MISMATCH", tuple(sorted(design.requirements))))
    return holds


def _decisions(design: DesignContract) -> list[Hold]:
    holds = []
    material = tuple(d["id"] for d in design.decisions if d["status"] == "OPEN" and d["category"] in MATERIAL)
    if material:
        holds.append(Hold("decisions", "UNRESOLVED_MATERIAL_DECISION", material))
    unbounded = tuple(d["id"] for d in design.decisions
                      if d["status"] == "OPEN" and d["category"] == LOCAL and not _text(d["bound"]))
    if unbounded:
        holds.append(Hold("decisions", "UNBOUNDED_LOCAL_CHOICE", unbounded))
    return holds


def _premises(design: DesignContract, results: tuple[PremiseResult, ...] | None) -> list[Hold]:
    if not design.premises:
        return []
    if results is None:
        return [Hold("platform-premise", "PREMISE_EVIDENCE_UNAVAILABLE", tuple(p["premise_id"] for p in design.premises))]
    infeasible = tuple(f"{r.premise_id}: {r.reason} {','.join(r.missing)}".strip() for r in results if not r.feasible)
    if infeasible:
        return [Hold("platform-premise", "INFEASIBLE_PREMISE", infeasible)]
    return []


def _direction(design: DesignContract, authority: DirectionAuthority | None) -> list[Hold]:
    # observed_edges is a source-import snapshot: it neither permits nor forbids a declared edge.
    affected = tuple(f"{e['source']} -> {e['target']}" for e in design.dependency_edges)
    if not affected:
        return []
    if authority is None or authority.status != DISPOSED:
        return [Hold("direction-authority", "ARCHITECTURE_AUTHORITY_HOLD", affected)]
    return [Hold("direction-authority", "DIRECTION_SCOPE_UNREVIEWED", affected)]


def premise_document(result: PremiseResult) -> dict:
    return {"premise_id": result.premise_id, "feasible": result.feasible, "reason": result.reason,
            "missing": list(result.missing), "evidence_refs": [asdict(r) for r in result.evidence_refs]}


def inspect_design(design: DesignContract, architecture: ArchitectureReport | None,
                   authority: DirectionAuthority | None, premises: tuple[PremiseResult, ...] | None) -> MechanicalReport:
    """Every check runs and reports in order; the existing architecture checks always come first."""
    ordered = (("existing-architecture", _architecture(architecture)), ("interface-compatibility", _interfaces(design)),
               ("contract-completeness", _completeness(design)), ("decisions", _decisions(design)),
               ("platform-premise", _premises(design, premises)), ("direction-authority", _direction(design, authority)))
    holds = tuple(h for _, found in ordered for h in found)
    checks = [{"check": name, "result": "HOLD" if found else "PASS", "reasons": [h.reason_code for h in found]}
              for name, found in ordered]
    if architecture is not None:
        checks[0]["existing"] = [{"name": r.name, "passed": r.passed, "violations": list(r.violations)}
                                 for r in architecture.results]
    premise_docs = tuple(premise_document(r) for r in premises or ())
    vector = {"design": design.digest, "requirements": dict(sorted(design.requirements.items())),
              "architecture": architecture.baseline if architecture else None,
              "premises": digest(list(premise_docs)), "authority": authority.digest if authority else None}
    return MechanicalReport(design.design_key, design.digest, MECHANICALLY_HELD if holds else REVIEW_REQUIRED,
                            tuple(checks), holds, premise_docs, vector)


@dataclass(frozen=True)
class ReviewRecord:
    reviewer: dict
    producer: dict
    design_digest: str
    mechanical_report_digest: str
    revision_vector: dict
    findings: tuple
    decision: str
    authority: str
    document: dict

    @property
    def digest(self) -> str:
        return digest(self.document)


@dataclass(frozen=True)
class ReviewAdmitted:
    review: ReviewRecord
    decision: str


@dataclass(frozen=True)
class ReviewRefused:
    reason_code: str
    affected: tuple[str, ...] = ()


def review_from_document(document: object) -> ReviewRecord | ReviewRefused:
    try:
        d = _keys(document, {"reviewer", "producer", "design_digest", "mechanical_report_digest", "revision_vector",
                             "findings", "decision", "authority"})
        reviewer, producer = _keys(d["reviewer"], {"actor", "invocation"}), _keys(d["producer"], {"actor", "invocation"})
        findings = [_keys(f, {"id", "blocking", "disposition"}) for f in d["findings"]] \
            if isinstance(d["findings"], list) else None
    except DesignInvalid:
        return ReviewRefused("INVALID_REVIEW")
    if findings is None or any(not _text(f["id"]) or type(f["blocking"]) is not bool or not _text(f["disposition"])
                               for f in findings):
        return ReviewRefused("INVALID_REVIEW")
    if not all(_text(v) for v in (*reviewer.values(), *producer.values(), d["design_digest"],
                                  d["mechanical_report_digest"], d["authority"])) \
            or d["decision"] not in (VERIFIED, REJECTED) or not isinstance(d["revision_vector"], dict) \
            or d["decision"] == REJECTED and not findings:
        return ReviewRefused("INVALID_REVIEW")
    return ReviewRecord(dict(reviewer), dict(producer), d["design_digest"], d["mechanical_report_digest"],
                        dict(d["revision_vector"]), tuple(findings), d["decision"], d["authority"],
                        json.loads(canonical(d)))


def admit_review(design: DesignContract | None, report: MechanicalReport | None, review: ReviewRecord,
                 reviewers: frozenset[str]) -> ReviewAdmitted | ReviewRefused:
    """A reviewer verdict is admitted only for the exact current design, report and revision vector."""
    if design is None or report is None:
        return ReviewRefused("NO_MECHANICAL_REPORT")
    stale = tuple(k for k, current, reviewed in (
        ("design", design.digest if design else None, review.design_digest),
        ("mechanical_report", report.digest if report else None, review.mechanical_report_digest),
        ("revision_vector", report.vector if report else None, review.revision_vector)) if current != reviewed)
    if stale:
        return ReviewRefused("STALE_REVIEW", stale)
    if review.producer != design.producer:
        return ReviewRefused("PRODUCER_MISMATCH", (review.producer["actor"],))
    if review.reviewer["actor"] == design.producer["actor"]:
        return ReviewRefused("SELF_REVIEW", ("actor:" + review.reviewer["actor"],))
    if review.reviewer["invocation"] == design.producer["invocation"]:
        return ReviewRefused("SELF_REVIEW", ("invocation:" + review.reviewer["invocation"],))
    if review.reviewer["actor"] not in reviewers:
        return ReviewRefused("UNAUTHORIZED_REVIEWER", (review.reviewer["actor"],))
    if review.decision == VERIFIED and report.status == MECHANICALLY_HELD:
        return ReviewRefused("MECHANICAL_HOLD_OUTSTANDING", tuple(h.reason_code for h in report.holds))
    blocking = tuple(f["id"] for f in review.findings if f["blocking"])
    if review.decision == VERIFIED and blocking:
        return ReviewRefused("BLOCKING_FINDINGS", blocking)
    return ReviewAdmitted(review, review.decision)


@dataclass(frozen=True)
class CurrentVerified:
    design_key: str
    design_digest: str
    review_digest: str
    vector: dict


@dataclass(frozen=True)
class Held:
    reason_code: str
    affected: tuple[str, ...] = ()


@dataclass(frozen=True)
class Stale:
    changed: tuple[str, ...]


def changed_keys(verified: dict, current: dict) -> tuple[str, ...]:
    return tuple(k for k in VECTOR_KEYS if verified.get(k) != current.get(k))


def applicability(status: str | None, report: MechanicalReport | None, review_digest: str | None,
                  last_review: str | None, current_vector: dict) -> CurrentVerified | Held | Stale:
    """DesignApplicability.check over the current internal state; only an exact vector is current."""
    if status is None or report is None:
        return Held("NO_DESIGN")
    if status == STALE:
        return Stale(changed_keys(report.vector, current_vector) or ("stale",))
    # A consumer holding any other revision than the current design's is stale, whatever the gate state.
    changed = changed_keys(report.vector, current_vector)
    if changed:
        return Stale(changed)
    if status == MECHANICALLY_HELD:
        return Held(MECHANICALLY_HELD, tuple(h.reason_code for h in report.holds))
    if status == REVIEW_REQUIRED:
        return Held("REVIEW_REJECTED" if last_review == REJECTED else REVIEW_REQUIRED)
    return CurrentVerified(report.design_key, report.design_digest, review_digest, report.vector)
