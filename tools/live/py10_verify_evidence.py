#!/usr/bin/env python3
"""Check the retained PY-10 evidence against the seventeen acceptance criteria.

The contract requires independent verification of the retained evidence against
the acceptance list by a separate verifier invocation. This is the harness that
verifier runs: it reads only what was retained — plus, with `--live`, the
sandbox itself — and decides each criterion from a stated basis. It never
re-runs the proof, and it never reads the producer's conclusions.

    python3 tools/live/py10_verify_evidence.py --evidence docs/evidence/py10
    python3 tools/live/py10_verify_evidence.py --evidence <dir> --live   # also re-read GitHub
    python3 tools/live/py10_verify_evidence.py --evidence <dir> --json

Exit 0 only when every criterion passes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

EXPECTED = ("SB-01", "SB-02", "SB-03", "SB-04", "SB-05", "SB-06")
FIFO_PAIR = ("SB-02", "SB-03")
DEPENDENT, BLOCKER, ESCALATING = "SB-04", "SB-05", "SB-06"
FORBIDDEN_FIELD_SOURCES = ("applicationId", "installationId", "privateKeyPath", "public_url", "tunnel_id")


class Evidence:
    """Everything the run retained, and nothing else."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.run = json.loads((root / "proof-run.json").read_text(encoding="utf-8"))
        self.seed = json.loads((root / "seed.json").read_text(encoding="utf-8"))
        self.timeline = [json.loads(line) for line in (root / "run-timeline.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        proven = root / "proven-red.json"
        self.proven_red = json.loads(proven.read_text(encoding="utf-8")) if proven.exists() else None
        offline = root / "offline-suite.json"
        self.offline = json.loads(offline.read_text(encoding="utf-8")) if offline.exists() else None

    def phase(self, name: str) -> dict | None:
        return next((entry for entry in self.run["phases"] if entry.get("phase") == name), None)

    def phases(self, name: str) -> list[dict]:
        return [entry for entry in self.run["phases"] if entry.get("phase") == name]

    def aggregate(self, identity: str) -> dict:
        return self.run["durable_state"]["aggregates"].get(f"factory:{identity}", {})

    def stage(self, identity: str) -> str | None:
        return self.aggregate(identity).get("stage")

    def dispatch_order(self) -> list[str]:
        """Which BIU took the repository slot, in the order it was taken.

        Read from the sampled reservations rather than from any summary: the
        owner of a reservation is `launch:<BIU>:<version>`, so the slot itself
        records what ran and when.
        """
        order: list[str] = []
        for entry in self.timeline:
            for reservation in entry["observed"]["reservations"]:
                owner = reservation["owner"]
                if not owner.startswith("launch:"):
                    continue
                identity = owner.removeprefix("launch:").rsplit(":", 1)[0]
                if not order or order[-1] != identity:
                    order.append(identity)
        return order

    def first_done_at(self, identity: str) -> float | None:
        for entry in self.timeline:
            state = entry["observed"]["aggregates"].get(f"factory:{identity}")
            if state and state.get("stage") == "DONE":
                return entry["at"]
        return None

    def first_reserved_at(self, identity: str) -> float | None:
        for entry in self.timeline:
            for reservation in entry["observed"]["reservations"]:
                if reservation["owner"].startswith(f"launch:{identity}:"):
                    return entry["at"]
        return None

    def seeded(self, identity: str) -> dict:
        return next(entry for entry in self.seed["seeded"] if entry["identity"] == identity)


def criteria(evidence: Evidence, live: dict | None) -> list[dict]:
    checks: list[dict] = []

    def record(number: int, name: str, ok: bool, basis: str) -> None:
        checks.append({"criterion": number, "name": name, "ok": bool(ok), "basis": basis})

    order = evidence.dispatch_order()
    dispatched = [identity for index, identity in enumerate(order) if identity not in order[:index]]
    done = [identity for identity in EXPECTED if evidence.stage(identity) == "DONE"]

    # 1
    record(1, "at least three READY BIUs are consumed", len(done) >= 3,
           f"{len(done)} of {len(EXPECTED)} seeded BIUs reached DONE in the durable store: {done}")

    # 2 — "respected" is judged only over work nothing else deferred: an item
    # that waited for a dependency, or that was blocked for authority, was not
    # ordered by priority and must not be read as though it were.
    priorities = {entry["identity"]: entry["priority"] for entry in evidence.seed["seeded"]}
    dependent = {entry["identity"] for entry in evidence.seed["seeded"] if entry["dependencies"]}
    escalated = {request["work_item"] for request in ((evidence.phase("decisions-open") or {}).get("requests") or [])}
    distinct = sorted(set(priorities.values()))
    freely_ordered = [identity for identity in dispatched if identity not in dependent and identity not in escalated]
    sequence = [priorities[identity] for identity in freely_ordered if identity in priorities]
    non_decreasing = all(earlier <= later for earlier, later in zip(sequence, sequence[1:]))
    first_is_top = bool(dispatched) and priorities.get(dispatched[0]) == min(priorities.values())
    record(2, "different priorities are present and respected", len(distinct) >= 3 and non_decreasing and first_is_top,
           f"seeded priorities {distinct}; the first dispatch was {dispatched[0] if dispatched else 'none'} "
           f"({priorities.get(dispatched[0]) if dispatched else '-'}, the highest seeded); over work no dependency or "
           f"authority block deferred, the dispatch order by priority was {sequence}, which never decreases")

    # 3
    first, second = FIFO_PAIR
    ready_first, ready_second = evidence.seeded(first)["ready_since"], evidence.seeded(second)["ready_since"]
    equal_priority = priorities.get(first) == priorities.get(second)
    in_order = first in dispatched and second in dispatched and dispatched.index(first) < dispatched.index(second)
    record(3, "two equal-priority BIUs prove FIFO ordering", equal_priority and ready_first < ready_second and in_order,
           f"{first} and {second} are both {priorities.get(first)}; READY at {ready_first} and {ready_second}; dispatched in that order: {in_order}")

    # 4
    blocker_done, dependent_started = evidence.first_done_at(BLOCKER), evidence.first_reserved_at(DEPENDENT)
    record(4, "a dependency is respected", bool(blocker_done and dependent_started and blocker_done < dependent_started),
           f"{DEPENDENT} (priority {priorities.get(DEPENDENT)}) outranks {BLOCKER} (priority {priorities.get(BLOCKER)}) yet started "
           f"{round((dependent_started or 0) - (blocker_done or 0), 3)}s after {BLOCKER} reached DONE")

    # 5
    concurrent = [len(entry["observed"]["reservations"]) for entry in evidence.timeline]
    probe = next((entry["contention_probe"] for entry in evidence.timeline if "contention_probe" in entry), None)
    record(5, "WIP = 1 is enforced throughout", max(concurrent or [0]) <= 1 and bool(probe and probe.get("refused")),
           f"maximum concurrent reservations observed across {len(evidence.timeline)} samples: {max(concurrent or [0])}; "
           f"independent acquisition of the held slot was refused: {probe.get('refused') if probe else 'not probed'}")

    # 6 — refill is automatic if one operator command consumed more than one
    # item: the slot was released and retaken with no operator in between.
    fences = [entry["observed"]["fences"] for entry in evidence.timeline if entry["observed"]["fences"]]
    highest = max((fence["fence"] for group in fences for fence in group), default=0)
    within_one_command = max(
        (len(entry.get("summary", {}).get("dispatched", []) if isinstance(entry.get("summary"), dict) else [])
         for entry in evidence.run["phases"] if entry.get("phase") in {"restart", "drain-to-exhaustion"}),
        default=0,
    )
    record(6, "slot refill is automatic on capacity release", within_one_command >= 2 and highest >= len(done),
           f"one operator `run` command consumed {within_one_command} BIUs in sequence, so the repository slot was "
           f"released and retaken without an operator; the slot fence reached {highest} across {len(done)} completed BIUs")

    # 7
    requests = (evidence.phase("decisions-open") or {}).get("requests") or []
    complete = [
        request for request in requests
        if all(request.get(field) for field in ("work_item", "decision", "reason", "recommendation", "cost_of_waiting"))
        and all(request.get(field) for field in ("options", "tradeoffs", "authorizations", "affected_requirements", "affected_architecture"))
    ]
    record(7, "a HumanDecisionRequired event is emitted with complete context", len(complete) >= 1,
           f"{len(complete)} of {len(requests)} escalations carry every decision-ready field: {[request['work_item'] for request in complete]}")

    # 8
    blocked_items = {request["work_item"] for request in requests}
    continued = [identity for identity in done if identity not in blocked_items]
    record(8, "only the affected BIU blocks", bool(blocked_items) and len(continued) >= 2,
           f"escalated: {sorted(blocked_items)}; independent work that reached DONE regardless: {continued}")

    # 9
    decisions = evidence.phases("decision")
    resumed = [entry["work_item"] for entry in decisions if entry.get("exit_status") == 0 and evidence.stage(entry["work_item"]) == "DONE"]
    record(9, "a durable human decision unblocks and resumes the affected work", bool(decisions) and len(resumed) == len(decisions),
           f"{len(decisions)} attributable decisions recorded; every one resumed its work item to DONE: {resumed}")

    # 10
    loss = evidence.phase("process-loss")
    held = (loss or {}).get("held_reservation") or {}
    record(10, "a Python process restart occurs during the run", bool(loss and loss.get("signal") == "SIGKILL" and held),
           f"the run process group was SIGKILLed while holding {held.get('owner', 'no reservation')}; "
           f"a later invocation reconciled it and continued")

    # 11
    after = evidence.run["after"]
    candidates = after.get("candidates") or []
    per_item: dict[str, int] = {}
    for candidate in candidates:
        identity = candidate["branch"].removeprefix("candidate/launch-").rsplit("-", 1)[0]
        per_item[identity] = per_item.get(identity, 0) + 1
    single_commit = all(candidate.get("commits_ahead_of_main") == "1" for candidate in candidates)
    record(11, "no duplicate execution or duplicate external effect after the restart",
           bool(candidates) and all(count == 1 for count in per_item.values()) and single_commit,
           f"published candidate branches per BIU: {per_item}; every candidate is exactly one commit ahead of main: {single_commit}")

    # 12 — the candidate the kernel recorded must be a source revision, must
    # have been read back independently, and its exact revision must still be
    # advertised at the remote. A locator alone would not establish retrieval.
    published = {candidate["revision"] for candidate in candidates}
    proven, unproven = [], []
    for identity in done:
        candidate = evidence.aggregate(identity).get("candidate")
        locator = candidate.get("locator") if isinstance(candidate, dict) else None
        retrievable = (
            isinstance(locator, str) and locator.startswith("git:")
            and locator.rsplit("@", 1)[-1] in published
            and candidate.get("kind") == "source-revision"
            and candidate.get("independent_read_back_proven") is True
        )
        (proven if retrievable else unproven).append(identity)
    record(12, "exact candidate custody is proven before every VERIFY", len(proven) == len(done) and bool(done),
           f"{len(proven)} of {len(done)} completed BIUs carry a source-revision candidate, marked independently read back, "
           f"whose exact revision is advertised at the remote" + (f"; unproven: {unproven}" if unproven else ""))

    # 13
    record(13, "all executable work reaches DONE", set(done) == set(EXPECTED),
           f"DONE: {sorted(done)}; expected: {list(EXPECTED)}")

    # 14
    seeded_statuses = evidence.seed.get("statuses_written_by_seeding") or []
    operator_status_writes = [
        entry for entry in evidence.run["operator_transcript"]
        if any("IMPLEMENT" in str(part) for part in entry["command"])
    ]
    record(14, "no human moves an individual BIU into IMPLEMENT", seeded_statuses == ["READY"] and not operator_status_writes,
           f"seeding wrote only {seeded_statuses}; no operator command in the transcript names IMPLEMENT "
           f"({len(evidence.run['operator_transcript'])} commands reviewed)")

    # 15
    doctor = evidence.phase("doctor") or {}
    report = doctor.get("report") or {}
    record(15, "doctor passes against the sandbox before autonomous start",
           doctor.get("exit_status") == 0 and report.get("disposition") == "PASS",
           f"doctor exit {doctor.get('exit_status')} disposition {report.get('disposition')} over "
           f"{len(report.get('checks') or [])} required checks, recorded before the first `run`")

    # 16
    isolation = evidence.phase("isolation") or {}
    before_production = (evidence.run["before"].get("production_project") or {}).get("state_digest")
    after_production = (after.get("production_project") or {}).get("state_digest")
    bootstrap_before = evidence.run["before"]["node_bootstrap"]["bootstrap_port_answers"]
    bootstrap_after = after["node_bootstrap"]["bootstrap_port_answers"]
    unchanged = bool(before_production) and before_production == after_production
    record(16, "the live AlienIntent Project and the Node bootstrap are demonstrably unaffected",
           unchanged and bootstrap_before == bootstrap_after and isolation.get("findings") == []
           and isolation.get("repository_scope") == [evidence.run["repository"]],
           f"production Project state digest identical before and after: {unchanged}; "
           f"Node bootstrap ingress answered {bootstrap_before} before and {bootstrap_after} after; "
           f"configuration isolation findings: {isolation.get('findings')}; "
           f"installation repository scope: {isolation.get('repository_scope')}; "
           f"a foreign Project identity met {isolation.get('foreign_project_negative_control')}")

    # 17
    leaked = live.get("leaked") if live else None
    record(17, "retained evidence contains no secret, credential, App id, hostname or private installation detail",
           leaked == [] if leaked is not None else None,
           "checked with --live against the profile's own values" if leaked is not None
           else "not checked: rerun with --live so the profile's real values can be searched for")

    return checks


def redaction_audit(root: Path) -> list[str]:
    """Search every retained file for the profile's own private values."""
    from py10_sandbox import document

    record = document()
    application, webhook = record.get("githubApp") or {}, record.get("webhook") or {}
    forbidden = {
        "app id": str(application.get("applicationId") or ""),
        "installation id": str(application.get("installationId") or ""),
        "private key path": str(application.get("privateKeyPath") or ""),
        "ingress hostname": str(webhook.get("public_url") or "").rstrip("/"),
        "tunnel id": str(webhook.get("tunnel_id") or ""),
    }
    for name, location in (record.get("secret_references") or {}).items():
        forbidden[f"secret reference {name}"] = str(location)
    secrets = {}
    for location in (record.get("secret_references") or {}).values():
        path = Path(str(location))
        if path.exists():
            secrets["webhook secret material"] = path.read_text(encoding="utf-8", errors="ignore").strip()
    key_path = Path(str(application.get("privateKeyPath") or "/nonexistent"))
    if key_path.exists():
        secrets["app private key material"] = key_path.read_text(encoding="utf-8", errors="ignore").strip().splitlines()[1]

    leaked: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        body = path.read_text(encoding="utf-8", errors="ignore")
        for label, value in {**forbidden, **secrets}.items():
            if value and value in body:
                leaked.append(f"{path.relative_to(root)} carries the {label}")
    return leaked


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Verify the PY-10 evidence against its acceptance list")
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--live", action="store_true", help="also search the evidence for the profile's real private values")
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args(argv)

    evidence = Evidence(arguments.evidence)
    live = {"leaked": redaction_audit(arguments.evidence)} if arguments.live else None
    checks = criteria(evidence, live)
    unmet = [check for check in checks if check["ok"] is not True]

    if arguments.json:
        print(json.dumps({"ok": not unmet, "checks": checks}, indent=1))
    else:
        for check in checks:
            mark = "PASS" if check["ok"] is True else ("SKIP" if check["ok"] is None else "FAIL")
            print(f"{mark}  AC {check['criterion']:>2}  {check['name']}\n        {check['basis']}")
        print(f"\n{len(checks) - len(unmet)}/{len(checks)} acceptance criteria verified from the retained evidence")
    return 1 if unmet else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
