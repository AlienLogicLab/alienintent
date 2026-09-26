#!/usr/bin/env python3
"""FX-E1 live proof: the Python-only runtime baseline on the sandbox production path.

WO-220502 (E1) under EXPLICIT_LIVE_TRANSPORT_PROOF_AUTHORITY. The operator drives
the shipped control plane — `python -m alienintent --profile-factory
alienintent.composition.sandbox_run_profile:profile` — against the identified
py10-sandbox profile, with every process it launches under the FX-E1 no-Node
instrument:

1. seed two fresh READY BIUs into the sandbox repository and Project;
2. `doctor`, then `run` until the first BIU holds the repository slot, then
   SIGKILL the run's process group while that work is in flight;
3. restart `run`, answer the resulting decision request through `decisions`,
   and drain to exhaustion;
4. restart the resident ingress once more and redeliver, through GitHub, a
   delivery an earlier process admitted; apply the local scope controls;
5. read back the durable store, the Project, the published candidates (from a
   fresh clone) and GitHub's own delivery log.

The proof never touches the AlienIntent repository, Project #1, the Node
bootstrap, its ports or the root tunnel. Output goes through the PY-10 redaction
boundary, and every raw observation is retained content-addressed.

    python3 tools/live/fx_e1_live_proof.py --apply --output docs/evidence/wave2-proof-fixtures/FX-E1

The run record lands at <output>/runs/<run-id>/proof-run.json; observations it
cites are relative to <output>.
"""
from __future__ import annotations

import argparse
import calendar
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import re
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fx_e1_evaluate import evaluate  # noqa: E402
from fx_e1_no_node import NoNodeInstrument, self_test  # noqa: E402
from py10_proof_run import node_bootstrap_observation, prepare_checkout, published_candidates, store_state  # noqa: E402
from py10_sandbox import (  # noqa: E402
    ROOT,
    Redactor,
    SeedWriter,
    credentialed_git_environment,
    credentials,
    document,
    git,
    profile_path,
    seed_body,
    seed_contract,
    seed_title,
    write_json,
)

from alienintent.composition.sandbox_profile import compose_profile  # noqa: E402
from alienintent.composition.sandbox_run_profile import SandboxBacklogComposition  # noqa: E402
from alienintent.execution_coordination.adapters.github_projects_v2 import GitHubProjectsV2Directory  # noqa: E402
from alienintent.installation.adapters.urllib_github_transport import UrllibGitHubTransport  # noqa: E402
from alienintent.installation.domain.project_identity import ProjectAddressRejected  # noqa: E402

ACTOR = "FX-E1 operator (Morty, WO-220502 PRODUCER)"
AUTHORITY = "AlienLogicLab/alienintent#122 (EXPLICIT_LIVE_TRANSPORT_PROOF_AUTHORITY)"
WORKER = ROOT / "tools/live/fx_e1_worker.sh"
DEFAULT_STATE_PARENT = Path.home() / ".local/state/alienintent-sandbox/fx-e1"
HOLD_SECONDS = 45
KILL_AFTER_DISPATCH_SECONDS = 5.0
DISPATCH_WAIT_SECONDS = 600.0
RUN_TIMEOUT_SECONDS = 1500.0
REDELIVERY_WAIT_SECONDS = 90.0
READY_SPACING_SECONDS = 2.0
# A Node executable as an argument-vector element, or a quoted `.mjs` path: a
# GraphQL `"node"` field read with `.get("node")` is not an invocation.
NODE_REFERENCE = re.compile(r"""\[\s*["'](?:[^"']*/)?(?:node|nodejs|npm|npx|corepack)["']\s*[,\]]|["'][^"'\s]*\.mjs["']""")


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def iso_epoch(value: str | None) -> float | None:
    if not value:
        return None
    return float(calendar.timegm(time.strptime(value[:19], "%Y-%m-%dT%H:%M:%S")))


