"""Readiness consumer values: attempts, recognized semantics, provenance binding and read-time applicability.

Vendor-neutral. Nothing here knows an executable location, subprocess syntax, transport or Agent Ready package
internals, and nothing here judges readiness: Agent Ready owns assessment semantics; this module only recognizes a
supplied result, refuses what cannot be attributed, and decides applicability. Hold and failure codes are an
AlienIntent vocabulary (READINESS_CONSUMER_HOLD_CODES_v1), never Agent Ready dispositions or lifecycle states.
"""
from dataclasses import dataclass, field
from hashlib import sha256
import json

READY, CLARIFY, SPLIT, HOLD = "READY", "CLARIFY", "SPLIT", "HOLD"
DISPOSITIONS = (READY, CLARIFY, SPLIT, HOLD)
DIRECT, MCP = "direct", "mcp"

LINT_HOLD = "LINT_HOLD"
ATTEMPT_FAILURE = "ATTEMPT_FAILURE"
CAPABILITY_PROVENANCE_HOLD = "CAPABILITY_PROVENANCE_HOLD"
STALE_ASSESSMENT = "STALE_ASSESSMENT"
SPLIT_RESULT_SET_NOT_MATERIALIZED = "SPLIT_RESULT_SET_NOT_MATERIALIZED"
CLARIFY_PENDING_DECISION = "CLARIFY_PENDING_DECISION"
PREREQUISITE_PENDING = "PREREQUISITE_PENDING"
ATTEMPT_CONFLICT = "ATTEMPT_CONFLICT"
ATTEMPT_IN_PROGRESS = "ATTEMPT_IN_PROGRESS"
PERSISTENCE_CONFLICT = "PERSISTENCE_CONFLICT"
NO_ASSESSMENT = "NO_ASSESSMENT"
HOLD_CODES = (LINT_HOLD, ATTEMPT_FAILURE, CAPABILITY_PROVENANCE_HOLD, STALE_ASSESSMENT,
              SPLIT_RESULT_SET_NOT_MATERIALIZED, CLARIFY_PENDING_DECISION, PREREQUISITE_PENDING, ATTEMPT_CONFLICT,
              ATTEMPT_IN_PROGRESS, PERSISTENCE_CONFLICT, NO_ASSESSMENT)

# Attempt failure classes: an attempt that fails carries no disposition.
TIMEOUT, PROVIDER_FAILURE, MCP_ERROR = "TIMEOUT", "PROVIDER_FAILURE", "MCP_ERROR"
MALFORMED, UNKNOWN_DISPOSITION, CONFLICTING = "MALFORMED", "UNKNOWN_DISPOSITION", "CONFLICTING"
NO_TERMINAL_RESULT, PROVENANCE = "NO_TERMINAL_RESULT", "PROVENANCE"
RAW_EVIDENCE_NOT_RETAINED = "RAW_EVIDENCE_NOT_RETAINED"

PRODUCT = "agent-ready"
UNKNOWN = "UNKNOWN"
CONTRACT_VERSION = "package-release-bound; no result-level identifier (agent-ready#1)"


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: bytes | str) -> str:
    return "sha256:" + sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def input_fingerprint(contract_digest: str | None, baseline: str, decisions: tuple[str, ...],
                      prerequisites: dict[str, str | None], design: dict[str, str]) -> str:
    """Contract digest, exact baseline, governing decisions, prerequisite states and verified design refs."""
    components = {"contract": contract_digest,
                  "baseline": baseline,
                  "decisions": sorted(decisions),
                  "prerequisites": dict(sorted(prerequisites.items())),
                  "design": dict(sorted(design.items()))}
    return digest(canonical(components))


@dataclass(frozen=True)
class ProducerBinding:
    """The configured producer identity, resolved at the composition boundary from installed metadata."""
    product: str
    product_version: str
    version_source: str
    executable: str
    transport: str
    editable_revision: str | None = None
    contract_version: str = CONTRACT_VERSION

    @property
    def schema_binding(self) -> str:
        return f"package-release-bound:{self.product}=={self.product_version}"


