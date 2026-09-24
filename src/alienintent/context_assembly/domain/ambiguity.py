"""Mechanical completeness findings over an immutable inventory; never exhaustive NL ambiguity detection.

A finding is a source-linked unanswered question, not an instruction. Inspection never edits
requirement intent and never decides product meaning: only an attributed decision resolves.
"""
from dataclasses import asdict, dataclass
import re

from alienintent.context_assembly.domain.inventory import (InventorySnapshot, Issue, Provenance, Requirement, Token,
                                                          digest, resolve)


class AmbiguityHold(ValueError):
    """Input cannot safely be inspected; the affected branch holds."""


LABELS = ("Intent", "Scope", "Non-goals", "Authority", "Acceptance")
PLACEHOLDERS = frozenset({"", "tbd", "todo", "undefined", "unknown", "n/a", "?", "tba"})
QUESTIONS = {
    "MISSING_INTENT": "What outcome is intended? The definition states no Intent.",
    "MISSING_SCOPE": "What is in scope? The definition states no Scope boundary.",
    "SCOPE_CONFLICT": "Scope and Non-goals name the same item; which applies?",
    "MISSING_AUTHORITY": "Which authority governs this requirement? None is stated or approved.",
    "UNDEFINED_ACCEPTANCE": "What measurable acceptance result applies? An acceptance result is undefined.",
    "AMBIGUOUS_DEPENDENCY": "Which definition does a dependency mean? It is unresolved, conflicting or retired.",
    "CONFLICTING_SOURCES": "Sources define this requirement differently; which definition governs?",
}
OPEN, RESOLVED, STALE = "OPEN", "RESOLVED", "STALE"
ELIGIBLE, HELD, RETIRED = "ELIGIBLE_FOR_PREPARATION", "HELD", "RETIRED"


@dataclass(frozen=True)
class SemanticQuestion:
    question: str
    locators: tuple[tuple[str, int, int], ...]


@dataclass(frozen=True)
class SemanticReview:
    """Attributable independent review imported as observations; it cannot answer or edit."""
    reviewer: str
    review_ref: str
    requirement_id: str
    requirement_revision: str
    questions: tuple[SemanticQuestion, ...]

    def __post_init__(self) -> None:
        if (any(not isinstance(v, str) or not v.strip() for v in
                (self.reviewer, self.review_ref, self.requirement_id, self.requirement_revision))
                or not isinstance(self.questions, tuple)
                or any(not isinstance(q, SemanticQuestion) or not q.question.strip() or len(q.question) > 2000
                       or not isinstance(q.locators, tuple) or not q.locators for q in self.questions)):
            raise AmbiguityHold("INVALID_SEMANTIC_REVIEW")

    @property
    def key(self) -> str:
        return digest([self.review_ref, self.requirement_id])


@dataclass(frozen=True)
class Finding:
    finding_id: str
    project: str
    requirement_id: str
    requirement_revision: str
    rule_code: str
    origin: str
    locators: tuple[tuple[str, int, int], ...]
    question: str
    blocked_reason: str
    required_actor: str
    affected: tuple[str, ...]
    reviewer_ref: str | None = None

    @property
    def work_item(self) -> str:
        return "upstream-question:" + self.finding_id


@dataclass(frozen=True)
class RequirementReport:
    requirement_id: str
    revision: str
    semantic_digest: str
    fields_present: tuple[str, ...]
    inventory_status: str
    mechanical_status: str
    semantic_review_status: str
    preparation: str
    hold_reasons: tuple[str, ...]
    finding_ids: tuple[str, ...]


@dataclass(frozen=True)
class InspectionReport:
    project: str
    inventory_digest: str
    requirements: tuple[RequirementReport, ...]
    findings: tuple[Finding, ...]
    statuses: tuple[tuple[str, str], ...]
    schema_version: int = 1

    @property
    def digest(self) -> str:
        return digest(asdict(self))

    def requirement(self, requirement_id: str) -> RequirementReport:
        return next(r for r in self.requirements if r.requirement_id == requirement_id)