class Observations:
    """Content-addressed raw observations; the run record cites them by digest."""

    def __init__(self, directory: Path, redact: Redactor) -> None:
        self.directory, self.redact = directory, redact
        self.directory.mkdir(parents=True, exist_ok=True)

    def retain(self, kind: str, payload: object) -> str:
        body = json.dumps({"kind": kind, "payload": self.redact(payload)}, indent=1, sort_keys=True) + "\n"
        name = sha256(body.encode()).hexdigest()
        (self.directory / f"{name}.json").write_text(body, encoding="utf-8")
        return f"observations/{name}.json"


class Operator:
    """Run the control-plane CLI exactly as an operator would, under the instrument."""

    def __init__(self, environment: dict[str, str], instrument: NoNodeInstrument, run_id: str) -> None:
        self.environment, self.instrument, self.run_id = environment, instrument, run_id
        self.transcript: list[dict] = []

    def command(self, *arguments: str) -> list[str]:
        return [sys.executable, "-m", "alienintent", "--json",
                "--profile-factory", "alienintent.composition.sandbox_run_profile:profile", *arguments]

    def launch(self, *arguments: str) -> subprocess.Popen:
        launched = subprocess.Popen(self.command(*arguments), cwd=ROOT, env=self.environment, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True, start_new_session=True)
        self.instrument.sampler.watch(launched.pid)
        return launched

    def finish(self, launched: subprocess.Popen, arguments: tuple[str, ...], started: float, timeout: float) -> dict:
        bounded = False
        try:
            out, err = launched.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            bounded = True
            os.killpg(os.getpgid(launched.pid), signal.SIGKILL)
            out, err = launched.communicate()
        entry = {
            "command": ["alienintent", *arguments], "pid": launched.pid, "started_at": started, "ended_at": time.time(),
            "exit_status": launched.returncode, "wall_clock_bound_reached": bounded,
            "stdout": _document(out), "stderr": (err or "").strip()[-1500:],
        }
        self.transcript.append(entry)
        return entry

    def invoke(self, *arguments: str, timeout: float = 600.0) -> dict:
        started = time.time()
        return self.finish(self.launch(*arguments), arguments, started, timeout)

    def mutation(self, *arguments: str, expected_version: int, intent: str, key: str, timeout: float = RUN_TIMEOUT_SECONDS, **extra: str) -> dict:
        flags: list[str] = []
        for name, value in extra.items():
            flags += [f"--{name.replace('_', '-')}", value]
        return self.invoke(*arguments, *flags, "--actor", ACTOR, "--authority", AUTHORITY, "--intent", intent,
                           "--expected-version", str(expected_version), "--reason", intent,
                           "--idempotency-key", f"{self.run_id}-{key}", timeout=timeout)


def _document(raw: str) -> object:
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return (raw or "").strip()[-3000:]


# --- durable reads, outside the control plane ----------------------------------------


def receipts(database: Path) -> list[dict]:
    if not database.exists():
        return []
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True, timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in connection.execute("SELECT event_id, digest, aggregate, version, status FROM receipts")]
    finally:
        connection.close()


def full_effects(database: Path) -> list[dict]:
    if not database.exists():
        return []
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True, timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in connection.execute("SELECT identity, aggregate, status, receipt FROM effects")]
    finally:
        connection.close()


def notification_lines(log: Path) -> list[dict]:
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


def wait_for_dispatch(database: Path, deadline: float) -> dict | None:
    while time.time() < deadline:
        state = store_state(database)
        if state["reservations"]:
            return state["reservations"][0]
        time.sleep(0.05)
    return None


def listener_owner(port: int) -> dict:
    """Who holds the ingress port, observed from the kernel, not asserted."""
    answer = subprocess.run(["ss", "-ltnpH", f"sport = :{port}"], capture_output=True, text=True, check=False).stdout
    pids = sorted({int(match) for match in re.findall(r"pid=(\d+)", answer)})
    owners = []
    for pid in pids:
        try:
            executable = os.readlink(f"/proc/{pid}/exe")
            argv = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
        except OSError:
            continue
        owners.append({"pid": pid, "executable_name": Path(executable).name,
                       "argv": [part.decode(errors="replace") for part in argv if part][:6]})
    return {"port": port, "owners": owners}


