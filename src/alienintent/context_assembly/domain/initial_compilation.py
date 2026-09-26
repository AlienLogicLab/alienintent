"""Initial compilation (U8): derive the INITIAL candidate from pinned requirements, verified design and proof plans.

No mapping is supplied. Derivation rule REQUIREMENT_BOUNDED_UNITS_v1 emits one unit per requirement the verified
design satisfies, keyed by the stable unit_key requirement:<id>. Finer semantic boundaries are Agent Ready SPLIT
judgment carried out by a later authorized Split Transaction; the compiler never chooses them. Every BiuContract
field is copied from one named source (the requirement's labelled fields, the verified design, the requirement's
proof plan or the authority limits); no clause is composed, and the four obligation categories are frozen from those
sources with a forward and reverse trace. The derived candidate is then passed unchanged through the U7 validator, so
validation is a post-derivation check, never the derivation.

Identities follow the SF-REQ-013 candidate identity design (INITIAL_IDENTITY_RESERVATION_v1): a persisted reservation
per unit_key is reused; a new unit_key takes the lowest unused unsuffixed number of the configured family and width,
excluding active, retired and reserved identities. New keys are assigned in unit_key value order, so identities never
depend on input enumeration, and a persisted reservation never moves when other units are added. A requirement that
already has a decomposition holds: that decomposition is immutable here. Nothing is released or materialized.
"""
from dataclasses import dataclass
import re
from typing import Mapping

from alienintent.context_assembly.domain.ambiguity import ELIGIBLE, InspectionReport, fields
from alienintent.context_assembly.domain.compilation import (
    CATEGORY_FIELDS, DONE, IDENTITY_GRAMMAR, INITIAL, CandidateInvalid, CompilationHold, ValidationReport, _ordered,
    _text, _texts, digest, hold, identity_valid, validate)
from alienintent.context_assembly.domain.design_admission import DesignContract
from alienintent.context_assembly.domain.inventory import InventorySnapshot, Requirement

DERIVED = "DERIVED_FROM_PINNED_INPUTS"
DERIVATION_RULE = "REQUIREMENT_BOUNDED_UNITS_v1"
IDENTITY_RULE = "INITIAL_IDENTITY_RESERVATION_v1"
BUDGET_RULE = "PER_UNIT_CAP_FROM_AUTHORITY_LIMITS"
RATIONALE = ("One unit per requirement the verified design satisfies: the requirement is the smallest authorized "
             "boundary of intent; finer semantic boundaries are Agent Ready SPLIT judgment applied by an authorized "
             "Split Transaction. Each field is copied from one named source; authority_limits.budget_policy is the "
             "authorized cap of each unit, never divided or raised. Candidate rule, subject to Design Verification.")
CANDIDATE_LABELS = ("INITIAL_COMPILATION", "ADMITTED_FOR_ASSESSMENT_ONLY",
                    "IDENTITY_RULES_CANDIDATE_NOT_INDEPENDENTLY_DESIGN_VERIFIED")
NON_CLAIMS = ("SPLIT_PREPARE_OR_APPLY", "ISSUE_ALLOCATION_OR_MATERIALIZATION", "LIFECYCLE_OR_RELEASE_TRANSITION",
              "SF_REQ_015_LINT_OR_ASSESSMENT", "OBLIGATION_SATISFACTION")
LIMIT_TEXTS = ("authority_issuer", "retry_policy", "release_policy")
LIMIT_LISTS = ("authority_references", "candidate_custody_requirements", "required_closure_actions",
               "stop_escalation_conditions", "target_repositories", "baselines", "required_capabilities")
PREFIX = "requirement:"
JUDGMENT = "JUDGMENT"


@dataclass(frozen=True)
class CompilationCandidate:
    """A derived, validated INITIAL candidate: admitted for assessment only, never released or materialized."""
    candidate_digest: str
    input_digest: str
    reservations: tuple[tuple[str, str], ...]
    body: dict

    admitted_for_assessment = True

    def document(self) -> dict:
        return self.body


def unit_key(requirement_id: str) -> str:
    return PREFIX + requirement_id


def items(value: str) -> list[str]:
    """Labelled-field items as the U2 inspection reads them: ';'-separated, trailing period removed."""
    return [i for i in (part.strip().rstrip(".").strip() for part in value.split(";")) if i]


