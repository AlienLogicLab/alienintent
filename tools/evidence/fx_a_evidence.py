"""FX-A disposable local proof (WO-220211). Never touches a live host, queue, provider, Project or profile.

Run against committed source; output must be a new directory. Every rerun keeps its own
immutable observations. The final custody comment identifies the evidence commit, whose
source files must match the recorded source candidate digests. The execution record is rewritten
after every stage, so a run stopped at any point leaves a durable INCOMPLETE record (a HOLD, never a PASS).
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fx_c_evidence import (  # noqa: E402  The FX-C harness primitives, reused unchanged.
    checkpoint, digest, discriminates, execute, failed_ids, git, pytest, retain)

ROOT = Path(__file__).resolve().parents[2]
INTEGRATION = "src/alienintent/composition/upstream_integration.py"
TEST = "tests/composition/test_upstream_integration_capstone.py"
BOUNDED = ("tests/context_assembly/test_design_admission.py", "tests/context_assembly/test_compilation_validation.py",
           "tests/context_assembly/test_readiness_consumer.py")
PREDECESSOR_SUITES = ("tests/context_assembly", "tests/evidence_learning/test_premise_evidence.py")
CONTRACT = "docs/evidence/wave2-proof-fixtures/FX-A/FX-A.md"
ADMISSION_BASELINE = "c5ef2bc033e712b61da045df47f25b01b40f4dcc"
ARCHITECTURE = ("tools/fitness/check_architecture.py", "--root", "src/alienintent", "--check", "all")
# Wave 2A providers composed unchanged: (BIU, issue, stage, accepted candidate, landing merge).
PREDECESSORS = (
    ("WO-220201", 76, "U1 inventory", "43ea5e2b745be02df6aebaf5ba1e328f4c75fa5e", "fcb65fffda65fc2a01516aed38d8d5a662cbaba8"),
    ("WO-220202", 80, "U2 ambiguity", "d0eacfb6dd8626b07ff1d99e9c633294f13d9de4", "70fa7148939dfcebbcef73d858f9f481869d7214"),
    ("WO-220203", 81, "U3 premise", "3e8dc7032dc7e61aac48b66ea9d08a3e789757ad", "474343a4142316941340762a243e965ef44bb15c"),
    ("WO-220204", 94, "U4 proof plans", "c8ed707efdb0cd70294bfdb6814ec9f9eb71216d", "44fd55cb0b54da0a43e77e4e3218dbb0653433ff"),
    ("WO-220205", 97, "U5 design admission", "6518d1ef09fc99e8abccf1c6234106f860fce7e6", "036c5fc2d2c7f1699b23ac171e9e019aa8d4fc98"),
    ("WO-220206", 110, "U6 coupling checks", "99e238b677da46c7b9d9ad65dd1b9477c28cf9ff", "f03b0cbab2835e01ea2c0d8c0379b1b1cc5f1e62"),
    ("WO-220207", 101, "U7 compilation validation", "9d97365f58d41147923d3070ac2f838937ed0f4f", "0588eae74bbbdddfd8650e349fff472f0db20eff"),
    ("WO-220208", 117, "U8 initial compilation", "e5a61dcd5746dcc158cf4fe823e4ab4d82d4ed5e", "610703bb6cf79d1fdf403bd6d7cfd2580c6a3bf9"),
    ("WO-220209", 105, "U9 readiness consumer", "6eecc30c002785f0cc82f0645fbef601c1503e84", "7595c9c9e953795a4bb148a5c56d7e6ea512414d"),
)
# One discriminating control per material failure class, applied once each in a disposable copy.
# (control, failure class, file, needle, replacement, pytest node ids, required assertions)
CONTROLS = (
    # Design admission stops holding an infeasible premise, so review verifies it and compilation proceeds.
    ("premise_gate_removed",
     "inventory, ambiguity and premise evidence must pass before design applicability and initial compilation",
     "src/alienintent/context_assembly/domain/design_admission.py",
     "    if infeasible:\n", "    if False and infeasible:\n",
     ("test_failed_upstream_evidence_stops_before_design_and_compilation[premise]",),
     ("failed upstream evidence must not compile",)),
    # The integration asks the design gate with the design's pinned requirement revisions, not the current eligible
    # inventory/inspection revisions.
    ("stale_source_revision_reused",
     "a source, decision or design revision mismatch invalidates downstream applicability/readiness",
     INTEGRATION, '"requirements": {r: revisions.get(r) for r in sorted(design.requirements)}',
     '"requirements": dict(sorted(design.requirements.items()))',
     ("test_revision_mismatch_invalidates_downstream_readiness[source]",),
     ("a stale READY must never be reused after a revision",)),
    # Lint stops consuming design applicability, so a candidate with a stale design vector reaches assessment.
    ("lint_design_duty_removed",
     "compilation and retained assessment consumption stay separate typed boundaries and cannot bypass design "
     "applicability or lint/provenance",
     "src/alienintent/context_assembly/domain/readiness.py",
     "    if not isinstance(design_applicability, CurrentVerified):\n", "    if False:\n",
     ("test_compilation_and_assessment_stay_separate_boundaries",),
     ("readiness must not bypass design applicability",)),
    # Initial compilation keeps its identity reservations in the lifecycle namespace instead of upstream:.
    ("reservations_in_lifecycle_namespace",
     "integration produces no lifecycle/Project mutation and cannot assert release",
     "src/alienintent/context_assembly/application/initial_compilation_service.py",
     'RESERVATIONS = "upstream:identity-reservations"', 'RESERVATIONS = "factory:identity-reservations"',
     ("test_integration_mutates_no_lifecycle_or_project_state",),
     ("the integration must not write lifecycle, release or Project state",)),
)


def predecessor_custody():
    """Each predecessor candidate and its landing merge must be ancestors of this candidate."""
    records = []
    for biu, issue, stage, candidate, merge in PREDECESSORS:
        ancestry = {ref: subprocess.run(["git", "merge-base", "--is-ancestor", ref, "HEAD"], cwd=ROOT).returncode == 0
                    for ref in (candidate, merge)}
        records.append({"biu": biu, "issue": issue, "stage": stage, "accepted_candidate": candidate,
                        "landing_merge": merge, "ancestor_of_candidate": ancestry})
    return records


def baseline_regression(output):
    """The full Python suite at the admission baseline, in a disposable detached worktree."""
    with tempfile.TemporaryDirectory(prefix="fx-a-baseline-") as temporary:
        tree = Path(temporary) / "baseline"
        subprocess.run(["git", "worktree", "add", "--detach", str(tree), ADMISSION_BASELINE], cwd=ROOT,
                       check=True, capture_output=True)
        try:
            observation = execute(tree, pytest())
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(tree)], cwd=ROOT, capture_output=True)
            subprocess.run(["git", "worktree", "prune"], cwd=ROOT, capture_output=True)
    return observation, retain(output, observation)


def readback(output):
    """One composed disposable chain and one revision per kind; every value is read back from durable state."""
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    from copy import deepcopy
    from dataclasses import asdict
    from tests.composition import test_upstream_integration_capstone as fx
    with tempfile.TemporaryDirectory(prefix="fx-a-readback-") as temporary:
        body = {}
        for index, (kind, (change, _, _)) in enumerate(fx.REVISIONS.items()):
            h = fx.Harness(Path(temporary) / f"h{index}")
            compiled, candidate, plan, outcome = fx.ready(h)
            before = h.outside()
            change(h)
            current = h.integration.current(candidate, plan)
            recompiled = h.integration.compile(fx.DKEY, deepcopy(fx.LIMITS))
            body[kind] = {
                "compiled": {"candidate_digest": compiled.candidate_digest, "input_digest": compiled.input_digest,
                             "inputs": compiled.document()["inputs"],
                             "completed": h.profile.initial_compilation.completed(compiled.input_digest)},
                "eligibility": asdict(outcome), "after_revision": {"type": type(current).__name__, **asdict(current)},
                "recompiled": recompiled.document() if hasattr(recompiled, "document") else repr(recompiled),
                "retained_attempts": [{"attempt_id": e["attempt_id"], "disposition": (e["outcome"] or {}).get(
                    "disposition")} for e in h.profile.readiness_consumer.history(fx.U1)],
                "producer_launches": len(h.producer.calls),
                "design_state": h.profile.design.read(fx.DKEY)[1]["status"],
                "outside_unchanged": h.outside() == before,
                "outside_aggregates": [a for a, _, _ in h.store.list_states(fx.PROFILE)
                                       if not a.startswith(fx.UPSTREAM_NAMESPACES)]}
            assert body[kind]["outside_unchanged"] and body[kind]["producer_launches"] == 1
            assert body[kind]["after_revision"]["type"] in ("LintHold", "Hold")
            assert body[kind]["retained_attempts"][0]["disposition"] == "READY"
        return retain(output, body), body


def run(output, invocation):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(CONTRACT), Path("docs/work-units/wave2/WO-220211.md"),
             Path("docs/evidence/wave2-readiness-assessments/WO-220211.2026-09-26T101031.613435Z.assessment.json"),
             Path("docs/evidence/wave2-design-contracts.json"), Path("docs/evidence/wave2-dependency-dag.json"),
             Path("docs/evidence/wave2-candidate-bius.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220211.packet.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220211.allocation.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220211.proof-packet.md"),
             *(Path(f"docs/evidence/wo-2202{n:02d}-fx-u{n}.md") for n in range(1, 7)),
             *(Path(f"docs/evidence/wave2-proof-fixtures/FX-U{n}.md") for n in (7, 8, 9)),
             Path(TEST), Path(__file__).relative_to(ROOT), Path("tools/evidence/fx_c_evidence.py"),
             *dict.fromkeys(Path(c[2]) for c in CONTROLS)]
    report = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-A",
        "work_unit": "WO-220211", "issue": 119, "invocation": invocation,
        "source_revision": git("rev-parse", "HEAD"),
        "source_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "admission_baseline": ADMISSION_BASELINE, "predecessors": predecessor_custody(),
        "input_digests": {str(p): digest((ROOT / p).read_bytes()) for p in paths if (ROOT / p).exists()},
        "missing_inputs": [str(p) for p in paths if not (ROOT / p).exists()],
        "commands": [], "holds": [], "baseline_conditions": [], "independent_verdict": "PENDING_FRESH_BIU_VERIFIER",
        "proof_level": "LOCAL_COMPOSED_OR_MECHANICAL", "live_proof": "NOT_ESTABLISHED",
        "agent_ready_invocations": 0, "producer": "FIXTURE_PRODUCER_NOT_NATIVE",
        "measurements": {"tokens": None, "cost": None, "provider_calls": None,
                         "reason": "UNKNOWN: provider usage is unavailable to this local fixture"}}
    if report["source_status"]:
        report["holds"].append("source is not a clean committed candidate")
    if report["missing_inputs"]:
        report["holds"].append("pinned inputs missing")
    if not all(all(p["ancestor_of_candidate"].values()) for p in report["predecessors"]):
        report["holds"].append("a predecessor candidate is not an ancestor of this candidate")
    mutations = []
    for label, command in (
        ("focused", pytest(TEST)),
        ("bounded_initial", pytest(*BOUNDED)),
        ("predecessor_suites", pytest(*PREDECESSOR_SUITES)),
        ("architecture", [sys.executable, "-B", *ARCHITECTURE]),
        ("architecture_fitness_tests", pytest("tests/test_architecture_fitness.py")),
        ("feature_regression_registry", pytest("tools/verification/test_feature_regressions.py")),
        ("python_regression", pytest()),
        ("node_regression", ["node", "scripts/check.mjs", "all"]),
    ):
        if label == "python_regression":
            # The slow baseline suite runs after the focused proof, so a stopped run has already kept it.
            checkpoint(output, report, mutations, "baseline_regression")
            try:
                baseline, baseline_ref = baseline_regression(output)
                baseline_failures = failed_ids(baseline["stdout"])
            except (subprocess.CalledProcessError, OSError) as error:
                report["holds"].append("baseline regression unavailable: " + repr(error))
                baseline_ref, baseline_failures = None, None
        checkpoint(output, report, mutations, label)
        observation = execute(ROOT, command)
        entry = {"id": label, "command": command, "exit_status": observation["exit_status"],
                 "observation_ref": retain(output, observation)}
        if label == "python_regression" and observation["exit_status"] != 0:
            failures = failed_ids(observation["stdout"])
            entry["failed"] = failures
            if failures and failures == baseline_failures:
                report["baseline_conditions"].append({
                    "condition": "PRE_EXISTING_BASELINE_FAILURE", "count": len(failures),
                    "baseline": ADMISSION_BASELINE, "baseline_ref": baseline_ref,
                    "note": "identical failing node ids at the admission baseline; no FX-A file is involved"})
            else:
                report["holds"].append(label + " failed beyond the recorded baseline condition")
        elif observation["exit_status"] != 0:
            report["holds"].append(label + " failed")
        report["commands"].append(entry)
    with tempfile.TemporaryDirectory(prefix="fx-a-controls-") as temporary:
        copy = Path(temporary)
        for name in ("src", "tests", "tools", "docs"):
            shutil.copytree(ROOT / name, copy / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copy2(ROOT / "pyproject.toml", copy / "pyproject.toml")
        for name, failure_class, relative, needle, replacement, tests, assertions in CONTROLS:
            checkpoint(output, report, mutations, "control:" + name)
            path = copy / relative
            original = path.read_text()
            count = original.count(needle)
            if count != 1:
                report["holds"].append(f"{name}: mutation count {count}, expected exactly one")
                mutations.append({"control": name, "file": relative, "application_count": count, "discriminates": False})
                continue
            command = pytest(*(TEST + "::" + t for t in tests))
            intact = execute(copy, command)
            path.write_text(original.replace(needle, replacement, 1))
            fault = execute(copy, command)
            path.write_text(original)
            restored = execute(copy, command)
            ok = discriminates(assertions, intact, fault, restored)
            mutations.append({"control": name, "failure_class": failure_class, "file": relative,
                "application_count": count, "source_digest": digest(original.encode()),
                "mutation": {"remove": needle, "replace_with": replacement}, "command": command,
                "assertions": list(assertions), "intact_exit": intact["exit_status"],
                "fault_exit": fault["exit_status"], "restored_exit": restored["exit_status"],
                "intact_ref": retain(output, intact), "fault_ref": retain(output, fault),
                "restored_ref": retain(output, restored), "discriminates": ok})
            if not ok:
                report["holds"].append(name + " did not discriminate")
    checkpoint(output, report, mutations, "readback")
    try:
        report["readback_ref"], observed = readback(output)
    except Exception as error:
        report["holds"].append("readback failed: " + repr(error))
        observed = None
    report["run_state"] = "COMPLETE"
    report["exit_status"] = 1 if report["holds"] else 0
    mapping = {
        "FX-A: inventory -> ambiguity -> premise/proof -> design applicability -> initial compilation -> lint and "
        "retained assessment consumption, in order": ["test_chain_runs_in_order_to_eligibility"],
        "class 1: inventory, ambiguity and premise evidence gate design applicability and compilation":
            ["test_failed_upstream_evidence_stops_before_design_and_compilation"],
        "class 2: a source, decision or design revision invalidates downstream applicability/readiness":
            ["test_revision_mismatch_invalidates_downstream_readiness",
             "test_unavailable_governing_decision_holds_before_assessment"],
        "class 3: compilation and retained assessment consumption stay separate typed boundaries":
            ["test_compilation_and_assessment_stay_separate_boundaries", "test_unbound_producer_holds_before_launch"],
        "class 4: no lifecycle/Project mutation; no output asserts release":
            ["test_integration_mutates_no_lifecycle_or_project_state",
             "test_revision_mismatch_invalidates_downstream_readiness"],
        "composition boundary: every stage must be composed": ["test_composition_requires_every_stage"],
        "negative controls (one per material failure class)": ["proven-red.json: " + ", ".join(c[0] for c in CONTROLS)],
    }
    (output / "execution-record.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "run-report.json").write_text(json.dumps({"acceptance_to_probes": mapping,
        "focused_command": report["commands"][0], "readback_ref": report.get("readback_ref"),
        "composed_readback": observed,
        "boundaries": "local/composed fixture only; fixture producer bound to a disposable package, never native "
                      "Agent Ready; no release, lifecycle transition, Project write, split apply or live operation",
        "proof_level": report["proof_level"], "live_proof": report["live_proof"], "exit_status": report["exit_status"]},
        indent=2, default=str) + "\n")
    (output / "proven-red.json").write_text(json.dumps({"controls": mutations, "holds": report["holds"]}, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-A", "exit_status": report["exit_status"], "holds": report["holds"],
                      "baseline_conditions": len(report["baseline_conditions"]), "controls": len(mutations),
                      "output": str(output)}))
    return report["exit_status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--invocation", required=True)
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.output, arguments.invocation))
