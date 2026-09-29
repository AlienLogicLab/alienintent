#!/usr/bin/env python3
"""Authoritative, read-only predicate adapter for the Factory Director Host (FDH-01).

The adapter reads only durable sources and derives the host's nine-boolean
``DirectorInputs`` projection with the mapping fixed by
``docs/work-units/wave2/FDH-01.md``:

* GitHub Project #1, through the fail-closed read path in
  ``tools/live/project_materialization.py`` (complete, internally consistent board, one
  item per Issue; non-Issue items are excluded as observable foreign pollution rather
  than failing the whole board closed), plus Issue comments for retained Agent Ready
  assessments;
* the Node runtime state file named by ``self-hosting.json`` ``paths.stateFile``
  (``active``, ``limitEscalations``, ``founderExceptions``);
* the Founder-hold record, the explicit-pause flag and the Director inbox named
  by the host configuration.

Any read failure, partial board, parse error or schema mismatch makes
``authoritative_state`` false and every other predicate false. The adapter never
writes to GitHub, the runtime state file or any configuration, never transitions
an Issue, and never infers authority from a process list. Its only writes are its
own projection and diagnostics files, each replaced atomically.

Source paths, schemas and the idle-reason precedence are documented in
``docs/operations/factory-director-runtime-contract.md``.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "live"))

import project_materialization as materialization  # noqa: E402
from release_admission import MalformedReceipt, agent_ready_disposition  # noqa: E402
from app_github_reader import AppGitHubReader  # noqa: E402
from factory_director_host import DirectorInputs  # noqa: E402

HOST_CONFIG_SCHEMA_VERSION = 1
HOLD_RECORD_SCHEMA_VERSION = 1
LIFECYCLE_STATES = frozenset(materialization.STATUS_OPTIONS)
WORKER_STATES = frozenset({"IMPLEMENT", "VERIFY", "ACCEPT"})
INBOX_ENTRY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.json$")
HOLD_KEYS = frozenset({"issue", "reason", "kind"})
HOLD_OPTIONAL_KEYS = frozenset({"recordedAt", "recordedBy"})
MAX_FOUNDER_FILE_BYTES = 4 * 1024 * 1024

UNAVAILABLE = DirectorInputs(False, False, False, False, False, False, False, False, False)


class SourceUnavailable(Exception):
    """A durable source is absent, unreadable, partial or inconsistent."""


class ProvenanceUnavailable(SourceUnavailable):
    """A required external read failed; no authoritative projection can be published."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def _positive_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _read_json(path: Path, label: str):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise SourceUnavailable(f"{label} is absent: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceUnavailable(f"{label} is unreadable or unparsable: {path}") from exc


def _read_founder_file(path: Path) -> bytes:
    with path.open("rb") as stream:
        data = stream.read(MAX_FOUNDER_FILE_BYTES + 1)
    if len(data) > MAX_FOUNDER_FILE_BYTES:
        raise SourceUnavailable(f"Founder file exceeds {MAX_FOUNDER_FILE_BYTES} bytes: {path}")
    return data


def _absolute_path(value, label: str) -> Path:
    if not isinstance(value, str) or not value or not Path(value).is_absolute():
        raise SourceUnavailable(f"{label} must be an absolute path")
    return Path(value)


@dataclass(frozen=True)
class AdapterConfig:
    self_hosting_config: Path
    founder_hold_record: Path
    pause_flag: Path
    director_inbox: Path
    wip_limit: int
    prepared_buffer_target: int


def load_adapter_config(path: Path | str) -> AdapterConfig:
    raw = _read_json(Path(path), "host configuration")
    if not isinstance(raw, dict) or raw.get("schemaVersion") != HOST_CONFIG_SCHEMA_VERSION:
        raise SourceUnavailable("host configuration schemaVersion is not 1")
    if not _positive_int(raw.get("wipLimit")):
        raise SourceUnavailable("host configuration wipLimit must be a positive integer")
    prepared_buffer_target = raw.get("preparedBufferTarget", 1)
    if not _positive_int(prepared_buffer_target):
        raise SourceUnavailable("host configuration preparedBufferTarget must be a positive integer")
    return AdapterConfig(
        self_hosting_config=_absolute_path(raw.get("selfHostingConfig"), "selfHostingConfig"),
        founder_hold_record=_absolute_path(raw.get("founderHoldRecord"), "founderHoldRecord"),
        pause_flag=_absolute_path(raw.get("pauseFlag"), "pauseFlag"),
        director_inbox=_absolute_path(raw.get("directorInbox"), "directorInbox"),
        wip_limit=raw["wipLimit"], prepared_buffer_target=prepared_buffer_target,
    )


