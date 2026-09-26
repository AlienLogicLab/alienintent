"""Compiler validation (U7): pure checks over supplied candidates; nothing is derived, reserved or applied here.

Two candidate modes are validated. INITIAL is a supplied candidate obligation mapping; admission proves validation
only (VALIDATION_ONLY) and never that anything derived it (U8). SPLIT_REPLAN is a frozen split proposal, the value a
future SplitTransaction.prepare would return; admission is "admitted for assessment" only, never apply.

The split rules are the Phase 5 candidate mechanisms carried forward by the SF-REQ-013 design (retained Integration
Parent, frozen/reverse mapping, identity-preserving graph rules, fixed-width grammar, exact-payload authority binding)
and are labelled PHASE5_CANDIDATE_MECHANISMS_NOT_INDEPENDENTLY_DESIGN_VERIFIED. Hold reason codes are a labelled
vocabulary (COMPILATION_HOLD_CODES_v1), never lifecycle states or Agent Ready dispositions. Every result is a
function of the supplied values only: report items are ordered by value, never by input enumeration.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Mapping

from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy, ContractValidationError

INITIAL, SPLIT_REPLAN = "INITIAL", "SPLIT_REPLAN"
DONE = "DONE"
VALIDATION_ONLY = "VALIDATION_ONLY"
CANDIDATE_RULES = "PHASE5_CANDIDATE_MECHANISMS_NOT_INDEPENDENTLY_DESIGN_VERIFIED"
PREDICATED, HISTORICAL_EDGE_SET = "PREDICATED", "HISTORICAL_EDGE_SET"
CHILD, INTEGRATION_PARENT = "CHILD", "INTEGRATION_PARENT"
CURRENT = "CURRENT"
# Candidate BIU grammar (C#/contracts/2/identities), full-string ASCII match; the configured policy binds family/width.
IDENTITY_GRAMMAR = r"\A(?:(?:PG|PY)-[0-9]{2}|WO-[0-9]{6})(?:[A-Z])?\Z"
CATEGORY_FIELDS = (("requirement", "satisfied_requirement_ids"), ("acceptance", "completion_criteria"),
                   ("verification", "verification_obligations"), ("evidence", "required_evidence"))
BUDGET_LIMITS = ("maximum_attempts", "hard_wall_clock_seconds", "retry_limit", "concurrency_limit", "cancellation_limit")
SUBSET_FIELDS = ("required_capabilities", "target_repositories", "authorized_scope")
NON_CLAIMS = ("INITIAL_DERIVATION", "SPLIT_PREPARE_OR_APPLY", "IDENTITY_RESERVATION_OR_ALLOCATION",
              "INVALIDATION_RECORDS", "SF_REQ_015_LINT_OR_ASSESSMENT", "SF-REQ-013-AC-06", "SF-REQ-013-AC-07",
              "SF-REQ-013-AC-08")
# Priority of the primary reason when one candidate carries several findings; every finding is still reported.
HOLD_CODES = (
    "DESIGN_HOLD", "UNRESOLVED_AUTHORITY", "INVALID_CANDIDATE", "SPLIT_UNAUTHORIZED", "SPLIT_AUTHORITY_STALE",
    "DONE_ORIGINAL", "ORIGINAL_GRAPH_MISMATCH", "INCOMPLETE_CONTRACT", "IDENTITY_REWRITTEN", "IDENTITY_GRAMMAR", "IDENTITY_COLLISION",
    "LINEAGE_MISSING", "LINEAGE_INCONSISTENT", "MISSING_ENDPOINT", "UNSPECIFIED_PREDICATE", "CYCLE",
    "EDGE_DISAGREEMENT", "DEPENDENCY_UNSATISFIED", "EDGE_REDIRECTED", "EDGE_PRUNED", "PREDICATE_WEAKENED",
    "PREREQUISITE_NOT_COPIED", "CHILD_PARENT_EDGE_MISSING", "INTER_CHILD_EDGE_UNAUTHORIZED", "EDGE_UNAUTHORIZED",
    "DECISION_CONFLICT", "OBLIGATION_LOST", "PARTIAL_MAPPING", "INTEGRATION_DUTY_DROPPED", "CLAUSE_NOT_VERBATIM",
    "OBLIGATION_INVENTED", "UNMAPPED_OBLIGATION", "BOUNDS_WIDENED", "INVALIDATION_INCOMPLETE",
    "ASSESSMENT_HISTORY_MUTATED", "STALE_ASSESSMENT_AS_CURRENT", "PERSISTENCE_CONFLICT",
    # U8 initial compilation, appended so no existing code changes rank.
    "INPUT_UNPINNED", "EXISTING_DECOMPOSITION", "IDENTITY_EXHAUSTED")
_LIST_FIELDS = ("units", "obligations", "edges", "requirements", "original_edges", "original_obligations", "results",
                "result_edges", "authorized_edges", "mapping", "reverse", "invalidation", "prior_assessments",
                "elaboration_approvals")


class CandidateInvalid(ValueError):
    """The supplied document does not have the candidate shape; the path names the offending element."""


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: object) -> str:
    return "sha256:" + sha256(canonical(value).encode()).hexdigest()


def _ordered(values) -> tuple:
    """Report order is value order; it never depends on input enumeration."""
    return tuple(sorted(set(values)))


def normalized(document: dict) -> dict:
    """Set-valued top-level lists in value order, so a permuted enumeration has one canonical form."""
    return {k: sorted(v, key=canonical) if k in _LIST_FIELDS and isinstance(v, list) else v
            for k, v in document.items()}


def candidate_digest(document: object) -> str:
    try:
        return digest(normalized(document) if isinstance(document, dict) else document)
    except (TypeError, ValueError):
        return digest(repr(document))


def payload_digest(proposal: dict) -> str:
    """The exact payload an authority record binds: the normalized proposal without the authority itself."""
    return digest(normalized({k: v for k, v in proposal.items() if k != "authority"}))


def original_revision(original: dict) -> str:
    return digest(original)


def graph_revision(edges: list) -> str:
    return digest(sorted(edges, key=canonical))


@dataclass(frozen=True)
class DependencyEdge:
    source: str
    target: str
    predicate: str | None

    @property
    def ref(self) -> str:
        return f"{self.source}->{self.target}"


@dataclass(frozen=True)
class CompilationHold:
    reason_code: str
    affected_refs: tuple[str, ...]
    mode: str
    candidate_digest: str
    detail: str = ""
    findings: tuple[tuple[str, tuple[str, ...]], ...] = ()

    def document(self) -> dict:
        return {"schema_version": 1, "record_kind": "CompilationHold", "mode": self.mode,
                "candidate_digest": self.candidate_digest, "reason_code": self.reason_code,
                "affected_refs": list(self.affected_refs), "detail": self.detail,
                "findings": [{"reason_code": c, "affected_refs": list(r)} for c, r in self.findings],
                "vocabulary": "COMPILATION_HOLD_CODES_v1", "transition": "NONE"}


@dataclass(frozen=True)
class ValidationReport:
    mode: str
    candidate_digest: str
    body: dict

    admitted_for_assessment = True

    def document(self) -> dict:
        return {"schema_version": 1, "record_kind": "ValidationReport", "mode": self.mode,
                "candidate_digest": self.candidate_digest, "admitted_for_assessment": True,
                "labels": [VALIDATION_ONLY, CANDIDATE_RULES] if self.mode == SPLIT_REPLAN else [VALIDATION_ONLY],
                "non_claims": list(NON_CLAIMS), **self.body}


def hold(mode: str, candidate: str, findings: list[tuple[str, tuple[str, ...]]], detail: str = "") -> CompilationHold:
    """One typed hold: the primary reason by fixed priority, with every finding retained in value order."""
    merged: dict[str, set[str]] = {}
    for code, refs in findings:
        merged.setdefault(code, set()).update(refs)
    ranked = tuple((code, _ordered(merged[code])) for code in HOLD_CODES if code in merged)
    return CompilationHold(ranked[0][0], ranked[0][1], mode, candidate, detail, ranked)


# --- document values --------------------------------------------------------------------------------------


def _list(document: dict, name: str, path: str = "") -> list:
    value = document.get(name, [])
    if not isinstance(value, list):
        raise CandidateInvalid(path + name)
    return value


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _where(path: str, entry: object) -> str:
    """Name an offending element by value, never by its enumeration index."""
    try:
        return f"{path}:{digest(entry)}"
    except (TypeError, ValueError):
        return f"{path}:unreadable"


def _texts(value: object, path: str) -> list:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise CandidateInvalid(path)
    return value


def edges_of(values: list, path: str) -> tuple[DependencyEdge, ...]:
    """Edges by value; a repeated (from, to) pair is refused, never resolved by enumeration order."""
    edges, seen = [], set()
    for entry in values:
        if not isinstance(entry, dict) or not _text(entry.get("from")) or not _text(entry.get("to")) \
                or not isinstance(entry.get("predicate"), (str, type(None))):
            raise CandidateInvalid(_where(path, entry))
        key = (entry["from"], entry["to"])
        if key in seen:
            raise CandidateInvalid(f"{path}:duplicate:{key[0]}->{key[1]}")
        seen.add(key)
        edges.append(DependencyEdge(entry["from"], entry["to"], entry.get("predicate")))
    return tuple(edges)


def contract_from_payload(document: object) -> BiuContract:
    """Build the existing BiuContract value; a missing or empty binding field raises ContractValidationError."""
    if not isinstance(document, dict):
        raise ContractValidationError("contract is required")
    names = [n for n in BiuContract.__dataclass_fields__ if n != "content_digest"]
    unknown = sorted(set(document) - set(names))
    if unknown:
        raise ContractValidationError(f"{unknown[0]} is not a contract field")
    for name in names:
        if name not in document and name != "dependencies":
            raise ContractValidationError(f"{name} is required")
    budget = document["budget_policy"]
    if not isinstance(budget, dict):
        raise ContractValidationError("budget_policy is required")
    values = {n: tuple(document.get(n) or ()) if isinstance(document.get(n, []), list) else document[n]
              for n in names if n != "budget_policy"}
    try:
        return BiuContract(budget_policy=BudgetPolicy(**{**budget, "hard_required_dimensions": tuple(
            budget.get("hard_required_dimensions") or ())}), **values)
    except TypeError as error:
        raise ContractValidationError("budget_policy is required") from error


def _field(error: ContractValidationError) -> str:
    message = str(error)
    return message.split(" ", 1)[0] if " is " in message and not message.startswith("budget") else "budget_policy"


def _body(unit: dict) -> str:
    """The clause text an obligation extent is compared against: document bytes, or the contract's clauses."""
    if isinstance(unit.get("body"), str):
        return unit["body"]
    contract = unit.get("contract")
    if not isinstance(contract, dict):
        return ""
    return "\n".join(v for value in contract.values() for v in (value if isinstance(value, list) else [value])
                     if isinstance(v, str))


