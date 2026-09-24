#!/usr/bin/env python3
"""Release admission preconditions for READY -> IMPLEMENT (SWF-21).

Deterministic gate, not judgment: it answers whether the *record* of a release is complete
and self-consistent before any worker is launched. It never decides that work should be
released — the nine SWF-21 conditions and Agent-Ready still govern that.

    python3 release_admission.py 55            # check a BIU Issue against live state

Exit 0 admits; exit 1 prints each failed check and why.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = "AlienLogicLab/alienintent"
WORKDIR = "/mnt/d/Projects/alienintent"
STATE = Path.home() / ".local/state/alienintent/state.json"

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

    return failures


# --- live fact gathering -------------------------------------------------------


def _git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=WORKDIR, capture_output=True, text=True)


def _gh_json(*args):
    out = subprocess.run(["gh", *args], cwd=WORKDIR, capture_output=True, text=True).stdout
    return json.loads(out) if out.strip() else {}


def release_record_from(body: str, comments: list[dict]) -> dict | None:
    """The newest record that authorizes IMPLEMENT and names a baseline (body or comment)."""
    for text in [c.get("body", "") for c in reversed(comments)] + [body]:
        if AUTHORIZES_IMPLEMENT.search(text) or SUPERSEDING_WORDING.search(text):
            match = BASELINE_IN_RECORD.search(text)
            return {"authorizes_implement": True, "baseline": match.group(1) if match else None}
    return None


def gather(issue: int, release_point: str = "origin/main") -> dict:
    data = _gh_json("issue", "view", str(issue), "-R", REPO, "--json", "body,comments,labels,projectItems")
    body, comments = data.get("body", ""), data.get("comments", [])
    record = release_record_from(body, comments)

    resolves = ancestral = False
    if record and record.get("baseline"):
        baseline = record["baseline"]
        resolves = _git("cat-file", "-e", f"{baseline}^{{commit}}").returncode == 0
        if resolves:
            ancestral = _git("merge-base", "--is-ancestor", baseline, release_point).returncode == 0

    items = _gh_json("project", "item-list", "1", "--owner", "AlienLogicLab",
                     "--format", "json", "-L", "500").get("items", [])
    mine = next((i for i in items if (i.get("content") or {}).get("number") == issue), {})

    blocked_by = _gh_json("api", f"repos/{REPO}/issues/{issue}/dependencies/blocked_by")
    open_deps = [d["number"] for d in (blocked_by if isinstance(blocked_by, list) else [])
                 if d.get("state") != "closed"]

    try:
        active = [k for k in json.loads(STATE.read_text()).get("active", {}) if f"#{issue}:" in k]
    except Exception:
        active = []

    return {
        "issue": issue,
        "status": project_status_from_issue(data) or mine.get("status"),
        "agent_ready": _assessment_disposition(issue, body, comments),
        "body": body,
        "release_record": record,
        "baseline_resolves": resolves,
        "baseline_ancestral": ancestral,
        "open_dependencies": open_deps,
        "active_invocations": active,
        "held": any("hold" in l.lower() for l in (data.get("labels") or []) if isinstance(l, str)),
    }


def biu_from_body(body: str) -> str | None:
    r"""The BIU whose assessment this Issue points at.

    The suffix is not optional decoration: SWF-33 inserted PY-09B under the repository's
    existing convention, and a pattern of `PY-\d\d` silently returned None for it — which
    the gate then reported as a missing assessment for a BIU whose assessment said READY.
    """
    match = re.search(r"(PY-\d\d[A-Z]?|WO-\d{6})\b[^\s]*\.assessment\.json", body or "")
    return match.group(1) if match else None


WAVE2_RECORD = re.compile(r"docs/evidence/wave2-readiness-assessments/(WO-\d{6}\.[^\s)`]*?\.assessment\.json)")


def assessment_record_path(body: str) -> Path | None:
    """Wave 2 (2026-09-22): the retained record is a ReadinessAssessment envelope produced by
    the Agent Ready product, linked from the Issue; Wave 1 records stay where they were."""
    match = WAVE2_RECORD.search(body or "")
    if match:
        return Path(WORKDIR) / "docs/evidence/wave2-readiness-assessments" / match.group(1)
    biu = biu_from_body(body)
    return Path(WORKDIR) / "docs/work-units/python" / f"{biu}.assessment.json" if biu else None


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


def _assessment_disposition(issue: int, body: str, comments: list[dict] | None = None) -> str | None:
    path = assessment_record_path(body)
    if path:
        try:
            return disposition_from_record(json.loads(path.read_text()))
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
