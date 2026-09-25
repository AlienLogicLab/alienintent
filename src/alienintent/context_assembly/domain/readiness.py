"""Readiness lint and routing values for SF-REQ-015 integration in Requirements / Planning.

Lint runs before any assessment. A missing duty is an attributable LintHold naming the duty and field; it is never a
fabricated Agent Ready HOLD disposition. Duty sources (LINT_DUTY_SOURCES_v1): decision, boundary and verification
from the required BiuContract fields plus the pinned proof plan; architecture from the U5 design applicability
(only CURRENT_VERIFIED passes; otherwise the U5 reason code verbatim); dependency from the execution lifecycle
snapshot and the declared upstream edges. Agent Ready alone judges readiness; nothing here does.
"""
from dataclasses import dataclass
from typing import Mapping

from alienintent.context_assembly.domain.compilation import contract_from_payload
from alienintent.context_assembly.domain.design_admission import CurrentVerified, Held, Stale
from alienintent.execution_coordination.domain.contract import ContractValidationError
from alienintent.execution_coordination.domain.readiness import LINT_HOLD, Hold, ReadinessEligibility, canonical, digest

DUTY_FIELDS = (
    ("decision", ("fixed_decisions",)),
    ("boundary", ("authorized_scope", "excluded_scope")),
    ("verification", ("verification_obligations",)),
)
CANDIDATE_TEXT_FIELDS = ("text", "baseline")
FIXTURE_RESULT_SET = "FIXTURE_MATERIALIZED_RESULT_SET_NOT_U8_PROOF"


@dataclass(frozen=True)
class LintHold:
    identity: str
    duty: str
    field: str
    detail: str

    def document(self) -> dict:
        return {"record_kind": "LintHold", "reason_code": LINT_HOLD, "identity": self.identity, "duty": self.duty,
                "field": self.field, "detail": self.detail}


@dataclass(frozen=True)
class LintReport:
    """Every duty is checked; any hold refuses assessment, and the first is the attributable reason."""
    identity: str
    candidate_digest: str
    contract_digest: str | None
    design_digest: str | None
    review_digest: str | None
    dependencies: tuple[tuple[str, str | None], ...]
    holds: tuple[LintHold, ...] = ()

    def document(self) -> dict:
        if self.holds:
            return {**self.holds[0].document(), "holds": [h.document() for h in self.holds]}
        return {"record_kind": "LintReport", "identity": self.identity, "candidate_digest": self.candidate_digest,
                "contract_digest": self.contract_digest, "design_digest": self.design_digest,
                "review_digest": self.review_digest, "dependencies": dict(self.dependencies),
                "duties": [d for d, _ in DUTY_FIELDS] + ["architecture", "dependency"]}


@dataclass(frozen=True)
class SplitResultSet:
    """A materialized result set supplied by U8's SplitTransaction; U9 only lints and reassesses each unit."""
    children: tuple[dict, ...]
    integration_parent: dict
    invalidated: tuple[str, ...]
    label: str


@dataclass(frozen=True)
class SplitRouted:
    identity: str
    attempt_id: str
    outcomes: tuple[tuple[str, object], ...]


Outcome = LintHold | Hold | ReadinessEligibility | SplitRouted


def identity_of(candidate: object) -> str:
    contract = candidate.get("contract") if isinstance(candidate, dict) else None
    identity = contract.get("identity") if isinstance(contract, dict) else None
    return identity if isinstance(identity, str) and identity else "<unidentified>"


def design_reason(applicability: CurrentVerified | Held | Stale | None) -> str:
    if isinstance(applicability, CurrentVerified):
        return "CURRENT_VERIFIED"
    if isinstance(applicability, Stale):
        return "STALE"
    return applicability.reason_code if isinstance(applicability, Held) else "NO_DESIGN"


def _present(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(v, str) and v for v in value)


def _field(error: ContractValidationError) -> str:
    message = str(error)
    return message.split(" ", 1)[0] if " is " in message else "contract"


def lint(candidate: object, design_applicability: CurrentVerified | Held | Stale | None,
         proof_plan: tuple[str, ...] | None, dependency_snapshot: Mapping[str, str | None]) -> LintReport:
    identity = identity_of(candidate)
    candidate = candidate if isinstance(candidate, dict) else {}
    document = candidate.get("contract") if isinstance(candidate.get("contract"), dict) else {}
    holds: list[LintHold] = []
    for duty, fields in DUTY_FIELDS:
        for name in fields:
            if not _present(document.get(name)):
                holds.append(LintHold(identity, duty, name, f"{name} is missing or empty"))
    if not proof_plan:
        holds.append(LintHold(identity, "verification", "proof_plan", "no pinned proof plan"))
    contract = None
    try:
        contract = contract_from_payload(document)
    except ContractValidationError as error:
        holds.append(LintHold(identity, "contract", _field(error), str(error)))
    for name in CANDIDATE_TEXT_FIELDS:
        if not isinstance(candidate.get(name), str) or not candidate[name]:
            holds.append(LintHold(identity, "contract", name, f"pinned candidate {name} is missing"))
    if not isinstance(design_applicability, CurrentVerified):
        holds.append(LintHold(identity, "architecture", "design_applicability", design_reason(design_applicability)))
    declared = tuple(d for d in document.get("dependencies") or () if isinstance(d, str))
    missing = [d for d in declared if dependency_snapshot.get(d) is None]
    if missing:
        holds.append(LintHold(identity, "dependency", "dependencies", "absent from the dependency snapshot: "
                              + ",".join(missing)))
    edges = candidate.get("dependency_edges")
    if not isinstance(edges, list) or sorted(edges) != sorted(declared):
        holds.append(LintHold(identity, "dependency", "dependency_edges", "declared dependency edges disagree with "
                              "the upstream snapshot"))
    return LintReport(identity, digest(canonical(candidate)), contract.content_digest if contract else None,
                      getattr(design_applicability, "design_digest", None),
                      getattr(design_applicability, "review_digest", None),
                      tuple((d, dependency_snapshot.get(d)) for d in sorted(declared)), tuple(holds))