def verbatim(clause: str, body: str) -> bool:
    """Byte-exact clause comparison; no normalization and no semantic inference (U-8, N-3)."""
    return clause in body


def holds_clause(clause: str, unit: dict) -> bool:
    """A document clause occurs byte-exactly; a contract clause must equal one whole contract entry."""
    if isinstance(unit.get("body"), str):
        return verbatim(clause, unit["body"])
    return verbatim("\n" + clause + "\n", "\n" + _body(unit) + "\n")


def identity_valid(identity: object, policy: Mapping[str, object]) -> bool:
    family, width = policy["family"], policy["width"]
    return (isinstance(identity, str) and identity.isascii() and re.match(IDENTITY_GRAMMAR, identity) is not None
            and re.match(rf"\A{re.escape(family)}-[0-9]{{{width}}}", identity) is not None)


def linked_requirements(document: dict, original: object = None) -> set[str]:
    """Every requirement a candidate touches: declared, carried by any unit contract, or a requirement obligation."""
    linked = set(_texts(document.get("requirements", []), "requirements"))
    entries = _list(document, "units") + _list(document, "results")
    contracts = [e.get("contract") for e in entries if isinstance(e, dict)]
    contracts.append(original.get("contract") if isinstance(original, dict) else None)
    for contract in contracts:
        if isinstance(contract, dict):
            linked |= set(_texts(contract.get("satisfied_requirement_ids", []), "satisfied_requirement_ids"))
    for entry in _list(document, "obligations") + _list(document, "original_obligations"):
        if isinstance(entry, dict) and "requirement" in (entry.get("category"), entry.get("kind")) \
                and isinstance(entry.get("id"), str):
            linked.add(entry["id"])
    return linked


