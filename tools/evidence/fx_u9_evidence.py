"""FX-U9 disposable local proof: readiness lint and the retained assessment consumer (WO-220209, SF-REQ-015).

Never touches a live queue, provider, model, network, Project or profile, and never launches Agent Ready: every
producer is a labelled fixture double bound to a disposable fixture package. Run against committed source; the
output directory must be new and every observation is immutable. The PY-10 bootstrap-assessor history is extracted
from pinned Git blobs and the retained Wave 2 records are copied by path; a digest mismatch of either is a HOLD
(exit 2) before any probe runs. Each control mutation is applied exactly once to a disposable source copy: intact
exit 0 -> fault exit 1 at the named assertion -> restored exit 0. A local PASS is not operational acceptance.
"""
from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
ADMISSION_BASELINE = "04cdd8cddaeb1bc19a34b2fae3d988678aaca28d"  # The RELEASED baseline (Issue #105).
PIN_BASELINE = "0588eae74bbbdddfd8650e349fff472f0db20eff"  # Where the Director re-measured the pinned inputs.
CONTRACT = "docs/work-units/wave2/WO-220209.md"
DRAFT = "docs/evidence/wave2-execution-packets/WO-220209.proof-packet.draft.md"
PLAN = "docs/evidence/wave2-proof-fixtures/FX-U9.md"
TEST = "tests/context_assembly/test_readiness_consumer.py"
EC_DOMAIN = "src/alienintent/execution_coordination/domain/readiness.py"
ADAPTER = "src/alienintent/execution_coordination/adapters/assessment_consumer.py"
LINT = "src/alienintent/context_assembly/domain/readiness.py"
SERVICE = "src/alienintent/context_assembly/application/readiness_service.py"
PROFILE_SOURCE = "src/alienintent/composition/upstream_profile.py"
BINDING = "src/alienintent/composition/readiness.py"
FITNESS = ("tools/fitness/check_architecture.py", "tests/test_architecture_fitness.py")
SOURCES = (EC_DOMAIN, "src/alienintent/execution_coordination/ports/readiness.py", ADAPTER, LINT,
           "src/alienintent/context_assembly/ports/readiness.py", SERVICE,
           "src/alienintent/context_assembly/adapters/readiness_clarification.py", BINDING, PROFILE_SOURCE, *FITNESS)
# (label, path, pinned sha256): the contract as natively assessed (input_sha256 of the READY receipt), every other
# input as pinned by the Director at PIN_BASELINE.
PINNED = (("contract", CONTRACT, "23f5b2eebbc1ece64bc8e6635b0c45dcffc36908888ecd5e709d445a342f5e5b"),
          ("draft_as_superseded", DRAFT, "75a37ddfac412833b171cd994729e557ac101aac85b35a93ccbba30f68965e87"),
          ("packet", "docs/evidence/wave2-execution-packets/WO-220209.packet.json",
           "91b972424f1ae8338ed0c235abddf026f792bb79b706ebc9ef48c302527288bb"),
          ("allocation", "docs/evidence/wave2-execution-packets/WO-220209.allocation.json",
           "47b3a0ff9b7857a53ac50690c8baa4591b156eb7e76fa17774424777e961d13d"),
          ("B", "docs/evidence/wave2-candidate-bius.json",
           "5515b6ce24286dd83a40cd295f61dd74a6c55a5b1c407597c0a65db36504d1f1"),
          ("D", "docs/evidence/wave2-dependency-dag.json",
           "be5f39f8d6d8c319dfd990ae9f52c32e84e7db6af13ef87f9d45b6cbeff20476"),
          ("S", "docs/evidence/wave2-specified-requirements.json",
           "332757c43b8754196e45f75a8ce2ee422e19382415e17ed22cd431f348d9b800"),
          ("C", "docs/evidence/wave2-design-contracts.json",
           "56676dd97cd09031882ee01e61af2a15071f1b92f6c914fde2169b682f056242"),
          ("REPAIR", "docs/evidence/wave2-revisions/2026-09-25-wo-220209-candidate-consistency-repair.md",
           "59ea62bd68bd0371cb03f2c9ebb17ad23736ac774511fb99c214ebb0d30e42f6"),
          ("RESP", "docs/evidence/wave2-revisions/2026-09-22-respecify-015-039.md",
           "ad7308bbdcb45dd303bee44a44b4c29cb0a17e783b0f67501d1e88a913495a60"),
          ("M", "docs/evidence/wave1-agent-ready-outcome-matrix.json",
           "f9730f9eccf4022e314f74bdf3d3ac257c0e07d00c76d6cf87419e472fe4e145"),
          ("PM", "docs/evidence/wave1-readiness-assessment-provenance.json",
           "a8f977e0bb26bd7f0b599042ccce853ff5d76dd9e00adff033990550408a8f21"),
          ("T", "docs/evidence/execution-trajectories/PY-10.jsonl",
           "101ffc18714a16f9096bd559fcfa7b15814b80b31dc47c84e1de9fd392cff282"),
          ("U7_contract", "docs/work-units/wave2/WO-220207.md",
           "0e05a12001ee303b5d7eebb4d57afe536def5f2f323c7946a69d1b30390e9525"),
          ("U7_evidence", "docs/evidence/wave2-proof-fixtures/FX-U7.md",
           "7d72d6bfbc4b54255017200eafad958246689ed01e34daf9d6d383079536acaf"))
