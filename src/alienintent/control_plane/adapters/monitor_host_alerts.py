"""Host failure alerts as C1 JUDGMENT attention: durable, deduplicated, pending until resolved.

A restart never resolves the alert; resolution stays with the alert authority (SEEN is not
RESOLVED), so the pending item survives the restart it prompted.
"""
from hashlib import sha256

from alienintent.control_plane.domain.attention import AttentionHold, AttentionOrigin
from alienintent.control_plane.domain.monitor_host import HostHold, HostOwnership
from alienintent.control_plane.ports.attention import AttentionPort
from alienintent.control_plane.ports.monitor_host import HostAlerts
from alienintent.evidence_learning.domain.records import canonical_bytes
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.execution_coordination.ports.operational_store import (
    SchemaIncompatible, StoreUnavailable, VersionConflict,
)

PRODUCER = "monitor-host-supervisor"
LANE = "monitor-host"


class AttentionHostAlerts(HostAlerts):
    def __init__(self, attention: AttentionPort, *, project: str, profile: str, required_authority: str) -> None:
        self.attention, self.project, self.profile = attention, project, profile
        self.required_authority = required_authority

    def origin(self, ownership: HostOwnership) -> AttentionOrigin:
        """Stable per launch, so every observer of the same failed launch names one item."""
        launch = [ownership.binding.unit, ownership.binding.host_invocation, ownership.launch_id]
        source = Ref(self.project, self.profile, "monitor-host:" + ownership.binding.profile,
                     "sha256:" + sha256(canonical_bytes(launch)).hexdigest(), "monitor-host-launch:" + ownership.launch_id)
        return AttentionOrigin("monitor-host:" + ownership.binding.profile, "monitor-host-alert:" + ownership.launch_id,
                               "JUDGMENT", "launch:" + ownership.launch_id, LANE, self.required_authority, PRODUCER,
                               source)

    def raise_alert(self, ownership: HostOwnership, reason: str, observation: dict[str, object]) -> str:
        try:
            return self.attention.ensure(self.origin(ownership)).identity
        except (AttentionHold, EvidenceHold, KeyError, StoreUnavailable, SchemaIncompatible, VersionConflict) as error:
            raise HostHold("ALERT_UNAVAILABLE") from error
