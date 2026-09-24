#!/usr/bin/env python3
"""Authoritative, read-only predicate adapter for the Factory Director Host (FDH-01).

The adapter reads only durable sources and derives the host's nine-boolean
``DirectorInputs`` projection with the mapping fixed by
``docs/work-units/wave2/FDH-01.md``:

* GitHub Project #1, through the fail-closed read path in
  ``tools/live/project_materialization.py`` (complete board, one item per Issue,
  no non-Issue items), plus Issue comments for retained Agent Ready assessments;
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
import json
import os
import re
import shutil
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "live"))

import project_materialization as materialization  # noqa: E402
from factory_director_host import DirectorInputs  # noqa: E402

HOST_CONFIG_SCHEMA_VERSION = 1
HOLD_RECORD_SCHEMA_VERSION = 1
LIFECYCLE_STATES = frozenset(materialization.STATUS_OPTIONS)
WORKER_STATES = frozenset({"IMPLEMENT", "VERIFY", "ACCEPT"})
ASSESSMENT_MARKER = re.compile(r"<!--\s*AGENT_READY_ASSESSMENT:(.*?)-->", re.DOTALL)
INBOX_ENTRY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.json$")
HOLD_KEYS = frozenset({"issue", "reason"})
HOLD_OPTIONAL_KEYS = frozenset({"recordedAt", "recordedBy"})

UNAVAILABLE = DirectorInputs(False, False, False, False, False, False, False, False, False)


class SourceUnavailable(Exception):
    """A durable source is absent, unreadable, partial or inconsistent."""


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


def load_adapter_config(path: Path | str) -> AdapterConfig:
    raw = _read_json(Path(path), "host configuration")
    if not isinstance(raw, dict) or raw.get("schemaVersion") != HOST_CONFIG_SCHEMA_VERSION:
        raise SourceUnavailable("host configuration schemaVersion is not 1")
    if not _positive_int(raw.get("wipLimit")):
        raise SourceUnavailable("host configuration wipLimit must be a positive integer")
    return AdapterConfig(
        self_hosting_config=_absolute_path(raw.get("selfHostingConfig"), "selfHostingConfig"),
        founder_hold_record=_absolute_path(raw.get("founderHoldRecord"), "founderHoldRecord"),
        pause_flag=_absolute_path(raw.get("pauseFlag"), "pauseFlag"),
        director_inbox=_absolute_path(raw.get("directorInbox"), "directorInbox"),
        wip_limit=raw["wipLimit"],
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

def validate_board(rows) -> dict[int, str]:
    """Issue number -> lifecycle state; the whole board or nothing."""
    if not isinstance(rows, list):
        raise SourceUnavailable("Project board is not a list of items")
    board: dict[int, str] = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("type") != "ISSUE":
            raise SourceUnavailable(f"non-Issue item on the Project: {row!r}"[:240])
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
    return board


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
                or not isinstance(hold["reason"], str) or not hold["reason"].strip()):
            raise SourceUnavailable(f"Founder-hold entry is malformed: {hold!r}"[:240])
        if hold["issue"] in holds:
            raise SourceUnavailable(f"Founder-hold record lists issue #{hold['issue']} twice")
        holds[hold["issue"]] = hold["reason"]
    return holds


def _ids(directory: Path) -> frozenset[str]:
    return frozenset(path.stem for path in directory.iterdir() if path.is_file() and INBOX_ENTRY.match(path.name))


def read_inbox(inbox: Path) -> tuple[tuple[str, ...], frozenset[str]]:
    """Unprocessed entry ids (``<id>.json`` with no ``processed/<id>.json``) and the escalation
    acknowledgement ids in ``escalations/``.

    A visible ``*.json`` file whose name is not a valid entry id fails closed rather than
    being silently ignored; dot-files and non-``.json`` names (temporary files) are not entries.
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
    return tuple(sorted(entries - receipts)), acknowledgements


def has_retained_assessment(comments: list[dict], issue: int, operators: frozenset[str]) -> bool:
    """A marker counts only in a comment by an authorized operator (self-hosting ``operator``).

    Markers from anyone else are not a source at all, so quoting the format cannot mark an
    Issue assessed or take the factory out of authoritative state.
    """
    found = False
    for comment in comments:
        if not isinstance(comment, dict) or not isinstance(comment.get("body"), str):
            raise SourceUnavailable(f"issue #{issue} comment is malformed")
        author, editor = comment.get("author"), comment.get("editor")
        if not isinstance(author, str) or author.lower() not in operators:
            continue
        if editor is not None and (not isinstance(editor, str) or editor.lower() not in operators):
            continue  # an operator's comment rewritten by someone else is no longer the operator's
        if editor is None and comment.get("lastEditedAt"):
            continue  # edited by an account GitHub no longer names: provenance unknown
        for match in ASSESSMENT_MARKER.finditer(comment["body"]):
            try:
                record = json.loads(match.group(1).strip())
            except json.JSONDecodeError as exc:
                raise SourceUnavailable(f"issue #{issue} has an unparsable Agent Ready assessment") from exc
            if not isinstance(record, dict) or not isinstance(record.get("disposition"), str):
                raise SourceUnavailable(f"issue #{issue} has a malformed Agent Ready assessment")
            found = True
    return found


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