# Input 8 (PY-10 history) by blob and input 4 (retained Wave 2 records) by name; both are digest-checked.
BLOBS = {"3c53cd3dc751c76eb167bb142d30f61825d3259a": (
             "c32830b931a06562fa12f273d83e55f4b7c1816c:docs/work-units/python/PY-10.assessment.json",
             "093a9d2c212593812e67edb5a7b04a36ac075970cfe970c60ade16cb3506c232"),
         "fe1e3efe3523f4376b2de66a650dca31fecdbfad": (
             "1f16b816cb0d30681eacbb2ea178eb2cf92ddd02:docs/work-units/python/PY-10.assessment.json",
             "1fc95f25b6c2d928fcb325525b46c1850bb56463c2428f0ea56afc99f181ebb4"),
         "30ea7c451505c5f6bfeba5b6496fff2b4fff01e4": (
             "693fef995f03ab3eca43cb74ad5692cdcd69ffcf:docs/work-units/python/PY-10.assessment.json",
             "9561bf71baaea6d0c6caf26eee87a23ab03beb6c83be68bbc5847447cde6e694")}
ASSESSMENTS = "docs/evidence/wave2-readiness-assessments/"
RECORDS = {"WO-220207.2026-09-25T001654.663618Z.assessment.json":
           "2862acb88dec9d240bd2c436cc2aae63ec704c0ef7663beeb5b96240948bd1ff",
           "WO-220102.2026-09-23T041739.192319Z.assessment.json":
           "e8c6d3da41ee96843e93f6f1149a65874cefc7a9f88eb7be4d1f7f0af98a3a71",
           "WO-220102.2026-09-23T053013.882036Z.assessment.json":
           "4df4717c74b957c6f4b21d527c8ec3c93471ecc64e0db56e70d6352641fcb167",
           "FDH-01.2026-09-24T021848.446095Z.assessment.json":
           "b4f70369c8066a097b012e45a48c4a3b7f54942d8fc4c45c64bc5d236d6356d6"}
COPIED = ("docs/evidence/wo-220203-fx-u3-premise-mapping.json", "docs/evidence/wave2-design-contracts.json",
          "docs/evidence/wave2-design-verification.json", "docs/evidence/py09b-live-checks-2026-09-21.json",
          "docs/evidence/py10/proof-run.json", "docs/evidence/wave1-biu-split-replan-design.json", "docs/evidence/wave1-readiness-assessment-provenance.json",
          "docs/evidence/wave1-agent-ready-outcome-matrix.json", "tools/evidence/check_assessment_producer.py",
          "pyproject.toml", *(ASSESSMENTS + name for name in RECORDS))
LABELS = ["SYNTHETIC_MCP_ENVELOPE_FROM_RETAINED_DIRECT", "FIXTURE_PRODUCER_NOT_NATIVE",
          "FIXTURE_MATERIALIZED_RESULT_SET_NOT_U8_PROOF", "SURROGATE_READINESS_HISTORY_NOT_AGENT_READY",
          "CONTRACT4_NOT_INDEPENDENTLY_DESIGN_VERIFIED", "FIXTURE_PACKAGE_NOT_AGENT_READY",
          "INTACT_BINDING_WITHOUT_LIVE_INVOCATION_v1", "LINT_DUTY_SOURCES_v1", "FX_U9_FIXTURE_SOURCES_v1",
          "CLARIFY_ROUTE_v1", "SPLIT_HANDOFF_CONSUMER_PORT_v1", "READINESS_CONSUMER_HOLD_CODES_v1",
          "NO_RELEASE_OBSERVABLE_v1", "FX_C1_EVIDENCE_LAYOUT", "COMPILATION_VALIDATION_HOLD_NOT_CONSUMED_BY_LINT"]
RESIDUALS = ["NATIVE_PRODUCER_POSITIVE_PROOF_U10_EXTENT", "SPLIT_TRANSACTION_U8_EXTENT",
             "AC_06_07_TRACE_OWNERSHIP_UNASSIGNED_IN_DAG", "SF_REQ_029_SERIALIZATION_NOT_CLAIMED",
             "RUBRIC_COPY_AND_DUPLICATE_ENGINE_NOT_MECHANICALLY_DETECTED", "OPERATOR_SURFACE_NOT_BUILT",
             "EDITABLE_CHECKOUT_REVISION_FROM_DIRECT_URL_ONLY", "PRODUCER_ADAPTER_NOT_CONSTRUCTED_FROM_BINDING_U10",
             "SPLIT_HANDOFF_NOT_RETRIED_AFTER_UNMATERIALIZED", "UNKNOWN_INVOCATION_COMPLETION_HELD"]


def node(name: str) -> str:
    return f"{TEST}::{name}"


def probes(*names: str) -> tuple[str, ...]:
    return tuple(node(n) for n in names)


DUTIES = ("decision", "boundary", "verification", "proof_plan", "architecture", "dependency", "dependency_edges")
ENVELOPE_PARITY = probes(*(f"test_direct_mcp_parity[{r}-{m}]" for r in ("ready", "hold")
                           for m in ("structured", "text", "both")))