def node_writer_observation() -> dict:
    """The Node live writer, observed from outside it: identity, liveness, ingress."""
    runtime = []
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            argv = Path(f"/proc/{name}/cmdline").read_bytes().split(b"\0")
        except OSError:
            continue
        if any(part.decode(errors="replace").endswith("bin/alienintent.mjs") for part in argv):
            runtime.append(int(name))
    return {"runtime_pids": sorted(runtime), **node_bootstrap_observation()}


# --- GitHub's own delivery log -------------------------------------------------------


def deliveries(composed: SandboxBacklogComposition, pages: int = 3) -> list[dict]:
    collected: list[dict] = []
    cursor = ""
    for _ in range(pages):
        document_ = composed.credentials.application_call("GET", f"/app/hook/deliveries?per_page=100{cursor}")
        listed = [entry for entry in (document_.get("items") or []) if isinstance(entry, dict)]
        collected += listed
        if len(listed) < 100:
            break
        cursor = f"&cursor={listed[-1].get('id')}"
    return collected


def redeliver(composed: SandboxBacklogComposition, delivery_id: object) -> str:
    try:
        composed.credentials.application_call("POST", f"/app/hook/deliveries/{delivery_id}/attempts", expected=202)
        return "requested"
    except Exception as error:  # noqa: BLE001 - the outcome is recorded
        return f"refused: {type(error).__name__}"


# --- seeding ---------------------------------------------------------------------------


def e1_contract(identity: str, priority: str, hold: int, purpose: str) -> dict:
    contract = seed_contract(identity, priority, purpose=purpose)
    contract["authority_issuer"] = "FX-E1 live transport proof (WO-220502)"
    contract["authority_references"] = ["SWF-08", "SWF-34", "EXPLICIT_LIVE_TRANSPORT_PROOF_AUTHORITY", "AlienLogicLab/alienintent#122"]
    contract["task"]["hold_seconds"] = hold
    return contract


def publish_contracts(record: dict, token: str, contracts: list[dict]) -> str:
    environment = credentialed_git_environment(record, token)
    repository = str(record["repository"])
    with tempfile.TemporaryDirectory(prefix="fx-e1-seed-") as scratch:
        checkout = Path(scratch) / "checkout"
        git("clone", "--quiet", f"https://github.com/{repository}.git", str(checkout), environment=environment)
        for contract in contracts:
            write_json(checkout / "biu" / f"{contract['identity']}.json", contract)
        git("add", "-A", cwd=checkout, environment=environment)
        git("-c", "user.name=AlienIntent FX-E1 seeding", "-c", "user.email=fx-e1@alienintent.invalid",
            "commit", "--quiet", "-m", f"FX-E1: seed {', '.join(c['identity'] for c in contracts)} (WO-220502)",
            cwd=checkout, environment=environment)
        git("push", "--quiet", "origin", "HEAD:refs/heads/main", cwd=checkout, environment=environment)
        return git("rev-parse", "HEAD", cwd=checkout, environment=environment).stdout.strip()


def seed_items(projects: GitHubProjectsV2Directory, writer: SeedWriter, contracts: list[dict]) -> list[dict]:
    seeded = []
    for contract in contracts:
        item = projects.add_draft_item(seed_title(contract), seed_body(contract))
        writer.set_field(item, "Priority", contract["task"]["priority"])
        writer.set_field(item, "Status", "READY")
        observed = projects.read_status(item)
        seeded.append({"identity": contract["identity"], "item": item, "status": observed.status,
                       "priority": observed.priority, "ready_since": observed.status_updated_at})
        time.sleep(READY_SPACING_SECONDS)
    return seeded


# --- static dependency path ---------------------------------------------------------------


