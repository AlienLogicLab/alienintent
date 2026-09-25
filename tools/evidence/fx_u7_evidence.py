"""FX-U7 disposable local proof: compiler validation of supplied candidates and frozen split proposals.

Never touches a live queue, provider, Project or profile. Run against committed source; the output directory
must be new and every observation is immutable. The SWF-33 historical contracts are extracted from pinned Git
blobs (never working-tree paths); a digest mismatch is a HOLD (exit 2) before any probe runs. Each control
mutation is applied exactly once to a disposable source copy: intact exit 0 -> fault exit 1 at the named
assertion -> restored exit 0. A local PASS is not operational acceptance.
"""
from dataclasses import asdict
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
ADMISSION_BASELINE = "7b6e19c4a17f1d797f61c99edafadd4857940dd6"
PIN_BASELINE = "e36e335"
CONTRACT = "docs/work-units/wave2/WO-220207.md"
PLAN = "docs/evidence/wave2-proof-fixtures/FX-U7.md"
TEST = "tests/context_assembly/test_compilation_validation.py"
DOMAIN = "src/alienintent/context_assembly/domain/compilation.py"
SERVICE = "src/alienintent/context_assembly/application/compilation_validation_service.py"
SOURCES = (DOMAIN, "src/alienintent/context_assembly/ports/compilation.py", SERVICE,
           "src/alienintent/context_assembly/adapters/compilation_repository.py",
           "src/alienintent/composition/compilation.py", "src/alienintent/composition/upstream_profile.py")
CONTRACT_PIN = "5a79622"  # The Director pin commit that added the FX-U7 packet to the contract.
# (label, path, pinned sha256 at its pin revision: the contract at CONTRACT_PIN, every other input at e36e335)
PINNED = (("contract", CONTRACT, "0e05a12001ee303b5d7eebb4d57afe536def5f2f323c7946a69d1b30390e9525"),
          ("packet", "docs/evidence/wave2-execution-packets/WO-220207.packet.json",
           "5c4a88ebd9c1b2e5f2d14a00f3de26c99e3eee95d91a8f456cffd0949532efde"),
          ("allocation", "docs/evidence/wave2-execution-packets/WO-220207.allocation.json",
           "2e297c63f2568abc22144a2432f33577cc5ad5b279825dbd160031ad6f810ac9"),
          ("C", "docs/evidence/wave2-design-contracts.json",
           "56676dd97cd09031882ee01e61af2a15071f1b92f6c914fde2169b682f056242"),
          ("D", "docs/evidence/wave2-dependency-dag.json",
           "b767305fde58e503bfacac95f3ea8c8eb23c6aabd7bb0211c93d5c6af16402af"),
          ("B", "docs/evidence/wave2-candidate-bius.json",
           "6c6e530059a0c076b43ac10750fb313a04b5f5dcd9db7959edc1c6c4c7487fd3"),
          ("S", "docs/evidence/wave2-specified-requirements.json",
           "332757c43b8754196e45f75a8ce2ee422e19382415e17ed22cd431f348d9b800"),
          ("P5", "docs/evidence/wave1-biu-split-replan-design.json",
           "0796f8eb18c853e1c349bc93b4ed8093e56bd2681f7fd968fb518167687bd8d2"))
# U7 pointers that must be byte-identical between the pin baseline and the admission baseline.
U7_POINTERS = {"docs/evidence/wave2-dependency-dag.json": ("/nodes/9", "/proof_fixtures/9", "/acceptance_trace/10",
                                                          "/acceptance_trace/11", "/acceptance_trace/12",
                                                          "/enforcement_obligations/3"),
               "docs/evidence/wave2-candidate-bius.json": ("/bius/9",)}
BLOBS = {"4f864b94191705953cf625fd34d203f0313b602e": ("1f16b816cb0d30681eacbb2ea178eb2cf92ddd02:docs/work-units/python/PY-10.md",
                                                      "7caa6a3c0b2440691c65ab8e95cfd79b449787435f4db63a239066a61d671ed0"),
         "b9e246f2c905af7f3c58e3d4c1b97548ce3fc452": ("35de8d7e9fa0e06f3e3e54e5fe546d78994883ec:docs/work-units/python/PY-10.md",
                                                      "197b05fcc837afbf866bced3c2aaaf849d5d21133935d31f23747c1215b2dbfa"),
         "78b5e01b9aa08bcc0c8977e73768efb62410746f": ("35de8d7e9fa0e06f3e3e54e5fe546d78994883ec:docs/work-units/python/PY-09B.md",
                                                      "cfd06a35e7eb65a7dcf9f9e8ca5175fa611666bf0cdabc9d5da6e8923c5a9428"),
         "fe1e3efe3523f4376b2de66a650dca31fecdbfad": ("35de8d7e9fa0e06f3e3e54e5fe546d78994883ec:docs/work-units/python/PY-10.assessment.json",
                                                      "1fc95f25b6c2d928fcb325525b46c1850bb56463c2428f0ea56afc99f181ebb4")}
