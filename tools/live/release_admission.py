#!/usr/bin/env python3
"""Release admission preconditions for READY -> IMPLEMENT (SWF-21, SWF-35, SF-REQ-002).

Deterministic gate, not judgment: it answers whether structured state admits a READY BIU to
IMPLEMENT before any worker is launched. It never decides that work should be released: the
nine SWF-21 conditions, SWF-35's standing grant and Agent-Ready still govern that.

    python3 release_admission.py 55            # check a BIU Issue against live state

Exit 0 admits; exit 1 prints each failed check and why.

Authority is structural, never a phrase in a comment (SF-REQ-002 amendment 2026-09-29). The
Agent-Ready disposition has one reader, `agent_ready_receipt`, shared with the Factory Director
inputs adapter: the newest native Agent Ready receipt on the Issue, posted and not edited by an
authorized operator. That receipt is bound to the task packet it assessed: its input digest must
equal the digest of the BIU's work-unit document at the release point, so an edited packet needs
a fresh assessment. The exact baseline is the one the BIU's execution packet names, and it must
resolve and be reachable from the release point.

Work-unit documents and execution packets are read from the release point (`git show
<release-point>:<path>`, default origin/main), never from a working tree: a record landed on
origin/main but absent from the shared checkout was invisible to the gate (Issue #83). The
repository is derived, not hard-coded: ALIENINTENT_WORKDIR if set, else the checkout holding
this file, else the checkout holding the current directory.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

REPO = "AlienLogicLab/alienintent"
WORKDIR_ENV = "ALIENINTENT_WORKDIR"
STATE = Path.home() / ".local/state/alienintent/state.json"
HOST_CONFIG = Path.home() / ".config/alienintent/factory-director-host.json"
PROJECT_ID = "PVT_kwDOEcrpC84Bj5i_"
PRIORITY_FIELD = "PVTSSF_lADOEcrpC84Bj5i_zhiy9vQ"
PRIORITY_OPTIONS = {"P0":"92998478","P1":"ae42b437","P2":"1da6e4a3","P3":"f10b964a","P4":"65e330b9","P5":"c29e1f42"}

UNAUTHORIZED_WORDING = re.compile(r"implementation is\s+\*{0,2}not\*{0,2}\s+authorized", re.I)
SUPERSEDING_WORDING = re.compile(r"\bRELEASED\b.*\bauthoriz", re.I)
NATIVE_RECEIPT = re.compile(r"<!--\s*AGENT_READY_ASSESSMENT:(.*?)-->", re.S)
AGENT_READY_DISPOSITIONS = frozenset({"READY", "CLARIFY", "SPLIT", "HOLD"})
# A work-unit identifier is one path segment: letters, digits and hyphens (WO-220611, PY-09B,
# SF-REQ-057). Anything else (a slash, `..`, a dot) never names a document.
WORK_UNIT_ID = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+")
WORK_UNIT_DIRS = ("docs/work-units/wave2", "docs/work-units/python", "docs/work-units")
PACKET_DIR = "docs/evidence/wave2-execution-packets"
SHA = re.compile(r"[0-9a-f]{7,40}")


def admit(facts: dict) -> list[dict]:
    """Return the failed checks. Empty list means the BIU is admissible."""
    failures = []

    def fail(check, why):
        failures.append({"check": check, "why": why})

    if facts.get("status") != "READY":
        fail("status_ready", f"Project status is {facts.get('status')!r}; release starts from READY.")
    if facts.get("agent_ready") != "READY":
        unreadable = facts.get("agent_ready_unreadable")
        fail("agent_ready", f"Agent-Ready disposition is {facts.get('agent_ready')!r}, not READY"
             + (f" ({unreadable})." if unreadable else "."))

    receipt = facts.get("receipt") or {}
    unit = receipt.get("work_unit_id")
    if not unit:
        fail("receipt_bound", "No native Agent Ready receipt names the work unit it assessed.")
    elif not facts.get("work_unit_sha256"):
        fail("receipt_bound", f"Work unit {unit} has no document at the release point, so its "
             "READY receipt cannot be bound to a task packet.")
    elif facts["work_unit_sha256"] != receipt.get("input_sha256"):
        fail("receipt_bound", f"Work unit {unit} changed after its newest Agent Ready assessment "
             f"(document {facts['work_unit_sha256'][:12]}, assessed {str(receipt.get('input_sha256'))[:12]}). "
             "A fresh assessment of the current packet is required (SWF-35).")

    baseline = facts.get("baseline")
    if not baseline:
        fail("baseline_named", f"The execution packet for {unit or 'this BIU'} does not name an "
             "exact baseline revision.")
    elif not facts.get("baseline_resolves"):
        fail("baseline_resolves", f"Baseline {baseline} does not resolve to a real repository revision.")
    elif not facts.get("baseline_ancestral"):
        fail("baseline_ancestral", f"Baseline {baseline} is not reachable from the intended release point.")

    body = facts.get("body") or ""
    if UNAUTHORIZED_WORDING.search(body) and not SUPERSEDING_WORDING.search(body):
        fail("authority_wording_consistent",
             "The Issue still states implementation is not authorized, with no superseding release statement. "
             "A producer reading it will correctly refuse.")

    if facts.get("open_dependencies"):
        fail("dependencies_satisfied", f"Open dependencies: {facts['open_dependencies']}.")
    if facts.get("active_invocations"):
        fail("no_active_invocation", f"An invocation already exists: {facts['active_invocations']}.")
    if facts.get("held"):
        fail("not_held", "The BIU is explicitly held.")

    wip_limit = facts.get("wip_limit")
    active_total = facts.get("active_claims_total")
    if wip_limit is None:
        fail("wip_limit_known", "wipLimit could not be read from the host configuration; "
             "admitting without it could silently exceed the concurrency policy.")
    elif active_total is None:
        fail("wip_capacity_known", "The current total active-claim count could not be read from "
             "the runtime state file.")
    elif active_total >= wip_limit:
        fail("wip_capacity_available",
             f"{active_total} claim(s) are already active against a wipLimit of {wip_limit}. "
             "Admitting this release would exceed the configured concurrency policy, regardless "
             "of whether this specific Issue has its own active invocation.")

    priority = facts.get("priority_reconciliation") or {}
    if priority.get("status") in {"UNAVAILABLE", "UNRESOLVED"}:
        fail("priority_inheritance_reconciled",
             f"BIU priority could not be deterministically reconciled: {priority}.")

    return failures


# --- live fact gathering -------------------------------------------------------


def repository_root() -> str | None:
    """The repository whose release point the gate reads. An explicit ALIENINTENT_WORKDIR
    wins outright; otherwise the checkout holding this file, then the one holding the current
    directory, so a live copy outside the repository still works when run from inside it."""
    override = os.environ.get(WORKDIR_ENV)
    for where in [override] if override else [str(Path(__file__).resolve().parent), os.getcwd()]:
        try:
            top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=where,
                                 capture_output=True, text=True)
        except OSError:
            continue
        if top.returncode == 0 and top.stdout.strip():
            return top.stdout.strip()
    return None


def _git(root, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def _gh_json(root, *args):
    out = subprocess.run(["gh", *args], cwd=root, capture_output=True, text=True).stdout
    return json.loads(out) if out.strip() else {}


def _parent_issue_number(root: str, issue: int) -> int | None:
    owner, name = REPO.split("/")
    query = ("query($owner:String!,$name:String!,$issue:Int!){repository(owner:$owner,name:$name)"
             "{issue(number:$issue){parent{number}}}}")
    payload = _gh_json(root, "api", "graphql", "-f", f"query={query}",
                       "-F", f"owner={owner}", "-F", f"name={name}", "-F", f"issue={issue}")
    parent = (((payload.get("data") or {}).get("repository") or {}).get("issue") or {}).get("parent")
    number = parent.get("number") if isinstance(parent, dict) else None
    return number if isinstance(number, int) else None


def reconcile_inherited_priority(root: str, issue: int, items: list[dict]) -> dict:
    """Repair deterministic child Priority drift from its native parent requirement.

    No model chooses the value. If the child already matches, this is read-only.
    If a parent exists and the child is blank/drifted, copy the parent's Project
    Priority, then independently read the Project back. Missing/ambiguous parent
    evidence is never guessed.
    """
    child = next((row for row in items if (row.get("content") or {}).get("number") == issue), None)
    if not child:
        return {"status": "UNAVAILABLE", "reason": "child-not-on-project"}

    parent_issue = _parent_issue_number(root, issue)
    if parent_issue is None:
        if child.get("priority") in PRIORITY_OPTIONS:
            return {"status": "UNCHANGED_NO_PARENT", "priority": child.get("priority")}
        return {"status": "UNRESOLVED", "reason": "missing-parent-and-priority"}

    parent = next((row for row in items if (row.get("content") or {}).get("number") == parent_issue), None)
    if not parent:
        return {"status": "UNRESOLVED", "reason": "parent-not-on-project", "parent_issue": parent_issue}
    expected = parent.get("priority")
    if expected not in PRIORITY_OPTIONS:
        return {"status": "UNRESOLVED", "reason": "parent-priority-invalid", "parent_issue": parent_issue}

    if child.get("priority") == expected:
        return {"status": "ALREADY_MATCHED", "priority": expected, "parent_issue": parent_issue}

    subprocess.run(
        ["gh", "project", "item-edit", "--id", child["id"], "--project-id", PROJECT_ID,
         "--field-id", PRIORITY_FIELD, "--single-select-option-id", PRIORITY_OPTIONS[expected]],
        cwd=root, check=True, capture_output=True, text=True,
    )
    refreshed = _gh_json(root, "project", "item-list", "1", "--owner", "AlienLogicLab",
                         "--format", "json", "-L", "500").get("items", [])
    observed = next((row.get("priority") for row in refreshed
                     if (row.get("content") or {}).get("number") == issue), None)
    if observed != expected:
        return {"status": "UNRESOLVED", "reason": "priority-readback-mismatch",
                "parent_issue": parent_issue, "expected": expected, "observed": observed}
    return {"status": "REPAIRED", "priority": expected, "parent_issue": parent_issue}


def refresh_release_point(root, release_point: str) -> bool | None:
    """Fetch a remote-tracking release point before reading it: a stale origin/main in the
    shared checkout hides a newly landed record exactly as the working tree did. None when
    the release point is not `<remote>/<branch>`; otherwise whether the fetch succeeded. A
    failed fetch is reported, not fatal: the gate then reads the local ref as it stands.
    Neither part may start with `-`: `git fetch` would take it as an option."""
    remote, _, branch = release_point.partition("/")
    if not branch or remote.startswith("-") or branch.startswith("-"):
        return None
    if _git(root, "remote", "get-url", remote).returncode != 0:
        return None
    return _git(root, "fetch", "--quiet", remote, branch).returncode == 0


def read_at_release_point(root, commit: str | None, path: PurePosixPath) -> bytes | None:
    """The committed bytes of `path` at the release point, or None. Never the working tree.
    Bytes, not text: the receipt's input digest is over the document exactly as committed."""
    if not commit:
        return None
    shown = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=root, capture_output=True)
    return shown.stdout if shown.returncode == 0 else None


