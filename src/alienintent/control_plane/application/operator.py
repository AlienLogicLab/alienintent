"""Named operator application services; CLI adapters never write the store."""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, is_dataclass
import json
import logging
import os
from pathlib import Path
import stat
from typing import Any, Protocol

from alienintent.control_plane.application.decision_inbox import DecisionInbox
from alienintent.execution_coordination.application.factory_coordinator import LAUNCH_KEY, LAUNCH_SCOPE
from alienintent.execution_coordination.domain.escalation import DecisionSubmission
from alienintent.execution_coordination.ports.operational_store import ReservationRejected
from alienintent.execution_coordination.ports.worker_provider import VERIFIER


logger = logging.getLogger(__name__)


class OperatorDenied(ValueError):
    pass


class WorkMigration(Protocol):
    """The project's work identity service as `work migrate` uses it (bound by the profile's composition)."""

    def migrate(self, snapshot: Mapping[str, object], profiles: Sequence[str]) -> object: ...


def migrate_work(identities: WorkMigration, snapshot: object, profiles: Sequence[str]) -> dict[str, object]:
    """`work migrate`: hand the identity snapshot and the named profiles to the project's work identity service,
    which owns the one transaction; the operator surface only validates the shape and reports."""
    if isinstance(snapshot, Mapping) and isinstance(snapshot.get("identity_snapshot"), Mapping):
        snapshot = snapshot["identity_snapshot"]  # An authority-limits document carries the snapshot inside.
    if not isinstance(snapshot, Mapping) or not profiles or not all(isinstance(p, str) and p for p in profiles):
        raise OperatorDenied("work migrate needs an identity snapshot object and at least one profile")
    report = identities.migrate(snapshot, list(profiles))
    return asdict(report) if is_dataclass(report) else dict(report)


class WorkRecords(Protocol):
    """The project's work-record operations as `work register`, `work import` and `work show` use them (bound by
    the profile's composition)."""

    def register(self, packet: bytes, repo: str, path: str, commit: str, label: str, kind: str,
                 parent_id: str | None) -> Any: ...

    def import_completed(self, packet: bytes, repo: str, path: str, commit: str, label: str, issue: str,
                         evidence: Mapping[str, object]) -> Any: ...

    def show(self, id_or_label: str) -> Any: ...


def register_work(records: WorkRecords, packet: bytes, repo: str, path: str, commit: str, label: str, kind: str,
                  parent_id: str | None) -> dict[str, object]:
    """`work register`: the packet file's bytes go to the project's work-record service, which owns the one
    transaction and the byte comparison with Git; the operator surface only reports the row."""
    return asdict(records.register(packet, repo, path, commit, label, kind, parent_id))


def import_work(records: WorkRecords, packet: bytes, repo: str, path: str, commit: str, label: str, issue: str,
                evidence: Mapping[str, object]) -> dict[str, object]:
    """`work import`: earlier completed work at DONE with exactly the evidence references given."""
    return asdict(records.import_completed(packet, repo, path, commit, label, issue, evidence))


def show_work(records: WorkRecords, id_or_label: str) -> dict[str, object]:
    """`work show`: the row, its parent, its children and the packet text at the pinned commit. A name no row holds
    is the read answer UNKNOWN_IDENTITY, not a failure."""
    record = records.show(id_or_label)
    if record is None:
        return {"answer": "UNKNOWN_IDENTITY"}
    value = asdict(record)
    value["packet"] = None if record.packet is None else record.packet.decode("utf-8")
    return value


class WorkAssessment(Protocol):
    """The project's packet assessment as `work assess` uses it (bound by the profile's composition)."""

    def assess(self, id_or_label: str, revision: tuple[bytes, str] | None, recover: str | None) -> Any: ...


def assess_work(assessment: WorkAssessment, id_or_label: str, revision: tuple[bytes, str] | None,
                recover: str | None) -> dict[str, object]:
    """`work assess`: the item id, attempt id, disposition and saved reference, or a refusal or hold returned as the
    read answer naming its code, the way `work show` answers UNKNOWN_IDENTITY."""
    result = assessment.assess(id_or_label, revision, recover)
    value = asdict(result)
    if "reason_code" in value:
        value["answer"] = value.pop("reason_code")
    return value


