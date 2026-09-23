"""FX-U1 assertions: changing parser, identity, scope or persistence must fail."""
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from alienintent.context_assembly.domain.inventory import (SourceSpec, SourceRecord, DefinitionSpan,
    Manifest, Provenance, assemble, classify, resolve, InventoryHold)
from alienintent.context_assembly.adapters.versioned_source import GitRequirementSource, historical_manifest
from alienintent.context_assembly.application.inventory_service import InventoryService
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.execution_coordination.ports.operational_store import VersionConflict

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/evidence/wave2-design-contracts.json"
FORMS = ("factory_plan_heading", "canonical_requirement", "recorded_as")

def source(token="SF-REQ-011", body="The system retains evidence.", form=FORMS[0], path="a.md",
           revision="r1", authority="approved", namespaces=("SF", "TEAM-X"), links=()):
    lines = {FORMS[0]: f"### {token} — Title", FORMS[1]: f"Canonical requirement: **{token}**.",
             FORMS[2]: f"Recorded as **{token} — Title**:"}
    text = lines[form] + "\n" + body + "\n"
    provenance = Provenance("local", path, revision, "fixture:"+path, "2026-09-23T00:00:00Z",
                            authority, "no-projection; source-to-inventory")
    spec = SourceSpec(path, revision, sha256(text.encode()).hexdigest(), (DefinitionSpan(1, 2, form),),
                      ((1, 2),), namespaces, provenance, "authority-"+revision, "Requirement", links)
    return SourceRecord(spec, text)

