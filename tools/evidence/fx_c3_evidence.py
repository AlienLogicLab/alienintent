"""FX-C3 disposable local proof. Never touches a live host, queue, provider, model or profile.

Run against committed source; output must be a new directory. Every rerun keeps its own
immutable observations. Each discriminating control is applied exactly once to a disposable
copy: intact exit 0, fault exit 1 at the named assertion, restored exit 0.
"""
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
DOMAIN = "src/alienintent/control_plane/domain/episode.py"
APP = "src/alienintent/control_plane/application/episode_control.py"
ADAPTER = "src/alienintent/control_plane/adapters/episode_repository.py"
PORTS = "src/alienintent/control_plane/ports/episode.py"
PROFILE = "src/alienintent/composition/control_plane_profile.py"
TEST = "tests/control_plane/test_episode_control.py"
HELPER = "tests/control_plane/episode_process.py"
CONTRACT = "docs/evidence/wave2-proof-fixtures/FX-C3.md"
ADMISSION_BASELINE = "ed0d4ffb3bfa59bf4bf9e966d6651bf4eaa2e707"
LABELS = ("LOCAL_SUBSTITUTE_USAGE_SOURCE", "LOCAL_OPERATOR_GRANT_TABLE", "INJECTED_INTEGER_MICROSECOND_CLOCKS",
          "LOCAL_JOURNAL_DELIVERY")
ARCHITECTURE = ("tools/fitness/check_architecture.py", "--root", "src/alienintent", "--check", "all")
_IDENTITY = ("        if (result.epoch, result.invocation, self.invocation) != (record.epoch, record.invocation, record.invocation):\n"
             "            return None\n"
             "        return result.epoch, result.invocation")
_UNBOUND = '        return UsageVerdict(None, "UNBOUND", None)'
_GRANT = ('    grant = authorized(grants, judgment.actor, objective, authority)\n'
          '    if grant is None:\n'
          '        return InvalidJudgment("UNAUTHORIZED")\n')
_PRIOR = ('    if observation.check_id != check_id:\n'
          '        return UsageVerdict(EndCause.CONTEXT_USAGE_UNAVAILABLE, "prior-check", None)\n')