class WorkAuthorizations(Protocol):
    """The project's work authorization as `work authorize` uses it (bound by the profile's composition)."""

    def authorize(self, id_or_label: str, commit: str, attempt: str, baseline: str, quote: str) -> Any: ...


def authorize_work(authorization: WorkAuthorizations, id_or_label: str, commit: str, attempt: str, baseline: str,
                   quote: str) -> dict[str, object]:
    """`work authorize`: the item, its evidence reference and the recorded release authorization, or a refusal
    returned as the read answer naming its code. It records the Founder's approval; it does not grant it."""
    return asdict(authorization.authorize(id_or_label, commit, attempt, baseline, quote))


class WorkCompletions(Protocol):
    """The project's completed-work recording as `work record-completed` uses it (bound by the profile's
    composition)."""

    def record(self, id_or_label: str, candidate: str, landing: str, record_path: str, verifications: Sequence[Any],
               approval: Any, quote: str) -> Any: ...


def record_completed_work(completion: WorkCompletions, id_or_label: str, candidate: str, landing: str,
                          record_path: str, verifications: Sequence[Any], approval: Any,
                          quote: str) -> dict[str, object]:
    """`work record-completed`: the item and its `work-completion` evidence reference once the row is DONE, or a
    refusal returned as the read answer naming its code. It records completed work; it does not judge it."""
    return asdict(completion.record(id_or_label, candidate, landing, record_path, verifications, approval, quote))


class WorkLinks(Protocol):
    """The project's link service as `work link` and `work display` use it (bound by the profile's composition)."""

    def link(self, id_or_label: str, issue: int | None) -> Any: ...

    def display(self, id_or_label: str) -> Any: ...


def link_work(links: WorkLinks, id_or_label: str, issue: int | None) -> dict[str, object]:
    """`work link`: the item's Issue, card and the duplicates closed, or a refusal returned as the read answer
    naming its code, the way `work show` answers UNKNOWN_IDENTITY."""
    return asdict(links.link(id_or_label, issue))


def display_work(links: WorkLinks, id_or_label: str) -> dict[str, object]:
    """`work display`: `unchanged` or `updated` once read back, or a refusal returned as the read answer."""
    return asdict(links.display(id_or_label))


# The stated answer of the read-only worker profile to every command other than `work context`.
NOT_AVAILABLE_IN_WORKER_PROFILE = "not-available-in-worker-profile"


class WorkContexts(Protocol):
    """The project's context assembly as `work context` uses it (bound by the profile's composition)."""

    def assemble(self, identity: str, role: str, correlation: str, contract_digest: str | None,
                 candidate: Any = None, clone: Path | None = None) -> Any: ...


def context_work(context: WorkContexts, id_or_label: str, role: str, correlation: str, candidate: str | None,
                 workspace: Path, contract_digest: str | None = None) -> dict[str, object]:
    """`work context`: the role's context package for the work item and attempt, or the hold that prevents launch,
    as the read answer. `contract_digest` is the launched invocation's (`--contract-digest`, which a launched
    package's `context_command` carries): another digest is held DIGEST_MISMATCH; without it none is compared. A
    VERIFIER runs it in its candidate clone (`workspace`), where the diff is taken."""
    return context.assemble(id_or_label, role, correlation, contract_digest, candidate,
                            workspace if role == VERIFIER else None).document()


# `work context --export` (unit WORKER-CREDENTIAL-BOUNDARY section 0.6b): the answers when nothing is printed.
NOT_IN_EXPORT, EXPORT_REFUSED = "not-in-export", "export-refused"
EXPORT_LIMIT = 16 << 20