# --- GitHub reads (read-only; queries only) ------------------------------------------------

def require_gh() -> None:
    """Fail closed, naming the tool and the PATH searched, when ``gh`` cannot be resolved.

    A systemd user unit does not inherit the login shell's PATH (FDH-91), so this is checked
    before the first GitHub read rather than surfacing as a raw ``FileNotFoundError``.
    """
    searched = os.environ.get("PATH", os.defpath)
    if shutil.which("gh", path=searched) is None:
        raise SourceUnavailable(f"required executable 'gh' is not resolvable on PATH={searched!r}; "
                                "set PATH in factory-director-host.env")


_COMMENTS_QUERY = (
    'query($owner:String!,$name:String!,$issue:Int!,$cursor:String){repository(owner:$owner,name:$name)'
    '{issue(number:$issue){comments(first:100,after:$cursor){totalCount pageInfo{hasNextPage endCursor}'
    ' nodes{body lastEditedAt author{login} editor{login}}}}}}')


def read_issue_comments(issue: int) -> list[dict]:
    """Every comment (author login, body) on one Issue; refuses an incomplete answer like ``read_board``."""
    owner, name = materialization.REPO.split("/")
    bodies: list[dict] = []
    cursor = None
    while True:
        args = ["api", "graphql", "-f", f"query={_COMMENTS_QUERY}", "-F", f"owner={owner}",
                "-F", f"name={name}", "-F", f"issue={issue}"]
        if cursor:
            args += ["-f", f"cursor={cursor}"]
        connection = json.loads(materialization._gh(*args))["data"]["repository"]["issue"]["comments"]
        nodes, info = connection["nodes"], connection["pageInfo"]
        if not isinstance(nodes, list) or not all(isinstance(node.get("body"), str) for node in nodes):
            raise SourceUnavailable(f"issue #{issue} comment page is malformed")
        bodies += [{"author": (node.get("author") or {}).get("login"),
                    "editor": (node.get("editor") or {}).get("login"), "lastEditedAt": node.get("lastEditedAt"),
                    "body": node["body"]} for node in nodes]
        if info["hasNextPage"] is False:
            break
        if info["hasNextPage"] is not True or not info.get("endCursor"):
            raise SourceUnavailable(f"issue #{issue} comment pagination is inconsistent")
        cursor = info["endCursor"]
    if connection["totalCount"] != len(bodies):
        raise SourceUnavailable(f"issue #{issue} reports {connection['totalCount']} comments, read {len(bodies)}")
    return bodies


# --- per-source validation ------------------------------------------------------------------

def validate_board(rows) -> tuple[dict[int, str], tuple[str, ...]]:
    """Issue number -> lifecycle state (the whole board or nothing), and the foreign
    (non-Issue) items observed.

    A non-Issue Project item -- a benign GitHub ``DRAFT_ISSUE`` card, for example -- is board
    pollution, not an authority signal: it is excluded from AlienIntent lifecycle state and
    reported back as a foreign item rather than failing the whole board closed. An ISSUE row
    is still held to strict validation: repository identity, issue number, lifecycle status
    and duplicates all fail closed, because those are exactly the shapes that could otherwise
    fabricate execution authority.
    """
    if not isinstance(rows, list):
        raise SourceUnavailable("Project board is not a list of items")
    board: dict[int, str] = {}
    foreign: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            raise SourceUnavailable(f"Project item is not an object: {row!r}"[:240])
        if row.get("type") != "ISSUE":
            foreign.append(f"{row.get('type')!r} item {row.get('id')!r}"[:120])
            continue
        issue, status = row.get("issue"), row.get("status")
        if not _positive_int(issue):
            raise SourceUnavailable(f"Project item {row.get('id')!r} has no Issue number")
        if row.get("repository") != materialization.REPO:
            raise SourceUnavailable(f"Project item for issue #{issue} is not from {materialization.REPO}: "
                                    f"{row.get('repository')!r}")
        if not isinstance(status, str) or status.upper() not in LIFECYCLE_STATES:
            raise SourceUnavailable(f"issue #{issue} has no recognised lifecycle Status ({status!r})")
        if issue in board:
            raise SourceUnavailable(f"duplicate Project items for issue #{issue}")
        board[issue] = status.upper()
    return board, tuple(foreign)


