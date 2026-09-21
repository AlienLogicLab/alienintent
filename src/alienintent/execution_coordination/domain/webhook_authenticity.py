"""The single production raw-byte webhook signature rule.

Ingress enforces it on every delivery; pre-autonomy validation exercises the
same function so the two cannot drift.
"""

from __future__ import annotations

from hashlib import sha256
import hmac


def signature_valid(secret: bytes, raw_body: bytes, authenticity: str) -> bool:
    expected = "sha256=" + hmac.new(secret, raw_body, sha256).hexdigest()
    return hmac.compare_digest(expected, authenticity)
