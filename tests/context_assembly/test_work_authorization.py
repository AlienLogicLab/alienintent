"""`work authorize`: the Founder's authorization recorded as the item's release record (acceptance checks 1-6), and
the create-only release record and shared wording check of AUTHORIZATION-CONSISTENT-WITH-LAUNCH (its checks 1-3, 6).

Every case uses the composed WorkRegistry over a temporary project database, a local clone with a local bare remote,
the `readiness` store and evidence folder, and a fixture Agent Ready executable answering the disposition written in
a file (FIXTURE_PACKAGE_NOT_AGENT_READY); nothing reaches GitHub. Packet texts, labels and quotes are TEST DATA.
"""
from __future__ import annotations

from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
import sqlite3

import pytest

from alienintent.composition.work_registry import WorkRegistry, project_configuration
from alienintent.context_assembly.application.work_authorization import (
    ALREADY_AUTHORIZED, AUTHORIZATION_STALE, AUTHORIZED_INSTRUCTIONS_FIXED, BASELINE_INVALID, GATE_WOULD_REFUSE,
    CONTRACT_UNSATISFIABLE, NOT_AUTHORIZABLE)
from alienintent.context_assembly.domain.work_contract import contract_block
from alienintent.context_assembly.domain.work_identity import Pointer
from alienintent.evidence_learning.domain.records import ref_from_document
from alienintent.execution_coordination.adapters.github_work_management import GitHubProjectsWorkManagement
from alienintent.execution_coordination.adapters.release_admission import (
    GitRevisionResolver, StoredReleaseAuthorizations)
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.release_admission import ReleasePreconditionGate
from alienintent.execution_coordination.domain.readiness import Hold
from alienintent.execution_coordination.domain.closure import ACTIONS
from alienintent.execution_coordination.domain.release import (
    BaselineEvidence, ReleaseAuthorization, ReleasePreconditionRefused, admit_release_preconditions)
from alienintent.execution_coordination.ports.operational_store import VersionConflict
from tests.context_assembly.test_initial_compilation import PROJECT, REPO, git, project_clone
from tests.context_assembly.test_readiness_consumer import fixture_package
from tests.context_assembly.test_work_contract import contract_payload
from tests.context_assembly.test_work_identity_service import commit_file

SCOPE = frozenset({"public", "private"})
QUOTE = "I authorize implementation of this unit exactly as approved."


