"""Direct webhook adapter with raw-byte HMAC and durable receipt-before-acknowledgement."""

from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Callable, Iterator

from alienintent.execution_coordination.domain.github_delivery import DeliveryRejected, DeliveryReference, delivery_reference
from alienintent.execution_coordination.domain.webhook_authenticity import signature_valid as raw_body_signature_valid
from alienintent.execution_coordination.ports.event_ingress import EventIngress, IngressReceipt, IngressRejected
from alienintent.execution_coordination.ports.operational_store import OperationalStore, Receipt, ReservationRejected, VersionConflict


RESIDENT_INGRESS_MARKER = b"alienintent-resident-ingress"


class GitHubWebhookIngress(EventIngress):
    def __init__(self, profile: str, repository: str, secret: bytes, store: OperationalStore, notify: Callable[[str], None], project_reference: str | None = None) -> None:
        self._profile, self._repository, self._secret, self._store, self._notify = profile, repository, secret, store, notify
        self._project_reference = project_reference

    def receive(self, delivery_id: str, category: str, authenticity: str, raw_body: bytes) -> IngressReceipt:
        if not self.signature_valid(self._secret, raw_body, authenticity):
            raise IngressRejected("invalid raw-body signature")
        try:
            payload = json.loads(raw_body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise IngressRejected("unsupported payload") from error
        reference = self._admissible(payload, category)
        work, version = reference.work, reference.version
        notification = self._notification(payload, category, work)
        prior = self._store.receipt(self._profile, delivery_id)
        if prior is not None:
            self._deliver(f"ingress:{delivery_id}", notification)
            return self._ingress_receipt(delivery_id, prior)
        aggregate = f"ingress:{work}"
        current, state = self._store.read_state(self._profile, aggregate)
        prior_version = state.get("source_version", -1)
        if not isinstance(prior_version, int):
            raise IngressRejected("invalid stored source version")
        if version < prior_version:
            raise IngressRejected("stale source version held for reconciliation")
        receipt, fresh = self._store.record_receipt_if_new(self._profile, delivery_id, sha256(raw_body).hexdigest(), aggregate)
        effect_id = f"ingress:{delivery_id}"
        if fresh:
            version = self._store.apply_receipt(self._profile, delivery_id, current, {"source_version": version, "category": category}, effect_id, {"notification": notification})
        self._deliver(effect_id, notification)
        return self._ingress_receipt(delivery_id, Receipt(delivery_id, aggregate, version, "applied") if fresh else receipt)

    def _admissible(self, payload: object, category: str) -> DeliveryReference:
        """Admit only deliveries this profile owns, at the boundary each one carries.

        A repository-bearing delivery is judged against the repository the
        installation is scoped to. A `projects_v2_item` delivery names no
        repository, so the configured Project identity is the only boundary it
        can be judged against — and `organization_projects` is organization
        wide, so this comparison is the control that keeps a foreign Project's
        delivery out. It is configuration-enforced, not token-enforced.
        """
        try:
            reference = delivery_reference(payload, category)
        except DeliveryRejected as error:
            raise IngressRejected(str(error)) from error
        if reference.repository is not None:
            if reference.repository != self._repository:
                raise IngressRejected("ambiguous profile or work reference")
            return reference
        if reference.project is None or self._project_reference is None:
            raise IngressRejected("ambiguous profile or work reference")
        if reference.project != self._project_reference:
            raise IngressRejected("delivery targets a project outside this profile")
        return reference

    @staticmethod
    def signature_valid(secret: bytes, raw_body: bytes, authenticity: str) -> bool:
        """Exercise the production raw-byte signature rule without ingress effects."""
        return raw_body_signature_valid(secret, raw_body, authenticity)

    def _notification(self, payload: object, category: str, work: str) -> str:
        if isinstance(payload, dict) and payload.get("execution_field_edit") is True:
            return f"downstream-drift:{work}"
        # `issue_comment` is one of the two events this installation subscribes to:
        # a comment on the Issue that carries a BIU is an upstream product change.
        if category in {"projects_v2_item", "issues", "issue_comment", "issue_dependency"}:
            return f"upstream-product-change:{work}"
        if category == "release_command":
            return f"explicit-release-command:{work}"
        if category == "internal_execution":
            return f"internal-execution-event:{work}"
        if category == "downstream_projection":
            return f"downstream-projection-receipt:{work}"
        raise IngressRejected("unsupported event category")

    def _ingress_receipt(self, delivery_id: str, receipt: Receipt) -> IngressReceipt:
        return IngressReceipt(delivery_id, self._profile, receipt.status == "applied", f"{receipt.status}:{receipt.version}")

    def _deliver(self, effect_id: str, notification: str) -> None:
        pending = {effect.identity for effect in self._store.pending_effects(self._profile)}
        if effect_id in pending:
            self._store.claim_effect(self._profile, effect_id)
        elif effect_id not in {effect.identity for effect in self._store.unresolved_effects(self._profile)}:
            return
        self._notify(notification)
        self._store.confirm_effect(self._profile, effect_id, f"notification:{effect_id}")


@contextmanager
def serve_webhook(ingress: GitHubWebhookIngress, address: str = "127.0.0.1", port: int = 0) -> Iterator[str]:
    """Bind the resident ingress; an ephemeral port keeps offline tests isolated."""
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            """Read-only liveness for the doctor transport probe; admits nothing."""
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(RESIDENT_INGRESS_MARKER)

        def do_POST(self) -> None:  # noqa: N802
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            try:
                ingress.receive(self.headers.get("X-GitHub-Delivery", ""), self.headers.get("X-GitHub-Event", ""), self.headers.get("X-Hub-Signature-256", ""), body)
            except (IngressRejected, VersionConflict):
                self.send_response(401)
            else:
                self.send_response(202)
            self.end_headers()
        def log_message(self, format: str, *args: object) -> None: pass
    server = ThreadingHTTPServer((address, port), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://{server.server_address[0]}:{server.server_port}/webhook"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
