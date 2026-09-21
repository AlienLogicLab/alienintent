"""Direct webhook adapter with raw-byte HMAC and durable receipt-before-acknowledgement."""

from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import hmac
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Callable, Iterator

from alienintent.execution_coordination.ports.event_ingress import EventIngress, IngressReceipt, IngressRejected
from alienintent.execution_coordination.ports.operational_store import OperationalStore, Receipt, ReservationRejected, VersionConflict


class GitHubWebhookIngress(EventIngress):
    def __init__(self, profile: str, repository: str, secret: bytes, store: OperationalStore, notify: Callable[[str], None]) -> None:
        self._profile, self._repository, self._secret, self._store, self._notify = profile, repository, secret, store, notify

    def receive(self, delivery_id: str, category: str, authenticity: str, raw_body: bytes) -> IngressReceipt:
        if not self.signature_valid(self._secret, raw_body, authenticity):
            raise IngressRejected("invalid raw-body signature")
        try:
            payload = json.loads(raw_body)
            work = payload.get("project_item", {}).get("id")
            version = payload.get("project_item", {}).get("version", 0)
        except (AttributeError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise IngressRejected("unsupported payload") from error
        if not isinstance(work, str) or not work or not isinstance(version, int):
            raise IngressRejected("ambiguous profile or work reference")
        repository_ref = payload.get("repository")
        repository = repository_ref.get("full_name") if isinstance(repository_ref, dict) else None
        if repository != self._repository:
            raise IngressRejected("ambiguous profile or work reference")
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

    @staticmethod
    def signature_valid(secret: bytes, raw_body: bytes, authenticity: str) -> bool:
        """Exercise the production raw-byte signature rule without ingress effects."""
        expected = "sha256=" + hmac.new(secret, raw_body, sha256).hexdigest()
        return hmac.compare_digest(expected, authenticity)

    def _notification(self, payload: object, category: str, work: str) -> str:
        if isinstance(payload, dict) and payload.get("execution_field_edit") is True:
            return f"downstream-drift:{work}"
        if category in {"projects_v2_item", "issues", "issue_dependency"}:
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
def serve_webhook(ingress: GitHubWebhookIngress) -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
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
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/webhook"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
