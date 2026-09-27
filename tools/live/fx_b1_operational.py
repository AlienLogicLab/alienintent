"""FX-B1 operational run (WO-220504): live trajectory receipts on the bound fx-b1 target.

`run` provisions the bound profile root, launches the B1P capture under real `systemd --user`
C5 supervision, seeds every anomaly class, consumes the journal with the trajectory-receipts
attention producer, kills and restarts the capture through C5's alert and granted restart,
consumes again, reads everything back and tears the transient units down. The root and its
stores are retained. `readback` reads a retained root without launching anything.

Every CLI runs under `tools/live/fx_b1_audit.py`, and this process audits itself, so the record
binds every path the proof touched. Nothing here reads `alienintent-observer.service` data or
factory state: any touched path under the factory state directory outside the bound root and
this checkout is a HOLD. A missing readback is a HOLD, never a PASS.
"""
from hashlib import sha256
import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import fx_b1_audit  # noqa: E402

STATE = Path.home() / ".local/state/alienintent"
BOUND_PARENT = STATE / "fx-b1"
DEFAULT_ROOT = BOUND_PARENT / "trajectory"
PROFILE = "fx-b1-trajectory-operational"
PROJECT = "alienintent"
ACTOR = "factory-director"
AUTHORITY = "founder-authorize-local-live-proof-target-20260927T0102Z"
JUDGMENT = "founder-judgment"
STALL_SECONDS = 2
KINDS = ("CAPTURE_STALL", "DUPLICATE_IDENTITY", "OUT_OF_ORDER", "SEQUENCE_GAP", "TIMESTAMP_REGRESSION")
CAPTURE = "alienintent.composition.trajectory_capture"
RECEIPTS = "alienintent.composition.trajectory_receipts"
INBOX = "alienintent.composition.attention_inbox"
NON_CLAIMS = (
    "No claim that alienintent-observer.service is replaced, retired, read or perturbed; no observer data was read.",
    "'Old/new observations across cutover' are this composition's own pre/post-restart observations (disposed "
    "2026-09-27); no other observation source is compared.",
    "No claim that this run substitutes for FX-B1P; B1P composition-level evidence is cited, not re-claimed.",
    "No release, migration cutover, persistent unit installation, notification, acknowledgement, resolution or "
    "activation is performed or authorized.",
)


def inside(path, parent):
    path, parent = os.path.normpath(str(path)), os.path.normpath(str(parent))
    return path == parent or path.startswith(parent + os.sep)


def forbidden_touches(paths, protected, allowed):
    """Every audited path under `protected` that is not inside one of the `allowed` subtrees, with
    symlinks resolved on both sides. An undecodable path is always forbidden."""
    paths = [p if p.startswith("UNDECODABLE:") else os.path.realpath(p) for p in paths]
    protected, allowed = os.path.realpath(protected), [os.path.realpath(a) for a in allowed]
    return sorted({p for p in paths if p.startswith("UNDECODABLE:")
                   or inside(p, protected) and not any(inside(p, a) for a in allowed)})


EXECUTABLES = frozenset({os.path.basename(sys.executable), "python3", "systemd-run", "systemctl", "env"})


def read_audit(log):
    """The audit log as touched paths and child-process argument vectors."""
    records = [json.loads(line) for line in Path(log).read_text().splitlines()] if Path(log).exists() else []
    return {"paths": sorted({r for r in records if isinstance(r, str)}),
            "executions": [r["exec"] for r in records if isinstance(r, dict)]}


def guard_root(root, bound_parent=BOUND_PARENT):
    """Refusals, decided before anything is written; empty means the root may be provisioned."""
    root = Path(os.path.abspath(root))
    holds = []
    if not inside(root, bound_parent) or root == Path(os.path.abspath(bound_parent)):
        holds.append("ROOT_OUTSIDE_BOUND_TARGET")
    if root.exists():
        if not root.is_dir():
            holds.append("ROOT_NOT_A_DIRECTORY")
        elif any(root.iterdir()):
            holds.append("ROOT_NOT_EMPTY")
        if (root / "state.json").exists():
            holds.append("ROOT_CONTAINS_FACTORY_STATE")
    return holds