class MalformedReceipt(ValueError):
    """An operator's Agent Ready marker that cannot be read: fail closed, never skip it."""


def receipt_record(record) -> dict | None:
    """A receipt counts only if the Agent Ready product produced it for a fingerprinted task
    packet: a ReadinessAssessment envelope, outcome ASSESSED, an agent-ready producer, a
    retained input digest and a disposition. A compatible shape is not evidence (Architecture
    Authority amendment (b)); anything else is no receipt."""
    if not isinstance(record, dict) or record.get("record_kind") != "ReadinessAssessment":
        return None
    provenance = record.get("provenance")
    if not isinstance(provenance, dict) or not isinstance(provenance.get("input_sha256"), str) \
            or not provenance["input_sha256"]:
        return None
    if record.get("outcome") != "ASSESSED" or not str(provenance.get("producer", "")).startswith("agent-ready"):
        return None
    disposition = record.get("disposition")
    disposition = disposition.strip().upper() if isinstance(disposition, str) else None
    if disposition not in AGENT_READY_DISPOSITIONS:
        return None
    unit = record.get("work_unit_id")
    return {"disposition": disposition, "input_sha256": provenance["input_sha256"].lower(),
            "work_unit_id": unit if isinstance(unit, str) and WORK_UNIT_ID.fullmatch(unit) else None}


