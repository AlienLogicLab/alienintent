"""`work record-completed`: an existing work item's actual approval, accepted candidate, verification and verified
landing recorded, and the row moved straight to DONE (RECORD-COMPLETED-WORK acceptance checks 1-3, 3a and the
reader of check 4).

Every case uses the composed WorkRegistry over a temporary project database, a local clone with 6c-1-shaped history
(the packet's pointer commit, a candidate branch merged into main, then the landing record on main), the `readiness`
store and evidence folder, and verdict and approval files in a temporary folder. Texts and quotes are TEST DATA.
"""
from __future__ import annotations

from base64 import b64decode
from dataclasses import asdict
from hashlib import sha256
import json
import sqlite3

import pytest

from alienintent.context_assembly.application.work_completion import (
    APPROVAL_MISSING, COORDINATOR_INCOMPLETE, COORDINATOR_OWNED, LANDING_UNVERIFIED, VERIFICATION_MISSING)
from alienintent.execution_coordination.domain.closure import ACTIONS, receipt
from alienintent.context_assembly.domain.work_contract import contract_block
from alienintent.context_assembly.domain.work_identity import Pointer
from alienintent.context_assembly.ports.work_item_repository import COMPLETION_CONFLICT, NOT_RECORDABLE
from alienintent.evidence_learning.domain.records import ref_from_document
from alienintent.evidence_learning.domain.refs import Ref
from tests.context_assembly.test_initial_compilation import REPO, git
from tests.context_assembly.test_work_authorization import Fx
from tests.context_assembly.test_work_identity_service import commit_file

SCOPE = frozenset({"private"})
QUOTE = "I approve recording this completed work."
RECORD = "docs/evidence/landing.md"


class Done:
    """One registered, assessed work item with 6c-1-shaped evidence: the arguments of a valid request."""

    def __init__(self, fx: Fx, label: str = "UNIT", changes: dict | None = None) -> None:
        self.fx = fx
        self.item, _ = fx.ready(label, changes=changes)
        self.instructions = fx.registry.records.show(self.item.id).packet
        self.digest = sha256(self.instructions).hexdigest()
        clone = fx.clone
        self.candidate = commit_file(clone, f"feature-{label}", f"src/{label}.py", b"print('candidate')\n")
        git(clone, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false",
            "merge", "-q", "--no-ff", "-m", "merge candidate", f"feature-{label}")
        self.landing = commit_file(clone, "main", RECORD, self.landing_text().encode())
        self.verdict = self.file("verdict.md", f"ACCEPT\n\n# VERIFIER verdict: work item {self.item.id}\n"
                                               f"Candidate {self.candidate}.\n")
        self.approval = self.file("approval.json", json.dumps({"item": self.item.id, "commit": self.item.pointer.commit,
                                                               "quote": "I approve"}))

    def landing_text(self, *, identity: str | None = None, candidate: str | None = None, digest: str | None = None):
        return (f"# Landing record\nWork item {identity or self.item.id}.\nCandidate {candidate or self.candidate}.\n"
                f"Packet sha256 {self.digest if digest is None else digest}.\n")

    def file(self, name: str, text: str) -> tuple[str, bytes]:
        path = self.fx.root / "given" / f"{self.item.label}-{name}"
        path.parent.mkdir(exist_ok=True)
        path.write_text(text)
        return str(path), path.read_bytes()

    def args(self, **changes) -> dict:
        return {"candidate": self.candidate, "landing": self.landing, "record_path": RECORD,
                "verifications": [self.verdict], "approval": self.approval, "quote": QUOTE} | changes

    def record(self, **changes):
        return self.fx.registry.completion.record(self.item.id, **self.args(**changes))


@pytest.fixture
def fx(tmp_path) -> Fx:
    return Fx(tmp_path / "fx")


def rows(fx: Fx) -> list[tuple]:
    connection = sqlite3.connect(fx.root / "work.sqlite")
    try:
        return connection.execute("SELECT id, label, state FROM work_item ORDER BY id").fetchall()
    finally:
        connection.close()


# --- check 1: truthful record, same identity -------------------------------------------------------------------------


