"""Static reachability checks for a registered work item's execution contract."""
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
    """Name each contract or host fact that prevents the deterministic path to DONE."""
    reasons = []
    unknown_evidence = set(contract.required_evidence) - OBSERVABLE_EVIDENCE
    if unknown_evidence:
        reasons.append(f"required_evidence: unobservable ids {', '.join(sorted(unknown_evidence))}")
    if contract.release_policy != "explicit-human-off":
        reasons.append("release_policy: registry release requires explicit-human-off")
    missing_capabilities = set(contract.required_capabilities) - BASE_CAPABILITIES
    if missing_capabilities:
        reasons.append(f"required_capabilities: unavailable without a decision: {', '.join(sorted(missing_capabilities))}")
    budget = contract.budget_policy
    missing_limits = [name for name in ("hard_wall_clock_seconds", "cancellation_limit")
                      if getattr(budget, name) is None]
    unsupported_dimensions = set(budget.required_dimensions) - provider_dimensions
    if missing_limits or unsupported_dimensions:
        detail = [f"missing {', '.join(missing_limits)}"] if missing_limits else []
        if unsupported_dimensions:
            detail.append(f"unsupported dimensions {', '.join(sorted(unsupported_dimensions))}")
        reasons.append(f"budget_policy: {'; '.join(detail)}")
    if not is_fixed(contract.required_closure_actions):
        reasons.append("required_closure_actions: must name each fixed closure action exactly once")
    absent_references = [entry for entry in contract.authority_references
                         if not present_at_pointer((entry.split() or [""])[0])]
    if absent_references:
        reasons.append(f"authority_references: absent at pointer: {', '.join(absent_references)}")
    absent_dependencies = [entry for entry in contract.dependencies if not registered(entry)]
    if absent_dependencies:
        reasons.append(f"dependencies: unregistered: {', '.join(absent_dependencies)}")
    if not landing:
        reasons.append("landing: DONE is unreachable; item ends at ready-to-land")
    return tuple(reasons)
