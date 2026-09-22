"""``python -m alienintent.composition.offline_proof``: run one FX proof over the S0 substrate.

Exit status 0 means every pinned predicate was observed (PASS); 1 means the
substrate or kernel did not behave as pinned (FAIL); 2 means a required
measurement could not be taken (HOLD) — a credential was present, or outbound
network denial was not established. A hold is never reported as PASS and never
as zero. The report and trajectory are left under the fixture root either way.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import errno
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from typing import Mapping

from alienintent.composition.offline_profile import OfflineProofSubstrate, ProofManifest, credential_findings, load_manifest
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.invocation_runtime.adapters.scripted_worker import SCRIPTED_PROVIDER, ScriptedWorkerProcess, journal_outcome, journal_provider_calls, journal_records

PROBE_ADDRESS = ("192.0.2.1", 9)
PROBE_REMOTE = "https://198.51.100.1/denied.git"
DENIAL_ERRNOS = frozenset({errno.ENETUNREACH, errno.EPERM, errno.EACCES})
SOURCE_ROOT = Path(__file__).resolve().parents[3]
RECORDER = "FX offline proof runner (alienintent.composition.offline_proof)"
EXIT_PASS, EXIT_FAIL, EXIT_HOLD = 0, 1, 2


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- isolation observations -------------------------------------------------------


def network_denial_probe(timeout: float, environment: Mapping[str, str]) -> dict[str, object]:
    """Attempt outbound network and record the refusal, or the absence of one.

    Only a definitive refusal (ENETUNREACH, EPERM, EACCES) establishes denial.
    A connection, a timeout or any other error leaves the status
    NOT_ESTABLISHED: silence is not denial.
    """
    observation: dict[str, object] = {
        "definition": "outbound TCP connect to TEST-NET 192.0.2.1:9 must be refused by the environment, and git must be unable to reach an HTTPS remote",
        "socket": {}, "git_ls_remote": "NOT_RUN", "net_namespace_inode": None, "status": "NOT_ESTABLISHED",
    }
    try:
        observation["net_namespace_inode"] = os.stat("/proc/self/ns/net").st_ino
    except OSError:
        pass
    try:
        with socket.create_connection(PROBE_ADDRESS, timeout=timeout):
            observation["socket"] = {"result": "connected", "detail": "connection succeeded; network is reachable"}
            return observation
    except (TimeoutError, socket.timeout):
        observation["socket"] = {"result": "timeout", "detail": f"no answer within {timeout}s; silence is not denial"}
        return observation
    except OSError as error:
        name = errno.errorcode.get(error.errno or 0, "unknown")
        observation["socket"] = {"result": "refused", "errno": error.errno, "name": name, "detail": str(error)}
        if error.errno not in DENIAL_ERRNOS:
            return observation
    try:
        completed = subprocess.run(["git", "ls-remote", PROBE_REMOTE], env=dict(environment) | {"GIT_TERMINAL_PROMPT": "0"}, capture_output=True, text=True, timeout=timeout + 10, check=False)
        observation["git_ls_remote"] = {"exit_status": completed.returncode, "stderr": completed.stderr.strip().splitlines()[:1]}
        if completed.returncode == 0:
            return observation
    except subprocess.TimeoutExpired:
        observation["git_ls_remote"] = {"exit_status": None, "stderr": ["timed out"]}
        return observation
    observation["status"] = "ENFORCED"
    return observation


def kernel_unchanged(manifest: ProofManifest, source_root: Path) -> dict[str, object]:
    """Whether the pinned kernel paths at the running source equal the release baseline."""
    result: dict[str, object] = {"definition": "git diff --quiet <baseline> -- <kernel_paths> exits 0 in the source checkout; blob ids recorded", "baseline": manifest.kernel_baseline, "paths": list(manifest.kernel_paths), "status": "HOLD"}
    if not manifest.kernel_baseline or not manifest.kernel_paths:
        result["reason"] = "manifest pins no kernel baseline or paths"
        return result
    head = subprocess.run(["git", "-C", str(source_root), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    if head.returncode:
        result["reason"] = "source root is not a git checkout"
        return result
    result["source_revision"] = head.stdout.strip()
    diff = subprocess.run(["git", "-C", str(source_root), "diff", "--quiet", manifest.kernel_baseline, "--", *manifest.kernel_paths], capture_output=True, text=True, check=False)
    blobs = {}
    for path in manifest.kernel_paths:
        blob = subprocess.run(["git", "-C", str(source_root), "rev-parse", f"HEAD:{path}"], capture_output=True, text=True, check=False)
        blobs[path] = blob.stdout.strip() if blob.returncode == 0 else "UNRESOLVED"
    result["blobs"] = blobs
    if diff.returncode == 0:
        result["status"] = "UNCHANGED"
    elif diff.returncode == 1:
        result["status"] = "CHANGED"
    else:
        result["reason"] = diff.stderr.strip()[:200]
    return result


# --- the proof --------------------------------------------------------------------


def check(identifier: str, name: str, ok: bool | None, expected: str, observed: object) -> dict[str, object]:
    return {"id": identifier, "name": name, "status": "HOLD" if ok is None else ("PASS" if ok else "FAIL"), "expected": expected, "observed": observed}


def _candidate_parts(locator: str) -> tuple[str, str]:
    prefix, reference = locator.rsplit("#", 1)
    branch, revision = reference.rsplit("@", 1)
    return branch, revision


def evaluate(substrate: OfflineProofSubstrate, summary, kernel: dict[str, object]) -> tuple[list[dict[str, object]], dict[str, object]]:
    manifest = substrate.manifest
    epoch = manifest.clock_epoch
    checks: list[dict[str, object]] = []
    facts: dict[str, object] = {"candidates": {}, "stages": {}, "correlations": {}}
    preflight = SQLiteOperationalStore.preflight(substrate.database)
    states = {}
    for item in substrate.items:
        try:
            states[item.identity] = substrate.coordinator.state(item.identity)
        except KeyError:
            states[item.identity] = None
    stages = {identity: (None if state is None else str(state.stage)) for identity, state in states.items()}
    facts["stages"] = stages
    facts["correlations"] = {identity: None if state is None else substrate.store.read_state(manifest.profile, f"factory:{identity}")[1].get("correlation") for identity, state in states.items()}
    all_done = bool(states) and all(state is not None and state.stage is LifecycleStage.DONE and state.candidate is not None and state.candidate.independent_read_back_proven for state in states.values())
    checks.append(check("P1", "real temporary SQLite", substrate.database.exists() and preflight.current_version == 2 and all_done, "state.sqlite at schema 2 holds every seeded aggregate at DONE with an independently read-back candidate", {"path": str(substrate.database), "schema_version": preflight.current_version, "stages": stages}))

    bare = subprocess.run(["git", "-C", str(substrate.remote), "rev-parse", "--is-bare-repository"], capture_output=True, text=True, check=False).stdout.strip() == "true"
    main = substrate.remote_advertises("main")
    advertised: dict[str, object] = {}
    clones_ok, dates_ok = True, True
    for identity, state in states.items():
        if state is None or state.candidate is None:
            advertised[identity] = None
            clones_ok = False
            continue
        branch, revision = _candidate_parts(state.candidate.locator)
        advertised[identity] = {"branch": branch, "revision": revision, "advertised": substrate.remote_advertises(branch)}
        correlation = facts["correlations"][identity]
        producer_clone = substrate.producer_read_back / f"producer-{correlation}"
        verifier_clone = substrate.verifier_root / revision
        resolved = {}
        for label, clone in (("producer_read_back", producer_clone), ("verifier_evidence", verifier_clone)):
            resolve = subprocess.run(["git", "-C", str(clone), "rev-parse", f"{revision}^{{commit}}"], capture_output=True, text=True, check=False) if (clone / ".git").exists() else None
            resolved[label] = None if resolve is None else resolve.stdout.strip()
        clones_ok = clones_ok and all(value == revision for value in resolved.values())
        author, committer = substrate.commit_dates(revision)
        dates_ok = dates_ok and author == epoch == committer
        facts["candidates"][identity] = {"branch": branch, "revision": revision, "locator": state.candidate.locator, "correlation": correlation, "clones": {label: str(clone) for label, clone in (("producer_read_back", producer_clone), ("verifier_evidence", verifier_clone))}, "resolved": resolved, "author_date": author, "committer_date": committer}
    checks.append(check("P2", "disposable local bare Git remote", bare and main == substrate.baseline_revision and bool(advertised) and all(entry is not None and entry["advertised"] == entry["revision"] for entry in advertised.values()), "remote.git is bare, advertises main at the baseline and each candidate branch at its revision", {"remote": str(substrate.remote), "bare": bare, "main": main, "baseline": substrate.baseline_revision, "candidates": advertised}))
    checks.append(check("P3", "publication and fetch into a fresh verifier worktree", clones_ok and bool(states), "the producer read-back clone and the kernel's verifier clone each resolve the exact candidate revision", {identity: entry.get("resolved") for identity, entry in facts["candidates"].items()}))

    receipts = substrate.work.receipts()
    receipts_by_identity = {identity: [(r["receipt"], r.get("state")) for r in receipts if r.get("identity") == identity] for identity in states}
    expected_receipts = [("release-proposed", None), ("execution-state-projected", "DONE")]
    checks.append(check("P4", "local work-management transport", substrate.work.seed_path.exists() and all(sequence == expected_receipts for sequence in receipts_by_identity.values()), "ready-snapshot.json exists and each item's receipts are release-proposed then execution-state-projected DONE", {"seed": str(substrate.work.seed_path), "receipts": receipts_by_identity}))
    checks.append(check("P5", "local provider transport", isinstance(substrate.process, ScriptedWorkerProcess) and substrate.process.capabilities.provider == SCRIPTED_PROVIDER, "the process behind RealWorkerProvider is ScriptedWorkerProcess with provider 'scripted'", {"process": type(substrate.process).__name__, "provider": substrate.process.capabilities.provider}))

    journal = journal_records(substrate.journal_path)
    stamps_ok = all(entry.get("at") == float(epoch) for entry in journal) and all(entry.get("at") == float(epoch) for entry in receipts) and bool(journal) and bool(receipts)
    checks.append(check("P6", "injected clock and IDs", stamps_ok and dates_ok, "every journal and receipt timestamp and every candidate author/committer date equals the injected epoch", {"epoch": epoch, "journal_stamps": sorted({entry.get("at") for entry in journal}), "receipt_stamps": sorted({entry.get("at") for entry in receipts}), "commit_dates": {identity: (entry["author_date"], entry["committer_date"]) for identity, entry in facts["candidates"].items()}}))

    read_back_ok = bool(states)
    journal_events: dict[str, list[str]] = {}
    for identity, state in states.items():
        correlation = facts["correlations"][identity]
        journal_events[identity] = [str(entry["event"]) for entry in journal if entry.get("correlation_id") == correlation or entry.get("invocation_id") == correlation]
        outcome = journal_outcome(substrate.journal_path, str(correlation))
        read_back_ok = read_back_ok and outcome is not None and state is not None and state.candidate is not None and outcome.candidate is not None and outcome.candidate.locator == state.candidate.locator
    checks.append(check("P7", "durable scripted worker journal", read_back_ok and all("invocation-started" in events and "invocation-outcome" in events for events in journal_events.values()), "the journal file over the same root reads back each invocation's outcome, and started/outcome records exist", {"path": str(substrate.journal_path), "events": journal_events}))

    provider_calls = journal_provider_calls(substrate.journal_path)
    checks.append(check("P10", "zero provider calls", provider_calls == 0, "sum of provider_calls over process-run journal records is 0", {"value": provider_calls, "definition": "attempts by the worker process adapter to execute a provider executable"}))
    checks.append(check("P11", "existing kernel unchanged", None if kernel["status"] == "HOLD" else kernel["status"] == "UNCHANGED", "pinned kernel paths equal the release baseline", kernel))

    collapse_ok = bool(states) and all(state is not None and state.stage is LifecycleStage.DONE and facts["correlations"][identity] == f"launch:{identity}:0" for identity, state in states.items()) and not any(r.get("state") in {"VERIFY", "REVIEW", "ACCEPT"} for r in receipts)
    limitation = {
        "observed": collapse_ok,
        "statement": "FactoryCoordinator._completed_for_outcome carries a successful producer outcome through verify/review/accept/close in one kernel step; no separate VERIFY, REVIEW or ACCEPT projection was emitted and no independent verifier invocation exists",
        "independent_verifier_invocation": "NOT_ESTABLISHED",
        "live_proof": "NOT_ESTABLISHED",
        "authority": "R1-GAP-039-ORCHESTRATION and R1-GAP-039-REAL-OUTCOME remain open; S0 reports the limitation and does not repair it",
    }
    checks.append(check("P12", "success-collapse limitation reported", collapse_ok, "each DONE item reached DONE under its single launch correlation with no VERIFY/REVIEW/ACCEPT projection; the limitation is stated", limitation))
    scripted_transitions = [entry for entry in journal if "stage" in entry or "lifecycle" in entry]
    checks.append(check("P13", "no scripted lifecycle transitions", not scripted_transitions and all(sequence == expected_receipts for sequence in receipts_by_identity.values()), "the journal carries no lifecycle field and the only lifecycle receipts are the kernel's projections", {"scripted_transition_records": len(scripted_transitions), "adapter_holds_store": hasattr(substrate.process, "_store") or hasattr(substrate.worker, "_store")}))
    facts["summary"] = {"stop_reason": str(summary.stop_reason), "dispatched": list(summary.dispatched), "authority_blocked": list(summary.authority_blocked), "failed": list(summary.failed)}
    facts["success_collapse_limitation"] = limitation
    facts["provider_calls_observed"] = {"value": provider_calls, "definition": "attempts by the worker process adapter to execute a provider executable, summed over the durable journal"}
    return checks, facts


def trajectory_events(manifest: ProofManifest, facts: Mapping[str, object], network: Mapping[str, object], credentials: tuple[str, ...], recorder: str, refs: list[str]) -> list[dict[str, object]]:
    now = utc_now()
    base = {"schema_version": "1.0", "project": f"{manifest.fixture_id} offline proof ({manifest.profile})", "actor_role": "FACTORY", "recorded_at": now, "recorder": recorder, "evidence_refs": refs}
    events: list[dict[str, object]] = [base | {
        "event_id": f"{manifest.fixture_id.lower()}-000-isolation-observed", "biu_id": "WO-220101", "actor_role": "OPERATOR", "event_type": "ISOLATION_OBSERVED",
        "observation_type": "independent verification", "verified": True, "result": str(network.get("status")),
        "description": f"Outbound network denial {network.get('status')}: {json.dumps(network.get('socket'))}; git ls-remote {json.dumps(network.get('git_ls_remote'))}. Credential variables present: {list(credentials)}.",
    }]
    for index, (identity, candidate) in enumerate(facts["candidates"].items(), start=1):
        stage = facts["stages"][identity]
        events.append(base | {"event_id": f"{manifest.fixture_id.lower()}-{index:03d}-released", "biu_id": identity, "event_type": "BIU_RELEASED", "lifecycle_from": "READY", "lifecycle_to": "IMPLEMENT", "observation_type": "state-record observation", "verified": True, "result": "RELEASED", "description": "Automatic policy release admitted by the unchanged kernel from the local ready snapshot."})
        events.append(base | {"event_id": f"{manifest.fixture_id.lower()}-{index:03d}-invocation-started", "biu_id": identity, "event_type": "INVOCATION_STARTED", "invocation_id": candidate["correlation"], "provider": SCRIPTED_PROVIDER, "observation_type": "state-record observation", "verified": True, "description": "Scripted worker process behind the unchanged RealWorkerProvider; no model, no credential."})
        events.append(base | {"event_id": f"{manifest.fixture_id.lower()}-{index:03d}-candidate-published", "biu_id": identity, "event_type": "CANDIDATE_PUBLISHED", "invocation_id": candidate["correlation"], "candidate_ref": candidate["locator"], "candidate_type": "source-revision", "branch": candidate["branch"], "commit_sha": candidate["revision"], "observation_type": "Git observation", "verified": True, "description": "Published to the disposable local bare remote and read back from a fresh clone by the producer path and again by the kernel custody gate."})
        events.append(base | {"event_id": f"{manifest.fixture_id.lower()}-{index:03d}-success-collapse-observed", "biu_id": identity, "event_type": "SUCCESS_COLLAPSE_OBSERVED", "invocation_id": candidate["correlation"], "lifecycle_from": "IMPLEMENT", "lifecycle_to": str(stage), "observation_type": "state-record observation", "verified": True, "description": facts["success_collapse_limitation"]["statement"]})
        if stage == "DONE":
            events.append(base | {"event_id": f"{manifest.fixture_id.lower()}-{index:03d}-done", "biu_id": identity, "event_type": "BIU_DONE", "lifecycle_to": "DONE", "observation_type": "state-record observation", "verified": True, "result": "DONE", "description": "Terminal state read back from state.sqlite; local proof only, live proof NOT_ESTABLISHED."})
    return events


def run_proof(root: Path, manifest: ProofManifest, environment: Mapping[str, str], *, report_path: Path | None = None, trajectory_path: Path | None = None, network_timeout: float = 3.0, source_root: Path = SOURCE_ROOT) -> tuple[int, dict[str, object]]:
    started = time.monotonic()
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    report_path = report_path or root / "run-report.json"
    trajectory_path = trajectory_path or root / "trajectory.jsonl"
    credentials = credential_findings(environment)
    network = network_denial_probe(network_timeout, environment)
    recorder = f"{RECORDER} for {manifest.fixture_id}"
    refs = ["run-report.json", "trajectory.jsonl", "worker-journal/journal.jsonl", "work-management/receipts.jsonl", "work-management/ready-snapshot.json", "state.sqlite"]
    report: dict[str, object] = {
        "schema_version": "1.0", "biu_id": "WO-220101", "fixture_id": manifest.fixture_id, "derived_from": str(trajectory_path), "evidence_refs": refs,
        "scope": "one local run of the S0 isolated proof substrate over a disposable root; describes the seeded probe items, not WO-220101's own lifecycle",
        "manifest": {"profile": manifest.profile, "seed": manifest.seed, "digest": manifest.digest, "work_items": [item.identity for item in manifest.work_items]},
        "injected_clock": {"epoch_seconds": manifest.clock_epoch, "definition": "every substrate clock read returns this value; artifact recorded_at uses the real clock"},
        "root": str(root), "network_denial": network, "credentials_present": list(credentials),
        "live_proof": "NOT_ESTABLISHED", "token_usage": "NOT_APPLICABLE", "cost": "NOT_APPLICABLE",
        "unknown_metrics": ["token_usage: no provider ran; NOT_APPLICABLE, never zero", "cost: no provider ran; NOT_APPLICABLE, never zero"],
        "recorder": recorder, "recorded_at": utc_now(), "hold_reasons": [], "checks": [],
    }
    holds: list[str] = []
    if credentials:
        holds.append(f"credential variables present in the proof environment: {list(credentials)}")
    if network.get("status") != "ENFORCED":
        holds.append(f"outbound network denial not established: {json.dumps(network.get('socket'))}")
    if holds:
        report |= {"verdict": "HOLD", "hold_reasons": holds, "elapsed_seconds": {"value": round(time.monotonic() - started, 3), "definition": "real wall-clock from probe start to report"}}
        _write(report_path, trajectory_path, report, [])
        return EXIT_HOLD, report
    substrate = OfflineProofSubstrate(root, manifest, environment)
    summary = substrate.coordinator.start()
    kernel = kernel_unchanged(manifest, source_root)
    checks, facts = evaluate(substrate, summary, kernel)
    events = trajectory_events(manifest, facts, network, credentials, recorder, refs)
    verdict = "PASS" if all(entry["status"] == "PASS" for entry in checks) else ("HOLD" if any(entry["status"] == "HOLD" for entry in checks) and all(entry["status"] != "FAIL" for entry in checks) else "FAIL")
    report |= {
        "verdict": verdict, "checks": checks, "kernel_unchanged": kernel, "success_collapse_limitation": facts["success_collapse_limitation"],
        "provider_calls_observed": facts["provider_calls_observed"], "lifecycle_terminal_stage": facts["stages"], "candidates": facts["candidates"],
        "coordinator_summary": facts["summary"], "reopened_root": substrate.reopened, "baseline_revision": substrate.baseline_revision,
        "substituted_boundaries": ["worker provider transport: ScriptedWorkerProcess behind the unchanged RealWorkerProvider", "worker outcome journal: ScriptedWorkerProvider durable JSONL", "work management transport: LocalWorkManagement durable receipts", "source-control remote: local bare repository by path", "decision notification: NoOpDecisionNotifier"],
        "hold_reasons": [f"{entry['id']}: {entry['observed']}" for entry in checks if entry["status"] == "HOLD"],
        "elapsed_seconds": {"value": round(time.monotonic() - started, 3), "definition": "real wall-clock from probe start to report"},
    }
    _write(report_path, trajectory_path, report, events)
    return {"PASS": EXIT_PASS, "FAIL": EXIT_FAIL, "HOLD": EXIT_HOLD}[verdict], report


def _write(report_path: Path, trajectory_path: Path, report: Mapping[str, object], events: list[dict[str, object]]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    trajectory_path.parent.mkdir(parents=True, exist_ok=True)
    trajectory_path.write_text("".join(json.dumps(event, sort_keys=True) + "\n" for event in events), encoding="utf-8")
    report_path.write_text(json.dumps(report, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="alienintent.composition.offline_proof")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--trajectory", type=Path)
    parser.add_argument("--network-timeout", type=float, default=3.0)
    args = parser.parse_args(argv)
    manifest = load_manifest(args.manifest)
    status, report = run_proof(args.root, manifest, os.environ, report_path=args.report, trajectory_path=args.trajectory, network_timeout=args.network_timeout)
    print(json.dumps({"fixture_id": manifest.fixture_id, "verdict": report["verdict"], "exit_status": status, "report": str(args.report or Path(args.root) / "run-report.json"), "hold_reasons": report.get("hold_reasons", [])}))
    return status


if __name__ == "__main__":
    sys.exit(main())
