"""Advisory proof-order diagnostics (014-proof-order) over recorded evidence ancestry.

Order is read only from each step's recorded preceding references; timestamps are never
consulted, so a clock cannot widen or narrow what counts as prior evidence. Diagnostics are
advisory and never block derivation or admission.
"""
from dataclasses import dataclass

from alienintent.evidence_learning.domain.refs import Ref

PLAN, INTACT, FAULT, RESTORED = "plan", "intact", "fault", "restored"
STEP_KINDS = frozenset({PLAN, INTACT, FAULT, RESTORED})


@dataclass(frozen=True)
class ProofStep:
    ref: Ref
    kind: str
    control: str | None
    preceding: tuple[Ref, ...]
    observer: str


@dataclass(frozen=True)
class ProofDiagnostic:
    name: str
    ref: Ref
    control: str | None
    strength: str = "ADVISORY"


def _ancestry(step: ProofStep, steps: dict[Ref, ProofStep]) -> list[ProofStep]:
    seen, pending, found = set(), list(step.preceding), []
    while pending:
        ref = pending.pop()
        if ref in seen or ref not in steps:
            continue
        seen.add(ref)
        found.append(steps[ref])
        pending.extend(steps[ref].preceding)
    return found


def proof_order_diagnostics(steps: tuple[ProofStep, ...]) -> tuple[ProofDiagnostic, ...]:
    by_ref = {s.ref: s for s in steps}
    diagnostics = []
    for step in steps:
        def emit(name: str) -> None:
            diagnostics.append(ProofDiagnostic("proof-order/" + name, step.ref, step.control))

        if any(ref not in by_ref for ref in step.preceding):
            emit("unresolved-ancestor")
        if step.kind == PLAN:
            continue
        ancestors = _ancestry(step, by_ref)
        if not any(a.kind == PLAN for a in ancestors):
            emit("missing-plan-ancestry")
        same = {a.kind for a in ancestors if a.control == step.control}
        if step.kind == FAULT and INTACT not in same:
            emit("fault-before-intact")
        if step.kind == RESTORED and FAULT not in same:
            emit("restored-before-fault")
    return tuple(diagnostics)