def test_the_existing_row_moves_straight_to_done_with_the_evidence_exactly_as_given(fx, monkeypatch):
    done = Done(fx)
    before, count = fx.row(done.item.id), len(rows(fx))
    monkeypatch.setattr(fx.registry.items, "set_state", lambda *a: pytest.fail("a transition was walked"))
    result = done.record()
    assert (result.answer, result.repeated, result.detail) == (None, False, "")
    after = fx.row(done.item.id)
    reference = ref_from_document(result.evidence_ref)
    assert (after.id, after.label, after.pointer, after.request_ref) == (
        before.id, before.label, before.pointer, before.request_ref)
    assert (after.state, after.verification_ref, after.approval_ref) == ("DONE", reference, None)
    assert after.assessment_ref == before.assessment_ref and len(rows(fx)) == count
    stored = fx.registry.assessment.consumer.repository.get(reference, SCOPE)
    value = json.loads(stored.value)
    assert reference.logical_id == f"work-completion/{done.item.id}" and stored.evidence_id == "work-completion"
    contract = contract_block(done.instructions, done.item.id)
    files = {key: value[key] for key in ("verifications", "approval")} | {"record": value["landing"]["record"]}
    assert {key: value[key] for key in value if key not in files and key != "landing"} == {
        "identity": done.item.id,
        "pointer": {"repo": REPO, "path": done.item.pointer.path, "commit": done.item.pointer.commit},
        "contract_digest": contract.content_digest, "candidate": done.candidate, "approver": "Founder",
        "quote": QUOTE}
    assert (value["landing"]["commit"], value["landing"]["default_branch"]) == (done.landing, "main")
    given = {"record": (RECORD, done.landing_text().encode()), "approval": done.approval}
    for name, (path, data) in given.items():
        assert (files[name]["path"], b64decode(files[name]["bytes_base64"])) == (path, data)
        assert files[name]["sha256"] == sha256(data).hexdigest()
    [verdict] = files["verifications"]
    assert (verdict["path"], b64decode(verdict["bytes_base64"])) == done.verdict


# --- check 2: DONE requires verified landing evidence ----------------------------------------------------------------


def on_side(done: Done) -> dict:
    """A landing commit holding a valid landing record, but on a branch that is not the default branch."""
    git(done.fx.clone, "branch", "-q", "side-landing", done.candidate)
    return {"landing": commit_file(done.fx.clone, "side-landing", RECORD, done.landing_text().encode())}


def unmerged_candidate(done: Done) -> dict:
    other = commit_file(done.fx.clone, "other", "src/other.py", b"other\n")
    landing = commit_file(done.fx.clone, "main", RECORD, done.landing_text(candidate=other).encode())
    return {"candidate": other, "landing": landing}


def landed(done: Done, **text) -> dict:
    return {"landing": commit_file(done.fx.clone, "main", RECORD, done.landing_text(**text).encode())}


def superseded(done: Done) -> dict:
    """The approval of the superseded revision: the item's first pointer commit."""
    first = git(done.fx.clone, "rev-parse", done.item.pointer.commit + "^").decode().strip()
    return {"approval": done.file("old.json", json.dumps({"item": done.item.id, "commit": first}))}


