"""Rules for assessing the exact instructions of a hand-registered work item (`work assess`).

A registered item points at its packet: a repository, a path and the exact commit. The fingerprint of an assessment
is that pointer together with the item's id, marked as a registered packet so it can never equal a fingerprint
ReadinessAdmission computes. The text sent to Agent Ready is the packet's bytes decoded as UTF-8, exactly. The latest
attempt is reused only when it assessed this fingerprint and recorded an outcome that is not a failure; an attempt
with this fingerprint and no outcome is in progress and is never assumed to be the latest. Everything here is pure.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from alienintent.context_assembly.domain.work_identity import PACKET, IdentityRetired, StoredPointer
from alienintent.execution_coordination.domain.readiness import canonical, digest

REGISTERED_PACKET = "registered-packet"
# Answers `work assess` returns instead of assessing; nothing is opened on any of them.
UNKNOWN_IDENTITY, NOT_A_REGISTERED_PACKET = "UNKNOWN_IDENTITY", "NOT_A_REGISTERED_PACKET"
IDENTITY_RETIRED, INSTRUCTIONS_NOT_TEXT = IdentityRetired.code, "INSTRUCTIONS_NOT_TEXT"
# Recovery refused: the original `work assess`, or a process carrying the attempt's marker, has not ended.
ASSESSMENT_PROCESS_RUNNING = "ASSESSMENT_PROCESS_RUNNING"
# The result-shape label recovery records an interrupted attempt's failure under, as "raised:<error>" is for a raise.
INTERRUPTED = "interrupted:operator"
# The attempt annotation naming the `work assess` process that launched (or recovered) it.
OWNER = "owner"


def registered_packet(request_ref: str) -> bool:
    """Only a hand-registered packet is assessed here; imported and compiler items keep their own evidence."""
    return request_ref.startswith(PACKET + ":")


def fingerprint(identity: str, pointer: StoredPointer) -> str:
    return digest(canonical({"kind": REGISTERED_PACKET, "id": identity, "repo": pointer.repo, "path": pointer.path,
                             "commit": pointer.commit}))


def instructions_text(packet: bytes) -> str | None:
    """The packet bytes decoded as UTF-8, exactly; None when they are not UTF-8 text."""
    try:
        return packet.decode("utf-8")
    except UnicodeDecodeError:
        return None


def reusable(latest: dict | None, input_fingerprint: str) -> bool:
    """The latest attempt is the result: it assessed this fingerprint and recorded an outcome that is not a failure."""
    return latest is not None and latest["input_fingerprint"] == input_fingerprint \
        and latest["outcome"] is not None and not latest["outcome"].get("failure_class")


def in_progress(history: Sequence[dict], input_fingerprint: str) -> dict | None:
    """The attempt with this fingerprint and no outcome, wherever it is in the item's history."""
    return next((a for a in history if a["outcome"] is None and a["input_fingerprint"] == input_fingerprint), None)


@dataclass(frozen=True)
class PacketAssessed:
    """A recorded disposition for the item's exact instructions. `assessment_ref` is the raw-output reference saved
    on the item, or None when the item's pointer moved while the run was going on (the attempt stays retained)."""
    identity: str
    attempt_id: str
    disposition: str
    assessment_ref: dict | None
    reused: bool