def binding_refusal(binding: ProducerBinding | None) -> str | None:
    """Why a binding cannot supply readiness; None only for an established product/package identity."""
    if binding is None:
        return "UNBOUND"
    if not binding.product_version or binding.product_version == UNKNOWN:
        return "PRODUCT_VERSION_UNKNOWN"
    if binding.product != PRODUCT:
        return "WRONG_PACKAGE"
    if binding.contract_version != CONTRACT_VERSION:
        return "CONTRACT_UNBOUND"
    return None


@dataclass(frozen=True)
class CandidateWorkUnit:
    """Pinned candidate text submitted for one attempt; the attempt ID exists before any invocation."""
    identity: str
    text: str
    attempt_id: str
    input_fingerprint: str


@dataclass(frozen=True)
class InvocationCustody:
    """What the invoking adapter observed about its own invocation; it is checked, never trusted by shape."""
    attempt_id: str
    input_sha256: str
    product: str
    product_version: str
    executable: str
    arguments: tuple[str, ...]
    provider: str
    started_at: str
    ended_at: str
    provider_evidence: dict | None = None


@dataclass(frozen=True)
class ProducerResponse:
    raw: bytes | None
    exit_status: int | None
    timed_out: bool
    shape: str
    custody: InvocationCustody | None


@dataclass(frozen=True)
class AttemptMetadata:
    identity: str
    attempt_id: str
    input_fingerprint: str
    input_sha256: str
    exit_status: int | None
    timed_out: bool
    custody: InvocationCustody | None
    binding: ProducerBinding | None


@dataclass(frozen=True)
class SemanticAssessment:
    """Recognized semantics; equality ignores the carrier: shape, supplied values and raw digest (direct/MCP parity)."""
    disposition: str
    body: str
    owner_clarifications: tuple[str, ...]
    values: tuple[str, ...] = field(compare=False)
    shape: str = field(compare=False)
    raw_digest: str | None = field(compare=False)


@dataclass(frozen=True)
class AttemptFailure:
    failure_class: str
    values: tuple[str, ...]
    detail: str
    raw_digest: str | None = field(compare=False, default=None)


@dataclass(frozen=True)
class ReadinessEligibility:
    """Eligibility for the separate SF-REQ-002 release gate only; never a release."""
    identity: str
    attempt_id: str
    contract_digest: str
    input_fingerprint: str


@dataclass(frozen=True)
class Hold:
    reason_code: str
    identity: str
    attempt_id: str | None = None
    detail: str = ""


@dataclass(frozen=True)
class HistoricalAssessment:
    """One retained historical assessment Git blob, addressed by revision and pinned by digest."""
    revision: str
    path: str
    blob: str
    sha256: str
    raw: bytes
    producer: str


def _members(pairs: list) -> dict:
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate member names make the payload ambiguous")
    return dict(pairs)


def _constant(name: str) -> object:
    raise ValueError(f"{name} is not JSON")


def _loads(text: str) -> object:
    """Parse JSON as data: duplicate member names and NaN/Infinity are malformed, never resolved silently."""
    return json.loads(text, object_pairs_hook=_members, parse_constant=_constant)


def _direct(document: object) -> tuple[tuple[str, ...], list, str | None]:
    if not isinstance(document, dict):
        return (), [], MALFORMED
    value = document.get("disposition")
    return ((value,) if isinstance(value, str) else ()), [document], None


def _envelope(document: object) -> tuple[tuple[str, ...], list, str | None]:
    """Known MCP parsing: structuredContent and every parseable JSON text content item supply values and bodies."""
    if not isinstance(document, dict) or not {"content", "structuredContent", "isError"} & set(document):
        return (), [], MALFORMED
    error = document.get("isError", False)
    if not isinstance(error, bool):
        return (), [], MALFORMED
    if error:
        return (), [], MCP_ERROR
    values, bodies = [], []
    structured = document.get("structuredContent")
    if isinstance(structured, dict) and isinstance(structured.get("disposition"), str):
        values.append(structured["disposition"])
        bodies.append(structured)
    content = document.get("content") or []
    if not isinstance(content, list):
        return (), [], MALFORMED
    for item in content:
        if not isinstance(item, dict) or item.get("type") != "text":
            continue
        try:
            parsed = _loads(item.get("text"))
        except (TypeError, ValueError):
            return tuple(values), [], MALFORMED
        if isinstance(parsed, dict) and isinstance(parsed.get("disposition"), str):
            values.append(parsed["disposition"])
            bodies.append(parsed)
    return tuple(values), bodies, None


