"""B1 live trajectory receipts (WO-220504): the attention producer over the B1P capture journal. Local only.

- `consume` is one consumption pass. It reads every committed capture journal entry through the
  B1P reader, checks that the prefix it already receipted is unchanged, ensures one C1 JUDGMENT
  attention item per anomaly in the profile's attention queue (the queue C5 alerts already use),
  then appends one receipt naming every newly consumed entry. The receipt chain is the cursor.
- Attention items are ensured before the receipt commits and their identities are deterministic,
  so a pass that dies in between leaves no second item when it is rerun.
- `receipts` only reads: the chain, this producer's attention items and their reconciliation
  against the journal.
- Nothing here alerts, notifies, acknowledges, resolves or activates, and nothing changes the
  capture composition, its supervision or `alienintent-observer.service`.
"""
from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
from dataclasses import asdict
import json
from pathlib import Path
import sys

from alienintent.composition.monitor_host import EXIT_HOLD, attention, load_config, utc_micros
from alienintent.composition.trajectory_capture import capture_journal
from alienintent.control_plane.application.attention import AttentionService
from alienintent.control_plane.domain.attention import AttentionHold, AttentionOrigin
from alienintent.control_plane.domain.monitor_host import HostHold, SupervisionConfig
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.application.trajectory_capture_service import replay
from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes, ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.evidence_learning.domain.trajectory_capture import EVENT, CaptureHold, digest
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.ports.operational_store import (
    OperationalStore, ReservationRejected, SchemaIncompatible, StoreUnavailable, VersionConflict,
)

MODULE = "alienintent.composition.trajectory_receipts"
PRODUCER = "trajectory-receipts"
METHOD = "trajectory-receipt"
RECEIPT_SCHEMA = 1