class Fx:
    def __init__(self, root: Path) -> None:
        root.mkdir(mode=0o700)
        self.root = root
        SQLiteOperationalStore(root / "fx.sqlite")
        self.clone, _ = project_clone(root)
        self.answer = root / "disposition"
        self.answer.write_text("READY")
        executable = fixture_package(root)
        executable.write_text(f"#!/bin/sh\nprintf '{{\"disposition\": \"%s\"}}' \"$(cat '{self.answer}')\"\n")
        executable.chmod(0o700)
        self.document = {"schema_version": 1, "projects": {PROJECT: {
            "database": str(root / "work.sqlite"),
            "repositories": {REPO: {"clone": str(self.clone), "remote": "origin", "default_branch": "main",
                                    "packets_branch": "alienintent/work-packets"}},
            "packets": {"repository": REPO, "directory": "work-packets"},
            "profiles": {"fx": str(root / "fx.sqlite")},
            "readiness": {"database": str(root / "readiness.sqlite"), "evidence_root": str(root / "evidence"),
                          "executable": str(executable), "provider": "claude"},
            "github": {"repository": "AlienLogicLab/alienintent-sandbox", "application_id": 1000001,
                       "installation_id": 2000002, "private_key_path": str(root / "key.pem"), "landing": True,
                       "project": {"project_id": "PVT_kwDOfixtureSandboxProject", "project_number": 2,
                                   "organization": "AlienLogicLab", "status_field_id": "PVTSSF_s",
                                   "priority_field_id": "PVTSSF_p"}}}}}
        self.registry = self.second()
        self.service = self.registry.authorization

    def second(self) -> WorkRegistry:
        """Another registry instance over the same configuration, as another process would build it."""
        return WorkRegistry(project_configuration(self.document, PROJECT))

    def packet(self, item, payload: dict | None = None, raw: str | None = None, changes: dict | None = None) -> bytes:
        default = contract_payload(item.id, required_evidence=["independent-verifier-accepted"],
                                   budget_policy={"maximum_attempts": 1, "hard_wall_clock_seconds": 60,
                                                  "cancellation_limit": 1}, authority_references=["README.md"],
                                   required_closure_actions=list(ACTIONS))
        default.update(changes or {})
        text = raw if raw is not None else json.dumps(payload or default, indent=1)
        return f"# Work unit: {item.label}\n\n```json alienintent-contract\n{text}\n```\n".encode()

    def ready(self, label: str = "UNIT", payload: dict | None = None, raw: str | None = None,
              changes: dict | None = None):
        """Register, give the packet its contract block at a new commit and assess it: (row, attempt id)."""
        path = f"docs/{label}.md"
        first = b"# Work unit: " + label.encode() + b"\n"
        item = self.registry.records.register(first, REPO, path, commit_file(self.clone, "main", path, first), label)
        data = self.packet(item, payload, raw, changes)
        result = self.registry.assessment.assess(item.id, (data, commit_file(self.clone, "main", path, data)))
        return self.row(item.id), result.attempt_id

    def row(self, identity: str):
        return self.registry.identities.find(identity)

    def main(self) -> str:
        return git(self.clone, "rev-parse", "main").decode().strip()

    def authorize(self, item, attempt: str, *, commit: str | None = None, baseline: str | None = None,
                  quote: str = QUOTE, service=None):
        return (service or self.service).authorize(item.id, commit or item.pointer.commit, attempt,
                                                   baseline or self.main(), quote)

    def objects(self) -> set[str]:
        return {path.name for path in (self.root / "evidence" / "objects").iterdir()}

    def written(self) -> tuple:
        """Everything this command could write: both databases and the evidence folder."""
        return dump(self.root / "work.sqlite"), dump(self.root / "readiness.sqlite"), self.objects()

    def releases(self) -> StoredReleaseAuthorizations:
        """The release records read back through a fresh store, profile `registry`."""
        return StoredReleaseAuthorizations(SQLiteOperationalStore(self.root / "readiness.sqlite"), "registry")


def dump(database: Path) -> str:
    connection = sqlite3.connect(database)
    try:
        return "\n".join(connection.iterdump())
    finally:
        connection.close()


@pytest.fixture
def fx(tmp_path) -> Fx:
    return Fx(tmp_path / "fx")


def gate(fx: Fx, identity: str, authorization) -> None:
    """The release gate's own preconditions as unit 6 composes them: the clone and its default branch."""
    resolver = GitRevisionResolver({REPO: fx.clone})
    resolves = resolver.resolves(REPO, authorization.baseline)
    evidence = BaselineEvidence("main", resolves, resolves and resolver.is_reachable(REPO, authorization.baseline,
                                                                                     "main"))
    admit_release_preconditions(identity, authorization, evidence, ())


def test_unsatisfiable_contract_writes_no_release_record_then_valid_contract_authorizes(fx):
    # A historical READY assessment can exist for a packet now refused by the static guard.
    fx.registry.assessment.satisfiable = None
    item, attempt = fx.ready(changes={"required_evidence": ["unobservable"]})
    before = fx.written()
    result = fx.authorize(item, attempt)
    assert result.answer == CONTRACT_UNSATISFIABLE and result.detail.startswith("required_evidence:")
    assert fx.releases().release_authorization(item.id) is None and fx.written() == before
    fx.registry.assessment.satisfiable = fx.registry.satisfiable
    valid, valid_attempt = fx.ready(label="VALID")
    assert fx.authorize(valid, valid_attempt).answer is None


# --- check 1: binding ------------------------------------------------------------------------------------------------


