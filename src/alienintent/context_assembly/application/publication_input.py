"""Assessed publication input (PY-SELF-00): the task text and contract exactly as the latest assessment checked them.

The readiness fingerprint binds the contract, baseline, decisions, prerequisites and design, never the text, so an
applicable READY alone does not prove which text was assessed. These comparisons bind the derived text, the
reconstructed contract and the pinned proof plan to the latest retained attempt and its raw receipt by value. Every
comparison is exact: a missing or wrong-typed field is a refusal, never coerced to a passing value.

BiuContract freezes its own attributes only and digests whatever JSON value a field holds, so a nested list or
mapping would stay shared with the mutable compiled body under an unchanged content digest. A contract is therefore
bound only when every field holds exactly its declared text, number or tuple of text.

The result is a snapshot for a later repository publisher. It is not permission to implement and not a publication
receipt; nothing here stores, caches, assesses or reads history, and the raw receipt's text is never interpreted.
"""
from dataclasses import dataclass

from alienintent.context_assembly.domain.compilation import contract_from_payload
from alienintent.evidence_learning.domain.records import ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy, ContractValidationError
from alienintent.execution_coordination.domain.readiness import READY, Hold, ReadinessEligibility, digest

UNBOUND = "PUBLICATION_INPUT_UNBOUND"
CHANGED = "PUBLICATION_INPUT_CHANGED"
UNIDENTIFIED = "<unidentified>"
# The declared field types of BiuContract and BudgetPolicy, each an immutable value when held exactly.
SCALARS = {"str": (str,), "int": (int,), "int | None": (int, type(None))}
TEXTS = "tuple[str, ...]"


@dataclass(frozen=True)
class AssessedPublicationInput:
    """The assessed text and contract of one work unit, bound to its latest applicable READY attempt."""
    identity: str
    contract: BiuContract
    text: str
    proof_plan: tuple[str, ...]
    attempt_id: str
    input_fingerprint: str
    text_digest: str
    raw_ref: Ref


@dataclass(frozen=True)
class PinnedInput:
    """The text, contract and proof plan of one derivation, held by value: the compiled body stays mutable."""
    contract: BiuContract
    text: str
    proof_plan: tuple[str, ...]


@dataclass(frozen=True)
class Reading:
    """One read of the derived input, its current eligibility and the latest retained attempt entry."""
    pinned: PinnedInput
    eligibility: ReadinessEligibility
    latest: dict | None


def refusal(identity: object, field: str, cause: str, attempt_id: str | None = None, reason: str = UNBOUND) -> Hold:
    return Hold(reason, identity if isinstance(identity, str) and identity else UNIDENTIFIED, attempt_id,
                f"{field}: {cause}")


def undeclared(value: BiuContract | BudgetPolicy, path: str = "") -> str | None:
    """The first field of a contract value that does not hold exactly its declared immutable type."""
    for name, field in value.__dataclass_fields__.items():
        member, declared = getattr(value, name), field.type
        if declared == BudgetPolicy.__name__:
            nested = undeclared(member, name + ".") if type(member) is BudgetPolicy else name
            if nested is not None:
                return nested
        elif declared == TEXTS:
            if type(member) is not tuple or any(type(v) is not str for v in member):
                return path + name
        elif type(member) not in SCALARS.get(declared, ()):  # A type not declared here is refused, never assumed.
            return path + name
    return None


def pinned(identity: object, candidate: dict, proof_plan: object) -> PinnedInput | Hold:
    """The caller's identity, the exact text, the reconstructed contract and a well-formed plan, or the refusal."""
    if type(identity) is not str or not identity:
        return refusal(identity, "identity", "no work identity supplied")
    if type(proof_plan) is not tuple or not proof_plan or any(type(p) is not str or not p for p in proof_plan):
        return refusal(identity, "proof_plan", "no well-formed pinned proof plan")
    text = candidate.get("text")
    if type(text) is not str or not text:
        return refusal(identity, "text", "pinned candidate text is missing")
    try:
        contract = contract_from_payload(candidate.get("contract"))
    except ContractValidationError as error:
        return refusal(identity, "contract", str(error))
    field = undeclared(contract)
    if field is not None:
        return refusal(identity, "contract", f"{field} is not its declared text or number")
    if contract.identity != identity:
        return refusal(identity, "identity", f"expected={identity} contract={contract.identity}")
    return PinnedInput(contract, text, proof_plan)


