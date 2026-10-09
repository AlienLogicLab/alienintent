"""Pure checks for contract facts that must allow the registry lifecycle to reach DONE."""

from __future__ import annotations

from collections.abc import Callable

from alienintent.execution_coordination.domain.closure import is_fixed
from alienintent.execution_coordination.domain.contract import BiuContract

ARTIFACT_VERIFIED = "artifact-verified"
VERIFIER_EVIDENCE = "independent-verifier-accepted"
OBSERVABLE_EVIDENCE = frozenset({ARTIFACT_VERIFIED, VERIFIER_EVIDENCE})
BASE_CAPABILITIES = frozenset({"python", "filesystem", "process-control"})


def unsatisfiable(contract: BiuContract, *, landing: bool, present_at_pointer: Callable[[str], bool],
                  registered: Callable[[str], bool], provider_dimensions: frozenset[str],
                  plan_authority: Callable[[BiuContract], tuple[str, ...]] | None = None) -> tuple[str, ...]:
    """Return one reason per failing deterministic lifecycle rule, in gate order. `automatic-on` passes only through
    `plan_authority` (the current approved plan authority's `outside_authority`), adding its reasons."""
    reasons: list[str] = []
    unknown_evidence = sorted(set(contract.required_evidence) - OBSERVABLE_EVIDENCE)
    if unknown_evidence:
        reasons.append(f"required_evidence: unobservable evidence ids: {', '.join(unknown_evidence)}")
    if contract.release_policy == "automatic-on":
        if plan_authority is None:
            reasons.append("release_policy: automatic-on requires an approved plan authority")
        else:
            reasons.extend(plan_authority(contract))
    elif contract.release_policy != "explicit-human-off":
        reasons.append("release_policy: registry releases require explicit-human-off")
    unavailable = sorted(set(contract.required_capabilities) - BASE_CAPABILITIES)
    if unavailable:
        reasons.append(f"required_capabilities: unavailable without a decision: {', '.join(unavailable)}")
    budget = contract.budget_policy
    missing_limits = [name for name in ("hard_wall_clock_seconds", "cancellation_limit")
                      if getattr(budget, name) is None]
    unsupported = sorted(set(budget.required_dimensions) - provider_dimensions)
    if missing_limits or unsupported:
        details = [*(f"{name} is required" for name in missing_limits),
                   *(f"unsupported dimension {name}" for name in unsupported)]
        reasons.append(f"budget_policy: {', '.join(details)}")
    if not is_fixed(contract.required_closure_actions):
        reasons.append("required_closure_actions: must contain exactly the five fixed closure actions")
    absent = [entry for entry in contract.authority_references
              if not present_at_pointer((entry.split() or [""])[0])]
    if absent:
        reasons.append(f"authority_references: absent at pointer: {', '.join(absent)}")
    unregistered = [entry for entry in contract.dependencies if not registered(entry)]
    if unregistered:
        reasons.append(f"dependencies: unregistered: {', '.join(unregistered)}")
    if not landing:
        reasons.append("landing: DONE is unreachable; item ends at ready-to-land")
    return tuple(reasons)
