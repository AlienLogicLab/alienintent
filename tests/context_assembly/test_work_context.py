"""Unit 6c-1: each role's context package (acceptance checks 1-6 and 8; check 7 is in tests/control_plane/test_cli.py
and the read-only opens in the adapters' own tests).

Every case uses the composed WorkRegistry over a temporary project database and configuration file, a local clone
with a local bare remote, the `readiness` store and evidence folder, and the fixture Agent Ready executable of
test_work_authorization (FIXTURE_PACKAGE_NOT_AGENT_READY). The coordinator state and reservations are written to the
store the way FactoryCoordinator writes them. Packet texts, labels, markers and review texts are TEST DATA.
"""
from __future__ import annotations

from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path

import pytest

from alienintent.composition.work_registry import WorkRegistry, load_project_configuration
from alienintent.context_assembly.application.work_context import SelfReviewExists
from alienintent.context_assembly.domain.reconstruction import ContextHold
from alienintent.context_assembly.domain.work_context import (
    FIELDS, PRODUCER, SELF_REVIEW_EXISTS, SELF_REVIEW_LABEL, VERIFIER, ContextPackage)
from alienintent.context_assembly.domain.work_contract import contract_block
from alienintent.context_assembly.domain.work_identity import Pointer
from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes, record_ref, \
    ref_from_document
from alienintent.execution_coordination.domain.custody import CandidateRef
from alienintent.execution_coordination.ports.operational_store import StoreUnavailable
from tests.context_assembly.test_initial_compilation import PROJECT, REPO, git
from tests.context_assembly.test_work_authorization import Fx, SCOPE
from tests.context_assembly.test_work_identity_service import commit_file

MARKER = "PRODUCER-PRIVATE-MARKER-7f3a"  # Planted in the PRODUCER's transcript, invocation output and journal.
REVIEW = "Self-review: every acceptance check passes; REVIEW-TEXT-91c2."
README = "README.md the fixture project's readme"