def export_context(export: str, environment: Mapping[str, str], founder_uid: int | None = None) -> dict[str, object]:
    """`work context --export <file>`: the package the control plane exported for this invocation, re-printed.

    It opens only `<...>/exports/<correlation>/context.json`, where `<correlation>` is ALIENINTENT_CORRELATION:
    each folder with O_PATH|O_DIRECTORY|O_NOFOLLOW, the file with O_RDONLY|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC, and
    refuses by fstat on those descriptors anything but Founder-owned folders and a Founder-owned regular file (the
    Founder's user is the owner of `exports`, unless `founder_uid` is given); it reads only from that descriptor. The
    work item, role and correlation must be ALIENINTENT_WORK_IDENTITY, ALIENINTENT_ROLE and ALIENINTENT_CORRELATION.
    A request for another correlation, path or argument answers `not-in-export` and reads nothing; another work item
    or role is found only inside the file, so that answer comes after reading it. A refused file answers
    `export-refused`. Without a trusted Founder fact for the worker, "the Founder's user" is the owner of `exports`. It builds no
    profile and opens no database, evidence repository or configuration. The identity check is a consistency check of
    this API, not an isolation boundary: every worker-user process can read any export whose path it learns."""
    identity, role, correlation = (environment.get(name, "") for name in (
        "ALIENINTENT_WORK_IDENTITY", "ALIENINTENT_ROLE", "ALIENINTENT_CORRELATION"))
    path = Path(export)
    if not (identity and role and correlation) or any(part in correlation for part in ("/", "\\", "..", "\x00")) \
            or not path.is_absolute() or path.name != "context.json" or path.parent.name != correlation \
            or path.parent.parent.name != "exports":
        return {"error": NOT_IN_EXPORT}
    folder_flags = os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptors: list[int] = []
    try:
        descriptors.append(os.open(path.parent.parent, folder_flags))
        descriptors.append(os.open(correlation, folder_flags, dir_fd=descriptors[0]))
        descriptors.append(os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                                   dir_fd=descriptors[1]))
        exports, folder, opened = (os.fstat(descriptor) for descriptor in descriptors)
        owner = exports.st_uid if founder_uid is None else founder_uid
        if exports.st_uid != owner or folder.st_uid != owner or opened.st_uid != owner \
                or not stat.S_ISREG(opened.st_mode) or opened.st_size > EXPORT_LIMIT:
            return {"error": EXPORT_REFUSED}
        data = b""
        while chunk := os.read(descriptors[2], 1 << 16):
            data += chunk
            if len(data) > EXPORT_LIMIT:
                return {"error": EXPORT_REFUSED}
    except OSError:
        return {"error": EXPORT_REFUSED}
    finally:
        for descriptor in descriptors:
            os.close(descriptor)
    try:
        document = json.loads(data.decode("utf-8"))
        named = document["context_command"]["environment"]["ALIENINTENT_CORRELATION"]
    except (ValueError, TypeError, KeyError):
        return {"error": EXPORT_REFUSED}
    if document.get("identity") != identity or document.get("role") != role or named != correlation:
        return {"error": NOT_IN_EXPORT}
    return document


class WorkLaunches(Protocol):
    """The registry coordinator as `work launch` uses it (bound by the profile's composition)."""

    def launch(self, identity: str) -> Any: ...


def launch_work(coordinator: WorkLaunches, identity: str) -> dict[str, object]:
    """`work launch`: one role step (PRODUCER at IMPLEMENT or VERIFIER at VERIFY) for exactly the named work item,
    reported as its run summary, or the answer that nothing was launched (`closure-not-automated`, `not-eligible`,
    `wip-refused`, `wip-limit-unavailable`)."""
    result = coordinator.launch(identity)
    return {"identity": identity, **({"answer": result} if isinstance(result, str) else asdict(result))}


# `work launch` answers when another launch holds the one exclusive registry-wide reservation, or when this process
# cannot name itself as its owner. Both write nothing.
LAUNCH_IN_PROGRESS, LAUNCH_OWNER_UNAVAILABLE = "LAUNCH_IN_PROGRESS", "LAUNCH_OWNER_UNAVAILABLE"


class LaunchOwnership(Protocol):
    """The existing process ownership observation, as the exclusive `work launch` reservation uses it."""

    def current(self) -> Mapping[str, object] | None: ...

    def owner_state(self, owner: Mapping[str, object]) -> str: ...