def control_reason(issue: int, state: str, claimed: frozenset[int], assessed: set[int]) -> str | None:
    """Why this Issue alone would make Director control required, ignoring holds."""
    if state == "READY":
        return "eligible:READY"
    if state in WORKER_STATES and issue not in claimed:
        return f"eligible:{state}_UNCLAIMED"
    if state == "REVIEW":
        return "selection:REVIEW"
    if state == "TASKS" and issue in assessed:
        return "selection:TASKS_ASSESSED"
    return None


def derive(board: dict[int, str], runtime: RuntimeView, holds: dict[int, str],
           unprocessed: tuple[str, ...], assessed: set[int], paused: bool, wip_limit: int,
           acknowledgements: frozenset[str] = frozenset()) -> Evaluation:
    reasons = {issue: reason for issue, state in board.items()
               if (reason := control_reason(issue, state, runtime.claimed_issues, assessed))}
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
        "controlRequiredBy": {str(k): v for k, v in sorted(unheld.items())},
        "heldControl": {str(k): v for k, v in sorted(held.items())},
        "unresolvedLimitEscalations": list(escalations),
        "escalationReceiptIds": {key: escalation_receipt_id(key, entry) for key, entry in runtime.escalations},
        "founderExceptions": runtime.founder_exceptions,
        "unprocessedInboxEntries": list(unprocessed),
    }
    fingerprint = sha256(json.dumps({
        "board": {str(k): v for k, v in sorted(board.items())}, "holds": sorted(holds),
        "inbox": list(unprocessed), "escalations": list(escalations), "assessed": sorted(assessed),
    }, sort_keys=True).encode()).hexdigest()
    return Evaluation(inputs, None, observations, fingerprint)


class AuthoritativeDirectorInputs:
    """Callable source of ``DirectorInputs`` for the host; publishes each projection atomically."""

    def __init__(self, host_config: Path | str, projection: Path | str | None = None, *,
                 board_reader: Callable[[], list] = materialization.read_board,
                 comments_reader: Callable[[int], list[dict]] = read_issue_comments) -> None:
        self.host_config = Path(host_config)
        self.projection = Path(projection) if projection is not None else None
        self.board_reader, self.comments_reader = board_reader, comments_reader

    # Each reader is a separate method so a negative control can break exactly one source.
    def read_board(self) -> dict[int, str]:
        if self.board_reader is materialization.read_board or self.comments_reader is read_issue_comments:
            require_gh()  # the default readers run gh; injected readers do not
        try:
            return validate_board(self.board_reader())
        except SourceUnavailable:
            raise
        except Exception as exc:  # MaterializationFailed, gh failure, malformed payload
            raise SourceUnavailable(f"Project board read failed: {exc}"[:300]) from exc

    def read_runtime(self, config: AdapterConfig) -> RuntimeView:
        repository, state_file, self.operators = validate_self_hosting(
            _read_json(config.self_hosting_config, "self-hosting configuration"))
        return validate_runtime_state(_read_json(state_file, "runtime state file"), repository)

    def read_holds(self, config: AdapterConfig) -> dict[int, str]:
        return validate_holds(_read_json(config.founder_hold_record, "Founder-hold record"))

    def read_inbox(self, config: AdapterConfig) -> tuple[tuple[str, ...], frozenset[str]]:
        return read_inbox(config.director_inbox)

    def read_pause(self, config: AdapterConfig) -> bool:
        try:
            os.lstat(config.pause_flag)
            return True
        except FileNotFoundError:
            return False
        except OSError as exc:  # unreadable is not "not paused"
            raise SourceUnavailable(f"pause flag cannot be checked: {exc}") from exc

    def read_assessed(self, board: dict[int, str]) -> set[int]:
        assessed = set()
        for issue in sorted(issue for issue, state in board.items() if state == "TASKS"):
            try:
                bodies = self.comments_reader(issue)
            except SourceUnavailable:
                raise
            except Exception as exc:
                raise SourceUnavailable(f"issue #{issue} comments read failed: {exc}"[:300]) from exc
            if has_retained_assessment(bodies, issue, self.operators):
                assessed.add(issue)
        return assessed

    def evaluate(self) -> Evaluation:
        try:
            config = load_adapter_config(self.host_config)
            runtime = self.read_runtime(config)
            holds = self.read_holds(config)
            unprocessed, acknowledgements = self.read_inbox(config)
            paused = self.read_pause(config)
            board = self.read_board()
            assessed = self.read_assessed(board)
            return derive(board, runtime, holds, unprocessed, assessed, paused, config.wip_limit, acknowledgements)
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
