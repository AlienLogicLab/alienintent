"""Pure checks for contract and host facts that can prevent a work item reaching DONE."""
from __future__ import annotations

from collections.abc import Callable

from alienintent.execution_coordination.domain.closure import is_fixed
from alienintent.execution_coordination.domain.contract import BiuContract

ARTIFACT_VERIFIED = "artifact-verified"
VERIFIER_EVIDENCE = "independent-verifier-accepted"
OBSERVABLE_EVIDENCE = frozenset({ARTIFACT_VERIFIED, VERIFIER_EVIDENCE})
BASE_CAPABILITIES = frozenset({"python", "filesystem", "process-control"})


def unsatisfiable(contract: BiuContract, *, landing: bool, present_at_pointer: Callable[[str], bool],
                  registered: Callable[[str], bool], provider_dimensions: frozenset[str]) -> tuple[str, ...]:
    """Return every deterministic refusal in contract-field order, without reading external state."""
    reasons = []
    unknown_evidence = set(contract.required_evidence) - OBSERVABLE_EVIDENCE
    if unknown_evidence:
        reasons.append(f"required_evidence: unobservable ids {', '.join(sorted(unknown_evidence))}")
    if contract.release_policy != "explicit-human-off":
        reasons.append(f"release_policy: {contract.release_policy} cannot be released explicitly")
    unavailable = set(contract.required_capabilities) - BASE_CAPABILITIES
    if unavailable:
        reasons.append(f"required_capabilities: unavailable {', '.join(sorted(unavailable))}")
    budget = contract.budget_policy
    missing_limits = [name for name in ("hard_wall_clock_seconds", "cancellation_limit")
                      if getattr(budget, name) is None]
    unsupported = set(budget.required_dimensions) - provider_dimensions
    if missing_limits or unsupported:
        details = [f"missing {', '.join(missing_limits)}"] if missing_limits else []
        if unsupported:
            details.append(f"unsupported dimensions {', '.join(sorted(unsupported))}")
        reasons.append(f"budget_policy: {'; '.join(details)}")
    if not is_fixed(contract.required_closure_actions):
        reasons.append("required_closure_actions: the five fixed actions are required exactly once")
    absent_references = [entry for entry in contract.authority_references
                         if not present_at_pointer((entry.split() or [""])[0])]
    if absent_references:
        reasons.append(f"authority_references: absent at pointer: {', '.join(absent_references)}")
    absent_dependencies = [entry for entry in contract.dependencies if not registered(entry)]
    if absent_dependencies:
        reasons.append(f"dependencies: unregistered: {', '.join(absent_dependencies)}")
    if not landing:
        reasons.append("landing: DONE is unreachable; the item would end at ready-to-land")
    return tuple(reasons)