# --- shared checks ----------------------------------------------------------------------------------------


def graph_findings(nodes: set[str], known: set[str], edges: tuple[DependencyEdge, ...],
                   predicates_required: bool = True) -> list[tuple[str, tuple[str, ...]]]:
    """Missing endpoints, predicate-free edges and every edge that lies on a cycle, by edge ref."""
    findings = []
    missing = [e.ref for e in edges if e.source not in nodes | known or e.target not in nodes | known]
    if missing:
        findings.append(("MISSING_ENDPOINT", _ordered(missing)))
    unspecified = [e.ref for e in edges if not _text(e.predicate)]
    if predicates_required and unspecified:
        findings.append(("UNSPECIFIED_PREDICATE", _ordered(unspecified)))
    successors: dict[str, set[str]] = {}
    for edge in edges:
        successors.setdefault(edge.source, set()).add(edge.target)

    def reaches(start: str, goal: str) -> bool:
        seen, frontier = set(), [start]
        while frontier:
            node = frontier.pop()
            if node == goal:
                return True
            if node not in seen:
                seen.add(node)
                frontier.extend(successors.get(node, ()))
        return False

    cyclic = [e.ref for e in edges if reaches(e.target, e.source)]
    if cyclic:
        findings.append(("CYCLE", _ordered(cyclic)))
    return findings


def dependency_authority(units: dict[str, dict], edges: tuple[DependencyEdge, ...], stages: Mapping[str, str | None],
                         projection: Mapping[str, str], require_done: bool = True) -> list[tuple[str, tuple[str, ...]]]:
    """013-dependency-authority: declared edges must agree, and only a DONE lifecycle stage satisfies a predecessor.

    Issue open/closed projection is never lifecycle authority: an open DONE predecessor is satisfied and a closed
    nonterminal one is not. Unknown sources are left to the endpoint check. An omitted dependencies field declares
    none, so every incoming edge disagrees. A split is planning, not execution eligibility: it is validated with
    require_done False (DEPENDENCY_SATISFACTION_INITIAL_ONLY), and the declared-edge rule still applies.
    """
    findings = []
    for identity, unit in units.items():
        if not unit:
            continue  # A result with no contract value (historical Markdown) declares no edges to compare.
        declared = unit.get("dependencies", [])
        if not isinstance(declared, list) or not all(isinstance(d, str) for d in declared):
            raise CandidateInvalid(f"{identity}:dependencies")
        incoming = {e.source for e in edges if e.target == identity}
        disagreement = [f"{identity}:{d}" for d in declared if d not in incoming]
        disagreement += [f"{identity}:{s}" for s in incoming if s not in declared]
        if disagreement:
            findings.append(("EDGE_DISAGREEMENT", _ordered(disagreement)))
    unsatisfied = []
    for edge in edges if require_done else ():
        if edge.source in units or stages.get(edge.source) is None:
            continue
        if stages.get(edge.source) != DONE:
            unsatisfied.append(edge.source)
    if unsatisfied:
        findings.append(("DEPENDENCY_UNSATISFIED", _ordered(unsatisfied)))
    return findings


