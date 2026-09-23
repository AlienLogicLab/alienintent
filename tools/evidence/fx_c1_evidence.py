"""FX-C1 disposable local proof. Never touches a live queue, provider or profile.

Run against committed source; output must be a new directory. Every rerun keeps
its own immutable observations. The final custody comment identifies the evidence
commit, whose source files must match the recorded source candidate digests.
"""
from dataclasses import asdict
from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
APP = Path("src/alienintent/control_plane/application/attention.py")
TEST = "tests/control_plane/test_attention.py"
CONTRACT = "docs/evidence/wave2-proof-fixtures/FX-C1.md"
CONTROLS = (
    ("origin_dedupe", "            return existing", '            return self._change(existing, "DUPLICATE", origin.producer)', "test_restart_dedupe_origin[DONE]", "origin dedupe lost history"),
    ("durable_creation", "        item = self.ensure(origin)", "        return None", "test_delivery_failure_pending_fresh_consumer", "durable attention creation must precede delivery"),
    ("consumer_bridge", 'NotificationAttempt(attempt_id, "DELIVERED", receipt=receipt)', 'NotificationAttempt(attempt_id, "DELIVERED")', "test_correlated_consumer_receipt", "consumer bridge lost durable correlated receipt"),
    ("actor", "if decision.actor not in {g.actor for g in applicable}:", "if False:", "test_resolution_authority_refusal[actor-intruder]", "DID NOT RAISE"),
    ("revision", "if decision.work_revision != item.origin.work_revision:", "if False:", "test_resolution_authority_refusal[work_revision-stale]", "DID NOT RAISE"),
    ("lane", "if decision.lane != item.origin.lane:", "if False:", "test_resolution_authority_refusal[lane-mailbox]", "DID NOT RAISE"),
    ("authority", "if decision.authority != item.origin.required_authority:", "if False:", "test_resolution_authority_refusal[authority-wrong]", "DID NOT RAISE"),
    ("seen_not_resolved", 'status="SEEN")', 'status="RESOLVED")', "test_seen_is_not_resolved_and_decision_inbox_distinct", "AssertionError"),
    ("resolution_evidence", "        self.repository.validate_resolution(item, decision)", "        pass", "test_resolution_requires_retrievable_correlated_disposition[unrelated]", "DID NOT RAISE"),
    ("unbound_activation", '            return ActivationHold("ACTIVATION_UNBOUND")', '            self.activation.launch(item)\n            return ActivationHold("ACTIVATION_UNBOUND")', "test_unbound_activation_zero_launches", "unbound activation launched a model"),
)


def digest(body):
    return "sha256:" + sha256(body).hexdigest()