def validate_self_hosting(raw) -> tuple[str, Path, frozenset[str]]:
    """The configured repository, the Node runtime state file it names, and its operator logins."""
    if not isinstance(raw, dict):
        raise SourceUnavailable("self-hosting configuration is not an object")
    repository, project, paths = raw.get("repository"), raw.get("project"), raw.get("paths")
    if not all(isinstance(value, dict) for value in (repository, project, paths)):
        raise SourceUnavailable("self-hosting configuration lacks repository, project or paths")
    full_name = f"{repository.get('owner')}/{repository.get('name')}"
    if full_name != materialization.REPO:
        raise SourceUnavailable(f"self-hosting repository {full_name!r} is not {materialization.REPO!r}")
    if (project.get("owner"), project.get("number")) != (materialization.PROJECT_OWNER,
                                                         materialization.PROJECT_NUMBER):
        raise SourceUnavailable("self-hosting project is not the Project the read path verifies")
    logins = (raw.get("operator") or {}).get("authorizedGithubLogins")
    if not isinstance(logins, list) or not all(isinstance(login, str) and login for login in logins):
        raise SourceUnavailable("self-hosting operator.authorizedGithubLogins is not a list of logins")
    return (full_name, _absolute_path(paths.get("stateFile"), "paths.stateFile"),
            frozenset(login.lower() for login in logins))


@dataclass(frozen=True)
class RuntimeView:
    claims: int
    claimed_issues: frozenset[int]
    escalations: tuple[tuple[str, dict], ...]
    founder_exceptions: int


def validate_runtime_state(raw, repository: str) -> RuntimeView:
    if not isinstance(raw, dict):
        raise SourceUnavailable("runtime state is not an object")
    active = raw.get("active")
    if not isinstance(active, dict):
        raise SourceUnavailable("runtime state has no active claim map")
    # The Node runtime creates these lazily (`??= {}`); absence means none recorded.
    escalations = raw.get("limitEscalations", {})
    exceptions = raw.get("founderExceptions", {})
    if not isinstance(escalations, dict) or not isinstance(exceptions, dict):
        raise SourceUnavailable("runtime limitEscalations or founderExceptions is not an object")
    claimed: set[int] = set()
    for lane, claim in active.items():
        item = claim.get("item") if isinstance(claim, dict) else None
        if (not isinstance(item, dict) or not isinstance(item.get("repository"), str)
                or not _positive_int(item.get("issue"))
                or not lane.startswith(f"{item['repository']}#{item['issue']}:")):
            raise SourceUnavailable(f"runtime active claim {lane!r} is inconsistent")
        if item["repository"] == repository:
            claimed.add(item["issue"])
    for key, entry in escalations.items():
        if (not isinstance(entry, dict) or not isinstance(entry.get("outcome"), str)
                or not isinstance(entry.get("at"), str)):
            raise SourceUnavailable(f"runtime limitEscalations entry {key!r} is malformed")
    for key, entry in exceptions.items():
        if not isinstance(entry, dict):
            raise SourceUnavailable(f"runtime founderExceptions entry {key!r} is malformed")
    return RuntimeView(len(active), frozenset(claimed), tuple(sorted(escalations.items())), len(exceptions))


def escalation_receipt_id(key: str, entry: dict) -> str:
    """Director receipt id for one exact escalation (a newer escalation of the BIU needs a new one)."""
    digest = sha256(f"{key}\n{entry['outcome']}\n{entry['at']}".encode()).hexdigest()[:32]
    return f"escalation-{digest}"


def unresolved_escalations(runtime: RuntimeView, board: dict[int, str],
                           acknowledgements: frozenset[str]) -> tuple[str, ...]:
    """The Node runtime never removes or resolves an escalation, so resolution is read from durable
    state: a Director acknowledgement ``<inbox>/escalations/<escalation id>.json`` for that exact
    escalation, or its Issue having reached DONE. Inbox ``processed/`` receipts never count."""
    unresolved = []
    for key, entry in runtime.escalations:
        repository, _, number = key.rpartition("#")
        done = repository == materialization.REPO and number.isdigit() and board.get(int(number)) == "DONE"
        if not done and escalation_receipt_id(key, entry) not in acknowledgements:
            unresolved.append(key)
    return tuple(unresolved)