class Cx(Fx):
    """Fx with its configuration written to a file, so the registry has a context command."""

    def __init__(self, root: Path) -> None:
        super().__init__(root)
        self.configuration_file = root / "project.json"
        self.configuration_file.write_text(json.dumps(self.document))
        self.registry = WorkRegistry(load_project_configuration(self.configuration_file, PROJECT))
        self.service, self.context = self.registry.authorization, self.registry.context
        self.store = self.registry.assessment.consumer.store

    def admitted(self, label: str = "UNIT", reserve: bool = True, **changes):
        """Registered, assessed READY, authorized and holding its WIP slot (and, with `reserve`, the repository
        reservation of its first PRODUCER launch)."""
        item, attempt = self.ready(label, changes={"authority_references": [README], **changes})
        assert self.authorize(item, attempt).answer is None
        self.store.acquire_within("registry", "wip", item.id, f"work:{item.id}", 10)
        if reserve:
            self.reserve(item, f"launch:{item.id}:0")
        return self.row(item.id)

    def reserve(self, item, correlation: str):
        """The repository reservation of the launch `correlation`, after any earlier launch released its own."""
        for held in self.store.recovery_reservations("registry"):
            if held.scope == "repository" and held.key == f"repository-{item.label}":
                self.store.release("registry", held.scope, held.key, held.owner, held.fence)
        return self.store.acquire("registry", "repository", f"repository-{item.label}", correlation)

    def digest(self, item) -> str:
        return contract_block(self.registry.records.show(item.id).packet, item.id).content_digest

    def produced(self, item, review: str | None = REVIEW):
        """The item at VERIFY on a published source-revision candidate, a fresh VERIFIER clone and (with `review`)
        the PRODUCER's recorded self-review; MARKER is planted in every PRODUCER-only record. Returns the VERIFIER's
        correlation, candidate and clone."""
        branch = f"producer/{item.label}"
        revision = commit_file(self.clone, branch, "src/candidate.py", b"print('candidate')\n")
        git(self.clone, "push", "-q", "origin", branch)
        remote = self.root / "remote.git"
        candidate = CandidateRef.source_revision("sha256:" + sha256(revision.encode()).hexdigest(),
                                                 f"git:{remote}#{branch}@{revision}").with_independent_read_back()
        clone = self.root / f"verifier-{item.label}"
        git(self.root, "clone", "-q", str(remote), str(clone))
        encoded = {"kind": str(candidate.kind), "identity": candidate.identity, "content_digest":
                   candidate.content_digest, "locator": candidate.locator, "provenance": candidate.provenance,
                   "independent_read_back_proven": True}
        state = {"stage": "VERIFY", "version": 2, "accepted": False, "closure": [], "candidate": encoded,
                 "implement_cycles": 1, "verify_cycles": 1, "rejections": 0,
                 "findings": [{"source": "verify", "correlation": "launch:earlier", "candidate": "earlier",
                               "findings": ["an earlier VERIFIER finding"]}],
                 # The PRODUCER's transcript and invocation output as raw coordinator fields: never carried.
                 "producer_correlation": MARKER, "correlation": MARKER, "outcome": MARKER, "receipts": [MARKER],
                 "verdict": {"reason": MARKER}, "transcript": MARKER, "invocation_candidate": {"locator": MARKER}}
        # The PRODUCER launch's journal entry (its effect payload) carries the marker too.
        self.store.commit_with_effect("registry", f"factory:{item.id}", 0, state, f"launch:{item.id}:0",
                                      {"correlation": f"launch:{item.id}:0", "role": "PRODUCER", "output": MARKER})
        self.store.claim_effect("registry", f"launch:{item.id}:0")  # The PRODUCER ran and reported.
        self.store.confirm_effect("registry", f"launch:{item.id}:0", "outcome:candidate")
        consumer = self.registry.assessment.consumer  # The PRODUCER's invocation output kept as evidence.
        consumer.repository.put(Observation(Header(PROJECT, consumer.profile, "producer-output", "1",
                                                   (self.context.definition,)),
                                            self.context.definition, "producer-output", "v1", (), MARKER, None,
                                            "producer", "producer"))
        if review is not None:
            self.context.record_self_review(item.id, candidate, review)
        correlation = f"launch:{item.id}:1"
        self.reserve(item, correlation)
        return correlation, candidate, clone


@pytest.fixture
def cx(tmp_path) -> Cx:
    return Cx(tmp_path / "cx")


def hold(result, reason: str, *refs: str) -> None:
    assert isinstance(result, ContextHold), result
    assert (str(result.reason), result.affected_refs[:len(refs)]) == (reason, refs), result


# --- checks 1 and 4: what each role receives, for the exact attempt --------------------------------------------------


def test_a_first_producer_gets_exactly_its_fields_from_the_records(cx):
    item = cx.admitted()
    record = cx.registry.records.show(item.id)
    package = cx.context.assemble(item.id, PRODUCER, f"launch:{item.id}:0", cx.digest(item))
    assert isinstance(package, ContextPackage)
    fields = package.fields
    assert set(fields) == FIELDS[PRODUCER] and "producer_self_review" not in fields and "diff" not in fields
    assert fields["instructions"]["text"].encode() == git(cx.clone, "show", f"{item.pointer.commit}:{item.pointer.path}")
    assert (fields["instructions"]["commit"], fields["instructions"]["path"]) == (item.pointer.commit, item.pointer.path)
    contract = contract_block(record.packet, item.id)
    assert fields["contract"] == {"block": json.loads(json.dumps(contract.canonical_payload())),
                                  "content_digest": contract.content_digest}
    assert fields["goal"] == contract.intent
    release = cx.releases().release_authorization(item.id)
    assert fields["release_record"]["record_ref"] == release.record_ref == item.approval_ref.revision_digest
    assert fields["release_record"]["evidence"]["quote"] == release.text
    assert fields["starting_revision"] == release.baseline == cx.main()
    [entry] = cx.registry.assessment.consumer.history(item.id)
    assert fields["assessment"] == {"assessment_ref": asdict(item.assessment_ref), "attempt_id": entry["attempt_id"],
                                    "input_fingerprint": entry["input_fingerprint"]}
    assert fields["allowed_scope"] == {"authorized_scope": ["src"], "excluded_scope": ["none"]}
    assert fields["stop_condition"] == {"completion_criteria": ["tests"], "maximum_attempts": 1}
    assert fields["escalation_condition"] == ["scope"]
    # Attempt 1: no coordinator state yet is version 0 with no cycles, not a hold.
    assert fields["attempt"] == 0
    assert fields["history"] == {"stage": None, "version": None, "implement_cycles": 0, "verify_cycles": 0,
                                 "rejections": 0, "findings": []}
    assert fields["resources"]["wip"]["owner"] == f"work:{item.id}"
    assert fields["resources"]["repository"]["owner"] == f"launch:{item.id}:0"
    assert fields["resources"]["cleanup"] == {"required_closure_actions": ["merge"],
                                              "candidate_custody_requirements": ["merge"]}
    command = fields["context_command"]
    assert command["argv"][1:] == ["--profile-factory", "alienintent.composition.work_registry:work_context_profile",
                                   "--json", "work", "context", item.id, "--role", PRODUCER, "--correlation",
                                   f"launch:{item.id}:0", "--contract-digest", cx.digest(item)]
    assert Path(command["argv"][0]).is_absolute() and Path(command["argv"][0]).name == "alienintent"
    assert command["environment"] == {"ALIENINTENT_PROJECT_CONFIGURATION": str(cx.configuration_file.resolve()),
                                      "ALIENINTENT_PROJECT": PROJECT}