def decision_findings(units: dict[str, BiuContract], decisions: Mapping[str, str]) -> list:
    """A fixed decision must name a FIXED decision of the verified design with the identical statement (U-8)."""
    conflicts = []
    for identity, contract in units.items():
        for text in contract.fixed_decisions:
            key, _, statement = text.partition(": ")
            if key not in decisions:
                conflicts.append(f"{identity}:{text} <> design:ABSENT")
            elif decisions[key] != statement:
                conflicts.append(f"{identity}:{text} <> design:{key}: {decisions[key]}")
    return [("DECISION_CONFLICT", _ordered(conflicts))] if conflicts else []


def _contracts(units: dict[str, dict], findings: list) -> dict[str, BiuContract]:
    contracts = {}
    for identity, unit in units.items():
        try:
            contracts[identity] = contract_from_payload(unit)
        except ContractValidationError as error:
            findings.append(("INCOMPLETE_CONTRACT", (f"{identity}:{_field(error)}",)))
            continue
    return contracts


# --- INITIAL ----------------------------------------------------------------------------------------------


def initial_units(candidate: dict) -> dict[str, dict]:
    units = {}
    for unit in _list(candidate, "units"):
        contract = unit.get("contract") if isinstance(unit, dict) else None
        if not isinstance(contract, dict) or not _text(contract.get("identity")):
            raise CandidateInvalid(_where("units", unit))
        if contract["identity"] in units:
            raise CandidateInvalid("units:duplicate:" + contract["identity"])
        units[contract["identity"]] = contract
    return units


UNREADABLE = (TypeError, ValueError, AttributeError, KeyError)


def validate(candidate: object, design_decisions: Mapping[str, str],
             stages: Mapping[str, str | None]) -> ValidationReport | CompilationHold:
    """Validate a supplied INITIAL candidate; an unreadable value is a typed hold, never an exception."""
    try:
        return _validate(candidate, design_decisions, stages)
    except UNREADABLE as error:
        return hold(INITIAL, candidate_digest(candidate), [("INVALID_CANDIDATE", ("unreadable:" + type(error).__name__,))])


def _validate(candidate: object, design_decisions: Mapping[str, str],
              stages: Mapping[str, str | None]) -> ValidationReport | CompilationHold:
    """Contract completeness, obligation coverage, graph and fixed decisions of a supplied INITIAL candidate."""
    identity = candidate_digest(candidate)
    try:
        if not isinstance(candidate, dict) or candidate.get("mode") != INITIAL:
            raise CandidateInvalid("mode")
        units = initial_units(candidate)
        edges = edges_of(_list(candidate, "edges"), "edges")
        obligations = _list(candidate, "obligations")
        _texts(candidate.get("requirements", []), "requirements")
        for entry in obligations:
            if not isinstance(entry, dict) or not _text(entry.get("id")) or not isinstance(entry.get("category"), str) \
                    or entry["category"] not in dict(CATEGORY_FIELDS):
                raise CandidateInvalid(_where("obligations", entry))
    except CandidateInvalid as error:
        return hold(INITIAL, identity, [("INVALID_CANDIDATE", (str(error),))])
    findings: list = []
    contracts = _contracts(units, findings)
    grammar = [u for u in units if re.match(IDENTITY_GRAMMAR, u) is None]
    if grammar:
        findings.append(("IDENTITY_GRAMMAR", _ordered(grammar)))
    known = {i for i, s in stages.items() if s is not None}
    findings += graph_findings(set(units), known, edges)
    findings += decision_findings(contracts, design_decisions)
    coverage, uncovered = {}, []
    for category, field in CATEGORY_FIELDS:
        wanted = [o["id"] for o in obligations if o["category"] == category]
        covered = [o for o in wanted if any(o in getattr(c, field) for c in contracts.values())]
        uncovered += [o for o in wanted if o not in covered]
        coverage[category] = {"total": len(set(wanted)), "covered": len(set(covered))}
    if uncovered:
        findings.append(("UNMAPPED_OBLIGATION", _ordered(uncovered)))
    if findings:
        return hold(INITIAL, identity, findings)
    return ValidationReport(INITIAL, identity, {
        "units": [{"identity": u, "content_digest": contracts[u].content_digest} for u in _ordered(units)],
        "edges": [{"from": s, "to": t, "predicate": p} for s, t, p in
                  _ordered((e.source, e.target, e.predicate) for e in edges)],
        "obligation_coverage": coverage, "coverage_is_not_satisfaction": True,
        "external_predecessors": [{"identity": s, "stage": stages.get(s)} for s in
                                  _ordered(e.source for e in edges if e.source not in units)],
        "provenance": "SUPPLIED_CANDIDATE_NOT_DERIVED"})


