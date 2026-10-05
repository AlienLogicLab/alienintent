"""`work assess`: Agent Ready on the exact instructions of a hand-registered work item (acceptance checks 1-6).

Every case uses a temporary project database, a local clone with a local bare remote, a real retained-assessment
store and a scripted producer double (FIXTURE_PRODUCER_NOT_NATIVE) bound to a disposable fixture package; nothing
launches Agent Ready. The interruption cases use real child processes the test starts and kills. Packet texts and
labels here are TEST DATA.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from alienintent.composition.readiness import resolve_binding
from alienintent.composition.work_registry import WorkRegistry
from alienintent.context_assembly.application.packet_assessment import PacketAssessment
from alienintent.context_assembly.application.work_authorization import AUTHORIZED_INSTRUCTIONS_FIXED, CONTRACT_UNSATISFIABLE
from alienintent.context_assembly.domain.packet_assessment import PacketAssessed
from alienintent.context_assembly.domain.work_identity import Pointer
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.domain.records import ref_from_document
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.execution_coordination.adapters.assessment_consumer import RetainedAssessmentConsumer
from alienintent.execution_coordination.adapters.release_admission import StoredReleaseAuthorizations
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.domain.readiness import (
    ATTEMPT_CONFLICT, ATTEMPT_FAILURE, ATTEMPT_IN_PROGRESS, CAPABILITY_PROVENANCE_HOLD, DIRECT, NO_ASSESSMENT,
    PROVIDER_FAILURE, TIMEOUT, AttemptMetadata, CandidateWorkUnit, Hold, InvocationCustody, ProducerResponse)
from alienintent.execution_coordination.domain.release import ReleaseAuthorization
from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
from tests.context_assembly.test_initial_compilation import PROJECT, REPO, Project, git
from tests.context_assembly.test_readiness_consumer import fixture_package
from tests.context_assembly.test_work_identity_service import commit_file, remote_refs, tag_commit

ROOT = Path(__file__).resolve().parents[2]
PROFILE, SCOPE = "work-preparation", frozenset({"public", "private"})
PATH = "docs/packet.md"
PACKET = b"# Work unit: fixture\n\nDo exactly this.\n"
REVISED = b"# Work unit: fixture\n\nDo exactly this, revised.\n"
ORIGINAL, RECOVERY = {"pid": 101, "start": 1, "boot": "b", "pidns": 1}, {"pid": 202, "start": 2, "boot": "b", "pidns": 1}


def expected_fingerprint(identity: str, commit: str) -> str:
    """Section 4's fingerprint, computed independently of the code under test."""
    document = {"kind": "registered-packet", "id": identity, "repo": REPO, "path": PATH, "commit": commit}
    return "sha256:" + sha256(json.dumps(document, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def sha(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def answer(producer, unit, document: dict | None = None) -> ProducerResponse:
    """A direct result with the bound producer's custody for exactly this attempt and text."""
    b = producer.binding
    custody = InvocationCustody(unit.attempt_id, sha(unit.text.encode()), b.product, b.product_version, b.executable,
                                (b.executable, "assess", "<fixture>", "--provider", "claude", "--json"), "claude",
                                "2026-10-02T00:00:00+00:00", "2026-10-02T00:00:01+00:00")
    return ProducerResponse(json.dumps(document or {"disposition": "READY"}).encode(), 0, False, DIRECT, custody)


class Producer:
    """FIXTURE_PRODUCER_NOT_NATIVE: the per-attempt builder and the producer it builds; counts builds and launches."""

    def __init__(self, binding, script=None):
        self.binding, self.script, self.built, self.calls = binding, script or answer, [], []

    def build(self, attempt, owner):
        self.built.append((attempt, owner))
        return self

    def assess(self, unit):
        self.calls.append(unit)
        return self.script(self, unit)


class Ownership:
    """A scripted process-ownership observation (the real one is used by the interruption test)."""

    def __init__(self, me=ORIGINAL, states=None, owned=()):
        self.me, self.states, self.owned = me, states or {}, owned

    def current(self):
        return self.me

    def owner_state(self, owner):
        return self.states.get(owner["pid"], "alive")

    def owned_work(self, invocation_id, owner=None):
        return self.owned


class Interrupted(BaseException):
    """The terminal closing under a running `work assess`: nothing in the service catches it."""


def interrupted(producer, unit):
    raise Interrupted()


class Fx:
    def __init__(self, root: Path, binding="established"):
        root.mkdir(mode=0o700)
        SQLiteOperationalStore(root / "fx.sqlite")
        self.root, self.project = root, Project(root / "project", {"fx": root / "fx.sqlite"})
        self.clone = self.project.clone
        self.registry = WorkRegistry(self.project.configuration)
        self.records, self.identities = self.registry.records, self.registry.identities
        self.store = SQLiteOperationalStore(root / "readiness.sqlite")
        self.evidence = LocalEvidenceRepository(root / "evidence", PROJECT, PROFILE)
        definition = Ref(PROJECT, PROFILE, "readiness-consumer", sha(b"fixture"), "fixture:readiness-consumer")
        self.consumer = RetainedAssessmentConsumer(self.evidence, self.store, PROJECT, PROFILE, definition,
                                                   "fixture work assess", SCOPE)
        self.binding = resolve_binding(fixture_package(root / "package", metadata=binding == "established"))
        self.producer = Producer(self.binding)
        self.releases = StoredReleaseAuthorizations(self.store, "registry")  # Empty unless a test authorizes.
        self.service = self.make()

    def make(self, ownership=None, producer=None, binding=None, consumer=None, identities=None) -> PacketAssessment:
        return PacketAssessment(self.records, identities or self.identities, consumer or self.consumer,
                                binding or self.binding, ownership or Ownership(), (producer or self.producer).build,
                                self.releases)

    def authorize(self, identity: str) -> None:
        """The release record `work authorize` writes (its own tests cover how)."""
        self.releases.record(ReleaseAuthorization(identity, sha(b"evidence"), True, "a" * 40, "fixture"))

    def register(self, data: bytes = PACKET, label: str = "PACKET", path: str = PATH):
        return self.records.register(data, REPO, path, commit_file(self.clone, "main", path, data), label)

    def row(self, identity: str):
        return self.identities.find(identity)

    def outcome(self, entry: dict) -> dict:
        return json.loads(self.evidence.get(ref_from_document(entry["outcome_ref"]), SCOPE).value)

    def opened(self, entry: dict) -> dict:
        return json.loads(self.evidence.get(ref_from_document(entry["opened_ref"]), SCOPE).value)


@pytest.fixture
def fx(tmp_path) -> Fx:
    return Fx(tmp_path / "fx")


def dump(database: Path) -> str:
    connection = sqlite3.connect(database)
    try:
        return "\n".join(connection.iterdump())
    finally:
        connection.close()


def test_unsatisfiable_refuses_before_an_attempt_and_valid_packet_still_runs(fx):
    item = fx.register()
    seen = []
    fx.service.satisfiable = lambda packet, commit, identity: seen.append((packet, commit, identity)) or (
        "required_evidence: unknown", "landing: DONE is unreachable")
    refused = fx.service.assess(item.id)
    assert refused.reason_code == CONTRACT_UNSATISFIABLE
    assert refused.detail == "required_evidence: unknown; landing: DONE is unreachable"
    assert seen == [(PACKET, item.pointer.commit, item.id)]
    assert fx.consumer.history(item.id) == () and fx.producer.calls == []
    fx.service.satisfiable = lambda packet, commit, identity: ()
    accepted = fx.service.assess(item.id)
    assert accepted.disposition == "READY" and len(fx.consumer.history(item.id)) == 1


# --- check 1: exactly the registered instructions -----------------------------------------------------------------


def test_assesses_the_pinned_bytes_not_the_working_tree_or_branch_head(fx):
    item = fx.register()
    commit = item.pointer.commit
    commit_file(fx.clone, "main", PATH, REVISED)  # The branch head now holds another version...
    (fx.clone / PATH).write_bytes(b"uncommitted working tree text\n")  # ...and the working tree a third.
    result = fx.service.assess(item.label)
    assert isinstance(result, PacketAssessed) and (result.identity, result.disposition, result.reused) == (
        item.id, "READY", False)
    [entry] = fx.consumer.history(item.id)
    assert entry["attempt_id"] == result.attempt_id
    assert entry["input_fingerprint"] == expected_fingerprint(item.id, commit)
    assert entry["input_sha256"] == sha(git(fx.clone, "show", f"{commit}:{PATH}")) == sha(PACKET)
    [unit] = fx.producer.calls
    assert unit.text.encode() == PACKET and (unit.identity, unit.attempt_id) == (item.id, result.attempt_id)
    assert (fx.opened(entry)["contract_digest"], fx.opened(entry)["lint_ref"]) == (None, None)
    row = fx.row(item.id)
    assert row.assessment_ref == ref_from_document(entry["raw_ref"]) == ref_from_document(result.assessment_ref)
    assert row.assessment_ref.logical_id == f"readiness/{item.id}/{result.attempt_id}/raw"
    assert fx.consumer.raw(item.id, result.attempt_id)[1] == '{"disposition": "READY"}'  # Unchanged bytes.
    # Neither database holds the packet text.
    assert "Do exactly this" not in dump(fx.project.database) + dump(fx.root / "readiness.sqlite")


# --- check 2: repeat and crash ------------------------------------------------------------------------------------


def test_repeat_runs_nothing_and_returns_the_same_attempt(fx):
    item = fx.register()
    first = fx.service.assess(item.id)
    again = fx.service.assess(item.id)
    assert again == PacketAssessed(item.id, first.attempt_id, "READY", first.assessment_ref, True)
    assert len(fx.producer.calls) == 1 and len(fx.consumer.history(item.id)) == 1


def test_reference_lost_after_recording_is_saved_by_the_rerun_without_running(fx, monkeypatch):
    item = fx.register()
    original = fx.identities.set_evidence

    def crash(*args):
        raise RuntimeError("process died after the outcome was recorded")

    monkeypatch.setattr(fx.identities, "set_evidence", crash)
    with pytest.raises(RuntimeError):
        fx.service.assess(item.id)
    [entry] = fx.consumer.history(item.id)
    assert entry["outcome"]["disposition"] == "READY" and fx.row(item.id).assessment_ref is None
    monkeypatch.setattr(fx.identities, "set_evidence", original)
    result = fx.service.assess(item.id)
    assert (result.attempt_id, result.reused, len(fx.producer.calls)) == (entry["attempt_id"], True, 1)
    assert fx.row(item.id).assessment_ref == ref_from_document(entry["raw_ref"])


# --- check 3: failure, provenance and interruption ----------------------------------------------------------------


def raising(producer, unit):
    raise RuntimeError("adapter failed")


def timing_out(producer, unit):
    return ProducerResponse(None, None, True, DIRECT, answer(producer, unit).custody)


@pytest.mark.parametrize("script, failure_class", [(raising, PROVIDER_FAILURE), (timing_out, TIMEOUT)])
def test_failure_is_recorded_and_the_rerun_runs_once_with_it_as_predecessor(fx, script, failure_class):
    item = fx.register()
    fx.producer.script = script
    failed = fx.service.assess(item.id)
    [entry] = fx.consumer.history(item.id)
    assert failed == Hold(ATTEMPT_FAILURE, item.id, entry["attempt_id"], failure_class)
    assert entry["outcome"]["failure_class"] == failure_class and fx.row(item.id) == item
    fx.producer.script = answer
    result = fx.service.assess(item.id)
    assert isinstance(result, PacketAssessed) and len(fx.producer.calls) == 2
    assert fx.consumer.history(item.id)[1]["predecessor"] == {"identity": item.id, "attempt_id": entry["attempt_id"]}


def test_unestablished_binding_holds_before_launch_and_never_blocks_a_later_run(tmp_path):
    fx = Fx(tmp_path / "fx", binding="unknown-version")
    item = fx.register()
    held = fx.service.assess(item.id)
    assert held == Hold(CAPABILITY_PROVENANCE_HOLD, item.id, None, "PRODUCT_VERSION_UNKNOWN")
    assert fx.producer.built == [] and fx.consumer.history(item.id) == () and fx.consumer.latest(item.id) is None
    retained = [json.loads(p.read_text())["payload"] for p in (fx.evidence.root / "objects").iterdir()]
    assert [p["evidence_id"] for p in retained] == ["readiness.provenance_held"]
    # The retained refusal is not an attempt: an established binding over the same store runs once.
    established = resolve_binding(fixture_package(tmp_path / "established"))
    producer = Producer(established)
    result = fx.make(producer=producer, binding=established).assess(item.id)
    assert isinstance(result, PacketAssessed) and len(producer.calls) == 1


OWNER_SCRIPT = ("import json, sys, time\n"
                "from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership\n"
                "print(json.dumps(dict(ProcOwnership().current())), flush=True)\n"
                "time.sleep(300)\n")


def ended(process: subprocess.Popen) -> None:
    process.kill()
    process.wait()


class Observed(Ownership):
    """The real /proc observation, with `current` naming the given owner process (a child the test controls)."""

    def __init__(self, owner):
        super().__init__(owner)
        self.real = ProcOwnership()

    def owner_state(self, owner):
        return self.real.owner_state(owner)

    def owned_work(self, invocation_id, owner=None):
        return self.real.owned_work(invocation_id, owner)


def test_interrupted_attempt_recovers_only_after_owner_and_marked_processes_end(fx):
    item = fx.register()
    owner_process = subprocess.Popen([sys.executable, "-c", OWNER_SCRIPT], stdout=subprocess.PIPE, text=True,
                                     env={**os.environ, "PYTHONPATH": str(ROOT / "src")})
    marked = None
    try:
        owner = json.loads(owner_process.stdout.readline())
        fx.producer.script = interrupted
        with pytest.raises(Interrupted):  # The original `work assess` is gone mid-run; its owner record stays.
            fx.make(Observed(owner)).assess(item.id)
        [entry] = fx.consumer.history(item.id)
        attempt = entry["attempt_id"]
        assert entry["outcome"] is None and entry["owner"] == owner and fx.producer.built == [(attempt, owner)]
        assert fx.service.assess(item.id) == Hold(ATTEMPT_IN_PROGRESS, item.id, attempt, "recover it by naming it")
        recovery_producer = Producer(fx.binding)
        recovery = fx.make(ProcOwnership(), recovery_producer)
        refused = recovery.assess(item.id, recover="00000000-0000-4000-8000-000000000000")
        assert refused.reason_code == NO_ASSESSMENT and fx.consumer.history(item.id) == (entry,)
        running = recovery.assess(item.id, recover=attempt)  # The recorded owner is alive.
        assert (running.reason_code, running.detail) == ("ASSESSMENT_PROCESS_RUNNING", str(owner_process.pid))
        ended(owner_process)
        marked = subprocess.Popen(["sleep", "300"], env={**os.environ, "ALIENINTENT_INVOCATION_ID": attempt})
        running = recovery.assess(item.id, recover=attempt)  # A process still carries the attempt's marker.
        assert (running.reason_code, running.detail) == ("ASSESSMENT_PROCESS_RUNNING", str(marked.pid))
        assert fx.consumer.history(item.id) == (entry,) and recovery_producer.calls == []
        ended(marked)
        result = recovery.assess(item.id, recover=attempt)
        assert isinstance(result, PacketAssessed) and len(recovery_producer.calls) == 1
        first, second = fx.consumer.history(item.id)
        assert first["outcome"]["failure_class"] == PROVIDER_FAILURE
        assert fx.outcome(first)["shape"] == "interrupted:operator"
        assert second["predecessor"] == {"identity": item.id, "attempt_id": attempt}
        # After an outcome the same id is refused and nothing changes.
        assert recovery.assess(item.id, recover=attempt).reason_code == NO_ASSESSMENT
        assert fx.consumer.history(item.id) == (first, second) and len(recovery_producer.calls) == 1
    finally:
        for process in (owner_process, marked):
            if process is not None and process.poll() is None:
                ended(process)


@pytest.mark.parametrize("states, owned, detail", [({101: "unknown"}, (), "101"),
                                                   ({101: "terminated"}, None, "process table not readable")])
def test_unknown_owner_or_unreadable_process_table_refuses_recovery(fx, states, owned, detail):
    item = fx.register()
    fx.producer.script = interrupted
    with pytest.raises(Interrupted):
        fx.service.assess(item.id)
    [entry] = fx.consumer.history(item.id)
    refused = fx.make(Ownership(RECOVERY, states, owned)).assess(item.id, recover=entry["attempt_id"])
    assert (refused.reason_code, refused.detail) == ("ASSESSMENT_PROCESS_RUNNING", detail)
    assert fx.consumer.history(item.id) == (entry,)


def test_original_paused_before_recording_its_owner_launches_nothing_after_recovery(fx):
    item = fx.register()
    recovery_producer = Producer(fx.binding)
    recovery = fx.make(Ownership(RECOVERY), recovery_producer)
    recovered = []

    class Paused(Ownership):
        def current(self):  # The original pauses here, after opening and before recording its owner.
            recovered.append(recovery.assess(item.id, recover=fx.consumer.latest(item.id)["attempt_id"]))
            return ORIGINAL

    held = fx.make(Paused()).assess(item.id)
    [first, second] = fx.consumer.history(item.id)
    assert isinstance(recovered[0], PacketAssessed) and recovered[0].attempt_id == second["attempt_id"]
    assert held == Hold(ATTEMPT_CONFLICT, item.id, first["attempt_id"], "owner")
    assert first["owner"] == RECOVERY and fx.producer.calls == [] and len(recovery_producer.calls) == 1


def test_late_result_of_a_recovered_attempt_is_a_conflict(fx):
    item = fx.register()
    recovery_producer = Producer(fx.binding)
    recovery = fx.make(Ownership(RECOVERY, {ORIGINAL["pid"]: "terminated"}), recovery_producer)
    recovered = []

    def late(producer, unit):  # Recovered while still running, then delivers its result.
        recovered.append(recovery.assess(item.id, recover=unit.attempt_id))
        return answer(producer, unit)

    fx.producer.script = late
    held = fx.service.assess(item.id)
    first, second = fx.consumer.history(item.id)
    assert held == Hold(ATTEMPT_CONFLICT, item.id, first["attempt_id"], "a different terminal response for this attempt")
    assert first["outcome"]["failure_class"] == PROVIDER_FAILURE and recovered[0].attempt_id == second["attempt_id"]
    assert fx.row(item.id).assessment_ref == ref_from_document(second["raw_ref"])


def test_recovery_racing_an_original_that_finishes_first_launches_nothing(fx):
    item = fx.register()
    fx.producer.script = interrupted
    with pytest.raises(Interrupted):
        fx.service.assess(item.id)
    [entry] = fx.consumer.history(item.id)
    attempt, assessed = entry["attempt_id"], entry["input_fingerprint"]

    class Racing(Recording):
        def observe(self, raw, metadata, shape):  # The original's result lands just before the failure record.
            response = answer(fx.producer, CandidateWorkUnit(item.id, PACKET.decode(), attempt, assessed))
            fx.consumer.observe(response.raw, AttemptMetadata(item.id, attempt, assessed, sha(PACKET), 0, False,
                                                              response.custody, fx.binding), DIRECT)
            return self._target.observe(raw, metadata, shape)

    recovery_producer = Producer(fx.binding)
    held = fx.make(Ownership(RECOVERY, {ORIGINAL["pid"]: "terminated"}), recovery_producer,
                   consumer=Racing(fx.consumer)).assess(item.id, recover=attempt)
    assert held == Hold(ATTEMPT_CONFLICT, item.id, attempt, "a different terminal response for this attempt")
    [entry] = fx.consumer.history(item.id)
    assert entry["outcome"]["disposition"] == "READY" and recovery_producer.built == []


# --- check 4: a new revision of the packet ------------------------------------------------------------------------


def test_new_revision_moves_the_pointer_publishes_its_tag_and_is_assessed(fx):
    item = fx.register()
    first = fx.service.assess(item.id)
    revised = commit_file(fx.clone, "main", PATH, REVISED)
    result = fx.service.assess(item.id, revision=(REVISED, revised))
    assert isinstance(result, PacketAssessed) and not result.reused and result.attempt_id != first.attempt_id
    row = fx.row(item.id)
    assert row.pointer.commit == revised and row.state == "CAPTURE"
    assert tag_commit(fx.clone, item.id) == revised == remote_refs(fx.clone)["refs/tags/work/" + item.id]
    earlier, latest = fx.consumer.history(item.id)
    assert earlier["attempt_id"] == first.attempt_id and earlier["outcome"]["disposition"] == "READY"
    assert (latest["input_fingerprint"], latest["input_sha256"]) == (expected_fingerprint(item.id, revised),
                                                                     sha(REVISED))
    assert fx.producer.calls[-1].text.encode() == REVISED
    assert row.assessment_ref == ref_from_document(latest["raw_ref"])
    # A file that differs from Git at that commit, and any move past CAPTURE, are refused; nothing is assessed.
    mismatch = fx.service.assess(item.id, revision=(b"not what Git holds\n", revised))
    assert mismatch.reason_code == "POINTER_MISMATCH" and len(fx.consumer.history(item.id)) == 2
    fx.identities.set_state(item.id, "SPECIFY")
    third = commit_file(fx.clone, "main", PATH, b"third\n")
    present = fx.service.assess(item.id, revision=(b"third\n", third))
    assert present.reason_code == "POINTER_PRESENT" and fx.row(item.id).pointer.commit == revised
    assert remote_refs(fx.clone)["refs/tags/work/" + item.id] == revised and len(fx.consumer.history(item.id)) == 2


@pytest.mark.parametrize("case, code", [("requirement", "NOT_A_REGISTERED_PACKET"),
                                        ("imported", "NOT_A_REGISTERED_PACKET"), ("retired", "IDENTITY_RETIRED"),
                                        ("refused-binding", CAPABILITY_PROVENANCE_HOLD),
                                        ("not-text", "INSTRUCTIONS_NOT_TEXT")])
def test_revision_never_moves_a_pointer_it_must_not(tmp_path, case, code):
    fx = Fx(tmp_path / "fx", binding="unknown-version" if case == "refused-binding" else "established")
    commit = commit_file(fx.clone, "main", PATH, PACKET)
    pointer = Pointer(REPO, PATH, commit, PACKET)
    if case == "requirement":
        item = fx.identities.register("requirement:SF-REQ-1", "REQ", "BIU", pointer=pointer)
    elif case == "imported":
        item = fx.records.import_completed(PACKET, REPO, PATH, commit, "IMP", "153", {})
    else:
        item = fx.records.register(PACKET, REPO, PATH, commit, "PACKET")
        if case == "retired":
            item = fx.identities.retire(item.id)
    data = b"\xff\xfe not text\n" if case == "not-text" else REVISED
    revised = commit_file(fx.clone, "main", PATH, data)
    held = fx.service.assess(item.id, revision=(data, revised))
    assert held.reason_code == code
    assert fx.row(item.id) == item and remote_refs(fx.clone)["refs/tags/work/" + item.id] == commit
    assert fx.consumer.history(item.id) == () and fx.producer.built == []


def test_run_finishing_after_the_pointer_moved_keeps_its_attempt_but_saves_no_reference(fx):
    item = fx.register()
    revised = commit_file(fx.clone, "main", PATH, REVISED)

    def moved_meanwhile(producer, unit):
        if len(producer.calls) == 1:
            fx.identities.set_pointer(item.id, Pointer(REPO, PATH, revised, REVISED))
        return answer(producer, unit)

    fx.producer.script = moved_meanwhile
    stale = fx.service.assess(item.id)
    assert isinstance(stale, PacketAssessed) and stale.assessment_ref is None
    assert fx.row(item.id).assessment_ref is None and fx.consumer.history(item.id)[0]["outcome"]["disposition"] == "READY"
    fresh = fx.service.assess(item.id)  # The moved pointer is a new fingerprint: assessed once more.
    assert not fresh.reused and len(fx.producer.calls) == 2
    assert fx.row(item.id).assessment_ref == ref_from_document(fresh.assessment_ref)


# --- check 5: a record, not an approval ---------------------------------------------------------------------------


class Recording:
    def __init__(self, target):
        self._target, self.calls = target, []

    def __getattr__(self, name):
        value = getattr(self._target, name)
        if not callable(value):
            return value

        def call(*args, **options):
            self.calls.append(name)
            return value(*args, **options)
        return call


def test_ready_changes_no_state_and_consumes_or_releases_nothing(fx):
    item = fx.register()
    consumer, identities = Recording(fx.consumer), Recording(fx.identities)
    result = fx.make(consumer=consumer, identities=identities).assess(item.id)
    assert result.disposition == "READY" and fx.row(item.id).state == item.state == "CAPTURE"
    calls = set(consumer.calls) | set(identities.calls)
    assert not calls & {"consume", "invalidate", "set_state", "retire"} and not any("release" in c for c in calls)
    assert [a for a, _, _ in fx.store.list_states(PROFILE, "")] == ["readiness:" + item.id]


# --- check 6: refusals open nothing -------------------------------------------------------------------------------


@pytest.mark.parametrize("case", ["unknown", "imported", "requirement", "retired", "not-text"])
def test_refusals_open_nothing(fx, case):
    commit = commit_file(fx.clone, "main", PATH, b"\xff\xfe" if case == "not-text" else PACKET)
    evidence = {"project": PROJECT, "profile": "fx", "logical_id": "imported", "revision_digest": sha(b"i"),
                "locator": "evidence:imported"}
    if case == "unknown":
        target, code = "missing", "UNKNOWN_IDENTITY"
    elif case == "imported":
        item = fx.records.import_completed(PACKET, REPO, PATH, commit, "IMP", "153", {"assessment": evidence})
        target, code = item.id, "NOT_A_REGISTERED_PACKET"
    elif case == "requirement":
        item = fx.identities.register("requirement:SF-REQ-1", "REQ", "BIU", pointer=Pointer(REPO, PATH, commit,
                                                                                               PACKET))
        target, code = item.id, "NOT_A_REGISTERED_PACKET"
    else:
        item = fx.records.register(b"\xff\xfe" if case == "not-text" else PACKET, REPO, PATH, commit, "PACKET")
        item = fx.identities.retire(item.id) if case == "retired" else item
        target, code = item.id, "IDENTITY_RETIRED" if case == "retired" else "INSTRUCTIONS_NOT_TEXT"
    held = fx.service.assess(target)
    assert isinstance(held, Hold) and held.reason_code == code
    assert fx.store.list_states(PROFILE, "") == () and fx.producer.built == []
    if case != "unknown":
        assert fx.row(item.id) == item  # An imported item's evidence is unchanged.
    if case == "imported":
        assert fx.row(item.id).assessment_ref == ref_from_document(evidence)


# --- authorized instructions and assessment are fixed (release record, check 5) -------------------------------------
# Every test above runs with an empty release store: the assess, reuse, revision and --recover paths are unchanged.


def test_an_authorized_item_refuses_a_revision_before_moving_its_pointer(fx):
    item = fx.register()
    first = fx.service.assess(item.id)
    fx.authorize(item.id)
    revised = commit_file(fx.clone, "main", PATH, REVISED)
    assert fx.service.assess(item.id, revision=(REVISED, revised)) == Hold(AUTHORIZED_INSTRUCTIONS_FIXED, item.id)
    assert fx.row(item.id).pointer.commit == item.pointer.commit == tag_commit(fx.clone, item.id)
    assert remote_refs(fx.clone)["refs/tags/work/" + item.id] == item.pointer.commit
    assert [a["attempt_id"] for a in fx.consumer.history(item.id)] == [first.attempt_id] and len(fx.producer.calls) == 1


def test_an_authorized_item_returns_its_reused_assessment_and_opens_no_new_attempt(fx):
    item = fx.register()
    first = fx.service.assess(item.id)
    fx.authorize(item.id)
    assert fx.service.assess(item.id) == replace(first, reused=True)
    other = fx.register(label="FAILED", path="docs/failed.md")
    fx.producer.script = raising
    failed = fx.service.assess(other.id)
    assert failed.reason_code == ATTEMPT_FAILURE
    fx.authorize(other.id)
    fx.producer.script = answer
    assert fx.service.assess(other.id) == Hold(AUTHORIZED_INSTRUCTIONS_FIXED, other.id)
    assert len(fx.consumer.history(other.id)) == 1 and len(fx.producer.calls) == 2


def test_revision_cannot_be_combined_with_recovery(fx):
    item = fx.register()
    with pytest.raises(ValueError):
        fx.service.assess(item.id, revision=(PACKET, item.pointer.commit), recover="any")
    assert fx.consumer.history(item.id) == ()