def test_the_verifier_gets_its_fields_and_never_the_producers_output(cx):
    item = cx.admitted()
    correlation, candidate, clone = cx.produced(item)
    package = cx.context.assemble(item.id, VERIFIER, correlation, cx.digest(item), candidate.locator, clone)
    assert isinstance(package, ContextPackage)
    fields = package.fields
    assert set(fields) == FIELDS[VERIFIER] and "assessment" not in fields
    revision = candidate.locator.rpartition("@")[2]
    assert fields["candidate"]["identity"] == candidate.identity and fields["candidate"]["locator"] == candidate.locator
    assert fields["diff"]["text"].encode() == git(clone, "diff", "--no-ext-diff", "--no-color", cx.main(), revision)
    assert "src/candidate.py" in fields["diff"]["text"]
    assert fields["history"]["findings"] == [{"source": "verify", "correlation": "launch:earlier",
                                              "candidate": "earlier", "findings": ["an earlier VERIFIER finding"]}]
    document = json.dumps(package.document())
    assert MARKER not in document  # Not the transcript, the invocation output or the journal entry.
    # The self-review only under its own field with the fixed label; never in findings.
    assert fields["producer_self_review"]["label"] == SELF_REVIEW_LABEL
    assert fields["producer_self_review"]["text"] == REVIEW
    assert document.count("REVIEW-TEXT-91c2") == 1 and "REVIEW-TEXT" not in json.dumps(fields["history"])
    assert fields["context_command"]["argv"][-4:] == ["--candidate", candidate.locator, "--contract-digest",
                                                      cx.digest(item)]
    # The exact CandidateRef is accepted the same way as its locator.
    assert cx.context.assemble(item.id, VERIFIER, correlation, cx.digest(item), candidate, clone) == package


# --- checks 2 and 4: missing facts prevent launch --------------------------------------------------------------------


def unassessed(cx):
    """Registered with a valid contract block, never assessed."""
    path = "docs/RAW.md"
    item = cx.registry.records.register(b"# raw\n", REPO, path, commit_file(cx.clone, "main", path, b"# raw\n"), "RAW")
    data = cx.packet(item)
    commit = commit_file(cx.clone, "main", path, data)
    cx.registry.identities.set_pointer(item.id, Pointer(REPO, path, commit, data))
    return cx.row(item.id)


def unauthorized(cx):
    item, _ = cx.ready("PLAIN", changes={"authority_references": [README]})
    return cx.row(item.id)


def no_evidence(cx):
    item = cx.admitted()
    (cx.root / "evidence" / "objects" / item.approval_ref.revision_digest.removeprefix("sha256:")).unlink()
    return item


