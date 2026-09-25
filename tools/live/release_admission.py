#!/usr/bin/env python3
"""Release admission preconditions for READY -> IMPLEMENT (SWF-21).

Deterministic gate, not judgment: it answers whether the *record* of a release is complete
and self-consistent before any worker is launched. It never decides that work should be
released — the nine SWF-21 conditions and Agent-Ready still govern that.

    python3 release_admission.py 55            # check a BIU Issue against live state

Exit 0 admits; exit 1 prints each failed check and why.

Readiness records are read from the release point (`git show <release-point>:<path>`, default
origin/main), never from a working tree: a record landed on origin/main but absent from the
shared checkout was invisible to the gate (Issue #83). The repository is derived, not
hard-coded: ALIENINTENT_WORKDIR if set, else the checkout holding this file, else the
checkout holding the current directory.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

REPO = "AlienLogicLab/alienintent"
WORKDIR_ENV = "ALIENINTENT_WORKDIR"
STATE = Path.home() / ".local/state/alienintent/state.json"
PROJECT_ID = "PVT_kwDOEcrpC84Bj5i_"
PRIORITY_FIELD = "PVTSSF_lADOEcrpC84Bj5i_zhiy9vQ"
PRIORITY_OPTIONS = {"P0":"92998478","P1":"ae42b437","P2":"1da6e4a3","P3":"f10b964a","P4":"65e330b9","P5":"c29e1f42"}

UNAUTHORIZED_WORDING = re.compile(r"implementation is\s+\*{0,2}not\*{0,2}\s+authorized", re.I)
SUPERSEDING_WORDING = re.compile(r"\bRELEASED\b.*\bauthoriz", re.I | re.S)
BASELINE_IN_RECORD = re.compile(r"baseline[^`]*`([0-9a-f]{7,40})`", re.I)
AUTHORIZES_IMPLEMENT = re.compile(r"IMPLEMENT is authorized", re.I)


def admit(facts: dict) -> list[dict]:
    """Return the failed checks. Empty list means the release record is admissible."""
    failures = []

    def fail(check, why):
        failures.append({"check": check, "why": why})

    if facts.get("status") != "READY":
        fail("status_ready", f"Project status is {facts.get('status')!r}; release starts from READY.")
    if facts.get("agent_ready") != "READY":
        fail("agent_ready", f"Agent-Ready disposition is {facts.get('agent_ready')!r}, not READY.")

    record = facts.get("release_record")
    if not record or not record.get("authorizes_implement"):
        fail("implementation_authorized",
             "No release record explicitly authorizes IMPLEMENT for this BIU.")
    else:
        if not record.get("baseline"):
            fail("baseline_named", "The release record does not name an exact baseline revision.")
        else:
            if not facts.get("baseline_resolves"):
                fail("baseline_resolves",
                     f"Baseline {record['baseline']} does not resolve to a real repository revision.")
            elif not facts.get("baseline_ancestral"):
                fail("baseline_ancestral",
                     f"Baseline {record['baseline']} is not reachable from the intended release point.")

    body = facts.get("body") or ""
    if UNAUTHORIZED_WORDING.search(body) and not SUPERSEDING_WORDING.search(body):
        fail("authority_wording_consistent",
             "The Issue still states implementation is not authorized, with no superseding release record. "
             "A producer reading it will correctly refuse.")

    if facts.get("open_dependencies"):
        fail("dependencies_satisfied", f"Open dependencies: {facts['open_dependencies']}.")
    if facts.get("active_invocations"):
        fail("no_active_invocation", f"An invocation already exists: {facts['active_invocations']}.")
    if facts.get("held"):
        fail("not_held", "The BIU is explicitly held.")

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


def read_at_release_point(root, commit: str | None, path: PurePosixPath) -> str | None:
    """The committed content of `path` at the release point, or None. Never the working tree."""
    if not commit:
        return None
    shown = _git(root, "show", f"{commit}:{path}")
    return shown.stdout if shown.returncode == 0 else None


def release_record_from(body: str, comments: list[dict]) -> dict | None:
    """The newest record that authorizes IMPLEMENT and names a baseline (body or comment)."""
    for text in [c.get("body", "") for c in reversed(comments)] + [body]:
        if AUTHORIZES_IMPLEMENT.search(text) or SUPERSEDING_WORDING.search(text):
            match = BASELINE_IN_RECORD.search(text)
            return {"authorizes_implement": True, "baseline": match.group(1) if match else None,
                    "text": text}
    return None


def gather(issue: int, release_point: str = "origin/main") -> dict:
    root = repository_root()
    fetched = refresh_release_point(root, release_point) if root else None
    rev = _git(root, "rev-parse", "--verify", "--quiet", f"{release_point}^{{commit}}") if root else None
    release_commit = rev.stdout.strip() if rev is not None and rev.returncode == 0 else None

    data = _gh_json(root, "issue", "view", str(issue), "-R", REPO, "--json", "body,comments,labels,projectItems")
    body, comments = data.get("body", ""), data.get("comments", [])
    record = release_record_from(body, comments)

    resolves = ancestral = False
    if root and record and record.get("baseline"):
        baseline = record["baseline"]
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
        active = [k for k in json.loads(STATE.read_text()).get("active", {}) if f"#{issue}:" in k]
    except Exception:
        active = []

    return {
        "issue": issue,
        "status": project_status_from_issue(data) or mine.get("status"),
        "agent_ready": _assessment_disposition(
            body, comments, (record or {}).get("text"),
            lambda path: read_at_release_point(root, release_commit, path)),
        "body": body,
        "release_record": record,
        "baseline_resolves": resolves,
        "baseline_ancestral": ancestral,
        "open_dependencies": open_deps,
        "active_invocations": active,
        "held": any("hold" in l.lower() for l in (data.get("labels") or []) if isinstance(l, str)),
        "repository": root,
        "release_point": release_point,
        "release_commit": release_commit,
        "release_point_fetched": fetched,
        "priority_reconciliation": priority_reconciliation,
    }


def biu_from_body(body: str) -> str | None:
    r"""The BIU whose assessment this Issue points at.

    The suffix is not optional decoration: SWF-33 inserted PY-09B under the repository's
    existing convention, and a pattern of `PY-\d\d` silently returned None for it — which
    the gate then reported as a missing assessment for a BIU whose assessment said READY.
    """
    match = re.search(r"(PY-\d\d[A-Z]?|WO-\d{6})\b[^\s]*\.assessment\.json", body or "")
    return match.group(1) if match else None


WAVE2_DIR = "docs/evidence/wave2-readiness-assessments"
# `<ID>.<stamp>.assessment.json` directly in WAVE2_DIR, for any BIU identifier (Issue #83: ARP-01
# and FDH-01 fell back to the native receipt). The ID is one segment of letters, digits and
# hyphens; the stamp is dot-separated non-empty segments of the same. Neither can hold `/` or
# `..`, and the path may not be preceded or continued by further path characters, so
# `../docs/...`, `.../<dir>/<ID>...` and `...json/..` are not readiness records.
WAVE2_RECORD = re.compile(
    r"(?<![\w./-])" + re.escape(WAVE2_DIR) + r"/"
    r"([A-Za-z0-9-]+\.[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*?\.assessment\.json)"
    r"(?!\.?[\w/-])")

WAVE1_DIR = "docs/work-units/python"
# A Wave 1 citation names the file `<BIU>.assessment.json` exactly: bare, or under WAVE1_DIR
# (a repository path or a GitHub blob URL). Anything else carrying a PY/WO identifier (a stamped
# Wave 2 name, another directory, a `..` segment) is not a Wave 1 record: reinterpreting a
# rejected Wave 2 citation as `WAVE1_DIR/<BIU>.assessment.json` admitted a record the Issue
# never cited (Issue #83, JC R1).
WAVE1_RECORD = re.compile(
    r"(?<![\w./-])([^\s`'\"()\[\]<>]*/)?(PY-\d\d[A-Z]?|WO-\d{6})\.assessment\.json(?!\.?[\w/-])")
# The directory must be the whole prefix: WAVE1_DIR itself, or a blob URL of this repository at
# a single-segment ref followed by WAVE1_DIR, so no `..` segment can occur. A prefix that merely ends in WAVE1_DIR
# (`docs/evidence/elsewhere/docs/work-units/python/`) names another file (Issue #83, JC R1,
# repair cycle 2).
WAVE1_PREFIX = re.compile(
    r"(?:https://github\.com/" + re.escape(REPO) + r"/blob/[A-Za-z0-9][\w.-]*/)?"
    + re.escape(WAVE1_DIR) + r"/")


def _wave1_biu(body: str) -> str | None:
    for match in WAVE1_RECORD.finditer(body or ""):
        prefix = match.group(1) or ""
        if not prefix or WAVE1_PREFIX.fullmatch(prefix):
            return match.group(2)
    return None


def assessment_record_path(body: str) -> PurePosixPath | None:
    """Wave 2 (2026-09-22): the retained record is a ReadinessAssessment envelope produced by
    the Agent Ready product, linked from the Issue; Wave 1 records stay where they were.
    The path is repository-relative: it is read at the release point, not from a checkout."""
    match = WAVE2_RECORD.search(body or "")
    if match:
        return PurePosixPath(WAVE2_DIR) / match.group(1)
    biu = _wave1_biu(body)
    return PurePosixPath(WAVE1_DIR) / f"{biu}.assessment.json" if biu else None


def disposition_from_record(record: dict) -> str | None:
    """A disposition counts only if the Agent Ready product produced it. A ReadinessAssessment
    envelope whose outcome is not ASSESSED, or whose producer is not Agent Ready, has none —
    a compatible shape is not evidence (Architecture Authority amendment (b))."""
    if record.get("record_kind") == "ReadinessAssessment":
        producer = str((record.get("provenance") or {}).get("producer", ""))
        if record.get("outcome") != "ASSESSED" or not producer.startswith("agent-ready"):
            return None
        return record.get("disposition")
    return record.get("disposition")


def project_status_from_issue(issue: dict) -> str | None:
    """Use the Issue's authoritative Project membership when list transport lags or omits it."""
    statuses = {str((item.get("status") or {}).get("name"))
                for item in (issue.get("projectItems") or [])
                if (item.get("status") or {}).get("name")}
    return next(iter(statuses)) if len(statuses) == 1 else None


