#!/usr/bin/env python3
"""FX-U4 intact/fault/restored discrimination on isolated source copies, judged by the node's own battery.

The FX-U4 plan is derived first through the composed UpstreamProfile; every control run is then
recorded through ProofPlanning.record, so the plan is the root of the evidence ancestry.
"""
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from alienintent.composition.premise_evidence import RetainedDoctorPremiseEvidence
from alienintent.composition.proof_mapping import (
    RetainedPredicateMapping, retained_design_ref, retained_requirement_revision)
from alienintent.composition.upstream_profile import UpstreamProfile
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.domain.battery import ControlRun, evaluate_control
from alienintent.evidence_learning.domain.proof_plan import ProofPlan
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore

ROOT = Path(__file__).resolve().parents[2]
INVOCATION = "AlienLogicLab/alienintent#94:PRODUCER:9f88f9ad-382c-4788-a255-ab3ac5092842"
BASELINE = "4b94f2d1d7d40c1889af79596e8f92c737e55d7e"
PROJECT, PROFILE, REQUIREMENT = "AlienLogicLab/alienintent", "fx-u4", "SF-REQ-014"
CONTRACT = "docs/evidence/wo-220204-fx-u4.md"
MAPPING, MAPPING_SHA256 = ("docs/evidence/wo-220204-fx-u4-predicate-mapping.json",
                           "aed79fa4dcb1bed44b493b015b0a3e14e1d042fcc24d3dab3c76856874aae00c")
PREMISE_MAPPING, PREMISE_SHA256 = ("docs/evidence/wo-220203-fx-u3-premise-mapping.json",
                                   "598abb9c11791428069e2b5605b51f7ebf61afd537f2ca02c39e6bc8ec1bd589")