@pytest.mark.parametrize("prepare,reason,refs", [
    (lambda cx: replace(cx.admitted(), id="no-such-item"), "MISSING_RECORD", ("work_item",)),
    (lambda cx: cx.registry.identities.retire(cx.admitted().id), "MISSING_RECORD", ("work_item",)),
    (lambda cx: cx.registry.identities.register("requirement:SF-REQ-9", "NO-POINTER", "BIU"), "MISSING_RECORD",
     ("work_item",)),
    (unassessed, "MISSING_RECORD", ("assessment",)),
    (unauthorized, "MISSING_RECORD", ("release_record",)),
    (no_evidence, "MISSING_RECORD", ("release_record",)),
    (lambda cx: cx.admitted(reserve=False), "MISSING_RECORD", ("resources", "repository")),
    (lambda cx: cx.admitted(dependencies=["unregistered-dependency"]), "MISSING_RECORD",
     ("dependencies", "unregistered-dependency")),
    (lambda cx: cx.admitted(authority_references=["docs/not-at-the-commit.md"]), "MISSING_RECORD",
     ("design_rules", "docs/not-at-the-commit.md")),
    (lambda cx: cx.admitted(authority_references=["a vault note, not a path"]), "MISSING_RECORD", ("design_rules",)),
])
def test_each_missing_fact_is_a_hold_naming_it(cx, prepare, reason, refs):
    item = prepare(cx)
    hold(cx.context.assemble(item.id, PRODUCER, f"launch:{item.id}:0", None), reason, *refs)


def test_a_missing_wip_reservation_and_a_malformed_contract_or_state_are_holds(cx):
    item = cx.admitted()
    wip = next(r for r in cx.store.recovery_reservations("registry") if r.scope == "wip")
    cx.store.release("registry", "wip", wip.key, wip.owner, wip.fence)
    hold(cx.context.assemble(item.id, PRODUCER, f"launch:{item.id}:0", None), "MISSING_RECORD", "resources", "wip")
    other = cx.admitted("BROKEN")
    cx.store.commit("registry", f"factory:{other.id}", 0, {"stage": "NOT-A-STAGE"})
    hold(cx.context.assemble(other.id, PRODUCER, f"launch:{other.id}:1", None), "MALFORMED_RECORD", "history")
    invalid, _ = cx.ready("INVALID", raw="{not json")
    hold(cx.context.assemble(invalid.id, PRODUCER, f"launch:{invalid.id}:0", None), "MALFORMED_RECORD", "contract")


def test_unreadable_evidence_and_store_are_their_own_holds(cx, monkeypatch):
    item, other = cx.admitted(), cx.admitted("OTHER")
    (cx.root / "evidence" / "objects" / item.approval_ref.revision_digest.removeprefix("sha256:")).write_bytes(b"x")
    hold(cx.context.assemble(item.id, PRODUCER, f"launch:{item.id}:0", None), "EVIDENCE_UNAVAILABLE", "release_record")

    def unavailable(*_):
        raise StoreUnavailable("database is locked")
    monkeypatch.setattr(cx.store, "recovery_reservations", unavailable)
    hold(cx.context.assemble(other.id, PRODUCER, f"launch:{other.id}:0", None), "STORE_UNAVAILABLE", "resources")


def test_the_verifier_is_held_without_a_candidate_or_its_self_review(cx):
    """Handoff step 8: no candidate in the coordinator state and no self-review record are MISSING_RECORD."""
    item = cx.admitted()
    clone = cx.root / "nowhere"
    hold(cx.context.assemble(item.id, VERIFIER, f"launch:{item.id}:0", None, None, clone), "MISSING_RECORD",
         "candidate")
    other = cx.admitted("OTHER")
    correlation, candidate, clone = cx.produced(other, review=None)
    hold(cx.context.assemble(other.id, VERIFIER, correlation, None, candidate.locator, clone), "MISSING_RECORD",
         "producer_self_review")


# --- check 3: conflicting facts prevent launch -----------------------------------------------------------------------