def validate_holds(raw) -> dict[int, str]:
    if not isinstance(raw, dict) or set(raw) != {"schemaVersion", "holds"}:
        raise SourceUnavailable("Founder-hold record must be exactly {schemaVersion, holds}")
    if raw["schemaVersion"] != HOLD_RECORD_SCHEMA_VERSION or not isinstance(raw["holds"], list):
        raise SourceUnavailable("Founder-hold record schemaVersion is not 1 or holds is not a list")
    holds: dict[int, str] = {}
    for hold in raw["holds"]:
        if (not isinstance(hold, dict) or not HOLD_KEYS <= set(hold)
                or not set(hold) <= HOLD_KEYS | HOLD_OPTIONAL_KEYS
                or not _positive_int(hold["issue"])
                or hold["kind"] != "FOUNDER_DECISION"
                or not isinstance(hold["reason"], str) or not hold["reason"].strip()):
            raise SourceUnavailable(f"Founder-hold entry is malformed: {hold!r}"[:240])
        if hold["issue"] in holds:
            raise SourceUnavailable(f"Founder-hold record lists issue #{hold['issue']} twice")
        holds[hold["issue"]] = hold["reason"]
    return holds


def _ids(directory: Path) -> frozenset[str]:
    return frozenset(path.stem for path in directory.iterdir() if path.is_file() and INBOX_ENTRY.match(path.name))


def validate_founder_receipt(entry_id: str, source: bytes, receipt: dict, rows: list[dict],
                             provenance_reader: Callable[[str, str, int], tuple[str, str]]) -> int:
    """Return the uniquely verified Issue number or explain why the receipt cannot clear intake."""
    try:
        entry = json.loads(source)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceUnavailable(f"Founder entry {entry_id}: source bytes are unparsable") from exc
    if not isinstance(entry, dict) or entry.get("kind") != "FOUNDER_REQUIREMENT":
        raise SourceUnavailable(f"Founder entry {entry_id}: source kind changed")
    for key in ("title", "authority", "requirement", "priority"):
        if not isinstance(entry.get(key), str) or not entry[key]:
            raise SourceUnavailable(f"Founder entry {entry_id}: {key} is absent")
    acceptance = entry.get("acceptance")
    if not isinstance(acceptance, list) or not acceptance or not all(
            isinstance(item, str) and item for item in acceptance):
        raise SourceUnavailable(f"Founder entry {entry_id}: acceptance is absent or malformed")
    material = receipt.get("materialization") if isinstance(receipt, dict) else None
    provenance = receipt.get("provenance") if isinstance(receipt, dict) else None
    if not isinstance(material, dict) or not isinstance(provenance, dict):
        raise SourceUnavailable(f"Founder entry {entry_id}: materialization or provenance is absent")
    if (receipt.get("entry") != entry_id or receipt.get("sourceSha256") != sha256(source).hexdigest()
            or provenance.get("sourceTitle") != entry["title"]
            or provenance.get("sourceAuthority") != entry["authority"]):
        raise SourceUnavailable(f"Founder entry {entry_id}: source identity, digest, title or authority differs")
    revision, artifact, issue = (material.get("revision"), material.get("canonicalArtifact"),
                                 material.get("issue"))
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise SourceUnavailable(f"Founder entry {entry_id}: revision is not a full SHA")
    if (not isinstance(artifact, str) or artifact.startswith("/") or not artifact.strip()
            or any(part in ("", ".", "..") for part in artifact.split("/"))):
        raise SourceUnavailable(f"Founder entry {entry_id}: canonical artifact path is invalid")
    if not _positive_int(issue) or material.get("project") != materialization.PROJECT_NUMBER:
        raise SourceUnavailable(f"Founder entry {entry_id}: Issue or configured Project identity differs")
    matches = [row for row in rows if row.get("type") == "ISSUE" and row.get("issue") == issue]
    if (len(matches) != 1 or matches[0].get("repository") != materialization.REPO
            or matches[0].get("id") != material.get("projectItem")):
        raise SourceUnavailable(f"Founder entry {entry_id}: unique Project item identity differs")
    if material.get("priority") != entry["priority"] or matches[0].get("priority") != entry["priority"]:
        raise SourceUnavailable(f"Founder entry {entry_id}: Founder priority differs")
    try:
        canonical_text, issue_body = provenance_reader(revision, artifact, issue)
    except Exception as exc:
        raise ProvenanceUnavailable(f"Founder entry {entry_id}: {exc}"[:300]) from exc
    for key, value in [("requirement", entry["requirement"]),
                       *(("acceptance", item) for item in acceptance)]:
        if value not in canonical_text and value not in issue_body:
            raise SourceUnavailable(f"Founder entry {entry_id}: exact {key} is absent from canonical/Issue")
    return issue


