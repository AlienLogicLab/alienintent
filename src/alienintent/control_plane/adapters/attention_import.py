"""Read-only bootstrap snapshot staging; source remains the only active writer."""
from hashlib import sha256
import json
from pathlib import Path

from alienintent.control_plane.domain.attention import AttentionHold, StagedAttention
from alienintent.control_plane.ports.attention import AttentionMigration, AttentionRepository
from alienintent.evidence_learning.domain.records import canonical_bytes
from alienintent.evidence_learning.domain.refs import Ref


class BootstrapAttentionImport(AttentionMigration):
    def __init__(self, repository: AttentionRepository, *, project: str, profile: str,
                 max_bytes: int = 10 * 1024 * 1024) -> None:
        if type(max_bytes) is not int or max_bytes <= 0:
            raise AttentionHold("INPUT_LIMIT_HOLD")
        self.repository, self.project, self.profile = repository, project, profile
        self.max_bytes = max_bytes

    def _read(self, source: Path, permitted_root: Path) -> bytes:
        source = Path(source).resolve()
        if not source.is_relative_to(Path(permitted_root).resolve()) or not source.is_file():
            raise AttentionHold("IMPORT_PATH_HOLD")
        with source.open("rb") as stream:
            raw = stream.read(self.max_bytes + 1)
        if len(raw) > self.max_bytes:
            raise AttentionHold("INPUT_LIMIT_HOLD")
        return raw

    def stage(self, source: Path, *, permitted_root: Path, source_id: str) -> StagedAttention:
        if not isinstance(source_id, str) or not source_id.strip():
            raise AttentionHold("SOURCE_ID_REQUIRED")
        raw = self._read(source, permitted_root)
        try:
            text = raw.decode("utf-8")
            records = [json.loads(line) for line in text.splitlines() if line.strip()]
        except (ValueError, UnicodeError) as error:
            raise AttentionHold("INVALID_IMPORT") from error
        aliases, states, originals = {}, {}, {}
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get("id"), str) or not record["id"]:
                raise AttentionHold("INVALID_IMPORT_RECORD")
            ident = record["id"]
            kind = record.get("kind")
            if kind == "item":
                if ident in originals and originals[ident] != record:
                    raise AttentionHold("ALIAS_CONFLICT")
                originals[ident] = record
                alias = "attention-import:" + sha256(canonical_bytes([self.project, self.profile, source_id, ident])).hexdigest()
                aliases[ident] = alias
                states.setdefault(ident, {"status": "PENDING", "handler": None, "history": []})
            elif kind not in {"ack", "seen", "notification"} or ident not in states:
                raise AttentionHold("INVALID_IMPORT_RECORD")
            if kind == "ack":
                if not record.get("by") or not record.get("note"):
                    raise AttentionHold("UNATTRIBUTED_IMPORT_RESOLUTION")
                states[ident].update(status="RESOLVED", handler=record["by"])
            elif kind == "seen" and states[ident]["status"] != "RESOLVED":
                states[ident]["status"] = "SEEN"
            states[ident]["history"].append(record)
        identity = "attention-stage:" + sha256(canonical_bytes([self.project, self.profile, source_id])).hexdigest()
        try:
            version, prior, preceding = self.repository.load(identity)
        except KeyError:
            version, prior, preceding = 0, None, None
        if prior is not None:
            if prior["raw_source"] == text:
                return StagedAttention(identity, version, preceding)
            if not text.startswith(prior["raw_source"]):
                raise AttentionHold("SOURCE_HISTORY_REWRITE")
            if any(aliases.get(key) != value for key, value in prior["aliases"].items()):
                raise AttentionHold("ALIAS_CONFLICT")
        digest = "sha256:" + sha256(raw).hexdigest()
        source_ref = Ref(self.project, self.profile, source_id, digest, "bootstrap-snapshot:" + source_id)
        body = {"schema_version": 1, "action": "STAGED", "source_id": source_id, "raw_source": text,
                "raw_digest": digest, "records": records, "aliases": aliases, "states": states,
                "writer": "SOURCE", "promotion": "NOT_AUTHORIZED", "actor": "bootstrap-import",
                "historical_resolution_only": True}
        version, ref = self.repository.save(identity, version, body, source_ref, "bootstrap-import", preceding)
        return StagedAttention(identity, version, ref)

    def read(self, identity: str) -> dict[str, object]:
        if not identity.startswith("attention-stage:"):
            raise AttentionHold("INVALID_STAGE_NAMESPACE")
        return self.repository.load(identity)[1]

    def compare(self, identity: str, source: Path, *, permitted_root: Path) -> dict[str, object]:
        stage = self.read(identity)
        unchanged = stage["raw_digest"] == "sha256:" + sha256(self._read(source, permitted_root)).hexdigest()
        return {"source_unchanged": unchanged, "writer": "SOURCE", "promotion": "NOT_AUTHORIZED",
                "origin_ids": sorted(stage["states"]), "aliases": stage["aliases"],
                "pending_origin_ids": self.rollback(identity)["pending_origin_ids"],
                "producer_consumer_comparison": "snapshot items and attributed history only; live replacement gates outstanding"}

    def rollback(self, identity: str) -> dict[str, object]:
        stage = self.read(identity)
        return {"writer": "SOURCE", "aliases_retained": True, "snapshot_retained": True,
                "new_writer_started": False,
                "pending_origin_ids": sorted(key for key, value in stage["states"].items() if value["status"] != "RESOLVED"),
                "reconciliation": "staging has no external effects; source pending items remain source-owned"}
