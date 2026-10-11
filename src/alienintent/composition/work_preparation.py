"""Work Preparation: `prepare_next()` prepares, checks, registers, assesses and releases the next plan-derived Work Item
(WORK-PREPARATION-REFILL R3a; spec 3.3-3.5; WPR-A2).

From the live canonical plan tip (read fresh): select the next eligible obligation (none while a derived item is live);
check the obligation revision's budget; run the PREPARER (one bounded session given one context package); check its
packet deterministically before anything is written (`context_assembly.domain.preparation.check_packet` plus the fixed
closure actions and the mutations block); commit it to the packets branch (git plumbing on the configured packets
clone, pushed through the one ref publisher), register it, bind its identity, assess it with Agent Ready and, READY,
release it by inherited release. Typed outcomes, never the Decision Inbox: an Agent Ready CLARIFY gets one PREPARER
revision of the same item with the findings; a refused packet uses one run and is tried again on the next call; a
PREPARER CLARIFY or HOLD, an Agent Ready SPLIT or HOLD, a malformed answer or an exhausted budget STOPS the obligation
with its cause (R4 surfaces a stopped obligation as the READY-supply fault). A real SPLIT and a re-issue after a failed
execution are WORK-PREPARATION-REFILL R3b; here a SPLIT stops ("cannot safely split yet").
"""
from __future__ import annotations

from collections.abc import Callable, Collection
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tempfile

from alienintent.context_assembly.domain.obligation_state import IN_PROGRESS as STATE_IN_PROGRESS, next_obligation
from alienintent.context_assembly.domain.preparation import PENDING, check_packet
from alienintent.context_assembly.domain.work_contract import ContractInvalid, contract_block
from alienintent.context_assembly.ports.work_item_repository import PacketRef
from alienintent.execution_coordination.domain.closure import is_fixed
from alienintent.execution_coordination.domain.plan_authority import Obligation, PlanAuthority, PlanScope
from alienintent.execution_coordination.ports.operational_store import VersionConflict
from alienintent.invocation_runtime.domain.mutation_spec import MutationSpecInvalid, parse_mutations

# prepare_next's answers.
RELEASED, NOT_RELEASED, NOTHING, IN_PROGRESS = "released", "not-released", "nothing-eligible", "in-progress"
REFUSED, STOPPED = "refused", "stopped"
UNAVAILABLE, NO_AUTHORITY = "canonical-main-unavailable", "no-plan-authority"
# The PREPARER's answers.
PACKET, CLARIFY, HOLD = "PACKET", "CLARIFY", "HOLD"
# One budget per obligation revision: PREPARER runs (decisions sections 38-39, 50).
BUDGET = 3
PREPARED_DIRECTORY = "docs/work-units/prepared"
PREPARER_IDENTITY = {"GIT_AUTHOR_NAME": "AlienIntent Work Preparation",
                     "GIT_AUTHOR_EMAIL": "work-preparation@alienintent",
                     "GIT_COMMITTER_NAME": "AlienIntent Work Preparation",
                     "GIT_COMMITTER_EMAIL": "work-preparation@alienintent"}
# What the PREPARER is told a packet must hold (spec 3.3); the obligation and the plan come in the context package.
PACKET_FORMAT = (
    "One markdown packet: a title; a ```json alienintent-contract``` block (identity PENDING-REGISTRATION, "
    "release_policy automatic-on, authority_issuer plan-authority:<plan content_digest>, authority_references "
    "['<plan path> obligation:<LABEL>'], authorized_scope inside the obligation's allowed_paths and outside the "
    "protected paths, budget within the caps, required_closure_actions exactly candidate-published, merged-to-main, "
    "landing-record, board-updated, workspaces-cleaned); a ```json alienintent-acceptance``` block "
    "{\"satisfies\": [the obligation's acceptance ids this item completes]}; a ```json alienintent-proof``` block "
    "{\"targeted_tests\": [test files]}; "
    "optionally a ```json alienintent-mutations``` block; and the work, its acceptance checks and its proof in prose.")


@dataclass(frozen=True)
class PreparationResult:
    answer: str
    obligation: str | None = None
    identity: str | None = None
    detail: str = ""


