#!/usr/bin/env python3
"""FX-U6 intact/fault/restored discrimination over an exact git export of the candidate revision.

One discriminating negative control per material failure class of WO-220206 (SF-REQ-051-AC-03 under the
2026-09-25 Founder coupling disposition). Where a class is enforced on two distinct surfaces (the source-level
fitness checker and design-level admission), each surface has its own control. Each control applies exactly one
named mutation to an isolated `git archive` export, runs only the named test, and restores the original bytes.
Nothing here records an independent verdict: that remains the verifier's.
"""
import argparse
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
FIXTURE, BIU = "FX-U6", "WO-220206"
INVOCATION = "AlienLogicLab/alienintent#110:PRODUCER:0dcd5fde-ad5e-4d85-b336-74e7c564bd3f"
# origin/main at claim; the RELEASED record named fc5c0a7fcbc0d70772c07cd35a4fe52a3e2641c7, its ancestor.
BASELINE = "23c408d6bea3cabea49c0f02e3157b3470f16416"
DOMAIN = "src/alienintent/context_assembly/domain/design_admission.py"
ADAPTER = "src/alienintent/composition/design_admission.py"
CHECKER = "tools/fitness/check_architecture.py"
REGISTER = "tools/fitness/coupling_register.json"
TESTS = "tests/context_assembly/test_design_admission.py"
FITNESS_TESTS = "tests/test_architecture_fitness.py"
DISPOSITION = "docs/decisions/2026-09-25-cross-module-coupling-risk-disposition.md"
DESIGN = "docs/evidence/wave2-design-contracts.json"
ADMISSION = "tests.context_assembly.test_design_admission.DesignAdmissionTests."
FITNESS = "tests.test_architecture_fitness.CouplingFitnessTests."
C1, C2, C3, C4, C5 = ("forbidden-dependency-or-interface", "introduced-cycle", "domain-import-classification",
                      "conforming-mechanical-pass-and-review", "persistence-ownership")

# (control, material class, file, old, new, test); every old string must occur exactly once.
CONTROLS = [
    ("forbidden-dependency-ignored", C1, DOMAIN,
     '        elif INNER_LAYERS & set(source[1:2]) and "adapters" in target:\n', "        elif False:\n",
     ADMISSION + "test_forbidden_dependency_fails_before_review"),
    ("incompatible-interface-ignored", C1, DOMAIN, "    if unmet:\n", "    if False:\n",
     ADMISSION + "test_incompatible_interface_fails_before_review"),
    ("design-cycle-check-bypassed", C2, DOMAIN,
     "        if inner not in coupling.cycles:  # A cycle must be declared exactly, edge for edge.\n",
     "        if False:\n", ADMISSION + "test_introduced_cross_module_cycle_fails_before_review"),
    ("source-cycle-check-bypassed", C2, CHECKER, "    for group in cycles(set(graph)):\n", "    for group in []:\n",
     FITNESS + "test_introduced_cross_module_cycle_fails"),
    ("design-domain-classification-bypassed", C3, DOMAIN,
     '            if source[0] != COMPOSITION_ROOT and target[1:2] == ("domain",):\n', "            if False:\n",
     ADMISSION + "test_cross_module_domain_import_is_classified_or_held"),
    ("source-unclassified-import-accepted", C3, CHECKER,
     "for key, sites in sorted(observed.items(), key=lambda item: item[0]) if key not in classified]",
     "for key, sites in sorted(observed.items(), key=lambda item: item[0]) if False]",
     FITNESS + "test_unclassified_domain_import_fails"),
    ("coupling-checks-not-run", C4, ADAPTER, "        for name in (*EXISTING_CHECKS, *COUPLING_CHECKS):\n",
     "        for name in EXISTING_CHECKS:\n",
     ADMISSION + "test_conforming_design_records_mechanical_pass_and_separate_attributable_review"),
    ("table-owner-unchecked", C5, CHECKER, "            elif owners[table] != relative:\n", "            elif False:\n",
     FITNESS + "test_table_mutated_outside_its_owner_fails"),
]
_OUTCOME = re.compile(r"^(FAIL|ERROR): (\w+) \(", re.MULTILINE)
BOUNDED = (
    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", TESTS, FITNESS_TESTS],
    [sys.executable, CHECKER, "--root", "src/alienintent", "--check", "all"],
)


