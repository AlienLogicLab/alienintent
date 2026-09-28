#!/usr/bin/env python3
"""FX-B3 / FX-B4 — canonical live release admission proof (WO-220506, Issue #126).

Phase 1 (``--target sandbox``, FX-B3) runs against ``AlienLogicLab/alienintent-sandbox`` /
Project #2; phase 2 (``--target production``, the fixture WO-220506.md names "FX-B4" — not DAG
node B4's own FX-B4, WO-220507) runs against the real ``AlienLogicLab/alienintent`` / Project #1
prelaunch boundary. Both drive the pinned case sequence (WO-220506.md "FX-B3 fixture", "Phase 2
target binding and fixture pin" and "FX-B3/FX-B4 canonical precondition re-pin") through the
production composition root ``GitHubProfileComposition``, whose ``FactoryCoordinator._run`` checks
``ReleasePreconditionGate`` then ``admit_release`` before any launch.

What is real: the profile and its Project, read fresh from GitHub for every admission pass through
a paginated reader; the operational store; the release gate over a fresh clone of the target
repository; the budget allocation; the K3 ``RoleBindingGuard``; and ``RealWorkerProvider`` with
its durable ``JsonlInvocationJournal`` and ``GitWorktreeAdapter``. What is doubled: only the
worker *process* (the S0 ``ScriptedWorkerProcess``), scripted to ``authority-block`` so no
candidate is committed or published and no provider runs. The clone's push URL is disabled too.

Writes are limited to the fixture's own Project draft items: create, set Priority/Status READY,
delete. Lifecycle projection is recorded locally and never written to the board. Every GraphQL
mutation is logged and must name only an item this run created. Every other item on the target
Project (and, in phase 1, on production Project #1, read-only) is digested before and after.

    python3 tools/live/fx_b3_release_admission_proof.py --target sandbox --out DIR
    python3 tools/live/fx_b3_release_admission_proof.py --target production --out DIR
    python3 tools/live/fx_b3_release_admission_proof.py --cleanup-ledger DIR/ledger.json   # recovery only

Exit 0 only when every case matches its pinned expectation, the launch total is exact, no provider
ran, every mutation stayed on the run's own items, cleanup is verified and non-interference holds.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
import re
import secrets as _secrets
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Callable, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[2]
for entry in (ROOT / "src", ROOT / "tools" / "live"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from alienintent.composition.github_profile import GitHubProfileComposition  # noqa: E402
from alienintent.composition.release_admission import ReleaseAdmissionConfig  # noqa: E402
from alienintent.composition.role_binding import ROLE_OPERATIONS  # noqa: E402
from alienintent.composition.sandbox_profile import compose_profile, compose_secrets  # noqa: E402
from alienintent.composition.sandbox_run_profile import contract_from_document, descriptor_from_body  # noqa: E402
import alienintent.execution_coordination.application.factory_coordinator as factory_coordinator  # noqa: E402
from alienintent.execution_coordination.adapters.github_projects_v2 import GitHubProjectsV2Directory  # noqa: E402
from alienintent.execution_coordination.domain.contract import BiuContract  # noqa: E402
from alienintent.execution_coordination.domain.release import ReleaseAuthorization, ReleasePreconditionRefused, UNAUTHORIZED_WORDING  # noqa: E402
from alienintent.execution_coordination.ports.worker_provider import PRODUCER, WorkerInvocation  # noqa: E402
from alienintent.installation.domain.project_identity import ProjectAddress  # noqa: E402
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl  # noqa: E402
from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter, ref_safe  # noqa: E402
from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal, journal_records  # noqa: E402
from alienintent.invocation_runtime.adapters.scripted_worker import ScriptedWorkerProcess  # noqa: E402
from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider  # noqa: E402
from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole, ReservationBook  # noqa: E402

WORK_UNIT, ISSUE = "WO-220506", 126
PRODUCTION_PROFILE = Path.home() / ".config/alienintent/self-hosting.json"
PRODUCTION_PROJECT_ID = "PVT_kwDOEcrpC84Bj5i_"
PRODUCTION_STATUS_FIELD = "PVTSSF_lADOEcrpC84Bj5i_zhisMnY"
PRODUCTION_PRIORITY_FIELD = "PVTSSF_lADOEcrpC84Bj5i_zhiy9vQ"
SANDBOX_PROJECT_ID = "PVT_kwDOEcrpC84BkIEX"
RELEASE_POINT = "origin/main"
NULL_REVISION = "0" * 40
ABSENT_REVISION = "b" * 40
DENIAL = "Implementation is **not** authorized by this Issue. Release remains an explicit authority step."
ABSENT_CAPABILITY = "fx-b3-absent-capability"
UNALLOCATED_DIMENSION = "fx-b3-unallocated-dimension"
VALID_BUDGET = {"hard_required_dimensions": ["attempts"], "maximum_attempts": 1, "hard_wall_clock_seconds": 60,
                "retry_limit": 0, "cancellation_limit": 1}
VALID_ALLOCATION = {"attempts": 1, "wall-clock": 60, "cancellation": 1}
PRODUCTION_ISOLATION = "production Project #1 read-only before/after (phase 1 compensating control)"


# --- the pinned cases ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Case:
    """One pinned step: its seeding and the refusal (or admission) it must produce.

    ``refused_by`` names the check that must refuse, in the form this fixture observes it:
    ``gate:<ReleasePreconditionGate check>``, ``admit_release:<ValueError message>`` or
    ``eligibility:<FactoryCoordinator eligibility reason>``; ``None`` means admitted and launched.
    """

    name: str
    step: str
    criterion: str
    expected_starts: int
    refused_by: str | None
    suffix: str
    contract: Mapping[str, object] = field(default_factory=dict)
    record: Mapping[str, object] | None = field(default_factory=dict)
    allocation: Mapping[str, int] | None = field(default_factory=lambda: dict(VALID_ALLOCATION))
    stale_digest: bool = False
    automatic_release: bool = True
    explicit_release: bool = False
    replay_of: str | None = None
    phase1_only: bool = False


CASES: tuple[Case, ...] = (
    Case("02-positive-control", "step 2", "every precondition, eligibility and allocation holds: admit and launch exactly once",
         1, None, "POS"),
    Case("03-identity-replay", "step 3", "re-attempt admission for the step-2 identity", 0, "eligibility:authority-block",
         "POS", replay_of="02-positive-control"),
    Case("04-policy-source-mismatch", "step 4", "automatic-on contract released by an explicit human source", 0,
         "admit_release:automatic-on release requires attributable policy authorization", "POLICY",
         automatic_release=False, explicit_release=True),
    Case("05-readiness-digest-mismatch", "step 5", "Project readiness digest is not the contract digest", 0,
         "admit_release:stale readiness reference", "DIGEST", stale_digest=True),
    Case("06-unsatisfied-dependency", "step 6", "dependency on work that is not DONE", 0, "eligibility:dependencies-incomplete",
         "DEP", contract={"dependencies": ["{prefix}-ABSENT-DEPENDENCY"]}),
    Case("07-missing-capability", "step 7", "required capability absent from the admitted set", 0,
         "admit_release:missing required capability", "CAP", contract={"required_capabilities": ["python", ABSENT_CAPABILITY]}),
    Case("08-missing-budget-dimension", "step 8 (re-pinned)", "allocation lacks one hard-required dimension", 0,
         "admit_release:absent hard-required budget dimension", "BUDGET",
         contract={"budget_policy": VALID_BUDGET | {"hard_required_dimensions": ["attempts", UNALLOCATED_DIMENSION]}}),
    Case("E1-eligibility-not-released", "'plus eligibility'", "explicit-release profile, never released", 0,
         "eligibility:not-released", "UNRELEASED", automatic_release=False),
    Case("09-no-release-record", "step 9", "no durable release record", 0, "gate:implementation-authorized", "NORECORD",
         record=None),
    Case("10-record-does-not-authorize", "step 10", "record does not authorize IMPLEMENT", 0,
         "gate:implementation-authorized", "NOAUTH", record={"authorizes_implement": False}),
    Case("11-no-exact-baseline", "step 11", "record names a symbolic baseline", 0, "gate:baseline-named", "NOBASE",
         record={"baseline": "main"}),
    Case("12a-null-baseline", "step 12", "baseline is the null revision", 0, "gate:baseline-resolves", "NULLBASE",
         record={"baseline": NULL_REVISION}),
    Case("12b-absent-baseline", "step 12", "baseline is well formed but absent", 0, "gate:baseline-resolves", "ABSENTBASE",
         record={"baseline": ABSENT_REVISION}),
    Case("13-unreachable-baseline", "step 13", "baseline is a local-only commit the release point cannot reach", 0,
         "gate:baseline-reachable", "DIVERGED", record={"baseline": "<diverged>"}),
    Case("14-unsuperseded-denial", "step 14", "denial wording with no superseding record, all else valid", 0,
         "gate:authority-wording-consistent", "DENIAL", contract={"intent": DENIAL, "authority_references": [DENIAL]}),
    Case("C1-superseded-denial-contrast", "step 14 contrast (informative)", "the same wording with a superseding record admits",
         1, None, "SUPERSEDED", contract={"intent": DENIAL, "authority_references": [DENIAL]},
         record={"superseding_record": "{record_ref}:superseding"}, phase1_only=True),
)


def cases_for(phase: int) -> tuple[Case, ...]:
    """Phase 2 omits the informative contrast: Project #1 gets exactly one positive launch."""
    return tuple(case for case in CASES if phase == 1 or not case.phase1_only)