def agent_ready_receipt(comments: list[dict], operators: frozenset[str]) -> dict | None:
    """The Issue's current Agent Ready receipt: the newest native receipt
    (`<!-- AGENT_READY_ASSESSMENT: {json} -->`) in a comment written, and not edited, by an
    authorized operator. Comments arrive oldest first. This is the only reader: the release gate
    and the Factory Director inputs adapter both call it, so they cannot disagree about the
    disposition. Raises MalformedReceipt for an unparsable operator marker."""
    latest = None
    for comment in comments:
        if not isinstance(comment, dict) or not isinstance(comment.get("body"), str):
            raise MalformedReceipt("comment is malformed")
        author, editor = comment.get("author"), comment.get("editor")
        if not isinstance(author, str) or author.lower() not in operators:
            continue
        if editor is not None and (not isinstance(editor, str) or editor.lower() not in operators):
            continue
        if editor is None and comment.get("lastEditedAt"):
            continue
        for match in NATIVE_RECEIPT.finditer(comment["body"]):
            try:
                record = json.loads(match.group(1).strip())
            except json.JSONDecodeError as exc:
                raise MalformedReceipt("unparsable Agent Ready assessment") from exc
            receipt = receipt_record(record)
            if receipt is not None:
                latest = receipt
    return latest