COPIED = ("docs/evidence/wo-220203-fx-u3-premise-mapping.json", "docs/evidence/wave2-design-contracts.json",
          "docs/evidence/wave2-design-verification.json", "docs/evidence/py09b-live-checks-2026-09-21.json",
          "docs/evidence/py10/proof-run.json", "docs/evidence/wave1-biu-split-replan-design.json", "pyproject.toml")
LABELS = ["VALIDATION_ONLY_HAND_AUTHORED_CANDIDATES", "SWF33_HISTORICAL_CONTRACT_FIXTURE_NOT_LIVE_MUTATION",
          "PHASE5_CANDIDATE_MECHANISMS_NOT_INDEPENDENTLY_DESIGN_VERIFIED", "DEPENDENCY_AUTHORITY_REUSE_v1",
          "UNRESOLVED_AUTHORITY_SOURCE_v1", "FIXED_DECISION_CONFLICT_RULE_v1", "NO_TRANSITION_OBSERVABLE_v2",
          "FX_C1_EVIDENCE_LAYOUT", "SPLIT_FIXTURE_FAMILIES_v1", "SWF33_REPLAY_EXACT_CLAUSE_RULE_v1",
          "BUDGET_CAPABILITY_BOUND_RULE_v1", "SPLIT_AUTHORITY_BINDING_v1", "IDENTITY_BOUNDS_VALIDATION_v1",
          "ASSESSMENT_HISTORY_VALIDATION_v1", "COMPILATION_HOLD_CODES_v1", "ACTIVE_INVOCATION_OUT_OF_FX_U7",
          "EXISTING_IMPLEMENTATION_INVENTORY_v1", "SYNTHETIC_SPLIT_ISSUER_N5", "DEPENDENCY_SATISFACTION_INITIAL_ONLY",
          "REVIEW_R1_REPAIR_CONTROLS_K35_K42", "REVIEW_R2_REPAIR_CONTROL_K43"]
RESIDUALS = ["SPLIT_APPLY_AND_DERIVATION_NOT_PROVEN_U8_EXTENT", "AC_06_08_TRACE_OWNERSHIP_UNASSIGNED_IN_DAG",
             "BUDGET_ENVELOPE_PARTITION_UNPROVEN", "ACTIVE_INVOCATION_FENCE_NOT_PROVEN_BY_FX_U7",
             "SWF33_ELABORATION_BINDING_INTERPRETIVE", "ORIGINAL_INVENTORY_SUPPLIED_FOR_MARKDOWN_ORIGINAL",
             "EXPECTED_VERSIONS_APPLY_TIME_NOT_CHECKED", "GRAPH_REVISION_BINDING_WITHIN_PAYLOAD_DIGEST",
             "DOWNSTREAM_EDGES_SUPPLIED_BY_PROPOSAL", "ELABORATION_APPROVAL_DIGEST_NOT_RECOMPUTED",
             "CHILD_EXTENT_ACCEPTS_OBLIGATION_ID", "MALFORMED_INPUT_HOLD_REF_ORDER_DEPENDENT"]


def node(name: str) -> str:
    return f"{TEST}::{name}"


def probes(*names: str) -> tuple[str, ...]:
    return tuple(node(n) for n in names)