def finding_identity(project: str, revision: str, rule: str, locators: tuple[tuple[str, int, int], ...],
                     reviewer_ref: str | None = None) -> str:
    parts: list[object] = [project, revision, rule, sorted(list(l) for l in locators)]
    if reviewer_ref is not None:
        parts.append(reviewer_ref)
    return digest(parts)


def resolution_identity(finding_id: str, decision_key: str, actor: str) -> str:
    return digest([finding_id, decision_key, actor])


def snapshot_from_document(document: dict) -> InventorySnapshot:
    """Rehydrate the consumed U1 snapshot; any drift from the pinned digest holds."""
    try:
        spans = lambda values: tuple(tuple(v) for v in values)
        requirement = lambda d: Requirement(**{**d, "dependencies": tuple(d["dependencies"]),
                                               "satisfaction_links": tuple(d["satisfaction_links"]),
                                               "provenance": tuple(Provenance(**p) for p in d["provenance"]),
                                               "source_paths": tuple(d["source_paths"]), "source_spans": spans(d["source_spans"])})
        snapshot = InventorySnapshot(
            document["project"], document["source_manifest_digest"],
            tuple(requirement(d) for d in document["current"]), tuple(requirement(d) for d in document["history"]),
            tuple(Token(**{**t, "operands": tuple(t["operands"])}) for t in document["tokens"]),
            tuple(Issue(**i) for i in document["identifier_issues"]), tuple(Issue(**i) for i in document["source_issues"]),
            spans(document["definition_locators"]), tuple(document["referenced_ids"]), tuple(document["defined_ids"]),
            tuple(document["unresolved"]), tuple(document["conflicts"]), tuple(document["retired"]),
            tuple(document["stale_links"]), document["prior_snapshot"], document["schema_version"])
    except (KeyError, TypeError) as error:
        raise AmbiguityHold("INVALID_INVENTORY_DOCUMENT") from error
    if snapshot.schema_version != 1 or snapshot.digest != digest(document):
        raise AmbiguityHold("INVENTORY_DOCUMENT_MISMATCH")
    return snapshot


def fields(semantic: str) -> dict[str, str]:
    """Split the normalized definition body at labelled fields; unlabelled prose is ignored."""
    pattern = re.compile(r"(?:(?<=\s)|^)(" + "|".join(re.escape(l) for l in LABELS) + r"):")
    matches = list(pattern.finditer(semantic))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index+1].start() if index+1 < len(matches) else len(semantic)
        value = semantic[match.end():end].strip()
        result[match[1]] = (result[match[1]] + "; " + value) if result.get(match[1]) else value
    return result


def _items(value: str) -> tuple[str, ...]:
    return tuple(i for i in (part.strip().rstrip(".").strip() for part in value.split(";")) if i)


def _undefined_acceptance(value: str) -> bool:
    items = _items(value)
    for item in items:
        match = re.fullmatch(r"[A-Z][A-Z0-9-]*-AC-[0-9]{2,}\s*:\s*(.*)", item)
        if not match or match[1].strip().rstrip(".").casefold() in PLACEHOLDERS:
            return True
    return not items


def mechanical_rules(requirement: Requirement, snapshot: InventorySnapshot) -> tuple[str, ...]:
    present = fields(requirement.semantic)
    rules = []
    if not present.get("Intent"):
        rules.append("MISSING_INTENT")
    if not present.get("Scope"):
        rules.append("MISSING_SCOPE")
    scope = {i.casefold() for i in _items(present.get("Scope", ""))}
    if scope & {i.casefold() for i in _items(present.get("Non-goals", ""))}:
        rules.append("SCOPE_CONFLICT")
    if not present.get("Authority") or not all(p.authority_status == "approved" for p in requirement.provenance):
        rules.append("MISSING_AUTHORITY")
    if _undefined_acceptance(present.get("Acceptance", "")):
        rules.append("UNDEFINED_ACCEPTANCE")
    unclear = set(snapshot.unresolved) | set(snapshot.conflicts) | set(snapshot.retired)
    if set(requirement.dependencies) & unclear:
        rules.append("AMBIGUOUS_DEPENDENCY")
    return tuple(rules)