def canonical(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False, default=str).encode()


def digest(body):
    return "sha256:" + sha256(body).hexdigest()


def retain(output, record):
    body = canonical(record)
    name = sha256(body).hexdigest()
    target = output / "observations" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.read_bytes() != body:
            raise RuntimeError("immutable observation collision")
    else:
        with target.open("xb") as stream:
            stream.write(body)
    return {"revision_digest": "sha256:" + name, "locator": "observations/" + name}


def environment():
    return {**os.environ, "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1",
            "XDG_RUNTIME_DIR": os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"}


def systemctl(*arguments):
    return subprocess.run(["systemctl", "--user", *arguments], env=environment(), capture_output=True, text=True,
                          check=False)


def until(predicate, timeout, what):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.1)
    raise TimeoutError("timed out waiting for " + what)


class Run:
    def __init__(self, output, audit_log):
        self.output, self.audit_log, self.commands = output, audit_log, []

    def cli(self, stage, module, *arguments, stdin=None):
        argv = [sys.executable, "-B", str(ROOT / "tools/live/fx_b1_audit.py"), str(self.audit_log), "-m", module,
                *arguments]
        result = subprocess.run(argv, cwd=ROOT, env=environment(), input=stdin, capture_output=True, text=True,
                                timeout=120)
        observation = {"stage": stage, "argv": argv, "stdin": stdin, "exit_status": result.returncode,
                       "stdout": result.stdout, "stderr": result.stderr}
        self.commands.append({"stage": stage, "argv": argv, "exit_status": result.returncode,
                              "observation_ref": retain(self.output, observation)})
        lines = result.stdout.strip().splitlines()
        try:
            return result.returncode, json.loads(lines[-1]) if lines else None
        except ValueError:
            return result.returncode, None


def event(seq, observed=None, source="fx-b1-source"):
    return {"source": source, "source_seq": seq, "observed_at": 1_790_000_000_000_000 + (observed or seq) * 1_000_000,
            "event": {"schema_version": "1.0", "event_id": f"{source}-{seq:03d}", "event_type": "TOOL_CALL",
                      "actor_role": "FACTORY", "description": f"synthetic FX-B1 operational event {seq}"}}


def lines(*documents):
    return "".join(json.dumps(d) + "\n" for d in documents)


def config_document(root, invocation):
    return {"schema_version": 1, "mode": "systemd", "project": PROJECT, "profile": PROFILE,
            "host_invocation": invocation, "root": str(root), "source_root": str(ROOT / "src"),
            "python": sys.executable, "systemd_run": shutil.which("systemd-run"),
            "systemctl": shutil.which("systemctl"), "env": shutil.which("env"),
            "policy": {"grace_seconds": 300, "interval_seconds": 1, "confirmation_seconds": 90,
                       "startup_seconds": 15, "stop_seconds": 5, "observe_seconds": 0.5},
            "host_actors": [ACTOR], "host_authority": AUTHORITY, "alert_authority": JUDGMENT,
            "judgment_authority": JUDGMENT, "capture": {"stall_seconds": STALL_SECONDS}}


def git(*argv):
    return subprocess.check_output(["git", *argv], cwd=ROOT, text=True).strip()


def receipt_items(listed, stream):
    return sorted((i for i in (listed or []) if i.get("work_ref") == "trajectory-capture:" + stream),
                  key=lambda i: i["identity"])