# (control, file, remove, replace_with, command node ids, expected failing node ids); command None -> pytest nodes.
CONTROLS = (
    ("K01-issue_closure_trusted", DOMAIN, "        if stages.get(edge.source) != DONE:\n",
     '        if projection.get(edge.source) != "CLOSED":\n',
     probes("test_open_done_predecessor_satisfied", "test_closed_nonterminal_predecessor_unsatisfied")),
    ("K02-declared_edge_omitted", DOMAIN, "        if disagreement:\n", "        if False:\n",
     probes("test_declared_edge_disagreement_refused")),
    ("K03-cycle_check_removed", DOMAIN, "    if cyclic:\n", "    if False:\n",
     probes("test_graph_refusal_names_edge[cycle]", "test_split_graph_refusal_names_edge[cycle]")),
    ("K04-endpoint_check_removed", DOMAIN, 'findings.append(("MISSING_ENDPOINT", _ordered(missing)))', "pass",
     probes("test_graph_refusal_names_edge[missing_endpoint]", "test_split_graph_refusal_names_edge[missing_endpoint]")),
    ("K05-predicate_check_removed", DOMAIN, "    if predicates_required and unspecified:\n", "    if False:\n",
     probes("test_graph_refusal_names_edge[no_predicate]", "test_split_graph_refusal_names_edge[no_predicate]")),
    ("K06-offending_edge_dropped", DOMAIN,
     "    return CompilationHold(ranked[0][0], ranked[0][1], mode, candidate, detail, ranked)",
     "    return CompilationHold(ranked[0][0], (), mode, candidate, detail, ranked)",
     probes("test_graph_refusal_names_edge[cycle]", "test_graph_refusal_names_edge[missing_endpoint]",
            "test_graph_refusal_names_edge[no_predicate]")),
    ("K07-contract_validation_swallowed", DOMAIN,
     'findings.append(("INCOMPLETE_CONTRACT", (f"{identity}:{_field(error)}",)))', "pass",
     probes("test_incomplete_contract_refused")),
    ("K08-coverage_category_dropped", DOMAIN, "    for category, field in CATEGORY_FIELDS:\n",
     "    for category, field in CATEGORY_FIELDS[:-1]:\n", probes("test_uncovered_obligation_refused[evidence]")),
    ("K09-design_gate_bypassed", SERVICE, "        if not decision.admitted:\n", "        if False:\n",
     probes("test_design_gate_holds[stale-STALE]", "test_design_gate_holds[unreviewed-REVIEW_REQUIRED]",
            "test_design_gate_holds[absent-NO_DESIGN]")),
    ("K10-authority_check_removed", SERVICE, "        if unresolved:\n", "        if False:\n",
     probes("test_unresolved_authority_holds")),
    ("K11-decision_conflict_ignored", DOMAIN,
     '    return [("DECISION_CONFLICT", _ordered(conflicts))] if conflicts else []', "    return []",
     probes("test_conflicting_decisions_hold")),
    ("K12-hold_writes_transition", SERVICE, '            event, status = HELD_EVENT, "HELD"\n',
     '            event, status = HELD_EVENT, "HELD"\n            self.store.commit(self.profile, "factory:" + mode, '
     'self.store.read_state(self.profile, "factory:" + mode)[0], {"stage": "READY"})\n',
     probes("test_hold_writes_no_transition")),
    ("K13-forward_conservation_skipped", DOMAIN, "    lost = [o for o in obligations if o not in rows]\n",
     "    lost = []\n", probes("test_split_nonconserving_refused[omission]")),
    ("K14-reverse_trace_skipped", DOMAIN,
     '        if entry.get("origin") not in obligations or bound(entry.get("destination")) is None:\n',
     "        if False:\n", probes("test_split_nonconserving_refused[invented_obligation]")),
    ("K15-clause_comparison_relaxed", DOMAIN, "    return clause in body\n",
     '    return " ".join(clause.split())[:20] in " ".join(body.split())\n',
     probes("test_split_nonconserving_refused[weakened_clause]", "test_swf33_replay[unbound]")),
    ("K16-partial_mapping_accepted", DOMAIN, "        if not destinations or None in targets:\n",
     "        if False:\n", probes("test_split_nonconserving_refused[partial_mapping]")),
    ("K17-shared_mapping_as_or", DOMAIN, "        if origin not in resolved:\n", "        if not resolved:\n",
     probes("test_split_nonconserving_refused[integration_duty_dropped]")),
    ("K18-bounds_clipped", DOMAIN, "    if widened:\n", "    if False:\n",
     probes("test_split_bounds_expansion_refused[capability]", "test_split_bounds_expansion_refused[budget_dimension]",
            "test_split_bounds_expansion_refused[repository_scope]")),
    ("K19-split_authority_unchecked", DOMAIN,
     '    if not authority or authority.get("issuer") not in (authority_limits.get("issuers") or ()):\n',
     "    if False:\n",
     probes("test_split_authority_refused[absent]", "test_split_authority_refused[issuer_outside_limits]")),
    ("K20-authority_binding_unchecked", DOMAIN, "    if stale:\n", "    if False:\n",
     probes("test_split_authority_refused[payload_digest_mismatch]",
            "test_split_authority_refused[stale_original_revision]")),
    ("K21-done_original_accepted", DOMAIN, "    if stages.get(origin) == DONE:\n", "    if False:\n",
     probes("test_split_of_done_original_refused")),
    ("K22-predicate_weakening_ignored", DOMAIN,
     "    same = (lambda a, b: a == b) if predicated else (lambda a, b: True)\n", "    same = lambda a, b: True\n",
     probes("test_dependency_rewrite_refused[weakened_predicate]")),
    ("K23-downstream_redirect_accepted", DOMAIN, "                redirected.append(edge.ref)\n",
     "                authorized = (*authorized, *(DependencyEdge(c, edge.target, edge.predicate) for c in children\n"
     "                                             if (c, edge.target) in result))\n",
     probes("test_dependency_rewrite_refused[downstream_redirected]")),
    ("K24-prerequisite_copy_unchecked", DOMAIN, '                not_copied.append(f"{edge.source}->{child}")\n',
     "                pass\n", probes("test_dependency_rewrite_refused[prerequisite_not_copied]")),
    ("K25-edge_set_superset_only", DOMAIN, "                pruned.append(edge.ref)\n", "                pass\n",
     probes("test_dependency_rewrite_refused[edge_pruned]")),
    ("K26-inter_child_edge_unchecked", DOMAIN, "            inter_child.append(edge.ref)\n", "            pass\n",
     probes("test_dependency_rewrite_refused[unauthorized_inter_child_edge]")),
    ("K27-identity_grammar_relaxed", DOMAIN, '(?:[A-Z])?\\Z"\n', '(?:[A-Z])?"\n',
     probes("test_identity_bounds_refused[grammar_invalid]")),
    ("K28-identity_collision_ignored", DOMAIN, "    if collisions:\n", "    if False:\n",
     probes("test_identity_bounds_refused[collision_active]", "test_identity_bounds_refused[collision_retired]",
            "test_identity_bounds_refused[collision_reserved]")),
    ("K29-lineage_inferred_from_suffix", DOMAIN, '        split_from = results[child].get("split_from")\n',
     '        split_from = results[child].get("split_from") or (child[:-1] if child[-1].isalpha() else None)\n',
     probes("test_lineage_refused[suffix_only_lineage]")),
    ("K30-invalidation_set_unchecked", DOMAIN, 'findings.append(("INVALIDATION_INCOMPLETE", _ordered(missing)))', "pass",
     probes("test_stale_assessment_history_refused[invalidation_missing_parent]",
            "test_stale_assessment_history_refused[invalidation_missing_changed_dependent]")),
    ("K31-assessment_history_digest_unchecked", DOMAIN, "        if observed is None or observed != expected:\n",
     "        if False:\n", probes("test_stale_assessment_history_refused[history_bytes_altered]")),
    ("K32-stale_ready_as_current", DOMAIN, '            current.append(str(entry.get("unit")))\n',
     "            pass\n", probes("test_stale_assessment_history_refused[stale_ready_as_current]")),
    ("K33-order_dependent_output", DOMAIN, "    return tuple(sorted(set(values)))\n",
     "    return tuple(dict.fromkeys(values))\n", probes("test_validation_deterministic_under_permutation")),
    ("K34-adapter_import_added", DOMAIN, "from typing import Mapping\n",
     "from typing import Mapping\nfrom alienintent.context_assembly.adapters.compilation_repository import "
     "EvidenceAssessmentHistory\n", ("ARCHITECTURE",)),
    # Review R1 repair controls (independent pre-candidate review REJECT; each defect was admitted before repair).
    ("K35-duplicate_edge_accepted", DOMAIN, "        if key in seen:\n", "        if False:\n",
     probes("test_review_r1_refusals[split:duplicate_edge]", "test_duplicate_edge_refused_in_any_order")),
    ("K36-contract_requirements_unlinked", DOMAIN, "    for contract in contracts:\n", "    for contract in ():\n",
     probes("test_review_r1_refusals[initial:unresolved_authority_via_contract]")),
    ("K37-original_graph_unanchored", DOMAIN, "        if graph:\n", "        if False:\n",
     probes("test_review_r1_refusals[split:original_graph_omitted]")),
    ("K38-original_inventory_unanchored", DOMAIN, "        if lost_clauses:\n", "        if False:\n",
     probes("test_review_r1_refusals[split:original_obligation_omitted]")),
    ("K39-omitted_dependencies_skipped", DOMAIN, '        declared = unit.get("dependencies", [])\n',
     '        declared = unit.get("dependencies")\n        if declared is None:\n            continue\n',
     probes("test_review_r1_refusals[initial:dependencies_omitted]")),
    ("K40-operation_id_optional", DOMAIN, '        if not _text(proposal.get("operation_id")):\n', "        if False:\n",
     probes("test_review_r1_refusals[split:operation_id_absent]")),
    ("K41-contract_clause_substring", DOMAIN,
     '    return verbatim("\\n" + clause + "\\n", "\\n" + _body(unit) + "\\n")\n',
     "    return verbatim(clause, _body(unit))\n", probes("test_review_r1_refusals[split:frozen_clause_truncated]")),
    ("K42-split_requires_done_predecessors", DOMAIN, "    for edge in edges if require_done else ():\n",
     "    for edge in edges:\n", probes("test_split_does_not_require_done_predecessors")),
    # Review R2 repair control.
    ("K43-result_contract_optional", DOMAIN, "        if uncontracted:\n", "        if False:\n",
     probes("test_review_r2_result_without_contract_refused[split:result_contract_as_body]",
            "test_review_r2_result_without_contract_refused[split:result_contract_absent]")),
)
ARCHITECTURE = ["-B", "tools/fitness/check_architecture.py", "--root", "src/alienintent", "--check", "all"]
_FAILED = re.compile(r"^FAILED (\S+) - (AssertionError|assert )", re.MULTILINE)
_ERROR = re.compile(r"^ERROR (\S+)", re.MULTILINE)