def prepare_founder_receipt_migration(entry_id: str, source: bytes, old_receipt: dict,
                                      rows: list[dict], provenance_reader: Callable[[str, str, int],
                                      tuple[str, str]]) -> dict:
    """Build a checked enrichment without writing operational state or replacing old evidence.

    The Director owns the eventual atomic write after independent live readback. Repeating
    this preparation over either the old or enriched receipt produces the same result.
    """
    if not isinstance(old_receipt, dict):
        raise SourceUnavailable(f"Founder entry {entry_id}: old receipt is not an object")
    try:
        entry = json.loads(source)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceUnavailable(f"Founder entry {entry_id}: source bytes are unparsable") from exc
    if not isinstance(entry, dict):
        raise SourceUnavailable(f"Founder entry {entry_id}: source is not an object")
    candidate = json.loads(json.dumps(old_receipt))
    expected = {"entry": entry_id, "sourceSha256": sha256(source).hexdigest(),
                "provenance": {"sourceTitle": entry.get("title"),
                               "sourceAuthority": entry.get("authority")}}
    for key, value in expected.items():
        if key in candidate and candidate[key] != value:
            raise SourceUnavailable(f"Founder entry {entry_id}: existing {key} conflicts with source")
        candidate[key] = value
    validate_founder_receipt(entry_id, source, candidate, rows, provenance_reader)
    return candidate


def read_inbox(inbox: Path, board: dict[int, str] | None = None, *, rows: list[dict] | None = None,
               provenance_reader: Callable[[str, str, int], tuple[str, str]] | None = None,
               failures: dict[str, str] | None = None) -> tuple[tuple[str, ...], frozenset[str]]:
    """Active entry ids and escalation acknowledgements in ``escalations/``.

    A visible ``*.json`` file whose name is not a valid entry id fails closed rather than
    being silently ignored; dot-files and non-``.json`` names (temporary files) are not entries.
    A Founder receipt discharges its entry only after exact provenance and Project DONE.
    """
    if not inbox.is_dir():
        raise SourceUnavailable(f"Director inbox directory is absent: {inbox}")
    processed, escalations = inbox / "processed", inbox / "escalations"
    for directory in (processed, escalations):
        if directory.exists() and not directory.is_dir():
            raise SourceUnavailable(f"Director inbox {directory.name}/ exists but is not a directory")
    try:
        files = [path for path in inbox.iterdir() if path.is_file()]
        receipts = _ids(processed) if processed.is_dir() else frozenset()
        acknowledgements = _ids(escalations) if escalations.is_dir() else frozenset()
    except OSError as exc:
        raise SourceUnavailable(f"Director inbox cannot be listed: {exc}") from exc
    unrecognised = [path.name for path in files if path.name.endswith(".json")
                    and not path.name.startswith(".") and not INBOX_ENTRY.match(path.name)]
    if unrecognised:
        raise SourceUnavailable(f"Director inbox has entries with invalid ids: {sorted(unrecognised)!r}"[:240])
    entries = {path.stem for path in files if INBOX_ENTRY.match(path.name)}

    # Product-intent input has a stronger completion rule than ordinary operational handoffs.
    # A FOUNDER_REQUIREMENT remains pending until its receipt proves durable materialization;
    # acknowledgement/defer text alone must never make the requirement disappear.
    valid_receipts = set(receipts)
    for entry_id in sorted(entries & receipts):
        entry_path = inbox / f"{entry_id}.json"
        try:
            source = _read_founder_file(entry_path)
            entry = json.loads(source)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SourceUnavailable(f"Director inbox entry {entry_id!r} cannot be parsed: {exc}"[:240]) from exc
        if not isinstance(entry, dict):
            raise SourceUnavailable(f"Director inbox entry {entry_id!r} is not an object")
        if entry.get("kind") != "FOUNDER_REQUIREMENT":
            continue
        receipt_path = processed / f"{entry_id}.json"
        try:
            receipt = json.loads(_read_founder_file(receipt_path))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            valid_receipts.discard(entry_id)
            if failures is not None:
                failures[entry_id] = f"Founder entry {entry_id}: receipt is unreadable or unparsable: {exc}"[:300]
            continue
        try:
            if rows is None or provenance_reader is None or board is None:
                raise SourceUnavailable("complete Project and provenance readers are required")
            issue = validate_founder_receipt(entry_id, source, receipt, rows, provenance_reader)
        except ProvenanceUnavailable:
            raise
        except SourceUnavailable as exc:
            valid_receipts.discard(entry_id)
            if failures is not None:
                failures[entry_id] = str(exc)
            continue
        # Materialization is a checkpoint, not completion. When authoritative board state is
        # available, a Founder requirement remains an active Director obligation until its
        # linked backlog item reaches DONE. This prevents materialized-but-forgotten intent.
        if board.get(issue) != "DONE":
            valid_receipts.discard(entry_id)

    return tuple(sorted(entries - valid_receipts)), acknowledgements