def attempt_refusal(identity: str, reading: Reading) -> Hold | None:
    """Why the latest retained attempt is not the READY assessment of exactly this text and contract."""
    bound, eligibility, latest = reading.pinned, reading.eligibility, reading.latest
    attempt = eligibility.attempt_id
    if not isinstance(latest, dict):
        return refusal(identity, "latest", "no retained attempt", attempt)
    comparisons = (("identity", identity, eligibility.identity),
                   ("attempt_id", eligibility.attempt_id, latest.get("attempt_id")),
                   ("input_fingerprint", eligibility.input_fingerprint, latest.get("input_fingerprint")),
                   ("contract_digest", bound.contract.content_digest, eligibility.contract_digest),
                   ("contract_digest", bound.contract.content_digest, latest.get("contract_digest")),
                   ("text_digest", digest(bound.text), latest.get("input_sha256")))
    for field, expected, observed in comparisons:
        if type(observed) is not str or observed != expected:
            return refusal(identity, field, f"expected={expected} observed={observed}", attempt)
    outcome = latest.get("outcome")
    if not isinstance(outcome, dict) or outcome.get("failure_class") or outcome.get("disposition") != READY:
        return refusal(identity, "outcome", f"latest attempt is not {READY}: {outcome}", attempt)
    if not isinstance(latest.get("raw_ref"), dict):
        return refusal(identity, "raw_ref", "latest attempt retains no raw receipt", attempt)
    return None


def receipt(identity: str, reading: Reading, retained: object, project: str, profile: str) -> Ref | Hold:
    """The retrieved raw receipt's reference, only when it is the latest attempt's own retained receipt."""
    attempt = reading.eligibility.attempt_id
    if not isinstance(retained, tuple) or len(retained) != 2:
        return refusal(identity, "raw_ref", "no retained raw receipt", attempt)
    reference, value = retained
    if reference != reading.latest["raw_ref"]:
        return refusal(identity, "raw_ref", f"retrieved={reference} latest raw_ref={reading.latest['raw_ref']}",
                       attempt)
    if type(value) is not str:
        return refusal(identity, "raw_ref", "retained receipt is not text", attempt)
    try:
        ref = ref_from_document(reference)
    except EvidenceHold as hold:
        return refusal(identity, "raw_ref", f"unreadable: {hold.reason_code}", attempt)
    expected = (("logical_id", f"readiness/{identity}/{attempt}/raw"), ("project", project), ("profile", profile))
    for field, required in expected:
        if getattr(ref, field) != required:
            return refusal(identity, "raw_ref", f"{field} expected={required} observed={getattr(ref, field)}",
                           attempt)
    return ref


def change(identity: str, first: Reading, last: Reading) -> Hold | None:
    """What differs between the first and the last read; the snapshot is refused if anything does."""
    attempt = first.eligibility.attempt_id
    for field in ("text", "contract", "proof_plan"):
        if getattr(first.pinned, field) != getattr(last.pinned, field):
            return refusal(identity, field, "changed between the first and the last read", attempt, CHANGED)
    if first.eligibility != last.eligibility:
        return refusal(identity, "eligibility", f"first={first.eligibility} last={last.eligibility}", attempt, CHANGED)
    if first.latest != last.latest:
        before, after = first.latest or {}, last.latest or {}
        fields = sorted(k for k in {*before, *after} if before.get(k) != after.get(k) or (k in before) != (k in after))
        return refusal(identity, "latest", "changed between the first and the last read: " + ",".join(fields),
                       attempt, CHANGED)
    return None


def bound(identity: str, reading: Reading, raw_ref: Ref) -> AssessedPublicationInput:
    return AssessedPublicationInput(identity, reading.pinned.contract, reading.pinned.text, reading.pinned.proof_plan,
                                    reading.eligibility.attempt_id, reading.eligibility.input_fingerprint,
                                    digest(reading.pinned.text), raw_ref)