# --- SPLIT_REPLAN -----------------------------------------------------------------------------------------


def split_units(proposal: dict) -> dict[str, dict]:
    results = {}
    for result in _list(proposal, "results"):
        if not isinstance(result, dict) or not _text(result.get("identity")) \
                or result.get("role") not in (CHILD, INTEGRATION_PARENT) or result["identity"] in results \
                or not isinstance(result.get("split_from"), (str, type(None))) \
                or not isinstance(result.get("operation_id"), (str, type(None))) \
                or not isinstance(result.get("contract", {}), dict) or not isinstance(result.get("body", ""), str):
            raise CandidateInvalid(_where("results", result))
        _texts(result.get("children", []), "children")
        results[result["identity"]] = result
    return results


def validate_split(proposal: object, original: object, authority_limits: Mapping[str, object],
                   identity_policy: Mapping[str, object], stages: Mapping[str, str | None],
                   history: Mapping[str, str | None]) -> ValidationReport | CompilationHold:
    """Validate a frozen split proposal against the pinned original; nothing is prepared, reserved or applied.

    history maps each prior-assessment locator to the digest its retained record has now (None when unreadable).
    An unreadable value is a typed hold, never an exception.
    """
    try:
        return _validate_split(proposal, original, authority_limits, identity_policy, stages, history)
    except UNREADABLE as error:
        return hold(SPLIT_REPLAN, candidate_digest(proposal),
                    [("INVALID_CANDIDATE", ("unreadable:" + type(error).__name__,))])