@pytest.mark.parametrize("prepare,code,detail", [
    (on_side, LANDING_UNVERIFIED, "landing not reachable from main"),
    (unmerged_candidate, LANDING_UNVERIFIED, "candidate is not an ancestor of the landing"),
    (lambda d: {"candidate": d.candidate[:12]}, LANDING_UNVERIFIED, "candidate is not an exact 40-hex commit"),
    (lambda d: {"record_path": "docs/evidence/missing.md"}, LANDING_UNVERIFIED, "landing record missing"),
    (lambda d: landed(d, identity="another-item"), LANDING_UNVERIFIED,
     "landing record does not name the item and the candidate"),
    (lambda d: landed(d, candidate=d.candidate[:7]), LANDING_UNVERIFIED,
     "landing record does not name the item and the candidate"),
    (lambda d: landed(d, digest=""), LANDING_UNVERIFIED, "instructions"),
    (lambda d: {"landing": d.landing[:7]}, LANDING_UNVERIFIED, "landing is not an exact 40-hex commit"),
    (lambda d: {"landing": "main"}, LANDING_UNVERIFIED, "landing is not an exact 40-hex commit"),
    (lambda d: {"landing": "f" * 40}, LANDING_UNVERIFIED, f"landing does not resolve in {REPO}"),
    (lambda d: {"verifications": [d.file("reject.md", f"REJECT\n{d.item.id} {d.candidate}\n")]},
     VERIFICATION_MISSING, "no ACCEPT naming the candidate and item"),
    (lambda d: {"verifications": [d.file("other.md", f"ACCEPT\n{d.item.id} {'e' * 40}\n")]},
     VERIFICATION_MISSING, "no ACCEPT naming the candidate and item"),
    (lambda d: {"verifications": [d.file("noid.md", f"ACCEPT\n{d.candidate}\n")]},
     VERIFICATION_MISSING, "no ACCEPT naming the candidate and item"),
    (lambda d: {"approval": d.file("item.json", json.dumps({"item": "another-item", "commit": d.item.pointer.commit}))},
     APPROVAL_MISSING, "item"),
    (superseded, APPROVAL_MISSING, "commit"),
    (lambda d: {"approval": d.file("short.json", json.dumps({"item": d.item.id, "commit": d.item.pointer.commit[:7]}))},
     APPROVAL_MISSING, "commit"),
    (lambda d: {"approval": d.file("list.json", "[]")}, APPROVAL_MISSING, "not a JSON object"),
    (lambda d: {"quote": "  "}, APPROVAL_MISSING, "quote"),
    (lambda d: d.fx.registry.identities.retire(d.item.id) and {}, NOT_RECORDABLE, "retired"),
])
def test_each_refusal_names_its_check_and_writes_nothing(fx, prepare, code, detail):
    done = Done(fx)
    changes = prepare(done)
    written = fx.written()
    result = done.record(**changes)
    assert (result.answer, result.detail, result.evidence_ref) == (code, detail, None)
    assert fx.written() == written
    assert fx.row(done.item.id).verification_ref is None


def test_one_accept_among_several_verifications_is_enough(fx):
    done = Done(fx)
    first = done.file("round1.md", f"ACCEPT\n{done.item.id} on an earlier candidate {'e' * 40}\n")
    result = done.record(verifications=[first, done.verdict])
    assert result.answer is None and fx.row(done.item.id).state == "DONE"


# --- check 3: conflicts stop it --------------------------------------------------------------------------------------


def coordinator(fx: Fx, identity: str, stage: str) -> None:
    fx.registry.assessment.consumer.store.commit("registry", f"factory:{identity}", 0, {
        "stage": stage, "version": 0, "accepted": False, "closure": [], "candidate": None})


@pytest.mark.parametrize("stage", ["IMPLEMENT", "VERIFY", "ACCEPT", "DONE"])
def test_any_coordinator_record_is_coordinator_owned(fx, stage):
    """AUTOMATED-CLOSURE check 10: `work record-completed` is never a second completion path."""
    done = Done(fx)
    coordinator(fx, done.item.id, stage)
    written = fx.written()
    result = done.record()
    assert (result.answer, result.detail) == (COORDINATOR_OWNED, f"coordinator stage {stage}")
    assert fx.written() == written and fx.row(done.item.id).state != "DONE"


# --- AUTOMATED-CLOSURE check 10: the coordinator's DONE projected to the row -----------------------------------------


def closed(fx: Fx, done: Done, *, stage: str = "DONE", drop: str | None = None, version: int = 0) -> dict:
    """A coordinator record closed with the five exact receipts, the landing pushed, and its journaled order."""
    git(fx.clone, "push", "-q", "origin", "main")
    receipts = [receipt(action, done.item.id, done.candidate) for action in ACTIONS if action != drop]
    fx.registry.assessment.consumer.store.commit("registry", f"factory:{done.item.id}", version, {
        "stage": stage, "version": 4, "accepted": True, "closure": list(ACTIONS), "receipts": sorted(receipts),
        "candidate": {"kind": "source-revision", "identity": "c", "content_digest": "d", "provenance": "p",
                      "locator": f"git:origin#candidate/x@{done.candidate}", "independent_read_back_proven": True},
        "verdict": {"kind": "accept", "reason": "r", "verifier_correlation": "launch:v:2"}})
    merge = git(fx.clone, "rev-parse", "main~1").decode().strip()
    return {"event": "closure-ordered", "candidate": done.candidate, "order": {
        "base": "0" * 40, "merge": merge, "record": done.landing, "record_path": RECORD, "attempt": 1,
        "actions": list(ACTIONS), "request_sha256": "1" * 64}}