# (control, file, remove, replace_with, command node ids) ; ("ARCHITECTURE",) runs the fitness checker instead.
CONTROLS = (
    ("K01-lint_bypassed", SERVICE,
     "        if report.holds:\n            return report.holds[0]  # Attributable, and nothing is invoked.\n",
     "        if False:\n            return report.holds[0]  # Attributable, and nothing is invoked.\n",
     probes(*(f"test_missing_duty_lint_hold[{d}]" for d in DUTIES))),
    ("K02-lint_duty_dropped[decision]", LINT, '    ("decision", ("fixed_decisions",)),\n', "",
     probes("test_missing_duty_lint_hold[decision]")),
    ("K02-lint_duty_dropped[boundary]", LINT, '    ("boundary", ("authorized_scope", "excluded_scope")),\n', "",
     probes("test_missing_duty_lint_hold[boundary]")),
    ("K02-lint_duty_dropped[verification]", LINT, '    ("verification", ("verification_obligations",)),\n', "",
     probes("test_missing_duty_lint_hold[verification]")),
    ("K02-lint_duty_dropped[proof_plan]", LINT, "    if not proof_plan:\n", "    if False:\n",
     probes("test_missing_duty_lint_hold[proof_plan]")),
    ("K02-lint_duty_dropped[architecture]", LINT, "    if not isinstance(design_applicability, CurrentVerified):\n",
     "    if False:\n", probes("test_missing_duty_lint_hold[architecture]")),
    ("K02-lint_duty_dropped[dependency]", LINT, "    if missing:\n", "    if False:\n",
     probes("test_missing_duty_lint_hold[dependency]")),
    ("K02-lint_duty_dropped[dependency_edges]", LINT,
     "    if not isinstance(edges, list) or sorted(edges) != sorted(declared):\n", "    if not isinstance(edges, list):\n",
     probes("test_missing_duty_lint_hold[dependency_edges]")),
    ("K03-contract_error_swallowed", LINT, '        holds.append(LintHold(identity, "contract", _field(error), str(error)))\n',
     "        pass\n", probes("test_incomplete_contract_lint_hold")),
    ("K04-lint_hold_as_disposition", LINT, '        return {"record_kind": "LintHold", "reason_code": LINT_HOLD,',
     '        return {"disposition": "HOLD", "record_kind": "LintHold", "reason_code": LINT_HOLD,',
     probes("test_lint_hold_is_not_agent_ready_hold")),
    ("K05-ready_releases", ADAPTER,
     '        status = "APPLICABLE" if isinstance(result, ReadinessEligibility) else "INAPPLICABLE"\n',
     '        status = "APPLICABLE" if isinstance(result, ReadinessEligibility) else "INAPPLICABLE"\n'
     '        if status == "APPLICABLE":\n'
     '            aggregate = "release:" + identity\n'
     '            self.store.commit(self.profile, aggregate, self.store.read_state(self.profile, aggregate)[0], '
     '{"released": identity})\n',
     probes("test_ready_yields_eligibility_only", "test_intact_binding_reaches_consumer_without_release_bypass")),
    ("K06-clarify_auto_reassess", SERVICE, "            if pending:\n", "            if False:\n",
     probes("test_clarify_routes_to_decision_inbox_then_reassess")),
    ("K07-clarify_generic_hold", SERVICE,
     "            items = [self.clarifications.open(identity, attempt, i, q)\n"
     "                     for i, q in enumerate(observed.owner_clarifications)]\n", "            items = []\n",
     probes("test_clarify_routes_to_decision_inbox_then_reassess")),
    ("K08-split_proceeds_without_set", SERVICE,
     '            return Hold(SPLIT_RESULT_SET_NOT_MATERIALIZED, identity, attempt, "U8 supplied no materialized '
     'result set")\n',
     "            return ReadinessEligibility(identity, attempt, report.contract_digest, fingerprint)\n",
     probes("test_split_without_result_set_refuses", "test_no_non_ready_authorizes_implementation[split]")),
    ("K09-split_generic_hold", SERVICE,
     "        results = self.split.handoff(identity, attempt, raw_ref, raw, (body,)) if self.split is not None else "
     "None\n", "        results = None\n", probes("test_split_without_result_set_refuses")),
    ("K10-integration_parent_skipped", SERVICE, "        for unit in (*results.children, results.integration_parent):\n",
     "        for unit in results.children:\n", probes("test_split_result_set_linted_and_reassessed_each")),
    ("K11-stale_applicability_kept", SERVICE, '            self.consumer.invalidate(stale, "SPLIT", attempt)\n',
     "            pass\n", probes("test_split_result_set_linted_and_reassessed_each")),
    ("K12-hold_reassess_loop", SERVICE,
     '        if disposition == HOLD and latest["input_fingerprint"] == fingerprint:\n', "        if False:\n",
     probes("test_hold_requires_prerequisite_then_reassess")),
    ("K13-non_ready_eligible", EC_DOMAIN, "    if disposition != READY:\n", "    if False:\n",
     probes("test_no_non_ready_authorizes_implementation[clarify]",
            "test_no_non_ready_authorizes_implementation[split]",
            "test_no_non_ready_authorizes_implementation[hold]")),
    ("K14-fingerprint_component_dropped[contract]", EC_DOMAIN, '    components = {"contract": contract_digest,\n',
     "    components = {\n", probes("test_fingerprint_change_invalidates_ready[contract]")),
    ("K14-fingerprint_component_dropped[baseline]", EC_DOMAIN, '                  "baseline": baseline,\n', "",
     probes("test_fingerprint_change_invalidates_ready[baseline]")),
    ("K14-fingerprint_component_dropped[decision]", EC_DOMAIN, '                  "decisions": sorted(decisions),\n', "",
     probes("test_fingerprint_change_invalidates_ready[decision]")),
    ("K14-fingerprint_component_dropped[prerequisite]", EC_DOMAIN,
     '                  "prerequisites": dict(sorted(prerequisites.items())),\n', "",
     probes("test_fingerprint_change_invalidates_ready[prerequisite]")),
    ("K14-fingerprint_component_dropped[design]", EC_DOMAIN, '                  "design": dict(sorted(design.items()))}\n',
     "                  }\n", probes("test_fingerprint_change_invalidates_ready[design]")),
    ("K15-overwrite_prior_outcome", ADAPTER, "        attempts = [*attempts, entry]\n",
     "        attempts = [*attempts[:-1], entry]\n",
     probes("test_fresh_assessment_links_predecessor", "test_resolved_blocker_cannot_rewrite_verdict")),
    ("K16-last_write_wins", ADAPTER,
     '            return Hold(ATTEMPT_CONFLICT, identity, attempt, "a different terminal response for this attempt")\n',
     "            pass\n", probes("test_duplicate_and_conflicting_response")),
    ("K17-top_level_only_parsing", EC_DOMAIN,
     "    if shape == MCP:\n        values, bodies, failure = _envelope(document)\n    elif shape == DIRECT:\n",
     "    if shape in (MCP, DIRECT):\n", ENVELOPE_PARITY),
    ("K18-trust_exit_zero", EC_DOMAIN, "    if not values:\n", "    if not values and exit_status != 0:\n",
     probes("test_mcp_failure_cases[no_terminal-0]", "test_zero_exit_without_semantic_result_fails[no_disposition]")),
    ("K19-first_value_wins", EC_DOMAIN,
     "    if len(set(values)) > 1 or len({canonical(b) for b in bodies}) > 1:\n", "    if False:\n",
     probes(*(f"test_mcp_failure_cases[{v}-{e}]" for v in ("conflict_struct_text", "conflict_two_texts")
              for e in (0, 1)), "test_ambiguous_payload_fails[body_conflict]")),
    ("K20-timeout_as_ready", EC_DOMAIN,
     '    if timed_out:\n        return AttemptFailure(TIMEOUT, (), "no terminal result before the deadline", raw_digest)\n',
     "    if timed_out:\n        exit_status = 0\n",
     probes("test_timeout_and_provider_failure_hold[timeout_no_bytes]",
            "test_timeout_and_provider_failure_hold[timeout_with_ready_bytes]")),
    ("K21-history_relabelled", ADAPTER, '            disposition = document.get("disposition")\n',
     '            disposition = {"BLOCKED": "HOLD", "SPLIT_RECOMMENDED": "SPLIT"}.get(document.get("disposition"), '
     'document.get("disposition"))\n', probes("test_py10_history_replay")),
    ("K22-surrogate_ready_admitted", ADAPTER, '                      "native_agent_ready": False,\n',
     '                      "native_agent_ready": disposition == "READY",\n', probes("test_py10_history_replay")),
    ("K23-history_digest_unchecked", ADAPTER, '            if digest(item.raw) != "sha256:" + item.sha256:\n',
     "            if False:\n", probes("test_py10_history_digest_mismatch_holds")),
    ("K24-provenance_check_bypassed", SERVICE, "        if refusal:\n", "        if False:\n",
     probes(*(f"test_unbound_or_unestablished_provenance_holds_before_launch[{v}]"
              for v in ("unbound", "version_unknown", "wrong_package")))),
    ("K25-shape_trusted", EC_DOMAIN, '    if custody is None:\n        return "NO_INVOCATION_CUSTODY"\n',
     '    if custody is None:\n        return None if isinstance(body, dict) and body.get("disposition") in '
     'DISPOSITIONS else "NO_INVOCATION_CUSTODY"\n',
     probes("test_surrogate_and_copied_evidence_refused[schema_perfect_surrogate]")),
    ("K26-copied_evidence_trusted", EC_DOMAIN,
     "    if (custody.product, custody.product_version, custody.executable) != \\\n"
     "            (binding.product, binding.product_version, binding.executable):\n",
     '    if custody.provider_evidence != (body.get("provider_evidence") if isinstance(body, dict) else None):\n',
     probes("test_surrogate_and_copied_evidence_refused[copied_provider_evidence]")),
    ("K27-correlation_unchecked", EC_DOMAIN,
     "    if (custody.attempt_id, custody.input_sha256) != (metadata.attempt_id, metadata.input_sha256):\n",
     "    if False:\n", probes("test_surrogate_and_copied_evidence_refused[disconnected_response]")),
    ("K28-composition_disconnected", PROFILE_SOURCE, "        self.readiness = (ReadinessAdmission(",
     "        self.readiness = None and (ReadinessAdmission(",
     probes("test_intact_binding_reaches_consumer_without_release_bypass", "test_composition_path_executed")),
    ("K29-adapter_import_added", EC_DOMAIN, "from hashlib import sha256\n",
     "from hashlib import sha256\nfrom alienintent.execution_coordination.adapters.assessment_consumer import "
     "RETAINED_ASSESSMENT\n", ("ARCHITECTURE", "domain imports adapters")),
    ("K30-agent_ready_private_import", BINDING, "from importlib import metadata\n",
     "from importlib import metadata\nimport agent_ready  # deliberate violation\n",
     ("ARCHITECTURE", "Agent Ready private import")),
    ("K31-cross_group_pair_added", ADAPTER, "import uuid\n",
     "import uuid\nfrom alienintent.context_assembly.domain.readiness import LintHold\n",
     probes("test_no_new_cross_group_import_pair")),
    # Review R1 repair controls (independent pre-candidate review REJECT; each defect was reproduced first).
    ("K32-duplicate_members_resolved", EC_DOMAIN, "    if len(keys) != len(set(keys)):\n", "    if False:\n",
     probes("test_ambiguous_payload_fails[direct_duplicate_key]", "test_ambiguous_payload_fails[text_duplicate_key]")),
    ("K33-is_error_identity_only", EC_DOMAIN,
     '    error = document.get("isError", False)\n    if not isinstance(error, bool):\n        return (), [], MALFORMED\n'
     "    if error:\n", '    error = document.get("isError", False)\n    if error is True:\n',
     probes("test_ambiguous_payload_fails[is_error_string]", "test_ambiguous_payload_fails[is_error_int]")),
    ("K34-producer_exception_escapes", SERVICE,
     '            response = ProducerResponse(None, None, False, "raised:" + type(error).__name__, None)\n',
     "            raise\n", probes("test_raising_producer_records_attempt_failure")),
    ("K35-annotation_not_retried", ADAPTER, "        for _ in range(2):", "        for _ in range(1):",
     probes("test_clarify_annotation_survives_one_pointer_conflict")),
    ("K36-mcp_exit_required", EC_DOMAIN, "    exited = exit_status == 0 or (shape == MCP and exit_status is None)\n",
     "    exited = exit_status == 0\n", probes("test_mcp_without_process_exit_is_recognized")),
)
ARCHITECTURE = ["-B", "tools/fitness/check_architecture.py", "--root", "src/alienintent", "--check", "all"]
_FAILED = re.compile(r"^FAILED (\S+) - (AssertionError|assert )", re.MULTILINE)
_ERROR = re.compile(r"^ERROR (\S+)", re.MULTILINE)