# --- targets --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Target:
    name: str
    fixture: str
    phase: int
    document: Mapping[str, object]

    @property
    def repository(self) -> str:
        return str(self.document["repository"])

    @property
    def prefix(self) -> str:
        return f"{self.fixture}-PROBE"

    def address(self) -> ProjectAddress:
        owner = self.repository.split("/", 1)[0]
        return ProjectAddress(str(self.document["project_reference"]), int(self.document["project_number"]), owner,
                              str(self.document["project_status_field"]), str(self.document["project_priority_field"]))


def production_document(path: Path = PRODUCTION_PROFILE) -> dict:
    """The Python profile document for the real Project #1, read from the running factory's own profile."""
    hosting = json.loads(path.read_text(encoding="utf-8"))
    repository = f"{hosting['repository']['owner']}/{hosting['repository']['name']}"
    project = hosting["project"]
    if repository != "AlienLogicLab/alienintent" or project.get("owner") != "AlienLogicLab" or int(project.get("number") or 0) != 1:
        raise SystemExit("the production profile no longer names AlienLogicLab/alienintent Project #1; refusing to guess")
    return {
        "profile": "alienintent-self-hosting", "repository": repository,
        "project_reference": PRODUCTION_PROJECT_ID, "project_number": 1,
        "project_status_field": PRODUCTION_STATUS_FIELD, "project_priority_field": PRODUCTION_PRIORITY_FIELD,
        "lifecycle_statuses": {"READY": "READY"},
        "projection_fields": {state: "Status" for state in ("IMPLEMENT", "VERIFY", "REVIEW", "ACCEPT", "DONE")},
        "webhook_secret_reference": "alienintent-webhook",
        "secret_references": {"alienintent-webhook": hosting["webhook"]["secretFile"]},
        "automatic_release": True, "githubApp": dict(hosting["githubApp"]),
    }


def sandbox_document() -> dict:
    import py10_sandbox
    document = py10_sandbox.document()
    if document.get("project_reference") != SANDBOX_PROJECT_ID or document.get("repository") != "AlienLogicLab/alienintent-sandbox":
        raise SystemExit("the sandbox profile no longer names alienintent-sandbox Project #2; refusing to guess")
    return document