def _validate_split(proposal: object, original: object, authority_limits: Mapping[str, object],
                    identity_policy: Mapping[str, object], stages: Mapping[str, str | None],
                    history: Mapping[str, str | None]) -> ValidationReport | CompilationHold:
    identity = candidate_digest(proposal)
    try:
        if not isinstance(proposal, dict) or proposal.get("mode") != SPLIT_REPLAN:
            raise CandidateInvalid("mode")
        if not isinstance(original, dict) or not _text(original.get("identity")):
            raise CandidateInvalid("original")
        if not _text(proposal.get("operation_id")):
            raise CandidateInvalid("operation_id")
        if not isinstance(identity_policy.get("family"), str) or type(identity_policy.get("width")) is not int:
            raise CandidateInvalid("identity_policy")
        _texts(authority_limits.get("issuers", []), "authority_limits")
        anchor = None
        if "contract" in original:
            try:
                anchor = contract_from_payload(original["contract"])
            except ContractValidationError as error:
                raise CandidateInvalid("original:" + _field(error)) from error
        results = split_units(proposal)
        original_edges = edges_of(_list(proposal, "original_edges"), "original_edges")
        result_edges = edges_of(_list(proposal, "result_edges"), "result_edges")
        authorized = edges_of(_list(proposal, "authorized_edges"), "authorized_edges")
        semantics = proposal.get("graph_semantics")
        if semantics not in (PREDICATED, HISTORICAL_EDGE_SET):
            raise CandidateInvalid("graph_semantics")
        obligations = {}
        for entry in _list(proposal, "original_obligations"):
            if not isinstance(entry, dict) or not _text(entry.get("id")) or not isinstance(entry.get("text"), str) \
                    or entry["id"] in obligations:
                raise CandidateInvalid(_where("original_obligations", entry))
            obligations[entry["id"]] = entry
        mapping, reverse = _list(proposal, "mapping"), _list(proposal, "reverse")
        for entry in mapping:
            if not isinstance(entry, dict) or not isinstance(entry.get("obligation_id"), str):
                raise CandidateInvalid(_where("mapping", entry))
            _texts(entry.get("maps_to"), "mapping:maps_to")
        for entry in reverse:
            if not isinstance(entry, dict) or not all(isinstance(entry.get(k), str)
                                                      for k in ("destination", "obligation_id", "origin")):
                raise CandidateInvalid(_where("reverse", entry))
        for entry in _list(proposal, "elaboration_approvals"):
            if not isinstance(entry, dict) or not isinstance(entry.get("obligation_id"), str):
                raise CandidateInvalid(_where("elaboration_approvals", entry))
        for entry in _list(proposal, "prior_assessments"):
            if not isinstance(entry, dict) or not isinstance(entry.get("ref"), dict):
                raise CandidateInvalid(_where("prior_assessments", entry))
        _texts(proposal.get("invalidation", []), "invalidation")
        snapshot = proposal.get("identity_snapshot") or {}
        bindings = proposal.get("destination_bindings") or {}
        if not isinstance(snapshot, dict) or not isinstance(bindings, dict) \
                or not all(isinstance(v, (str, type(None))) for v in bindings.values()):
            raise CandidateInvalid("identity_snapshot")
        for name in ("active", "retired", "reserved"):
            _texts(snapshot.get(name, []), "identity_snapshot:" + name)
    except CandidateInvalid as error:
        return hold(SPLIT_REPLAN, identity, [("INVALID_CANDIDATE", (str(error),))])

    findings: list = []
    origin = original["identity"]
    operation = proposal.get("operation_id")

    # Exact-payload authority binding (N-5): presence and issuer bounds, then digest and revision binding.
    authority = proposal.get("authority") or {}
    if not isinstance(authority, dict):
        authority = {}
    if not authority or authority.get("issuer") not in (authority_limits.get("issuers") or ()):
        findings.append(("SPLIT_UNAUTHORIZED", (f"issuer:{authority.get('issuer')}",)))
    expected = {"payload_digest": payload_digest(proposal), "original_revision": original_revision(original),
                "graph_revision": graph_revision(proposal.get("original_edges", [])), "operation_id": operation}
    stale = [f"{k}:expected={v}:observed={authority.get(k)}" for k, v in expected.items() if authority.get(k) != v]
    if stale:
        findings.append(("SPLIT_AUTHORITY_STALE", _ordered(stale)))

    if stages.get(origin) == DONE:
        findings.append(("DONE_ORIGINAL", (origin,)))

    # The frozen graph and inventory are anchored to the pinned original, never taken on the proposal's word.
    if anchor is not None:
        incoming = {e.source for e in original_edges if e.target == origin}
        graph = [f"{origin}:{d}" for d in set(anchor.dependencies) ^ incoming]
        if graph:
            findings.append(("ORIGINAL_GRAPH_MISMATCH", _ordered(graph)))
        frozen = {o["text"] for o in obligations.values()}
        lost_clauses = [f"{origin}:{c}" for _, field in CATEGORY_FIELDS for c in getattr(anchor, field)
                        if c not in frozen]
        if lost_clauses:
            findings.append(("OBLIGATION_LOST", _ordered(lost_clauses)))

    # Identity bounds (N-7): existing identities preserved; new identities grammar-valid and collision-free.
    parents = [u for u, r in results.items() if r["role"] == INTEGRATION_PARENT]
    children = [u for u, r in results.items() if r["role"] == CHILD]
    if parents != [origin] or proposal.get("integration_parent") != origin:
        findings.append(("IDENTITY_REWRITTEN", (origin,)))
    invalid = [u for u in results if not identity_valid(u, identity_policy)]
    if invalid:
        findings.append(("IDENTITY_GRAMMAR", _ordered(invalid)))
    taken = {name: set(snapshot.get(name) or ()) for name in ("active", "retired", "reserved")}
    collisions = [f"{c}:{name}" for c in children for name, ids in taken.items() if c in ids]
    if collisions:
        findings.append(("IDENTITY_COLLISION", _ordered(collisions)))

    # Lineage is explicit; it is never inferred from a suffix or sort position.
    missing, inconsistent, lineage = [], [], {}
    for child in children:
        split_from = results[child].get("split_from")
        lineage[child] = split_from
        if split_from is None:
            missing.append(child)
        elif split_from != origin or results[child].get("operation_id") != operation:
            inconsistent.append(child)
    listed = set(results[origin].get("children") or ()) if origin in results else set()
    inconsistent += [c for c in children if c not in listed] + [c for c in listed if c not in children]
    if missing:
        findings.append(("LINEAGE_MISSING", _ordered(missing)))
    if inconsistent:
        findings.append(("LINEAGE_INCONSISTENT", _ordered(inconsistent)))

    contracts = _contracts({u: r["contract"] for u, r in results.items() if "contract" in r}, findings)
    if anchor is not None:
        # A contract original anchors bounds and declared edges, so every result must be a BiuContract.
        uncontracted = [f"{u}:contract" for u, r in results.items() if "contract" not in r]
        if uncontracted:
            findings.append(("INCOMPLETE_CONTRACT", _ordered(uncontracted)))

    known = set(taken["active"]) | {i for i, s in stages.items() if s is not None}
    predicated = semantics == PREDICATED
    findings += graph_findings(set(results), known, result_edges, predicates_required=predicated)
    rewrites = _rewrite_findings(origin, children, original_edges, result_edges, authorized, predicated, findings)

    conservation = _conservation(proposal, original, results, origin, children, obligations, mapping, reverse,
                                 bindings, findings)

    bounds = "NOT_APPLICABLE_NO_CONTRACT_VALUES"
    if anchor is not None and contracts:
        bounds = _bounds(anchor, contracts, findings)

    invalidation = _history(proposal, results, origin, original_edges, result_edges, history, findings)

    if findings:
        return hold(SPLIT_REPLAN, identity, findings)
    return ValidationReport(SPLIT_REPLAN, identity, {
        "operation_id": operation, "payload_digest": expected["payload_digest"],
        "original": {"identity": origin, "revision": expected["original_revision"],
                     "graph_revision": expected["graph_revision"]},
        "graph_semantics": semantics, "identity_rewrites": rewrites,
        "lineage": [{"child": c, "split_from": lineage[c], "operation_id": operation}
                    for c in _ordered(children)],
        "identity_bounds": {"policy": dict(identity_policy), "checked": list(_ordered(results)), "result": "PASS"},
        "original_anchor": "CONTRACT_GRAPH_AND_INVENTORY" if anchor is not None else "SUPPLIED_INVENTORY_NOT_DERIVED",
        "predecessor_stage": "NOT_REQUIRED_FOR_SPLIT_VALIDATION",
        "conservation": conservation, "bounds": bounds, **invalidation,
        "authority": {"issuer": authority.get("issuer"), "binding": "EXACT_PAYLOAD_AND_REVISIONS"}})