def predicates(readback, stream):
    """Each packet acceptance criterion, decided only from retained readback."""
    acks = readback["acks"]
    journal = readback["journal_after"]["entries"]
    before = [e["event"] for e in readback["journal_before"]["entries"] if e["kind"] == "EVENT"]
    events = [e["event"] for e in journal if e["kind"] == "EVENT"]
    captured = {a["ack"]["event_id"]: a["ack"] for a in acks if a["ack"].get("status") == "CAPTURED"}
    by_id = {e["event_id"]: e for e in events}
    kinds = sorted({a["kind"] for e in journal for a in e["anomalies"]})
    sessions = [e for e in journal if e["kind"] == "SESSION"]
    reconciliation = readback["receipts"]["reconciliation"]
    chain = readback["receipts"]["receipts"]
    items_1, items_down, items_3 = (readback["produced"][k] or [] for k in ("after_consume_1", "while_down", "final"))
    pending = receipt_items(readback["queue"]["final"], stream)
    down = readback["submission_while_down"]["replies"]
    observed = [e["event"] for r in chain for e in r["entries"] if e["event"]]
    result = {
        "identity_order_timestamps_stable": (
            len(captured) == 7 and len(before) == 6 and len(events) == 7
            and events[:len(before)] == before
            and [e["capture_seq"] for e in events] == list(range(1, len(events) + 1))
            and all(x["captured_at"] <= y["captured_at"] for x, y in zip(events, events[1:]))
            and all((by_id[k]["capture_seq"], by_id[k]["identity"], by_id[k]["captured_at"]) ==
                    (v["capture_seq"], v["identity"], v["captured_at"]) for k, v in captured.items())),
        "five_anomaly_classes_durable": set(KINDS) <= set(kinds),
        "no_loss_no_duplication_queue_retained": (
            len(by_id) == len(events) and set(by_id) == set(captured)
            and readback["retry"].get("status") == "DUPLICATE"
            and len(down) == 1 and all("hold" in r for r in down)
            and items_1 == items_down and len(items_1) == 5
            and all(i in items_3 for i in items_1)
            and len({i["event_identity"] for i in items_3}) == len(items_3)),
        "pre_post_restart_reconcile": (
            reconciliation.get("reconciled") is True
            and [s["launch_id"] for s in sessions] == [readback["launch_1"], readback["launch_2"]]
            and sessions[1]["session"]["reconciled"]["entries"] == len(readback["journal_before"]["entries"])
            and sessions[1]["session"]["reconciled"]["events"] == len(before)
            and readback["consume"]["while_down"].get("status") == "UP_TO_DATE"
            and readback["consume"]["idempotent"].get("status") == "UP_TO_DATE"
            and readback["consume"]["after_restart"].get("from_entry") ==
                readback["consume"]["before_kill"].get("to_entry", -1) + 1),
        "attention_producer_observes_receipts": (
            sorted(o["capture_seq"] for o in observed) == [e["capture_seq"] for e in events]
            and all(by_id[o["event_id"]]["identity"] == o["identity"] for o in observed)
            and len(items_3) == reconciliation.get("anomalies") == 7
            and {i["status"] for i in items_3} == {"PENDING"} and {i["kind"] for i in items_3} == {"JUDGMENT"}
            and sorted(i["identity"] for i in pending) == sorted(i["identity"] for i in items_3)),
        "observer_boundary_and_disjointness": (
            readback["root_guard"] == [] and readback["audit"]["forbidden"] == []
            and readback["audit"]["unexpected_executions"] == [] and readback["audit"]["executions"] > 0
            and readback["audit"]["paths"] > 0 and readback["audit"]["root_touched"]
            and readback["units_after_teardown"].strip() == ""),
    }
    return {k: "PASS" if v else "HOLD" for k, v in result.items()}