def target(name: str) -> Target:
    if name == "sandbox":
        return Target("sandbox", "FX-B3", 1, sandbox_document())
    if name == "production":
        return Target("production", "FX-B4", 2, production_document())
    raise SystemExit(f"unknown target {name!r}")


# --- boards ---------------------------------------------------------------------------------------

_FIELD = "field{ ... on ProjectV2FieldCommon{ name } }"
BOARD_QUERY = f"""query($project:ID!,$cursor:String,$detailed:Boolean!){{ node(id:$project){{ ... on ProjectV2 {{ id number
 items(first:50, after:$cursor){{ pageInfo{{ hasNextPage endCursor }} nodes{{ id type isArchived updatedAt
  content{{ __typename
   ... on DraftIssue{{ id title body updatedAt }}
   ... on Issue{{ id number title body state updatedAt closedAt
     labels(first:50) @include(if:$detailed){{ nodes{{ name }} }}
     assignees(first:20) @include(if:$detailed){{ nodes{{ login }} }}
     comments(last:100) @include(if:$detailed){{ totalCount nodes{{ id updatedAt body }} }} }} }}
  fieldValues(first:30){{ nodes{{ __typename
   ... on ProjectV2ItemFieldSingleSelectValue{{ name updatedAt {_FIELD} }}
   ... on ProjectV2ItemFieldTextValue{{ text updatedAt {_FIELD} }}
   ... on ProjectV2ItemFieldNumberValue{{ number updatedAt {_FIELD} }}
   ... on ProjectV2ItemFieldDateValue{{ date updatedAt {_FIELD} }}
   ... on ProjectV2ItemFieldIterationValue{{ title updatedAt {_FIELD} }} }} }} }} }} }} }} }}"""

_MUTATION_NAME = re.compile(r"\{\s*(\w+)\s*\(")


def sha256(text: str | bytes | None) -> str | None:
    if text is None:
        return None
    return "sha256:" + hashlib.sha256(text.encode("utf-8") if isinstance(text, str) else text).hexdigest()


def normalize_item(node: Mapping[str, object]) -> dict:
    """One Project item as comparable facts; bodies are digested, never retained."""
    content = node.get("content") or {}
    fields: dict[str, dict] = {}
    for value in ((node.get("fieldValues") or {}).get("nodes") or []):
        if not isinstance(value, Mapping) or not isinstance(value.get("field"), Mapping):
            continue
        name = value["field"].get("name")
        observed = next((value[key] for key in ("name", "text", "number", "date", "title") if key in value), None)
        if isinstance(name, str):
            fields[name] = {"value": observed, "updatedAt": value.get("updatedAt")}
    normalized_content = {
        "typename": content.get("__typename"), "id": content.get("id"), "number": content.get("number"),
        "title": content.get("title"), "body_sha256": sha256(content.get("body")), "state": content.get("state"),
        "updatedAt": content.get("updatedAt"), "closedAt": content.get("closedAt"),
    }
    if "labels" in content:
        normalized_content["labels"] = sorted(label["name"] for label in (content["labels"] or {}).get("nodes") or [])
    if "assignees" in content:
        normalized_content["assignees"] = sorted(user["login"] for user in (content["assignees"] or {}).get("nodes") or [])
    if "comments" in content:
        comments = content["comments"] or {}
        normalized_content["comments"] = {
            "totalCount": comments.get("totalCount"),
            "last": [{"id": entry.get("id"), "updatedAt": entry.get("updatedAt"), "body_sha256": sha256(entry.get("body"))}
                     for entry in comments.get("nodes") or []],
        }
    return {"id": node.get("id"), "type": node.get("type"), "isArchived": node.get("isArchived"),
            "updatedAt": node.get("updatedAt"), "content": normalized_content, "fields": fields,
            "_body": content.get("body")}


def item_digest(item: Mapping[str, object]) -> str:
    public = {key: value for key, value in item.items() if not key.startswith("_")}
    return sha256(json.dumps(public, sort_keys=True, separators=(",", ":")))  # type: ignore[return-value]


def board_digest(items: Iterable[Mapping[str, object]], exclude: Iterable[str] = ()) -> dict:
    excluded = set(exclude)
    return {str(item["id"]): {"digest": item_digest(item), "item": {k: v for k, v in item.items() if not k.startswith("_")}}
            for item in items if item["id"] not in excluded}


def board_diff(before: Mapping[str, Mapping], after: Mapping[str, Mapping]) -> dict:
    """Every item added, removed or changed between two digests of the same board."""
    changed = []
    for identity in sorted(set(before) & set(after)):
        if before[identity]["digest"] != after[identity]["digest"]:
            left, right = before[identity]["item"], after[identity]["item"]
            keys = sorted(key for key in set(left) | set(right) if left.get(key) != right.get(key))
            changed.append({"id": identity, "keys": keys, "before": {k: left.get(k) for k in keys}, "after": {k: right.get(k) for k in keys}})
    return {"added": sorted(set(after) - set(before)), "removed": sorted(set(before) - set(after)), "changed": changed,
            "items_before": len(before), "items_after": len(after),
            "unchanged": not (set(after) ^ set(before)) and not changed}


class RecordingTransport:
    """Pass every call through; retain each GraphQL mutation's operation and addressed identities."""

    def __init__(self, inner: object) -> None:
        self._inner = inner
        self.mutations: list[dict] = []
        self.reads = 0

    def request(self, method: str, url: str, headers: Mapping[str, str], body: bytes | None = None):
        document = json.loads(body) if body else {}
        query = str(document.get("query") or "")
        if query.lstrip().startswith("mutation"):
            match = _MUTATION_NAME.search(query)
            variables = document.get("variables") or {}
            self.mutations.append({"at": _now(), "operation": match.group(1) if match else "unknown",
                                   "project": variables.get("project"), "item": variables.get("item"),
                                   "field": variables.get("field"), "title": variables.get("title")})
        else:
            self.reads += 1
        return self._inner.request(method, url, headers, body)  # type: ignore[attr-defined]