def recognize(raw: bytes | None, exit_status: int | None, timed_out: bool,
              shape: str) -> SemanticAssessment | AttemptFailure:
    """One terminal value, agreed by every supplied value, from a known shape; everything else fails the attempt."""
    raw_digest = digest(raw) if raw is not None else None
    # A CLI result needs its process exit status; an MCP tool result has none of its own.
    exited = exit_status == 0 or (shape == MCP and exit_status is None)
    if timed_out:
        return AttemptFailure(TIMEOUT, (), "no terminal result before the deadline", raw_digest)
    if not raw:
        return AttemptFailure(NO_TERMINAL_RESULT if exited else PROVIDER_FAILURE, (), "no output", raw_digest)
    try:
        document = _loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return AttemptFailure(MALFORMED, (), "output is not unambiguous JSON", raw_digest)
    if shape == MCP:
        values, bodies, failure = _envelope(document)
    elif shape == DIRECT:
        values, bodies, failure = _direct(document)
    else:
        return AttemptFailure(MALFORMED, (), "unknown result shape", raw_digest)
    if failure is not None:
        return AttemptFailure(failure, values, "purported result is not a recognized terminal value", raw_digest)
    if not values:
        return AttemptFailure(NO_TERMINAL_RESULT, values, "no disposition value", raw_digest)
    if len(set(values)) > 1 or len({canonical(b) for b in bodies}) > 1:
        return AttemptFailure(CONFLICTING, values, "supplied disposition values or result bodies disagree", raw_digest)
    disposition = values[0] if values else None
    if disposition not in DISPOSITIONS:
        return AttemptFailure(UNKNOWN_DISPOSITION, values, "not an Agent Ready disposition", raw_digest)
    if not exited:
        return AttemptFailure(PROVIDER_FAILURE, values, f"exit status {exit_status}", raw_digest)
    body = bodies[0]
    clarifications = body.get("owner_clarifications")
    return SemanticAssessment(disposition, canonical(body), tuple(str(c) for c in clarifications or ()), values,
                              shape, raw_digest)


def provenance_failure(binding: ProducerBinding | None, metadata: AttemptMetadata, body: object) -> str | None:
    """Only invocation custody from the bound producer authenticates; body shape and provider_evidence never do."""
    refusal = binding_refusal(binding)
    if refusal:
        return refusal
    custody = metadata.custody
    if custody is None:
        return "NO_INVOCATION_CUSTODY"
    if (custody.product, custody.product_version, custody.executable) != \
            (binding.product, binding.product_version, binding.executable):
        return "PRODUCER_NOT_BOUND"
    if (custody.attempt_id, custody.input_sha256) != (metadata.attempt_id, metadata.input_sha256):
        return "RESPONSE_NOT_CORRELATED"
    return None


def decide(identity: str, entry: dict | None, current_fingerprint: str,
           invalidated: frozenset[str] = frozenset()) -> ReadinessEligibility | Hold:
    """Read-time applicability of the latest attempt; only an applicable READY is eligible."""
    if not entry or entry.get("outcome") is None:
        return Hold(NO_ASSESSMENT, identity, entry.get("attempt_id") if entry else None)
    attempt = entry["attempt_id"]
    outcome = entry["outcome"]
    if outcome.get("failure_class"):
        return Hold(ATTEMPT_FAILURE, identity, attempt, outcome["failure_class"])
    if attempt in invalidated:
        return Hold(STALE_ASSESSMENT, identity, attempt, "applicability invalidated")
    if entry.get("input_fingerprint") != current_fingerprint:
        return Hold(STALE_ASSESSMENT, identity, attempt, "assessed inputs no longer match")
    disposition = outcome.get("disposition")
    if disposition != READY:
        code = {CLARIFY: CLARIFY_PENDING_DECISION, SPLIT: SPLIT_RESULT_SET_NOT_MATERIALIZED,
                HOLD: PREREQUISITE_PENDING}.get(disposition, ATTEMPT_FAILURE)
        return Hold(code, identity, attempt, str(disposition))
    return ReadinessEligibility(identity, attempt, entry["contract_digest"], current_fingerprint)