def _same(revision: str, other: object) -> bool:
    return isinstance(other, str) and revision.removeprefix("sha256:") == other.removeprefix("sha256:")


def _limits(document: object) -> dict:
    """The authority limits the compiler copies and bounds against; a malformed value is INVALID_CANDIDATE."""
    if not isinstance(document, dict):
        raise CandidateInvalid("authority_limits")
    for name in LIMIT_TEXTS:
        if not _text(document.get(name)):
            raise CandidateInvalid("authority_limits:" + name)
    for name in LIMIT_LISTS:
        _texts(document.get(name), "authority_limits:" + name)
    if not isinstance(document.get("budget_policy"), dict):
        raise CandidateInvalid("authority_limits:budget_policy")
    policy = document.get("identity_policy")
    if not isinstance(policy, dict) or not isinstance(policy.get("family"), str) or type(policy.get("width")) is not int \
            or not 1 <= policy["width"] <= 6:  # The identity grammar admits no wider number.
        raise CandidateInvalid("authority_limits:identity_policy")
    snapshot = document.get("identity_snapshot")
    if not isinstance(snapshot, dict):
        raise CandidateInvalid("authority_limits:identity_snapshot")
    for name in ("active", "retired", "reserved"):
        _texts(snapshot.get(name, []), "authority_limits:identity_snapshot:" + name)
    existing = document.get("existing_decomposition", {})
    if not isinstance(existing, dict) or not all(_text(k) for k in existing):
        raise CandidateInvalid("authority_limits:existing_decomposition")
    for identities in existing.values():
        _texts(identities, "authority_limits:existing_decomposition")
    try:  # Every value the candidate copies or digests must be canonical JSON (no NaN, infinity, set or object).
        digest(_normalized(document))
    except (TypeError, ValueError, RecursionError) as error:
        raise CandidateInvalid("authority_limits:not_canonical_json") from error
    return document


def input_digest(inventory: InventorySnapshot | None, inspection: InspectionReport | None, design: DesignContract,
                 review_digest: str, plans: Mapping[str, dict | None], limits: object,
                 stages: Mapping[str, str | None]) -> str:
    """Binds every pinned input by value; mapping order never contributes. Persisted reservations are compiler state,
    not input: regenerating the same input keys the same pointer, and the candidate digest binds the identities."""
    try:
        bound = _normalized(_limits(limits))
    except CandidateInvalid as error:
        bound = "INVALID:" + str(error)  # A malformed value is identified by its refusal, never by repr.
    return digest({"inventory": inventory.digest if inventory else None,
                   "inspection": inspection.digest if inspection else None, "design": design.digest,
                   "review": review_digest,
                   "proof_plans": {r: p.get("digest") if isinstance(p, dict) else None for r, p in sorted(plans.items())},
                   "authority_limits": bound, "stages": {k: v for k, v in sorted(stages.items())}})


def _normalized(limits: dict) -> dict:
    """Identity sets are sets: their enumeration never contributes to a digest."""
    result = dict(limits)
    if isinstance(limits.get("identity_snapshot"), dict):
        result["identity_snapshot"] = {k: sorted(v, key=repr) if isinstance(v, list) else v
                                       for k, v in limits["identity_snapshot"].items()}
    if isinstance(limits.get("existing_decomposition"), dict):
        result["existing_decomposition"] = {k: sorted(v, key=repr) if isinstance(v, list) else v
                                            for k, v in limits["existing_decomposition"].items()}
    return result


