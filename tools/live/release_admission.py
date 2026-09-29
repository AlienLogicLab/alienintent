#!/usr/bin/env python3
"""Release admission preconditions for READY -> IMPLEMENT (SWF-21).

Deterministic gate, not judgment: it answers whether structured state admits a READY BIU to
IMPLEMENT before any worker is launched. It never decides that work should be released — the
nine SWF-21 conditions and Agent-Ready still govern that.

    python3 release_admission.py 55            # check a BIU Issue against live state

Exit 0 admits; exit 1 prints each failed check and why.

The Agent-Ready disposition has one reader, `agent_ready_disposition`, shared with the Factory
Director inputs adapter: the newest native Agent Ready receipt on the Issue, posted and not
edited by an authorized operator. Authority to IMPLEMENT is structural (Project status READY
plus a READY receipt plus the checks below), never a phrase in a comment.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = "AlienLogicLab/alienintent"
STATE = Path.home() / ".local/state/alienintent/state.json"
HOST_CONFIG = Path.home() / ".config/alienintent/factory-director-host.json"
PROJECT_ID = "PVT_kwDOEcrpC84Bj5i_"
PRIORITY_FIELD = "PVTSSF_lADOEcrpC84Bj5i_zhiy9vQ"
PRIORITY_OPTIONS = {"P0":"92998478","P1":"ae42b437","P2":"1da6e4a3","P3":"f10b964a","P4":"65e330b9","P5":"c29e1f42"}

NATIVE_RECEIPT = re.compile(r"<!--\s*AGENT_READY_ASSESSMENT:(.*?)-->", re.S)
AGENT_READY_DISPOSITIONS = frozenset({"READY", "CLARIFY", "SPLIT", "HOLD"})


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


class MalformedReceipt(ValueError):
    """An operator's Agent Ready marker that cannot be read: fail closed, never skip it."""


def receipt_disposition(record) -> str | None:
    """A disposition counts only if the Agent Ready product produced it for a fingerprinted task
    packet: a ReadinessAssessment envelope, outcome ASSESSED, an agent-ready producer and a
    retained input digest. A compatible shape is not evidence (Architecture Authority
    amendment (b)); anything else carries no disposition."""
    if not isinstance(record, dict) or record.get("record_kind") != "ReadinessAssessment":
        return None
    provenance = record.get("provenance")
    if not isinstance(provenance, dict) or not provenance.get("input_sha256"):
        return None
    if record.get("outcome") != "ASSESSED" or not str(provenance.get("producer", "")).startswith("agent-ready"):
        return None
    disposition = record.get("disposition")
    disposition = disposition.strip().upper() if isinstance(disposition, str) else None
    return disposition if disposition in AGENT_READY_DISPOSITIONS else None


def agent_ready_disposition(comments: list[dict], operators: frozenset[str]) -> str | None:
    """The Agent Ready disposition of the Issue's current task packet: the newest native receipt
    (`<!-- AGENT_READY_ASSESSMENT: {json} -->`) in a comment written, and not edited, by an
    authorized operator. Comments arrive oldest first. This is the only reader: the release gate
    and the Factory Director inputs adapter both call it, so they cannot disagree. Records
    cited from an Issue body or a release comment are not consulted; they can be older than the
    newest receipt. Raises MalformedReceipt for an unparsable operator marker."""
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
            disposition = receipt_disposition(record)
            if disposition is not None:
                latest = disposition
    return latest


# --- live fact gathering -------------------------------------------------------


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


def gather(issue: int) -> dict:
    root = None  # gh addresses the repository explicitly (-R); no checkout is read
    data = _gh_json(root, "issue", "view", str(issue), "-R", REPO, "--json", "body,comments,labels,projectItems")

    try:
        host_config = json.loads(HOST_CONFIG.read_text())
    except Exception:
        host_config = {}
    wip_limit = host_config.get("wipLimit") if isinstance(host_config.get("wipLimit"), int) else None

    agent_ready, unreadable = None, None
    try:
        agent_ready = agent_ready_disposition(comments_from_gh(data.get("comments") or []),
                                              read_operators(host_config))
    except (MalformedReceipt, OSError, KeyError, TypeError, ValueError) as exc:
        unreadable = f"assessment unreadable: {exc}"[:200]

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
        "agent_ready": agent_ready,
        "agent_ready_unreadable": unreadable,
        "open_dependencies": open_deps,
        "active_invocations": active,
        "active_claims_total": active_claims_total,
        "wip_limit": wip_limit,
        "held": any("hold" in l.lower() for l in (data.get("labels") or []) if isinstance(l, str)),
        "priority_reconciliation": priority_reconciliation,
    }


def project_status_from_issue(issue: dict) -> str | None:
    """Use the Issue's authoritative Project membership when list transport lags or omits it."""
    statuses = {str((item.get("status") or {}).get("name"))
                for item in (issue.get("projectItems") or [])
                if (item.get("status") or {}).get("name")}
    return next(iter(statuses)) if len(statuses) == 1 else None


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: release_admission.py <issue-number>", file=sys.stderr)
        return 2
    issue = int(argv[0])
    facts = gather(issue)
    failures = admit(facts)
    print(f"BIU #{issue}: status={facts['status']} agent_ready={facts['agent_ready']}")
    if not failures:
        print("ADMITTED: READY -> IMPLEMENT may proceed.")
        return 0
    print("REFUSED: do not transition and do not launch a worker.")
    for f in failures:
        print(f"  - {f['check']}: {f['why']}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