def evidence_differs(cx, item, field: str, value: object) -> None:
    """Replace the release evidence with one whose `field` differs, keeping approval_ref and record_ref bound to it."""
    consumer = cx.registry.assessment.consumer
    original = consumer.repository.get(item.approval_ref, SCOPE)
    values = json.loads(original.value) | {field: value}
    changed = replace(original, value=canonical_bytes(values).decode())
    reference = consumer.repository.put(changed)
    cx.registry.identities.set_evidence(item.id, "approval", reference)
    _, release = cx.store.read_state("registry", f"release-authorization:{item.id}")
    cx.store.commit("registry", f"release-authorization:{item.id}", 1, release | {"record_ref":
                                                                                   reference.revision_digest})


@pytest.mark.parametrize("change,refs", [
    (lambda cx, item: cx.store.commit("registry", f"release-authorization:{item.id}", 1, cx.store.read_state(
        "registry", f"release-authorization:{item.id}")[1] | {"record_ref": "sha256:" + "0" * 64}),
     ("release_record", "record_ref")),
    (lambda cx, item: evidence_differs(cx, item, "pointer", {"repo": REPO, "path": "x", "commit": "0" * 40}),
     ("release_record", "pointer")),
    (lambda cx, item: evidence_differs(cx, item, "attempt_id", "another-attempt"), ("release_record", "attempt_id")),
    (lambda cx, item: evidence_differs(cx, item, "contract_digest", "sha256:" + "1" * 64),
     ("release_record", "contract_digest")),
])
def test_stale_or_mismatched_authorization_is_a_digest_mismatch(cx, change, refs):
    item = cx.admitted()
    change(cx, item)
    hold(cx.context.assemble(item.id, PRODUCER, f"launch:{item.id}:0", cx.digest(item)), "DIGEST_MISMATCH", *refs)


def test_another_contract_digest_attempt_or_candidate_is_refused(cx):
    item = cx.admitted()
    hold(cx.context.assemble(item.id, PRODUCER, f"launch:{item.id}:0", "sha256:" + "2" * 64), "DIGEST_MISMATCH",
         "contract_digest")
    correlation, candidate, clone = cx.produced(item)
    # A stale correlation (the attempt before the state advanced) is VERSION_DRIFT.
    hold(cx.context.assemble(item.id, VERIFIER, f"launch:{item.id}:0", None, None, clone), "VERSION_DRIFT", "attempt")
    hold(cx.context.assemble(item.id, VERIFIER, correlation, None, candidate.locator + "0", clone), "DIGEST_MISMATCH",
         "candidate")


# --- check 5: dependencies and references arrive resolved ------------------------------------------------------------


def test_a_dependency_and_a_reference_arrive_with_their_contents(cx):
    dependency = cx.admitted("DEPENDENCY")
    cx.store.commit("registry", f"factory:{dependency.id}", 0, {"stage": "DONE", "outcome": "closed"})
    item = cx.admitted(dependencies=[dependency.id])
    fields = cx.context.assemble(item.id, PRODUCER, f"launch:{item.id}:0", None).fields
    [resolved] = fields["dependencies"]
    assert (resolved["identity"], resolved["label"], resolved["stage"], resolved["outcome"]) == (
        dependency.id, "DEPENDENCY", "DONE", "closed")
    assert resolved["packet"]["text"].encode() == cx.registry.records.show(dependency.id).packet
    [reference] = fields["design_rules"]["authority_references"]
    assert (reference["reference"], reference["path"], reference["commit"]) == (README, "README.md",
                                                                                 item.pointer.commit)
    assert reference["text"].encode() == git(cx.clone, "show", f"{item.pointer.commit}:README.md")
    assert fields["design_rules"]["fixed_decisions"] == ["FD"]


# --- check 6: the self-review ----------------------------------------------------------------------------------------