def dependency_path(environment: dict[str, str]) -> dict:
    """The module closure the production path adds, and Node invocations in its source.

    Interpreter start-up (`site` and the host's `.pth` hooks) loads modules before
    any application code runs; they are recorded separately and are not part of
    the closure. The closure is what importing the control plane and the sandbox
    composition adds on top of that start-up set.
    """
    probe = (
        "import json, sys, sysconfig\n"
        "def files():\n"
        "    return {getattr(m, '__file__', None) or '' for m in list(sys.modules.values())} - {''}\n"
        "startup = files()\n"
        "import alienintent.control_plane.adapters.cli, alienintent.composition.sandbox_run_profile\n"
        "print(json.dumps({'stdlib': sysconfig.get_paths()['stdlib'], 'startup': sorted(startup), 'closure': sorted(files() - startup)}))\n"
    )
    answer = subprocess.run([sys.executable, "-c", probe], cwd=ROOT, env=environment, capture_output=True, text=True, check=False)
    loaded = json.loads(answer.stdout or "{}")
    source = str(ROOT / "src" / "alienintent")
    stdlib = loaded.get("stdlib", "")
    closure, startup = loaded.get("closure", []), loaded.get("startup", [])
    other = [path for path in closure if not path.startswith(source) and not path.startswith(stdlib)]
    references = []
    for path in sorted((ROOT / "src" / "alienintent").rglob("*.py")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if NODE_REFERENCE.search(line):
                references.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()[:160]}")
    return {
        "exit_status": answer.returncode,
        "modules_loaded": len(closure),
        "alienintent_modules": sum(path.startswith(source) for path in closure),
        "stdlib_modules": sum(path.startswith(stdlib) for path in closure),
        "modules_outside_stdlib_and_alienintent": other,
        "interpreter_startup_modules_outside_stdlib": [path for path in startup if not path.startswith(stdlib)],
        "node_references_in_python_source": references,
        "node_reference_pattern": NODE_REFERENCE.pattern,
    }


# --- local scope controls on the real resident process ------------------------------------