class LiveBoard:
    """The configured Project through the product directory, plus a paginated reader for full observation."""

    def __init__(self, address: ProjectAddress, transport: RecordingTransport, authorization: Callable[[], Mapping[str, str]]) -> None:
        import py10_sandbox
        self.address, self.transport, self._authorization = address, transport, authorization
        self.directory = GitHubProjectsV2Directory(address, transport, authorization)
        self.writer = py10_sandbox.SeedWriter(address, transport, authorization)

    def _graphql(self, query: str, variables: Mapping[str, object]) -> Mapping[str, object]:
        body = json.dumps({"query": query, "variables": dict(variables)}).encode("utf-8")
        response = self.transport.request("POST", "https://api.github.com/graphql",
                                          dict(self._authorization()) | {"Content-Type": "application/json"}, body)
        document = json.loads(response.body or b"{}")
        if response.status != 200 or document.get("errors"):
            raise RuntimeError(f"Projects v2 read failed: HTTP {response.status} {str(document.get('errors'))[:300]}")
        return document["data"]

    def read_items(self, detailed: bool = False) -> list[dict]:
        items, cursor = [], None
        while True:
            node = self._graphql(BOARD_QUERY, {"project": self.address.project_id, "cursor": cursor, "detailed": detailed})["node"]
            self.address.resolve(node.get("id"), node.get("number"))
            page = node["items"]
            items.extend(normalize_item(entry) for entry in page["nodes"] if isinstance(entry, Mapping))
            if not page["pageInfo"]["hasNextPage"]:
                return items
            cursor = page["pageInfo"]["endCursor"]

    def schema_statuses(self) -> tuple[str, ...]:
        return tuple(self.directory.schema().status_options)

    def create(self, title: str, body: str) -> str:
        return self.directory.add_draft_item(title, body)

    def make_ready(self, item: str) -> None:
        self.writer.set_field(item, "Priority", "P5")
        if self.directory.write_status(item, "READY", 0) != 0:
            raise RuntimeError(f"Status READY did not read back for {item}")

    def read_back(self, item: str) -> dict:
        state = self.directory.read_status(item)
        return {"item": state.item_id, "status": state.status, "priority": state.priority, "title": state.title,
                "body_sha256": sha256(state.body), "status_updated_at": state.status_updated_at}

    def delete(self, item: str) -> str:
        return self.directory.delete_item(item)

    def absent(self, item: str) -> bool:
        try:
            self.directory.read_status(item)
        except Exception:  # noqa: BLE001 - an unreadable deleted item is the expected answer
            return True
        return False


# --- probes and contracts -------------------------------------------------------------------------


def probe_identity(prefix: str, launch: str, suffix: str) -> str:
    return f"{prefix}-{launch}-{suffix}"


def probe_title(identity: str) -> str:
    return f"{identity} — release-admission proof scaffolding, safe to close, do not act"


def contract_document(identity: str, target_: Target, overrides: Mapping[str, object], prefix: str) -> dict:
    document = {
        "identity": identity, "version": "1",
        "intent": f"{target_.fixture} release-admission fixture probe for {WORK_UNIT} (Issue #{ISSUE}); never executed.",
        "satisfied_requirement_ids": ["SF-REQ-015", "SF-REQ-051"], "fixed_decisions": [target_.fixture],
        "authorized_scope": ["none: fixture scaffolding"], "excluded_scope": ["everything"], "dependencies": [],
        "required_capabilities": ["python"], "budget_policy": dict(VALID_BUDGET), "retry_policy": "no-retry",
        "completion_criteria": ["none"], "verification_obligations": ["none"], "required_evidence": ["artifact-verified"],
        "non_goals": ["everything"], "candidate_custody_requirements": ["none"], "release_policy": "automatic-on",
        "authority_issuer": f"{target_.fixture} fixture ({WORK_UNIT})", "authority_references": [WORK_UNIT, f"AlienLogicLab/alienintent#{ISSUE}"],
        "target_repositories": [target_.repository], "baselines": [RELEASE_POINT], "required_closure_actions": ["none"],
        "stop_escalation_conditions": ["any"],
    }
    for key, value in overrides.items():
        document[key] = [entry.replace("{prefix}", prefix) for entry in value] if key == "dependencies" else value
    return document


def probe_body(identity: str, contract: BiuContract, digest: str, launch: str, fixture: str) -> str:
    return "\n".join([
        f"biu: {identity}",
        f"contract: fixture/{identity}.json",
        f"readiness_digest: {digest}",
        f"depends_on: {', '.join(contract.dependencies)}",
        "",
        f"{fixture} release-admission fixture item for {WORK_UNIT} (Issue #{ISSUE}), Director-authorized",
        f"scaffolding, not a BIU and not work. Created and deleted within fixture run {launch}. Do not act on it.",
    ])


def launch_id() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + _secrets.token_hex(2)


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


# --- checkout -------------------------------------------------------------------------------------


def git(checkout: Path, *arguments: str, environment: Mapping[str, str] | None = None) -> str:
    return subprocess.run(["git", *arguments], cwd=checkout, env=None if environment is None else dict(environment),
                          capture_output=True, text=True, check=True).stdout.strip()


def prepare_checkout(root: Path, url: str, environment: Mapping[str, str] | None) -> dict:
    """A fresh clone of the target; pushes are disabled and the diverged baseline is a local-only object."""
    checkout = root / "checkout"
    subprocess.run(["git", "clone", "--quiet", "--no-tags", url, str(checkout)], env=None if environment is None else dict(environment),
                   capture_output=True, text=True, check=True)
    disabled = root / "push-disabled.invalid"
    git(checkout, "remote", "set-url", "--push", "origin", str(disabled))
    release_point = git(checkout, "rev-parse", "--verify", f"{RELEASE_POINT}^{{commit}}")
    identity = {"GIT_AUTHOR_NAME": "fx-b3", "GIT_AUTHOR_EMAIL": "fx-b3@example.invalid",
                "GIT_COMMITTER_NAME": "fx-b3", "GIT_COMMITTER_EMAIL": "fx-b3@example.invalid"}
    diverged = git(checkout, "commit-tree", f"{release_point}^{{tree}}", "-p", release_point, "-m",
                   f"{WORK_UNIT} fixture: local-only diverged commit, never pushed", environment=dict(os.environ) | identity)
    return {"path": checkout, "url": url, "release_point": RELEASE_POINT, "release_point_revision": release_point,
            "baseline": release_point, "diverged": diverged, "push_url": str(disabled)}