def digest(body: bytes) -> str:
    return "sha256:" + sha256(body).hexdigest()


def encoded(record) -> bytes:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False, default=repr).encode()


def retain(output: Path, record) -> dict:
    """Immutable observation named by its digest; a differing body under an existing name is refused."""
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


def execute(cwd: Path, argv: list[str], inputs: Path | None) -> dict:
    # A wide terminal keeps pytest's "FAILED <node> - AssertionError" summary untruncated for long node IDs.
    environment = {**os.environ, "PYTHONPATH": str(cwd / "src") + os.pathsep + str(cwd), "PYTHONDONTWRITEBYTECODE": "1",
                   "COLUMNS": "400"}
    if inputs is not None:
        environment["FX_U9_FIXTURE_INPUTS"] = str(Path(inputs).resolve())  # Controls run with another cwd.
    try:
        result = subprocess.run(argv, cwd=cwd, env=environment, text=True, capture_output=True, timeout=900)
        return {"argv": argv, "cwd": str(cwd), "exit_status": result.returncode, "stdout": result.stdout,
                "stderr": result.stderr}
    except subprocess.TimeoutExpired as error:
        return {"argv": argv, "cwd": str(cwd), "exit_status": None, "error": str(error),
                "stdout": str(error.stdout), "stderr": str(error.stderr)}