def agent_ready_disposition(comments: list[dict], operators: frozenset[str]) -> str | None:
    """The disposition of `agent_ready_receipt`, or None."""
    receipt = agent_ready_receipt(comments, operators)
    return receipt["disposition"] if receipt else None


def read_operators(host_config: dict) -> frozenset[str]:
    """Authorized operator logins, from the same self-hosting configuration the Factory
    Director reads (`operator.authorizedGithubLogins`)."""
    raw = json.loads(Path(host_config["selfHostingConfig"]).read_text())
    logins = (raw.get("operator") or {}).get("authorizedGithubLogins")
    if not isinstance(logins, list) or not all(isinstance(login, str) and login for login in logins):
        raise ValueError("operator.authorizedGithubLogins is not a list of logins")
    return frozenset(login.lower() for login in logins)


def comments_from_gh(comments: list[dict]) -> list[dict]:
    """`gh issue view` comments in the reader's shape. gh names no editor, so an edited comment
    has an unknown editor and is not counted."""
    return [{"author": (c.get("author") or {}).get("login"), "editor": None,
             "lastEditedAt": "edited" if c.get("includesCreatedEdit") else None,
             "body": c.get("body")} for c in comments if isinstance(c, dict)]


def work_unit_document(unit: str | None, read) -> tuple[PurePosixPath | None, bytes | None]:
    """The work-unit document a receipt assessed, read with `read` at the release point: the
    first of WORK_UNIT_DIRS holding `<unit>.md`. An identifier that is not one plain segment
    names nothing."""
    if not unit or not WORK_UNIT_ID.fullmatch(unit):
        return None, None
    for directory in WORK_UNIT_DIRS:
        path = PurePosixPath(directory) / f"{unit}.md"
        raw = read(path)
        if raw is not None:
            return path, raw
    return None, None


def packet_baseline(unit: str | None, read) -> str | None:
    """The exact baseline the BIU's execution packet names (`starting_authority`
    `admission_baseline_sha`, else `baseline_sha`), read at the release point."""
    if not unit or not WORK_UNIT_ID.fullmatch(unit):
        return None
    raw = read(PurePosixPath(PACKET_DIR) / f"{unit}.packet.json")
    try:
        authority = json.loads(raw).get("starting_authority") if raw is not None else None
    except (json.JSONDecodeError, AttributeError):
        return None
    if not isinstance(authority, dict):
        return None
    for key in ("admission_baseline_sha", "baseline_sha"):
        value = authority.get(key)
        if isinstance(value, str) and SHA.fullmatch(value.strip()):
            return value.strip()
    return None


