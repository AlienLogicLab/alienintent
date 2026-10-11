"""Work Preparation's deterministic check of a PREPARER packet (WORK-PREPARATION-REFILL R3a, spec 3.3-3.4). Pure.

WPR-A2: "the control plane refuses any packet outside the obligation's authority before anything is written". A packet
the PREPARER prepares for obligation <LABEL> passes only when its contract parses under the pending identity; names
exactly that obligation (`<plan> obligation:<LABEL>`); is issued by exactly the live tip (`plan-authority:<digest>`);
is `automatic-on`; is inside the live authority (`outside_authority` is empty: repositories, capabilities,
requirement ids, budget caps, scope inside the obligation's paths and outside protected paths); declares in its
```json alienintent-acceptance``` block a non-empty set of the obligation's own acceptance ids (the acceptance text
stays the plan's: the packet names ids, never restates them); and declares its targeted proof set. The checks that
need other contexts (the fixed closure actions, the mutations block) run in the composition.
"""
from __future__ import annotations

import json

from alienintent.context_assembly.domain.proof_set import ProofSetInvalid, parse_proof
from alienintent.context_assembly.domain.work_contract import ContractInvalid, contract_block
from alienintent.execution_coordination.domain.plan_authority import (
    ISSUER_PREFIX, PlanAuthority, obligation_labels, outside_authority)

# The identity a prepared packet carries until it is registered and bound.
PENDING = "PENDING-REGISTRATION"
OPEN, CLOSE = "```json alienintent-acceptance", "```"


class AcceptanceBlockInvalid(ValueError):
    """The packet holds more than one, or a malformed, acceptance block."""


def parse_acceptance(text: str) -> tuple[str, ...] | None:
    """The acceptance ids the packet's one acceptance block says it satisfies; None without a block;
    AcceptanceBlockInvalid for more than one, an unclosed or a malformed block (exactly `satisfies`, a non-empty list
    of distinct strings)."""
    lines = text.split("\n")
    opens = [index for index, line in enumerate(lines) if line == OPEN]
    if not opens:
        return None
    if len(opens) > 1:
        raise AcceptanceBlockInvalid("more than one acceptance block")
    close = next((index for index in range(opens[0] + 1, len(lines)) if lines[index] == CLOSE), None)
    if close is None:
        raise AcceptanceBlockInvalid("the acceptance block is not closed")
    try:
        document = json.loads("\n".join(lines[opens[0] + 1:close]))
    except ValueError as error:
        raise AcceptanceBlockInvalid(f"the acceptance block is not JSON: {error}") from None
    ids = document.get("satisfies") if isinstance(document, dict) and set(document) == {"satisfies"} else None
    if not isinstance(ids, list) or not ids or not all(isinstance(i, str) and i for i in ids) \
            or len(set(ids)) != len(ids):
        raise AcceptanceBlockInvalid("satisfies must be a non-empty list of distinct acceptance ids")
    return tuple(ids)


def check_packet(packet: bytes, authority: PlanAuthority, label: str) -> tuple[str, ...]:
    """Every reason the packet prepared for obligation `label` is refused under the live `authority`; empty when it
    passes. Nothing is written either way."""
    obligation = authority.scope.obligation(label)
    if obligation is None:
        return (f"obligation: {label} is not in the plan at the live tip",)
    try:
        contract = contract_block(packet, PENDING)
    except ContractInvalid as error:
        return (f"contract: {error}",)
    reasons = []
    if obligation_labels(contract) != (label,):
        reasons.append(f"obligation: the packet must reference exactly obligation {label}")
    if contract.authority_issuer != ISSUER_PREFIX + authority.content_digest:
        reasons.append(f"issuer: must be {ISSUER_PREFIX}{authority.content_digest}, the live tip")
    if contract.release_policy != "automatic-on":
        reasons.append("release_policy: a prepared item is automatic-on")
    reasons.extend(outside_authority(contract, authority))
    text = packet.decode("utf-8")
    try:
        satisfies = parse_acceptance(text)
    except AcceptanceBlockInvalid as error:
        reasons.append(f"acceptance: {error}")
    else:
        own = {acceptance.id for acceptance in obligation.acceptance}
        if satisfies is None:
            reasons.append("acceptance: the packet declares no acceptance block")
        elif not set(satisfies) <= own:
            reasons.append(f"acceptance: not obligation {label}'s ids: {', '.join(sorted(set(satisfies) - own))}")
    try:
        if parse_proof(text) is None:
            reasons.append("proof: the packet declares no targeted proof set")
    except ProofSetInvalid as error:
        reasons.append(f"proof: {error}")
    return tuple(reasons)