# --- one case -------------------------------------------------------------------------------------


class AdmissionObserver:
    """Observation-only wrappers at the call site: each delegates unchanged and records its answer."""

    def __init__(self) -> None:
        self.admit: list[dict] = []
        self.gate: list[dict] = []
        self._original = factory_coordinator.admit_release

    def __enter__(self) -> "AdmissionObserver":
        original = self._original

        def observed(existing, request):
            try:
                admitted = original(existing, request)
            except ValueError as error:
                self.admit.append({"identity": request.identity, "result": "refused", "reason": str(error)})
                raise
            self.admit.append({"identity": request.identity, "result": "admitted", "reason": None})
            return admitted

        factory_coordinator.admit_release = observed
        return self

    def __exit__(self, *_: object) -> None:
        factory_coordinator.admit_release = self._original

    def watch(self, gate: object) -> None:
        check = gate.check  # type: ignore[attr-defined]

        def observed(item):
            try:
                check(item)
            except ReleasePreconditionRefused as refusal:
                self.gate.append({"identity": item.identity, "result": "refused", "check": refusal.check})
                raise
            self.gate.append({"identity": item.identity, "result": "passed", "check": None})

        gate.check = observed  # type: ignore[attr-defined]


def refused_by(identity: str, gate_log: list[dict], admit_log: list[dict], imported: bool, reason: str | None) -> str | None:
    """Which check refused this identity, from observed answers only."""
    gate = [entry for entry in gate_log if entry["identity"] == identity]
    admit = [entry for entry in admit_log if entry["identity"] == identity]
    if any(entry["result"] == "refused" for entry in gate):
        return "gate:" + next(entry["check"] for entry in gate if entry["result"] == "refused")
    if any(entry["result"] == "refused" for entry in admit):
        return "admit_release:" + next(entry["reason"] for entry in admit if entry["result"] == "refused")
    if not gate and not admit and imported and reason:
        return f"eligibility:{reason}"
    return None


@dataclass
class RunContext:
    target: Target
    board: object
    launch: str
    root: Path
    checkout: dict
    contracts: dict[str, BiuContract]
    items: dict[str, str]
    snapshot_calls: list[dict] = field(default_factory=list)

    def rows(self, identities: Iterable[str]) -> tuple[dict, ...]:
        """A fresh read of the Project, restricted to this run's own probe items (blast-radius control)."""
        wanted = {self.items[identity]: identity for identity in identities}
        observed = [item for item in self.board.read_items() if item["id"] in wanted]  # type: ignore[attr-defined]
        rows = []
        for item in sorted(observed, key=lambda entry: ((entry["fields"].get("Status") or {}).get("updatedAt") or "", entry["id"])):
            status = (item["fields"].get("Status") or {}).get("value")
            if status != "READY":
                continue
            descriptor = descriptor_from_body(item["_body"])
            if descriptor.identity != wanted[item["id"]] or not str(item["content"]["title"]).startswith(self.target.prefix):
                raise RuntimeError("a probe item no longer carries its own descriptor; refusing to import it")
            rows.append({
                "identity": descriptor.identity, "repository": self.target.repository, "membership": True, "complete": True,
                "status": status, "priority": (item["fields"].get("Priority") or {}).get("value"),
                "dependencies": list(descriptor.dependencies), "contract": descriptor.contract_path,
                "contract_digest": descriptor.readiness_digest,
                "readiness": f"project-item {item['id']} READY at {(item['fields'].get('Status') or {}).get('updatedAt') or 'unrecorded'}",
                "wave": "2", "source_version": self.target.address().project_id,
            })
        self.snapshot_calls.append({"at": _now(), "identities": [row["identity"] for row in rows]})
        return tuple(rows)

    def contract_for(self, row: Mapping[str, object]) -> BiuContract:
        contract = self.contracts[str(row.get("identity"))]
        if tuple(contract.dependencies) != tuple(row.get("dependencies") or ()):
            raise RuntimeError("upstream dependency edges disagree with the fixture contract")
        return contract