def test_the_self_review_is_bound_to_the_exact_candidate_and_create_only(cx):
    item = cx.admitted()
    correlation, candidate, clone = cx.produced(item)
    reference = cx.context.record_self_review(item.id, candidate, REVIEW)  # The same text again: the same Ref.
    record = cx.registry.assessment.consumer.repository.get(reference, SCOPE)
    assert json.loads(record.value) == {"identity": item.id, "candidate_locator": candidate.locator,
                                        "candidate_digest": candidate.content_digest, "text": REVIEW}
    version, stored = cx.store.read_state("registry", f"self-review:{item.id}:{candidate.content_digest}")
    assert version == 1 and ref_from_document(stored["evidence_ref"]) == reference == record_ref(record)
    assert stored["candidate"]["locator"] == candidate.locator and stored["candidate"]["identity"] == candidate.identity
    objects = cx.objects()
    with pytest.raises(SelfReviewExists) as refused:
        cx.context.record_self_review(item.id, candidate, REVIEW + " Edited afterwards.")
    assert refused.value.code == SELF_REVIEW_EXISTS and cx.objects() == objects
    assert cx.store.read_state("registry", f"self-review:{item.id}:{candidate.content_digest}") == (version, stored)
    # A package for another candidate does not find it.
    other = CandidateRef.source_revision("sha256:" + "3" * 64, candidate.locator[:-40] + "3" * 40)
    _, state = cx.store.read_state("registry", f"factory:{item.id}")
    cx.store.commit("registry", f"factory:{item.id}", 1, state | {"candidate": {
        "kind": "source-revision", "identity": other.identity, "content_digest": other.content_digest,
        "locator": other.locator, "provenance": other.provenance, "independent_read_back_proven": False}})
    cx.reserve(item, f"launch:{item.id}:2")
    hold(cx.context.assemble(item.id, VERIFIER, f"launch:{item.id}:2", None, None, clone), "MISSING_RECORD",
         "producer_self_review")


# --- check 8: deterministic and read-only ----------------------------------------------------------------------------


def test_assembly_is_byte_identical_and_writes_nothing(cx):
    item = cx.admitted()
    correlation, candidate, clone = cx.produced(item)
    before = cx.written()
    reservations = cx.store.recovery_reservations("registry")
    producer = [cx.context.assemble(item.id, PRODUCER, f"launch:{item.id}:1", None) for _ in range(2)]
    verifier = [cx.context.assemble(item.id, VERIFIER, correlation, None, None, clone) for _ in range(2)]
    assert producer[0].canonical_bytes() == producer[1].canonical_bytes()
    assert verifier[0].canonical_bytes() == verifier[1].canonical_bytes()
    assert cx.written() == before and cx.store.recovery_reservations("registry") == reservations


# --- revision 4b, check 4: the running worker's own call, in the coordinator's real launch order -------------------


def launched(cx, item, role: str, claim: bool = True) -> str:
    """FactoryCoordinator._run's order: the correlation from the store version, the repository reservation, the
    launch saved with `commit_with_effect` for that correlation (store version v + 1), then `claim_effect`."""
    version, raw = cx.store.read_state("registry", f"factory:{item.id}")
    correlation = f"launch:{item.id}:{version}"
    cx.reserve(item, correlation)
    state = raw or {"stage": "IMPLEMENT", "version": 0, "accepted": False, "closure": [], "candidate": None,
                    "implement_cycles": 0, "verify_cycles": 0}
    cx.store.commit_with_effect("registry", f"factory:{item.id}", version, state | {
        "role": role, "implement_cycles": 1 if role == PRODUCER else state["implement_cycles"]}, correlation,
        {"correlation": correlation, "work": item.id, "role": role})
    if claim:
        cx.store.claim_effect("registry", correlation)
    return correlation


