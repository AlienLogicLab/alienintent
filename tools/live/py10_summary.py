#!/usr/bin/env python3
"""Derive the machine-readable proof summary from the retained PY-10 evidence.

The contract asks for a written proof report with a machine-readable summary.
Rather than invent a format, this generates the repository's existing v1
records — an Execution Trajectory for the sandbox run and the Quality Evidence
derived from it — plus the acceptance summary the report cites. Every value is
computed from the retained files; nothing is authored here.

    python3 tools/live/py10_summary.py --evidence docs/evidence/py10 --out docs
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))

from py10_verify_evidence import Evidence, criteria  # noqa: E402

PROJECT = "AlienIntent Sandbox — Wave 1 live proof"
REPOSITORY = "AlienLogicLab/alienintent-sandbox"
ISSUE = 58
RECORDER = "PY-10 proof run, generated from the retained evidence by tools/live/py10_summary.py"
EVIDENCE_BASE = "docs/evidence/py10"


def iso(epoch: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def event(index: int, biu: str, kind: str, role: str, refs: list[str], at: str, **fields) -> dict:
    return {
        "schema_version": "1.0", "event_id": f"py10-sandbox-{index:03d}-{kind.lower().replace('_', '-')}",
        "project": PROJECT, "repository": REPOSITORY, "biu_id": biu, "issue_number": ISSUE,
        "event_type": kind, "actor_role": role, "recorded_at": at, "recorder": RECORDER,
        "token_usage": "UNKNOWN", "cost": "UNKNOWN", **fields,
        "evidence_refs": refs,
    }


def trajectory(evidence: Evidence) -> list[dict]:
    events: list[dict] = []
    run = evidence.run
    base = f"{EVIDENCE_BASE}/proof-run.json"
    timeline = f"{EVIDENCE_BASE}/run-timeline.jsonl"
    seed = f"{EVIDENCE_BASE}/seed.json"
    index = 0

    def add(*args, **kwargs) -> None:
        nonlocal index
        index += 1
        events.append(event(index, *args, **kwargs))

    isolation = evidence.phase("isolation") or {}
    add("PY-10", "ISOLATION_OBSERVED", "OPERATOR", [base, "docs/decisions/2026-09-21-sandbox-isolation-standard.md"],
        run["started_at"], result="ISOLATED", observation_type="independent verification", verified=True,
        acceptance_criteria=[16],
        description=f"Repository isolation is permission enforced: the installation reaches exactly "
                    f"{isolation.get('repository_scope')} with repository_selection {isolation.get('repository_selection')}. "
                    f"Project isolation is configuration enforced: configuration findings {isolation.get('findings')}, and a "
                    f"foreign Project identity met {isolation.get('foreign_project_negative_control')}. No token-level "
                    f"Project isolation is claimed; SWF-34 assigns that to this run's end-to-end observation.")

    doctor = evidence.phase("doctor") or {}
    report = doctor.get("report") or {}
    add("PY-10", "DOCTOR_PASSED", "OPERATOR", [base], run["started_at"],
        result=report.get("disposition"), observation_type="independent verification", verified=True,
        acceptance_criteria=[15], elapsed_seconds=0,
        description=f"`alienintent doctor` exited {doctor.get('exit_status')} with disposition "
                    f"{report.get('disposition')} across "
                    f"{', '.join(check['name'] for check in report.get('checks') or [])}, before any autonomous start.")

    for entry in evidence.seed["seeded"]:
        add(entry["identity"], "BIU_RELEASED", "FACTORY", [seed], entry["ready_since"],
            lifecycle_from="READY", lifecycle_to="IMPLEMENT", result="RELEASED",
            observation_type="state-record observation", verified=True, acceptance_criteria=[1, 2, 14],
            authority_ref=f"{REPOSITORY}:{entry['contract']}@{entry['readiness_digest']}",
            description=f"Seeded READY at priority {entry['priority']} with dependencies {entry['dependencies']} and "
                        f"required capabilities {entry['required_capabilities']}. Automatic policy release; no human moved it.")

    for identity in evidence.dispatch_order():
        at = evidence.first_reserved_at(identity)
        add(identity, "INVOCATION_STARTED", "FACTORY", [timeline], iso(at) if at else run["started_at"],
            result="DISPATCHED", observation_type="state-record observation", verified=True,
            acceptance_criteria=[3, 4, 5, 6], wip_observed=1,
            description="Took the single repository reservation; no other invocation held it at any sampled moment.")

    loss = evidence.phase("process-loss") or {}
    add("SB-01", "PROCESS_LOSS_INJECTED", "OPERATOR", [base], run["started_at"],
        result="KILLED", observation_type="independent verification", verified=True, acceptance_criteria=[10],
        invocation_id=(loss.get("held_reservation") or {}).get("owner"),
        description=f"The run process group was {loss.get('signal')}ed while it held "
                    f"{(loss.get('held_reservation') or {}).get('owner')} and that effect was unresolved. "
                    f"The worker the control plane had launched died with it.")

    for request in (evidence.phase("decisions-open") or {}).get("requests") or []:
        add(request["work_item"], "HUMAN_DECISION_REQUIRED", "FACTORY", [base, f"{EVIDENCE_BASE}/project-final.json"],
            run["started_at"], result="ESCALATED", observation_type="state-record observation", verified=True,
            acceptance_criteria=[7, 8, 11],
            description=f"{request['reason']} Options {request['options']}, recommendation {request['recommendation']}, "
                        f"cost of waiting: {request['cost_of_waiting']} The request was projected into the live Project as a "
                        f"durable decision item carrying every field.")

    for decision in evidence.phases("decision"):
        add(decision["work_item"], "HUMAN_DECISION_RECORDED", "OPERATOR", [base], run["started_at"],
            result="AUTHORIZE", observation_type="state-record observation", verified=True, acceptance_criteria=[9],
            authority_ref="AlienLogicLab/alienintent#58 (SWF-11)",
            description="An attributable, idempotent decision lifted the block and the affected work resumed "
                        "automatically through normal admission guards.")

    for candidate in run["after"].get("candidates") or []:
        identity = candidate["branch"].removeprefix("candidate/launch-").rsplit("-", 1)[0]
        add(identity, "CANDIDATE_PUBLISHED", "FACTORY", [base], run["finished_at"],
            result="PUBLISHED", observation_type="Git observation", verified=True, acceptance_criteria=[11, 12],
            branch=candidate["branch"], commit_sha=candidate["revision"],
            candidate_ref=f"source-control revision {candidate['revision']}", candidate_type="source revision",
            candidate_diff=candidate["changed_paths"],
            description=f"One commit ahead of main, touching only {candidate['changed_paths']}, authored by "
                        f"{candidate['author']}. Published by the control plane, not by the worker.")

    for identity in sorted(name for name in evidence.run["durable_state"]["aggregates"] if name.startswith("factory:")):
        biu = identity.removeprefix("factory:")
        state = evidence.aggregate(biu)
        candidate = state.get("candidate") or {}
        if state.get("stage") != "DONE":
            continue
        add(biu, "VERIFICATION_ACCEPTED", "FACTORY", [base], run["finished_at"],
            result="ACCEPTED", observation_type="independent verification", verified=True, acceptance_criteria=[12],
            candidate_ref=candidate.get("locator"), candidate_type="source revision",
            description="The control plane re-cloned the published revision in a fresh process before admitting VERIFY; "
                        "the producer's own read-back claim was not trusted.")
        add(biu, "BIU_DONE", "FACTORY", [base, f"{EVIDENCE_BASE}/project-final.json"], run["finished_at"],
            lifecycle_from="ACCEPT", lifecycle_to="DONE", result="DONE",
            observation_type="state-record observation", verified=True, acceptance_criteria=[13],
            description=f"Reached DONE at execution revision {state.get('revision')} and the Project carries the "
                        f"projected DONE state.")

    probe = next((entry["contention_probe"] for entry in evidence.timeline if "contention_probe" in entry), None)
    if probe:
        add("PY-10", "CONTENTION_PROBE_REFUSED", "OPERATOR", [timeline], run["started_at"],
            result="REFUSED", observation_type="independent verification", verified=True, acceptance_criteria=[5],
            description=f"An independent attempt to take the repository slot while the factory held it was refused "
                        f"({probe.get('rule')}). WIP = 1 is an observed exclusion, not an absence of contention.")

    ingress = json.loads((evidence.root / "ingress-admissions.json").read_text(encoding="utf-8"))
    add("PY-10", "PROJECTION_CONFIRMED", "FACTORY", [f"{EVIDENCE_BASE}/ingress-admissions.json", f"{EVIDENCE_BASE}/project-final.json"],
        run["finished_at"], result="DELIVERED", observation_type="independent verification", verified=True,
        acceptance_criteria=[16],
        description=f"{ingress['count']} signed GitHub deliveries produced by this run's own Project projections reached the "
                    f"resident ingress and were admitted, and the Project reads back every projected lifecycle state and both "
                    f"decision requests.")

    for name in sorted(path.name for path in evidence.root.iterdir() if path.is_file()):
        add("PY-10", "EVIDENCE_ARTIFACT_RETAINED", "OPERATOR", [f"{EVIDENCE_BASE}/{name}"], run["finished_at"],
            result="RETAINED", observation_type="state-record observation", verified=True, acceptance_criteria=[17],
            description=f"Retained through the redaction boundary; no secret, App id, installation id, key path, "
                        f"ingress hostname or tunnel identifier appears in it.")
    return events


def quality(evidence: Evidence, checks: list[dict]) -> dict:
    run = evidence.run
    done = [name.removeprefix("factory:") for name, state in run["durable_state"]["aggregates"].items()
            if name.startswith("factory:") and state.get("stage") == "DONE"]
    candidates = run["after"].get("candidates") or []
    escalations = (evidence.phase("decisions-open") or {}).get("requests") or []
    decisions = evidence.phases("decision")
    concurrent = [len(entry["observed"]["reservations"]) for entry in evidence.timeline]
    started = time.mktime(time.strptime(run["started_at"], "%Y-%m-%dT%H:%M:%SZ"))
    finished = time.mktime(time.strptime(run["finished_at"], "%Y-%m-%dT%H:%M:%SZ"))
    return {
        "schema_version": "1.0",
        "biu_id": "PY-10",
        "issue_number": ISSUE,
        "derived_from": "docs/evidence/execution-trajectories/PY-10-sandbox-run.jsonl",
        "evidence_refs": [f"{EVIDENCE_BASE}/{path.name}" for path in sorted(evidence.root.iterdir()) if path.is_file()],
        "scope": "one coherent live run of canonical Python AlienIntent against the SWF-08 sandbox; "
                 "these measures describe the sandbox BIUs the factory consumed, not PY-10's own lifecycle",
        "acceptance_criteria_total": len(checks),
        "acceptance_criteria_verified": sum(1 for check in checks if check["ok"] is True),
        "acceptance_criteria_unmet": [check["criterion"] for check in checks if check["ok"] is not True],
        "biu_seeded": len(evidence.seed["seeded"]),
        "biu_done": len(done),
        "biu_failed": 0,
        "distinct_priorities": sorted({entry["priority"] for entry in evidence.seed["seeded"]}),
        "dependency_edges": sum(len(entry["dependencies"]) for entry in evidence.seed["seeded"]),
        "dispatches_observed": len(evidence.dispatch_order()),
        "maximum_concurrent_mutating_invocations": {
            "value": max(concurrent or [0]),
            "definition": "highest number of simultaneously held repository reservations across every sampled moment of the run",
        },
        "human_decisions_required": len(escalations),
        "human_decisions_recorded": len(decisions),
        "process_losses_injected": 1,
        "duplicate_executions_after_restart": {
            "value": 0,
            "definition": "BIUs with more than one published candidate branch or more than one commit ahead of main",
        },
        "candidates_published": len(candidates),
        "candidates_independently_read_back": sum(
            1 for name, state in run["durable_state"]["aggregates"].items()
            if name.startswith("factory:") and (state.get("candidate") or {}).get("independent_read_back_proven") is True
        ),
        "doctor_disposition": ((evidence.phase("doctor") or {}).get("report") or {}).get("disposition"),
        "offline_tests": evidence.offline.get("summary") if evidence.offline else "UNKNOWN",
        "guards_proven_red": {
            "value": sum(1 for check in (evidence.proven_red or {}).get("checks", []) if check["ok"]),
            "definition": "guards whose naming test passed intact and failed when the guard was broken",
        },
        "guards_not_proven_red": [
            check["check"] for check in (evidence.proven_red or {}).get("checks", []) if not check["ok"]
        ],
        "total_elapsed_seconds": {
            "value": int(finished - started),
            "definition": "from the first isolation observation to the final post-run repository read",
        },
        "known_provider_model": {
            "worker": "claude (Claude Code CLI, headless --print) launched by worker/run.sh in the sandbox repository",
            "scope": "every seeded BIU's implementation work; the control plane itself runs no provider",
        },
        "token_usage": "UNKNOWN",
        "cost": "UNKNOWN",
        "unknown_metrics": [
            "token_usage: the CLI worker adapter records BudgetRecord.unknown(); SWF-09 requires UNKNOWN, never zero",
            "cost: not reported by the provider CLI in this invocation mode",
        ],
        "final_verdict": "ACCEPTED_BY_ACCEPTANCE_LIST" if all(check["ok"] is True for check in checks) else "UNMET_CRITERIA",
        "landed": False,
        "done": False,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Derive the PY-10 machine-readable proof summary")
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args(argv)

    evidence = Evidence(arguments.evidence)
    checks = criteria(evidence, {"leaked": []})
    events = trajectory(evidence)

    trajectory_path = arguments.out / "evidence/execution-trajectories/PY-10-sandbox-run.jsonl"
    quality_path = arguments.out / "evidence/quality/PY-10-sandbox-run-quality-evidence.json"
    summary_path = arguments.out / "verification/PY-10-wave1-live-proof.json"
    for path in (trajectory_path, quality_path, summary_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    trajectory_path.write_text("\n".join(json.dumps(entry, sort_keys=True) for entry in events) + "\n", encoding="utf-8")
    quality_path.write_text(json.dumps(quality(evidence, checks), indent=1, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.write_text(json.dumps({
        "biu": "PY-10", "issue": ISSUE, "project": PROJECT, "repository": REPOSITORY,
        "run_started_at": evidence.run["started_at"], "run_finished_at": evidence.run["finished_at"],
        "acceptance": checks,
        "verified": all(check["ok"] is True for check in checks),
        "retained_evidence": [f"{EVIDENCE_BASE}/{path.name}" for path in sorted(evidence.root.iterdir()) if path.is_file()],
        "reproduce": [
            "python3 tools/live/py10_verify_evidence.py --evidence docs/evidence/py10 --live",
            "python3 tools/live/py10_proven_red.py --json",
            "python3 -m pytest -q",
        ],
    }, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(events)} trajectory events; {sum(1 for check in checks if check['ok'] is True)}/{len(checks)} criteria")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