RETAINED = ("docs/evidence/py09b-live-checks-2026-09-21.json", "docs/evidence/py10/proof-run.json")
SPECIFICATION, DESIGN = "docs/evidence/wave2-specified-requirements.json", "docs/evidence/wave2-design-contracts.json"
DOMAIN = "src/alienintent/evidence_learning/domain/proof_plan.py"
BATTERY = "src/alienintent/evidence_learning/domain/battery.py"
ORDER = "src/alienintent/evidence_learning/domain/proof_order.py"
REPAIR = "src/alienintent/evidence_learning/domain/repair.py"
SERVICE = "src/alienintent/evidence_learning/application/proof_planning_service.py"
PORT = "src/alienintent/evidence_learning/ports/proof_planning.py"
ADAPTER = "src/alienintent/composition/proof_mapping.py"
PROFILE_MODULE = "src/alienintent/composition/upstream_profile.py"
TESTS = "tests/evidence_learning/test_proof_planning.py"
MODULE = "tests.evidence_learning.test_proof_planning."
COMPOSED, UNIT = "ProofPlanningTests", "ProofPlanDomainTests"
AC = {n: f"{REQUIREMENT}/SF-REQ-014-AC-0{n}/" for n in range(1, 5)}
AC1, AC2, AC3 = AC[1] + "pinned-before-implementation", AC[2] + "qualified-control", AC[3] + "four-part-isolation"
AC4 = AC[4] + "judgment-attribution-and-coverage"
SERVICE_MODULE = "src/alienintent/evidence_learning/application/proof_planning_service.py"
PASSED_REPLAY = "elif replay.get(old.obligation_id) is not ReplayStatus.PASSED:"
# (control, enforcement, obligation, file, old, new, test class, test)
CONTROLS = [
    ("incomplete-obligation-accepted", "AC-01", AC1, DOMAIN, "    if incomplete:\n", "    if False:\n",
     COMPOSED, "test_incomplete_mechanical_obligation_holds"),
    ("revision-link-removed", "AC-01", AC1, DOMAIN,
     "if mapping.requirement_id != rid or mapping.requirement_revision != requirement.ref.revision_digest:",
     "if mapping.requirement_id != rid:", COMPOSED, "test_mapping_for_another_requirement_revision_holds"),
    ("circular-oracle-accepted", "AC-02", AC2, DOMAIN,
     "if not p.derived_from or any(_implementation_derived(s, implementation_roots) for s in p.derived_from)]",
     "if not p.derived_from]", COMPOSED, "test_implementation_derived_predicate_is_refused"),
    ("unconditional-success-qualified", "014-discrimination", AC2, BATTERY, "    if fault.exit_status == 0:\n",
     "    if False:\n", UNIT, "test_battery_refuses_unconditional_success"),
    ("zero-application-qualified", "014-discrimination", AC2, BATTERY, "    if fault.application_count == 0:\n",
     "    if False:\n", UNIT, "test_battery_refuses_zero_application"),
    ("overdetermined-qualified", "014-discrimination", AC2, BATTERY,
     "if fault.application_count != 1 or set(fault.failed_assertions) != {target_assertion}:", "if False:",
     UNIT, "test_battery_refuses_overdetermined_kill"),
    ("unrelated-failure-qualified", "014-discrimination", AC2, BATTERY,
     "if fault.exit_status is None or fault.errors or target_assertion not in fault.failed_assertions:", "if False:",
     UNIT, "test_battery_refuses_unrelated_failure"),
    ("premise-check-removed", "AC-03", AC3, DOMAIN,
     "        if predicate.kind is PredicateKind.PLATFORM_ISOLATION:\n            if premise_reader is None:",
     "        if False:\n            if premise_reader is None:", COMPOSED, "test_credential_denial_obligation_is_infeasible_proof"),
    ("judgment-attribution-removed", "AC-04", AC4, DOMAIN, "if _missing(predicate, _JUDGMENT_FIELDS):", "if False:",
     COMPOSED, "test_unattributed_judgment_holds"),
    ("judgment-mechanical-pass-accepted", "AC-04", AC4, DOMAIN,
     "if predicate.command.strip() or predicate.expected.strip():", "if False:",
     COMPOSED, "test_judgment_claiming_mechanical_pass_is_refused"),
    ("coverage-hold-removed", "AC-04", AC4, DOMAIN, "    if uncovered:\n", "    if False:\n",
     COMPOSED, "test_removed_required_predicate_blocks_admission"),
    ("composition-disconnected", "014-composition", AC1, PROFILE_MODULE, "if proof_mappings is not None else None)",
     "if False else None)", COMPOSED, "test_composed_profile_derives_and_persists_the_fx_u4_plan"),
    ("prior-obligation-drop-accepted", "014-repair-preservation", AC4, DOMAIN, "        if dropped:\n",
     "        if False:\n", COMPOSED, "test_dropped_prior_obligation_holds"),
    ("judgment-inputs-change-accepted", "014-repair-preservation", AC4, DOMAIN, "        if changed:\n",
     "        if False:\n", COMPOSED, "test_changed_judgment_reviewer_inputs_hold"),
    ("unauthorized-supersession-accepted", "014-repair-preservation", AC4, DOMAIN,
     "supersession.authorized_by != supersession_authority or not supersession_authority", "False",
     COMPOSED, "test_unauthorized_supersession_holds"),
    ("prior-proof-skip-accepted", "014-repair-preservation", AC4, REPAIR, PASSED_REPLAY,
     "elif replay.get(old.obligation_id) not in (ReplayStatus.PASSED, ReplayStatus.SKIPPED):",
     COMPOSED, "test_skipped_prior_proof_is_rejected"),
    ("prior-proof-failure-accepted", "014-repair-preservation", AC4, REPAIR, PASSED_REPLAY,
     "elif replay.get(old.obligation_id) not in (ReplayStatus.PASSED, ReplayStatus.FAILED):",
     COMPOSED, "test_failed_prior_proof_is_rejected"),
    ("replacement-proof-unchecked", "014-repair-preservation", AC4, REPAIR,
     " or replay.get(replacement) is not ReplayStatus.PASSED", "",
     COMPOSED, "test_supersession_without_passing_replacement_is_rejected"),
    ("fault-before-intact-undiagnosed", "014-proof-order", AC1, ORDER, "if step.kind == FAULT and INTACT not in same:",
     "if False:", UNIT, "test_out_of_order_evidence_is_diagnosed"),
    ("missing-plan-ancestry-undiagnosed", "014-proof-order", AC1, ORDER,
     "if not any(a.kind == PLAN for a in ancestors):", "if False:", UNIT, "test_missing_plan_ancestry_is_diagnosed"),
    ("prior-proof-drop-accepted", "014-repair-preservation", AC4, REPAIR, PASSED_REPLAY,
     "elif replay.get(old.obligation_id) not in (ReplayStatus.PASSED, None):",
     COMPOSED, "test_dropped_prior_proof_is_rejected"),
    # Revision 1: controls for the independent-review repairs.
    ("path-normalization-removed", "AC-02", AC2, DOMAIN, '        if part == "..":\n', "        if False:\n",
     UNIT, "test_disguised_implementation_sources_are_circular"),
    ("blank-list-items-accepted", "AC-01", AC1, DOMAIN,
     "if isinstance(value, tuple) and value and not any(_blank(v) for v in value):",
     "if isinstance(value, tuple) and value:", UNIT, "test_blank_list_items_are_incomplete"),
    ("live-supersession-accepted", "014-repair-preservation", AC4, DOMAIN, "    if live:\n", "    if False:\n",
     UNIT, "test_supersession_of_a_live_obligation_is_invalid"),
    ("live-obligation-exempted", "014-repair-preservation", AC4, REPAIR,
     "if old.obligation_id in replacements and kept is None:", "if old.obligation_id in replacements:",
     UNIT, "test_live_obligation_is_replayed_even_if_named_superseded"),
    ("authority-digest-unchecked", "AC-04", AC4, ADAPTER,
     'return body is not None and sha256(body).hexdigest() == record["sha256"]', "return True",
     COMPOSED, "test_review_record_digest_and_schema_version_are_checked"),
    ("pointer-consistency-removed", "014-repair-preservation", AC4, SERVICE_MODULE,
     'return state["plan_ref"] == plans[-1]["ref"] and state["plan_digest"] == plans[-1]["digest"]', "return True",
     COMPOSED, "test_lost_plan_pointer_is_not_an_empty_history"),
    # Revision 2: controls for the confirmatory-review repairs.
    ("emptied-state-accepted", "014-repair-preservation", AC4, SERVICE_MODULE,
     "if (version, state) != (0, {}) and not _valid_state(state, requirement_id):",
     "if state and not _valid_state(state, requirement_id):",
     COMPOSED, "test_emptied_or_non_object_state_is_a_hold_not_an_empty_history"),
    ("nested-root-comparison-removed", "AC-02", AC2, DOMAIN, "folded[:len(prefix)] == prefix", "folded[:1] == prefix",
     UNIT, "test_nested_roots_and_prefixed_whitespace_are_circular"),
]
_OUTCOME = re.compile(r"^(FAIL|ERROR): (\w+) \(", re.MULTILINE)