NATIVE_COMMENT = re.compile(r"<!--\s*AGENT_READY_ASSESSMENT:\s*(\{.*?\})\s*-->", re.S)


def disposition_from_native_comment(text: str) -> str | None:
    """Accept only a self-identifying native Agent Ready receipt with a retained input digest."""
    match = NATIVE_COMMENT.search(text or "")
    if not match:
        return None
    try:
        record = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    provenance = record.get("provenance") or {}
    if not provenance.get("input_sha256"):
        return None
    return disposition_from_record(record)


def _assessment_disposition(body: str, comments: list[dict] | None = None,
                            release_text: str | None = None, read=lambda path: None) -> str | None:
    """The Issue body's record first (as before), then the release record's; a record counts
    only if `read` finds it at the release point. Otherwise the native receipt, unchanged."""
    for text in (body, release_text):
        path = assessment_record_path(text)
        raw = read(path) if path else None
        if raw is not None:
            try:
                return disposition_from_record(json.loads(raw))
            except Exception:
                pass
    for comment in reversed(comments or []):
        disposition = disposition_from_native_comment(comment.get("body", ""))
        if disposition:
            return disposition
    return None


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
    record = facts.get("release_record") or {}
    print(f"BIU #{issue}: status={facts['status']} agent_ready={facts['agent_ready']} "
          f"baseline={record.get('baseline')} resolves={facts['baseline_resolves']} "
          f"ancestral={facts['baseline_ancestral']}")
    if not failures:
        print("ADMITTED: release record complete; READY -> IMPLEMENT may proceed.")
        return 0
    print("REFUSED: do not transition and do not launch a worker.")
    for f in failures:
        print(f"  - {f['check']}: {f['why']}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
