"""Durable attention handling. Delivery never supplies resolution authority."""
from collections.abc import Callable
from dataclasses import asdict
from hashlib import sha256

from alienintent.control_plane.domain.attention import (
    Acknowledgement, ActivationHold, ActivationPolicy, AttentionHold, AttentionItem, AttentionOrigin,
    DeliveryReceipt, NotificationAttempt, Resolution, ResolverGrant,
)
from alienintent.control_plane.ports.attention import (
    AttentionActivation, AttentionNotifier, AttentionPort, AttentionRepository,
)
from alienintent.evidence_learning.domain.records import canonical_bytes, ref_from_document
from alienintent.execution_coordination.ports.operational_store import VersionConflict


class AttentionService(AttentionPort):
    def __init__(self, repository: AttentionRepository, *, project: str, profile: str,
                 clock: Callable[[], str], next_id: Callable[[], str], resolvers: tuple[ResolverGrant, ...],
                 notifier: AttentionNotifier | None = None, activation: AttentionActivation | None = None,
                 activation_policy: ActivationPolicy | None = None, acknowledgers: tuple[str, ...] = ()) -> None:
        self.repository, self.project, self.profile = repository, project, profile
        self.clock, self.next_id, self.resolvers = clock, next_id, tuple(resolvers)
        self.notifier, self.activation, self.activation_policy = notifier, activation, activation_policy
        # Named human acknowledgers are trusted composition input, never a caller claim.
        self.acknowledgers = tuple(acknowledgers)

    def ensure(self, origin: AttentionOrigin) -> AttentionItem:
        if (origin.source_ref.project, origin.source_ref.profile) != (self.project, self.profile):
            raise AttentionHold("ORIGIN_SCOPE")
        identity = "attention:" + sha256(canonical_bytes([
            self.project, self.profile, origin.work_ref, origin.event_identity, origin.kind])).hexdigest()
        try:
            existing = self.show(identity)
        except KeyError:
            existing = None
        if existing is not None:
            if existing.origin != origin:
                raise AttentionHold("ORIGIN_CONFLICT")
            return existing
        body = {"origin": asdict(origin), "status": "PENDING", "attempts": [],
                "handler": None, "resolution_ref": None, "action": "CREATED", "actor": origin.producer,
                "at": self.clock()}
        self.repository.save(identity, 0, body, origin.source_ref, origin.producer, None)
        return self.show(identity)

    def show(self, identity: str) -> AttentionItem:
        if not identity.startswith("attention:"):
            raise AttentionHold("INVALID_ATTENTION_NAMESPACE")
        version, body, ref = self.repository.load(identity)
        raw_origin = dict(body["origin"])
        raw_origin["source_ref"] = ref_from_document(raw_origin["source_ref"])
        attempts = []
        for started in body["attempts"]:
            try:
                _, delivery, _ = self.repository.load(self._delivery_identity(identity, started["identity"]))
            except KeyError:
                a = started
            else:
                if delivery["item_identity"] != identity or delivery["attempt"]["identity"] != started["identity"]:
                    raise AttentionHold("DELIVERY_CORRELATION")
                a = delivery["attempt"]
            attempts.append(NotificationAttempt(a["identity"], a["status"], a["diagnostic"],
                None if a["receipt"] is None else DeliveryReceipt(**a["receipt"])))
        raw_ack = body.get("acknowledgement")
        acknowledgement = None if raw_ack is None else Acknowledgement(**(
            dict(raw_ack) | {"item_history_ref": ref_from_document(raw_ack["item_history_ref"])}))
        return AttentionItem(identity, version, AttentionOrigin(**raw_origin), body["status"], tuple(attempts),
            body["handler"], None if body["resolution_ref"] is None else ref_from_document(body["resolution_ref"]), ref,
            acknowledgement)

    def list_pending(self) -> tuple[AttentionItem, ...]:
        return tuple(item for identity in self.repository.identities("attention:")
                     if (item := self.show(identity)).status != "RESOLVED")

    def history(self, identity: str) -> tuple[dict[str, object], ...]:
        history = list(self.repository.history(identity))
        for attempt in self.show(identity).attempts:
            try:
                _, delivery, _ = self.repository.load(self._delivery_identity(identity, attempt.identity))
            except KeyError:
                continue
            history.append(delivery)
        return tuple(history)

    @staticmethod
    def _delivery_identity(identity: str, attempt: str) -> str:
        return "attention-delivery:" + sha256(canonical_bytes([identity, attempt])).hexdigest()

    def _change(self, item: AttentionItem, action: str, actor: str, **changes: object) -> AttentionItem:
        if not isinstance(actor, str) or not actor.strip():
            raise AttentionHold("ACTOR_REQUIRED")
        _, body, _ = self.repository.load(item.identity)
        body.update(changes, action=action, actor=actor, at=self.clock())
        self.repository.save(item.identity, item.version, body, item.origin.source_ref, actor, item.history_ref)
        return self.show(item.identity)

    @staticmethod
    def _version(item: AttentionItem, expected: int) -> None:
        if type(expected) is not int or expected != item.version:
            raise VersionConflict("stale attention version")

    def seen(self, identity: str, actor: str, expected_version: int) -> AttentionItem:
        item = self.show(identity)
        self._version(item, expected_version)
        if item.status == "RESOLVED":
            raise AttentionHold("ALREADY_RESOLVED")
        return self._change(item, "SEEN", actor, status="SEEN")

    def acknowledge(self, identity: str, actor: str, expected_version: int, statement: str) -> AttentionItem:
        """Human receipt of the exact version shown. SEEN, not RESOLVED: suppression and the queue stay."""
        item = self.show(identity)
        self._version(item, expected_version)
        if item.status == "RESOLVED":
            raise AttentionHold("ALREADY_RESOLVED")
        if item.acknowledgement is not None:
            raise AttentionHold("ALREADY_ACKNOWLEDGED")
        if actor not in self.acknowledgers:
            raise AttentionHold("WRONG_ACKNOWLEDGER")
        if not isinstance(statement, str) or not statement.strip():
            raise AttentionHold("STATEMENT_REQUIRED")
        receipt = Acknowledgement(identity, item.version, item.history_ref, actor, self.clock(), statement)
        return self._change(item, "ACKNOWLEDGED", actor, status="SEEN", acknowledgement=asdict(receipt))

    def resolve(self, identity: str, decision: Resolution) -> AttentionItem:
        item = self.show(identity)
        self._version(item, decision.expected_version)
        if item.status == "RESOLVED":
            raise AttentionHold("ALREADY_RESOLVED")
        # Each authority axis is explicit and independently fault-tested.
        applicable = tuple(g for g in self.resolvers if
            (g.authority, g.work_ref, g.work_revision, g.lane) ==
            (item.origin.required_authority, item.origin.work_ref, item.origin.work_revision, item.origin.lane))
        if decision.actor not in {g.actor for g in applicable}:
            raise AttentionHold("WRONG_ACTOR")
        if decision.work_revision != item.origin.work_revision:
            raise AttentionHold("WRONG_REVISION")
        if decision.lane != item.origin.lane:
            raise AttentionHold("WRONG_LANE")
        if decision.authority != item.origin.required_authority:
            raise AttentionHold("WRONG_AUTHORITY")
        if (decision.decision_ref.project, decision.decision_ref.profile) != (self.project, self.profile):
            raise AttentionHold("DECISION_SCOPE")
        self.repository.validate_resolution(item, decision)
        return self._change(item, "RESOLVED", decision.actor, status="RESOLVED",
            handler=decision.actor, resolution_ref=asdict(decision.decision_ref))

    def handle(self, origin: AttentionOrigin) -> AttentionItem:
        item = self.ensure(origin)
        if self.notifier is None or item.status == "RESOLVED" or item.attempts:
            return item
        return self.notify(item.identity, item.version)

    def notify(self, identity: str, expected_version: int) -> AttentionItem:
        item = self.show(identity)
        self._version(item, expected_version)
        if self.notifier is None or item.status == "RESOLVED":
            raise AttentionHold("NOTIFICATION_UNAVAILABLE")
        attempt_id = self.next_id()
        if not isinstance(attempt_id, str) or not attempt_id.strip() or any(a.identity == attempt_id for a in item.attempts):
            raise AttentionHold("ATTEMPT_ID_CONFLICT")
        attempt = NotificationAttempt(attempt_id, "UNCONFIRMED")
        item = self._change(item, "NOTIFICATION_STARTED", "notifier",
            attempts=[asdict(a) for a in (*item.attempts, attempt)])
        try:
            receipt = self.notifier.notify(item, attempt_id)
        except Exception as error:
            attempt = NotificationAttempt(attempt_id, "FAILED", str(error))
        else:
            if (isinstance(receipt, DeliveryReceipt) and receipt.item_identity == identity
                    and receipt.attempt_id == attempt_id and receipt.consumer and receipt.receipt_id):
                attempt = NotificationAttempt(attempt_id, "DELIVERED", receipt=receipt)
            else:
                attempt = NotificationAttempt(attempt_id, "UNCONFIRMED", "missing or wrong receipt correlation")
        # An observation has its own immutable identity/CAS, so concurrent SEEN
        # or RESOLVED handling cannot discard the known delivery outcome. No
        # delivery or decision is retried to repair a stale attention pointer.
        self.repository.save(self._delivery_identity(identity, attempt_id), 0,
            {"item_identity": identity, "attempt": asdict(attempt),
             "action": "NOTIFICATION_" + attempt.status, "actor": "notifier", "at": self.clock(),
             "started_history_ref": asdict(item.history_ref)}, item.history_ref, "notifier", None)
        return self.show(identity)

    def request_activation(self, identity: str, actor: str, expected_version: int) -> ActivationHold:
        item = self.show(identity)
        self._version(item, expected_version)
        policy = self.activation_policy
        if policy is None:
            return ActivationHold("ACTIVATION_UNBOUND")
        expected = ActivationPolicy(self.profile, identity, item.version, actor,
            item.origin.required_authority, item.origin.work_revision, item.origin.lane)
        if policy != expected or self.activation is None or item.status == "RESOLVED":
            return ActivationHold("ACTIVATION_NOT_APPLICABLE")
        # C1 deliberately has no authority-bearing episode admission. Even an
        # applicable policy cannot bypass the future fenced activation owner.
        return ActivationHold("ACTIVATION_EXECUTOR_UNBOUND")