def verify_inputs(directory: Path) -> list[str]:
    """Digest mismatches of the extracted PY-10 blobs and the copied retained records; nonempty is a HOLD."""
    expected = {**{b: e for b, (_, e) in BLOBS.items()}, **RECORDS}
    return [name for name, value in sorted(expected.items())
            if not (directory / name).is_file() or sha256((directory / name).read_bytes()).hexdigest() != value]


def extract_inputs(target: Path) -> dict:
    target.mkdir(parents=True)
    extracted = {}
    for blob, (source, expected) in sorted(BLOBS.items()):
        data = subprocess.check_output(["git", "cat-file", "blob", blob], cwd=ROOT)
        (target / blob).write_bytes(data)
        extracted[blob] = {"source": source, "sha256": sha256(data).hexdigest(), "expected_sha256": expected}
    for name, expected in sorted(RECORDS.items()):
        data = (ROOT / ASSESSMENTS / name).read_bytes()
        (target / name).write_bytes(data)
        extracted[name] = {"source": ASSESSMENTS + name, "sha256": sha256(data).hexdigest(), "expected_sha256": expected}
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    from tests.context_assembly.test_readiness_consumer import compute_git_facts
    facts = compute_git_facts(ROOT)
    (target / "git-facts.json").write_text(json.dumps(facts, indent=2, sort_keys=True) + "\n")
    extracted["git-facts.json"] = {"source": "git log/merge-base/show at the candidate revision",
                                   "sha256": sha256((target / "git-facts.json").read_bytes()).hexdigest()}
    return extracted


def reconcile_baseline() -> dict:
    """Pinned digests hold at the pin baseline, the admission baseline and the candidate's working tree."""
    rows = []
    for label, path, pinned in PINNED:
        row = {"label": label, "path": path, "pinned_sha256": pinned,
               "at_candidate": sha256((ROOT / path).read_bytes()).hexdigest()}
        for name, revision in (("at_admission_baseline", ADMISSION_BASELINE), ("at_pin_baseline", PIN_BASELINE)):
            try:
                row[name] = sha256(subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT,
                                                           stderr=subprocess.DEVNULL)).hexdigest()
            except subprocess.CalledProcessError:
                row[name] = None
        rows.append(row)
    base = subprocess.check_output(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True).strip()
    moved = subprocess.check_output(["git", "diff", "--name-only", ADMISSION_BASELINE, base, "--", "src", "tests",
                                     "tools"], cwd=ROOT, text=True).split()
    required = {label for label, _, _ in PINNED} - {"contract", "draft_as_superseded"}
    return {"pin_baseline": PIN_BASELINE, "admission_baseline": ADMISSION_BASELINE, "candidate_base": base,
            "inputs": rows, "source_changed_between_admission_and_candidate_base": moved,
            "reconciled": all(r["pinned_sha256"] == r["at_candidate"] == r["at_admission_baseline"] for r in rows)
            and all(r["pinned_sha256"] == r["at_pin_baseline"] for r in rows if r["label"] in required)
            and not moved}