def _dependents(snapshot: InventorySnapshot, requirement_id: str) -> tuple[str, ...]:
    affected, changed = {requirement_id}, True
    while changed:
        changed = False
        for d in snapshot.current:
            if d.requirement_id not in affected and affected & set(d.dependencies):
                affected.add(d.requirement_id)
                changed = True
    return tuple(sorted(affected))


def requirement_revision(definitions: list[Requirement]) -> str:
    revisions = sorted({d.revision for d in definitions})
    return revisions[0] if len(revisions) == 1 else "conflict:" + digest(revisions)


def _covered(locators: tuple[tuple[str, int, int], ...], spans: tuple[tuple[str, int, int], ...]) -> bool:
    return all(any(path == p and s <= start <= end <= e for p, s, e in spans) for path, start, end in locators)


def inspect(snapshot: InventorySnapshot, reviews: tuple[SemanticReview, ...], decision_actor: str,
            statuses: dict[str, str]) -> InspectionReport:
    """Deterministically derive findings and branch-local holds from pinned inputs and finding statuses."""
    if not decision_actor:
        raise AmbiguityHold("MISSING_DECISION_AUTHORITY")
    by_id: dict[str, list[Requirement]] = {}
    for d in snapshot.current:
        by_id.setdefault(d.requirement_id, []).append(d)
    findings: list[Finding] = []
    entries: dict[str, dict] = {}
    for requirement_id, definitions in sorted(by_id.items()):
        revision = requirement_revision(definitions)
        spans = tuple(sorted({s for d in definitions for s in d.source_spans}))
        affected = _dependents(snapshot, requirement_id)
        rules = (("CONFLICTING_SOURCES",) if requirement_id in snapshot.conflicts
                 else () if definitions[0].retired else mechanical_rules(definitions[0], snapshot))
        own: list[Finding] = []
        for rule in rules:
            fid = finding_identity(snapshot.project, revision, rule, spans)
            own.append(Finding(fid, snapshot.project, requirement_id, revision, rule, "MECHANICAL", spans,
                               f"{requirement_id}: {QUESTIONS[rule]}",
                               f"{rule}: {requirement_id} cannot advance to upstream preparation until {decision_actor} answers {fid}",
                               decision_actor, affected))
        semantic_status, review_holds = "NOT_RECORDED", []
        for review in sorted((r for r in reviews if r.requirement_id == requirement_id), key=lambda r: r.review_ref):
            if review.requirement_revision != revision:
                continue  # A review of another revision is prior evidence, not a current finding.
            semantic_status = "RECORDED_FINDINGS" if review.questions or semantic_status == "RECORDED_FINDINGS" else "RECORDED_NO_FINDINGS"
            for index, question in enumerate(review.questions):
                if not _covered(question.locators, spans):
                    semantic_status = "UNVERIFIED"
                    review_holds.append("SEMANTIC_LOCATOR_OUTSIDE_REQUIREMENT:" + review.review_ref)
                    continue
                reviewer_ref = f"{review.review_ref}#{index}"
                locators = tuple(sorted(question.locators))
                fid = finding_identity(snapshot.project, revision, "SEMANTIC_REVIEW", locators, reviewer_ref)
                own.append(Finding(fid, snapshot.project, requirement_id, revision, "SEMANTIC_REVIEW", "SEMANTIC_REVIEW",
                                   locators, f"{requirement_id}: {question.question}",
                                   f"SEMANTIC_REVIEW: {requirement_id} cannot advance to upstream preparation until {decision_actor} answers {fid}",
                                   decision_actor, affected, reviewer_ref))
        overlapping = any(i.path == path and (i.line == 0 or start <= i.line <= end)
                          for i in snapshot.identifier_issues + snapshot.source_issues for path, start, end in spans)
        inventory_status = resolve(snapshot, requirement_id).status
        mechanical = "UNVERIFIED" if overlapping else "INCOMPLETE" if rules else "COMPLETE"
        reasons = [f"{f.rule_code}:{f.finding_id}" for f in own if statuses.get(f.finding_id, OPEN) != RESOLVED]
        reasons += review_holds
        if mechanical == "UNVERIFIED":
            reasons.append("INSPECTION_UNVERIFIED")
        if inventory_status not in (ELIGIBLE, "RETIRED"):
            reasons.append("INVENTORY_" + inventory_status)
        findings.extend(own)
        entries[requirement_id] = {
            "revision": revision, "semantic_digest": digest(sorted(d.semantic for d in definitions)),
            "fields_present": tuple(sorted(k for k, v in fields(definitions[0].semantic).items() if v)) if len(definitions) == 1 else (),
            "inventory_status": inventory_status, "mechanical": mechanical, "semantic": semantic_status,
            "reasons": reasons, "finding_ids": tuple(sorted(f.finding_id for f in own)),
            "retired": inventory_status == "RETIRED", "dependencies": {x for d in definitions for x in d.dependencies}}
    held = {i for i, e in entries.items() if e["reasons"]}
    changed = True
    while changed:  # A hold reaches only requirements that depend on a held requirement.
        changed = False
        for requirement_id, entry in entries.items():
            blocked = sorted(entry["dependencies"] & held)
            if blocked and requirement_id not in held:
                entry["reasons"] += ["DEPENDENCY_HELD:" + b for b in blocked]
                held.add(requirement_id)
                changed = True
    requirements = tuple(RequirementReport(
        requirement_id, e["revision"], e["semantic_digest"], e["fields_present"], e["inventory_status"], e["mechanical"],
        e["semantic"], RETIRED if e["retired"] else HELD if e["reasons"] else ELIGIBLE, tuple(e["reasons"]), e["finding_ids"])
        for requirement_id, e in sorted(entries.items()))
    ordered = tuple(sorted(findings, key=lambda f: f.finding_id))
    return InspectionReport(snapshot.project, snapshot.digest, requirements, ordered,
                            tuple((f.finding_id, statuses.get(f.finding_id, OPEN)) for f in ordered))