def retained_assessment_disposition(comments: list[dict], issue: int, operators: frozenset[str]) -> str | None:
    """The Issue's Agent Ready disposition, from the reader the release gate uses."""
    try:
        return agent_ready_disposition(comments, operators)
    except MalformedReceipt as exc:
        raise SourceUnavailable(f"issue #{issue}: {exc}") from exc


# --- mapping ------------------------------------------------------------------------------

@dataclass(frozen=True)
class Evaluation:
    inputs: DirectorInputs
    failure: str | None = None
    observations: dict = field(default_factory=dict)
    # Digest of the durable state a Director episode advances (board states, holds, unprocessed
    # inbox entries, unresolved escalations, assessed Issues). Worker claims are deliberately
    # excluded. The host compares it across a short episode to tell progress from a crash.
    fingerprint: str | None = None


def control_reason(issue: int, state: str, claimed: frozenset[int], assessed: dict[int, str],
                   supply_candidates: frozenset[int] = frozenset()) -> str | None:
    """Why this Issue alone would make Director control required, ignoring holds."""
    if state == "READY":
        return "eligible:READY"
    if state in WORKER_STATES and issue not in claimed:
        return f"eligible:{state}_UNCLAIMED"
    if state == "REVIEW":
        return "selection:REVIEW"
    # Only a READY verdict is work the Director can advance. HOLD, CLARIFY and SPLIT wait for a
    # changed task packet and a new assessment; counting them kept selection true forever.
    if state == "TASKS" and assessed.get(issue) == "READY":
        return "selection:TASKS_ASSESSED"
    if state == "TASKS" and issue in supply_candidates:
        return "selection:TASKS_SUPPLY"
    return None


def derive(board: dict[int, str], runtime: RuntimeView, holds: dict[int, str],
           unprocessed: tuple[str, ...], assessed: dict[int, str] | set[int], paused: bool, wip_limit: int,
           acknowledgements: frozenset[str] = frozenset(), *,
           biu_issues: frozenset[int] = frozenset(), prepared_buffer_target: int = 1) -> Evaluation:
    if not isinstance(assessed, dict):
        assessed = {issue: "UNKNOWN" for issue in assessed}
    prepared_depth = sum(1 for issue, state in board.items()
                         if state == "READY" or (state == "TASKS" and assessed.get(issue) == "READY"))
    supply_candidates = frozenset(issue for issue, state in board.items()
                                  if prepared_depth < prepared_buffer_target and state == "TASKS"
                                  and issue in biu_issues and issue not in assessed and issue not in holds)
    reasons = {issue: reason for issue, state in board.items()
               if (reason := control_reason(issue, state, runtime.claimed_issues, assessed,
                                            supply_candidates))}
    unheld = {issue: reason for issue, reason in reasons.items() if issue not in holds}
    held = {issue: reason for issue, reason in reasons.items() if issue in holds}
    eligible = any(reason.startswith("eligible:") for reason in unheld.values())
    selection = any(reason.startswith("selection:") for reason in unheld.values())
    escalations = unresolved_escalations(runtime, board, acknowledgements)
    attention = bool(escalations)
    inbox = bool(unprocessed)
    inputs = DirectorInputs(
        authoritative_state=True,
        eligible_authorized_work=eligible,
        executable_capacity=runtime.claims < wip_limit,
        attention_required=attention,
        pending_director_inbox=inbox,
        lifecycle_requires_selection=selection,
        # At or above the limit, not only equal: a worker handoff briefly overlaps two claims
        # (FDH-92), and that is full WIP, not a refusal. The two predicates stay exact complements.
        wip_intentionally_full=runtime.claims >= wip_limit,
        founder_decision_pending=bool(held) and not unheld and not attention and not inbox,
        explicit_pause=paused,
    )
    observations = {
        "boardIssues": len(board), "activeClaims": runtime.claims, "wipLimit": wip_limit,
        "preparedBufferTarget": prepared_buffer_target, "preparedBufferDepth": prepared_depth,
        "supplyCandidates": sorted(supply_candidates),
        "controlRequiredBy": {str(k): v for k, v in sorted(unheld.items())},
        "heldControl": {str(k): v for k, v in sorted(held.items())},
        "unresolvedLimitEscalations": list(escalations),
        "escalationReceiptIds": {key: escalation_receipt_id(key, entry) for key, entry in runtime.escalations},
        "founderExceptions": runtime.founder_exceptions,
        "unprocessedInboxEntries": list(unprocessed),
    }
    fingerprint = sha256(json.dumps({
        "board": {str(k): v for k, v in sorted(board.items())}, "holds": sorted(holds),
        "inbox": list(unprocessed), "escalations": list(escalations), "assessed": sorted(assessed.items()),
    }, sort_keys=True).encode()).hexdigest()
    return Evaluation(inputs, None, observations, fingerprint)


