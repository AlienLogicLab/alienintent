"""Neutral authenticated event-custody boundary."""

from __future__ import annotations

from dataclasses import dataclass


class IngressRejected(ValueError):
    """An event is unauthenticated, ambiguous, or stale."""


@dataclass(frozen=True)
class IngressReceipt:
    identity: str
    profile: str
    accepted: bool
    detail: str


class EventIngress:
    def receive(self, delivery_id: str, category: str, authenticity: str, raw_body: bytes) -> IngressReceipt: ...