class InventoryTests(unittest.TestCase):
    def test_historical_exact_manifest(self):
        manifest = historical_manifest(CONTRACT)
        self.assertEqual(len(manifest.entries), 17)
        records = GitRequirementSource(ROOT).read(manifest)
        snapshot = assemble(manifest.project, records)
        expected = json.loads(CONTRACT.read_text())["contracts"][0]["identifier_contract"]["historical_fixture_manifest"]
        slots = sorted((e["path"], s["line"], s["form"], s["requirement_id"])
                       for e in expected["entries"] for s in e["definition_slots"])
        self.assertEqual(sorted(snapshot.definition_locators), slots)
        self.assertEqual(snapshot.referenced_ids, tuple(expected["expected"]["referenced_ids"]))
        self.assertEqual(snapshot.defined_ids, tuple(sorted({s[3] for s in slots})))
        self.assertEqual(len(snapshot.defined_ids), 53)
        self.assertEqual(snapshot.unresolved, ("SF-REQ-048", "SF-REQ-052", "SF-REQ-056"))
        self.assertEqual(snapshot.retired, ("SF-REQ-054",))
        self.assertEqual(snapshot.identifier_issues, ())
        self.assertEqual(snapshot.source_issues, ())
        self.assertEqual(sum(d.requirement_id == "SF-REQ-050" for d in snapshot.current), 1)
        self.assertEqual(resolve(snapshot, "SF-REQ-050").status, "UNVERIFIED")
        self.assertEqual(snapshot.digest, assemble(manifest.project, tuple(reversed(records))).digest)

    def test_all_forms_exact_tokens_and_issues(self):
        for form in FORMS:
            for token in ("SF-REQ-011A", "SF-REQ-1000", "TEAM-X-REQ-011"):
                with self.subTest(form=form, token=token):
                    s = assemble("p", (source(token, form=form),))
                    self.assertEqual(s.defined_ids, (token,))
                    self.assertEqual(tuple(t.raw_token for t in s.tokens if t.kind == "RequirementIdentifier"), (token,))
                    self.assertEqual(s.identifier_issues, ())
            for token, reason in (("SF-REQ-01", "UNRECOGNIZED_REQUIREMENT_ID"),
                                  ("SF-REQ-011AA", "UNRECOGNIZED_REQUIREMENT_ID"),
                                  ("SF-REQ-011-extra", "UNRECOGNIZED_REQUIREMENT_ID"),
                                  ("OTHER-REQ-011", "UNAUTHORIZED_REQUIREMENT_NAMESPACE"),
                                  ("", "MISSING_REQUIREMENT_ID"),
                                  ("SF-REQ-011 SF-REQ-012", "AMBIGUOUS_REQUIREMENT_ID")):
                with self.subTest(form=form, token=token):
                    s = assemble("p", (source(token, form=form),))
                    self.assertTrue(any(i.reason == reason and i.line == 1 for i in s.identifier_issues), s)
                    self.assertEqual(s.defined_ids, ())

    def test_reference_kinds_and_definition_rejection(self):
        examples = {
            "SF-REQ-053-AC-01": ("AcceptanceCriterionId", ()),
            "SF-REQ-001/SF-REQ-002": ("CompoundReference", ("SF-REQ-001", "SF-REQ-002")),
            "SF-REQ-030/054": ("CompoundReference", ("SF-REQ-030", "SF-REQ-054")),
            "SF-REQ-001–010": ("CompoundReference", ("SF-REQ-001", "SF-REQ-010")),
            "SF-REQ-001..010": ("CompoundReference", ("SF-REQ-001", "SF-REQ-010")),
            "SF-REQ-001-010": ("CompoundReference", ("SF-REQ-001", "SF-REQ-010")),
            "SF-REQ-007's": ("PossessiveReference", ("SF-REQ-007",)),
            "SF-REQ-018’s": ("PossessiveReference", ("SF-REQ-018",)),
        }
        for token, (kind, operands) in examples.items():
            with self.subTest(token=token):
                got = classify(token, ("SF",))
                self.assertEqual((got.kind, got.operands, got.reason), (kind, operands, None))
                self.assertEqual(got.raw_token, token)
                for form in FORMS:
                    s = assemble("p", (source(token, form=form),))
                    self.assertEqual(s.defined_ids, ())
                    self.assertTrue(any(i.reason == "WRONG_IDENTIFIER_KIND" for i in s.identifier_issues))
        self.assertEqual(classify("SF-REQ-053-AC-01", ("SF",)).parent_id, "SF-REQ-053")
        for bad in ("SF-REQ-010–001", "SF-REQ-001–0010", "SF-REQ-011AA", "SF-REQ-007'sx",
                    "SF-REQ-001–TEAM-X-REQ-010", "SF-REQ-001A–010", "SF-REQ-011-AC-1"):
            self.assertEqual(classify(bad, ("SF",)).reason, "UNRECOGNIZED_REQUIREMENT_ID")
        s = assemble("p", (source(body="[SF-REQ-007](https://host/SF-REQ-999) SF-REQ-053-AC-01"),))
        self.assertEqual(s.referenced_ids, ("SF-REQ-007", "SF-REQ-011"))
        self.assertEqual(s.identifier_issues, ())

    def test_conflicts_aliases_revision_retirement_and_local_holds(self):
        a = source(body="The system retains **evidence**. SF-REQ-002", links=("BIU:1",))
        b = source(body="The system retains evidence. SF-REQ-002", form=FORMS[1], path="b.md", links=("BIU:1",))
        s = assemble("p", (a, b))
        self.assertEqual(len(s.current), 1)
        self.assertEqual(len(s.current[0].provenance), 2)
        self.assertEqual(s.current[0].dependencies, ("SF-REQ-002",))
        self.assertEqual(s.current[0].satisfaction_links, ("BIU:1",))
        self.assertEqual(resolve(s, "SF-REQ-011").status, "ELIGIBLE_FOR_PREPARATION")
        self.assertEqual(resolve(s, "SF-REQ-002").status, "UNRESOLVED")
        conflict = assemble("p", (a, source(body="Discard evidence.", path="c.md"), source("SF-REQ-003", path="ok.md")))
        self.assertEqual(resolve(conflict, "SF-REQ-011").status, "CONFLICT")
        self.assertIsNone(resolve(conflict, "SF-REQ-011").definition)
        self.assertEqual(resolve(conflict, "SF-REQ-003").status, "ELIGIBLE_FOR_PREPARATION")
        new = assemble("p", (source(body="Retain new evidence.", revision="r2", links=("BIU:1",)),), previous=s)
        self.assertEqual(len(new.history), 2)
        self.assertEqual(new.stale_links, ("BIU:1",))
        self.assertEqual(new.prior_snapshot, s.digest)
        retired = assemble("p", (source(body="RETIRED; superseded.", links=("BIU:1",)),))
        reused = assemble("p", (source(revision="r2"),), previous=retired)
        self.assertEqual(resolve(reused, "SF-REQ-011").status, "CONFLICT")
        malformed = assemble("p", (source(body="SF-REQ-011-extra"), source("SF-REQ-003", path="ok.md")))
        self.assertEqual(resolve(malformed, "SF-REQ-011").status, "UNVERIFIED")
        self.assertEqual(resolve(malformed, "SF-REQ-003").status, "ELIGIBLE_FOR_PREPARATION")

    def test_source_scope_digest_and_provenance(self):
        manifest = historical_manifest(CONTRACT)
        reader = GitRequirementSource(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            # An excluded malformed document must never enter the explicit source list.
            root = Path(tmp)
            import subprocess
            subprocess.run(["git", "clone", "--quiet", "--no-checkout", "--shared", str(ROOT), str(root/"repo")], check=True)
            (root/"repo"/"excluded.md").write_text("SF-REQ-011-extra")
            observed = assemble(manifest.project, GitRequirementSource(root/"repo").read(manifest))
            self.assertEqual(observed.identifier_issues, ())
            self.assertNotIn("excluded.md", tuple(t.path for t in observed.tokens))
        bad = replace(manifest, entries=(replace(manifest.entries[0], digest="0"*64), *manifest.entries[1:]))
        observed = assemble(manifest.project, reader.read(bad))
        self.assertTrue(any(i.reason == "SOURCE_DIGEST_MISMATCH" for i in observed.source_issues))
        self.assertEqual(observed.status, "UNVERIFIED")
        for path in ("../secret", "/secret", "a/../../secret"):
            bad = replace(manifest, entries=(replace(manifest.entries[0], path=path),))
            self.assertTrue(reader.read(bad)[0].issue)
        a = source()
        for field in Provenance.__dataclass_fields__:
            with self.subTest(field=field):
                with self.assertRaises(InventoryHold):
                    replace(a.spec.provenance, **{field: ""})

    def test_semantic_symbols_and_retirement_mentions_are_not_normalized_away(self):
        a = source(body="Compute x*y; this requirement must not be retired.")
        b = source(body="Compute xy; this requirement must not be retired.", path="b.md")
        s = assemble("p", (a, b))
        self.assertEqual(s.retired, ())
        self.assertEqual(resolve(s, "SF-REQ-011").status, "CONFLICT")

    def test_excluded_spans_cannot_complete_markdown_pairs(self):
        a = source()
        for text, line in (("SF-REQ-011*\n", 1), ("*\nSF-REQ-011*\n", 2)):
            record = SourceRecord(replace(a.spec, digest=sha256(text.encode()).hexdigest(), definitions=(), references=((line, line),)), text)
            s = assemble("p", (record,))
            self.assertEqual(tuple(t.raw_token for t in s.tokens), ("SF-REQ-011*",))
            self.assertEqual(s.identifier_issues[0].reason, "UNRECOGNIZED_REQUIREMENT_ID")

    def test_private_history_never_downgrades_and_duplicate_returns_current_ref(self):
        from alienintent.evidence_learning.domain.refs import EvidenceHold
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repository = LocalEvidenceRepository(root/"evidence", "p", "test")
            store = SQLiteOperationalStore(root/"state.db")
            definition = Ref("p", "test", "fx-u1", "sha256:"+"a"*64, "fixture:fx-u1")
            service = InventoryService(repository, store, "p", "test", definition, "first", frozenset({"private", "public"}))
            a = source(body="CONFIDENTIAL")
            sa = assemble("p", (a,))
            ma = Manifest("p", (a.spec,), "synthetic")
            _, ref = service.publish(ma, sa, 0)
            duplicate = InventoryService(repository, store, "p", "test", definition, "second", frozenset({"private", "public"}))
            self.assertEqual(duplicate.publish(ma, sa, 1), (1, ref))
            b = source(revision="r2", body="Public revision.")
            b = replace(b, spec=replace(b.spec, access_label="public"))
            sb = assemble("p", (b,), previous=sa)
            _, ref2 = service.publish(Manifest("p", (b.spec,), "synthetic"), sb, 1)
            with self.assertRaisesRegex(EvidenceHold, "ACCESS_DENIED"):
                repository.get(ref2, frozenset({"public"}))
            empty = assemble("p", (), previous=sb)
            _, ref3 = service.publish(Manifest("p", (), "empty"), empty, 2)
            with self.assertRaisesRegex(EvidenceHold, "ACCESS_DENIED"):
                repository.get(ref3, frozenset({"public"}))

    def test_definition_ledger_inline_dependencies_and_historical_provenance(self):
        a = source(body="Depends on SF-REQ-002", form=FORMS[2])
        text = "Recorded as **SF-REQ-011**: Depends on SF-REQ-002\n"
        b = SourceRecord(replace(a.spec, path="b.md", provenance=replace(a.spec.provenance, external_identity="b.md", source_link="fixture:b.md"), digest=sha256(text.encode()).hexdigest(),
                                 definitions=(DefinitionSpan(1, 1, FORMS[2]),), references=()), text)
        s = assemble("p", (a, b))
        self.assertEqual(len(s.current), 1)
        self.assertEqual(s.current[0].dependencies, ("SF-REQ-002",))
        self.assertTrue(any(t.path == "b.md" and t.raw_token == "SF-REQ-011" for t in s.tokens))
        first = assemble("p", (a,))
        second = assemble("p", (b,), previous=first)
        self.assertEqual(len(second.history[0].provenance), 2)
        retired = assemble("p", (source(body="RETIRED"),))
        gone = assemble("p", (), previous=retired)
        self.assertEqual(resolve(gone, "SF-REQ-011").status, "RETIRED")

    def test_unpaired_markdown_never_salvages_and_plain_recorded_body_is_semantic(self):
        for token in ("SF-REQ-011*extra", "SF-REQ-011`extra", "SF-REQ-011**", "SF-REQ-011_extra"):
            s = assemble("p", (source(body=token),))
            self.assertTrue(any(t.raw_token == token and t.reason == "UNRECOGNIZED_REQUIREMENT_ID" for t in s.tokens), token)
            self.assertEqual(resolve(s, "SF-REQ-011").status, "UNVERIFIED")
        for marker in ("*", "**", "`", "__"):
            s = assemble("p", (source(body=marker+"SF-REQ-007"+marker),))
            self.assertEqual(s.identifier_issues, ())
            self.assertIn("SF-REQ-007", s.referenced_ids)
        a = source(form=FORMS[2])
        records = []
        for path, text in (("a.md", "Recorded as SF-REQ-011: Retain evidence.\n"),
                           ("b.md", "Recorded as SF-REQ-011: Discard evidence.\n")):
            records.append(SourceRecord(replace(a.spec, path=path, digest=sha256(text.encode()).hexdigest(),
                                                definitions=(DefinitionSpan(1, 1, FORMS[2]),), references=((1, 1),)), text))
        s = assemble("p", tuple(records))
        self.assertEqual(resolve(s, "SF-REQ-011").status, "CONFLICT")
        self.assertEqual({d.semantic for d in s.current}, {"Retain evidence.", "Discard evidence."})

    def test_issue_holds_only_affected_span_within_one_source(self):
        text = "### SF-REQ-011 — Title\nSF-REQ-011-extra\n### SF-REQ-003 — Title\nGood definition.\n"
        record = source()
        spec = replace(record.spec, digest=sha256(text.encode()).hexdigest(),
                       definitions=(DefinitionSpan(1, 2, FORMS[0]), DefinitionSpan(3, 4, FORMS[0])), references=((1, 4),))
        s = assemble("p", (SourceRecord(spec, text),))
        self.assertEqual(resolve(s, "SF-REQ-011").status, "UNVERIFIED")
        self.assertEqual(resolve(s, "SF-REQ-003").status, "ELIGIBLE_FOR_PREPARATION")

    def test_persistence_cas_readback_history_and_digest(self):
        from alienintent.evidence_learning.domain.refs import EvidenceHold
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repository = LocalEvidenceRepository(root/"evidence", "p", "test")
            store = SQLiteOperationalStore(root/"state.db")
            definition = Ref("p", "test", "fx-u1", "sha256:"+"a"*64, "fixture:fx-u1")
            service = InventoryService(repository, store, "p", "test", definition, "invocation", frozenset({"private"}))
            record = source()
            manifest = Manifest("p", (record.spec,), "synthetic")
            snapshot = assemble("p", (record,))
            self.assertEqual(service.read(), (0, None))
            version, ref = service.publish(manifest, snapshot, 0)
            self.assertEqual(version, 1)
            self.assertEqual(service.read()[1]["defined_ids"], ["SF-REQ-011"])
            self.assertEqual(service.publish(manifest, snapshot, 1), (1, ref))
            with self.assertRaises(VersionConflict):
                service.publish(manifest, snapshot, 0)
            with self.assertRaisesRegex(InventoryHold, "MANIFEST_DIGEST_MISMATCH"):
                service.publish(replace(manifest, entries=(replace(record.spec, digest="0"*64),)), snapshot, 1)
            changed = source(revision="r2", body="Changed definition.")
            next_manifest = Manifest("p", (changed.spec,), "synthetic")
            next_snapshot = assemble("p", (changed,), previous=snapshot)
            version2, ref2 = service.publish(next_manifest, next_snapshot, 1)
            self.assertEqual(version2, 2)
            self.assertNotEqual(ref, ref2)
            self.assertEqual(len(service.read()[1]["history"]), 2)
            self.assertEqual(repository.get(ref, frozenset({"private"})).evidence_id, "inventory.snapshot")
            (root/"evidence"/ref2.locator).write_text("corrupt")
            with self.assertRaises(EvidenceHold):
                service.read()

    def test_reference_only_and_separate_056(self):
        record = source("SF-REQ-056")
        reference = replace(record, spec=replace(record.spec, definitions=()))
        s = assemble("p", (reference,))
        self.assertEqual(s.defined_ids, ())
        self.assertEqual(resolve(s, "SF-REQ-056").status, "UNRESOLVED")
        new = assemble("p", (record,), previous=s)
        self.assertEqual(new.defined_ids, ("SF-REQ-056",))
        self.assertEqual(s.defined_ids, ())
        with self.assertRaises(InventoryHold):
            assemble("other", (record,), previous=s)

if __name__ == "__main__":
    unittest.main()