def digest(path: str) -> str:
    return sha256((ROOT / path).read_bytes()).hexdigest()


def compose(state: Path) -> UpstreamProfile:
    state.mkdir(mode=0o700)
    contract = Ref(PROJECT, PROFILE, "FX-U4-contract", "sha256:" + digest(CONTRACT), "repository:" + CONTRACT)
    return UpstreamProfile(
        LocalEvidenceRepository(state / "evidence", PROJECT, PROFILE), SQLiteOperationalStore(state / "operational.sqlite"),
        PROJECT, PROFILE, contract, INVOCATION, "Founder", frozenset({"private"}),
        premise_evidence=RetainedDoctorPremiseEvidence(ROOT, Path(PREMISE_MAPPING), PREMISE_SHA256, PROJECT, PROFILE),
        premise_target="AlienLogicLab/alienintent-sandbox",
        proof_mappings=RetainedPredicateMapping(ROOT, Path(MAPPING), MAPPING_SHA256, PROJECT, PROFILE),
        mapping_reviewer="POSTW1-VERIFY-010", supersession_authority="Founder")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--invocation", default=INVOCATION)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    candidate = Ref(PROJECT, PROFILE, "candidate", "sha256:" + sha256(revision.encode()).hexdigest(), "git:" + revision)
    fixture_digest = "sha256:" + sha256(b"".join((ROOT / p).read_bytes() for p in (
        "tools/evidence/fx_u4_evidence.py", TESTS, CONTRACT, MAPPING))).hexdigest()
    profile = compose(args.output / "state")
    requirement = retained_requirement_revision(ROOT, SPECIFICATION, REQUIREMENT, PROJECT, PROFILE)
    plan = profile.proofs.derive(requirement, retained_design_ref(ROOT, DESIGN, REQUIREMENT, PROJECT, PROFILE), 0)
    if not isinstance(plan, ProofPlan):
        raise RuntimeError(f"FX-U4 plan did not derive: {plan}")
    plan_ref = Ref(**profile.proofs.read(REQUIREMENT)[1]["plan_ref"])
    refs, observations, outcomes = [plan_ref], [], []

    def run(root, control, obligation, phase, test, applications, preceding):
        cmd = [sys.executable, "-m", "unittest", MODULE + test, "-v"]
        env = dict(os.environ, PYTHONPATH=str(root / "src") + os.pathsep + str(root), PYTHONDONTWRITEBYTECODE="1")
        try:
            completed = subprocess.run(cmd, cwd=root, env=env, capture_output=True, timeout=120)
            status, raw = completed.returncode, completed.stdout + completed.stderr
        except subprocess.TimeoutExpired as error:
            status, raw = None, (error.stdout or b"") + (error.stderr or b"") + b"\nTIMEOUT\n"
        text = raw.decode(errors="replace")
        failed = tuple(m.group(2) for m in _OUTCOME.finditer(text) if m.group(1) == "FAIL")
        errors = tuple(m.group(2) for m in _OUTCOME.finditer(text) if m.group(1) == "ERROR")
        filename = f"{control}-{phase}.log"
        (args.output / filename).write_bytes(raw)
        expected = "nonzero failure of the named assertion only" if phase == "fault" else "exit 0"
        observation = {"schema_version": 1, "fixture": "FX-U4", "control": control, "phase": phase, "command": cmd,
                       "expected": expected, "exit_status": status, "raw_output_sha256": sha256(raw).hexdigest(),
                       "raw_output": filename, "application_count": applications, "failed_assertions": list(failed),
                       "errors": list(errors)}
        recorded = profile.proofs.record(obligation, candidate, fixture_digest, args.invocation, expected,
                                         json.dumps(observation, sort_keys=True), status, control=control, phase=phase,
                                         preceding=preceding)
        if not isinstance(recorded, Ref):
            raise RuntimeError(f"{control}/{phase}: evidence not recorded: {recorded}")
        observation["observation_ref"] = asdict(recorded)
        observations.append(observation)
        refs.append(recorded)
        print(control, phase, status, flush=True)
        return ControlRun(phase, status, applications, failed, errors), recorded

    with tempfile.TemporaryDirectory(prefix="fx-u4-") as tmp:
        root = Path(tmp)
        shutil.copytree(ROOT / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "tests", root / "tests", ignore=shutil.ignore_patterns("__pycache__"))
        for path in (MAPPING, PREMISE_MAPPING, SPECIFICATION, DESIGN, "docs/evidence/wave2-design-verification.json", *RETAINED):
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, root / path)
        for control, enforcement, obligation, path, old, new, test_class, test in CONTROLS:
            target = root / path
            original = target.read_text()
            count = original.count(old)
            if count != 1:
                raise RuntimeError(f"{control}: expected exactly one mutation site, got {count}")
            intact, previous = run(root, control, obligation, "intact", f"{test_class}.{test}", 0, (plan_ref,))
            target.write_text(original.replace(old, new))
            fault, previous = run(root, control, obligation, "fault", f"{test_class}.{test}", count, (previous,))
            domain_green = None
            if control == "composition-disconnected":
                # 014-composition proven-red: the domain tests stay green while the composed assertion fails.
                env = dict(os.environ, PYTHONPATH=str(root / "src"), PYTHONDONTWRITEBYTECODE="1")
                domain = subprocess.run([sys.executable, "-m", "unittest", MODULE + UNIT, "-v"], cwd=root, env=env,
                                        capture_output=True, timeout=120)
                (args.output / f"{control}-fault-domain.log").write_bytes(domain.stdout + domain.stderr)
                domain_green = {"exit_status": domain.returncode, "raw_output": f"{control}-fault-domain.log",
                                "raw_output_sha256": sha256(domain.stdout + domain.stderr).hexdigest()}
            target.write_text(original)
            restored, _ = run(root, control, obligation, "restored", f"{test_class}.{test}", 0, (previous,))
            verdict = evaluate_control(obligation, control, test, (intact, fault, restored))
            discriminated = verdict.qualified and (domain_green is None or domain_green["exit_status"] == 0)
            outcomes.append({"control": control, "enforcement": enforcement, "obligation_id": obligation,
                             "test": f"{test_class}.{test}", "battery_verdict": verdict.reason,
                             "domain_tests_while_disconnected": domain_green, "discriminated": discriminated})
    diagnostics = profile.proofs.proof_order(tuple(refs))
    report = {"schema_version": 1, "fixture": "FX-U4", "baseline": BASELINE, "invocation": args.invocation,
              "candidate_revision": revision, "contract_sha256": digest(CONTRACT), "mapping_sha256": digest(MAPPING),
              "premise_mapping_sha256": digest(PREMISE_MAPPING), "fixture_digest": fixture_digest,
              "requirement_revision": requirement.ref.revision_digest,
              "plan": {"digest": plan.digest, "observation_ref": asdict(plan_ref),
                       "obligations": [o.obligation_id for o in plan.obligations],
                       "premise_refs": [asdict(r) for r in plan.premise_refs]},
              "implementation_files": {p: digest(p) for p in (DOMAIN, BATTERY, ORDER, REPAIR, PORT, SERVICE, ADAPTER,
                                                              PROFILE_MODULE, TESTS)},
              "tokens": None, "cost": None, "measurement_reason": "UNKNOWN: invocation billing telemetry unavailable",
              "controls": outcomes, "proof_order_diagnostics": [asdict(d) for d in diagnostics],
              "observations": observations, "verdict": "independent verifier pending"}
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if all(o["discriminated"] for o in outcomes) and not diagnostics else 1


if __name__ == "__main__":
    sys.exit(main())