def digest(body: bytes) -> str:
    return "sha256:" + sha256(body).hexdigest()


def encoded(record) -> bytes:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


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
        environment["FX_U7_FIXTURE_INPUTS"] = str(Path(inputs).resolve())  # Controls run with another cwd.
    try:
        result = subprocess.run(argv, cwd=cwd, env=environment, text=True, capture_output=True, timeout=900)
        return {"argv": argv, "cwd": str(cwd), "exit_status": result.returncode, "stdout": result.stdout,
                "stderr": result.stderr}
    except subprocess.TimeoutExpired as error:
        return {"argv": argv, "cwd": str(cwd), "exit_status": None, "error": str(error),
                "stdout": str(error.stdout), "stderr": str(error.stderr)}


def verify_inputs(directory: Path) -> list[str]:
    """Digest mismatches of the extracted SWF-33 blobs; nonempty is a HOLD."""
    mismatches = []
    for blob, (_, expected) in sorted(BLOBS.items()):
        path = directory / blob
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != expected:
            mismatches.append(blob)
    return mismatches


def extract_inputs(target: Path) -> dict:
    target.mkdir(parents=True)
    extracted = {}
    for blob, (source, expected) in sorted(BLOBS.items()):
        data = subprocess.check_output(["git", "cat-file", "blob", blob], cwd=ROOT)
        (target / blob).write_bytes(data)
        extracted[blob] = {"source": source, "sha256": sha256(data).hexdigest(), "expected_sha256": expected,
                           "bytes": len(data)}
    return extracted


