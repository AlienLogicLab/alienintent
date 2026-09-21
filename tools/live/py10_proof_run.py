#!/usr/bin/env python3
"""Drive the PY-10 coherent live run and retain its evidence.

This script is the operator. It issues exactly the control-plane commands the
contract names — `doctor`, `run`, `decisions` — against the live sandbox, takes
one deliberate process loss mid-run, and records what it observed. It never
moves a BIU into IMPLEMENT and never writes a Project Status (AC 14): every
lifecycle projection in the run is made by the factory itself.

    python3 tools/live/py10_proof_run.py --apply
    python3 tools/live/py10_proof_run.py --apply --fresh   # discard prior run state first

Evidence lands under `<state>/evidence/`, produced through the redaction
boundary so no secret, App id, installation id, key path or ingress hostname
can reach it.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))

from py10_sandbox import (  # noqa: E402
    ROOT,
    Redactor,
    credentialed_git_environment,
    credentials,
    document,
    git,
    profile_path,
    state_root,
    write_json,
)

from alienintent.composition.sandbox_profile import compose_profile  # noqa: E402

ACTOR = "PY-10 operator"
AUTHORITY = "AlienLogicLab/alienintent#58 (SWF-11)"
RUN_TIMEOUT_SECONDS = 2400
KILL_AFTER_DISPATCH_SECONDS = 8.0
DISPATCH_WAIT_SECONDS = 600.0


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class Operator:
    """Run the control-plane CLI exactly as an operator would."""

    def __init__(self, state: Path, environment: dict[str, str], transcript: list[dict], redact: Redactor) -> None:
        self.state, self.environment, self.transcript, self.redact = state, environment, transcript, redact

    def command(self, *arguments: str) -> list[str]:
        return [
            sys.executable, "-m", "alienintent", "--json",
            "--profile-factory", "alienintent.composition.sandbox_run_profile:profile", *arguments,
        ]

    def invoke(self, *arguments: str, timeout: float = 300.0) -> dict:
        """Run one operator command under an external wall-clock bound.

        The bound belongs to the run, not to the control plane. The coordinator
        has no terminal handling for a non-success worker outcome, so a
        misconfigured dispatch would re-dispatch the same item indefinitely
        with real provider spend. The whole process group is killed at the
        bound, so that failure mode is contained and visible in the transcript
        rather than silent and expensive.
        """
        started = time.time()
        launched = subprocess.Popen(
            self.command(*arguments), cwd=ROOT, env=self.environment,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True,
        )
        bounded = False
        try:
            out, err = launched.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            bounded = True
            os.killpg(os.getpgid(launched.pid), signal.SIGKILL)
            out, err = launched.communicate()
        entry = {
            "at": now(), "command": ["alienintent", *arguments], "exit_status": launched.returncode,
            "elapsed_seconds": round(time.time() - started, 3), "wall_clock_bound_reached": bounded,
            "stdout": _document(out), "stderr": (err or "").strip()[-600:],
        }
        self.transcript.append(self.redact(entry))
        return entry

    def mutation(self, *arguments: str, target: str, expected_version: int, intent: str, key: str, timeout: float = RUN_TIMEOUT_SECONDS) -> dict:
        return self.invoke(
            *arguments, target, "--actor", ACTOR, "--authority", AUTHORITY, "--intent", intent,
            "--expected-version", str(expected_version), "--reason", intent, "--idempotency-key", key,
            timeout=timeout,
        )


def _document(raw: str) -> object:
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw.strip()[-2000:]


# --- durable-state reads (read-only, outside the control plane) ---------------


def store_state(database: Path) -> dict:
    if not database.exists():
        return {"aggregates": {}, "reservations": [], "effects": []}
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True, timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        aggregates = {
            row["identity"]: {"revision": row["version"], **json.loads(row["state"])}
            for row in connection.execute("SELECT identity, version, state FROM aggregates")
        }
        reservations = [dict(row) for row in connection.execute("SELECT scope, resource_key, owner, fence FROM reservations")]
        effects = [dict(row) for row in connection.execute("SELECT identity, aggregate, status FROM effects")]
        return {"aggregates": aggregates, "reservations": reservations, "effects": effects}
    finally:
        connection.close()


def wait_for_dispatch(database: Path, deadline: float) -> dict | None:
    """Wait until the factory holds the repository slot — a worker is in flight."""
    while time.time() < deadline:
        state = store_state(database)
        if state["reservations"]:
            return state["reservations"][0]
        time.sleep(0.05)
    return None


# --- isolation observation (AC 16) --------------------------------------------


def node_bootstrap_observation() -> dict:
    """The Node bootstrap keeps running and is not reconfigured (binding rule 2)."""
    listening = subprocess.run(["ss", "-ltn"], capture_output=True, text=True, check=False).stdout
    answers = {}
    for port in (8787, 8788):
        probe = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "5", f"http://127.0.0.1:{port}/"],
            capture_output=True, text=True, check=False,
        )
        answers[str(port)] = probe.stdout.strip() or "no answer"
    config = Path("/etc/cloudflared/config.yml")
    return {
        "bootstrap_ports_listening": [port for port in ("8787", "8788") if f":{port} " in listening],
        "bootstrap_port_answers": answers,
        "root_tunnel_config_mtime": int(config.stat().st_mtime) if config.exists() else None,
        "definition": "the Node bootstrap's own ingress, observed from outside it; PY-10 neither starts, stops nor reconfigures it",
    }


def isolation_observation(record: dict, state: Path) -> dict:
    """The two isolation controls, observed rather than asserted (SWF-34).

    Repository isolation is permission enforced, so it is read back from what
    GitHub reports the installation can reach. Project isolation is
    configuration enforced, so it is read back from the configuration itself
    and from the refusal a foreign identity meets.
    """
    from alienintent.composition.sandbox_run_profile import SandboxBacklogComposition
    from alienintent.installation.domain.project_identity import ProjectAddressRejected

    composed = SandboxBacklogComposition(record, state / "isolation.sqlite", lambda _: None)
    findings = list(composed.isolation_findings())
    installation = composed.credentials.installation()
    try:
        composed.address.resolve("PVT_kwDOanIdentityThisProfileDoesNotTarget", None)
        negative_control = "a foreign Project identity resolved — the control does not operate"
    except ProjectAddressRejected as error:
        negative_control = f"typed refusal: {error}"
    return {
        "findings": findings,
        "repository_scope": list(composed.credentials.repositories()),
        "repository_selection": installation.get("repository_selection"),
        "configured_project": composed.profile.project_reference,
        "foreign_project_negative_control": negative_control,
        "standard": "SWF-34: repository isolation is permission enforced; Project isolation is configuration enforced; "
                    "AC 16 is the compensating end-to-end control. No token-level Project isolation is claimed.",
    }


def production_project_observation(record: dict, project_id: str) -> dict:
    """A read-only digest of the production Project, so 'unchanged' is checkable.

    The identity read here is the one already recorded in
    `docs/operations/py10-sandbox.md`, and it is reduced to a digest rather than
    republished. This observation is made by this tool, never by a shipped
    adapter: `GitHubProjectsV2Directory` refuses to address any Project but the
    configured one, and that refusal is itself part of the isolation evidence.
    """
    from hashlib import sha256

    from alienintent.installation.adapters.urllib_github_transport import UrllibGitHubTransport

    minted = credentials(record)
    query = """query($project:ID!){ node(id:$project){ ... on ProjectV2 { id number title updatedAt
      items(first:100){ totalCount nodes { id updatedAt } } } } }"""
    response = UrllibGitHubTransport().request(
        "POST", "https://api.github.com/graphql",
        dict(minted.authorization()) | {"Content-Type": "application/json"},
        json.dumps({"query": query, "variables": {"project": project_id}}).encode(),
    )
    answer = json.loads(response.body or b"{}")
    node = (answer.get("data") or {}).get("node")
    if not isinstance(node, dict):
        return {"observed": False, "detail": f"production Project could not be read (HTTP {response.status})"}
    items = node.get("items") or {}
    fingerprint = json.dumps(
        {"count": items.get("totalCount"), "items": sorted((entry["id"], entry["updatedAt"]) for entry in items.get("nodes") or [])},
        sort_keys=True,
    )
    return {
        "observed": True,
        "item_count": items.get("totalCount"),
        "project_updated_at": node.get("updatedAt"),
        "state_digest": "sha256:" + sha256(fingerprint.encode()).hexdigest(),
        "identity_digest": "sha256:" + sha256(str(node.get("id")).encode()).hexdigest(),
        "definition": "digest over every item identity and its updatedAt; equal digests before and after mean nothing in that Project changed",
    }


# --- candidate custody, observed at the remote --------------------------------


def published_candidates(record: dict, token: str) -> dict:
    environment = credentialed_git_environment(record, token)
    repository = str(record["repository"])
    advertised = git("ls-remote", "--heads", f"https://github.com/{repository}.git", environment=environment).stdout
    branches = {}
    for line in advertised.splitlines():
        revision, _, reference = line.partition("\t")
        branches[reference.removeprefix("refs/heads/")] = revision.strip()
    return branches


def candidate_commit_detail(record: dict, token: str, checkout: Path, branches: dict[str, str]) -> list[dict]:
    environment = credentialed_git_environment(record, token)
    git("fetch", "--quiet", "origin", "+refs/heads/*:refs/remotes/origin/*", cwd=checkout, environment=environment, check=False)
    detail = []
    for branch, revision in sorted(branches.items()):
        if not branch.startswith("candidate/"):
            continue
        show = git("show", "--no-patch", "--format=%H%n%s%n%an", revision, cwd=checkout, environment=environment, check=False)
        files = git("diff", "--name-only", f"{revision}^", revision, cwd=checkout, environment=environment, check=False)
        parent = git("rev-list", "--count", f"main..{revision}", cwd=checkout, environment=environment, check=False)
        lines = show.stdout.splitlines()
        detail.append({
            "branch": branch, "revision": revision,
            "subject": lines[1] if len(lines) > 1 else "", "author": lines[2] if len(lines) > 2 else "",
            "changed_paths": files.stdout.split(), "commits_ahead_of_main": parent.stdout.strip(),
        })
    return detail


# --- the run ------------------------------------------------------------------


def prepare_checkout(record: dict, token: str, checkout: Path) -> str:
    environment = credentialed_git_environment(record, token)
    repository = str(record["repository"])
    if checkout.exists():
        shutil.rmtree(checkout)
    checkout.parent.mkdir(parents=True, exist_ok=True)
    git("clone", "--quiet", f"https://github.com/{repository}.git", str(checkout), environment=environment)
    return git("rev-parse", "HEAD", cwd=checkout, environment=environment).stdout.strip()


def run_environment(record: dict, token: str, state: Path, checkout: Path) -> dict[str, str]:
    return credentialed_git_environment(record, token) | {
        "ALIENINTENT_SANDBOX_PROFILE": str(profile_path()),
        "ALIENINTENT_SANDBOX_STATE": str(state),
        "ALIENINTENT_SANDBOX_CHECKOUT": str(checkout),
        "PYTHONPATH": str(ROOT / "src"),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Drive the PY-10 coherent live run")
    parser.add_argument("--apply", action="store_true", required=True)
    parser.add_argument("--fresh", action="store_true", help="discard prior run state")
    parser.add_argument("--production-project", default="", help="production Project identity for the AC 16 observation")
    arguments = parser.parse_args(argv)

    record = document()
    redact = Redactor(record)
    profile = compose_profile(record)
    state = state_root()
    evidence_root = state / "evidence"
    if arguments.fresh and state.exists():
        # The seeding record is evidence about the backlog this run consumed,
        # produced before the run and not reproducible from it. Discarding run
        # state must not discard it.
        seed = evidence_root / "seed.json"
        preserved = seed.read_bytes() if seed.exists() else None
        shutil.rmtree(state)
        evidence_root.mkdir(parents=True, exist_ok=True)
        if preserved is not None:
            seed.write_bytes(preserved)
    state.mkdir(parents=True, exist_ok=True)
    evidence_root.mkdir(parents=True, exist_ok=True)
    if not (evidence_root / "seed.json").exists():
        raise SystemExit("no seeding record is retained; run py10_seed_backlog.py before the proof run")
    checkout = state / "repository"
    database = state / "state.sqlite"

    minted = credentials(record)
    token = minted.token().value
    baseline = prepare_checkout(record, token, checkout)
    environment = run_environment(record, token, state, checkout)

    transcript: list[dict] = []
    operator = Operator(state, environment, transcript, redact)
    phases: list[dict] = []
    started_at = now()

    before = {
        "at": started_at,
        "node_bootstrap": node_bootstrap_observation(),
        "sandbox_baseline": baseline,
        "published_branches": published_candidates(record, token),
    }
    if arguments.production_project:
        before["production_project"] = production_project_observation(record, arguments.production_project)

    # The observer samples the durable store for the whole run.
    stop_marker = state / "observer.stop"
    if stop_marker.exists():
        stop_marker.unlink()
    timeline = evidence_root / "run-timeline.jsonl"
    observer = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve().parent / "py10_run_observer.py"),
         "--state", str(state), "--until", str(stop_marker), "--timeline", str(timeline)],
        cwd=ROOT, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )

    try:
        # --- AC 15: doctor passes against the sandbox before autonomous start.
        phases.append(redact({"phase": "isolation", **isolation_observation(record, state)}))

        doctor = operator.invoke("doctor", timeout=600)
        phases.append({"phase": "doctor", "exit_status": doctor["exit_status"], "report": doctor["stdout"]})
        if doctor["exit_status"] != 0:
            raise SystemExit("doctor did not pass; autonomous start was not attempted")

        # --- AC 10: a deliberate process loss while a worker is in flight.
        launched = subprocess.Popen(
            operator.command("run", "service", "--actor", ACTOR, "--authority", AUTHORITY,
                             "--intent", "drain the seeded backlog", "--expected-version", "0",
                             "--reason", "PY-10 coherent live run", "--idempotency-key", "py10-run-1"),
            cwd=ROOT, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            start_new_session=True,
        )
        reservation = wait_for_dispatch(database, time.time() + DISPATCH_WAIT_SECONDS)
        if reservation is None:
            launched.kill()
            raise SystemExit("no dispatch was observed; the run cannot be interrupted mid-work")
        time.sleep(KILL_AFTER_DISPATCH_SECONDS)
        before_kill = store_state(database)
        os.killpg(os.getpgid(launched.pid), signal.SIGKILL)
        launched.wait(timeout=60)
        after_kill = store_state(database)
        phases.append(redact({
            "phase": "process-loss",
            "boundary": "SIGKILL to the run process group while the repository reservation was held and its effect was unresolved",
            "signal": "SIGKILL", "exit_status": launched.returncode,
            "held_reservation": reservation,
            "before": before_kill, "after": after_kill,
            "definition": "the whole process group is signalled, so the worker the control plane launched dies with it",
        }))

        # --- restart: recovery, then the rest of the backlog.
        restarted = operator.mutation("run", target="service", expected_version=0,
                                      intent="resume after the process loss", key="py10-run-2")
        phases.append({"phase": "restart", "exit_status": restarted["exit_status"], "summary": restarted["stdout"]})

        # --- AC 7, 8: the escalations, with complete context.
        listed = operator.invoke("decisions", "list")
        open_requests = listed["stdout"] if isinstance(listed["stdout"], list) else []
        phases.append({"phase": "decisions-open", "requests": redact(open_requests)})

        # --- AC 9: each decision is attributable, durable, and resumes the work.
        for index, request in enumerate(open_requests):
            work_item = request["work_item"]
            revision = store_state(database)["aggregates"].get(f"factory:{work_item}", {}).get("revision", 0)
            decided = operator.invoke(
                "decisions", "decide", work_item, "--choice", "authorize",
                "--biu-version", str(request["biu_version"]),
                "--actor", ACTOR, "--authority", AUTHORITY,
                "--intent", f"authorize {work_item} to resume through normal admission guards",
                "--expected-version", str(revision), "--reason", "PY-10 live proof decision",
                "--idempotency-key", f"py10-decision-{index}", timeout=RUN_TIMEOUT_SECONDS,
            )
            phases.append({"phase": "decision", "work_item": work_item, "exit_status": decided["exit_status"], "record": decided["stdout"]})

        # --- AC 13: the executable backlog is exhausted.
        final = operator.mutation("run", target="service", expected_version=0,
                                  intent="confirm the executable backlog is exhausted", key="py10-run-3")
        phases.append({"phase": "drain-to-exhaustion", "exit_status": final["exit_status"], "summary": final["stdout"]})
        phases.append({"phase": "status", "status": operator.invoke("status")["stdout"]})
        for identity in ("SB-01", "SB-02", "SB-03", "SB-04", "SB-05", "SB-06"):
            phases.append({"phase": "explain", "target": identity, "account": operator.invoke("explain", identity)["stdout"]})
    finally:
        stop_marker.write_text(now(), encoding="utf-8")
        try:
            observer.wait(timeout=30)
        except subprocess.TimeoutExpired:
            observer.kill()

    token = credentials(record).token().value
    branches = published_candidates(record, token)
    after = {
        "at": now(),
        "node_bootstrap": node_bootstrap_observation(),
        "published_branches": branches,
        "candidates": candidate_commit_detail(record, token, checkout, branches),
    }
    if arguments.production_project:
        after["production_project"] = production_project_observation(record, arguments.production_project)

    run_record = {
        "biu": "PY-10", "profile": profile.profile, "repository": profile.repository,
        "project": profile.project_reference, "started_at": started_at, "finished_at": now(),
        "before": before, "after": after, "phases": phases,
        "durable_state": store_state(database),
        "operator_transcript": transcript,
    }
    write_json(evidence_root / "proof-run.json", redact(run_record))
    print(json.dumps({"evidence": str(evidence_root / "proof-run.json"), "phases": [entry["phase"] for entry in phases]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