class AuthoritativeDirectorInputs:
    """Callable source of ``DirectorInputs`` for the host; publishes each projection atomically."""

    def __init__(self, host_config: Path | str, projection: Path | str | None = None, *,
                 board_reader: Callable[[], list] | None = None,
                 comments_reader: Callable[[int], list[dict]] | None = None) -> None:
        self.host_config = Path(host_config)
        self.projection = Path(projection) if projection is not None else None
        self.board_reader, self.comments_reader = board_reader, comments_reader
        self._app_reader: AppGitHubReader | None = None
        self.last_foreign_project_items: tuple[str, ...] = ()
        self.last_biu_issues: frozenset[int] = frozenset()
        self.last_board_rows: list[dict] = []
        self.inbox_failures: dict[str, str] = {}
        self.provenance_reader: Callable[[str, str, int], tuple[str, str]] | None = None

    # Each reader is a separate method so a negative control can break exactly one source.
    def app_reader(self, config: AdapterConfig) -> AppGitHubReader:
        if self._app_reader is None:
            self._app_reader = AppGitHubReader(config.self_hosting_config)
        return self._app_reader

    def read_board(self, config: AdapterConfig) -> dict[int, str]:
        try:
            rows = self.board_reader() if self.board_reader is not None else self.app_reader(config).board()
            board, foreign = validate_board(rows)
            self.last_biu_issues = frozenset(
                row.get("issue") for row in rows if isinstance(row, dict) and row.get("type") == "ISSUE"
                and (any(isinstance(label, str) and label.lower() == "biu" for label in row.get("labels", []))
                     or (isinstance(row.get("title"), str) and row["title"].startswith(("WO-", "PY-", "FDH-", "ARP-"))))
                and _positive_int(row.get("issue")))
        except SourceUnavailable:
            raise
        except Exception as exc:  # MaterializationFailed, gh failure, malformed payload
            raise SourceUnavailable(f"Project board read failed: {exc}"[:300]) from exc
        self.last_foreign_project_items = foreign
        self.last_board_rows = rows
        return board

    def read_founder_provenance(self, config: AdapterConfig, revision: str,
                                artifact: str, issue: int) -> tuple[str, str]:
        """Bounded GitHub App reads of canonical main ancestry, artifact and Issue body."""
        reader = self.app_reader(config)
        owner, name = materialization.REPO.split("/")
        root = f"https://api.github.com/repos/{quote(owner)}/{quote(name)}"

        def get(url: str, label: str) -> dict:
            try:
                response = reader.transport.request("GET", url,
                                                    reader.credentials.authorization() | {"Accept": "application/vnd.github+json"})
                if response.status != 200:
                    raise SourceUnavailable(f"{label} returned HTTP {response.status}")
                value = json.loads(response.body)
                if not isinstance(value, dict):
                    raise TypeError("not an object")
                return value
            except SourceUnavailable:
                raise
            except Exception as exc:
                raise SourceUnavailable(f"{label} unavailable: {type(exc).__name__}: {exc}"[:300]) from exc

        comparison = get(f"{root}/compare/{revision}...main?per_page=1", "canonical remote comparison")
        if comparison.get("status") not in ("ahead", "identical"):
            raise SourceUnavailable(f"revision {revision} is not ancestral to canonical remote main")
        content = get(f"{root}/contents/{quote(artifact, safe='/')}?ref={revision}", "canonical artifact")
        if content.get("type") != "file" or content.get("encoding") != "base64":
            raise SourceUnavailable("canonical artifact is not a base64 file at revision")
        try:
            artifact_text = base64.b64decode(content["content"].replace("\n", ""), validate=True).decode("utf-8")
        except (KeyError, ValueError, UnicodeDecodeError) as exc:
            raise SourceUnavailable("canonical artifact content cannot be decoded") from exc
        issue_doc = get(f"{root}/issues/{issue}", f"issue #{issue}")
        if issue_doc.get("number") != issue or not isinstance(issue_doc.get("body"), str):
            raise SourceUnavailable(f"issue #{issue} body or identity differs")
        return artifact_text, issue_doc["body"]

    def read_runtime(self, config: AdapterConfig) -> RuntimeView:
        repository, state_file, self.operators = validate_self_hosting(
            _read_json(config.self_hosting_config, "self-hosting configuration"))
        return validate_runtime_state(_read_json(state_file, "runtime state file"), repository)

    def read_holds(self, config: AdapterConfig) -> dict[int, str]:
        return validate_holds(_read_json(config.founder_hold_record, "Founder-hold record"))

    def read_inbox(self, config: AdapterConfig, board: dict[int, str] | None = None) -> tuple[tuple[str, ...], frozenset[str]]:
        self.inbox_failures = {}
        reader = self.provenance_reader or (lambda revision, artifact, issue:
            self.read_founder_provenance(config, revision, artifact, issue))
        return read_inbox(config.director_inbox, board, rows=self.last_board_rows,
                          provenance_reader=reader, failures=self.inbox_failures)

    def read_pause(self, config: AdapterConfig) -> bool:
        try:
            os.lstat(config.pause_flag)
            return True
        except FileNotFoundError:
            return False
        except OSError as exc:  # unreadable is not "not paused"
            raise SourceUnavailable(f"pause flag cannot be checked: {exc}") from exc

    def read_assessed(self, board: dict[int, str], config: AdapterConfig) -> dict[int, str]:
        assessed: dict[int, str] = {}
        for issue in sorted(issue for issue, state in board.items() if state == "TASKS"):
            try:
                bodies = self.comments_reader(issue) if self.comments_reader is not None else self.app_reader(config).comments(issue)
            except SourceUnavailable:
                raise
            except Exception as exc:
                raise SourceUnavailable(f"issue #{issue} comments read failed: {exc}"[:300]) from exc
            disposition = retained_assessment_disposition(bodies, issue, self.operators)
            if disposition is not None:
                assessed[issue] = disposition
        return assessed

    def evaluate(self) -> Evaluation:
        try:
            config = load_adapter_config(self.host_config)
            runtime = self.read_runtime(config)
            holds = self.read_holds(config)
            paused = self.read_pause(config)
            board = self.read_board(config)
            unprocessed, acknowledgements = self.read_inbox(config, board)
            assessed = self.read_assessed(board, config)
            evaluation = derive(board, runtime, holds, unprocessed, assessed, paused, config.wip_limit,
                                acknowledgements, biu_issues=self.last_biu_issues,
                                prepared_buffer_target=config.prepared_buffer_target)
            evaluation.observations["foreignProjectItems"] = list(self.last_foreign_project_items)
            evaluation.observations["inboxFailures"] = self.inbox_failures
            return evaluation
        except SourceUnavailable as exc:
            return Evaluation(UNAVAILABLE, str(exc))
        except Exception as exc:  # anything unexpected is also not authoritative
            return Evaluation(UNAVAILABLE, f"adapter error: {type(exc).__name__}: {exc}"[:300])

    def publish(self, evaluation: Evaluation) -> None:
        if self.projection is None:
            return
        _atomic_json(self.projection, asdict(evaluation.inputs))
        _atomic_json(self.projection.with_name(self.projection.stem + ".diagnostics.json"),
                     {"at": _now(), "failure": evaluation.failure,
                      "observations": evaluation.observations})

    def __call__(self) -> DirectorInputs:
        evaluation = self.evaluate()
        self.last_failure = evaluation.failure  # the host records the cause with the refusal
        self.last_fingerprint = evaluation.fingerprint
        self.publish(evaluation)
        return evaluation.inputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="read-only Factory Director predicate adapter")
    parser.add_argument("--config", required=True, help="Factory Director Host configuration JSON")
    parser.add_argument("--projection", help="write the nine-boolean projection atomically here")
    args = parser.parse_args(argv)
    adapter = AuthoritativeDirectorInputs(args.config, args.projection)
    evaluation = adapter.evaluate()
    adapter.publish(evaluation)
    print(json.dumps({"inputs": asdict(evaluation.inputs), "failure": evaluation.failure,
                      "observations": evaluation.observations}, indent=2, sort_keys=True))
    return 0 if evaluation.inputs.authoritative_state else 1


if __name__ == "__main__":
    raise SystemExit(main())