def exclusive_launch_work(launcher: Callable[[], WorkLaunches], identity: str, store: Any, ownership: LaunchOwnership,
                          profile: str = "registry") -> dict[str, object]:
    """`work launch`, one at a time: `launch_work` inside one exclusive registry-wide reservation (the store's atomic
    `acquire`, scope `launch`, key `registry`, owner `launcher:<this process as canonical JSON>`), released with its
    owner and fence afterwards. A held reservation is taken over only when its owner has `terminated`; while it is
    `alive` or `unknown`, or when another process took it over first, the answer is LAUNCH_IN_PROGRESS."""
    current = ownership.current()
    if current is None:
        return {"identity": identity, "answer": LAUNCH_OWNER_UNAVAILABLE}
    owner = "launcher:" + json.dumps(dict(current), sort_keys=True, separators=(",", ":"))
    try:
        reservation = store.acquire(profile, LAUNCH_SCOPE, LAUNCH_KEY, owner)
    except ReservationRejected:
        held = next((r for r in store.recovery_reservations(profile) if (r.scope, r.key) == (LAUNCH_SCOPE, LAUNCH_KEY)),
                    None)
        state = "unknown"
        if held is not None:
            try:
                recorded = json.loads(held.owner.removeprefix("launcher:"))
            except ValueError:
                recorded = None
            state = ownership.owner_state(recorded) if isinstance(recorded, dict) else "unknown"
        if held is None or state != "terminated":
            return {"identity": identity, "answer": LAUNCH_IN_PROGRESS, "owner_state": state}
        try:
            store.release(profile, held.scope, held.key, held.owner, held.fence)  # StaleFence: taken over first
            reservation = store.acquire(profile, LAUNCH_SCOPE, LAUNCH_KEY, owner)
        except ReservationRejected:
            return {"identity": identity, "answer": LAUNCH_IN_PROGRESS, "owner_state": state}
    try:
        return launch_work(launcher(), identity)
    finally:
        store.release(profile, reservation.scope, reservation.key, reservation.owner, reservation.fence)


class WorkDecisions(Protocol):
    """The registry decision path as `work decide` uses it (bound by the profile's composition)."""

    def decide(self, identity: str, choice: str, quote: str) -> Mapping[str, object]: ...


def decide_work(decisions: WorkDecisions, identity: str, choice: str, quote: str) -> dict[str, object]:
    """`work decide`: a choice the work item's open decision request offers, through the existing decision path; it
    never launches anything (the next step is always an explicit `work launch`)."""
    if not quote.strip():
        raise OperatorDenied("work decide needs the Founder's words")
    return {"identity": identity, **decisions.decide(identity, choice, quote)}