class Composed:
    """One case's production composition over its own fresh store and journal."""

    def __init__(self, context: RunContext, case: Case, identity: str) -> None:
        root = context.root / "cases" / case.name
        root.mkdir(parents=True, exist_ok=True)
        self.root, self.identity = root, identity
        document = dict(context.target.document) | {"automatic_release": case.automatic_release}
        profile = compose_profile(document)
        self.journal_path, self.process_path = root / "invocation-journal.jsonl", root / "process-journal.jsonl"
        journal = JsonlInvocationJournal(self.journal_path, time.time)
        environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(root), "LANG": "C.UTF-8",
                       "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0"}
        process = ScriptedWorkerProcess({identity: ["authority-block"]}, {}, time.time, self.process_path, environment)
        repository = context.target.repository

        def grant(invocation: WorkerInvocation) -> CapabilityGrant:
            return CapabilityGrant(f"{context.target.fixture}-{invocation.work_identity}", "1", invocation.correlation_id,
                                   InvocationRole.PRODUCER, profile.profile, repository, ROLE_OPERATIONS[PRODUCER], int(time.time()) + 3600)

        worker = RealWorkerProvider(
            process, GitSourceControl(), context.checkout["path"], "origin",
            lambda invocation: f"candidate/{ref_safe(invocation.correlation_id)}", root / "producer-read-back", grant, repository,
            GitWorktreeAdapter(context.checkout["path"], root / "workspaces"), ReservationBook(1, 2),
            now=time.time, sleep=time.sleep, journal=journal,
        )
        self.projections: list[dict] = []

        def projection(work: str, field_: str, state: str, revision: int) -> int:
            # Withheld by design: the fixture writes nothing to the board but its own items' creation,
            # READY status and deletion. The attempted projection is retained as evidence instead.
            self.projections.append({"identity": work, "field": field_, "state": state, "revision": revision, "written": False})
            return revision

        self.notifications: list[str] = []
        allocation = {} if case.allocation is None else {identity: dict(case.allocation)}
        self.composition = GitHubProfileComposition(
            profile, compose_secrets(document), root / "state.sqlite", lambda: context.rows([identity]),
            context.contract_for,  # type: ignore[arg-type] - GitHubProjectsWorkManagement accepts a per-row resolver
            self.notifications.append, projection_write=projection, worker=worker, journal=journal,
            checkout=context.checkout["path"], release_admission=ReleaseAdmissionConfig(RELEASE_POINT, allocation),
        )
        self.coordinator = self.composition.coordinator

    def record_release(self, case: Case, context: RunContext) -> dict | None:
        if case.record is None:
            return None
        record_ref = f"{context.target.fixture}:{context.launch}:{self.identity}:release-record"
        values = {"identity": self.identity, "record_ref": record_ref, "authorizes_implement": True,
                  "baseline": context.checkout["baseline"],
                  "text": f"IMPLEMENT is authorized for this {context.target.fixture} probe item by the {WORK_UNIT} fixture."} | dict(case.record)
        if values["baseline"] == "<diverged>":
            values["baseline"] = context.checkout["diverged"]
        if isinstance(values.get("superseding_record"), str):
            values["superseding_record"] = values["superseding_record"].replace("{record_ref}", record_ref)
        self.composition.release_records.record(ReleaseAuthorization(**values))
        return values


def journal_counts(journal_path: Path, process_path: Path) -> dict:
    invocations = journal_records(journal_path) if journal_path.exists() else ()
    processes = journal_records(process_path) if process_path.exists() else ()
    return {
        "invocation_started": sum(1 for entry in invocations if entry.get("event") == "invocation-started"),
        "invocation_outcomes": [entry.get("kind") for entry in invocations if entry.get("event") == "invocation-outcome"],
        "publication_started": sum(1 for entry in invocations if entry.get("event") == "publication-started"),
        "process_runs": [entry.get("step") for entry in processes if entry.get("event") == "process-run"],
        "provider_calls": sum(int(entry.get("provider_calls", 0)) for entry in processes if entry.get("event") == "process-run"),
    }


def run_case(context: RunContext, case: Case, composed: Composed, observer: AdmissionObserver, *, before: dict | None = None) -> dict:
    """Drive the real prelaunch call site once for one case and observe everything it did."""
    identity = composed.identity
    gate_mark, admit_mark = len(observer.gate), len(observer.admit)
    snapshot_mark = len(context.snapshot_calls)
    summary = composed.coordinator.release_and_start(identity) if case.explicit_release else composed.coordinator.start()
    counts = journal_counts(composed.journal_path, composed.process_path)
    try:
        record = composed.coordinator.state(identity).record or {}
    except KeyError:
        record = {}
    try:
        account = composed.coordinator.guard_account(identity)
        reason = str(account["reason"])
    except KeyError:
        account, reason = None, None
    imported = any(identity in call["identities"] for call in context.snapshot_calls[snapshot_mark:])
    if reason is None and imported:
        item = next((entry for entry in composed.composition.work.import_ready_snapshot() if entry.identity == identity), None)
        if item is not None and not all(composed.coordinator._is_done(dependency) for dependency in item.dependencies):
            reason = "dependencies-incomplete"
        elif item is not None and not (composed.coordinator._is_automatic(item) or composed.coordinator._is_released(identity)):
            reason = "not-released"
    gate_log, admit_log = observer.gate[gate_mark:], observer.admit[admit_mark:]
    starts = counts["invocation_started"] - (before or {}).get("invocation_started", 0)
    observed_refusal = refused_by(identity, gate_log, admit_log, imported, reason if starts == 0 else None)
    return {
        "case": case.name, "pinned_step": case.step, "criterion": case.criterion, "identity": identity,
        "item": context.items[identity], "expected_worker_starts": case.expected_starts, "expected_refused_by": case.refused_by,
        "observed_worker_starts": starts, "observed_refused_by": observed_refusal,
        "gate_answers": gate_log, "admit_release_answers": admit_log, "imported_from_fresh_board_read": imported,
        "eligibility": account, "stop_reason": str(summary.stop_reason), "dispatched": list(summary.dispatched),
        "authority_blocked": list(summary.authority_blocked), "recorded_correlation": record.get("correlation"),
        "recorded_outcome": record.get("outcome"), "recorded_hold_reason": record.get("hold_reason"),
        "journal": counts, "binding_refusals": dict(composed.composition.worker.refusals),
        "projection_attempts": list(composed.projections), "profile_automatic_release": case.automatic_release,
        "allocation": case.allocation, "explicit_release": case.explicit_release,
        "matches_expected": starts == case.expected_starts and observed_refusal == case.refused_by,
    }


# --- the run --------------------------------------------------------------------------------------


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def cleanup(board: LiveBoard, ledger: Mapping[str, object]) -> dict:
    deleted, failures = [], []
    for identity, item in dict(ledger.get("items") or {}).items():
        try:
            answer = board.delete(item)
            deleted.append({"identity": identity, "item": item, "deleted_item_id": answer})
        except Exception as error:  # noqa: BLE001 - every failure is reported and fails the run
            failures.append({"identity": identity, "item": item, "error": type(error).__name__ + ": " + str(error)[:200]})
    remaining = {item["id"] for item in board.read_items()}
    wanted = set(dict(ledger.get("items") or {}).values())
    absent = {item: board.absent(item) and item not in remaining for item in sorted(wanted)}
    return {"deleted": deleted, "failures": failures, "absent_after_fresh_read": absent,
            "verified": not failures and all(absent.values()) and all(entry["deleted_item_id"] == entry["item"] for entry in deleted)}