def compile_initial(inventory: InventorySnapshot | None, inspection: InspectionReport | None, design: DesignContract,
                    review_digest: str, plans: Mapping[str, dict | None], authority_limits: object,
                    reservations: Mapping[str, str], stages: Mapping[str, str | None]
                    ) -> CompilationCandidate | CompilationHold:
    """Derive, conserve and validate; any unpinned input, gap or invalid result is a typed hold."""
    identity = input_digest(inventory, inspection, design, review_digest, plans, authority_limits, stages)
    try:
        limits = _limits(authority_limits)
    except CandidateInvalid as error:
        return hold(INITIAL, identity, [("INVALID_CANDIDATE", (str(error),))])
    findings: list = []
    requirements = _pinned(inventory, inspection, design, findings)
    if findings:
        return hold(INITIAL, identity, findings)
    existing = limits.get("existing_decomposition", {})
    decomposed = [f"{r}:{','.join(sorted(existing[r]))}" for r in requirements if existing.get(r)]
    if decomposed:
        return hold(INITIAL, identity, [("EXISTING_DECOMPOSITION", _ordered(decomposed))])

    try:
        obligations = {r: _obligations(requirements[r], design, plans.get(r), findings) for r in requirements}
    except CandidateInvalid as error:
        return hold(INITIAL, identity, [("INVALID_CANDIDATE", (str(error),))])
    assigned = _reserve(sorted(unit_key(r) for r in requirements), limits, reservations, findings)
    if findings:
        return hold(INITIAL, identity, findings)
    units = {r: assigned[unit_key(r)] for r in requirements}
    edges = _edges(requirements, units, existing, findings)
    capabilities = sorted(set(_design_values(design, "capabilities")))
    widened = [f"{units[r]}:required_capabilities:{c}" for r in requirements for c in capabilities
               if c not in limits["required_capabilities"]]
    if widened:
        findings.append(("BOUNDS_WIDENED", _ordered(widened)))
    if findings:
        return hold(INITIAL, identity, findings)

    contracts = {r: _contract(r, requirements[r], units[r], design, plans[r], inspection, limits, capabilities,
                              sorted({e["from"] for e in edges if e["to"] == units[r]}), obligations[r])
                 for r in requirements}
    mapping, reverse = _trace(obligations, contracts, units, findings)
    if findings:
        return hold(INITIAL, identity, findings)

    # The existing U7 validator is the post-derivation check; it never stands in for derivation.
    decisions = {d["id"]: d["statement"] for d in design.decisions if d["status"] == "FIXED"}
    known = set(limits["identity_snapshot"].get("active", []))
    validation_stages = {i: stages.get(i) or ("ACTIVE_SNAPSHOT" if i in known else None)
                         for i in {e["from"] for e in edges} - set(units.values())}
    candidate = {"mode": INITIAL, "requirements": sorted(requirements),
                 "obligations": [{"id": o["text"], "category": o["category"]} for r in sorted(obligations)
                                 for o in obligations[r]],
                 "units": [{"unit_key": unit_key(r), "contract": contracts[r]} for r in sorted(contracts)],
                 "edges": edges}
    report = validate(candidate, decisions, validation_stages)
    if isinstance(report, CompilationHold):
        return hold(INITIAL, identity, list(report.findings), report.detail)
    return _candidate(identity, requirements, units, contracts, edges, obligations, mapping, reverse, report,
                      inventory, inspection, design, review_digest, plans, limits, assigned, stages)


def _pinned(inventory, inspection, design, findings) -> dict[str, Requirement]:
    """The design's requirements at the exact inventory revision, each eligible in the inspection of that inventory."""
    if inventory is None or inspection is None:
        findings.append(("INPUT_UNPINNED", tuple(n for n, v in (("inventory", inventory), ("inspection", inspection))
                                                 if v is None)))
        return {}
    if inspection.inventory_digest != inventory.digest:
        findings.append(("INPUT_UNPINNED", (f"inspection:{inspection.inventory_digest}<>inventory:{inventory.digest}",)))
        return {}
    current: dict[str, list[Requirement]] = {}
    for requirement in inventory.current:
        current.setdefault(requirement.requirement_id, []).append(requirement)
    reports = {r.requirement_id: r for r in inspection.requirements}
    pinned, unpinned, unresolved = {}, [], []
    for rid, revision in design.requirements.items():
        definitions = current.get(rid, [])
        if len(definitions) != 1 or not _same(definitions[0].revision, revision):
            unpinned.append(f"{rid}:design={revision}:inventory={[d.revision for d in definitions]}")
            continue
        report = reports.get(rid)
        if report is None or report.revision != definitions[0].revision:
            unpinned.append(f"{rid}:inspection")
        elif report.preparation != ELIGIBLE:
            unresolved += [rid, *report.finding_ids]
        else:
            pinned[rid] = definitions[0]
    if unpinned:
        findings.append(("INPUT_UNPINNED", _ordered(unpinned)))
    if unresolved:
        findings.append(("UNRESOLVED_AUTHORITY", _ordered(unresolved)))
    return pinned