def test_the_evidence_binds_the_item_and_the_release_record_is_accepted_by_the_gate(fx):
    item, attempt = fx.ready()
    baseline = fx.main()
    result = fx.authorize(item, attempt, baseline=baseline)
    assert (result.answer, result.repeated) == (None, False)
    reference = ref_from_document(result.evidence_ref)
    record = fx.registry.assessment.consumer.repository.get(reference, SCOPE)
    [entry] = fx.registry.assessment.consumer.history(item.id)
    assert json.loads(record.value) == {
        "identity": item.id, "pointer": {"repo": REPO, "path": item.pointer.path, "commit": item.pointer.commit},
        "attempt_id": attempt, "assessment_ref": asdict(item.assessment_ref),
        "contract_digest": contract_block(fx.registry.records.show(item.id).packet, item.id).content_digest,
        "baseline": baseline, "approver": "Founder", "quote": QUOTE}
    assert entry["attempt_id"] == attempt and entry["raw_ref"] == asdict(item.assessment_ref)
    assert reference.logical_id == f"work-authorization/{item.id}"
    assert fx.row(item.id).approval_ref == reference
    stored = fx.releases().release_authorization(item.id)
    assert (stored.identity, stored.authorizes_implement, stored.baseline, stored.text) == (
        item.id, True, baseline, QUOTE)
    # record_ref is the exact content digest of the stored evidence object.
    body = (fx.root / "evidence" / "objects" / reference.revision_digest.removeprefix("sha256:")).read_bytes()
    assert stored.record_ref == reference.revision_digest == "sha256:" + sha256(body).hexdigest()
    gate(fx, item.id, stored)  # Accepted: no refusal raised.
    assert asdict(stored) == result.authorization


# --- check 2: live and stale checks ----------------------------------------------------------------------------------


def parent(fx, item) -> str:
    """The commit before the item's pointer commit: a real commit that is not the pointer."""
    return git(fx.clone, "rev-parse", item.pointer.commit + "^").decode().strip()


def not_latest(fx, item, attempt):
    consumer = fx.registry.assessment.consumer
    consumer.open(item.id, "sha256:" + "1" * 64, "sha256:" + "2" * 64, None, None, None, fx.registry.assessment.binding)
    return {}


def older_pointer(fx, item, attempt):
    data = fx.registry.records.show(item.id).packet + b"\nrevised\n"
    commit = commit_file(fx.clone, "main", item.pointer.path, data)
    fx.registry.identities.set_pointer(item.id, Pointer(REPO, item.pointer.path, commit, data))
    return {"commit": commit}


def side_branch(fx, item, attempt):
    commit = commit_file(fx.clone, "side", "docs/side.md", b"side\n")
    return {"baseline": commit}


@pytest.mark.parametrize("prepare,code,detail", [
    (lambda fx, item, attempt: fx.registry.identities.retire(item.id) and {}, "IDENTITY_RETIRED", ""),
    (lambda fx, item, attempt: fx.registry.identities.set_state(item.id, "SPECIFY") and {}, NOT_AUTHORIZABLE,
     "state SPECIFY"),
    (lambda fx, item, attempt: {"commit": parent(fx, item)}, AUTHORIZATION_STALE, "--commit is not the pointer commit"),
    (lambda fx, item, attempt: {"attempt": "not-an-attempt"}, AUTHORIZATION_STALE,
     "--attempt is not the item's assessment"),
    (not_latest, AUTHORIZATION_STALE, "--attempt is not the latest attempt"),
    (older_pointer, AUTHORIZATION_STALE, "--attempt is not of the current pointer"),
    (lambda fx, item, attempt: {"baseline": fx.main()[:12]}, BASELINE_INVALID, "not an exact 40-hex commit"),
    (lambda fx, item, attempt: {"baseline": "f" * 40}, BASELINE_INVALID, f"does not resolve in {REPO}"),
    (side_branch, BASELINE_INVALID, "not reachable from main"),
    (lambda fx, item, attempt: {"quote": "Implementation is not authorized yet."}, GATE_WOULD_REFUSE,
     "authority-wording-consistent"),
])
def test_each_refusal_names_its_check_and_writes_nothing(fx, prepare, code, detail):
    item, attempt = fx.ready()
    changes = prepare(fx, item, attempt) or {}
    before = fx.written()
    item = fx.row(item.id)
    result = fx.service.authorize(item.id, changes.get("commit", item.pointer.commit), changes.get("attempt", attempt),
                                  changes.get("baseline", fx.main()), changes.get("quote", QUOTE))
    assert (result.answer, result.detail) == (code, detail)
    assert fx.written() == before and fx.releases().release_authorization(item.id) is None


def test_an_attempt_that_is_not_ready_is_stale(fx):
    fx.answer.write_text("HOLD")
    item, attempt = fx.ready()
    before = fx.written()
    result = fx.authorize(item, attempt)
    assert (result.answer, result.detail) == (AUTHORIZATION_STALE, "--attempt is not READY")
    assert fx.written() == before