def local_post(port: int, event: str, delivery: str, body: bytes, signature: str) -> int:
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/webhook", data=body, method="POST",
        headers={"X-GitHub-Event": event, "X-GitHub-Delivery": delivery, "X-Hub-Signature-256": signature,
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as answer:
            return answer.status
    except urllib.error.HTTPError as error:
        return error.code


def scope_controls(composed: SandboxBacklogComposition, port: int, database: Path, run_id: str) -> list[dict]:
    secret = composed.secrets.resolve(composed.profile.webhook_secret_reference)
    foreign = json.dumps({"action": "edited", "projects_v2_item": {
        "node_id": "PVTI_fx_e1_foreign", "project_node_id": "PVT_fx_e1_project_this_profile_does_not_target",
        "content_node_id": "DI_fx_e1_foreign"}}).encode()
    own = json.dumps({"action": "edited", "projects_v2_item": {
        "node_id": "PVTI_fx_e1_unsigned", "project_node_id": composed.profile.project_reference,
        "content_node_id": "DI_fx_e1_unsigned"}}).encode()
    cases = (
        ("unsigned_delivery_for_the_configured_project", own, ""),
        ("wrong_secret_delivery_for_the_configured_project", own, "sha256=" + hmac.new(b"not-the-sandbox-secret", own, sha256).hexdigest()),
        ("correctly_signed_delivery_for_a_foreign_project", foreign, "sha256=" + hmac.new(secret, foreign, sha256).hexdigest()),
    )
    results = []
    for name, body, signature in cases:
        delivery = f"fx-e1-{run_id}-{name}"
        status = local_post(port, "projects_v2_item", delivery, body, signature)
        admitted = any(row["event_id"] == delivery for row in receipts(database))
        results.append({"control": name, "http_status": status, "durable_receipt_created": admitted,
                        "label": "LOCAL mechanical scope control against the real resident ingress process; not operational proof"})
    try:
        composed.address.resolve("PVT_fx_e1_project_this_profile_does_not_target", None)
        results.append({"control": "foreign_project_address_resolution", "refused": False})
    except ProjectAddressRejected as error:
        results.append({"control": "foreign_project_address_resolution", "refused": True, "detail": str(error)})
    return results


# --- readback ---------------------------------------------------------------------------------


def candidate_readback(record: dict, token: str, identities: list[str]) -> list[dict]:
    """Every seeded BIU's published candidate, read back from a fresh clone."""
    branches = published_candidates(record, token)
    environment = credentialed_git_environment(record, token)
    repository = str(record["repository"])
    results = []
    with tempfile.TemporaryDirectory(prefix="fx-e1-readback-") as scratch:
        clone = Path(scratch) / "fresh"
        git("clone", "--quiet", "--no-local", f"https://github.com/{repository}.git", str(clone), environment=environment)
        git("fetch", "--quiet", "origin", "+refs/heads/*:refs/remotes/origin/*", cwd=clone, environment=environment, check=False)
        for identity in identities:
            matching = {name: revision for name, revision in branches.items() if name.startswith("candidate/") and identity in name}
            for branch, revision in sorted(matching.items()):
                shown = git("show", f"{revision}:docs/{identity}.md", cwd=clone, environment=environment, check=False)
                results.append({
                    "identity": identity, "branch": branch, "revision": revision,
                    "note_read_back": shown.returncode == 0 and f"# {identity}" in shown.stdout,
                    "note_excerpt": shown.stdout.strip().splitlines()[-1][:200] if shown.stdout.strip() else "",
                })
            if not matching:
                results.append({"identity": identity, "branch": None, "revision": None, "note_read_back": False})
    return results


# --- the run ----------------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="FX-E1 live proof")
    parser.add_argument("--apply", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--state-parent", type=Path, default=DEFAULT_STATE_PARENT)
    arguments = parser.parse_args(argv)

    fixture = ROOT / "docs/evidence/wave2-proof-fixtures/FX-E1"
    plan_path, identification_path = fixture / "fixture-plan.json", fixture / "identification.json"
    if not plan_path.is_file() or not identification_path.is_file():
        raise SystemExit("FX-E1 fixture plan and identification must be pinned before any live call")
    revision = git("rev-parse", "HEAD", cwd=ROOT).stdout.strip()
    pinned = {
        "source_revision": revision,
        "source_clean": git("status", "--porcelain", "--", "src", "tools/live", cwd=ROOT).stdout.strip() == "",
        "fixture_plan_digest": "sha256:" + sha256(plan_path.read_bytes()).hexdigest(),
        "identification_digest": "sha256:" + sha256(identification_path.read_bytes()).hexdigest(),
        "fixture_plan_committed_before_run": git("log", "-1", "--format=%H", "--", str(plan_path.relative_to(ROOT)), cwd=ROOT).stdout.strip() != "",
        "identification_committed_before_run": git("log", "-1", "--format=%H", "--", str(identification_path.relative_to(ROOT)), cwd=ROOT).stdout.strip() != "",
    }

    record = document()
    redact = Redactor(record)
    profile = compose_profile(record)
    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    tag = time.strftime("%d%H%M", time.gmtime())
    state = arguments.state_parent / run_id
    state.mkdir(parents=True, exist_ok=True)
    output = arguments.output
    observations = Observations(output / "observations", redact)
    database, notifications_log = state / "state.sqlite", state / "ingress-notifications.jsonl"

    # --- the instrument precedes every live call.
    instrument_test = self_test()
    if not instrument_test["ok"]:
        raise SystemExit("the no-Node instrument does not discriminate; no live call was made")
    instrument = NoNodeInstrument(state)
    os.environ["PATH"] = instrument.environment()["PATH"]
    instrument.sampler.watch(os.getpid())
    phases: list[dict] = []
    started_at = now()

    with instrument:
        static = dependency_path(dict(os.environ) | {"PYTHONPATH": str(ROOT / "src")})
        before = {"at": now(), "node_writer": node_writer_observation()}

        # --- live from here on.
        minted = credentials(record)
        token = minted.token().value
        transport = UrllibGitHubTransport()
        projects = GitHubProjectsV2Directory(profile.project_address(), transport, minted.authorization)
        writer = SeedWriter(profile.project_address(), transport, minted.authorization)
        identities = [f"E1-{tag}-A", f"E1-{tag}-B"]
        contracts = [
            e1_contract(identities[0], "P0", HOLD_SECONDS, "in flight when the run process is killed; must survive restart"),
            e1_contract(identities[1], "P1", 0, "dispatched by a restarted process after the process loss"),
        ]
        seed_revision = publish_contracts(record, token, contracts)
        seeded = seed_items(projects, writer, contracts)
        phases.append({"phase": "seed", "seed_revision": seed_revision, "items": seeded,
                       "statuses_written_by_seeding": ["READY"], "observation": observations.retain("seed", {"contracts": contracts, "items": seeded})})

        checkout = state / "repository"
        baseline = prepare_checkout(record, token, checkout)
        environment = credentialed_git_environment(record, token) | {
            "ALIENINTENT_SANDBOX_PROFILE": str(profile_path()),
            "ALIENINTENT_SANDBOX_STATE": str(state),
            "ALIENINTENT_SANDBOX_CHECKOUT": str(checkout),
            "ALIENINTENT_SANDBOX_WORKER_COMMAND": json.dumps(["/bin/bash", str(WORKER)]),
            "PYTHONPATH": str(ROOT / "src"),
        }
        operator = Operator(environment, instrument, run_id)
        composed = SandboxBacklogComposition(record, state / "isolation.sqlite", lambda _: None)
        before["published_branches"] = published_candidates(record, token)
        before["sandbox_baseline"] = baseline
        isolation = {"findings": list(composed.isolation_findings()),
                     "repository_scope": list(composed.credentials.repositories())}

        # --- doctor: the live readiness gate the run itself enforces.
        doctor = operator.invoke("doctor", timeout=600)
        phases.append({"phase": "doctor", "process": "doctor", "exit_status": doctor["exit_status"],
                       "report": doctor["stdout"], "observation": observations.retain("doctor", doctor)})
        if doctor["exit_status"] != 0:
            raise SystemExit("doctor did not pass; the live run was not started")

        # --- process A: run until the held BIU owns the slot, then kill it.
        started = time.time()
        process_a = operator.launch("run", "service", "--actor", ACTOR, "--authority", AUTHORITY,
                                    "--intent", "FX-E1 drain the seeded backlog", "--expected-version", "0",
                                    "--reason", "FX-E1 live transport proof", "--idempotency-key", f"{run_id}-run-a")
        reservation = wait_for_dispatch(database, time.time() + DISPATCH_WAIT_SECONDS)
        listener_a = listener_owner(profile.webhook_listen_port)
        if reservation is None:
            os.killpg(os.getpgid(process_a.pid), signal.SIGKILL)
            operator.finish(process_a, ("run", "service"), started, 30)
            raise SystemExit("no dispatch was observed; the run cannot be interrupted mid-work")
        time.sleep(KILL_AFTER_DISPATCH_SECONDS)
        before_kill = store_state(database)
        killed_at = time.time()
        os.killpg(os.getpgid(process_a.pid), signal.SIGKILL)
        entry_a = operator.finish(process_a, ("run", "service"), started, 60)
        after_kill = store_state(database)
        phases.append({
            "phase": "process-loss", "process": "A", "pid": process_a.pid, "window": [started, killed_at],
            "signal": "SIGKILL", "exit_status": entry_a["exit_status"], "held_reservation": reservation,
            "ingress_listener": listener_a, "store_before_kill": before_kill, "store_after_kill": after_kill,
            "effect_unresolved_at_kill": any(effect["status"] not in ("confirmed", "succeeded") for effect in after_kill["effects"]
                                             if effect["identity"].startswith("launch:")),
            "observation": observations.retain("process-A", {"entry": entry_a, "before": before_kill, "after": after_kill}),
        })

        # --- process B: restart, recovery.
        restarted = operator.mutation("run", "service", expected_version=0, intent="FX-E1 resume after the process loss", key="run-b")
        phases.append({"phase": "restart", "process": "B", "pid": restarted["pid"], "window": [restarted["started_at"], restarted["ended_at"]],
                       "exit_status": restarted["exit_status"], "summary": restarted["stdout"],
                       "observation": observations.retain("process-B", restarted)})

        # --- decisions raised for the seeded work, answered through the control plane.
        listed = operator.invoke("decisions", "list")
        requests = [request for request in (listed["stdout"] if isinstance(listed["stdout"], list) else [])
                    if request.get("work_item") in identities]
        phases.append({"phase": "decisions-open", "requests": requests, "observation": observations.retain("decisions-list", listed)})
        for index, request in enumerate(requests):
            work_item = request["work_item"]
            current = store_state(database)["aggregates"].get(f"factory:{work_item}", {}).get("revision", 0)
            decided = operator.mutation("decisions", "decide", work_item, expected_version=current,
                                        intent=f"authorize {work_item} to resume through normal admission guards (FX-E1)",
                                        key=f"decision-{index}", choice="authorize", biu_version=str(request["biu_version"]))
            phases.append({"phase": "decision", "work_item": work_item, "pid": decided["pid"], "exit_status": decided["exit_status"],
                           "record": decided["stdout"], "observation": observations.retain("decision", decided)})

        # --- process C: drain to exhaustion.
        final = operator.mutation("run", "service", expected_version=0, intent="FX-E1 confirm the backlog is exhausted", key="run-c")
        phases.append({"phase": "drain-to-exhaustion", "process": "C", "pid": final["pid"], "window": [final["started_at"], final["ended_at"]],
                       "exit_status": final["exit_status"], "summary": final["stdout"], "observation": observations.retain("process-C", final)})
        status = operator.invoke("status")
        explained = {identity: operator.invoke("explain", identity)["stdout"] for identity in identities}
        phases.append({"phase": "status", "status": status["stdout"], "explain": explained,
                       "observation": observations.retain("status", {"status": status, "explain": explained})})

        # --- process D: the ingress restarted once more; a delivery an earlier process admitted is redelivered.
        admitted_before = {row["event_id"]: row for row in receipts(database)}
        recorded = deliveries(composed)
        # Every control-plane process is resident while it lives, so each one's
        # window attributes the deliveries it may have admitted.
        named = {process_a.pid: "A", restarted["pid"]: "B", final["pid"]: "C"}
        processes = {"A": (started, killed_at)} | {
            named.get(entry["pid"], f"{entry['command'][1]}@{entry['pid']}"): (entry["started_at"], entry["ended_at"])
            for entry in operator.transcript if entry["pid"] != process_a.pid
        }

        def admitting_process(entry: dict) -> str | None:
            moment = iso_epoch(entry.get("delivered_at"))
            for name, (low, high) in processes.items():
                if moment is not None and low - 2 <= moment <= high + 2:
                    return name
            return None

        window = [entry for entry in recorded if (iso_epoch(entry.get("delivered_at")) or 0) >= started - 2]
        admitted_earlier = [entry for entry in window if entry.get("status_code") == 202 and entry.get("guid") in admitted_before]
        admitted_earlier.sort(key=lambda entry: (admitting_process(entry) != "A", entry.get("delivered_at") or ""))
        stop = state / "resident.stop"
        resident_started = time.time()
        resident = subprocess.Popen([sys.executable, str(ROOT / "tools/live/fx_e1_resident.py"), str(stop)], cwd=ROOT,
                                    env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        instrument.sampler.watch(resident.pid)
        ready_line = resident.stdout.readline().strip() if resident.stdout else ""
        listener_d = listener_owner(profile.webhook_listen_port)
        replay: dict = {"available": bool(admitted_earlier)}
        if admitted_earlier:
            target = admitted_earlier[0]
            guid = str(target["guid"])
            receipt_before = admitted_before[guid]
            effect_before = [effect for effect in full_effects(database) if effect["identity"] == f"ingress:{guid}"]
            lines_before = len(notification_lines(notifications_log))
            requested = redeliver(composed, target["id"])
            attempt: dict | None = None
            deadline = time.time() + REDELIVERY_WAIT_SECONDS
            while time.time() < deadline and attempt is None:
                time.sleep(5)
                attempt = next((entry for entry in deliveries(composed, pages=1)
                                if entry.get("guid") == guid and entry.get("redelivery") and entry.get("id") != target["id"]), None)
            time.sleep(5)
            receipt_after = next((row for row in receipts(database) if row["event_id"] == guid), None)
            effect_after = [effect for effect in full_effects(database) if effect["identity"] == f"ingress:{guid}"]
            replay |= {
                "guid": guid, "originally_admitted_by": admitting_process(target), "original_status_code": target.get("status_code"),
                "redelivery_request": requested,
                "redelivery_status_code": attempt.get("status_code") if attempt else None,
                "redelivered_at": attempt.get("delivered_at") if attempt else None,
                "receipt_before": receipt_before, "receipt_after": receipt_after,
                "receipt_unchanged": receipt_after == receipt_before,
                "effect_before": effect_before, "effect_after": effect_after,
                "notification_lines_before": lines_before, "notification_lines_after": len(notification_lines(notifications_log)),
            }
        controls = scope_controls(composed, profile.webhook_listen_port, database, run_id)
        stop.write_text(now(), encoding="utf-8")
        try:
            resident.wait(timeout=30)
        except subprocess.TimeoutExpired:
            resident.kill()
        phases.append({"phase": "ingress-restart", "process": "D", "pid": resident.pid,
                       "window": [resident_started, time.time()], "ready": ready_line.startswith("resident"),
                       "ingress_listener": listener_d, "replay": replay, "scope_controls": controls,
                       "observation": observations.retain("process-D", {"replay": replay, "controls": controls})})

        # --- readback.
        token = credentials(record).token().value
        project_readback = []
        for item in seeded:
            observed = projects.read_status(item["item"])
            project_readback.append({"identity": item["identity"], "item": item["item"], "status": observed.status,
                                     "status_updated_at": observed.status_updated_at})
        processes["D"] = (resident_started, time.time())
        recorded = deliveries(composed)
        window = [entry for entry in recorded if (iso_epoch(entry.get("delivered_at")) or 0) >= started - 2]
        durable = {row["event_id"]: row for row in receipts(database)}
        delivery_log = [{
            "guid": entry.get("guid"), "event": entry.get("event"), "action": entry.get("action"),
            "delivered_at": entry.get("delivered_at"), "status_code": entry.get("status_code"),
            "redelivery": entry.get("redelivery"), "process": admitting_process(entry),
            "durable_receipt": entry.get("guid") in durable,
        } for entry in window]
        readback = {
            "store": {"state": store_state(database), "effects": full_effects(database), "receipts": list(durable.values())},
            "project": project_readback,
            "candidates": candidate_readback(record, token, identities),
            "deliveries": delivery_log,
            "notifications": notification_lines(notifications_log),
        }
        readback["observation"] = observations.retain("readback", readback)
        after = {"at": now(), "node_writer": node_writer_observation(), "published_branches": published_candidates(record, token)}

    run_record = {
        "record_kind": "FxE1ProofRun", "schema_version": "1", "fixture_id": "FX-E1", "work_unit": "WO-220502",
        "run_id": run_id, "profile": profile.profile, "repository": profile.repository, "project": profile.project_reference,
        "actor": ACTOR, "authority": AUTHORITY, "pinned": pinned, "identities": identities,
        "started_at": started_at, "finished_at": now(),
        "substitutions": [{
            "what": "worker note author",
            "substitute": "tools/live/fx_e1_worker.sh writes the note deterministically instead of a provider CLI",
            "unchanged": "the worker is launched by the shipped CliWorkerProvider through RealWorkerProvider and RoleBindingGuard; "
                         "the control plane publishes and reads back the candidate with the installation credential",
            "claims_nothing_about": "provider behaviour, provider spend or provider helper processes",
        }],
        "instrument_self_test": instrument_test, "no_node": instrument.report(), "dependency_path": static,
        "isolation": isolation, "before": before, "after": after, "phases": phases, "readback": readback,
        "operator_transcript": observations.retain("operator-transcript", operator.transcript),
        "tokens_and_cost": "UNKNOWN (no provider was invoked by the run; the PRODUCER session's own usage is not exposed)",
    }
    run_record["verdict"] = evaluate(run_record)
    # One record per run, so a held run is preserved rather than overwritten on repair.
    destination = output / "runs" / run_id / "proof-run.json"
    write_json(destination, redact(run_record))
    print(json.dumps({"proof_run": str(destination), "verdict": run_record["verdict"]["disposition"],
                      "predicates": {p["id"]: p["outcome"] for p in run_record["verdict"]["predicates"]}}, indent=1))
    return 0 if run_record["verdict"]["disposition"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