def _design_values(design: DesignContract, name: str) -> list[str]:
    entry = design.fields.get(name) or {}
    return list(entry.get("value") or ())


def _obligations(requirement: Requirement, design: DesignContract, plan: dict | None, findings) -> list[dict]:
    """The frozen four-category inventory of one unit: id, category, verbatim clause and its contract field.

    plan is the retained U4 proof-plan document of this requirement (plan_document plus its digest)."""
    rid = requirement.requirement_id
    field = dict(CATEGORY_FIELDS)
    frozen = [{"id": rid, "category": "requirement", "text": rid}]
    acceptance = {}
    for clause in items(fields(requirement.semantic).get("Acceptance", "")):
        acceptance[clause.split(":", 1)[0].strip()] = clause
        frozen.append({"id": clause.split(":", 1)[0].strip(), "category": "acceptance", "text": clause})
    if plan is None:
        findings.append(("UNMAPPED_OBLIGATION", (f"{rid}:proof_plan",)))
        return frozen
    if not _plan_shape(plan):
        raise CandidateInvalid(f"{rid}:proof_plan")
    proofs = sorted(plan["obligations"], key=lambda o: o["obligation_id"])
    stale = [] if plan["requirement_ref"]["logical_id"] == rid and _same(
        requirement.revision, plan["requirement_ref"]["revision_digest"]) else [f"{rid}:proof_plan:requirement"]
    if plan["design_ref"]["logical_id"] != design.design_key \
            or not _same(design.digest, plan["design_ref"]["revision_digest"]):
        stale.append(f"{rid}:proof_plan:design")
    stale += [f"{rid}:{o['obligation_id']}" for o in proofs if not _same(requirement.revision, o["requirement_revision"])]
    if stale:
        findings.append(("INPUT_UNPINNED", _ordered(stale)))
    proven = {o["predicate"]["acceptance_id"] for o in proofs}
    unproven = [f"{a}:verification" for a in acceptance if a not in proven]
    if unproven:
        findings.append(("UNMAPPED_OBLIGATION", _ordered(unproven)))
    invented = [o["obligation_id"] for o in proofs if o["predicate"]["acceptance_id"] not in acceptance]
    if invented:
        findings.append(("OBLIGATION_INVENTED", _ordered(invented)))
    for obligation in proofs:
        oid, predicate = obligation["obligation_id"], obligation["predicate"]
        frozen.append({"id": oid, "category": "verification", "text": f"{oid}: {predicate['statement']}"})
        duty = predicate["decision_record"] if predicate["kind"] == JUDGMENT else "; ".join(predicate["evidence_schema"])
        frozen.append({"id": oid + "#evidence", "category": "evidence", "text": f"{oid}#evidence: {duty}"})
    for text in sorted(set(_design_values(design, "evidence"))):
        frozen.append({"id": f"{design.design_key}#evidence:{digest(text)[7:19]}", "category": "evidence",
                       "text": text})
    return [{**o, "unit_key": unit_key(rid), "field": field[o["category"]]} for o in frozen]


def _plan_shape(plan: object) -> bool:
    refs = ("requirement_ref", "design_ref")
    if not isinstance(plan, dict) or not isinstance(plan.get("obligations"), list) or not _text(plan.get("digest")) \
            or not all(isinstance(plan.get(r), dict) and all(isinstance(plan[r].get(k), str)
                                                             for k in ("logical_id", "revision_digest")) for r in refs):
        return False
    for entry in plan["obligations"]:
        predicate = entry.get("predicate") if isinstance(entry, dict) else None
        if not isinstance(predicate, dict) or not all(_text(entry.get(k)) for k in ("obligation_id",
                                                                                     "requirement_revision")) \
                or not all(isinstance(predicate.get(k), str) for k in ("acceptance_id", "statement", "kind",
                                                                         "decision_record")) \
                or not isinstance(predicate.get("evidence_schema"), (list, tuple)) \
                or not all(isinstance(v, str) for v in predicate["evidence_schema"]):
            return False
    return True