def revision(obligation: Obligation) -> str:
    """The obligation revision: the digest of its plan entry; a changed entry is a new revision with a new budget."""
    return "sha256:" + sha256(json.dumps(asdict(obligation), sort_keys=True).encode()).hexdigest()


class WorkPreparation:
    def __init__(self, registry, preparer: Callable[[dict], dict], budget: int = BUDGET) -> None:
        """`registry` is the composed WorkRegistry; `preparer(context)` runs one PREPARER session and answers its
        result document ({"answer": PACKET|CLARIFY|HOLD, "packet": text, "reason": text})."""
        self.registry, self.preparer, self.budget = registry, preparer, budget
        self.store = registry.assessment.consumer.store

    # --- the budget record ----------------------------------------------------------------------------------------

    def _key(self, obligation: Obligation) -> str:
        return f"preparation:{obligation.label}:{revision(obligation)}"

    def _read(self, key: str) -> tuple[int, dict]:
        version, raw = self.store.read_state("registry", key)
        return version, dict(raw or {"runs": 0, "stopped": False, "cause": "", "identity": None, "latest": ""})

    def _write(self, key: str, version: int, record: dict) -> int:
        self.store.commit("registry", key, version, record)
        return version + 1

    def stopped(self, scope: PlanScope) -> frozenset[str]:
        """The obligations whose current revision Work Preparation stopped."""
        return frozenset(obligation.label for obligation in scope.obligations
                         if self._read(self._key(obligation))[1].get("stopped"))

    # --- prepare_next -----------------------------------------------------------------------------------------------

    def prepare_next(self) -> PreparationResult:
        authority = self.registry.plan_approval.current()
        if authority is None:
            return PreparationResult(UNAVAILABLE if getattr(self.registry, "canonical_main_unreadable", False)
                                     else NO_AUTHORITY)
        states = self.registry.obligation_states(authority, self.stopped(authority.scope))
        live = [state.label for state in states if state.status == STATE_IN_PROGRESS]
        if live:
            return PreparationResult(IN_PROGRESS, live[0])
        label = next_obligation(authority.scope, states)
        if label is None:
            return PreparationResult(NOTHING)
        obligation = authority.scope.obligation(label)
        key = self._key(obligation)
        version, record = self._read(key)
        findings: object = None
        revised = False
        while True:
            if record["runs"] >= self.budget:
                return self._stop(key, version, record, label, "budget-exhausted")
            record["runs"] += 1
            version = self._write(key, version, record)
            answer = self.preparer(self._context(authority, obligation, record, findings))
            kind = answer.get("answer") if isinstance(answer, dict) else None
            if kind in (CLARIFY, HOLD):
                return self._stop(key, version, record, label, f"preparer-{kind.lower()}: {answer.get('reason', '')}")
            text = answer.get("packet") if kind == PACKET else None
            if not isinstance(text, str):
                return self._stop(key, version, record, label, "preparer-answer-malformed")
            data = text.encode("utf-8")
            reasons = (*check_packet(data, authority, label), *self._composition_reasons(data))
            if reasons:
                record["latest"] = "; ".join(reasons)
                if record.get("identity"):  # a refused revision: the registered item stops with its obligation
                    return self._abandon(key, version, record, label, "revision-refused: " + record["latest"])
                self._write(key, version, record)
                return PreparationResult(REFUSED, label, None, "; ".join(reasons))
            try:
                identity, commit, bound = self._publish(label, revision(obligation), record, data)
            except Exception as error:  # noqa: BLE001 - the packets branch or registry failed: a typed stop
                return self._abandon(key, version, record, label,
                                     f"publication-failed: {type(error).__name__}: {error}")
            record["identity"] = identity
            version = self._write(key, version, record)
            try:
                assessed = self.registry.assessment.assess(identity, (bound, commit))
                disposition = getattr(assessed, "disposition", None)
                if disposition == "READY":
                    released = self.registry.release.release(identity)
                    if released.answer is not None:
                        return self._abandon(key, version, record, label, f"not-released: {released.answer}")
                    # The item is out of preparation: the obligation's next item is a new Work Item (its own
                    # identity and path); the runs stay with the obligation revision.
                    record.update(identity=None, path=None, items=[*record.get("items", []), identity])
                    self._write(key, version, record)
                    return PreparationResult(RELEASED, label, identity, released.detail or "")
                if disposition == "CLARIFY" and not revised:  # one PREPARER revision of the same item
                    findings, revised = self._findings(identity), True
                    continue
                cause = f"agent-ready-{(disposition or getattr(assessed, 'reason_code', 'hold')).lower()}"
            except Exception as error:  # noqa: BLE001 - a failure after registration stops the obligation
                # (never a live item that blocks every later preparation)
                cause = f"preparation-failed: {type(error).__name__}: {error}"
            return self._abandon(key, version, record, label, cause)

    def _abandon(self, key: str, version: int, record: dict, label: str, cause: str) -> PreparationResult:
        """A registered item that will not be released: retired (so it is never a live item blocking every later
        preparation) and its obligation STOPPED with the cause."""
        identity = record.get("identity")
        if identity:
            self.registry.identities.retire(identity)
        return self._stop(key, version, record, label, cause, identity)

    def _stop(self, key: str, version: int, record: dict, label: str, cause: str,
              identity: str | None = None) -> PreparationResult:
        record.update(stopped=True, cause=cause)
        self._write(key, version, record)
        return PreparationResult(STOPPED, label, identity or record.get("identity"), cause)

    def _context(self, authority: PlanAuthority, obligation: Obligation, record: dict, findings: object) -> dict:
        prior = [asdict(item) for item in self.registry.derived_items(authority.scope)
                 if item.obligation == obligation.label]
        return {"plan": {"path": authority.plan_path, "commit": authority.commit,
                         "content_digest": authority.content_digest},
                "obligation": asdict(obligation), "protected_paths": list(authority.scope.protected_paths),
                "budget_caps": dict(authority.scope.budget_caps), "prior_items": prior,
                "identity": PENDING, "work_item": record.get("identity"), "findings": findings,
                "budget": {"runs": record["runs"], "limit": self.budget}, "packet_format": PACKET_FORMAT}

    def _composition_reasons(self, data: bytes) -> tuple[str, ...]:
        reasons = []
        try:
            if not is_fixed(contract_block(data, PENDING).required_closure_actions):
                reasons.append("required_closure_actions: exactly the five fixed closure actions")
        except ContractInvalid:
            pass  # check_packet names it
        try:
            parse_mutations(data.decode("utf-8"))
        except MutationSpecInvalid as error:
            reasons.append(f"mutations: {error}")
        return tuple(reasons)

    def _findings(self, identity: str) -> object:
        """Agent Ready's retained answer for the item's current instructions, given to the PREPARER's revision."""
        history = self.registry.assessment.consumer.history(identity)
        return history[-1].get("outcome") if history else None

    # --- the packets branch -------------------------------------------------------------------------------------------

    def _publish(self, label: str, revision_digest: str, record: dict, data: bytes) -> tuple[str, str, bytes]:
        """Commit the packet (registered once; a revision moves the same item), bind its identity, push; answers
        (identity, bound commit, bound bytes)."""
        identity = record.get("identity")
        # Unique per obligation revision and run; a revision of the same item keeps its registered path.
        tag = f"{revision_digest.removeprefix('sha256:')[:8]}-{record['runs']}"
        path = record.get("path") or f"{PREPARED_DIRECTORY}/{label.lower()}-{tag}.md"
        record["path"] = path
        if identity is None:
            commit = self._commit(path, data, f"Prepare {label} (Work Preparation)")
            item = self.registry.records.register(data, self._repository(), path, commit, f"{label}-{tag}", "BIU",
                                                  None)
            if item.pointer is None or item.pointer.commit != commit:  # an existing row, never this packet
                raise RuntimeError(f"registration returned another item for {path}")
            identity = record["identity"] = item.id  # known at once: a failed bind still retires it
        bound = data.replace(PENDING.encode(), identity.encode())
        return identity, self._commit(path, bound, f"Bind {label} to work item {identity[:8]}"), bound

    def _repository(self) -> str:
        return self.registry.configuration.packets_repository

    def _commit(self, path: str, data: bytes, message: str) -> str:
        """One commit on the packets branch holding `data` at `path` on top of the remote branch tip (git plumbing in
        the configured packets clone, with a private index), pushed through the one ref publisher."""
        location = self.registry.configuration.repositories[self._repository()]
        clone, branch, remote = Path(location.clone), location.packets_branch, location.remote
        tip = "refs/alienintent/packets-tip"
        self._git(clone, {}, "fetch", "-q", remote, f"+refs/heads/{branch}:{tip}")
        parent = self._git(clone, {}, "rev-parse", "--verify", f"{tip}^{{commit}}")
        with tempfile.TemporaryDirectory() as folder:
            index = {"GIT_INDEX_FILE": os.path.join(folder, "index")}
            self._git(clone, index, "read-tree", parent)
            blob = self._git(clone, index, "hash-object", "-w", "--stdin", data=data)
            self._git(clone, index, "update-index", "--add", "--cacheinfo", f"100644,{blob},{path}")
            tree = self._git(clone, index, "write-tree")
            commit = self._git(clone, PREPARER_IDENTITY, "commit-tree", tree, "-p", parent, "-m", message)
        self.registry.publisher.publish(clone, remote, (PacketRef(f"refs/heads/{branch}", commit, False),))
        # The clone's own packets branch retains the commit for registration (only a fast-forward, never a rewrite).
        local = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}^{{commit}}"],
                               cwd=clone, capture_output=True, check=False, timeout=60).stdout.decode().strip()
        if local and local != parent and subprocess.run(["git", "merge-base", "--is-ancestor", local, commit],
                                                         cwd=clone, capture_output=True, timeout=60).returncode:
            raise RuntimeError(f"the local {branch} holds commits the remote packets branch lacks")
        self._git(clone, {}, "update-ref", f"refs/heads/{branch}", commit, *((local,) if local else ()))
        return commit

    @staticmethod
    def _git(clone: Path, extra: dict, *args: str, data: bytes | None = None) -> str:
        result = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=clone, input=data,
                                capture_output=True, check=False, timeout=300, env=os.environ | extra)
        if result.returncode:
            raise RuntimeError(f"git {args[0]} failed: {result.stderr.decode(errors='replace').strip()[:200]}")
        return result.stdout.decode().strip()


