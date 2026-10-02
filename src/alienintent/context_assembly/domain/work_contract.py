"""The execution contract of a hand-written packet: one marked block inside the packet (Founder decision 2026-10-02).

The block opens on a line that is exactly OPEN and closes on the next line that is exactly CLOSE. Its content is one
JSON object, validated by the existing `contract_from_payload`, whose `identity` must be the registered item's id. No
block, two blocks, an unclosed block, invalid JSON, a validator refusal or another identity is CONTRACT_INVALID,
naming which. No other packet text is read and no field is ever inferred from prose. Everything here is pure.
"""
from __future__ import annotations

import json

from alienintent.context_assembly.domain.compilation import contract_from_payload
from alienintent.execution_coordination.domain.contract import BiuContract

OPEN, CLOSE = "```json alienintent-contract", "```"
CONTRACT_INVALID = "CONTRACT_INVALID"
# Which rule refused the block.
NOT_TEXT, MISSING, DUPLICATE, UNCLOSED = "not UTF-8 text", "no contract block", "more than one contract block", \
    "unclosed contract block"
INVALID_JSON, REFUSED, OTHER_IDENTITY = "invalid JSON", "refused by the validator", "identity is not the work item's id"


class ContractInvalid(ValueError):
    """CONTRACT_INVALID: `which` names the rule that refused the packet's contract block."""
    code = CONTRACT_INVALID

    def __init__(self, which: str, detail: str = "") -> None:
        self.which, self.detail = which, detail
        super().__init__(f"{self.code}: {which}" + (f" ({detail})" if detail else ""))


def contract_block(packet: bytes, identity: str) -> BiuContract:
    """The contract in the packet's one marked block; ContractInvalid naming the rule that refused it."""
    try:
        lines = packet.decode("utf-8").split("\n")
    except UnicodeDecodeError:
        raise ContractInvalid(NOT_TEXT) from None
    opens = [index for index, line in enumerate(lines) if line == OPEN]
    if not opens:
        raise ContractInvalid(MISSING)
    if len(opens) > 1:
        raise ContractInvalid(DUPLICATE)
    close = next((index for index in range(opens[0] + 1, len(lines)) if lines[index] == CLOSE), None)
    if close is None:
        raise ContractInvalid(UNCLOSED)
    try:
        document = json.loads("\n".join(lines[opens[0] + 1:close]))
    except ValueError as error:
        raise ContractInvalid(INVALID_JSON, str(error)) from None
    try:
        contract = contract_from_payload(document)
    except (TypeError, ValueError) as error:  # ContractValidationError is a ValueError.
        raise ContractInvalid(REFUSED, str(error)) from None
    if contract.identity != identity:
        raise ContractInvalid(OTHER_IDENTITY, str(contract.identity))
    return contract
