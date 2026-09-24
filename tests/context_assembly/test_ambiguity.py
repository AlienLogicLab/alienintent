"""FX-U2 assertions: questions hold only their branch; only an exact attributed decision resolves."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from alienintent.composition.upstream_profile import UpstreamProfile
from alienintent.context_assembly.application.ambiguity_service import AmbiguityService
from alienintent.context_assembly.domain.ambiguity import (AmbiguityHold, AnswerHold, QuestionResolution,
                                                          SemanticQuestion, SemanticReview)
from alienintent.context_assembly.domain.inventory import (DefinitionSpan, Manifest, Provenance, SourceRecord,
                                                           SourceSpec, assemble)
from alienintent.control_plane.application.decision_inbox import DecisionInbox
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
from alienintent.execution_coordination.domain.escalation import (DecisionRecord, DecisionRecorded,
                                                                  DecisionSubmission)
from tests.execution_coordination.test_factory_coordinator import MemoryWorkManagement, ScriptedWorker, _item

PROJECT, PROFILE, ACTOR = "AlienLogicLab/alienintent", "fx-u2", "Founder"


def body(rid, **fields):
    lines = {"Intent": "Retain attributable evidence for every decision.",
             "Scope": "evidence retention; decision attribution.", "Non-goals": "live release.",
             "Authority": "Founder decision FD-9.", "Acceptance": f"{rid}-AC-01: every decision names its actor."}
    lines.update(fields)
    return tuple(f"{label}: {value}" for label, value in lines.items() if value is not None)


def record(rid, path, lines, revision="r1", authority="approved"):
    text = f"### {rid} — Title\n" + "\n".join(lines) + "\n"
    n = len(lines) + 1
    provenance = Provenance("local", path, revision, "fixture:"+path, "2026-09-24T00:00:00Z", authority,
                            "no-projection; source-to-inventory")
    spec = SourceSpec(path, revision, sha256(text.encode()).hexdigest(), (DefinitionSpan(1, n, "factory_plan_heading"),),
                      ((1, n),), ("SF",), provenance, "authority-"+revision, "Requirement")
    return SourceRecord(spec, text)


class PermissiveAdmission:
    def validate_decision(self, record): return None
    def record_decision(self, record): return None
    def resume_after_decision(self): return None


class Harness:
    def __init__(self, root: Path, channel=True):
        root.mkdir(parents=True, exist_ok=True)
        self.store = SQLiteOperationalStore(root/"operational.sqlite")
        self.repository = LocalEvidenceRepository(root/"evidence", PROJECT, PROFILE)
        self.definition_ref = Ref(PROJECT, PROFILE, "FX-U2-contract", "sha256:"+"0"*64, "repository:docs/evidence/wo-220202-fx-u2.md")
        self.profile = UpstreamProfile(self.repository, self.store, PROJECT, PROFILE, self.definition_ref, "fx-u2-test",
                                       ACTOR, frozenset({"private"}))
        self.service = self.profile.ambiguity
        if not channel:
            self.service = AmbiguityService(self.profile.inventory, self.repository, self.store, self.profile.questions,
                                            PROJECT, PROFILE, self.definition_ref, "fx-u2-test", ACTOR, frozenset({"private"}))
        self.snapshot = None

    def publish(self, *records):
        snapshot = assemble(PROJECT, records, self.snapshot)
        version, _ = self.profile.inventory.read()
        self.profile.inventory.publish(Manifest(PROJECT, tuple(r.spec for r in records), "fx-u2"), snapshot, version)
        self.snapshot = snapshot

    def inspect(self, reviews=()):
        return self.service.inspect(self.service.read()[0], reviews)

    def answer(self, finding, actor=ACTOR, key=None, inbox=None):
        submission = DecisionSubmission(actor, "FD-9 answer", finding.work_item, 0, 0, key or "k-"+finding.finding_id[:12], "resolve")
        return (inbox or self.profile.inbox).submit(submission)

    def resolve(self, finding, decision, revision=None):
        return self.service.resolve(finding.finding_id, decision, revision or finding.requirement_revision, self.service.read()[0])

    def finding(self, report, rid, rule):
        found = [f for f in report.findings if f.requirement_id == rid and f.rule_code == rule]
        assert len(found) == 1, (rid, rule, report.findings)
        return found[0]

    def status(self, finding):
        return self.service.show(finding.finding_id)[1]


class AmbiguityTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="fx-u2-")
        self.h = Harness(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def assertHold(self, result, reason):
        self.assertIsInstance(result, AnswerHold, result)
        self.assertEqual(result.reason, reason)

    def test_missing_fields_and_conflicting_sources_open_source_linked_questions(self):
        """SF-REQ-012-AC-01."""
        h = self.h
        h.publish(record("SF-REQ-901", "901.md", body("SF-REQ-901", Intent=None)),
                  record("SF-REQ-902", "902.md", body("SF-REQ-902", Scope="evidence retention; live release")),
                  record("SF-REQ-903", "903.md", body("SF-REQ-903", Authority=None)),
                  record("SF-REQ-904", "904.md", body("SF-REQ-904", Acceptance="SF-REQ-904-AC-01: TBD.")),
                  record("SF-REQ-905", "905a.md", body("SF-REQ-905", Intent="Retain evidence.")),
                  record("SF-REQ-905", "905b.md", body("SF-REQ-905", Intent="Discard evidence.")),
                  record("SF-REQ-906", "906.md", body("SF-REQ-906")))
        report = h.inspect()
        expected = {"SF-REQ-901": ("MISSING_INTENT", (("901.md", 1, 5),)),
                    "SF-REQ-902": ("SCOPE_CONFLICT", (("902.md", 1, 6),)),
                    "SF-REQ-903": ("MISSING_AUTHORITY", (("903.md", 1, 5),)),
                    "SF-REQ-904": ("UNDEFINED_ACCEPTANCE", (("904.md", 1, 6),)),
                    "SF-REQ-905": ("CONFLICTING_SOURCES", (("905a.md", 1, 6), ("905b.md", 1, 6)))}
        open_items = {q.work_item for q in h.profile.inbox.list_open()}
        for rid, (rule, locators) in expected.items():
            with self.subTest(rid=rid):
                self.assertEqual(tuple(sorted(f.rule_code for f in report.findings if f.requirement_id == rid)), (rule,))
                f = h.finding(report, rid, rule)
                self.assertEqual(f.locators, locators)
                self.assertIn(rid, f.question)
                self.assertTrue(f.blocked_reason.startswith(rule+": "+rid+" cannot advance"))
                self.assertEqual((f.required_actor, f.origin, h.status(f)), (ACTOR, "MECHANICAL", "OPEN"))
                entry = report.requirement(rid)
                self.assertEqual(entry.preparation, "HELD")
                self.assertIn(f"{rule}:{f.finding_id}", entry.hold_reasons)
                self.assertIn(f.work_item, open_items)
        self.assertEqual(report.requirement("SF-REQ-906").mechanical_status, "COMPLETE")
        self.assertEqual(report.requirement("SF-REQ-906").preparation, "ELIGIBLE_FOR_PREPARATION")
        self.assertEqual(h.service.report(), report)

    def test_only_matching_attributed_decision_resolves_that_question(self):
        """SF-REQ-012-AC-02 and changed inputs becoming STALE."""
        h = self.h
        h.publish(record("SF-REQ-910", "910.md", body("SF-REQ-910", Intent=None, Acceptance="SF-REQ-910-AC-01: TBD")),
                  record("SF-REQ-911", "911.md", body("SF-REQ-911", Scope=None)))
        report = h.inspect()
        intent = h.finding(report, "SF-REQ-910", "MISSING_INTENT")
        acceptance = h.finding(report, "SF-REQ-910", "UNDEFINED_ACCEPTANCE")
        other = h.finding(report, "SF-REQ-911", "MISSING_SCOPE")
        decision = h.answer(intent)
        with self.assertRaises(PermissionError):
            h.answer(acceptance, actor="Mallory")
        # A reply for a different revision leaves the hold intact but is retained as evidence.
        held = h.resolve(intent, decision, "another-revision")
        self.assertHold(held, "REVISION_HOLD")
        self.assertEqual(h.status(intent), "OPEN")
        self.assertEqual(h.service.show(intent.finding_id)[2][-1]["event"], "answer_rejected")
        self.assertIsNotNone(h.repository.get(Ref(**held.evidence_ref), frozenset({"private"})))
        self.assertHold(h.resolve(acceptance, decision), "FINDING_MISMATCH")
        unrecorded = DecisionRecord(replace(decision.submission, work_item=acceptance.work_item, idempotency_key="forged"),
                                    DecisionRecorded(acceptance.work_item, 0, "forged", ACTOR))
        self.assertHold(h.resolve(acceptance, unrecorded), "AUTHORITY_HOLD")
        permissive = DecisionInbox(h.store, PermissiveAdmission(), PROFILE)
        wrong_actor = h.answer(other, actor="Mallory", inbox=permissive)
        self.assertHold(h.resolve(other, wrong_actor), "AUTHORITY_HOLD")
        self.assertEqual({h.status(f) for f in (intent, acceptance, other)}, {"OPEN"})
        self.assertEqual(h.service.report().requirement("SF-REQ-910").preparation, "HELD")
        # The exact attributed decision resolves only its own question.
        resolved = h.resolve(intent, decision)
        self.assertIsInstance(resolved, QuestionResolution)
        self.assertEqual((resolved.actor, resolved.finding_id), (ACTOR, intent.finding_id))
        self.assertEqual((h.status(intent), h.status(acceptance), h.status(other)), ("RESOLVED", "OPEN", "OPEN"))
        entry = h.service.report().requirement("SF-REQ-910")
        self.assertEqual(entry.preparation, "HELD")
        self.assertNotIn(f"MISSING_INTENT:{intent.finding_id}", entry.hold_reasons)
        self.assertEqual(h.resolve(intent, decision), resolved)
        self.assertIsInstance(h.resolve(acceptance, h.answer(acceptance)), QuestionResolution)
        self.assertEqual(h.service.report().requirement("SF-REQ-910").preparation, "ELIGIBLE_FOR_PREPARATION")
        self.assertHold(h.service.resolve(other.finding_id, wrong_actor, other.requirement_revision, 0), "STALE_INPUT")
        # Changed relevant input makes prior findings and resolutions STALE; a fresh question opens.
        h.publish(record("SF-REQ-910", "910.md", body("SF-REQ-910", Intent=None), revision="r2"),
                  record("SF-REQ-911", "911.md", body("SF-REQ-911", Scope=None)))
        self.assertHold(h.resolve(intent, decision), "STALE_INSPECTION")
        report = h.inspect()
        fresh = h.finding(report, "SF-REQ-910", "MISSING_INTENT")
        self.assertNotEqual(fresh.finding_id, intent.finding_id)
        self.assertEqual((h.status(intent), h.status(acceptance), h.status(fresh)), ("STALE", "STALE", "OPEN"))
        self.assertEqual(h.service.show(intent.finding_id)[2][-2]["status"], "RESOLVED")
        self.assertHold(h.resolve(intent, decision), "REVISION_HOLD")
        self.assertHold(h.resolve(fresh, decision), "FINDING_MISMATCH")
        self.assertEqual(report.requirement("SF-REQ-910").preparation, "HELD")
        self.assertEqual(h.status(other), "OPEN")

    def test_complete_requirement_passes_and_semantic_review_holds_without_editing_intent(self):
        """SF-REQ-012-AC-03."""
        h = self.h
        h.publish(record("SF-REQ-920", "920.md", body("SF-REQ-920")), record("SF-REQ-921", "921.md", body("SF-REQ-921")))
        before = h.inspect()
        entry = before.requirement("SF-REQ-920")
        self.assertEqual((entry.mechanical_status, entry.preparation, entry.semantic_review_status),
                         ("COMPLETE", "ELIGIBLE_FOR_PREPARATION", "NOT_RECORDED"))
        self.assertEqual(entry.fields_present, ("Acceptance", "Authority", "Intent", "Non-goals", "Scope"))
        self.assertEqual(before.findings, ())
        inventory = h.profile.inventory.read()
        review = SemanticReview("reviewer-jc", "review:jc-1", "SF-REQ-920", entry.revision,
                                (SemanticQuestion("Does 'every decision' include deferred decisions?", (("920.md", 6, 6),)),))
        stale_review = replace(review, review_ref="review:jc-old", requirement_revision="old-revision")
        self.assertHold(h.inspect((stale_review,)), "REVIEW_REVISION_MISMATCH")
        clean = SemanticReview("reviewer-jc", "review:jc-2", "SF-REQ-921", before.requirement("SF-REQ-921").revision, ())
        after = h.inspect((review, clean))
        reviewed = after.requirement("SF-REQ-920")
        finding = h.finding(after, "SF-REQ-920", "SEMANTIC_REVIEW")
        self.assertEqual((reviewed.mechanical_status, reviewed.semantic_review_status, reviewed.preparation),
                         ("COMPLETE", "RECORDED_FINDINGS", "HELD"))
        self.assertEqual((finding.origin, finding.reviewer_ref, finding.required_actor), ("SEMANTIC_REVIEW", "review:jc-1#0", ACTOR))
        self.assertIn(f"SEMANTIC_REVIEW:{finding.finding_id}", reviewed.hold_reasons)
        # Intent is not rewritten: revision, semantic body and the inventory itself are unchanged.
        self.assertEqual((reviewed.revision, reviewed.semantic_digest), (entry.revision, entry.semantic_digest))
        self.assertEqual(h.profile.inventory.read(), inventory)
        self.assertEqual(after.requirement("SF-REQ-921").semantic_review_status, "RECORDED_NO_FINDINGS")
        self.assertEqual(after.requirement("SF-REQ-921").preparation, "ELIGIBLE_FOR_PREPARATION")
        self.assertHold(h.inspect((replace(review, questions=()),)), "REVIEW_CONFLICT")
        self.assertIsInstance(h.resolve(finding, h.answer(finding)), QuestionResolution)
        self.assertEqual(h.service.report().requirement("SF-REQ-920").preparation, "ELIGIBLE_FOR_PREPARATION")

    def test_unrelated_requirement_stays_preparable_and_no_worker_launches(self):
        """SF-REQ-012-AC-04."""
        h, root = self.h, Path(self._tmp.name)
        artifacts = LocalArtifactStore(root/"producer", root/"verifier")
        worker = ScriptedWorker(artifacts, {"independent": ["success"]})
        coordinator = FactoryCoordinator(h.store, MemoryWorkManagement([_item("independent", 0, 1)]), worker, artifacts, PROFILE)
        h.publish(record("SF-REQ-930", "930.md", body("SF-REQ-930", Intent=None)),
                  record("SF-REQ-931", "931.md", body("SF-REQ-931") + ("Depends on SF-REQ-930.",)),
                  record("SF-REQ-932", "932.md", body("SF-REQ-932")))
        report = h.inspect()
        self.assertEqual([report.requirement(r).preparation for r in ("SF-REQ-930", "SF-REQ-931", "SF-REQ-932")],
                         ["HELD", "HELD", "ELIGIBLE_FOR_PREPARATION"])
        self.assertIn("DEPENDENCY_HELD:SF-REQ-930", report.requirement("SF-REQ-931").hold_reasons)
        finding = h.finding(report, "SF-REQ-930", "MISSING_INTENT")
        self.assertEqual(finding.affected, ("SF-REQ-930", "SF-REQ-931"))
        self.assertEqual(worker.dispatched, [])
        decision = h.answer(finding)
        self.assertEqual(worker.dispatched, [])
        self.assertIsInstance(h.resolve(finding, decision), QuestionResolution)
        report = h.service.report()
        self.assertEqual({r.preparation for r in report.requirements}, {"ELIGIBLE_FOR_PREPARATION"})
        self.assertEqual(worker.dispatched, [])
        self.assertEqual(h.store.pending_effects(PROFILE), ())
        self.assertEqual(h.store.recovery_reservations(PROFILE), ())
        self.assertIsNotNone(coordinator)  # Live in the same store for the whole question lifecycle.

    def test_replay_is_idempotent_and_conflicts_hold(self):
        h = self.h
        h.publish(record("SF-REQ-940", "940.md", body("SF-REQ-940", Intent=None)))
        first = h.inspect()
        version = h.service.read()[0]
        self.assertEqual(h.inspect(), first)
        self.assertEqual(h.service.read()[0], version)
        self.assertHold(h.service.inspect(version - 1), "STALE_INPUT")
        self.assertEqual(len(h.profile.inbox.list_open()), 1)
        h.store.commit(PROFILE, h.service.aggregate, version, {"schema_version": 2})
        with self.assertRaises(AmbiguityHold):
            h.inspect()

    def test_no_decision_channel_keeps_a_durable_open_finding(self):
        h = Harness(Path(self._tmp.name)/"no-channel", channel=False)
        h.publish(record("SF-REQ-950", "950.md", body("SF-REQ-950", Authority=None)),
                  record("SF-REQ-951", "951.md", body("SF-REQ-951")))
        report = h.inspect()
        finding = h.finding(report, "SF-REQ-950", "MISSING_AUTHORITY")
        self.assertEqual(h.profile.inbox.list_open(), ())
        self.assertEqual(h.status(finding), "OPEN")
        self.assertEqual(report.requirement("SF-REQ-951").preparation, "ELIGIBLE_FOR_PREPARATION")
        self.assertIsInstance(h.resolve(finding, DecisionRecord(
            DecisionSubmission(ACTOR, "x", finding.work_item, 0, 0, "k", "resolve"),
            DecisionRecorded(finding.work_item, 0, "k", ACTOR))), AnswerHold)


if __name__ == "__main__":
    unittest.main()