def pointer_values(document, pointer: str):
    for part in pointer.strip("/").split("/"):
        document = document[int(part)] if isinstance(document, list) else document[part]
    return document


def reconcile_baseline() -> dict:
    """Pinned digests are checked at the pin baseline by blob; the U7 pointers must be equal at the admission one."""
    rows = []
    for label, path, pinned in PINNED:
        pin = CONTRACT_PIN if label == "contract" else PIN_BASELINE
        at_pin = subprocess.check_output(["git", "show", f"{pin}:{path}"], cwd=ROOT)
        current = (ROOT / path).read_bytes()
        row = {"label": label, "path": path, "pin_revision": pin, "pinned_sha256": pinned,
               "at_pin_baseline": sha256(at_pin).hexdigest(),
               "at_admission_baseline": sha256(current).hexdigest()}
        if path in U7_POINTERS:
            row["u7_pointers_identical"] = {p: encoded(pointer_values(json.loads(at_pin), p)) ==
                                            encoded(pointer_values(json.loads(current), p)) for p in U7_POINTERS[path]}
        rows.append(row)
    changed = subprocess.check_output(["git", "diff", "--name-only", PIN_BASELINE, ADMISSION_BASELINE, "--", "src",
                                       "tests", "tools"], cwd=ROOT, text=True).split()
    consumed = ["src/alienintent/context_assembly/application/design_admission_service.py",
                "src/alienintent/context_assembly/domain/design_admission.py",
                "src/alienintent/context_assembly/application/ambiguity_service.py",
                "src/alienintent/execution_coordination/domain/contract.py",
                "src/alienintent/execution_coordination/application/factory_coordinator.py",
                "src/alienintent/execution_coordination/adapters/sqlite_store.py",
                "src/alienintent/execution_coordination/adapters/local_work_management.py",
                "src/alienintent/evidence_learning/adapters/local_evidence_repository.py",
                "src/alienintent/composition/upstream_profile.py"]
    return {"pin_baseline": PIN_BASELINE, "admission_baseline": ADMISSION_BASELINE, "inputs": rows,
            "source_changed_between_baselines": changed,
            "consumed_interfaces_changed": sorted(set(consumed) & set(changed)),
            "reconciled": all(r["pinned_sha256"] == r["at_pin_baseline"] for r in rows)
            and all(all(r.get("u7_pointers_identical", {}).values()) for r in rows)
            and not set(consumed) & set(changed)}