def operate(root, output, invocation, run, readback):
    config = root / "fx-b1-supervision.json"
    stream = readback["stream"]
    config.write_text(json.dumps(config_document(root, stream), indent=2) + "\n")
    (root / "attention-inbox.json").write_text(json.dumps({"root": str(root), "project": PROJECT, "profile": PROFILE,
        "invocation": invocation, "acknowledgers": []}, indent=2) + "\n")
    readback["config_digest"] = digest(config.read_bytes())
    from alienintent.composition.monitor_host import load_config
    from alienintent.composition.trajectory_capture import TrajectoryCaptureProfile, read_journal, socket_path

    class Refuse:
        def __getattr__(self, name):
            raise AssertionError("read-only view called the manager: " + name)

    loaded = load_config(config)
    profile = TrajectoryCaptureProfile(loaded, config, manager=Refuse())
    unit = loaded.binding().unit
    observer = unit.removesuffix(".service").replace("alienintent-monitor-", "alienintent-monitor-observer-")
    readback |= {"unit": unit, "monitor_observer": observer}
    c = ("--config", str(config))

    def ownership():
        return profile.records.read(PROFILE)[1]

    def session_of(launch_id):
        try:
            return any(e["kind"] == "SESSION" and e["launch_id"] == launch_id
                       for e in read_journal(loaded)["entries"]) and socket_path(loaded).exists()
        except Exception:
            return False

    def submit(stage, *documents):
        code, reply = run.cli(stage, CAPTURE, "submit", *c, stdin=lines(*documents))
        replies = (reply or {}).get("replies", [])
        for document, ack in zip(documents, replies):
            readback["acks"].append({"stage": stage, "submitted": document["event"]["event_id"],
                                     "source_seq": document["source_seq"], "ack": ack})
        return code, replies

    def consume(stage):
        code, result = run.cli(stage, RECEIPTS, "consume", *c, "--consumer", f"{invocation}:{stage}")
        readback["consume"][stage] = result or {"hold": "NO_OUTPUT", "exit_status": code}

    def queue(stage):
        """The pending queue through the independent C1 reader, and every status of this producer's items."""
        _, listed = run.cli("queue:" + stage, INBOX, "list", "--config", str(root / "attention-inbox.json"))
        readback["queue"][stage] = listed
        _, receipted = run.cli("receipts:" + stage, RECEIPTS, "receipts", *c)
        readback["produced"][stage] = (receipted or {}).get("attention")

    try:
        code, launched = run.cli("launch", CAPTURE, "launch", *c, "--actor", ACTOR, "--authority", AUTHORITY)
        if code != 0:
            raise RuntimeError(f"launch failed: {launched}")
        readback["launch_1"] = launched["launch_id"]
        until(lambda: session_of(launched["launch_id"]), 60, "the capture session of launch 1")
        until(lambda: (o := ownership()).state == "RUNNING" and o.systemd_invocation_id, 60, "launch bound")

        submit("seed", *(event(s) for s in (1, 2, 3)), event(6), event(4, observed=6), event(2), event(7, observed=1))
        until(lambda: any(a["kind"] == "CAPTURE_STALL" for e in read_journal(loaded)["entries"] for a in e["anomalies"]),
              STALL_SECONDS * 10, "the capture stall record")
        consume("before_kill")
        queue("after_consume_1")
        readback["journal_before"] = read_journal(loaded)

        killed_at = datetime.now(UTC).isoformat()
        kill = systemctl("kill", "--signal=SIGKILL", "--kill-whom=main", unit)
        killed = until(lambda: (o := ownership()).state == "ALERTED" and o, 120, "the termination alert")
        readback["kill"] = {"at": killed_at, "exit_status": kill.returncode, "alert_reason": killed.alert_reason,
                            "alert": killed.alert, "launch_id": killed.launch_id}
        code, down = submit("while_down", event(8))
        readback["submission_while_down"] = {"exit_status": code, "replies": down,
                                             "accepted": any("hold" not in r for r in down)}
        consume("while_down")
        queue("while_down")

        code, restarted = run.cli("restart", CAPTURE, "restart", *c, "--actor", ACTOR, "--authority", AUTHORITY,
                                  "--replaces", killed.launch_id, "--alert", killed.alert)
        if code != 0:
            raise RuntimeError(f"restart failed: {restarted}")
        readback["launch_2"] = restarted["launch_id"]
        until(lambda: session_of(restarted["launch_id"]), 60, "the capture session of launch 2")
        _, retry = submit("retry", event(7, observed=1))
        _, fresh = submit("after_restart", event(9))
        readback["retry"], readback["fresh"] = (retry or [{}])[0], (fresh or [{}])[0]
        consume("after_restart")
        consume("idempotent")

        _, readback["journal_after"] = run.cli("journal", CAPTURE, "journal", *c)
        _, readback["receipts"] = run.cli("receipts", RECEIPTS, "receipts", *c)
        queue("final")
        readback["monitor_starts"] = [(h["record"]["instance_id"], h["record"]["generation"])
                                      for h in profile.monitor.repository.history(PROFILE)
                                      if h["observation"]["action"] == "STARTED"]
        readback["ownership_final"] = str(ownership())
    finally:
        systemctl("stop", observer + ".timer", observer + ".service")
        systemctl("kill", "--signal=SIGKILL", "--kill-whom=all", unit)
        systemctl("stop", unit)
        systemctl("reset-failed", unit, observer + ".service")
        readback["units_after_teardown"] = systemctl("list-units", "--all", "--no-legend", unit,
                                                     observer + ".*").stdout