# --- the production PREPARER session ---------------------------------------------------------------------------------

PREPARER_ROLE, PREPARATION_RESULT = "PREPARER", "preparation.json"
PREPARER_WALL_CLOCK = 1800
RESULT_LIMIT = 1 << 20
PREPARER_INSTRUCTIONS = """You are the PREPARER for AlienIntent Work Preparation. Your current working directory is a
read-only clone of current canonical main. Prepare exactly one bounded Work Item for the obligation in the context
package below, from the plan's intent and acceptance only: never invent intent, broaden authority, touch a protected
path, change priority or dependencies, weaken acceptance or resolve an owner ambiguity. Use the supplied context first;
inspect only the files and tests the obligation's paths and acceptance name (no broad repository exploration).

When the context names `findings`, revise the packet for the same Work Item with them. When the context names
`prior_items`, do not repeat work they already did.

Write exactly one JSON file to this path and nothing else:
{result}
with either {{"answer": "PACKET", "packet": "<the whole packet markdown>"}} or
{{"answer": "CLARIFY" or "HOLD", "reason": "<the missing information, named>"}}.

Packet format: {packet_format}

Context package:
{context}
"""


class WorkerPreparer:
    """One PREPARER session (WORK-PREPARATION-REFILL R3a): a fresh clone of current canonical main, the provider command
    of the `PREPARER` route with the instructions on standard input, run as the worker user when one is configured (as
    every role is), and the result document read back from the worker's own results folder by a checked descriptor;
    the clone is cleaned up. Any failure answers a typed HOLD, so Work Preparation stops the obligation as a fault."""

    def __init__(self, registry) -> None:
        self.registry = registry

    def __call__(self, context: dict) -> dict:
        from uuid import uuid4
        from alienintent.composition import work_registry as composed
        from alienintent.composition.model_routing import provider_command, resolve_route
        configuration = self.registry.configuration
        name = configuration.packets_repository
        main = self.registry._canonical_main(name)
        if main is None:
            return {"answer": HOLD, "reason": "canonical main could not be fetched"}
        invocation = f"prepare-{uuid4().hex}"
        root, user = composed.launch_root(configuration), configuration.worker_user
        try:
            route = resolve_route(PREPARER_ROLE)
            if user is None:
                return self._local(context, invocation, main, root, route, provider_command)
            return self._as_worker(context, invocation, main, root, user, route, provider_command, composed)
        except Exception as error:  # noqa: BLE001 - a session that could not run is a typed hold, never a crash
            return {"answer": HOLD, "reason": f"the PREPARER session failed: {type(error).__name__}: {error}"}

    @staticmethod
    def _instructions(context: dict, result: Path) -> bytes:
        return PREPARER_INSTRUCTIONS.format(result=result, packet_format=PACKET_FORMAT,
                                            context=json.dumps(context, indent=1, sort_keys=True)).encode()

    def _as_worker(self, context, invocation, main, root, user, route, provider_command, composed) -> dict:
        from alienintent.invocation_runtime.adapters.cli_worker import run_as_worker
        from alienintent.invocation_runtime.adapters.git_source_control import open_worker_file, read_descriptor
        from alienintent.invocation_runtime.adapters.git_worktree import WorkerCloneAdapter
        from alienintent.composition.sandbox_run_profile import worker_environment
        packets = self.registry.configuration.repositories[self.registry.configuration.packets_repository]
        worker_root, results = root / "worker", root / "results"
        environment = worker_environment(root) | {"HOME": str(worker_root / "home"), "TMPDIR": str(worker_root / "tmp"),
                                                  "CODEX_HOME": str(worker_root / "auth" / "codex"),
                                                  "USER": user, "LOGNAME": user}
        if route.get("provider") != composed.WORKER_PROVIDER:
            return {"answer": HOLD, "reason": f"worker provider unsupported: {route.get('provider')}"}
        if not composed.worker_login_present(user, environment, Path(environment["CODEX_HOME"])):
            return {"answer": HOLD, "reason": "worker provider login missing"}
        clones = WorkerCloneAdapter(Path(packets.clone), worker_root, results, user, environment)
        workspace = clones.allocate(invocation, f"preparation:{invocation}", main)
        try:
            composed.prepare_worker_session(user, environment, Path(packets.clone), root / "intake.git")
            result = results / invocation / PREPARATION_RESULT
            run_as_worker(user, environment, provider_command(route, workspace.path), cwd=workspace.path,
                          input=self._instructions(context, result), timeout=PREPARER_WALL_CLOCK)
            descriptor = open_worker_file(result, composed.worker_uid(user))
            try:
                return self._answer(read_descriptor(descriptor, RESULT_LIMIT))
            finally:
                os.close(descriptor)
        finally:
            clones.cleanup(workspace, None)

    def _local(self, context, invocation, main, root, route, provider_command) -> dict:
        """No worker user (a development profile): the same session as the operator, in a detached worktree."""
        packets = self.registry.configuration.repositories[self.registry.configuration.packets_repository]
        workspace, result = root / "preparation" / invocation, root / "preparation" / f"{invocation}.json"
        workspace.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "worktree", "add", "-q", "--detach", str(workspace), main], cwd=packets.clone,
                       check=True, capture_output=True, timeout=300)
        try:
            subprocess.run(provider_command(route, workspace), cwd=workspace, input=self._instructions(context, result),
                           capture_output=True, check=False, timeout=PREPARER_WALL_CLOCK)
            if result.stat().st_size > RESULT_LIMIT:  # checked before reading: never read whole
                return {"answer": HOLD, "reason": f"the PREPARER's result is over the {RESULT_LIMIT}-byte limit"}
            with result.open("rb") as handle:
                return self._answer(handle.read(RESULT_LIMIT))
        finally:
            result.unlink(missing_ok=True)
            subprocess.run(["git", "worktree", "remove", "--force", str(workspace)], cwd=packets.clone,
                           capture_output=True, check=False, timeout=300)

    @staticmethod
    def _answer(data: bytes) -> dict:
        try:
            document = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return {"answer": HOLD, "reason": "the PREPARER's result is not JSON"}
        if not isinstance(document, dict):
            return {"answer": HOLD, "reason": "the PREPARER's result is not an object"}
        return document