def _rewrite_findings(origin, children, original_edges, result_edges, authorized, predicated, findings) -> list:
    """Candidate identity-preserving graph rules (C#/contracts/2/design_decisions/4); every rewrite is reported."""
    result = {(e.source, e.target): e.predicate for e in result_edges}
    same = (lambda a, b: a == b) if predicated else (lambda a, b: True)
    pruned, redirected, weakened, not_copied, no_parent_edge, rewrites = [], [], [], [], [], []
    for edge in original_edges:
        key = (edge.source, edge.target)
        if key not in result:
            if edge.source == origin and any((c, edge.target) in result for c in children):
                redirected.append(edge.ref)
            else:
                pruned.append(edge.ref)
        elif not same(result[key], edge.predicate):
            weakened.append(edge.ref)
        else:
            rewrites.append(("PRESERVED", edge.ref, edge.ref, result[key]))
    for edge in original_edges:
        if edge.target != origin:
            continue
        for child in children:
            copy = (edge.source, child)
            if copy not in result:
                not_copied.append(f"{edge.source}->{child}")
            elif not same(result[copy], edge.predicate):
                weakened.append(f"{edge.source}->{child}")
            else:
                rewrites.append(("COPIED_TO_CHILD", edge.ref, f"{edge.source}->{child}", result[copy]))
    for child in children:
        key = (child, origin)
        if key not in result:
            no_parent_edge.append(f"{child}->{origin}")
        elif predicated and result[key] != DONE:
            weakened.append(f"{child}->{origin}")
        else:
            rewrites.append(("CHILD_TO_PARENT", None, f"{child}->{origin}", result[key]))
    expected = {(e.source, e.target) for e in original_edges} | {(c, origin) for c in children}
    expected |= {(e.source, c) for e in original_edges if e.target == origin for c in children}
    allowed = {(e.source, e.target): e.predicate for e in authorized}
    inter_child, unauthorized = [], []
    for edge in result_edges:
        key = (edge.source, edge.target)
        if key in expected:
            continue
        if key in allowed and same(allowed[key], edge.predicate):
            rewrites.append(("AUTHORIZED", None, edge.ref, edge.predicate))
        elif edge.source in children and edge.target in children:
            inter_child.append(edge.ref)
        elif not (edge.source == origin and edge.target in children):  # O->child is reported as a cycle.
            unauthorized.append(edge.ref)
    for code, refs in (("EDGE_PRUNED", pruned), ("EDGE_REDIRECTED", redirected), ("PREDICATE_WEAKENED", weakened),
                       ("PREREQUISITE_NOT_COPIED", not_copied), ("CHILD_PARENT_EDGE_MISSING", no_parent_edge),
                       ("INTER_CHILD_EDGE_UNAUTHORIZED", inter_child), ("EDGE_UNAUTHORIZED", unauthorized)):
        if refs:
            findings.append((code, _ordered(refs)))
    return [{"rule": r, "source_edge": s, "result_edge": t, "predicate": p}
            for r, s, t, p in sorted(rewrites, key=lambda x: (x[0], x[2], x[1] or ""))]