def coordinated(fx: Fx) -> tuple[Done, dict]:
    done = Done(fx, changes={"required_closure_actions": list(ACTIONS)})
    return done, closed(fx, done)


def test_record_coordinated_writes_a_real_work_completion_record_and_repeats_write_nothing(fx):
    done, order = coordinated(fx)
    result = fx.registry.completion.record_coordinated(done.item.id, order)
    assert (result.answer, result.repeated) == (None, False), result.detail
    reference = ref_from_document(result.evidence_ref)
    row = fx.row(done.item.id)
    assert (row.state, row.verification_ref) == ("DONE", reference)
    stored = fx.registry.assessment.consumer.repository.get(reference, SCOPE)
    value = json.loads(stored.value)
    assert (stored.evidence_id, reference.logical_id) == ("work-completion", f"work-completion/{done.item.id}")
    assert set(value) == {"identity", "source", "pointer", "contract_digest", "candidate", "landing", "coordinator",
                          "release_record", "approver"}
    assert (value["source"], value["candidate"], value["landing"]["commit"], value["landing"]["default_branch"]) == (
        "coordinator", done.candidate, done.landing, "main")
    assert value["coordinator"]["verdict"]["verifier_correlation"] == "launch:v:2"
    assert value["coordinator"]["receipts"] == sorted(receipt(a, done.item.id, done.candidate) for a in ACTIONS)
    assert fx.registry.completion.recorded(done.item.id) is True  # a dependent becomes admissible
    written = fx.written()
    again = fx.registry.completion.record_coordinated(done.item.id, order)
    assert (again.answer, again.repeated, again.evidence_ref) == (None, True, result.evidence_ref)
    assert fx.written() == written


@pytest.mark.parametrize("case", ["not-done", "receipt-missing", "no-order", "unreadable-remote", "record-elsewhere"])
def test_record_coordinated_refuses_and_writes_nothing(fx, case):
    done, order = coordinated(fx)
    if case in ("not-done", "receipt-missing"):
        order = closed(fx, done, stage="ACCEPT" if case == "not-done" else "DONE", version=1,
                       drop="workspaces-cleaned" if case == "receipt-missing" else None)
    if case == "unreadable-remote":
        git(fx.clone, "remote", "set-url", "origin", str(fx.root / "missing.git"))
    if case == "record-elsewhere":
        order["order"]["record"] = done.candidate  # not a commit holding the landing record
    written = fx.written()
    result = fx.registry.completion.record_coordinated(done.item.id, None if case == "no-order" else order)
    expected = COORDINATOR_INCOMPLETE if case in ("not-done", "receipt-missing") else LANDING_UNVERIFIED
    assert result.answer == expected and fx.written() == written and fx.row(done.item.id).state != "DONE"


def test_the_same_request_twice_is_a_repeat_and_other_evidence_is_completion_conflict(fx):
    done = Done(fx)
    first = done.record()
    written = fx.written()
    again = done.record()
    assert (again.answer, again.repeated, again.evidence_ref) == (None, True, first.evidence_ref)
    other = done.record(quote="Other words.")
    assert (other.answer, other.detail) == (COMPLETION_CONFLICT, "DONE with other evidence")
    assert fx.written() == written


def test_a_row_at_done_without_this_record_is_completion_conflict(fx):
    """A row already DONE with other evidence, or none (set directly: no command reaches it in this fixture)."""
    done = Done(fx)
    connection = sqlite3.connect(fx.root / "work.sqlite")
    with connection:
        connection.execute("UPDATE work_item SET state = 'DONE' WHERE id = ?", (done.item.id,))
    connection.close()
    written = fx.written()
    assert (done.record().answer, fx.written()) == (COMPLETION_CONFLICT, written)


