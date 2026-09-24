#!/usr/bin/env python3
"""FX-U5 intact/fault/restored discrimination on isolated source copies, judged by the U4 battery.

The FX-U5 plan is derived first through the composed UpstreamProfile (U4 ProofPlanning over the pinned
mapping, restricted to the U5 node's acceptance IDs); every control run is then recorded through
ProofPlanning.record, so the plan is the root of the evidence ancestry.
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
from alienintent.evidence_learning.domain.proof_plan import ProofPlan, RequirementRevision
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore

ROOT = Path(__file__).resolve().parents[2]
INVOCATION = "AlienLogicLab/alienintent#97:PRODUCER:a206da1a-2d97-4fe5-86c7-42e8e9eacaa3"
BASELINE = "7be12188edf632710fe842d95fc70b444e2ed279"
PROJECT, PROFILE, REQUIREMENT = "AlienLogicLab/alienintent", "fx-u5", "SF-REQ-051"
NODE_ACCEPTANCE = tuple(f"SF-REQ-051-AC-0{n}" for n in (1, 2, 4, 5, 6))
CONTRACT = "docs/evidence/wo-220205-fx-u5.md"
MAPPING, MAPPING_SHA256 = ("docs/evidence/wo-220205-fx-u5-predicate-mapping.json",
                          "e000d1f964ce628e50370ae6db5bff62959e7dd2642ae1d089887d0f7e4fef3a")
PREMISE_MAPPING, PREMISE_SHA256 = ("docs/evidence/wo-220203-fx-u3-premise-mapping.json",
                                   "598abb9c11791428069e2b5605b51f7ebf61afd537f2ca02c39e6bc8ec1bd589")
RETAINED = ("docs/evidence/py09b-live-checks-2026-09-21.json", "docs/evidence/py10/proof-run.json")
SPECIFICATION, DESIGN = "docs/evidence/wave2-specified-requirements.json", "docs/evidence/wave2-design-contracts.json"
DOMAIN = "src/alienintent/context_assembly/domain/design_admission.py"
PORT = "src/alienintent/context_assembly/ports/design_admission.py"
SERVICE = "src/alienintent/context_assembly/application/design_admission_service.py"
ADAPTER = "src/alienintent/composition/design_admission.py"
PROFILE_MODULE = "src/alienintent/composition/upstream_profile.py"
TESTS = "tests/context_assembly/test_design_admission.py"
MODULE = "tests.context_assembly.test_design_admission."
COMPOSED, UNIT = "DesignAdmissionTests", "DesignAdmissionDomainTests"
OB = {k: f"{REQUIREMENT}/SF-REQ-051-AC-0{n}/{p}" for k, n, p in (
    ("AC-01", 1, "proportional-contract"), ("AC-02", 2, "material-decisions-block"),
    ("AC-04", 4, "impossible-premise-rejected"), ("AC-05", 5, "revision-invalidation"),
    ("051-review-applicability", 5, "051-review-applicability"), ("AC-06", 6, "readiness-refusal"),
    ("051-architecture-boundary", 6, "051-architecture-boundary"))}
ARCH, REVIEW = "051-architecture-boundary", "051-review-applicability"


def control(name, enforcement, path, old, new, test, test_class=COMPOSED):
    return (name, enforcement, OB[enforcement], path, old, new, test_class, test)


# (control, enforcement, obligation, file, old, new, test class, test)
CONTROLS = [
    control("authority-hold-bypassed", ARCH, DOMAIN, "    if authority is None or authority.status != DISPOSED:\n",
            "    if False:\n", "test_direction_dependent_admission_holds_on_open_authority"),
    control("observed-edges-as-policy", ARCH, DOMAIN,
            "for e in design.dependency_edges)\n",
            "for e in design.dependency_edges\n                     if authority is None or e['target'] not in "
            "authority.observed_edges.get(e['source'], ()))\n", "test_observed_edge_is_not_permission"),
    control("architecture-check-ignored", ARCH, DOMAIN, "    if failed:\n", "    if False:\n",
            "test_forbidden_adapter_import_holds_before_review"),
    control("interface-compatibility-removed", ARCH, DOMAIN, "    if unmet:\n", "    if False:\n",
            "test_incompatible_consumer_input_holds"),
    control("review-before-checks-accepted", REVIEW, DOMAIN, "    if design is None or report is None:\n",
            "    if False:\n", "test_review_before_checks_is_refused"),
    control("self-review-accepted", REVIEW, DOMAIN, '    if review.reviewer["actor"] == design.producer["actor"]:\n',
            "    if False:\n", "test_self_review_is_refused_and_downstream_holds"),
    control("shared-invocation-accepted", REVIEW, DOMAIN,
            '    if review.reviewer["invocation"] == design.producer["invocation"]:\n', "    if False:\n",
            "test_shared_producer_invocation_is_self_review"),
    control("stale-design-review-accepted", REVIEW, DOMAIN, "    if stale:\n", "    if False:\n",
            "test_stale_design_review_replay_holds"),
    control("unauthorized-reviewer-accepted", REVIEW, DOMAIN, '    if review.reviewer["actor"] not in reviewers:\n',
            "    if False:\n", "test_unauthorized_reviewer_is_refused"),
    control("stale-vector-accepted", "AC-05", DOMAIN, "    if changed:\n", "    if False:\n",
            "test_changed_requirement_revision_is_stale"),
    control("history-dropped", "AC-05", SERVICE, '"history": [*base["history"], {"event": event, "ref": asdict(ref)}]',
            '"history": [{"event": event, "ref": asdict(ref)}]', "test_new_design_revision_invalidates_and_retains_history"),
    control("incomplete-design-accepted", "AC-01", DOMAIN, "    if absent:\n        holds.append(",
            "    if False:\n        holds.append(", "test_incomplete_design_holds"),
    control("unexplained-inapplicability-accepted", "AC-01", DOMAIN, "    if unexplained:\n", "    if False:\n",
            "test_unexplained_inapplicability_holds"),
    control("material-decision-open-accepted", "AC-02", DOMAIN, "    if material:\n", "    if False:\n",
            "test_open_material_decision_blocks_and_bounded_local_choice_stays_open"),
    control("unbounded-local-choice-accepted", "AC-02", DOMAIN, "    if unbounded:\n", "    if False:\n",
            "test_unbounded_local_choice_holds"),
    control("blocking-finding-verified", "AC-02", DOMAIN, "    if review.decision == VERIFIED and blocking:\n",
            "    if False:\n", "test_blocking_finding_cannot_be_verified"),
    control("premise-evidence-ignored", "AC-04", DOMAIN, "    if infeasible:\n", "    if False:\n",
            "test_impossible_premise_is_rejected_despite_complete_checklist"),
    control("held-design-verified", "AC-04", DOMAIN,
            "    if review.decision == VERIFIED and report.status == MECHANICALLY_HELD:\n", "    if False:\n",
            "test_verified_review_of_held_design_is_refused"),
    control("readiness-gate-bypassed", "AC-06", SERVICE, "        admitted = isinstance(result, CurrentVerified)\n",
            "        admitted = True\n", "test_readiness_refuses_missing_design_review_and_authority_without_project_state"),
    control("composition-disconnected", "AC-06", PROFILE_MODULE, "if design_reviewers else None)",
            "if False else None)", "test_conforming_independent_review_is_current_and_ready"),
    # Revision 1 (pre-candidate PRODUCER self-review): stale, rejection and history-length guards.
    control("stale-reverified-in-place", REVIEW, SERVICE,
            '        if isinstance(result, ReviewAdmitted) and state["status"] == STALE:\n', "        if False:\n",
            "test_stale_design_is_not_reverified_in_place"),
    control("prior-rejection-overridden", "AC-02", SERVICE,
            '        elif isinstance(result, ReviewAdmitted) and result.decision == VERIFIED and state["last_review"] == REJECTED:\n',
            "        elif False:\n", "test_attributed_rejection_stands_until_repair"),
    control("truncated-history-accepted", "AC-05", SERVICE, '                or len(state["history"]) != version \\\n',
            "", "test_corrupted_state_is_a_hold"),
]
_OUTCOME = re.compile(r"^(FAIL|ERROR): (\w+) \(", re.MULTILINE)


def digest(path: str) -> str:
    return sha256((ROOT / path).read_bytes()).hexdigest()


def compose(state: Path) -> UpstreamProfile:
    state.mkdir(mode=0o700)
    contract = Ref(PROJECT, PROFILE, "FX-U5-contract", "sha256:" + digest(CONTRACT), "repository:" + CONTRACT)
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
        "tools/evidence/fx_u5_evidence.py", TESTS, CONTRACT, MAPPING))).hexdigest()
    profile = compose(args.output / "state")
    full = retained_requirement_revision(ROOT, SPECIFICATION, REQUIREMENT, PROJECT, PROFILE)
    # SF-REQ-051-AC-03 is outside the U5 node extent: the plan covers exactly the node's acceptance IDs.
    requirement = RequirementRevision(full.requirement_id, NODE_ACCEPTANCE, full.ref)
    plan = profile.proofs.derive(requirement, retained_design_ref(ROOT, DESIGN, REQUIREMENT, PROJECT, PROFILE), 0)
    if not isinstance(plan, ProofPlan):
        raise RuntimeError(f"FX-U5 plan did not derive: {plan}")
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
        observation = {"schema_version": 1, "fixture": "FX-U5", "control": control, "phase": phase, "command": cmd,
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

    with tempfile.TemporaryDirectory(prefix="fx-u5-") as tmp:
        root = Path(tmp)
        shutil.copytree(ROOT / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "tests", root / "tests", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "tools" / "fitness", root / "tools" / "fitness", ignore=shutil.ignore_patterns("__pycache__"))
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
                # Composition proven-red: the domain tests stay green while the composed assertion fails.
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
    report = {"schema_version": 1, "fixture": "FX-U5", "baseline": BASELINE, "invocation": args.invocation,
              "candidate_revision": revision, "contract_sha256": digest(CONTRACT), "mapping_sha256": digest(MAPPING),
              "premise_mapping_sha256": digest(PREMISE_MAPPING), "fixture_digest": fixture_digest,
              "requirement_revision": requirement.ref.revision_digest,
              "plan": {"digest": plan.digest, "observation_ref": asdict(plan_ref),
                       "obligations": [o.obligation_id for o in plan.obligations],
                       "premise_refs": [asdict(r) for r in plan.premise_refs]},
              "node_acceptance_ids": list(NODE_ACCEPTANCE),
              "implementation_files": {p: digest(p) for p in (DOMAIN, PORT, SERVICE, ADAPTER, PROFILE_MODULE, TESTS)},
              "tokens": None, "cost": None, "measurement_reason": "UNKNOWN: invocation billing telemetry unavailable",
              "controls": outcomes, "proof_order_diagnostics": [asdict(d) for d in diagnostics],
              "observations": observations, "verdict": "independent verifier pending"}
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if all(o["discriminated"] for o in outcomes) and not diagnostics else 1


if __name__ == "__main__":
    sys.exit(main())