def _conservation(proposal, original, results, origin, children, obligations, mapping, reverse, bindings,
                  findings) -> dict:
    """Forward and reverse conservation of the frozen original obligations (SF-REQ-013-AC-05)."""
    approvals = {a.get("obligation_id"): a for a in _list(proposal, "elaboration_approvals") if isinstance(a, dict)
                 and _text(a.get("decision_ref")) and re.fullmatch(r"sha256:[0-9a-f]{64}", str(a.get("decision_digest")))}
    rows: dict[str, list] = {}
    for row in mapping:
        rows.setdefault(row.get("obligation_id"), []).extend(row["maps_to"])

    def bound(destination: object) -> str | None:
        target = bindings.get(destination, destination) if isinstance(destination, str) else None
        return target if isinstance(target, str) and target in results else None

    lost = [o for o in obligations if o not in rows]
    invented = [str(o) for o in rows if o not in obligations]
    partial, dropped, not_verbatim, extents = [], [], [], []
    for obligation, destinations in rows.items():
        if obligation not in obligations:
            continue
        text = obligations[obligation]["text"]
        targets = [bound(d) for d in destinations]
        if not destinations or None in targets:
            partial.append(obligation)
        resolved = {t for t in targets if t is not None}
        if origin not in resolved:
            dropped.append(obligation)
        elaborated = obligation in approvals
        if not elaborated and not holds_clause(text, original):
            not_verbatim.append(obligation)
        for target in _ordered(resolved):
            if target == origin:
                if not elaborated and not holds_clause(text, results[target]):
                    not_verbatim.append(obligation)
            elif not (holds_clause(text, results[target]) or verbatim(obligation, _body(results[target]))):
                # A child extent is the verbatim clause or an elaborated extent under the same obligation ID.
                not_verbatim.append(obligation)
            extents.append((obligation, target))
    for entry in reverse:
        if entry.get("origin") not in obligations or bound(entry.get("destination")) is None:
            invented.append(str(entry.get("obligation_id")))
    for code, refs in (("OBLIGATION_LOST", lost), ("PARTIAL_MAPPING", partial), ("INTEGRATION_DUTY_DROPPED", dropped),
                       ("CLAUSE_NOT_VERBATIM", not_verbatim), ("OBLIGATION_INVENTED", invented)):
        if refs:
            findings.append((code, _ordered(refs)))
    shared = _ordered(o for o, d in rows.items() if len({bound(x) for x in d}) > 1)
    return {"forward": {"mapped": len([o for o in obligations if o in rows]), "total": len(obligations)},
            "reverse": {"entries": len(reverse), "complete": not invented},
            "integration_parent": origin, "shared_rows": list(shared), "shared_rule": "ALL_EXTENTS_REQUIRED",
            "elaboration_bound": [{"obligation_id": o, "decision_ref": approvals[o]["decision_ref"],
                                   "decision_digest": approvals[o]["decision_digest"]}
                                  for o in _ordered(o for o in approvals if o in obligations)],
            "extents": len(set(extents)), "comparison": "BYTE_EXACT", "mapping_is_not_satisfaction": True}


def _bounds(original: BiuContract, contracts: dict[str, BiuContract], findings: list) -> str:
    """Per resulting unit: no budget dimension above the original, no capability/scope beyond it; never clipped."""
    widened = []
    base = original.budget_policy
    for identity, contract in contracts.items():
        policy = contract.budget_policy
        for name in BUDGET_LIMITS:
            limit, value = getattr(base, name), getattr(policy, name)
            if limit is not None and (value is None or value > limit):
                widened.append(f"{identity}:budget_policy.{name}:{limit}->{value}")
        if not set(base.hard_required_dimensions) <= set(policy.hard_required_dimensions):
            widened.append(f"{identity}:budget_policy.hard_required_dimensions:"
                           f"{list(base.hard_required_dimensions)}->{list(policy.hard_required_dimensions)}")
        for name in SUBSET_FIELDS:
            extra = sorted(set(getattr(contract, name)) - set(getattr(original, name)))
            if extra:
                widened.append(f"{identity}:{name}:{list(getattr(original, name))}->{extra}")
    if widened:
        findings.append(("BOUNDS_WIDENED", _ordered(widened)))
    return "WITHIN_ORIGINAL"


def _history(proposal, results, origin, original_edges, result_edges, history, findings) -> dict:
    """Invalidation must cover every result and each existing unit whose dependency semantics changed; prior
    assessments stay byte-identical and are never carried as current for a changed unit."""
    def incoming(edges, unit):
        return {(e.source, e.predicate) for e in edges if e.target == unit}

    existing = {e.target for e in original_edges} - set(results)
    changed = {u for u in existing | ({e.target for e in result_edges} - set(results))
               if incoming(original_edges, u) != incoming(result_edges, u)}
    required = set(results) | changed
    declared = set(proposal.get("invalidation") or ())
    missing = [u for u in required if u not in declared]
    if missing:
        findings.append(("INVALIDATION_INCOMPLETE", _ordered(missing)))
    mutated, current, prior = [], [], []
    for entry in _list(proposal, "prior_assessments"):
        locator = str((entry.get("ref") or {}).get("locator")) if isinstance(entry, dict) else "invalid"
        expected, observed = (entry.get("digest") if isinstance(entry, dict) else None), history.get(locator)
        if observed is None or observed != expected:
            mutated.append(f"{locator}:expected={expected}:observed={observed}")
            continue
        if entry.get("applicability") == CURRENT and entry.get("unit") in required:
            current.append(str(entry.get("unit")))
        prior.append({"unit": entry.get("unit"), "locator": locator, "digest": expected, "unchanged": True,
                      "disposition": entry.get("disposition"), "applicability": entry.get("applicability"),
                      "inapplicable_to": list(_ordered(u for u in required if u == entry.get("unit") or u in results))})
    if mutated:
        findings.append(("ASSESSMENT_HISTORY_MUTATED", _ordered(mutated)))
    if current:
        findings.append(("STALE_ASSESSMENT_AS_CURRENT", _ordered(current)))
    return {"invalidation": list(_ordered(declared)), "dependency_semantics_changed": list(_ordered(changed)),
            "prior_assessments": sorted(prior, key=canonical)}