def _reserve(keys: list[str], limits: dict, reservations: Mapping[str, str], findings) -> dict[str, str]:
    """INITIAL_IDENTITY_RESERVATION_v1; collisions and exhaustion fail closed, never renumber. An identity of an
    existing decomposition is occupied whether or not the snapshot lists it."""
    policy, snapshot = limits["identity_policy"], limits["identity_snapshot"]
    family, width = policy["family"], policy["width"]
    occupied = {i for name in ("active", "retired") for i in snapshot.get(name, [])}
    occupied |= {i for ids in limits.get("existing_decomposition", {}).values() for i in ids}
    taken = occupied | set(snapshot.get("reserved", [])) | set(reservations.values())
    assigned, grammar, collisions, exhausted = {}, [], [], []
    for key in keys:  # Stable unit_key value order: never input enumeration.
        identity = reservations.get(key)
        if identity is not None:
            if not identity_valid(identity, policy):
                grammar.append(f"{key}:{identity}")
            elif identity in occupied or list(reservations.values()).count(identity) > 1:
                # A reserved number found active or retired belongs to other work: its own decomposition held above.
                collisions.append(f"{key}:{identity}")
            assigned[key] = identity
            continue
        number = next((n for n in range(1, 10 ** width) if f"{family}-{n:0{width}d}" not in taken), None)
        if number is None:
            exhausted.append(f"{key}:{family}/{width}")
            continue
        identity = f"{family}-{number:0{width}d}"
        if re.match(IDENTITY_GRAMMAR, identity) is None:
            grammar.append(f"{key}:{identity}")
        taken.add(identity)
        assigned[key] = identity
    for code, refs in (("IDENTITY_GRAMMAR", grammar), ("IDENTITY_COLLISION", collisions),
                       ("IDENTITY_EXHAUSTED", exhausted)):
        if refs:
            findings.append((code, _ordered(refs)))
    return assigned


def _edges(requirements: dict[str, Requirement], units: dict[str, str], existing: dict, findings) -> list[dict]:
    """Requirement dependencies become DONE edges; a dependency with no unit or decomposition cannot be invented."""
    edges, missing = set(), []
    for rid, requirement in requirements.items():
        for dependency in requirement.dependencies:
            sources = [units[dependency]] if dependency in units else list(existing.get(dependency) or ())
            if not sources:
                missing.append(f"{rid}:{dependency}")
            edges |= {(source, units[rid]) for source in sources}
    if missing:
        findings.append(("MISSING_ENDPOINT", _ordered(missing)))
    return [{"from": s, "to": t, "predicate": DONE} for s, t in sorted(edges)]


def _contract(rid, requirement, identity, design, plan, inspection, limits, capabilities, dependencies,
              obligations) -> dict:
    """Every field from one named source; the version binds exactly the sources of this unit."""
    labelled = fields(requirement.semantic)
    clauses = {name: [o["text"] for o in obligations if o["field"] == name] for _, name in CATEGORY_FIELDS}
    sources = [f"requirement:{rid}@{requirement.revision}", f"design:{design.design_key}@{design.digest}",
               f"proof-plan:{rid}@{plan['digest']}", f"inspection:{inspection.digest}"]
    non_goals = items(labelled.get("Non-goals", ""))
    document = {
        "identity": identity, "intent": labelled.get("Intent", ""),
        "satisfied_requirement_ids": clauses["satisfied_requirement_ids"],
        "fixed_decisions": sorted(f"{d['id']}: {d['statement']}" for d in design.decisions if d["status"] == "FIXED"),
        "authorized_scope": items(labelled.get("Scope", "")), "excluded_scope": non_goals,
        "dependencies": dependencies, "required_capabilities": capabilities,
        "budget_policy": dict(limits["budget_policy"]), "retry_policy": limits["retry_policy"],
        "completion_criteria": clauses["completion_criteria"],
        "verification_obligations": clauses["verification_obligations"],
        "required_evidence": clauses["required_evidence"],
        "non_goals": non_goals + [v for v in sorted(set(_design_values(design, "non_goals"))) if v not in non_goals],
        "candidate_custody_requirements": list(limits["candidate_custody_requirements"]),
        "release_policy": limits["release_policy"], "authority_issuer": limits["authority_issuer"],
        "authority_references": sorted(set(limits["authority_references"])) + sources,
        "target_repositories": sorted(set(limits["target_repositories"])),
        "baselines": sorted(set(limits["baselines"])),
        "required_closure_actions": list(limits["required_closure_actions"]),
        "stop_escalation_conditions": list(limits["stop_escalation_conditions"])}
    return {"version": digest(document), **document}