def readback(inputs: Path) -> dict:
    """Representative scenarios through the composed profile on fresh disposable roots; observed outcomes."""
    os.environ["FX_U9_FIXTURE_INPUTS"] = str(Path(inputs).resolve())
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    from dataclasses import asdict, is_dataclass
    from tests.context_assembly import test_readiness_consumer as t

    def summary(result):
        document = asdict(result) if is_dataclass(result) else {"value": repr(result)}
        return {"type": type(result).__name__, **json.loads(json.dumps(document, default=repr))}

    ready = lambda: t.ready_producer()
    scenarios = {
        "ready:intact_binding": (lambda: t.FixtureProducer(t.intact), {}, lambda v: t.candidate(v, text=t.pinned_contract_text())),
        "clarify": (lambda: t.ready_producer(**{t.X: [t.body("CLARIFY", owner_clarifications=list(t.QUESTIONS))]}),
                    {}, t.candidate),
        "split:no_result_set": (lambda: t.ready_producer(**{t.X: [t.split_body()]}),
                                {"split": t.RecordingSplit(None)}, t.candidate),
        "hold": (lambda: t.ready_producer(**{t.X: [t.record("hold")["assessment"]]}), {}, t.candidate),
        "lint:missing_decision": (ready, {}, lambda v: t.candidate(v, drop=("fixed_decisions",))),
        "lint:missing_dependency": (ready, {}, lambda v: t.candidate(v, dependencies=(t.P1, "WO-990999"))),
        "provenance:unbound": (ready, {"executable": None}, t.candidate),
        "provenance:version_unknown": (ready, {"package": {"metadata": False}}, t.candidate),
        "provenance:wrong_package": (ready, {"package": {"name": "agent-ready-surrogate"}}, t.candidate),
        **{f"refused:{name}": ((lambda s=script: t.FixtureProducer(s)), {}, t.candidate)
           for name, (script, _) in t.REFUSALS.items()},
        **{f"mcp_failure:{name}": ((lambda b=build: t.FixtureProducer(
            lambda p, u: t.respond(p, u, t.encode(b()), t.MCP, 0))), {}, t.candidate)
           for name, (build, _) in t.MCP_FAILURES.items()},
    }
    observed = {}
    with tempfile.TemporaryDirectory(prefix="fx-u9-readback-") as temporary:
        for index, (name, (make_producer, options, build)) in enumerate(sorted(scenarios.items())):
            producer = make_producer()
            h = t.Harness(Path(temporary) / f"s{index}", producer, **options)
            h.lifecycle(t.P1, "DONE")
            vector = h.design("verified")
            before = h.guarded()
            result = h.service.assess(build(vector), t.PLAN)
            history = h.consumer.history(t.X)
            observed[name] = {"result": summary(result), "producer_calls": len(producer.calls),
                              "opened_before_call": producer.opened_before_call,
                              "attempts": list(history), "outcome": h.outcome(t.X) if history else None,
                              "pointer": h.consumer.read(t.X)[1],
                              "inbox_open": [e.decision for e in h.profile.inbox.list_open()],
                              "factory_and_release_unchanged": h.guarded() == before}
        h = t.Harness(Path(temporary) / "py10", t.ready_producer())
        replay = h.profile.readiness_history.replay(t.py10_history())
        observed["py10:replay"] = {"records": [{k: v for k, v in r.items() if k not in ("raw_ref", "ref")}
                                               for r in replay]}
        observed["py10:digest_mismatch"] = summary(h.profile.readiness_history.replay(t.py10_history(corrupt=True)))
    return observed


def acceptance_map() -> dict:
    return {
        "SF-REQ-015-AC-01": {"P01": ["test_complete_candidate_proceeds_to_assessment"],
                             "P02": ["test_missing_duty_lint_hold", "test_incomplete_contract_lint_hold"],
                             "P03": ["test_lint_hold_is_not_agent_ready_hold"], "P04": ["covered by P20-P23"]},
        "SF-REQ-015-AC-02": {"P05": ["test_ready_yields_eligibility_only"],
                             "P06": ["test_clarify_routes_to_decision_inbox_then_reassess",
                                     "test_clarify_annotation_survives_one_pointer_conflict"],
                             "P07": ["test_split_without_result_set_refuses"],
                             "P08": ["test_split_result_set_linted_and_reassessed_each"],
                             "P09": ["test_hold_requires_prerequisite_then_reassess"],
                             "P10": ["test_no_non_ready_authorizes_implementation"]},
        "SF-REQ-015-AC-03": {"P11": ["test_fingerprint_change_invalidates_ready"],
                             "P12": ["test_fresh_assessment_links_predecessor", "test_pointer_commit_is_compare_and_swap"],
                             "P13": ["test_resolved_blocker_cannot_rewrite_verdict"],
                             "P14": ["test_duplicate_and_conflicting_response"]},
        "SF-REQ-015-AC-04": {"P15": ["test_direct_mcp_parity", "test_mcp_without_process_exit_is_recognized"],
                             "P16": ["test_mcp_failure_cases", "test_ambiguous_payload_fails"],
                             "P17": ["test_timeout_and_provider_failure_hold",
                                     "test_raising_producer_records_attempt_failure"],
                             "P18": ["test_zero_exit_without_semantic_result_fails"]},
        "SF-REQ-015-AC-05": {"P19": ["test_py10_history_replay", "test_py10_history_digest_mismatch_holds"]},
        "015-envelope-applicability": {"probes": ["P11", "P12", "P13", "P15", "P16", "P17", "P18"],
                                       "proven_red": {"top-level-only parsing": "K17", "trust exit zero": "K18",
                                                      "overwrite prior outcome": "K15"}},
        "015-composed-authority": {
            "P20": ["test_unbound_or_unestablished_provenance_holds_before_launch",
                    "test_unknown_product_version_holds", "test_no_producer_configured_holds"],
            "P21": ["test_surrogate_and_copied_evidence_refused"],
            "P22": ["test_intact_binding_reaches_consumer_without_release_bypass"],
            "P23": ["test_composition_path_executed"],
            "P24": ["tools/fitness/check_architecture.py --check all", "tests/test_architecture_fitness.py",
                    "test_no_new_cross_group_import_pair (U-4)",
                    "test_readiness_modules_never_release_or_import_agent_ready"],
            "proven_red": {"schema-perfect surrogate READY": "K25", "copied provider_evidence": "K26",
                           "wrong package identity": "K24 (P20[wrong_package])",
                           "response disconnected from its invocation": "K27",
                           "provenance checking bypassed": "K24", "composition disconnected": "K28"}},
        "D#/nodes/11/completion_predicate": {
            "four dispositions": ["P05", "P06", "P07", "P08", "P09", "P10"],
            "MCP failure regardless of exit status": ["P16", "P18"],
            "raw bytes and predecessor attempts": ["P12", "P15", "P17"], "changed inputs invalidate READY": ["P11"],
            "separate release gate": ["P05", "P22"], "PY-10 replay, never Agent Ready": ["P19"],
            "CAPABILITY_PROVENANCE_HOLD before launch": ["P20"], "provenance, not schema shape": ["P21"],
            "CLARIFY via SF-REQ-035": ["P06"], "SPLIT port and refusal without a result set": ["P07"],
            "lint and reassessment of each result": ["P08"]}}


