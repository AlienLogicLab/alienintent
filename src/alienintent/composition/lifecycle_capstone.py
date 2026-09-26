"""``python -m alienintent.composition.lifecycle_capstone``: FX-O, the WO-220404 offline capstone.

The canonical multi-role lifecycle (SF-REQ-039) runs end to end over the S0
isolated proof substrate with every predecessor seam bound, through the
production orchestration path only:

- S0 (WO-220101): real temporary SQLite, a disposable local bare Git remote,
  worktree allocation, publication and fresh-clone retrieval through the
  unchanged ``RealWorkerProvider`` / ``GitSourceControl`` / ``GitWorktreeAdapter``,
  local Work Management receipts, one injected clock and the Deterministic
  Test Worker (``ScriptedWorkerProcess``) as the only worker process;
- K1/K2/K3 (WO-220401..03): the provider journals every role outcome durably,
  the coordinator routes one canonical role per stage and reaches the worker
  only through the ``RoleBindingGuard`` over that same journal;
- C1 (WO-220301): each decision escalation becomes one durable JUDGMENT
  attention item; the DecisionInbox stays the only decision path;
- AC-08 (this BIU): the journal carries the owner process identity, and the
  Invocation Runtime attests restart-time ownership, so a conclusively lost
  invocation is recovered deterministically and an UNKNOWN one never is.

Each scenario runs in its own disposable root. Faults are injected only at a
transport boundary - the durable journal, the store's custody record, the
local remote, the worker process or by killing the composing process - never
by writing lifecycle state. Exit 0 is PASS, 1 FAIL, 2 HOLD (a credential was
present or outbound network denial was not established; never reported as
PASS or zero). No live transport, shared profile or sovereignty is claimed.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
import itertools
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Callable, Mapping

from alienintent.composition.control_plane_profile import AttentionProfile
from alienintent.composition.offline_profile import OfflineProofSubstrate, ProofManifest, credential_findings, manifest_from_document
from alienintent.composition.offline_proof import check, network_denial_probe
from alienintent.composition.role_binding import ROLE_OPERATIONS, RoleBindingGuard
from alienintent.control_plane.application.decision_inbox import DecisionInbox
from alienintent.control_plane.domain.attention import AttentionHold, AttentionOrigin
from alienintent.control_plane.ports.attention import AttentionPort
from alienintent.control_plane.ports.decision_notifier import DecisionNotifier, DeliveryHealth
from alienintent.evidence_learning.domain.records import canonical_bytes
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.execution_coordination.domain.escalation import DecisionSubmission, HumanDecisionRequired, SupersededDecision
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.ports.worker_provider import MISSING_TERMINAL_RESULT, WorkerInvocation, WorkerProvider
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter
from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal, journal_records
from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
from alienintent.invocation_runtime.adapters.scripted_worker import SCRIPTED_PROVIDER, journal_provider_calls
from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider, decode_candidate
from alienintent.invocation_runtime.domain.runtime import INVOCATION_MARKER, INVOCATION_OWNER_MARKER, CapabilityGrant, InvocationRole, ReservationBook, owner_token

FIXTURE, BIU = "FX-O", "WO-220404"
EXIT_PASS, EXIT_FAIL, EXIT_HOLD = 0, 1, 2
CRASH_EXIT = 17
GRANT_SECONDS = 3600
JUDGMENT_AUTHORITY, DECISION_LANE = "factory-decision-authority", "factory-decision"
SUBSTITUTIONS = (
    "worker process: Deterministic Test Worker (ScriptedWorkerProcess) behind the production RealWorkerProvider; no model, provider or credential",
    "source-control remote: a local bare repository by path",
    "work management transport: LocalWorkManagement durable receipts",
    "judgment notification: C1 attention items only; no delivery channel is bound",
    "human decision: an attributable DecisionInbox submission made by the fixture",
    "feature-regression receipt: the scripted verifier's SCRIPTED_FIXTURE receipt, not a real pack run",
    "owner death: the composing process is killed (os._exit) at a named journal or process boundary",
    "surviving owned work: a marker-carrying sleep process started by the fixture",
)


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- C1 judgment attention at the decision boundary --------------------------------


class AttentionDecisionNotifier(DecisionNotifier):
    """Each decision escalation becomes exactly one durable C1 JUDGMENT attention item.

    It notifies only: the item carries no decision authority, and the work
    stays held until the DecisionInbox records an attributable decision.
    Re-registering the same escalation (a restart) finds the same item.
    """

    def __init__(self, attention: AttentionPort, *, project: str, profile: str) -> None:
        self.attention, self.project, self.profile = attention, project, profile

    def origin(self, escalation: HumanDecisionRequired) -> AttentionOrigin:
        body = [escalation.work_item, escalation.biu_version, escalation.reason, list(escalation.options)]
        event = f"decision:{escalation.work_item}:{escalation.biu_version}"
        source = Ref(self.project, self.profile, event, "sha256:" + sha256(canonical_bytes(body)).hexdigest(),
                     "decision-inbox:" + escalation.work_item)
        return AttentionOrigin(escalation.work_item, event, "JUDGMENT", f"biu-version:{escalation.biu_version}",
                               DECISION_LANE, JUDGMENT_AUTHORITY, "factory-coordinator", source)

    def notify(self, escalation: HumanDecisionRequired) -> DeliveryHealth:
        try:
            item = self.attention.handle(self.origin(escalation))
        except (AttentionHold, EvidenceHold, KeyError) as error:
            return DeliveryHealth(False, f"judgment attention unavailable: {type(error).__name__}")
        return DeliveryHealth(True, f"{item.identity} {item.status}")


# --- the composed substrate ----------------------------------------------------------


class CapstoneSubstrate(OfflineProofSubstrate):
    """S0's substrate with K1/K2/K3 bound and C1 judgment attention composed."""

    def _compose_worker(self) -> WorkerProvider:
        self.journal = JsonlInvocationJournal(self.journal_path, self.clock)
        self.ownership = ProcOwnership()
        self.real_worker = RealWorkerProvider(
            self.process, GitSourceControl(), self.checkout, "origin", self.candidate_branch, self.producer_read_back,
            self.grant, self.manifest.repository, GitWorktreeAdapter(self.checkout, self.workspaces), ReservationBook(1, 2),
            now=self.clock, sleep=lambda _: None, journal=self.journal, ownership=self.ownership,
        )
        return RoleBindingGuard(self.real_worker, self.journal, self.store, self.manifest.profile, self.manifest.repository, self.clock)

    def _compose_notifier(self) -> DecisionNotifier:
        root = self.root / "control-plane"
        root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.fromtimestamp(self.manifest.clock_epoch, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        counter = itertools.count(1)
        self.attention = AttentionProfile(root, project=self.manifest.repository, name=self.manifest.profile, invocation=BIU,
                                          clock=lambda: stamp, next_id=lambda: f"{FIXTURE}-attempt-{next(counter)}", resolvers=())
        self.notifier = AttentionDecisionNotifier(self.attention.attention, project=self.manifest.repository, profile=self.manifest.profile)
        return self.notifier

    def grant(self, invocation: WorkerInvocation) -> CapabilityGrant:
        """One grant per dispatch, naming the invocation and the canonical role it plays."""
        role = InvocationRole(invocation.role)
        return CapabilityGrant(f"{self.manifest.fixture_id}-{invocation.work_identity}", "1", invocation.correlation_id, role,
                               self.manifest.profile, self.manifest.repository, ROLE_OPERATIONS[str(role)], int(self.clock()) + GRANT_SECONDS)

    @property
    def work_identity(self) -> str:
        return self.manifest.work_items[0].identity


# --- manifest ----------------------------------------------------------------------


def load_document(path: Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def scenario_manifest(document: Mapping[str, object], script: list[str] | tuple[str, ...]) -> ProofManifest:
    """The pinned manifest with its single work item scripted for one scenario phase."""
    derived = json.loads(json.dumps(document))
    derived["work_items"][0]["script"] = list(script)
    return manifest_from_document(derived)


def compose(root: Path, document: Mapping[str, object], script, environment: Mapping[str, str]) -> CapstoneSubstrate:
    return CapstoneSubstrate(root, scenario_manifest(document, script), environment)


# --- transport-boundary faults ---------------------------------------------------------


def fault_journal(substrate: CapstoneSubstrate, fault: str) -> None:
    """Corrupt the producer's durable outcome record as it is appended; the process itself succeeds."""
    append = substrate.journal.append

    def faulty(record):
        if record.get("event") == "invocation-outcome" and record.get("role") == "PRODUCER" and record.get("kind") != MISSING_TERMINAL_RESULT:
            if fault == "misattribute-producer-outcome":
                return append(dict(record) | {"work_identity": "O-OTHER"})
            if fault == "duplicate-producer-outcome":
                append(record)
                return append(record)
            if fault == "malform-producer-outcome":
                return append(dict(record) | {"findings": "not-a-list"})
        return append(record)

    substrate.journal.append = faulty  # type: ignore[method-assign]


def fault_at_verify(substrate: CapstoneSubstrate, fault: str) -> None:
    """At the VERIFY projection, forge the custody record or withdraw the published branch."""
    project = substrate.work.project_execution_state

    def faulty(identity, stage, revision=0):
        if stage == LifecycleStage.VERIFY:
            version, raw = substrate.store.read_state(substrate.manifest.profile, f"factory:{identity}")
            candidate = dict(raw["candidate"])
            if fault == "forge-custody-at-verify":
                forged = "sha256:" + "f" * 64
                candidate["identity"] = str(candidate["identity"]).replace(str(candidate["content_digest"]), forged)
                candidate["content_digest"] = forged
                substrate.store.commit(substrate.manifest.profile, f"factory:{identity}", version, raw | {"candidate": candidate})
            elif fault == "unpublish-at-verify":
                branch = str(candidate["locator"]).rsplit("#", 1)[1].rsplit("@", 1)[0]
                subprocess.run(["git", "--git-dir", str(substrate.remote), "update-ref", "-d", f"refs/heads/{branch}"],
                               env=substrate.git_environment, check=True, capture_output=True)
        return project(identity, stage, revision)

    substrate.work.project_execution_state = faulty  # type: ignore[method-assign]


def die_at(substrate: CapstoneSubstrate, boundary: str, ready: Path | None) -> None:
    """End this composing process at the named boundary; with ``ready``, stay alive there instead."""
    def end() -> None:
        if ready is not None:
            ready.write_text(str(os.getpid()))
            time.sleep(600)
        os._exit(CRASH_EXIT)

    append = substrate.journal.append

    def dying(record):
        producer = record.get("role") == "PRODUCER"
        if boundary == "before-producer-outcome" and producer and record.get("event") == "invocation-outcome":
            end()
        entry = append(record)
        if boundary == "after-invocation-started" and producer and record.get("event") == "invocation-started":
            end()
        if boundary == "after-producer-outcome" and producer and record.get("event") == "invocation-outcome":
            end()
        return entry

    substrate.journal.append = dying  # type: ignore[method-assign]
    if boundary == "after-producer-progress":
        run = substrate.process.run

        def progressing(invocation_id, role, workspace, wall_clock_seconds):
            result = run(invocation_id, role, workspace, wall_clock_seconds)
            if role is InvocationRole.PRODUCER and result.kind == "success":
                end()
            return result

        substrate.process.run = progressing  # type: ignore[method-assign]


def crash_child(root: Path, manifest_path: Path, scenario: str, environment: Mapping[str, str], *, hang: bool = False) -> subprocess.Popen | int:
    """Run the scenario's first phase in a separate composing process that dies (or hangs) at its boundary."""
    command = [sys.executable, "-m", "alienintent.composition.lifecycle_capstone", "crash", "--root", str(root),
               "--manifest", str(manifest_path), "--scenario", scenario] + (["--hang"] if hang else [])
    child_environment = dict(environment) | {"PYTHONPATH": os.pathsep.join(filter(None, (str(Path(__file__).resolve().parents[2]), environment.get("PYTHONPATH"))))}
    if not hang:
        return subprocess.run(command, env=child_environment, capture_output=True, text=True, timeout=300, check=False).returncode
    process = subprocess.Popen(command, env=child_environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ready = Path(root) / "owner-ready"
    deadline = time.monotonic() + 120
    while not ready.exists():
        if process.poll() is not None or time.monotonic() > deadline:
            raise RuntimeError("the owning process never reached its boundary")
        time.sleep(0.05)
    return process


# --- observation (read-only) -----------------------------------------------------------


def outcomes(substrate: CapstoneSubstrate) -> list[tuple[str, str, str]]:
    return [(str(r["role"]), str(r["correlation_id"]), str(r["kind"])) for r in journal_records(substrate.journal_path) if r.get("event") == "invocation-outcome"]


def started(substrate: CapstoneSubstrate, role: str | None = None) -> list[str]:
    return [str(r["correlation_id"]) for r in journal_records(substrate.journal_path)
            if r.get("event") == "invocation-started" and (role is None or r.get("role") == role)]


def process_runs(substrate: CapstoneSubstrate, role: str | None = None) -> list[tuple[str, str, str]]:
    return [(str(r["role"]), str(r["invocation_id"]), str(r["result"])) for r in journal_records(substrate.journal_path)
            if r.get("event") == "process-run" and (role is None or r.get("role") == role)]


def effects(substrate: CapstoneSubstrate) -> list[tuple[str, str, str | None]]:
    return list(substrate.store.effect_ledger(substrate.manifest.profile))


def advertised(substrate: CapstoneSubstrate | Path) -> dict[str, str]:
    remote = substrate.remote if isinstance(substrate, CapstoneSubstrate) else Path(substrate) / "remote.git"
    heads = subprocess.run(["git", "ls-remote", "--heads", str(remote)], capture_output=True, text=True, check=True, env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "GIT_CONFIG_NOSYSTEM": "1", "HOME": str(remote.parent)}).stdout
    return {line.split("refs/heads/", 1)[1]: line.split()[0] for line in heads.splitlines() if "refs/heads/candidate/" in line}


def state_of(substrate: CapstoneSubstrate) -> dict[str, object]:
    projected = substrate.coordinator.state(substrate.work_identity)
    return {"stage": str(projected.stage), "outcome": projected.outcome,
            "candidate": None if projected.candidate is None else projected.candidate.locator,
            "read_back_proven": bool(projected.candidate and projected.candidate.independent_read_back_proven),
            "record": {key: value for key, value in (projected.record or {}).items() if key in {"rejections", "findings", "producer_correlation", "receipts", "closure", "hold_reason", "outcome_kind", "verdict"}}}


def inbox(substrate: CapstoneSubstrate) -> list[str]:
    _, raw = substrate.store.read_state(substrate.manifest.profile, "decision-inbox")
    return sorted((raw.get("open") or {}).keys())


def attention_items(substrate: CapstoneSubstrate) -> list[dict[str, object]]:
    service = substrate.attention.attention
    return [{"identity": identity, "status": service.show(identity).status, "kind": service.show(identity).origin.kind,
             "work_ref": service.show(identity).origin.work_ref, "event": service.show(identity).origin.event_identity}
            for identity in substrate.attention.repository.identities("attention:")]


def revision_of(locator: str | None) -> str | None:
    return None if locator is None else locator.rsplit("@", 1)[1]


def git_head(path: Path, environment: Mapping[str, str]) -> str | None:
    if not (path / ".git").exists():
        return None
    result = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], env=dict(environment), capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def open_request(substrate: CapstoneSubstrate) -> HumanDecisionRequired | None:
    decisions = DecisionInbox(substrate.store, substrate.coordinator, substrate.manifest.profile)
    return next((entry for entry in decisions.list_open() if entry.work_item == substrate.work_identity), None)


def decide(substrate: CapstoneSubstrate, key: str) -> bool:
    """An attributable human decision through the DecisionInbox, the only decision path; False when none is open."""
    request = open_request(substrate)
    if request is None:
        return False
    try:
        DecisionInbox(substrate.store, substrate.coordinator, substrate.manifest.profile).submit(DecisionSubmission(
            "fx-o-operator", "WO-220404 fixture decision", substrate.work_identity, request.biu_version, request.biu_version, key, "authorize"))
    except SupersededDecision:
        # The work is no longer held at that version: there is nothing to decide.
        return False
    return True


# --- scenarios -----------------------------------------------------------------------------


Scenario = Callable[[Path, Mapping[str, object], Path, Mapping[str, str]], tuple[list[dict[str, object]], dict[str, object]]]


def _spec(document: Mapping[str, object], name: str) -> Mapping[str, object]:
    return document["scenarios"][name]  # type: ignore[index]


def lifecycle(root: Path, document, manifest_path: Path, environment) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Producer -> independent verifier rejects -> rework -> fresh candidate -> verifier accepts -> closure, then a restart."""
    spec = _spec(document, "lifecycle")
    composed = compose(root, document, spec["script"], environment)
    summary = composed.coordinator.start()
    state = state_of(composed)
    observed = outcomes(composed)
    remote = advertised(composed)
    producers = [(c, k) for r, c, k in observed if r == "PRODUCER"]
    verifiers = [(c, k) for r, c, k in observed if r == "VERIFIER"]
    closures = [(c, k) for r, c, k in observed if r == "CLOSURE"]
    journal = journal_records(composed.journal_path)
    candidates = [decode_candidate(r["candidate"]) for r in journal if r.get("event") == "invocation-outcome" and r.get("role") == "PRODUCER"]
    revisions = [revision_of(c.locator) for c in candidates if c is not None]
    verifier_heads = {c: git_head(composed.producer_read_back / f"verifier-{c}", composed.git_environment) for c, _ in verifiers}
    verified = [decode_candidate(r["candidate"]) for r in journal if r.get("event") == "invocation-outcome" and r.get("role") == "VERIFIER"]
    closure_head = git_head(composed.producer_read_back / f"closure-{closures[0][0]}", composed.git_environment) if closures else None
    receipts = [(r["receipt"], r.get("state")) for r in composed.work.receipts()]
    ledger = effects(composed)
    record = state["record"]
    findings = record.get("findings") or []
    before = (len(journal), ledger)
    reopened = compose(root, document, spec["script"], environment)
    again = reopened.coordinator.start()
    after = (len(journal_records(reopened.journal_path)), effects(reopened))
    launches = started(composed)
    checks = [
        check("L1", "complete lifecycle reaches DONE", state["stage"] == "DONE" and state["outcome"] == "closed" and state["read_back_proven"] and set(summary.dispatched) == {composed.work_identity},
              "the item reaches DONE (closed) with an independently read-back candidate", {"state": state, "dispatched": list(summary.dispatched)}),
        check("L2", "distinct canonical role invocations", [k for _, k in producers] == ["success", "success"] and [k for _, k in verifiers] == ["reject", "accept"] and [k for _, k in closures] == ["closed"] and len(set(launches)) == len(launches) == 5,
              "PRODUCER success, VERIFIER reject, PRODUCER success, VERIFIER accept, CLOSURE closed; five distinct correlations", {"outcomes": observed, "started": launches}),
        check("L3", "actual local Git publication of each candidate", len(revisions) == 2 and len(set(revisions)) == 2 and all(remote.get(c.locator.rsplit("#", 1)[1].rsplit("@", 1)[0]) == revision_of(c.locator) for c in candidates if c) and revision_of(state["candidate"]) == revisions[-1],
              "both producer candidates are advertised by the bare remote at their exact revisions; custody holds the second", {"remote": remote, "revisions": revisions}),
        check("L4", "fresh verifier retrieval of the exact candidate", len(verifiers) == 2 and all(verifier_heads[c] == revision_of(v.locator) for (c, _), v in zip(verifiers, verified) if v) and [revision_of(v.locator) for v in verified if v] == revisions and all(c not in {p for p, _ in producers} for c, _ in verifiers),
              "each verifier invocation is distinct from every producer and judged a fresh clone at exactly the candidate it was given", {"verifier_heads": verifier_heads, "judged": [revision_of(v.locator) if v else None for v in verified]}),
        check("L5", "rejection recorded and reworked into a fresh candidate", record.get("rejections") == 1 and len(findings) == 1 and findings[0].get("source") == "verifier" and findings[0].get("correlation") == verifiers[0][0] and findings[0].get("findings"),
              "one attributable verifier finding under the rejecting invocation; rejections = 1", {"findings": findings, "rejections": record.get("rejections")}),
        check("L6", "no success-collapse projection", receipts == [("release-proposed", None), ("execution-state-projected", "VERIFY"), ("execution-state-projected", "IMPLEMENT"), ("release-proposed", None), ("execution-state-projected", "VERIFY"), ("execution-state-projected", "ACCEPT"), ("execution-state-projected", "DONE")],
              "each producer run passes release admission; the kernel projects VERIFY, IMPLEMENT (rework), VERIFY, ACCEPT and DONE, each after its own role outcome", {"receipts": receipts}),
        check("L7", "actual closure receipts", closures and record.get("receipts") == ["candidate-published"] and record.get("closure") == ["candidate-published"] and closure_head == revisions[-1],
              "closure performed and read back candidate-published by re-retrieving the accepted revision into a fresh clone", {"receipts": record.get("receipts"), "closure_clone_head": closure_head}),
        check("L8", "exactly one effect per invocation, each confirmed", [e[0] for e in ledger] == sorted(launches) and all(status == "confirmed" and receipt == f"outcome:{kind}" for (identity, status, receipt), (_, _, kind) in zip(ledger, sorted(observed, key=lambda o: o[1]))),
              "one FD-05 effect per launch correlation, confirmed with its read-back outcome kind; none pending or unknown", {"effects": ledger}),
        check("L9", "restart is idempotent", again.dispatched == () and before == after,
              "reopening the root dispatches nothing and changes neither the journal nor the effect ledger", {"dispatched_after_restart": list(again.dispatched), "journal_records": [before[0], after[0]]}),
        check("L10", "zero provider calls and no scripted lifecycle", journal_provider_calls(composed.journal_path) == 0 and not any("stage" in r or "lifecycle" in r for r in journal) and not hasattr(composed.process, "_store"),
              "no provider executable was attempted; the journal carries no lifecycle field; the scripted process holds no store", {"provider_calls": journal_provider_calls(composed.journal_path)}),
    ]
    return checks, {"state": state, "outcomes": observed, "candidates": revisions, "effects": ledger, "receipts": receipts}


def wrong_candidate(root: Path, document, manifest_path: Path, environment):
    """A custody record naming a candidate the producer never published is refused before the verifier launches."""
    spec = _spec(document, "wrong-candidate")
    composed = compose(root, document, spec["script"], environment)
    fault_at_verify(composed, str(spec["fault"]))
    composed.coordinator.start()
    state = state_of(composed)
    refusals = dict(composed.worker.refusals)
    return [check("W1", "wrong candidate refused before launch", state["stage"] == "VERIFY" and state["outcome"] == "authority-block" and list(refusals.values()) == ["candidate-custody-unattributable"] and process_runs(composed, "VERIFIER") == [] and started(composed, "VERIFIER") == [] and inbox(composed) == [composed.work_identity],
                  "held at VERIFY: the guard refuses the verifier (candidate-custody-unattributable); no verifier starts or runs; a decision is requested", {"state": state, "refusals": refusals, "verifier_runs": process_runs(composed, "VERIFIER")})], {"refusals": refusals}


def unpublished_candidate(root: Path, document, manifest_path: Path, environment):
    """A candidate withdrawn from the remote cannot be retrieved, so nothing is judged."""
    spec = _spec(document, "unpublished-candidate")
    composed = compose(root, document, spec["script"], environment)
    fault_at_verify(composed, str(spec["fault"]))
    composed.coordinator.start()
    state = state_of(composed)
    observed = outcomes(composed)
    return [check("U1", "unpublished candidate is not retrievable and holds", state["stage"] == "VERIFY" and state["outcome"] == "authority-block" and [k for r, _, k in observed if r == "VERIFIER"] == ["candidate-unavailable"] and process_runs(composed, "VERIFIER") == [],
                  "the verifier's fresh retrieval refuses the unpublished revision; no verifier process runs; held at VERIFY", {"state": state, "outcomes": observed, "remote": advertised(composed)})], {"outcomes": observed}


def corrupted_outcome(name: str, identifier: str) -> Scenario:
    def scenario(root: Path, document, manifest_path: Path, environment):
        spec = _spec(document, name)
        composed = compose(root, document, spec["script"], environment)
        fault_journal(composed, str(spec["fault"]))
        composed.coordinator.start()
        state = state_of(composed)
        runs = process_runs(composed, "PRODUCER")
        unknown = [e for e in effects(composed) if e[1] == "unknown"]
        return [check(identifier, f"{spec['fault']} holds despite process success",
                      state["stage"] == "IMPLEMENT" and state["outcome"] == "authority-block" and state["candidate"] is None and runs == [("PRODUCER", f"launch:{composed.work_identity}:0", "success")] and started(composed, "PRODUCER") == [f"launch:{composed.work_identity}:0"] and [e[0] for e in unknown] == [f"launch:{composed.work_identity}:0"] and composed.worker.retained == {},
                      "the process succeeded and published, but its durable outcome is not this invocation's: no transition, no custody, no replacement; the effect stays UNKNOWN for a decision",
                      {"state": state, "producer_runs": runs, "unknown_effects": unknown, "remote": advertised(composed)})], {"state": state}
    return scenario


def delayed_readback(root: Path, document, manifest_path: Path, environment):
    """The owner dies after the durable producer outcome; the restart reads it back once and never re-runs it."""
    spec = _spec(document, "delayed-readback")
    exit_status = crash_child(root, manifest_path, "delayed-readback", environment)
    restarted = compose(root, document, spec["restart_script"], environment)
    restarted.coordinator.start()
    state = state_of(restarted)
    observed = outcomes(restarted)
    return [check("D1", "delayed correlated read-back is applied exactly once", exit_status == CRASH_EXIT and state["stage"] == "DONE" and [r for r, _, _ in process_runs(restarted)] == ["PRODUCER", "VERIFIER"] and [(r, k) for r, _, k in observed] == [("PRODUCER", "success"), ("VERIFIER", "accept"), ("CLOSURE", "closed")],
                  "after the owner died past its durable outcome, recovery reads it back and advances once: one producer run, DONE", {"crash_exit": exit_status, "state": state, "runs": process_runs(restarted), "outcomes": observed})], {"state": state}


def judgment_hold(root: Path, document, manifest_path: Path, environment):
    """A judgment-required outcome holds, survives restart as one attention item, is not released by SEEN, and resumes exactly once on a decision."""
    spec = _spec(document, "judgment-hold")
    composed = compose(root, document, spec["script"], environment)
    composed.coordinator.start()
    held = state_of(composed)
    held_inbox = inbox(composed)
    first = attention_items(composed)
    reopened = compose(root, document, spec["restart_script"], environment)
    again = reopened.coordinator.start()
    # The same escalation delivered again by the restarted composition finds the same item.
    request = open_request(reopened)
    redelivered = reopened.notifier.notify(request) if request is not None else DeliveryHealth(False, "no open decision request")
    items = attention_items(reopened)
    held_runs = process_runs(reopened, "PRODUCER")
    service = reopened.attention.attention
    seen = service.seen(items[0]["identity"], "fx-o-operator", service.show(items[0]["identity"]).version) if items else None
    still = reopened.coordinator.start()
    still_state = state_of(reopened)
    decide(reopened, "fx-o-judgment-authorize")
    done = state_of(reopened)
    runs = process_runs(reopened, "PRODUCER")
    decisions = [identity for identity, _, _ in reopened.store.list_states(reopened.manifest.profile, "decision:")]
    return [
        check("J1", "judgment-required outcome holds with one JUDGMENT attention item", held["stage"] == "IMPLEMENT" and held["outcome"] == "authority-block" and held_inbox == [composed.work_identity] and len(first) == 1 and first[0]["kind"] == "JUDGMENT" and first[0]["status"] == "PENDING",
              "the worker's authority-block holds at IMPLEMENT, opens one DecisionInbox request and one PENDING JUDGMENT attention item", {"state": held, "inbox": held_inbox, "attention": first}),
        check("J2", "restart dedupes the attention item and launches nothing", again.dispatched == () and redelivered.delivered and [i["identity"] for i in items] == [i["identity"] for i in first] and [r[1] for r in held_runs] == [f"launch:{composed.work_identity}:0"],
              "after a restart the same escalation, delivered again, resolves to the same single attention identity; nothing is dispatched", {"attention": items, "redelivered": redelivered.detail, "dispatched": list(again.dispatched)}),
        check("J3", "SEEN is not a decision", seen is not None and seen.status == "SEEN" and still.dispatched == () and still_state["outcome"] == "authority-block",
              "marking the item SEEN leaves the work held and dispatches nothing", {"seen": None if seen is None else seen.status, "state": still_state}),
        check("J4", "one attributable decision resumes exactly once", done["stage"] == "DONE" and [r[2] for r in runs] == ["authority-block", "success"] and decisions == [f"decision:{composed.work_identity}"],
              "a single DecisionInbox authorize readmits the work once: exactly two producer runs (the held one and one resumed), DONE", {"state": done, "producer_runs": runs, "decisions": decisions}),
    ], {"attention": items}


def unknown_effect(root: Path, document, manifest_path: Path, environment):
    """The owner dies after publishing but before its durable outcome: the effect is UNKNOWN, so nothing replaces it until one decision authorizes exactly one effect."""
    spec = _spec(document, "unknown-effect")
    exit_status = crash_child(root, manifest_path, "unknown-effect", environment)
    published = advertised(root)
    restarted = compose(root, document, spec["restart_script"], environment)
    attested = restarted.real_worker.attest_ownership(WorkerInvocation(restarted.work_identity, f"launch:{restarted.work_identity}:0", None, "PRODUCER"))
    restarted.coordinator.start()
    held = state_of(restarted)
    held_starts = started(restarted, "PRODUCER")
    items = attention_items(restarted)
    decide(restarted, "fx-o-unknown-effect-authorize")
    done = state_of(restarted)
    ledger = effects(restarted)
    remote = advertised(restarted)
    original = f"candidate/launch-{restarted.work_identity}-0"
    return [
        check("E1", "an escaped effect is UNKNOWN and is never replaced", exit_status == CRASH_EXIT and attested.kind == "effect-unknown" and not attested.quiescent and held["outcome"] == "authority-block" and held_starts == [f"launch:{restarted.work_identity}:0"] and restarted.worker.retained == {} and len(items) == 1,
              "the owner is dead but its publication began: attestation effect-unknown, nothing retained, no replacement, one JUDGMENT item", {"crash_exit": exit_status, "attested": attested.kind, "state": held, "producer_starts": held_starts}),
        check("E2", "exactly one authorized effect and readback identity", [e for e in ledger if e[1] == "authority-authorized"] == [(f"launch:{restarted.work_identity}:0", "authority-authorized", None)] and done["stage"] == "DONE" and remote.get(original) == published.get(original) and revision_of(done["candidate"]) != published.get(original),
              "one decision authorizes exactly the one unknown effect; the escaped publication is retained untouched; a new candidate reaches DONE", {"effects": ledger, "original_branch": [published.get(original), remote.get(original)], "state": done}),
    ], {"effects": ledger}


def conclusive_loss(name: str, prefix: str) -> Scenario:
    def scenario(root: Path, document, manifest_path: Path, environment):
        spec = _spec(document, name)
        exit_status = crash_child(root, manifest_path, name, environment)
        restarted = compose(root, document, spec["restart_script"], environment)
        original = f"launch:{restarted.work_identity}:0"
        restarted.coordinator.start()
        state = state_of(restarted)
        retained = [r for r in journal_records(restarted.journal_path) if r.get("event") == "invocation-outcome" and r.get("kind") == MISSING_TERMINAL_RESULT]
        starts = started(restarted, "PRODUCER")
        runs = process_runs(restarted, "PRODUCER")
        begun = [r for r in journal_records(restarted.journal_path) if r.get("event") == "invocation-started" and r.get("correlation_id") == original]
        progress = git_head(restarted.workspaces / original, restarted.git_environment) if (restarted.workspaces / original).exists() else None
        ledger = effects(restarted)
        expected_runs = 1 if name == "crash-before-output" else 2
        checks = [
            check(f"{prefix}1", "conclusive owner death with a confirmed missing result recovers deterministically",
                  exit_status == CRASH_EXIT and state["stage"] == "DONE" and len(retained) == 1 and retained[0]["correlation_id"] == original and retained[0]["ownership"] == "owner-terminated"
                  and len(starts) == 2 and starts[0] == original and len(runs) == expected_runs and inbox(restarted) == [] and restarted.worker.retained == {original: "owner-terminated"}
                  and (original, "confirmed", f"outcome:{MISSING_TERMINAL_RESULT}") in ledger,
                  "the restart attests the journaled owner ended with nothing owned alive and no publication begun, retains missing-terminal-result against the original invocation, and re-dispatches once in the same run with no decision",
                  {"crash_exit": exit_status, "retained": retained, "producer_starts": starts, "producer_runs": runs, "inbox": inbox(restarted), "state": state}),
            check(f"{prefix}2", "original identity and evidence preserved",
                  len(begun) == 1 and isinstance(begun[0].get("owner"), dict) and f"candidate/launch-{restarted.work_identity}-0" not in advertised(restarted)
                  and (name == "crash-before-output" or (progress is not None and progress != restarted.baseline_revision)),
                  "the original invocation keeps its one attested start and its retained outcome; nothing was published under it" + ("; its worktree keeps the progress commit" if name != "crash-before-output" else ""),
                  {"started": begun, "progress_head": progress, "baseline": restarted.baseline_revision}),
        ]
        return checks, {"state": state}
    return scenario


def unknown_ownership(name: str, identifier: str) -> Scenario:
    def scenario(root: Path, document, manifest_path: Path, environment):
        spec = _spec(document, name)
        survivor = None
        if name == "owner-alive":
            owner = crash_child(root, manifest_path, name, environment, hang=True)
        else:
            owner = crash_child(root, manifest_path, name, environment)
            work = document["work_items"][0]["identity"]  # type: ignore[index]
            [begun] = [r for r in journal_records(Path(root) / "worker-journal" / "journal.jsonl") if r.get("event") == "invocation-started"]
            # Work the dead owner left behind: it carries that owner's markers.
            survivor = subprocess.Popen(["sleep", "120"], env={"PATH": environment.get("PATH", "/usr/bin:/bin"), INVOCATION_MARKER: f"launch:{work}:0",
                                                               INVOCATION_OWNER_MARKER: f"{owner_token(begun['owner'])}/left-behind"})
        try:
            restarted = compose(root, document, spec["restart_script"], environment)
            original = f"launch:{restarted.work_identity}:0"
            attested = restarted.real_worker.attest_ownership(WorkerInvocation(restarted.work_identity, original, None, "PRODUCER"))
            restarted.coordinator.start()
            state = state_of(restarted)
            starts = started(restarted, "PRODUCER")
        finally:
            for process in (owner, survivor):
                if isinstance(process, subprocess.Popen):
                    process.send_signal(signal.SIGKILL)
                    process.wait()
        expected = "owner-alive" if name == "owner-alive" else "owned-work-active"
        return [check(identifier, "UNKNOWN ownership blocks replacement",
                      attested.kind == expected and not attested.quiescent and state["outcome"] == "authority-block" and starts == [original] and restarted.worker.retained == {} and process_runs(restarted, "PRODUCER") == [],
                      f"attestation {expected}: nothing is retained against the original invocation and no replacement actor launches; the item holds for a decision",
                      {"attested": attested.kind, "state": state, "producer_starts": starts})], {"state": state}
    return scenario


SCENARIOS: dict[str, Scenario] = {
    "lifecycle": lifecycle,
    "wrong-candidate": wrong_candidate,
    "unpublished-candidate": unpublished_candidate,
    "miscorrelated-outcome": corrupted_outcome("miscorrelated-outcome", "M1"),
    "duplicate-outcome": corrupted_outcome("duplicate-outcome", "N1"),
    "malformed-outcome": corrupted_outcome("malformed-outcome", "F1"),
    "delayed-readback": delayed_readback,
    "judgment-hold": judgment_hold,
    "unknown-effect": unknown_effect,
    "crash-before-output": conclusive_loss("crash-before-output", "C"),
    "progress-then-crash": conclusive_loss("progress-then-crash", "P"),
    "owner-alive": unknown_ownership("owner-alive", "A1"),
    "owned-work-active": unknown_ownership("owned-work-active", "B1"),
}


def run_scenario(name: str, root: Path, manifest_path: Path, environment: Mapping[str, str]) -> tuple[list[dict[str, object]], dict[str, object]]:
    return SCENARIOS[name](Path(root), load_document(manifest_path), Path(manifest_path), environment)


# --- the proof ----------------------------------------------------------------------------


def run_proof(root: Path, manifest_path: Path, environment: Mapping[str, str], *, scenarios: tuple[str, ...] | None = None, network_timeout: float = 3.0) -> tuple[int, dict[str, object]]:
    started_at = time.monotonic()
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    document = load_document(manifest_path)
    credentials = credential_findings(environment)
    network = network_denial_probe(network_timeout, environment)
    report: dict[str, object] = {
        "schema_version": "1.0", "record_kind": "CapstoneProofRun", "biu_id": BIU, "fixture_id": FIXTURE,
        "manifest": {"path": str(manifest_path), "digest": "sha256:" + sha256(json.dumps(document, sort_keys=True, separators=(",", ":")).encode()).hexdigest()},
        "network_denial": network, "credentials_present": list(credentials), "substituted_boundaries": list(SUBSTITUTIONS),
        "live_proof": "NOT_ESTABLISHED", "shared_profile_proof": "NOT_ESTABLISHED", "sovereignty_proof": "NOT_ESTABLISHED",
        "token_usage": "UNKNOWN", "cost": "UNKNOWN", "recorded_at": utc_now(), "hold_reasons": [], "scenarios": {},
    }
    holds = []
    if credentials:
        holds.append(f"credential variables present in the proof environment: {list(credentials)}")
    if network.get("status") != "ENFORCED":
        holds.append(f"outbound network denial not established: {json.dumps(network.get('socket'))}")
    if holds:
        report |= {"verdict": "HOLD", "hold_reasons": holds}
        _write(root, report)
        return EXIT_HOLD, report
    statuses = []
    for name in scenarios or tuple(SCENARIOS):
        try:
            checks, facts = run_scenario(name, root / "scenarios" / name, manifest_path, environment)
        except Exception as error:  # noqa: BLE001 - a scenario that cannot complete is a FAIL, reported, never skipped
            checks, facts = [check(f"{name}-error", f"{name} completed", False, "the scenario completes", f"{type(error).__name__}: {error}")], {}
        report["scenarios"][name] = {"checks": checks, "facts": facts}  # type: ignore[index]
        statuses.extend(entry["status"] for entry in checks)
    verdict = "PASS" if statuses and all(status == "PASS" for status in statuses) else "FAIL"
    report |= {"verdict": verdict, "elapsed_seconds": round(time.monotonic() - started_at, 3),
               "provider": SCRIPTED_PROVIDER}
    _write(root, report)
    return EXIT_PASS if verdict == "PASS" else EXIT_FAIL, report


def _write(root: Path, report: Mapping[str, object]) -> None:
    (Path(root) / "run-report.json").write_text(json.dumps(report, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _crash_main(arguments: argparse.Namespace) -> int:
    document = load_document(arguments.manifest)
    spec = _spec(document, arguments.scenario)
    composed = compose(arguments.root, document, spec["script"], os.environ)
    die_at(composed, str(spec["crash"]), Path(arguments.root) / "owner-ready" if arguments.hang else None)
    composed.coordinator.start()
    print(json.dumps({"crashed": False}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="alienintent.composition.lifecycle_capstone")
    sub = parser.add_subparsers(dest="command")
    crash = sub.add_parser("crash", help="internal: compose one scenario phase and die (or hang) at its boundary")
    crash.add_argument("--root", type=Path, required=True)
    crash.add_argument("--manifest", type=Path, required=True)
    crash.add_argument("--scenario", required=True)
    crash.add_argument("--hang", action="store_true")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--scenario", action="append", choices=tuple(SCENARIOS))
    parser.add_argument("--network-timeout", type=float, default=3.0)
    arguments = parser.parse_args(argv)
    if arguments.command == "crash":
        return _crash_main(arguments)
    if arguments.root is None or arguments.manifest is None:
        parser.error("--root and --manifest are required")
    status, report = run_proof(arguments.root, arguments.manifest, os.environ, scenarios=tuple(arguments.scenario or ()) or None,
                               network_timeout=arguments.network_timeout)
    print(json.dumps({"fixture_id": FIXTURE, "verdict": report["verdict"], "exit_status": status, "hold_reasons": report["hold_reasons"],
                      "failed": [c["id"] for s in report.get("scenarios", {}).values() for c in s["checks"] if c["status"] != "PASS"]}))
    return status


if __name__ == "__main__":
    sys.exit(main())