def export(revision: str, target: Path) -> None:
    archive = subprocess.run(["git", "archive", "--format=tar", revision], cwd=ROOT, capture_output=True, check=True)
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
        tar.extractall(target, filter="data")


def execute(root: Path, command: list[str], output: Path, name: str) -> dict:
    env = dict(os.environ, PYTHONPATH=str(root / "src") + os.pathsep + str(root), PYTHONDONTWRITEBYTECODE="1")
    try:
        completed = subprocess.run(command, cwd=root, env=env, capture_output=True, timeout=600)
        status, raw = completed.returncode, completed.stdout + completed.stderr
    except subprocess.TimeoutExpired as error:
        status, raw = None, (error.stdout or b"") + (error.stderr or b"") + b"\nTIMEOUT\n"
    (output / f"{name}.log").write_bytes(raw)
    return {"command": [Path(command[0]).name if command[0] == sys.executable else command[0], *command[1:]],
            "exit_status": status, "raw_output": f"{name}.log", "raw_output_sha256": sha256(raw).hexdigest(),
            "text": raw.decode(errors="replace")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", default="HEAD")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    revision = subprocess.check_output(["git", "rev-parse", args.revision], cwd=ROOT, text=True).strip()
    outcomes, bounded = [], []
    with tempfile.TemporaryDirectory(prefix="fx-u6-") as tmp:
        root = Path(tmp)
        export(revision, root)
        files = {p: sha256((root / p).read_bytes()).hexdigest()
                 for p in (DOMAIN, ADAPTER, CHECKER, REGISTER, TESTS, FITNESS_TESTS, DISPOSITION, DESIGN,
                           "tools/evidence/fx_u6_evidence.py")}
        for index, command in enumerate(BOUNDED):
            run = execute(root, command, args.output, f"bounded-{index + 1}")
            bounded.append({k: v for k, v in run.items() if k != "text"})
            print("bounded", index + 1, run["exit_status"], flush=True)
        for control, material, path, old, new, test in CONTROLS:
            target = root / path
            original = target.read_bytes()
            count = original.decode().count(old)
            if count != 1:
                raise RuntimeError(f"{control}: expected exactly one mutation site, got {count}")
            command = [sys.executable, "-m", "unittest", test, "-v"]
            phases = {}
            for phase in ("intact", "fault", "restored"):
                if phase == "fault":
                    target.write_bytes(original.decode().replace(old, new).encode())
                mutated = sha256(target.read_bytes()).hexdigest()
                run = execute(root, command, args.output, f"{control}-{phase}")
                failed = [m.group(2) for m in _OUTCOME.finditer(run.pop("text")) if m.group(1) == "FAIL"]
                phases[phase] = {**run, "application_count": count if phase == "fault" else 0,
                                 "file_sha256": mutated, "failed_assertions": failed,
                                 "expected": "nonzero: the named assertion fails" if phase == "fault" else "exit 0"}
                if phase == "fault":
                    target.write_bytes(original)
                print(control, phase, run["exit_status"], flush=True)
            name = test.rsplit(".", 1)[1]
            discriminated = (phases["intact"]["exit_status"] == 0 and phases["restored"]["exit_status"] == 0
                             and phases["fault"]["exit_status"] not in (0, None)
                             and phases["fault"]["failed_assertions"] == [name]
                             and phases["restored"]["file_sha256"] == phases["intact"]["file_sha256"])
            outcomes.append({"control": control, "material_class": material, "file": path, "mutation": [old, new],
                             "test": test, "phases": phases, "discriminated": discriminated})
    report = {"schema_version": 1, "record_kind": "ProofFixtureReport", "fixture": FIXTURE, "biu": BIU,
              "invocation": INVOCATION, "baseline": BASELINE, "candidate_source_revision": revision,
              "authority": DISPOSITION, "files_sha256": files, "bounded_commands": bounded, "controls": outcomes,
              "negative_control_applications": sum(o["phases"]["fault"]["application_count"] for o in outcomes),
              "tokens": None, "cost": None, "measurement_reason": "UNKNOWN: invocation billing telemetry unavailable",
              "verdict": "independent verifier pending"}
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    passed = all(o["discriminated"] for o in outcomes) and all(b["exit_status"] == 0 for b in bounded)
    print("FX-U6", "DISCRIMINATED" if passed else "NOT DISCRIMINATED")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