def test_the_latest_ready_attempt_is_stale_when_it_is_not_the_rows_assessment(fx, monkeypatch):
    path, first = "docs/UNIT.md", b"# Work unit: UNIT\n"
    item = fx.registry.records.register(first, REPO, path, commit_file(fx.clone, "main", path, first), "UNIT")
    data = fx.packet(item)
    original = fx.registry.identities.set_evidence

    def crash(*args):
        raise RuntimeError("process died before the assessment reference was saved")

    monkeypatch.setattr(fx.registry.identities, "set_evidence", crash)
    with pytest.raises(RuntimeError):
        fx.registry.assessment.assess(item.id, (data, commit_file(fx.clone, "main", path, data)))
    monkeypatch.setattr(fx.registry.identities, "set_evidence", original)
    [entry] = fx.registry.assessment.consumer.history(item.id)
    item = fx.row(item.id)
    assert entry["outcome"]["disposition"] == "READY" and item.assessment_ref is None
    before = fx.written()
    result = fx.authorize(item, entry["attempt_id"])
    assert (result.answer, result.detail) == (AUTHORIZATION_STALE, "--attempt is not the item's assessment")
    assert fx.written() == before


@pytest.mark.parametrize("contract", [{"raw": "{not json"}, {"payload": contract_payload("another-identity")}])
def test_an_invalid_contract_block_is_refused(fx, contract):
    # A historical READY attempt can predate this static assessment guard.
    fx.registry.assessment.satisfiable = None
    item, attempt = fx.ready(**contract)
    before = fx.written()
    result = fx.authorize(item, attempt)
    assert result.answer == "CONTRACT_INVALID" and result.detail.startswith("CONTRACT_INVALID: ")
    assert fx.written() == before


def test_unknown_and_pointerless_items_are_refused(fx, monkeypatch):
    item, attempt = fx.ready()
    before = fx.written()
    assert fx.service.authorize("missing", "a" * 40, attempt, fx.main(), QUOTE).answer == "UNKNOWN_IDENTITY"
    show = fx.registry.records.show
    monkeypatch.setattr(fx.registry.records, "show", lambda name: replace(show(name), item=replace(
        show(name).item, pointer=None)))
    result = fx.authorize(item, attempt)
    assert (result.answer, result.detail) == (NOT_AUTHORIZABLE, "no packet pointer")
    assert fx.written() == before
    with pytest.raises(ValueError):
        fx.authorize(item, attempt, quote="  ")


# --- check 3: repeat and crash ---------------------------------------------------------------------------------------


def test_a_repeat_changes_nothing_in_this_or_another_process(fx):
    item, attempt = fx.ready()
    first = fx.authorize(item, attempt)
    before = fx.written()
    again = fx.authorize(item, attempt)
    other = fx.authorize(item, attempt, service=fx.second().authorization)
    assert again == other == replace(first, repeated=True)
    assert fx.written() == before


def test_a_crash_after_the_evidence_is_completed_by_the_rerun_without_a_second_record(fx, monkeypatch):
    item, attempt = fx.ready()
    before = fx.objects()

    def crash(*args):
        raise RuntimeError("process died after the evidence record")

    monkeypatch.setattr(fx.service.releases, "record", crash)
    with pytest.raises(RuntimeError):
        fx.authorize(item, attempt)
    written = fx.objects()
    assert len(written - before) == 1 and fx.releases().release_authorization(item.id) is None
    assert fx.row(item.id).approval_ref is None
    rerun = fx.authorize(item, attempt, service=fx.second().authorization)
    assert (rerun.answer, rerun.repeated) == (None, False) and fx.objects() == written
    assert fx.row(item.id).approval_ref == ref_from_document(rerun.evidence_ref)


def test_a_crash_after_the_release_record_is_repaired_by_the_rerun(fx, monkeypatch):
    item, attempt = fx.ready()

    def crash(*args):
        raise RuntimeError("process died after the release record")

    monkeypatch.setattr(fx.service.identities, "set_evidence", crash)
    with pytest.raises(RuntimeError):
        fx.authorize(item, attempt)
    written, stored = fx.objects(), fx.releases().release_authorization(item.id)
    assert stored is not None and fx.row(item.id).approval_ref is None
    rerun = fx.authorize(item, attempt, service=fx.second().authorization)
    assert (rerun.answer, rerun.repeated) == (None, True) and fx.objects() == written
    assert fx.row(item.id).approval_ref == ref_from_document(rerun.evidence_ref)
    assert fx.releases().release_authorization(item.id) == stored