class ReceiptHold(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def entry_digest(entry: Mapping[str, object]) -> str:
    return digest(dict(entry))


def prefix_digest(entries: tuple[Mapping[str, object], ...]) -> str:
    return digest([entry_digest(e) for e in entries])


class TrajectoryReceipts:
    """One consumer of one capture stream: journal in, attention items and receipts out."""

    def __init__(self, entries: Callable[[], tuple[dict[str, object], ...]], attention: AttentionService,
                 store: OperationalStore, evidence: EvidenceRepository, *, project: str, profile: str, stream: str,
                 judgment_authority: str, consumer: str) -> None:
        self.read_entries, self.attention, self.store, self.evidence = entries, attention, store, evidence
        self.project, self.profile, self.stream = project, profile, stream
        self.judgment_authority, self.consumer = judgment_authority, consumer
        self.identity = "trajectory-receipts:" + stream
        self.work_ref = "trajectory-capture:" + stream

    def _pointer(self) -> tuple[int, Ref | None]:
        try:
            version, pointer = self.store.read_state(self.profile, self.identity)
        except (StoreUnavailable, SchemaIncompatible) as error:
            raise ReceiptHold("RECEIPTS_STORE_UNAVAILABLE") from error
        if not pointer:
            return version, None
        if pointer.get("schema_version") != 1:
            raise ReceiptHold("RECEIPTS_POINTER_SCHEMA_INCOMPATIBLE")
        try:
            return version, ref_from_document(pointer["head_ref"])
        except (KeyError, TypeError, ValueError, EvidenceHold) as error:
            raise ReceiptHold("RECEIPTS_POINTER_INVALID") from error

    def chain(self) -> tuple[dict[str, object], ...]:
        """Every committed receipt, oldest first; a broken chain holds."""
        version, ref = self._pointer()
        receipts = []
        while ref is not None:
            try:
                record = self.evidence.get(ref, frozenset({"private"}))
            except EvidenceHold as error:
                raise ReceiptHold("RECEIPT_UNREADABLE:" + error.reason_code) from error
            if (not isinstance(record, Observation) or record.header.logical_id != self.identity
                    or record.method != METHOD or not isinstance(record.value, str)
                    or record.header.revision != str(version)):
                raise ReceiptHold("RECEIPT_INVALID")
            receipt = json.loads(record.value)
            if receipt.get("receipt_seq") != version:
                raise ReceiptHold("RECEIPTS_CHAIN_MISMATCH")
            receipts.append(receipt | {"receipt_ref": asdict(ref)})
            parents = record.header.preceding_refs
            if len(parents) != (0 if version == 1 else 1):
                raise ReceiptHold("RECEIPTS_CHAIN_MISMATCH")
            ref = parents[0] if parents else None
            version -= 1
        return tuple(reversed(receipts))

    def _journal(self) -> tuple[dict[str, object], ...]:
        try:
            entries = self.read_entries()
            replay(entries)
        except CaptureHold as hold:
            raise ReceiptHold("JOURNAL_UNREADABLE:" + hold.reason) from hold
        return entries

    def origin(self, entry: Mapping[str, object], anomaly: Mapping[str, object]) -> AttentionOrigin:
        revision = entry_digest(entry)
        source = Ref(self.project, self.profile, self.work_ref, revision,
                     f"{self.work_ref}#entry-{entry['entry_seq']}")
        return AttentionOrigin(self.work_ref, str(anomaly["anomaly_id"]), "JUDGMENT", revision,
                               "trajectory-anomaly:" + str(anomaly["kind"]), self.judgment_authority, PRODUCER, source)

    def _receipted(self, entries: tuple[dict[str, object], ...]) -> tuple[int, int]:
        """(receipt chain version, entries already consumed), after checking the consumed prefix."""
        version, _ = self._pointer()
        chain = self.chain() if version else ()
        consumed = chain[-1]["to_entry"] if chain else 0
        if consumed > len(entries):
            raise ReceiptHold("RECEIPTS_AHEAD_OF_JOURNAL")
        if chain and chain[-1]["prefix_digest"] != prefix_digest(entries[:consumed]):
            raise ReceiptHold("RECEIPTS_PREFIX_MISMATCH")
        return version, consumed

    def consume(self) -> dict[str, object]:
        entries = self._journal()
        version, consumed = self._receipted(entries)
        fresh = entries[consumed:]
        if not fresh:
            return {"status": "UP_TO_DATE", "receipt_seq": version, "to_entry": consumed, "consumed": 0}
        receipted = []
        for entry in fresh:
            items = []
            for anomaly in entry["anomalies"]:
                try:
                    item = self.attention.ensure(self.origin(entry, anomaly))
                except AttentionHold as hold:
                    raise ReceiptHold("ATTENTION_" + hold.reason) from hold
                items.append({"anomaly_id": anomaly["anomaly_id"], "kind": anomaly["kind"],
                              "attention": item.identity})
            event = entry["event"] if entry["kind"] == EVENT else None
            receipted.append({"entry_seq": entry["entry_seq"], "kind": entry["kind"], "launch_id": entry["launch_id"],
                              "entry_digest": entry_digest(entry), "anomalies": items,
                              "event": None if event is None else {k: event[k] for k in (
                                  "capture_seq", "event_id", "identity", "captured_at", "source", "source_seq")}})
        receipt = {"schema_version": RECEIPT_SCHEMA, "receipt_seq": version + 1, "consumer": self.consumer,
                   "stream": self.stream, "from_entry": consumed + 1, "to_entry": len(entries),
                   "prefix_digest": prefix_digest(entries), "entries": receipted}
        ref = self._append(version, receipt)
        return {"status": "RECEIPTED", "receipt_seq": version + 1, "receipt_ref": asdict(ref),
                "from_entry": consumed + 1, "to_entry": len(entries), "consumed": len(fresh),
                "events": sum(1 for e in receipted if e["event"] is not None),
                "attention": [a["attention"] for e in receipted for a in e["anomalies"]]}

    def _append(self, version: int, receipt: dict[str, object]) -> Ref:
        preceding = self._pointer()[1]
        source = Ref(self.project, self.profile, self.work_ref, receipt["prefix_digest"],
                     f"{self.work_ref}#entries-1-{receipt['to_entry']}")
        record = Observation(Header(self.project, self.profile, self.identity, str(version + 1), (source,),
            preceding_refs=() if preceding is None else (preceding,)), source, self.identity, METHOD, (source,),
            canonical_bytes(receipt).decode(), None, PRODUCER + ":" + self.consumer, self.consumer)
        try:
            ref = self.evidence.put(record)
            self.store.commit(self.profile, self.identity, version, {"schema_version": 1, "head_ref": asdict(ref)})
        except VersionConflict as error:
            raise ReceiptHold("RECEIPTS_VERSION_CONFLICT") from error
        except (StoreUnavailable, SchemaIncompatible, ReservationRejected, EvidenceHold) as error:
            raise ReceiptHold("RECEIPTS_STORE_UNAVAILABLE") from error
        return ref

    def items(self) -> tuple[dict[str, object], ...]:
        """This producer's attention items for this stream, read from the queue."""
        found = []
        for identity in self.attention.repository.identities("attention:"):
            item = self.attention.show(identity)
            if item.origin.producer == PRODUCER and item.origin.work_ref == self.work_ref:
                found.append({"identity": item.identity, "version": item.version, "status": item.status,
                              "event_identity": item.origin.event_identity, "lane": item.origin.lane,
                              "work_revision": item.origin.work_revision, "history_ref": asdict(item.history_ref)})
        return tuple(sorted(found, key=lambda i: i["event_identity"]))

    def reconcile(self) -> dict[str, object]:
        """Receipts against the journal and the queue; any gap or repeat is named, never hidden."""
        entries, chain, items = self._journal(), self.chain(), self.items()
        receipted = [e for r in chain for e in r["entries"]]
        seqs = [e["entry_seq"] for e in receipted]
        journal_events = {e["event"]["capture_seq"]: e["event"] for e in entries if e["kind"] == EVENT}
        observed = [e["event"] for e in receipted if e["event"] is not None]
        anomalies = {a["anomaly_id"]: (e, a) for e in entries for a in e["anomalies"]}
        by_anomaly: dict[str, list[dict[str, object]]] = {}
        for item in items:
            by_anomaly.setdefault(str(item["event_identity"]), []).append(item)
        mismatched_events = [s for s, e in ((o["capture_seq"], o) for o in observed)
                             if s not in journal_events or any(journal_events[s][k] != e[k] for k in e)]
        mismatched_entries = [e["entry_seq"] for e in receipted if not 1 <= e["entry_seq"] <= len(entries)
                              or entry_digest(entries[e["entry_seq"] - 1]) != e["entry_digest"]]
        report = {
            "journal_entries": len(entries), "receipts": len(chain), "receipted_entries": len(receipted),
            "entries_in_order_once": seqs == list(range(1, len(seqs) + 1)),
            "unreceipted_entries": [e["entry_seq"] for e in entries[len(seqs):]] if seqs == list(
                range(1, len(seqs) + 1)) else None,
            "journal_events": len(journal_events), "observed_events": len(observed),
            "events_observed_once": sorted(o["capture_seq"] for o in observed) == sorted(journal_events)
                                    and len(observed) == len(journal_events),
            "mismatched_events": mismatched_events, "mismatched_entries": mismatched_entries,
            "anomalies": len(anomalies), "attention_items": len(items),
            "anomalies_without_item": sorted(a for a in anomalies if a not in by_anomaly),
            "anomalies_with_duplicate_items": sorted(a for a, v in by_anomaly.items() if len(v) > 1),
            "items_without_anomaly": sorted(a for a in by_anomaly if a not in anomalies),
            "pending_items": sum(1 for i in items if i["status"] == "PENDING"),
            "anomaly_kinds": sorted({str(a["kind"]) for _, a in anomalies.values()}),
        }
        report["reconciled"] = (report["entries_in_order_once"] and report["unreceipted_entries"] == []
                                and report["events_observed_once"] and not mismatched_events
                                and not mismatched_entries
                                and not report["anomalies_without_item"]
                                and not report["anomalies_with_duplicate_items"]
                                and not report["items_without_anomaly"])
        return report


def open_receipts(config: SupervisionConfig, consumer: str,
                  clock: Callable[[], int] = utc_micros) -> TrajectoryReceipts:
    """The consumer of the supervised stream, over the same root's C5 attention profile."""
    root = Path(config.root)
    return TrajectoryReceipts(capture_journal(config, "trajectory-capture-reader").entries,
                              attention(config, consumer, clock).attention,
                              SQLiteOperationalStore(root / "trajectory-receipts.sqlite"),
                              LocalEvidenceRepository(root / "trajectory-receipts-evidence", config.project,
                                                      config.profile),
                              project=config.project, profile=config.profile, stream=config.host_invocation,
                              judgment_authority=config.judgment_authority, consumer=consumer)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=MODULE, description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("consume", "receipts"))
    parser.add_argument("--config", type=Path)
    parser.add_argument("--consumer", default="trajectory-receipts-reader")
    arguments = parser.parse_args(argv)
    try:
        receipts = open_receipts(load_config(arguments.config), arguments.consumer)
        if arguments.command == "consume":
            result: object = receipts.consume()
        else:
            result = {"receipts": list(receipts.chain()), "attention": list(receipts.items()),
                      "reconciliation": receipts.reconcile()}
    except (HostHold, ReceiptHold) as hold:
        print(json.dumps({"hold": hold.reason}), flush=True)
        return EXIT_HOLD
    print(json.dumps(result, default=str), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