def readback(output: Path, inputs: Path) -> dict:
    """Every scenario through the composed profile on a fresh disposable root; observed reports and holds."""
    os.environ["FX_U7_FIXTURE_INPUTS"] = str(Path(inputs).resolve())
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    from tests.context_assembly import test_compilation_validation as fixture
    observed = {}
    with tempfile.TemporaryDirectory(prefix="fx-u7-readback-") as temporary:
        cases = {**{name: setup for name, (setup, _, _) in fixture.SCENARIOS.items()},
                 "initial:valid": fixture.run_initial(stages=((fixture.P1, "DONE"),)), "split:valid": fixture.run_split_b(),
                 "swf33:bound": fixture.run_split_a()}
        for index, (name, setup) in enumerate(sorted(cases.items())):
            h = fixture.Harness(Path(temporary) / f"s{index}")
            call = setup(h)
            before = h.snapshot()
            result = call()
            version, state = h.service.read(result.candidate_digest)
            record = h.service.retained(fixture.Ref(**state["result_ref"]))
            observed[name] = {"result": result.document(), "pointer_version": version, "pointer": state,
                              "evidence_id": record.evidence_id, "record_value_sha256": sha256(record.value.encode()).hexdigest(),
                              "non_compilation_state_unchanged": h.snapshot() == before,
                              "factory_states": [a for a, _, _ in h.store.list_states(fixture.PROFILE, "factory:")],
                              "release_states": [a for a, _, _ in h.store.list_states(fixture.PROFILE, "release:")],
                              "work_management_receipts": len(h.work.receipts()),
                              "reservations": [asdict(r) for r in h.store.recovery_reservations(fixture.PROFILE)]}
    return observed