# --- check 4: a different authorization ------------------------------------------------------------------------------


def test_a_different_authorization_never_replaces_the_recorded_one(fx):
    item, attempt = fx.ready()
    earlier = parent(fx, item)
    commit_file(fx.clone, "main", "docs/later.md", b"later\n")
    first = fx.authorize(item, attempt)
    stored, before = fx.releases().release_authorization(item.id), fx.written()
    assert stored.record_ref == ref_from_document(first.evidence_ref).revision_digest
    for changes, code in (({"baseline": earlier}, ALREADY_AUTHORIZED),
                          ({"quote": QUOTE + " Again."}, ALREADY_AUTHORIZED),
                          ({"commit": earlier}, AUTHORIZATION_STALE), ({"commit": fx.main()}, AUTHORIZATION_STALE)):
        assert fx.authorize(item, attempt, **changes).answer == code
    assert fx.authorize(item, "another-attempt").answer == AUTHORIZATION_STALE
    assert fx.written() == before and fx.releases().release_authorization(item.id) == stored


# --- check 5 (composed): instructions and assessment fixed ------------------------------------------------------------


def test_after_authorization_assess_neither_moves_the_pointer_nor_opens_an_attempt(fx):
    item, attempt = fx.ready()
    fx.authorize(item, attempt)
    data = fx.registry.records.show(item.id).packet + b"\nrevised\n"
    revised = commit_file(fx.clone, "main", item.pointer.path, data)
    assessment = fx.second().assessment
    assert assessment.assess(item.id, (data, revised)) == Hold(AUTHORIZED_INSTRUCTIONS_FIXED, item.id)
    assert fx.row(item.id).pointer.commit == item.pointer.commit
    reused = assessment.assess(item.id)
    assert (reused.attempt_id, reused.reused) == (attempt, True)
    assert len(assessment.consumer.history(item.id)) == 1


# --- check 6: no state change ----------------------------------------------------------------------------------------


def test_authorization_changes_no_state_and_calls_nothing_else(fx, monkeypatch):
    item, attempt = fx.ready()
    assert item.state == "CAPTURE"

    def forbidden(*args):
        raise AssertionError("authorization must not change workflow state")

    monkeypatch.setattr(fx.registry.identities, "set_state", forbidden)
    assert fx.authorize(item, attempt).answer is None
    assert fx.row(item.id).state == "CAPTURE"


# --- AUTHORIZATION-CONSISTENT-WITH-LAUNCH ----------------------------------------------------------------------------


class Interleaved:
    """One run's release records, logging each read and write to `events`. `record` first runs `meanwhile` (another
    run), so this run pauses between its "no record yet" check and its write; `after` runs once its write is done."""

    def __init__(self, name: str, releases, events: list, meanwhile=None, after=None) -> None:
        self.name, self.releases, self.events, self.meanwhile, self.after = name, releases, events, meanwhile, after

    def release_authorization(self, identity: str):
        found = self.releases.release_authorization(identity)
        self.events.append((self.name, "none" if found is None else "found"))
        return found

    def record(self, authorization) -> None:
        if self.meanwhile is not None:
            self.meanwhile()
        self.events.append((self.name, "write"))
        self.releases.record(authorization)
        if self.after is not None:
            self.after()


def run(fx: Fx, name: str, events: list, meanwhile=None, after=None):
    """Another process's `work authorize`, its release records wrapped as `Interleaved`."""
    service = fx.second().authorization
    service.releases = Interleaved(name, service.releases, events, meanwhile, after)
    return service


def stored_version(fx: Fx, identity: str) -> int:
    """How many times the item's release record was written (the store version)."""
    return SQLiteOperationalStore(fx.root / "readiness.sqlite").read_state(
        "registry", f"release-authorization:{identity}")[0]