class OperatorControlPlane:
    def __init__(self, profile: str, store: Any, work: Any, coordinator: Any, readiness: Callable[[], bool], clock: Callable[[], str] = lambda: "not-recorded") -> None:
        self._profile, self._store, self._work, self._coordinator, self._readiness, self._clock = profile, store, work, coordinator, readiness, clock

    def status(self) -> dict[str, object]:
        diagnostics: list[dict[str, object]] = []
        try:
            upstream = {"source": "work-management", "status": "available", "items": [item.identity for item in self._work.import_ready_snapshot()]}
        except Exception:
            upstream = {"source": "work-management", "status": "unavailable"}
            diagnostics.append(self._coalesce_diagnostic("upstream-unavailable", "work-management unavailable"))
        items = [
            {"identity": identity.removeprefix("factory:"), "revision": version, "lifecycle": state.get("stage"), "outcome": state.get("outcome")}
            for identity, version, state in self._store.list_states(self._profile, "factory:")
        ]
        delivery = getattr(self._coordinator, "delivery_health", {})
        projection = "healthy" if delivery and all(value.delivered for value in delivery.values()) else "unknown"
        logger.info("operator_status", extra={"profile": self._profile, "upstream": upstream["status"], "projection": projection})
        return {"profile": self._profile, "upstream": upstream, "execution": {"source": "operational-store", "status": "known", "items": items, "wip": len(items)}, "projection": {"source": "decision-notifier", "status": projection}, "diagnostics": diagnostics}

    def _coalesce_diagnostic(self, condition: str, message: str) -> dict[str, object]:
        """Persist changed-condition evidence without emitting duplicate diagnostics."""
        identity = f"control-plane-diagnostic:{condition}"
        # Status must remain available during an outage even when another
        # operator records the same persistent condition concurrently.
        for _ in range(4):
            version, prior = self._store.read_state(self._profile, identity)
            now = self._clock()
            transition = not prior or prior.get("message") != message
            state = {
                "condition": condition, "message": message,
                "first_seen": now if transition else prior.get("first_seen"), "last_seen": now,
                "repeat_count": 1 if transition else int(prior.get("repeat_count", 0)) + 1,
            }
            try:
                self._store.commit(self._profile, identity, version, state)
                return state | {"transition": transition}
            except Exception as error:
                from alienintent.execution_coordination.ports.operational_store import VersionConflict
                if not isinstance(error, VersionConflict):
                    raise
        return {"condition": condition, "message": "work-management unavailable", "transition": False, "coalescing": "contended"}

    def explain(self, target: str) -> dict[str, object]:
        account = self._coordinator.guard_account(target)
        evidence = account.pop("evidence")
        account.pop("target", None)
        return {"target": target, "guard_outcomes": account, "evidence": evidence}

    def run(self, **fields: object) -> object:
        self._admit(fields)
        if not self._readiness():
            raise OperatorDenied("readiness gate failed; autonomous work was not started")
        return self._coordinator.start()

    def resume(self, **fields: object) -> object:
        self._admit(fields)
        self._coordinator.reconcile(str(fields["target"]))
        if not self._readiness():
            raise OperatorDenied("readiness gate failed; autonomous work was not started")
        return self._coordinator.start()

    def cancel(self, **fields: object) -> object:
        self._admit(fields)
        return self._coordinator.cancel(str(fields["target"]), str(fields["actor"]), str(fields["authority"]), int(fields["expected_version"]), str(fields["reason"]), str(fields["idempotency_key"]))

    def stop(self, **fields: object) -> object:
        self._admit(fields)
        return self._coordinator.stop_owned(str(fields["actor"]), str(fields["authority"]), int(fields["expected_version"]), str(fields["reason"]), str(fields["idempotency_key"]))

    def reconcile(self, **fields: object) -> object:
        self._admit(fields)
        return self._coordinator.reconcile(str(fields["target"]))

    def decisions_list(self) -> list[dict[str, object]]:
        return [asdict(value) for value in DecisionInbox(self._store, self._coordinator, self._profile).list_open()]

    def decisions_show(self, identity: str) -> dict[str, object]:
        value = DecisionInbox(self._store, self._coordinator, self._profile).show(identity)
        return asdict(value) if is_dataclass(value) else value

    def decisions_decide(self, identity: str, **fields: object) -> dict[str, object]:
        self._admit(fields)
        biu_version = fields.get("biu_version")
        if not isinstance(biu_version, int) or biu_version < 0:
            raise OperatorDenied("BIU version is required")
        _, state = self._store.read_state(self._profile, f"factory:{identity}")
        kernel_version = state.get("version")
        if not isinstance(kernel_version, int) or kernel_version < 0:
            raise OperatorDenied("decision target has no kernel version")
        record = DecisionInbox(self._store, self._coordinator, self._profile).submit(DecisionSubmission(str(fields["actor"]), str(fields["authority"]), identity, biu_version, kernel_version, str(fields["idempotency_key"]), str(fields["choice"])))
        return asdict(record)

    def _admit(self, fields: dict[str, object]) -> None:
        required = ("actor", "authority", "target", "intent", "reason", "idempotency_key")
        if any(not isinstance(fields.get(key), str) or not fields[key] for key in required):
            raise OperatorDenied("actor, authority, target, intent, reason and idempotency key are required")
        expected = fields.get("expected_version")
        if not isinstance(expected, int) or expected < 0:
            raise OperatorDenied("expected version is required")
        revision, state = self._store.read_state(self._profile, f"factory:{fields['target']}")
        prior = state.get("cancellation") if state else None
        if isinstance(prior, dict) and prior.get("idempotency_key") == fields["idempotency_key"]:
            return
        if state and revision != expected:
            raise OperatorDenied("stale expected version")