def _trace(obligations, contracts, units, findings) -> tuple[list, list]:
    """Forward: every frozen obligation has an explicit extent. Reverse: every obligation clause of a contract traces
    to a frozen obligation of its own unit. Either gap holds; mapping is never satisfaction."""
    mapping, reverse, unmapped, invented = [], [], [], []
    for rid, frozen in obligations.items():
        contract = contracts[rid]
        for obligation in frozen:
            extents = [{"identity": units[rid], "field": obligation["field"]}] \
                if obligation["text"] in contract[obligation["field"]] else []
            if not extents:
                unmapped.append(f"{rid}:{obligation['id']}")
            mapping.append({"obligation_id": obligation["id"], "category": obligation["category"],
                            "unit_key": obligation["unit_key"], "extents": extents})
        for _, name in CATEGORY_FIELDS:
            for clause in contract[name]:
                origin = [o["id"] for o in frozen if o["field"] == name and o["text"] == clause]
                if not origin:
                    invented.append(f"{units[rid]}:{name}:{clause}")
                reverse += [{"identity": units[rid], "field": name, "obligation_id": o} for o in origin]
    for code, refs in (("UNMAPPED_OBLIGATION", unmapped), ("OBLIGATION_INVENTED", invented)):
        if refs:
            findings.append((code, _ordered(refs)))
    key = lambda row: digest(row)
    return sorted(mapping, key=key), sorted(reverse, key=key)


def _candidate(identity, requirements, units, contracts, edges, obligations, mapping, reverse,
               report: ValidationReport, inventory, inspection, design, review_digest, plans, limits, assigned,
               stages) -> CompilationCandidate:
    validation = report.document()
    body = {
        "schema_version": 1, "record_kind": "CompilationCandidate", "mode": INITIAL, "provenance": DERIVED,
        "derivation_rule": DERIVATION_RULE, "identity_rule": IDENTITY_RULE, "budget_rule": BUDGET_RULE,
        "rationale": RATIONALE, "labels": list(CANDIDATE_LABELS),
        "admitted_for_assessment": True,
        "inputs": {"inventory": inventory.digest, "inspection": inspection.digest,
                   "design": {"design_key": design.design_key, "design_digest": design.digest,
                              "review_digest": review_digest},
                   "requirements": {r: requirements[r].revision for r in sorted(requirements)},
                   "proof_plans": {r: plans[r]["digest"] for r in sorted(requirements)},
                   "authority_limits": digest(_normalized(limits))},
        "units": [{"unit_key": unit_key(r), "identity": units[r], "content_digest": validation_digest(validation, units[r]), "contract": contracts[r]}
                  for r in sorted(requirements)],
        "edges": edges,
        "external_predecessors": [{"identity": s, "stage": stages.get(s)}
                                  for s in _ordered(e["from"] for e in edges if e["from"] not in units.values())],
        "obligations": [{k: o[k] for k in ("id", "category", "unit_key", "field", "text")}
                        for r in sorted(obligations) for o in obligations[r]],
        "mapping": mapping, "reverse": reverse,
        "coverage": validation["obligation_coverage"], "coverage_is_not_satisfaction": True,
        "validation": {"record_kind": validation["record_kind"], "labels": validation["labels"],
                       "candidate_digest": report.candidate_digest, "report_digest": digest(validation)},
        "reservations": dict(sorted(assigned.items())), "non_claims": list(NON_CLAIMS)}
    return CompilationCandidate(digest(body), identity, tuple(sorted(assigned.items())), body)


def validation_digest(validation: dict, identity: str) -> str:
    """The BiuContract content_digest the U7 validator computed for one unit."""
    return next(u["content_digest"] for u in validation["units"] if u["identity"] == identity)


def is_initial_compilation(document: object) -> bool:
    """The completion predicate: only a derived CompilationCandidate counts; a U7 report of a supplied candidate
    (VALIDATION_ONLY, SUPPLIED_CANDIDATE_NOT_DERIVED) never does, whatever its units."""
    return isinstance(document, dict) and document.get("record_kind") == "CompilationCandidate" \
        and document.get("provenance") == DERIVED and document.get("mode") == INITIAL \
        and document.get("derivation_rule") == DERIVATION_RULE