def credentials_for(document: Mapping[str, object]):
    import py10_sandbox
    return py10_sandbox.credentials(dict(document))


def clone_environment(target_: Target, credentials) -> dict | None:
    if target_.name == "sandbox":
        import py10_sandbox
        return py10_sandbox.credentialed_git_environment(dict(target_.document), credentials.token().value)
    return None  # production: the executing worker's own read access, as for every other clone of this repository


def execute(target_: Target, out: Path, run_root: Path) -> int:
    """Bind the live boards and the fresh clone, then run the pinned sequence."""
    import py10_sandbox
    from alienintent.installation.adapters.urllib_github_transport import UrllibGitHubTransport

    credentials = credentials_for(target_.document)
    board = LiveBoard(target_.address(), RecordingTransport(UrllibGitHubTransport()), credentials.authorization)
    watched: dict[str, LiveBoard] = {}
    if target_.name == "sandbox":
        production = production_document()
        watched[PRODUCTION_ISOLATION] = LiveBoard(Target("production", "FX-B4", 2, production).address(),
                                                  RecordingTransport(UrllibGitHubTransport()), credentials_for(production).authorization)
    return run_phase(target_, board, watched, out, run_root, py10_sandbox.Redactor(dict(target_.document)),
                     lambda: prepare_checkout(run_root, f"https://github.com/{target_.repository}", clone_environment(target_, credentials)))