def test_check1_a_release_record_is_never_overwritten(tmp_path):
    records = StoredReleaseAuthorizations(SQLiteOperationalStore(tmp_path / "s.sqlite"), "registry")
    first = ReleaseAuthorization("X", "sha256:" + "a" * 64, True, "b" * 40, QUOTE)
    records.record(first)
    for other in (replace(first, record_ref="sha256:" + "c" * 64, baseline="c" * 40), first):
        with pytest.raises(VersionConflict):
            records.record(other)
    assert records.release_authorization("X") == first


def test_check2_competing_authorizations_leave_one_record_and_one_approval(fx):
    item, attempt = fx.ready()
    earlier = parent(fx, item)
    commit_file(fx.clone, "main", "docs/later.md", b"later\n")
    events, results, before = [], {}, fx.objects()
    second = run(fx, "B", events)
    first = run(fx, "A", events,
                meanwhile=lambda: results.setdefault("B", fx.authorize(item, attempt, service=second)))
    results["A"] = fx.authorize(item, attempt, baseline=earlier, service=first)
    # Both runs passed the "no record yet" check before either wrote; B wrote first, A's write then conflicted.
    assert events == [("A", "none"), ("B", "none"), ("B", "write"), ("B", "found"), ("A", "write"), ("A", "found")]
    winner, loser = results["B"], results["A"]
    assert (winner.answer, winner.repeated) == (None, False)
    assert (loser.answer, loser.authorization) == (ALREADY_AUTHORIZED, winner.authorization)
    assert asdict(fx.releases().release_authorization(item.id)) == winner.authorization
    assert stored_version(fx, item.id) == 1
    assert fx.row(item.id).approval_ref == ref_from_document(winner.evidence_ref)
    assert len(fx.objects() - before) == 2  # The loser's evidence object is kept, unreferenced.


def test_check4_an_equal_record_found_after_a_conflict_is_a_repeat(fx):
    item, attempt = fx.ready()
    events, results = [], {}
    second = run(fx, "B", events)
    first = run(fx, "A", events,
                meanwhile=lambda: results.setdefault("B", fx.authorize(item, attempt, service=second)))
    results["A"] = fx.authorize(item, attempt, service=first)
    assert events == [("A", "none"), ("B", "none"), ("B", "write"), ("B", "found"), ("A", "write"), ("A", "found")]
    assert (results["B"].answer, results["B"].repeated) == (None, False)
    assert results["A"] == replace(results["B"], repeated=True)
    assert fx.row(item.id).approval_ref == ref_from_document(results["A"].evidence_ref)
    assert stored_version(fx, item.id) == 1


def test_check6_a_conflict_loser_with_the_same_baseline_and_other_words_is_refused(fx):
    item, attempt = fx.ready()
    events, results = [], {}
    second = run(fx, "B", events)
    first = run(fx, "A", events,
                meanwhile=lambda: results.setdefault("B", fx.authorize(item, attempt, service=second)))
    results["A"] = fx.authorize(item, attempt, quote=QUOTE + " Again.", service=first)
    assert events == [("A", "none"), ("B", "none"), ("B", "write"), ("B", "found"), ("A", "write"), ("A", "found")]
    winner, loser = results["B"], results["A"]
    assert (loser.answer, loser.authorization) == (ALREADY_AUTHORIZED, winner.authorization)
    assert asdict(fx.releases().release_authorization(item.id)) == winner.authorization
    assert fx.row(item.id).approval_ref == ref_from_document(winner.evidence_ref)


def test_check6_a_conflict_loser_differing_only_in_record_ref_is_refused(fx):
    item, attempt = fx.ready()
    events: list = []
    other = ReleaseAuthorization(item.id, "sha256:" + "e" * 64, True, fx.main(), QUOTE)
    lost = fx.authorize(item, attempt, service=run(fx, "A", events,
                                                   meanwhile=lambda: fx.releases().record(other)))
    assert events == [("A", "none"), ("A", "write"), ("A", "found")]
    assert (lost.answer, lost.authorization) == (ALREADY_AUTHORIZED, asdict(other))
    assert fx.releases().release_authorization(item.id) == other and fx.row(item.id).approval_ref is None