@dataclass(frozen=True)
class AnswerHold:
    """Typed non-success; the finding keeps its hold."""
    reason: str
    finding_id: str | None = None
    evidence_ref: dict | None = None


@dataclass(frozen=True)
class QuestionResolution:
    resolution_id: str
    finding_id: str
    requirement_revision: str
    actor: str
    authority_reference: str
    idempotency_key: str
    evidence_ref: dict


def finding_from_document(value: dict) -> Finding:
    return Finding(**{**value, "locators": tuple(tuple(l) for l in value["locators"]), "affected": tuple(value["affected"])})


def review_from_document(value: dict) -> SemanticReview:
    return SemanticReview(**{**value, "questions": tuple(
        SemanticQuestion(q["question"], tuple(tuple(l) for l in q["locators"])) for q in value["questions"])})


def report_from_document(value: dict) -> InspectionReport:
    report = InspectionReport(
        value["project"], value["inventory_digest"],
        tuple(RequirementReport(**{**r, **{k: tuple(r[k]) for k in ("fields_present", "hold_reasons", "finding_ids")}})
              for r in value["requirements"]),
        tuple(finding_from_document(f) for f in value["findings"]),
        tuple(tuple(s) for s in value["statuses"]), value["schema_version"])
    if report.schema_version != 1 or report.digest != digest(value):
        raise AmbiguityHold("INSPECTION_REPORT_MISMATCH")
    return report
