"""Attention is durable advisory work, separate from decision authority."""
from dataclasses import dataclass

from alienintent.evidence_learning.domain.refs import Ref


class AttentionHold(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class AttentionOrigin:
    work_ref: str
    event_identity: str
    kind: str
    work_revision: str
    lane: str
    required_authority: str
    producer: str
    source_ref: Ref

    def __post_init__(self) -> None:
        if self.kind not in {"DONE", "JUDGMENT"} or any(
            not isinstance(v, str) or not v.strip() for v in
            (self.work_ref, self.event_identity, self.work_revision, self.lane,
             self.required_authority, self.producer)
        ):
            raise AttentionHold("INVALID_ORIGIN")


@dataclass(frozen=True)
class ResolverGrant:
    actor: str
    authority: str
    work_ref: str
    work_revision: str
    lane: str


@dataclass(frozen=True)
class Resolution:
    actor: str
    authority: str
    work_revision: str
    lane: str
    expected_version: int
    decision_ref: Ref


@dataclass(frozen=True)
class DeliveryReceipt:
    item_identity: str
    attempt_id: str
    consumer: str
    receipt_id: str


@dataclass(frozen=True)
class NotificationAttempt:
    identity: str
    status: str
    diagnostic: str | None = None
    receipt: DeliveryReceipt | None = None


@dataclass(frozen=True)
class Acknowledgement:
    """Human receipt: an explicit, item-bound, timestamped act of a configured human acknowledger.

    Queue insertion, notification delivery, rendering and SEEN never produce one."""
    item_identity: str
    item_version: int
    item_history_ref: Ref
    actor: str
    at: str
    statement: str


@dataclass(frozen=True)
class AttentionItem:
    identity: str
    version: int
    origin: AttentionOrigin
    status: str
    attempts: tuple[NotificationAttempt, ...]
    handler: str | None
    resolution_ref: Ref | None
    history_ref: Ref
    acknowledgement: Acknowledgement | None = None


@dataclass(frozen=True)
class ActivationPolicy:
    """Trusted composition input, never derived from a notification or caller claim."""
    profile: str
    item_identity: str
    item_version: int
    actor: str
    authority: str
    work_revision: str
    lane: str


@dataclass(frozen=True)
class ActivationHold:
    reason: str


@dataclass(frozen=True)
class StagedAttention:
    identity: str
    version: int
    history_ref: Ref