def test_check6_an_equal_conflict_loser_repairs_the_crashed_winners_approval(fx):
    item, attempt = fx.ready()
    events: list = []

    def crash() -> None:
        raise RuntimeError("process died after the release record, before approval_ref")

    def winner_crashes() -> None:
        with pytest.raises(RuntimeError, match="process died after the release record"):
            fx.authorize(item, attempt, service=run(fx, "A", events, after=crash))

    lost = fx.authorize(item, attempt, service=run(fx, "C", events, meanwhile=winner_crashes))
    assert events == [("C", "none"), ("A", "none"), ("A", "write"), ("C", "write"), ("C", "found")]
    assert (lost.answer, lost.repeated) == (None, True)
    stored = fx.releases().release_authorization(item.id)
    assert stored.record_ref == ref_from_document(lost.evidence_ref).revision_digest
    assert fx.row(item.id).approval_ref == ref_from_document(lost.evidence_ref)
    assert stored_version(fx, item.id) == 1


def launch(fx: Fx, item, records) -> None:
    """The release gate at launch over the row the READY view builds for the item (`work_registry`), imported."""
    item = fx.row(item.id)
    contract = contract_block(fx.registry.records.show(item.id).packet, item.id)
    row = {"complete": True, "membership": True, "repository": REPO, "status": "READY", "priority": "P1",
           "identity": item.id, "contract_digest": contract.content_digest, "readiness": item.assessment_ref.logical_id,
           "dependencies": list(contract.dependencies), "card": "card"}
    [ready] = GitHubProjectsWorkManagement("registry", REPO, {"READY": "READY"}, {}, lambda: (row,),
                                           contract).import_ready_snapshot()
    ReleasePreconditionGate(records, GitRevisionResolver({REPO: fx.clone}), "main").check(ready)


@pytest.mark.parametrize("changes", [{"intent": "Implementation is not authorized yet."},
                                     {"non_goals": ["none", "Release is refused pending review."]}])
def test_check3_authorization_and_launch_refuse_the_same_contract_wording(fx, tmp_path, changes):
    item, attempt = fx.ready(changes=changes)
    before = fx.written()
    result = fx.authorize(item, attempt)
    assert (result.answer, result.detail) == (GATE_WOULD_REFUSE, "authority-wording-consistent")
    assert fx.written() == before
    records = StoredReleaseAuthorizations(SQLiteOperationalStore(tmp_path / "launch.sqlite"), "registry")
    records.record(ReleaseAuthorization(item.id, "sha256:" + "a" * 64, True, fx.main(), QUOTE))
    with pytest.raises(ReleasePreconditionRefused) as refused:
        launch(fx, item, records)
    assert refused.value.check == "authority-wording-consistent"
    clean, clean_attempt = fx.ready("CLEAN")
    assert fx.authorize(clean, clean_attempt).answer is None
    launch(fx, clean, fx.releases())  # Accepted: no refusal raised.


def test_check6_crash_then_compete_then_retry(fx):
    item, attempt = fx.ready()
    earlier = parent(fx, item)
    commit_file(fx.clone, "main", "docs/later.md", b"later\n")
    events: list = []

    def crash() -> None:
        raise RuntimeError("process died after the release record, before approval_ref")

    def winner_crashes() -> None:
        with pytest.raises(RuntimeError, match="process died after the release record"):
            fx.authorize(item, attempt, service=run(fx, "A", events, after=crash))

    # C passes its "no record yet" check, then the winner A writes and crashes, then C's write conflicts.
    lost = fx.authorize(item, attempt, baseline=earlier, service=run(fx, "C", events, meanwhile=winner_crashes))
    assert events == [("C", "none"), ("A", "none"), ("A", "write"), ("C", "write"), ("C", "found")]
    stored = fx.releases().release_authorization(item.id)
    assert stored.baseline == fx.main() and fx.row(item.id).approval_ref is None
    assert (lost.answer, lost.authorization) == (ALREADY_AUTHORIZED, asdict(stored))
    competing = fx.authorize(item, attempt, baseline=earlier, service=fx.second().authorization)
    assert (competing.answer, competing.authorization) == (ALREADY_AUTHORIZED, asdict(stored))
    assert fx.releases().release_authorization(item.id) == stored and fx.row(item.id).approval_ref is None
    retry = fx.authorize(item, attempt, service=fx.second().authorization)
    assert (retry.answer, retry.repeated) == (None, True)
    assert fx.row(item.id).approval_ref == ref_from_document(retry.evidence_ref)
    assert stored.record_ref == ref_from_document(retry.evidence_ref).revision_digest
    assert fx.releases().release_authorization(item.id) == stored and stored_version(fx, item.id) == 1