def run_operational(root, output, invocation):
    root, output = Path(os.path.abspath(root)), Path(os.path.abspath(output))
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    readback = {"fixture": "FX-B1", "root": str(root), "profile": PROFILE, "stream": f"fx-b1-{stamp}",
                "started_at": datetime.now(UTC).isoformat(), "root_guard": guard_root(root), "acks": [],
                "consume": {}, "queue": {}, "produced": {}}
    output.mkdir(parents=True, exist_ok=False)
    audit_log = output / "audit.log.partial"
    record = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-B1",
              "work_unit": "WO-220504", "dag_node": "B1", "issue": 124, "invocation": invocation,
              "source_revision": git("rev-parse", "HEAD"),
              "source_status": git("status", "--porcelain"),
              "admission_baseline": "01764fccf144a536023854dd533b05952131cb44",
              "predecessor": {"biu": "WO-220610", "dag_node": "B1P", "issue": 140, "fixture": "FX-B1P",
                              "accepted_candidate": "2d3d1f970e262e5f330cfb848784c74a0c991a0d",
                              "ancestor_of_candidate": subprocess.run(
                                  ["git", "merge-base", "--is-ancestor", "2d3d1f970e262e5f330cfb848784c74a0c991a0d",
                                   "HEAD"], cwd=ROOT).returncode == 0},
              "target": {"profile": PROFILE, "root": str(root), "authority": AUTHORITY, "host_actor": ACTOR,
                         "supervisor": "systemd --user (C5 SystemdHostManager)"},
              "proof_level": "OPERATIONAL_OR_EXTERNAL_AUTHORITY",
              "labels": ["BOUND_TARGET_FX_B1_TRAJECTORY_OPERATIONAL", "REAL_USER_SYSTEMD_MANAGER",
                         "B1P_COMPOSITION_UNCHANGED", "SYNTHETIC_SOURCE_DIRECT_FEED",
                         "HOST_AND_MONITOR_OBSERVER_UNITS_CONFIG_CONFINED", "AUDIT_ALLOWS_CANDIDATE_SRC_TOOLS_OUTPUT",
                         "ROOT_RETAINED_AFTER_RUN"],
              "measurements": {"tokens": None, "cost": None, "provider_calls": None,
                               "reason": "UNKNOWN: provider usage is unavailable to this local operational run"},
              "independent_verdict": "PENDING_FRESH_BIU_VERIFIER", "non_claims": list(NON_CLAIMS), "holds": []}
    if record["source_status"]:
        record["holds"].append("source is not a clean committed candidate")
    if not record["predecessor"]["ancestor_of_candidate"]:
        record["holds"].append("WO-220610 accepted candidate is not an ancestor")
    run = Run(output, audit_log)
    if readback["root_guard"]:
        record["holds"].append("root guard refused: " + ", ".join(readback["root_guard"]))
    else:
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        fx_b1_audit.install(audit_log)
        try:
            operate(root, output, invocation, run, readback)
        except Exception as error:  # the record keeps what happened; a failure is a HOLD, never a PASS
            record["holds"].append(f"operational run stopped: {type(error).__name__}: {error}")
    audit = read_audit(audit_log)
    touched = audit["paths"]
    # The bound root, and from this checkout only the candidate's own source and tools (imported by
    # every audited process) and this run's output directory.
    allowed = (str(root), str(ROOT / "src"), str(ROOT / "tools"), str(output))
    unexpected = [argv for argv in audit["executions"] if os.path.basename(argv[0] if argv else "") not in EXECUTABLES]
    readback["audit"] = {"protected": str(STATE), "allowed": list(allowed), "paths": len(touched),
                         "executions": len(audit["executions"]), "unexpected_executions": unexpected,
                         "root_touched": any(inside(p, root) for p in touched),
                         "forbidden": forbidden_touches(touched, STATE, allowed),
                         "touched_under_state_outside_root": sorted(p for p in touched if inside(p, STATE)
                                                                    and not inside(p, root))}
    readback["audit_ref"] = retain(output, {"touched": touched, "executions": audit["executions"]})
    if audit_log.exists():
        audit_log.unlink()
    readback["finished_at"] = datetime.now(UTC).isoformat()
    try:
        readback["predicates"] = predicates(readback, readback["stream"])
    except (KeyError, TypeError, IndexError) as error:
        readback["predicates"] = None
        record["holds"].append(f"readback incomplete: {type(error).__name__}: {error}")
    if readback["predicates"]:
        record["holds"] += [f"predicate {k} is HOLD" for k, v in readback["predicates"].items() if v != "PASS"]
    record |= {"commands": run.commands, "predicates": readback["predicates"], "readback_ref": retain(output, readback),
               "run_state": "COMPLETE"}
    record["result"] = "HOLD" if record["holds"] else "OPERATIONAL_READBACK_COMPLETE"
    record["exit_status"] = 1 if record["holds"] else 0
    (output / "readback.json").write_text(json.dumps(readback, indent=2, default=str) + "\n")
    (output / "execution-record.json").write_text(json.dumps(record, indent=2, default=str) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-B1", "result": record["result"], "holds": record["holds"],
                      "predicates": record["predicates"], "output": str(output)}))
    return record["exit_status"]