def gather(issue: int, release_point: str = "origin/main") -> dict:
    root = repository_root()
    fetched = refresh_release_point(root, release_point) if root else None
    rev = _git(root, "rev-parse", "--verify", "--quiet", f"{release_point}^{{commit}}") if root else None
    release_commit = rev.stdout.strip() if rev is not None and rev.returncode == 0 else None

    def read(path):
        return read_at_release_point(root, release_commit, path) if root else None

    data = _gh_json(root, "issue", "view", str(issue), "-R", REPO, "--json", "body,comments,labels,projectItems")
    body = data.get("body", "")

    try:
        host_config = json.loads(HOST_CONFIG.read_text())
    except Exception:
        host_config = {}
    wip_limit = host_config.get("wipLimit") if isinstance(host_config.get("wipLimit"), int) else None

    receipt, unreadable = None, None
    try:
        receipt = agent_ready_receipt(comments_from_gh(data.get("comments") or []),
                                      read_operators(host_config))
    except (MalformedReceipt, OSError, KeyError, TypeError, ValueError) as exc:
        unreadable = f"assessment unreadable: {exc}"[:200]
    unit = (receipt or {}).get("work_unit_id")
    document_path, document = work_unit_document(unit, read)
    baseline = packet_baseline(unit, read)

    resolves = ancestral = False
    if root and baseline:
        resolves = _git(root, "cat-file", "-e", f"{baseline}^{{commit}}").returncode == 0
        if resolves:
            ancestral = _git(root, "merge-base", "--is-ancestor", baseline,
                             release_commit or release_point).returncode == 0

    items = _gh_json(root, "project", "item-list", "1", "--owner", "AlienLogicLab",
                     "--format", "json", "-L", "500").get("items", [])
    priority_reconciliation = reconcile_inherited_priority(root, issue, items)
    if priority_reconciliation.get("status") == "REPAIRED":
        items = _gh_json(root, "project", "item-list", "1", "--owner", "AlienLogicLab",
                         "--format", "json", "-L", "500").get("items", [])
    mine = next((i for i in items if (i.get("content") or {}).get("number") == issue), {})

    blocked_by = _gh_json(root, "api", f"repos/{REPO}/issues/{issue}/dependencies/blocked_by")
    open_deps = [d["number"] for d in (blocked_by if isinstance(blocked_by, list) else [])
                 if d.get("state") != "closed"]

    try:
        all_active = json.loads(STATE.read_text()).get("active", {})
    except Exception:
        all_active = None
    active = [k for k in (all_active or {}) if f"#{issue}:" in k]
    active_claims_total = len(all_active) if all_active is not None else None

    return {
        "issue": issue,
        "status": project_status_from_issue(data) or mine.get("status"),
        "agent_ready": (receipt or {}).get("disposition"),
        "agent_ready_unreadable": unreadable,
        "receipt": receipt,
        "work_unit_path": str(document_path) if document_path else None,
        "work_unit_sha256": hashlib.sha256(document).hexdigest() if document is not None else None,
        "body": body,
        "baseline": baseline,
        "baseline_resolves": resolves,
        "baseline_ancestral": ancestral,
        "open_dependencies": open_deps,
        "active_invocations": active,
        "active_claims_total": active_claims_total,
        "wip_limit": wip_limit,
        "held": any("hold" in l.lower() for l in (data.get("labels") or []) if isinstance(l, str)),
        "repository": root,
        "release_point": release_point,
        "release_commit": release_commit,
        "release_point_fetched": fetched,
        "priority_reconciliation": priority_reconciliation,
    }


def project_status_from_issue(issue: dict) -> str | None:
    """Use the Issue's authoritative Project membership when list transport lags or omits it."""
    statuses = {str((item.get("status") or {}).get("name"))
                for item in (issue.get("projectItems") or [])
                if (item.get("status") or {}).get("name")}
    return next(iter(statuses)) if len(statuses) == 1 else None


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: release_admission.py <issue-number> [release-point]", file=sys.stderr)
        return 2
    issue = int(argv[0])
    facts = gather(issue, argv[1] if len(argv) > 1 else "origin/main")
    fetched = {None: "not a remote ref", True: "fetched", False: "FETCH FAILED; local ref used"}
    print(f"release point {facts['release_point']} -> {facts['release_commit'] or 'UNRESOLVED'} "
          f"({fetched[facts['release_point_fetched']]}) in {facts['repository'] or 'NO REPOSITORY'}",
          file=sys.stderr)
    failures = admit(facts)
    print(f"BIU #{issue}: status={facts['status']} agent_ready={facts['agent_ready']} "
          f"work_unit={facts['work_unit_path']} baseline={facts['baseline']} "
          f"resolves={facts['baseline_resolves']} ancestral={facts['baseline_ancestral']}")
    if not failures:
        print("ADMITTED: READY -> IMPLEMENT may proceed.")
        return 0
    print("REFUSED: do not transition and do not launch a worker.")
    for f in failures:
        print(f"  - {f['check']}: {f['why']}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