def test_the_running_workers_own_calls_get_their_package(cx):
    """A worker is never locked out by its own launch save: before and after `commit_with_effect` and
    `claim_effect`, the same correlation gets the package with `attempt` v."""
    item = cx.admitted(reserve=False)
    cx.reserve(item, f"launch:{item.id}:0")
    before = cx.context.assemble(item.id, PRODUCER, f"launch:{item.id}:0", cx.digest(item))
    correlation = launched(cx, item, PRODUCER)
    running = cx.context.assemble(item.id, PRODUCER, correlation, cx.digest(item))
    assert isinstance(before, ContextPackage) and isinstance(running, ContextPackage)
    assert correlation == f"launch:{item.id}:0" and before.fields["attempt"] == running.fields["attempt"] == 0
    assert running.fields["history"]["stage"] == "IMPLEMENT" and running.fields["history"]["implement_cycles"] == 1
    other = cx.admitted("OTHER")
    _, candidate, clone = cx.produced(other)
    verifier = launched(cx, other, VERIFIER)
    assert verifier == f"launch:{other.id}:1"
    package = cx.context.assemble(other.id, VERIFIER, verifier, cx.digest(other), candidate.locator, clone)
    assert isinstance(package, ContextPackage) and package.fields["attempt"] == 1


def confirmed(cx, item, correlation):
    cx.store.confirm_effect("registry", correlation, "outcome:candidate")


def parked(cx, item, correlation):
    """The worker's outcome is unknown: the effect stays `unknown` and the store moves to v + 2."""
    version, raw = cx.store.read_state("registry", f"factory:{item.id}")
    cx.store.park_unknown_effect("registry", correlation, version, raw | {"outcome": "authority-block"})


def saved_again(cx, item, correlation):
    version, raw = cx.store.read_state("registry", f"factory:{item.id}")
    cx.store.commit("registry", f"factory:{item.id}", version, raw | {"outcome": "rework"})


@pytest.mark.parametrize("after,claim", [(confirmed, True), (parked, True), (saved_again, False)])
def test_a_finished_parked_or_superseded_launch_is_version_drift(cx, after, claim):
    item = cx.admitted(reserve=False)
    correlation = launched(cx, item, PRODUCER, claim=claim)
    after(cx, item, correlation)
    hold(cx.context.assemble(item.id, PRODUCER, correlation, None), "VERSION_DRIFT", "attempt")


def test_another_version_another_item_or_a_save_without_this_effect_is_version_drift(cx):
    item, other = cx.admitted(reserve=False), cx.admitted("OTHER", reserve=False)
    launched(cx, item, PRODUCER)
    for correlation in (f"launch:{item.id}:2", f"launch:{item.id}:00", f"launch:{other.id}:0",
                        f"launch:{item.id}:-1", f"other:{item.id}:0"):
        hold(cx.context.assemble(item.id, PRODUCER, correlation, None), "VERSION_DRIFT", "attempt")
    # Not yet launched (store version 0): another item's correlation, or a non-canonical version, is still refused.
    for correlation in (f"launch:{item.id}:0", f"launch:{other.id}:00"):
        hold(cx.context.assemble(other.id, PRODUCER, correlation, None), "VERSION_DRIFT", "attempt")
    # v + 1 reached by a plain save, with no effect for launch:<other>:0.
    cx.store.commit("registry", f"factory:{other.id}", 0, {"stage": "IMPLEMENT", "version": 0, "accepted": False,
                                                           "closure": [], "candidate": None})
    cx.reserve(other, f"launch:{other.id}:0")
    hold(cx.context.assemble(other.id, PRODUCER, f"launch:{other.id}:0", None), "VERSION_DRIFT", "attempt")


def test_a_running_worker_stays_bound_to_the_approved_instructions(cx):
    """Handoff section 4: in the running launch, a moved pointer or a release record that no longer matches holds
    the worker's own call; it is never given a package for other instructions."""
    item = cx.admitted(reserve=False)
    correlation = launched(cx, item, PRODUCER)
    data = cx.registry.records.show(item.id).packet + b"\nother instructions\n"
    commit = commit_file(cx.clone, "main", item.pointer.path, data)
    cx.registry.identities.set_pointer(item.id, Pointer(REPO, item.pointer.path, commit, data))
    hold(cx.context.assemble(item.id, PRODUCER, correlation, None), "MISSING_RECORD", "assessment")
    other = cx.admitted("OTHER", reserve=False)
    running = launched(cx, other, PRODUCER)
    evidence_differs(cx, other, "contract_digest", "sha256:" + "4" * 64)
    hold(cx.context.assemble(other.id, PRODUCER, running, None), "DIGEST_MISMATCH", "release_record",
         "contract_digest")