def acceptance_map() -> dict:
    return {
        "SF-REQ-013-AC-03": {"P01": ["test_valid_initial_graph_admitted_for_assessment"],
                             "P02": ["test_graph_refusal_names_edge"], "P03": ["test_split_graph_refusal_names_edge"]},
        "SF-REQ-013-AC-04": {"P06": ["test_design_gate_holds"], "P07": ["test_unresolved_authority_holds"],
                             "P08": ["test_conflicting_decisions_hold"], "P09": ["test_hold_writes_no_transition"]},
        "SF-REQ-013-AC-05": {"P09": ["test_hold_writes_no_transition"], "P13": ["test_swf33_replay"],
                             "P14": ["test_split_nonconserving_refused"], "P15": ["test_split_bounds_expansion_refused"],
                             "P16": ["test_split_authority_refused"]},
        "013-dependency-authority": {"P10": ["test_open_done_predecessor_satisfied"],
                                     "P11": ["test_closed_nonterminal_predecessor_unsatisfied"],
                                     "P12": ["test_declared_edge_disagreement_refused"]},
        "U7-PREDICATE": {
            "incomplete contract": ["P04 test_incomplete_contract_refused"],
            "uncovered obligation": ["P05 test_uncovered_obligation_refused"],
            "cyclic/missing/predicate-free edge": ["P02", "P03"], "stale design": ["P06 test_design_gate_holds"],
            "unauthorized replan": ["P16", "P17 test_split_of_done_original_refused"],
            "nonconserving replan": ["P13", "P14", "P15"],
            "deterministic identity rewrites": ["P18 test_valid_split_candidate_admitted_for_assessment",
                                                "P19 test_dependency_rewrite_refused",
                                                "P23 test_validation_deterministic_under_permutation"],
            "preserved predicates": ["P19"], "identity and authority bounds": ["P16", "P20 test_identity_bounds_refused"],
            "lineage": ["P21 test_lineage_refused"],
            "immutable stale-assessment history": ["P13", "P22 test_stale_assessment_history_refused"],
            "validation only": ["P01", "P13", "P18"]},
        "REVIEW_R1_REPAIRS": {"duplicate edge": ["test_review_r1_refusals[split:duplicate_edge]",
                                                  "test_duplicate_edge_refused_in_any_order"],
                              "requirement linked through a contract": [
                                  "test_review_r1_refusals[initial:unresolved_authority_via_contract]"],
                              "original graph/inventory anchored": [
                                  "test_review_r1_refusals[split:original_graph_omitted]",
                                  "test_review_r1_refusals[split:original_obligation_omitted]",
                                  "test_review_r1_refusals[split:frozen_clause_truncated]"],
                              "omitted dependencies": ["test_review_r1_refusals[initial:dependencies_omitted]"],
                              "operation_id required": ["test_review_r1_refusals[split:operation_id_absent]"],
                              "result contract required under a contract original (R2)": [
                                  "test_review_r2_result_without_contract_refused[split:result_contract_as_body]",
                                  "test_review_r2_result_without_contract_refused[split:result_contract_absent]"],
                              "split predecessors": ["test_split_does_not_require_done_predecessors"],
                              "malformed input is a typed hold": ["test_malformed_split_is_a_typed_hold",
                                                                  "test_malformed_initial_is_a_typed_hold",
                                                                  "test_malformed_original_and_policy_are_typed_holds"]},
        "C#/contracts/2/architecture_fitness": {"P24": ["tools/fitness/check_architecture.py --check all",
                                                        "test_context_assembly_adds_no_cross_group_import_pair (D-1)"]}}


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
        print(json.dumps({"fixture": "FX-U7", "exit_status": 2, "hold": "SWF33_INPUT_DIGEST_MISMATCH",
                          "blobs": mismatched}))
        return 2  # HOLD before any probe runs.
    (inputs / "digests.json").write_text(json.dumps(extracted, indent=2, sort_keys=True) + "\n")
    baseline = reconcile_baseline()
    if not baseline["reconciled"]:
        holds.append("pinned inputs or U7 pointers do not reconcile at the admission baseline")
    paths = [CONTRACT, PLAN, TEST, str(Path(__file__).relative_to(ROOT)), *SOURCES]
    record = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-U7",
              "work_unit_id": "WO-220207", "invocation": invocation, "source_revision": revision,
              "source_status": status, "admission_baseline": ADMISSION_BASELINE, "pin_baseline": PIN_BASELINE,
              "candidate_contract_sha256": "00148ba18b4466cb0d30f18ba50af44226210a0c564d15d2f50045af4c3a1ec7",
              "input_digests": {**{label: "sha256:" + pinned for label, _, pinned in PINNED},
                                **{"swf33:" + b: "sha256:" + e for b, (_, e) in sorted(BLOBS.items())},
                                **{p: digest((ROOT / p).read_bytes()) for p in paths}},
              "baseline_reconciliation_ref": retain(output, baseline), "commands": [], "holds": holds,
              "labels": LABELS, "residuals": RESIDUALS, "independent_verdict": "PENDING_FRESH_BIU_VERIFIER",
              "proof_level": "LOCAL_COMPOSED_OR_MECHANICAL", "live_proof": "NOT_ESTABLISHED",
              "measurements": {"tokens": None, "cost": None, "provider_calls": None,
                               "reason": "UNKNOWN: provider usage is unavailable to this local fixture"}}
    for label, argv, env_inputs in (
            ("focused", [sys.executable, "-B", "-m", "pytest", "-q", TEST], inputs),
            ("python_regression", [sys.executable, "-B", "-m", "pytest", "-q"], None),
            ("architecture", [sys.executable, *ARCHITECTURE], None),
            ("node_regression", ["node", "scripts/check.mjs", "all"], None)):
        observation = execute(ROOT, argv, env_inputs)
        record["commands"].append({"id": label, "command": argv, "exit_status": observation["exit_status"],
                                   "observation_ref": retain(output, observation)})
        if observation["exit_status"] != 0:
            holds.append(label + " failed")
        print(label, observation["exit_status"], flush=True)

    # The digest-mismatch HOLD is itself asserted once: a corrupted extracted blob must exit 2, not 1.
    with tempfile.TemporaryDirectory(prefix="fx-u7-corrupt-") as temporary:
        corrupt = Path(temporary) / "fixture-inputs"
        shutil.copytree(inputs, corrupt)
        victim = corrupt / sorted(BLOBS)[0]
        victim.write_bytes(victim.read_bytes() + b"\n")
        argv = [sys.executable, "-B", str(Path(__file__).relative_to(ROOT)), "--verify-inputs", str(corrupt)]
        observation = execute(ROOT, argv, None)
        record["commands"].append({"id": "swf33_digest_mismatch_hold", "command": argv, "expected_exit": 2,
                                   "exit_status": observation["exit_status"], "observation_ref": retain(output, observation)})
        if observation["exit_status"] != 2:
            holds.append("SWF-33 digest mismatch did not HOLD with exit 2")

    controls = []
    with tempfile.TemporaryDirectory(prefix="fx-u7-controls-") as temporary:
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
            argv = ([sys.executable, *ARCHITECTURE] if nodes == ("ARCHITECTURE",)
                    else [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *nodes])
            intact = execute(copy, argv, inputs)
            target.write_text(original.replace(remove, replace_with, 1))
            fault = execute(copy, argv, inputs)
            target.write_text(original)
            restored = execute(copy, argv, inputs)
            if nodes == ("ARCHITECTURE",):
                assertion = "domain imports adapters"
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
        observed = readback(output, inputs)
        record["readback_ref"] = retain(output, observed)
    except Exception as error:  # A failed readback is a hold, never a PASS.
        holds.append("readback failed: " + repr(error))
        observed = {}
    record["exit_status"] = 1 if holds else 0
    bound, unbound = observed.get("swf33:bound", {}).get("result", {}), observed.get("swf33:unbound", {}).get("result", {})
    report = {
        "fixture_id": "FX-U7", "work_unit_id": "WO-220207", "proof_level": record["proof_level"],
        "acceptance_to_probes": acceptance_map(), "ac_06_08_trace_ownership": "UNASSIGNED_IN_DAG",
        "observed": {name: {"record_kind": o["result"]["record_kind"], "reason_code": o["result"].get("reason_code"),
                            "affected_refs": o["result"].get("affected_refs"), "detail": o["result"].get("detail"),
                            "admitted_for_assessment": o["result"].get("admitted_for_assessment", False),
                            "non_compilation_state_unchanged": o["non_compilation_state_unchanged"],
                            "work_management_receipts": o["work_management_receipts"],
                            "release_states": o["release_states"]} for name, o in sorted(observed.items())},
        "swf33_replay": {"unbound_hold": {"reason_code": unbound.get("reason_code"),
                                          "affected_refs": unbound.get("affected_refs")},
                         "bound": {"forward": bound.get("conservation", {}).get("forward"),
                                   "reverse": bound.get("conservation", {}).get("reverse"),
                                   "shared_rows": bound.get("conservation", {}).get("shared_rows"),
                                   "elaboration_bound": bound.get("conservation", {}).get("elaboration_bound"),
                                   "prior_assessments": bound.get("prior_assessments")},
                         "non_verbatim_rows": ["PY-10-READINESS-PREREQUISITES", "PY-10-SCOPE-01"],
                         "residual": "SWF33_ELABORATION_BINDING_INTERPRETIVE"},
        "non_claims": ["initial decomposition derivation (U8)", "SplitTransaction.prepare/apply, identity "
                       "reservation/allocation, invalidation records, atomic apply/readback, recovery (U8)",
                       "SF-REQ-015 lint/submission/reassessment", "013-graph-coverage (U8)",
                       "SF-REQ-013-AC-06, AC-07 and AC-08", "Phase 5 mechanism approval", "operational acceptance"],
        "prior_art_not_imported": ["tools/evidence/check_split_design.py", "tools/evidence/check_wave2_dag.py"],
        "readback_ref": record.get("readback_ref"), "exit_status": record["exit_status"]}
    (output / "execution-record.json").write_text(json.dumps(record, indent=2) + "\n")
    (output / "run-report.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "proven-red.json").write_text(json.dumps({"controls": controls, "holds": holds}, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-U7", "exit_status": record["exit_status"], "holds": holds,
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
        print(json.dumps({"hold": "SWF33_INPUT_DIGEST_MISMATCH", "blobs": bad} if bad else {"verified": len(BLOBS)}))
        raise SystemExit(2 if bad else 0)
    if arguments.output is None or not arguments.invocation:
        parser.error("--output and --invocation are required")
    raise SystemExit(run(arguments.output, arguments.invocation))