def readback_only(root, output):
    """Read a retained root through the same CLIs; launches, consumes and writes nothing there."""
    root, output = Path(os.path.abspath(root)), Path(os.path.abspath(output))
    output.mkdir(parents=True, exist_ok=False)
    run = Run(output, output / "audit.log")
    config = root / "fx-b1-supervision.json"
    _, journal = run.cli("journal", CAPTURE, "journal", "--config", str(config))
    _, receipts = run.cli("receipts", RECEIPTS, "receipts", "--config", str(config))
    audit = read_audit(output / "audit.log")
    forbidden = forbidden_touches(audit["paths"], STATE, (str(root), str(ROOT / "src"), str(ROOT / "tools"),
                                                           str(output)))
    reconciled = bool(receipts and receipts.get("reconciliation", {}).get("reconciled")) and not forbidden
    result = {"root": str(root), "commands": run.commands, "journal_entries": len((journal or {}).get("entries", [])),
              "reconciliation": (receipts or {}).get("reconciliation"), "audit_forbidden": forbidden,
              "result": "RETAINED_READBACK_RECONCILED" if reconciled else "HOLD"}
    (output / "retained-readback.json").write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(json.dumps({"result": result["result"], "output": str(output)}))
    return 0 if reconciled else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("run", "readback"))
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--invocation")
    arguments = parser.parse_args()
    if arguments.command == "run":
        if not arguments.invocation:
            parser.error("--invocation is required for run")
        raise SystemExit(run_operational(arguments.root, arguments.output, arguments.invocation))
    raise SystemExit(readback_only(arguments.root, arguments.output))