# --- check 3a: interrupted write -------------------------------------------------------------------------------------


def test_an_interrupted_row_write_is_finished_by_the_same_request(fx, monkeypatch):
    done = Done(fx)
    objects = fx.objects()
    real = fx.registry.identities.record_completed
    calls = []

    def fail_once(*args):
        calls.append(args)
        if len(calls) == 1:
            raise RuntimeError("interrupted after the evidence write")
        return real(*args)

    monkeypatch.setattr(fx.registry.identities, "record_completed", fail_once)
    with pytest.raises(RuntimeError):
        done.record()
    row = fx.row(done.item.id)
    assert (row.state, row.verification_ref) == ("CAPTURE", None)
    [written] = fx.objects() - objects  # the evidence record, unreferenced so far
    result = done.record()
    reference = ref_from_document(result.evidence_ref)
    assert result.answer is None and fx.row(done.item.id).verification_ref == reference
    assert fx.objects() - objects == {written} == {reference.revision_digest.removeprefix("sha256:")}
    before = fx.written()
    other = done.record(verifications=[done.file("again.md", f"ACCEPT\n{done.item.id} {done.candidate} again\n")])
    assert other.answer == COMPLETION_CONFLICT and fx.written() == before


def test_a_pointer_moved_after_the_checks_writes_nothing_to_the_row(fx, monkeypatch):
    done = Done(fx)
    repository = fx.registry.completion.evidence
    real, moved = repository.put, {}

    def put_then_move(record):
        reference = real(record)
        data = done.instructions + b"\nrevised after the checks\n"
        commit = commit_file(fx.clone, "main", done.item.pointer.path, data)
        moved["row"] = fx.registry.identities.set_pointer(done.item.id, Pointer(REPO, done.item.pointer.path,
                                                                                 commit, data))
        return reference

    monkeypatch.setattr(repository, "put", put_then_move)
    result = done.record()
    assert (result.answer, result.detail) == (NOT_RECORDABLE, "pointer changed")
    row = fx.row(done.item.id)
    assert (row.state, row.verification_ref, row.pointer) == ("CAPTURE", None, moved["row"].pointer)


def test_a_row_retired_after_the_checks_is_not_recordable(fx, monkeypatch):
    done = Done(fx)
    repository = fx.registry.completion.evidence
    real = repository.put
    retire = fx.registry.identities.retire
    monkeypatch.setattr(repository, "put", lambda record: (real(record), retire(done.item.id))[0])
    assert (done.record().answer, fx.row(done.item.id).state) == (NOT_RECORDABLE, "CAPTURE")


# --- check 4: the reader dependency admission is given ---------------------------------------------------------------


def test_only_a_row_recorded_complete_with_its_own_record_reads_as_complete(fx):
    done = Done(fx)
    completion = fx.registry.completion
    assert completion.recorded(done.item.id) is False  # at CAPTURE
    reference = ref_from_document(done.record().evidence_ref)
    assert completion.recorded(done.item.id) is True
    assert completion.recorded("no-such-item") is False

    def imported(issue: str, verification: Ref | None) -> bool:
        """A row DONE from `work import` with this `--verification` reference."""
        path, data = f"docs/imported-{issue}.md", f"# imported {issue}\n".encode()
        given = {"verification": None if verification is None else asdict(verification)}
        row = fx.registry.records.import_completed(data, REPO, path, commit_file(fx.clone, "main", path, data),
                                                   f"IMPORTED-{issue}", issue, given)
        assert (row.state, row.verification_ref) == ("DONE", verification)
        return completion.recorded(row.id)

    shaped = Ref(reference.project, reference.profile, "work-completion/imported", "sha256:" + "0" * 64,
                 "objects/" + "0" * 64)
    assert imported("901", reference) is False  # a work-completion record that names another identity
    assert imported("902", shaped) is False  # shaped like one, but no evidence record exists
    assert imported("903", fx.row(done.item.id).assessment_ref) is False  # some other verification reference
    assert imported("904", None) is False  # a bare DONE
    fx.registry.identities.retire(done.item.id)
    assert completion.recorded(done.item.id) is False  # recorded complete but retired