def encoded(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def retain(output, record):
    body = encoded(record)
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


def execute(cwd, argv):
    environment = {**os.environ, "PYTHONPATH": str(cwd / "src") + os.pathsep + str(cwd),
                   "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        result = subprocess.run(argv, cwd=cwd, env=environment, text=True, capture_output=True, timeout=240)
        return {"argv": argv, "cwd": str(cwd), "exit_status": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired as error:
        return {"argv": argv, "cwd": str(cwd), "exit_status": None, "error": str(error),
                "stdout": str(error.stdout), "stderr": str(error.stderr)}


def readback(output, invocation):
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    from alienintent.composition.control_plane_profile import AttentionProfile
    from alienintent.control_plane.domain.attention import ResolverGrant
    from tests.control_plane.test_attention import origin, recorded_resolution
    class Channel:
        calls = 0
        def notify(self, item, attempt_id):
            self.calls += 1
            raise OSError("FX-C1 injected channel failure")
    class LaunchSpy:
        count = 0
        def launch(self, item):
            self.count += 1
            raise AssertionError("no model launch permitted")
    channel, spy = Channel(), LaunchSpy()
    configuration = {"project": "project", "name": "fixture", "invocation": invocation,
                     "clock": "2026-09-23T00:00:00Z", "attempt_id": "attempt-1",
                     "resolvers": [{"actor": "director", "authority": "authority-1", "work_ref": "issue:78", "work_revision": "rev-1", "lane": "product"}],
                     "activation_policy": "UNBOUND", "notification": "injected channel failure"}
    with tempfile.TemporaryDirectory(prefix="fx-c1-readback-") as temporary:
        root = Path(temporary)
        def profile():
            return AttentionProfile(root, project="project", name="fixture", invocation=invocation,
                clock=lambda: configuration["clock"], next_id=lambda: "attempt-1",
                resolvers=(ResolverGrant(**configuration["resolvers"][0]),), notifier=channel, activation=spy)
        first = profile().attention.handle(origin())
        fresh = profile()
        pending = fresh.attention.show(first.identity)
        assert pending == first and pending.status == "PENDING"
        assert pending.attempts[0].status == "FAILED"
        seen = fresh.attention.seen(pending.identity, "director", pending.version)
        assert seen.status == "SEEN" and fresh.attention.list_pending()
        hold = fresh.attention.request_activation(seen.identity, "director", seen.version)
        assert spy.count == 0 and hold.reason == "ACTIVATION_UNBOUND"
        decision = recorded_resolution(fresh, seen)
        resolved = fresh.attention.resolve(seen.identity, decision)
        assert profile().attention.show(seen.identity) == resolved
        assert resolved.handler == "director" and not profile().attention.list_pending()
        assert profile().attention.handle(origin()) == resolved and channel.calls == 1
        source = root / "bootstrap.jsonl"
        rows = [{"kind": "item", "id": "legacy-pending", "handled": False},
                {"kind": "item", "id": "legacy-resolved", "handled": False},
                {"kind": "ack", "id": "legacy-resolved", "by": "founder", "note": "historical disposition"}]
        source.write_text("".join(json.dumps(r) + "\n" for r in rows))
        original = source.read_bytes()
        staged = fresh.migration.stage(source, permitted_root=root, source_id="bootstrap-product")
        assert source.read_bytes() == original
        comparison = profile().migration.compare(staged.identity, source, permitted_root=root)
        rollback = profile().migration.rollback(staged.identity)
        assert comparison["source_unchanged"] and rollback["pending_origin_ids"] == ["legacy-pending"]
        body = {"origin": asdict(origin()), "pending": asdict(pending), "seen": asdict(seen),
                "resolved": asdict(resolved), "history": fresh.attention.history(seen.identity),
                "activation": asdict(hold), "model_launch_count": spy.count,
                "notification_calls": channel.calls, "migration": profile().migration.read(staged.identity),
                "comparison": comparison, "rollback": rollback,
                "operational_readback": fresh.store.list_states("fixture"),
                "immutable_history_objects": {path.name: json.loads(path.read_bytes())
                    for path in sorted(fresh.evidence.objects.iterdir()) if not path.name.startswith(".")}}
        return retain(output, body), retain(output, configuration), spy.count


def run(output, invocation):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(CONTRACT), Path("docs/evidence/wave2-proof-fixtures/FX-C1/implementation-plan.md"),
             Path("docs/evidence/wave2-execution-packets/WO-220301.packet.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220301.allocation.json"), Path(TEST),
             Path(__file__).relative_to(ROOT), Path("src/alienintent/composition/control_plane_profile.py"),
             *(p.relative_to(ROOT) for p in sorted((ROOT / "src/alienintent/control_plane").glob("**/attention*.py")))]
    paths = list(dict.fromkeys(paths))
    report = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-C1",
        "invocation": invocation, "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "admission_baseline": "3d14d3004971d447bc597075f778c4aad4b037d9",
        "input_digests": {str(p): digest((ROOT / p).read_bytes()) for p in paths},
        "commands": [], "holds": [], "independent_verdict": "PENDING_FRESH_BIU_VERIFIER",
        "proof_level": "LOCAL_COMPOSED_OR_MECHANICAL", "live_proof": "NOT_ESTABLISHED",
        "measurements": {"tokens": None, "cost": None, "provider_calls": None,
                         "reason": "UNKNOWN: provider usage is unavailable to this local fixture"}}
    if report["source_status"]:
        report["holds"].append("source is not a clean committed candidate")
    command = [sys.executable, "-B", "-m", "pytest", "-q", TEST]
    intact = execute(ROOT, command)
    report["commands"].append({"id": "intact", "command": command, "exit_status": intact["exit_status"], "observation_ref": retain(output, intact)})
    if intact["exit_status"] != 0:
        report["holds"].append("intact suite failed")
    for label, command in (
        ("python_regression", [sys.executable, "-B", "-m", "pytest", "-q"]),
        ("architecture", [sys.executable, "-B", "tools/fitness/check_architecture.py", "--root", "src/alienintent", "--check", "all"]),
        ("node_regression", ["node", "scripts/check.mjs", "all"]),
    ):
        observation = execute(ROOT, command)
        report["commands"].append({"id": label, "command": command, "exit_status": observation["exit_status"],
                                   "observation_ref": retain(output, observation)})
        if observation["exit_status"] != 0:
            report["holds"].append(label + " failed")
    mutations = []
    with tempfile.TemporaryDirectory(prefix="fx-c1-controls-") as temporary:
        copy = Path(temporary)
        for name in ("src", "tests"):
            shutil.copytree(ROOT / name, copy / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copy2(ROOT / "pyproject.toml", copy / "pyproject.toml")
        path = copy / APP
        original = path.read_text()
        for name, needle, replacement, test, assertion in CONTROLS:
            count = original.count(needle)
            if count != 1:
                raise RuntimeError(f"{name}: mutation count {count}, expected exactly one")
            command = [sys.executable, "-B", "-m", "pytest", "-q", TEST + "::" + test]
            path.write_text(original.replace(needle, replacement, 1))
            fault = execute(copy, command)
            path.write_text(original)
            restored = execute(copy, command)
            discriminates = (fault["exit_status"] == 1 and assertion in fault["stdout"]
                            and ("AssertionError" in fault["stdout"] or "Failed: DID NOT RAISE" in fault["stdout"])
                            and restored["exit_status"] == 0)
            mutations.append({"control": name, "application_count": count, "source_digest": digest(original.encode()),
                "mutation": {"remove": needle, "replace_with": replacement}, "command": command,
                "assertion": assertion, "fault_exit": fault["exit_status"], "restored_exit": restored["exit_status"],
                "fault_ref": retain(output, fault), "restored_ref": retain(output, restored), "discriminates": discriminates})
            if not discriminates:
                report["holds"].append(name + " did not discriminate")
    try:
        report["readback_ref"], report["profile_ref"], report["model_launch_count"] = readback(output, invocation)
        report["profile_digest"] = report["profile_ref"]["revision_digest"]
    except Exception as error:
        report["holds"].append("readback failed: " + repr(error))
        report["model_launch_count"] = None
    report["exit_status"] = 1 if report["holds"] else 0
    mapping = {"SF-REQ-053-AC-05": ["test_restart_dedupe_origin", "test_delivery_failure_pending_fresh_consumer",
        "test_concurrent_handling_preserves_delivery_result", "test_notification_crash_preserves_unconfirmed_attempt",
        "test_resolution_authority_refusal", "test_resolution_requires_retrievable_correlated_disposition",
        "test_seen_is_not_resolved_and_decision_inbox_distinct", "test_correlated_consumer_receipt"],
        "SF-REQ-053-AC-06": ["test_unbound_activation_zero_launches", "test_bound_activation_policy_does_not_supply_episode_executor"]}
    (output / "execution-record.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "run-report.json").write_text(json.dumps({"acceptance_to_probes": mapping,
        "focused_command": report["commands"][0], "readback_ref": report.get("readback_ref"),
        "model_launch_count": report["model_launch_count"], "migration": "staged snapshots/aliases only; source writer retained",
        "activation": "notification only; explicit policy applicability checked; authority-bearing executor remains unbound",
        "proof_level": report["proof_level"], "exit_status": report["exit_status"]}, indent=2) + "\n")
    (output / "proven-red.json").write_text(json.dumps({"controls": mutations, "holds": report["holds"]}, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-C1", "exit_status": report["exit_status"], "holds": report["holds"],
                      "controls": len(mutations), "model_launch_count": report["model_launch_count"], "output": str(output)}))
    return report["exit_status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--invocation", required=True)
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.output, arguments.invocation))