def run_phase(target_: Target, board, watched: Mapping[str, object], out: Path, run_root: Path, redact,
              checkout_factory: Callable[[], dict]) -> int:
    launch = launch_id()
    started = _now()
    transport = board.transport
    statuses = board.schema_statuses()
    if "READY" not in statuses:
        raise SystemExit("the target Project has no READY Status option")
    before = board_digest(board.read_items(detailed=True))
    watched_before = {name: board_digest(other.read_items(detailed=True)) for name, other in watched.items()}

    checkout = checkout_factory()
    selected = cases_for(target_.phase)
    contracts: dict[str, BiuContract] = {}
    bodies: dict[str, tuple[str, str]] = {}
    prefix = f"{target_.prefix}-{launch}"
    for case in selected:
        identity = probe_identity(target_.prefix, launch, case.suffix)
        if identity in contracts:
            continue
        contract = contract_from_document(contract_document(identity, target_, case.contract, prefix))
        stale = contract_from_document(contract_document(identity, target_, dict(case.contract) | {"version": "0"}, prefix))
        contracts[identity] = contract
        bodies[identity] = (probe_title(identity), probe_body(identity, contract, (stale if case.stale_digest else contract).content_digest,
                                                               launch, target_.fixture))

    ledger_path = out / "ledger.json"
    ledger: dict[str, object] = {"target": target_.name, "project": target_.address().project_id, "launch": launch, "items": {}}
    context = RunContext(target_, board, launch, run_root, checkout, contracts, ledger["items"])  # type: ignore[arg-type]
    probes, results, failure = [], [], None
    try:
        # Step 1: seed every probe item and read each back fresh before any admission attempt.
        for identity, (title, body) in bodies.items():
            item = board.create(title, body)
            ledger["items"][identity] = item  # type: ignore[index]
            write_json(ledger_path, ledger)
            board.make_ready(item)
            readback = board.read_back(item)
            probes.append({"identity": identity, "item": item, "title": title, "body_sha256": sha256(body),
                           "contract_digest": contracts[identity].content_digest, "readback": readback,
                           "readback_ok": readback["status"] == "READY" and readback["priority"] == "P5"
                           and readback["title"] == title and readback["body_sha256"] == sha256(body)})
        if not all(probe["readback_ok"] for probe in probes):
            raise RuntimeError("a probe item did not read back exactly as seeded")

        composed_by_case: dict[str, Composed] = {}
        with AdmissionObserver() as observer:
            for case in selected:
                identity = probe_identity(target_.prefix, launch, case.suffix)
                if case.replay_of:
                    composed = composed_by_case[case.replay_of]
                    prior = journal_counts(composed.journal_path, composed.process_path)
                    results.append(run_case(context, case, composed, observer, before=prior))
                    continue
                composed = Composed(context, case, identity)
                observer.watch(composed.composition.release_admission.gate)
                release = composed.record_release(case, context)
                composed_by_case[case.name] = composed
                result = run_case(context, case, composed, observer)
                result["release_record"] = release
                results.append(result)
        # Step 15: fresh readback — every probe still READY, untouched by the coordinator.
        final = {item["id"]: item for item in board.read_items()}
        step15 = {identity: {"present": item in final, "status": (final.get(item, {}).get("fields", {}).get("Status") or {}).get("value")}
                  for identity, item in ledger["items"].items()}  # type: ignore[union-attr]
    except Exception as error:  # noqa: BLE001 - reported, then cleanup still runs
        failure = type(error).__name__ + ": " + str(error)[:500]
        step15 = None
    finally:
        cleaned = cleanup(board, ledger)
        write_json(ledger_path, ledger | {"cleanup": cleaned})

    after = board_digest(board.read_items(detailed=True))
    target_diff = board_diff(before, after)
    watched_diff = {name: board_diff(watched_before[name], board_digest(other.read_items(detailed=True))) for name, other in watched.items()}
    created = set(dict(ledger["items"]).values())  # type: ignore[arg-type]
    scoped = [m for m in transport.mutations if m["operation"] != "addProjectV2DraftIssue"]
    mutation_scope_ok = all(m["item"] in created and m["project"] == target_.address().project_id for m in scoped) and all(
        m["project"] == target_.address().project_id for m in transport.mutations)
    watched_mutations = {name: other.transport.mutations for name, other in watched.items()}
    expected_total = sum(case.expected_starts for case in selected)
    observed_total = sum(result["observed_worker_starts"] for result in results)
    provider_calls = sum(result["journal"]["provider_calls"] for result in results if result["case"] != "03-identity-replay")
    publications = sum(result["journal"]["publication_started"] for result in results if result["case"] != "03-identity-replay")
    checks = {
        "no_failure": failure is None,
        "all_cases_match": bool(results) and len(results) == len(selected) and all(result["matches_expected"] for result in results),
        "exact_launch_total": observed_total == expected_total,
        "zero_provider_calls": provider_calls == 0,
        "zero_publications": publications == 0,
        "no_binding_refusals": all(not result["binding_refusals"] for result in results),
        "no_board_projection_written": all(not any(p["written"] for p in result["projection_attempts"]) for result in results),
        "probes_intact_at_readback": step15 is not None and all(entry["present"] and entry["status"] == "READY" for entry in step15.values()),
        "mutations_only_on_own_items": mutation_scope_ok,
        "watched_boards_not_written": all(not mutations for mutations in watched_mutations.values()),
        "cleanup_verified": cleaned["verified"],
        "target_board_unchanged": target_diff["unchanged"],
        "watched_boards_unchanged": all(diff["unchanged"] for diff in watched_diff.values()),
    }
    passed = all(checks.values())
    record = {
        "record_kind": "ReleaseAdmissionProof", "schema_version": 1, "fixture": target_.fixture, "phase": target_.phase,
        "work_unit": WORK_UNIT, "issue": ISSUE,
        "label": ("OPERATIONAL — phase 1, isolated sandbox target; does not satisfy the 'actual live-profile' criterion by itself"
                  if target_.phase == 1 else "OPERATIONAL — phase 2, real AlienLogicLab/alienintent Project #1 prelaunch boundary; worker process doubled"),
        "launch_id": launch, "started_at": started, "ended_at": _now(),
        "invocation": {"argv": sys.argv, "tool": "tools/live/fx_b3_release_admission_proof.py",
                       "tool_sha256": sha256(Path(__file__).read_bytes()), "source_revision": _source_revision()},
        "target": {"name": target_.name, "repository": target_.repository, "project_id": target_.address().project_id,
                   "project_number": target_.address().project_number, "profile": str(target_.document["profile"])},
        "composition": {
            "root": "alienintent.composition.github_profile.GitHubProfileComposition",
            "call_site": "FactoryCoordinator._run: ReleasePreconditionGate.check -> admit_release -> RoleBindingGuard.start",
            "worker": "RoleBindingGuard(RealWorkerProvider(ScriptedWorkerProcess['authority-block'], JsonlInvocationJournal, GitWorktreeAdapter))",
            "snapshot": "fresh paginated Projects v2 read per admission pass, restricted to this run's own probe item ids",
            "projection": "withheld: recorded locally, never written to the board",
            "observation": "admit_release and ReleasePreconditionGate.check wrapped observation-only; each delegates unchanged",
        },
        "checkout": {key: str(value) for key, value in checkout.items() if key != "path"},
        "probe_items": probes, "cases": results, "step15_readback": step15,
        "totals": {"expected_worker_starts": expected_total, "observed_worker_starts": observed_total,
                   "provider_calls": provider_calls, "publications": publications},
        "snapshot_reads": context.snapshot_calls, "mutations": transport.mutations, "watched_mutations": watched_mutations,
        "cleanup": cleaned, "non_interference": {"target": target_diff, **watched_diff},
        "tokens_and_cost": "UNKNOWN (no provider ran; the fixture itself spends no tokens)",
        "failure": failure, "checks": checks, "passed": passed, "exit_status": 0 if passed else 1,
    }
    write_json(out / "result.json", redact(record))
    write_json(out / "board-before.json", redact(before))
    write_json(out / "board-after.json", redact(after))
    for name in watched:
        write_json(out / "production-board-before-after-diff.json", redact(watched_diff[name]))
    for case_dir in sorted((run_root / "cases").glob("*")) if (run_root / "cases").exists() else ():
        for journal in ("invocation-journal.jsonl", "process-journal.jsonl"):
            if (case_dir / journal).exists():
                (out / "journals" / case_dir.name).mkdir(parents=True, exist_ok=True)
                (out / "journals" / case_dir.name / journal).write_text(redact.text((case_dir / journal).read_text(encoding="utf-8")), encoding="utf-8")
    print(json.dumps({"fixture": target_.fixture, "launch": launch, "passed": passed, "checks": checks,
                      "totals": record["totals"], "failure": failure}, indent=1))
    return 0 if passed else 1


def _source_revision() -> dict:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "tools/live/fx_b3_release_admission_proof.py"], cwd=ROOT,
                           capture_output=True, text=True, check=False).stdout.strip()
    return {"head": head, "tool_uncommitted": bool(dirty)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", choices=("sandbox", "production"))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--cleanup-ledger", type=Path, help="recovery only: delete the items a crashed run recorded")
    args = parser.parse_args(argv)
    if args.cleanup_ledger:
        ledger = json.loads(args.cleanup_ledger.read_text(encoding="utf-8"))
        target_ = target(ledger["target"])
        if ledger["project"] != target_.address().project_id:
            raise SystemExit("ledger names another Project")
        from alienintent.installation.adapters.urllib_github_transport import UrllibGitHubTransport
        board = LiveBoard(target_.address(), RecordingTransport(UrllibGitHubTransport()), credentials_for(target_.document).authorization)
        result = cleanup(board, ledger)
        print(json.dumps(result, indent=1))
        return 0 if result["verified"] else 1
    if not args.target or not args.out:
        parser.error("--target and --out are required")
    run_root = Path(tempfile.mkdtemp(prefix=f"fx-b3-{args.target}-"))
    try:
        return execute(target(args.target), args.out, run_root)
    finally:
        shutil.rmtree(run_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