# (control, file, needle, replacement, pytest node ids or None for the architecture check, required assertions)
# The six ★ controls discharge the 053-tenure-fence proven-red obligation.
CONTROLS = (
    ("old_epoch_accepted", APP, _IDENTITY, "        return record.epoch, record.invocation",
     ("test_competing_epochs_cannot_overwrite",), ("STALE_EPOCH",)),
    ("context_item_omitted", PROFILE, "        document = dict(result.document)\n",
     '        document = {**result.document, "current_work": list(result.document["current_work"])[1:]}\n',
     ("test_replacement_equivalence",), ("the successor reconstructs equal",)),
    ("unbound_as_zero", DOMAIN, _UNBOUND, '        return UsageVerdict(None, "MEASURED_SAFE", 0.0)',
     ("test_usage_unbound",), ("UNBOUND is recorded explicitly",)),
    ("unbound_auto_terminates", DOMAIN, _UNBOUND,
     '        return UsageVerdict(EndCause.CONTEXT_USAGE_UNAVAILABLE, "UNBOUND", None)',
     ("test_usage_unbound",), ("a missing usage binding alone does not end tenure",)),
    ("bound_unavailable_ignored", DOMAIN,
     '        return UsageVerdict(EndCause.CONTEXT_USAGE_UNAVAILABLE, "unavailable", None)',
     '        return UsageVerdict(None, "unavailable", None)',
     ("test_usage_bound_invalid[unavailable]",), ("expected ENDED CONTEXT_USAGE_UNAVAILABLE",)),
    ("unauthorized_contradiction_accepted", DOMAIN, _GRANT,
     '    grant = authorized(grants, judgment.actor, objective, authority) or OperatorGrant(judgment.actor, authority, objective)\n',
     ("test_contradiction[unauthorized]",), ("expected InvalidJudgment(UNAUTHORIZED)",)),
    ("age_boundary", DOMAIN, "    if now_us - record.began_us >= policy.max_age_s * SECOND:",
     "    if now_us - record.began_us > policy.max_age_s * SECOND:",
     ("test_age_limit[at]",), ("expected ENDED AGE_LIMIT",)),
    ("transition_boundary", DOMAIN, "    if record.transitions >= policy.max_transitions:",
     "    if record.transitions >= policy.max_transitions + 1:",
     ("test_transition_limit[32]",), ("the 32nd admission reaches the limit",)),
    ("blocked_limit_removed", DOMAIN,
     "    if record.blocked_since_us is not None and now_us - record.blocked_since_us >= policy.max_blocked_s * SECOND:",
     "    if False:", ("test_blocked_limit[at]",), ("expected ENDED BLOCKED_LIMIT",)),
    ("threshold_boundary", DOMAIN, "    if ratio >= policy.threshold:", "    if ratio > policy.threshold:",
     ("test_usage_bound_threshold[at]",), ("expected ENDED CONTEXT_USAGE_LIMIT",)),
    ("prior_check_accepted", DOMAIN, _PRIOR, "",
     ("test_usage_bound_invalid[prior_check]",), ("prior-check",)),
    ("vector_check_removed", APP, "        if stale:\n", "        if False:\n",
     ("test_obsolete_revision_refused", "test_state_vector_mismatch"), ("STALE_VECTOR",)),
    ("authority_skipped_on_current", APP,
     "        if (result.work, result.action, result.expected_version) not in offered:\n", "        if False:\n",
     ("test_current_revision_still_authority_checked[blocked_item]",),
     ("a current-revision result still requires authority",)),
    ("immediate_cause_ignored", APP, "        if identity != bound:\n",
     '        if identity != bound and kind != "provider":\n',
     ("test_immediate_end[provider]",), ("expected ENDED PROVIDER_CHANGE",)),
    ("auto_renew", APP, "        ended = replace(record, state=EpisodeState.ENDED, cause=cause, last_check_us=now)\n",
     "        ended = replace(record, epoch=record.epoch + 1, began_us=now, deadline_us=now + self.policy.max_age_s"
     " * SECOND, transitions=0, blocked_since_us=None, accepted_contradictions=0, last_check_us=now)\n",
     ("test_no_automatic_renewal",), ("ending never starts a new epoch",)),
    ("budget_reset", APP, "            admitted_total=0 if prior is None else prior.admitted_total,\n",
     "            admitted_total=0,\n",
     ("test_renewal_new_epoch_retains_budget",), ("carries budget accounting",)),
    ("clock_regression_accepted", APP, "        if record is not None and now < record.last_check_us:\n",
     "        if False:\n", ("test_restart_utc_deadline[regression]",), ("CLOCK_REGRESSION",)),
    ("adapter_import_added", APP, "from alienintent.control_plane.ports.episode import (\n",
     "from alienintent.control_plane.adapters.episode_repository import DurableEpisodeRepository\n"
     "from alienintent.control_plane.ports.episode import (\n", None, ("application imports adapters",)),
    # Producer addition beyond the drafted controls.
    ("one_biu_removed", APP, "        if result.work != record.objective:\n", "        if False:\n",
     ("test_one_bius_only",), ("ONE_BIU",)),
    # Repairs after independent pre-verify review (forged identity, authority scope, lost count, blocked observation).
    ("forged_identity_accepted", APP, "(record.epoch, record.invocation, record.invocation)",
     "(record.epoch, record.invocation, self.invocation)",
     ("test_old_epoch_process_cannot_use_current_identity", "test_competing_epochs_cannot_overwrite"),
     ("STALE_EPOCH",)),
    ("grant_authority_ignored", DOMAIN,
     "    return next((g for g in grants if (g.actor, g.objective, g.authority) == (actor, objective, authority)), None)",
     "    return next((g for g in grants if (g.actor, g.objective) == (actor, objective)), None)",
     ("test_contradiction[wrong_authority]", "test_begin_requires_matching_authority"),
     ("expected InvalidJudgment(UNAUTHORIZED)",)),
    ("claim_conflict_uncaught", APP, "        except (ReservationRejected, StoreUnavailable, VersionConflict):\n",
     "        except (ReservationRejected, StoreUnavailable):\n",
     ("test_interrupted_claim_still_counts",), ("a delivery conflict escaped after admission",)),
    ("blocked_not_observed_on_results", APP,
     "        if observed.blocked_since_us != record.blocked_since_us:\n", "        if False:\n",
     ("test_blocked_observed_on_results",), ("a result observes and persists the block",)),
)
END_CAUSES = {
    "AGE_LIMIT": ["test_age_limit[at]", "test_deadline_timer_independent_of_model", "test_restart_utc_deadline[expired]"],
    "TRANSITION_LIMIT": ["test_transition_limit[32]", "test_transition_limit[33]"],
    "BLOCKED_LIMIT": ["test_blocked_limit[at]", "test_blocked_observed_on_results"],
    "CONTRADICTION": ["test_contradiction[accepted]"],
    "STALE_VECTOR": ["test_state_vector_mismatch", "test_obsolete_revision_refused"],
    "CONTEXT_USAGE_LIMIT": ["test_usage_bound_threshold[at]"],
    "CONTEXT_USAGE_UNAVAILABLE": ["test_usage_bound_invalid[unavailable]", "test_usage_bound_invalid[prior_check]"],
    "CONTEXT_USAGE_INVALID": ["test_usage_bound_invalid[wrong_invocation]", "test_usage_bound_invalid[nan_used]",
                              "test_usage_bound_invalid[negative_used]", "test_usage_bound_invalid[zero_limit]",
                              "test_usage_bound_invalid[inf_limit]"],
    "CONTEXT_EXHAUSTED": ["test_immediate_end[context_exhausted]"],
    "TERMINAL_OUTCOME": ["test_immediate_end[terminal]"],
    "OBJECTIVE_CHANGE": ["test_immediate_end[objective]"],
    "AUTHORITY_CHANGE": ["test_immediate_end[authority]"],
    "PROVIDER_CHANGE": ["test_immediate_end[provider]"],
    "MODEL_CHANGE": ["test_immediate_end[model]"],
    "EXPLICIT_REQUEST": ["test_immediate_end[explicit]"],
}


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
        result = subprocess.run(argv, cwd=cwd, env=environment, text=True, capture_output=True, timeout=900)
        return {"argv": argv, "cwd": str(cwd), "exit_status": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired as error:
        return {"argv": argv, "cwd": str(cwd), "exit_status": None, "error": str(error),
                "stdout": str(error.stdout), "stderr": str(error.stderr)}


def failed_nodes(observation):
    return sorted(line.split(" - ")[0].removeprefix("FAILED ").strip()
                  for line in observation["stdout"].splitlines() if line.startswith("FAILED "))


def control_command(tests):
    if tests is None:
        return [sys.executable, "-B", *ARCHITECTURE]
    return [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *(TEST + "::" + t for t in tests)]


def discriminates(tests, assertions, fault, restored):
    if restored["exit_status"] != 0 or fault["exit_status"] != 1:
        return False
    if not all(a in fault["stdout"] for a in assertions):
        return False
    return tests is None or "AssertionError" in fault["stdout"] or "Failed: DID NOT RAISE" in fault["stdout"]


def baseline_regression(output, baseline):
    """Run the same full suite at the pinned code baseline, in its own detached worktree."""
    with tempfile.TemporaryDirectory(prefix="fx-c3-baseline-") as temporary:
        tree = Path(temporary) / "tree"
        subprocess.run(["git", "worktree", "add", "--detach", str(tree), baseline], cwd=ROOT, check=True,
                       capture_output=True)
        try:
            observation = execute(tree, [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider"])
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(tree)], cwd=ROOT, capture_output=True)
    return observation, retain(output, observation)


def readback(output, invocation):
    """Composed disposable run; every value is read back from the durable store and S1 history."""
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    from alienintent.control_plane.domain.episode import TenurePolicy
    from tests.context_assembly.test_context_reconstruction import seed
    from tests.control_plane.test_episode_control import (
        OBJECTIVE, SECOND, T0, Clocks, LaunchSpy, Timer, admit, episode_profile, start,
    )
    clocks, timer, spy = Clocks(), Timer(), LaunchSpy()
    policy = TenurePolicy()
    configuration = {"project": "project", "name": "fixture", "invocation": invocation, "objective": OBJECTIVE,
                     "policy": {**policy.document(), "policy_digest": policy.digest()},
                     "clocks": "injected UTC anchor + monotonic, integer microseconds", "t0": T0,
                     "usage_binding": "UNBOUND (no usage source injected)", "labels": list(LABELS)}
    with tempfile.TemporaryDirectory(prefix="fx-c3-readback-") as temporary:
        root = Path(temporary) / "profile"
        root.mkdir()
        seed(root)
        profile = episode_profile(root, clocks, invocation=invocation, timer=timer)
        first = start(profile)
        admit(profile, 3)
        clocks.mono = 3600 * SECOND
        aged = profile.episodes.tick(OBJECTIVE)
        renewed = start(profile)
        admit(profile, 1, start_index=3)
        ended = profile.episodes.end(OBJECTIVE, epoch=renewed.epoch, actor="director")
        reopened = episode_profile(root, Clocks(T0 + 3601 * SECOND), invocation=invocation + "-reader")
        version, pointer = reopened.store.read_state("fixture", "episode:" + OBJECTIVE)
        body = {"steps": {"begin_epoch_1": first.document(), "age_end": aged.document(),
                          "begin_epoch_2": renewed.document(), "explicit_end": ended.document()},
                "episode_pointer": {"version": version, "state": pointer},
                "episode_history": reopened.repository.history(OBJECTIVE),
                "reopened_equals_writer": reopened.repository.load(OBJECTIVE) == (version, ended),
                "timer_armed": timer.armed, "model_launch_count": spy.count,
                "unresolved_effects": [e.identity for e in reopened.store.unresolved_effects("fixture")]}
        assert body["reopened_equals_writer"] and (str(aged.cause), str(ended.cause)) == ("AGE_LIMIT", "EXPLICIT_REQUEST")
        assert (renewed.epoch, renewed.admitted_total) == (2, 3) and spy.count == 0
        return retain(output, body), retain(output, configuration), spy.count, configuration["policy"]


def run(output, invocation, baseline):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(CONTRACT), Path("docs/work-units/wave2/WO-220303.md"),
             Path("docs/evidence/wave2-design-contracts.json"), Path("docs/evidence/wave2-dependency-dag.json"),
             Path("docs/evidence/wave2-candidate-bius.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220303.packet.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220303.allocation.json"),
             Path("docs/evidence/wave2-proof-fixtures/FX-C2/execution-record.json"),
             Path(TEST), Path(HELPER), Path(__file__).relative_to(ROOT), *map(Path, (DOMAIN, APP, ADAPTER, PORTS, PROFILE))]
    report = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-C3",
        "invocation": invocation, "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "admission_baseline": ADMISSION_BASELINE, "code_baseline": baseline,
        "input_digests": {str(p): digest((ROOT / p).read_bytes()) for p in paths},
        "labels": list(LABELS), "commands": [], "holds": [], "residuals": [],
        "independent_verdict": "PENDING_FRESH_BIU_VERIFIER",
        "proof_level": "LOCAL_COMPOSED_OR_MECHANICAL", "live_proof": "NOT_ESTABLISHED",
        "measurements": {"tokens": None, "cost": None, "provider_calls": None,
                         "reason": "UNKNOWN: provider usage is unavailable to this local fixture"}}
    if report["source_status"]:
        report["holds"].append("source is not a clean committed candidate")
    regression = None
    for label, command in (
        ("focused", [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", TEST]),
        ("python_regression", [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider"]),
        ("architecture", [sys.executable, "-B", *ARCHITECTURE]),
        ("architecture_fitness_tests", [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_architecture_fitness.py"]),
        ("node_regression", ["node", "scripts/check.mjs", "all"]),
    ):
        observation = execute(ROOT, command)
        entry = {"id": label, "command": command, "exit_status": observation["exit_status"],
                 "observation_ref": retain(output, observation)}
        report["commands"].append(entry)
        if label == "python_regression":
            regression = (entry, observation)
        elif observation["exit_status"] != 0:
            report["holds"].append(label + " failed")
    entry, observation = regression
    if observation["exit_status"] != 0:
        # A failure is admissible only if the identical node already fails at the code baseline.
        base, base_ref = baseline_regression(output, baseline)
        candidate_failed, baseline_failed = failed_nodes(observation), failed_nodes(base)
        new = sorted(set(candidate_failed) - set(baseline_failed))
        entry["baseline_comparison"] = {"baseline": baseline, "baseline_exit_status": base["exit_status"],
            "baseline_observation_ref": base_ref, "candidate_failed": candidate_failed,
            "baseline_failed": baseline_failed, "new_failures": new}
        if new or not candidate_failed:
            report["holds"].append("python_regression failed beyond the baseline")
        else:
            report["residuals"].append(f"PREEXISTING_BASELINE_FAILURES: {len(baseline_failed)} nodes fail identically at "
                                       f"code baseline {baseline}; outside the C3 extent, returned to their owners")
    mutations = []
    with tempfile.TemporaryDirectory(prefix="fx-c3-controls-") as temporary:
        copy = Path(temporary)
        for name in ("src", "tests", "tools"):
            shutil.copytree(ROOT / name, copy / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copy2(ROOT / "pyproject.toml", copy / "pyproject.toml")
        for name, relative, needle, replacement, tests, assertions in CONTROLS:
            path = copy / relative
            original = path.read_text()
            count = original.count(needle)
            if count != 1:
                raise RuntimeError(f"{name}: mutation count {count}, expected exactly one")
            command = control_command(tests)
            intact = execute(copy, command)
            path.write_text(original.replace(needle, replacement, 1))
            fault = execute(copy, command)
            path.write_text(original)
            restored = execute(copy, command)
            ok = intact["exit_status"] == 0 and discriminates(tests, assertions, fault, restored)
            mutations.append({"control": name, "file": relative, "application_count": count,
                "source_digest": digest(original.encode()), "mutation": {"remove": needle, "replace_with": replacement},
                "command": command, "assertions": list(assertions), "intact_exit": intact["exit_status"],
                "fault_exit": fault["exit_status"], "restored_exit": restored["exit_status"],
                "intact_ref": retain(output, intact), "fault_ref": retain(output, fault),
                "restored_ref": retain(output, restored), "discriminates": ok})
            if not ok:
                report["holds"].append(name + " did not discriminate")
    try:
        report["readback_ref"], report["profile_ref"], report["model_launch_count"], report["policy"] = readback(output, invocation)
        report["profile_digest"] = report["profile_ref"]["revision_digest"]
    except Exception as error:
        report["holds"].append("readback failed: " + repr(error))
        report["model_launch_count"], report["policy"] = None, None
    report["usage_binding"] = "UNBOUND (default composition); BOUND exercised only with the labelled scripted source"
    report["exit_status"] = 1 if report["holds"] else 0
    mapping = {
        "SF-REQ-053-AC-02": ["test_age_limit", "test_transition_limit", "test_blocked_limit", "test_immediate_end",
                             "test_contradiction", "test_usage_unbound", "test_usage_bound_threshold",
                             "test_usage_bound_invalid", "test_deadline_timer_independent_of_model",
                             "test_restart_utc_deadline", "test_no_automatic_renewal",
                             "test_renewal_new_epoch_retains_budget", "test_one_bius_only",
                             "test_begin_requires_matching_authority", "test_blocked_observed_on_results"],
        "SF-REQ-053-AC-03": ["test_competing_epochs_cannot_overwrite", "test_old_epoch_process_cannot_use_current_identity", "test_obsolete_revision_refused",
                             "test_state_vector_mismatch", "test_current_revision_still_authority_checked"],
        "053-tenure-fence": ["test_replacement_equivalence", "test_expiry_does_not_cancel_admitted",
                             "test_interrupted_claim_still_counts",
                             "test_episode_profile_composed", *[c[0] for c in CONTROLS]],
    }
    (output / "execution-record.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "run-report.json").write_text(json.dumps({"acceptance_to_probes": mapping, "end_cause_table": END_CAUSES,
        "focused_command": report["commands"][0], "readback_ref": report.get("readback_ref"),
        "model_launch_count": report["model_launch_count"],
        "labels": {"LOCAL_SUBSTITUTE_USAGE_SOURCE": "BOUND usage comes from a scripted same-invocation source (U-8); does not close LRN-023",
                   "LOCAL_OPERATOR_GRANT_TABLE": "contradiction/begin/end authority is an injected OperatorGrant table (U-7, ResolverGrant precedent)",
                   "INJECTED_INTEGER_MICROSECOND_CLOCKS": "UTC anchor read once per process plus injected monotonic progress; integer microseconds",
                   "LOCAL_JOURNAL_DELIVERY": "an admitted effect is delivered to the S2 local durable journal, not a remote consumer"},
        "boundaries": "no bootstrap handoff (POSTW1-DECIDE-006A), host activation, monitor work, SF-REQ-008/029 amendments or C1/C2/S2/U5 change; contradiction truth stays operator judgment",
        "proof_level": report["proof_level"], "live_proof": report["live_proof"], "exit_status": report["exit_status"]}, indent=2) + "\n")
    (output / "proven-red.json").write_text(json.dumps({"controls": mutations, "holds": report["holds"]}, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-C3", "exit_status": report["exit_status"], "holds": report["holds"],
                      "residuals": report["residuals"], "controls": len(mutations),
                      "model_launch_count": report["model_launch_count"], "output": str(output)}))
    return report["exit_status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--invocation", required=True)
    parser.add_argument("--baseline", required=True, help="code baseline commit for regression comparison")
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.output, arguments.invocation, arguments.baseline))