def run(output: Path, invocation: str) -> int:
    output.mkdir(parents=True, exist_ok=False)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
    holds: list[str] = []
    if status:
        holds.append("source is not a clean committed candidate")
    inputs = output / "fixture-inputs"
    extracted = extract_inputs(inputs)
    mismatched = verify_inputs(inputs)
    if mismatched:
        print(json.dumps({"fixture": "FX-U9", "exit_status": 2, "hold": "INPUT_DIGEST_MISMATCH", "inputs": mismatched}))
        return 2  # HOLD before any probe runs.
    (inputs / "digests.json").write_text(json.dumps(extracted, indent=2, sort_keys=True) + "\n")
    baseline = reconcile_baseline()
    if not baseline["reconciled"]:
        holds.append("pinned inputs do not reconcile across the pin, admission and candidate revisions")
    paths = [PLAN, TEST, str(Path(__file__).relative_to(ROOT)), *SOURCES]
    record = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-U9",
              "work_unit_id": "WO-220209", "invocation": invocation, "source_revision": revision,
              "source_status": status, "admission_baseline": ADMISSION_BASELINE, "pin_baseline": PIN_BASELINE,
              "candidate_contract_sha256": "0adf1ddfc35b430c91275b54faf26c40445c45b8d80c314d294ef96261add0f0",
              "input_digests": {**{label: "sha256:" + pinned for label, _, pinned in PINNED},
                                **{"py10:" + b: "sha256:" + e for b, (_, e) in sorted(BLOBS.items())},
                                **{"retained:" + n: "sha256:" + e for n, e in sorted(RECORDS.items())},
                                **{p: digest((ROOT / p).read_bytes()) for p in paths}},
              "baseline_reconciliation_ref": retain(output, baseline), "commands": [], "holds": holds,
              "labels": LABELS, "residuals": RESIDUALS, "independent_verdict": "PENDING_FRESH_BIU_VERIFIER",
              "proof_level": "LOCAL_COMPOSED_OR_MECHANICAL", "live_proof": "NOT_ESTABLISHED",
              "measurements": {"model_launches": 0, "provider_calls": 0, "agent_ready_invocations": 0,
                               "tokens": None, "cost": None,
                               "reason": "UNKNOWN: no provider or model is invoked by this local fixture; the "
                                         "producing session's own usage is not measured here"}}
    for label, argv, env_inputs in (
            ("focused", [sys.executable, "-B", "-m", "pytest", "-q", TEST], inputs),
            ("python_regression", [sys.executable, "-B", "-m", "pytest", "-q"], None),
            ("architecture", [sys.executable, *ARCHITECTURE], None),
            ("architecture_fitness_tests", [sys.executable, "-B", "-m", "pytest", "-q", FITNESS[1]], None),
            ("node_regression", ["node", "scripts/check.mjs", "all"], None)):
        observation = execute(ROOT, argv, env_inputs)
        record["commands"].append({"id": label, "command": argv, "exit_status": observation["exit_status"],
                                   "observation_ref": retain(output, observation)})
        if observation["exit_status"] != 0:
            holds.append(label + " failed")
        print(label, observation["exit_status"], flush=True)

    # The digest-mismatch HOLD is itself asserted once: a corrupted extracted blob must exit 2, not 1.
    with tempfile.TemporaryDirectory(prefix="fx-u9-corrupt-") as temporary:
        corrupt = Path(temporary) / "fixture-inputs"
        shutil.copytree(inputs, corrupt)
        victim = corrupt / sorted(BLOBS)[0]
        victim.write_bytes(victim.read_bytes() + b"\n")
        argv = [sys.executable, "-B", str(Path(__file__).relative_to(ROOT)), "--verify-inputs", str(corrupt)]
        observation = execute(ROOT, argv, None)
        record["commands"].append({"id": "input_digest_mismatch_hold", "command": argv, "expected_exit": 2,
                                   "exit_status": observation["exit_status"], "observation_ref": retain(output, observation)})
        if observation["exit_status"] != 2:
            holds.append("input digest mismatch did not HOLD with exit 2")

    controls = []
    with tempfile.TemporaryDirectory(prefix="fx-u9-controls-") as temporary:
        copy = Path(temporary)
        for name in ("src", "tests"):
            shutil.copytree(ROOT / name, copy / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(ROOT / "tools" / "fitness", copy / "tools" / "fitness",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for path in COPIED:
            (copy / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / path, copy / path)
        for control, path, remove, replace_with, nodes in CONTROLS:
            target = copy / path
            original = target.read_text()
            count = original.count(remove)
            if count != 1:
                raise RuntimeError(f"{control}: mutation count {count}, expected exactly one")
            architecture = nodes[0] == "ARCHITECTURE"
            argv = ([sys.executable, *ARCHITECTURE] if architecture
                    else [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *nodes])
            intact = execute(copy, argv, inputs)
            target.write_text(original.replace(remove, replace_with, 1))
            fault = execute(copy, argv, inputs)
            target.write_text(original)
            restored = execute(copy, argv, inputs)
            if architecture:
                assertion = nodes[1]
                named = assertion in fault["stdout"]
            else:
                # Every named node must fail by assertion; an exception in any of them does not discriminate.
                failed = {n for n, _ in _FAILED.findall(fault["stdout"])}
                errors = _ERROR.findall(fault["stdout"])
                assertion = "FAILED " + " ; FAILED ".join(f"{n} - AssertionError" for n in nodes)
                named = set(nodes) <= failed and not errors
            discriminates = (intact["exit_status"] == 0 and fault["exit_status"] == 1 and named
                             and restored["exit_status"] == 0 and target.read_text() == original)
            controls.append({"control": control, "application_count": count, "file": path,
                             "source_digest": digest(original.encode()),
                             "mutation": {"remove": remove, "replace_with": replace_with}, "command": argv,
                             "assertion": assertion, "intact_exit": intact["exit_status"],
                             "fault_exit": fault["exit_status"], "restored_exit": restored["exit_status"],
                             "intact_ref": retain(output, intact), "fault_ref": retain(output, fault),
                             "restored_ref": retain(output, restored), "discriminates": discriminates})
            print(control, intact["exit_status"], fault["exit_status"], restored["exit_status"], discriminates, flush=True)
            if not discriminates:
                holds.append(control + " did not discriminate")

    try:
        observed = readback(inputs)
        record["readback_ref"] = retain(output, observed)
    except Exception as error:  # A failed readback is a hold, never a PASS.
        holds.append("readback failed: " + repr(error))
        observed = {}
    record["exit_status"] = 1 if holds else 0
    report = {
        "fixture_id": "FX-U9", "work_unit_id": "WO-220209", "proof_level": record["proof_level"],
        "acceptance_to_probes": acceptance_map(), "ac_06_07_trace_ownership": "UNASSIGNED_IN_DAG",
        "observability": "READY semantics are counted separately from released work: eligibility only, "
                         "zero admit_release calls and no release:/factory: writes by U9",
        "observed": {name: {"result": o.get("result"), "producer_calls": o.get("producer_calls"),
                            "failure_class": (o.get("outcome") or {}).get("failure_class"),
                            "failure_detail": (o.get("outcome") or {}).get("detail"),
                            "disposition": (o.get("outcome") or {}).get("disposition"),
                            "inbox_open": o.get("inbox_open"),
                            "factory_and_release_unchanged": o.get("factory_and_release_unchanged")}
                     for name, o in sorted(observed.items()) if name.split(":")[0] != "py10"},
        "py10_replay": observed.get("py10:replay"), "py10_digest_mismatch": observed.get("py10:digest_mismatch"),
        "non_claims": ["U8 SplitTransaction prepare/apply and result materialization",
                       "U10 native CLI/MCP adapter conformance and positive native-producer proof",
                       "SF-REQ-015-AC-06 and AC-07", "SF-REQ-029 retained-assessment serialization",
                       "release or lifecycle transition", "anything about Agent Ready itself",
                       "re-verification of the landed WO-220207 checker", "operational acceptance"],
        "prior_art_not_imported": ["tools/orchestration/readiness_assessment.py",
                                   "tools/orchestration/factory_director_inputs.py", "tools/live/release_admission.py",
                                   "tools/evidence/check_assessment_producer.py (test-side negative shape evidence)"],
        "readback_ref": record.get("readback_ref"), "exit_status": record["exit_status"]}
    (output / "execution-record.json").write_text(json.dumps(record, indent=2) + "\n")
    (output / "run-report.json").write_text(json.dumps(report, indent=2, default=repr) + "\n")
    (output / "proven-red.json").write_text(json.dumps({"controls": controls, "holds": holds}, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-U9", "exit_status": record["exit_status"], "holds": holds,
                      "controls": len(controls), "discriminated": sum(c["discriminates"] for c in controls),
                      "output": str(output)}))
    return record["exit_status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--invocation")
    parser.add_argument("--verify-inputs", type=Path)
    arguments = parser.parse_args()
    if arguments.verify_inputs is not None:
        bad = verify_inputs(arguments.verify_inputs)
        print(json.dumps({"hold": "INPUT_DIGEST_MISMATCH", "inputs": bad} if bad else {"verified": len(BLOBS) + len(RECORDS)}))
        raise SystemExit(2 if bad else 0)
    if arguments.output is None or not arguments.invocation:
        parser.error("--output and --invocation are required")
    raise SystemExit(run(arguments.output, arguments.invocation))
