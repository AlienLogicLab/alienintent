# WO-220203 / FX-U3 execution record (PRODUCER)

These are local proof receipts only. They are not an independent verdict, not a release, and
not operational success.

## Identity and authority

- **Issue:** #81. The Factory Director's RELEASED comment (episode
  `factory-director-eeb12163b1f84428bafed8b9f46ac7e9`, 2026-09-24T08:10:47Z) authorizes
  IMPLEMENT for WO-220203 only (DAG node U3, SF-REQ-014/SF-REQ-051).
- **Invocation:** `AlienLogicLab/alienintent#81:PRODUCER:b2ddac1f-5d65-45bc-9511-5e8996123534`.
- **Worker:** Morty, Claude `claude-opus-5-5`.
- **Branch:** runtime-managed `b-disp/7603a51e-bcd3-4f98-b44a-45bd7cf7b205`.
- **Admission baseline:** `06e7e0c1f384e29c304788b11e0e559d8bdacc73` (`origin/main`). It was
  clean at admission, and baseline `pytest tests` passed 526/526.
- **Work order:** `docs/work-units/wave2/WO-220203.md`, sha256 `4bbc7166…a1e7`. This equals the
  native Agent Ready READY input
  (`docs/evidence/wave2-readiness-assessments/WO-220203.2026-09-23T175207.676430Z.assessment.json`).
  The packet and allocation are
  `docs/evidence/wave2-execution-packets/WO-220203.{packet,allocation}.json`.
- **Predecessor:** WO-220102 / S1, merged by `0515444`, an ancestor of the baseline. The S1 code
  and receipts are unmodified: `git diff 06e7e0c..HEAD` touches only the nine U3 paths listed
  below. The S1 focused regression passes (58 tests).

## Commits (in order)

1. `ed28aaa`: FX-U3 contract and semantic predicate mapping, pinned before implementation.
2. `dc6d16d`: implementation. Changed files:
   - `evidence_learning/domain/premise.py`
   - `ports/premise_evidence.py`
   - `application/premise_service.py`
   - `composition/premise_evidence.py`
   - `composition/upstream_profile.py`
   - `tests/evidence_learning/test_premise_evidence.py`
   - `tools/evidence/fx_u3_evidence.py`
3. `97ade24`: repair of independent review 1, plus contract Revision 1 and the mapping revision.
4. `a8b7aab`: repair of independent review 2, plus contract Revision 2.
5. `3c04a67`: repair of independent review 3, plus contract Revision 3 and the re-pinned mapping.
6. `936a991`: closes the LOW items from the final review, plus contract Revision 4. **This is the
   revision proven below** (`report.json` `candidate_revision`).

The evidence commit that adds this record and `docs/evidence/wo-220203-fx-u3/` is the published
candidate head. The Issue comment records its exact SHA.

## What was built

- **Retained evidence read.** The bridge reads retained installation-doctor capability
  evidence:
  - `docs/evidence/py09b-live-checks-2026-09-21.json`, sha256 `526435a0…acffaf`. It contains the
    PY-09B doctor run, `disposition=PASS` over all eight `REQUIRED_CHECKS`.
  - `docs/evidence/py10/proof-run.json`, sha256 `d8fa0efa…ec5358`. It contains the PY-10 AC 16
    before/after readback.
- **Composition boundary.** `composition/premise_evidence.py` reads the artifacts, turns them
  into neutral `evidence_learning` values, and passes those values to `UpstreamProfile.premises`.
  The mapping and the artifacts are digest-pinned. Reads are confined to the repository root and
  bounded.
- **Four observables.** Each is judged under the SWF-34-derived mapping (sha256
  `598abb9c11791428069e2b5605b51f7ebf61afd537f2ca02c39e6bc8ec1bd589`, which equals `report.json`
  `mapping_sha256`), with eight mapped predicates in total:
  - `POSITIVE_TARGET_ACCESS`: 3 predicates.
  - `PROFILE_SCOPING`: 2 predicates.
  - `OUT_OF_SCOPE_REJECTION`: 2 predicates, each with a literal detail pattern.
  - `OUTSIDE_STATE_READBACK`: 6 type-exact before/after pointers.
- **Missing or failed premise.** Missing, failed, malformed or unachievable premises return
  `InfeasibleProof(reason, missing, evidence_refs, "return the premise to source authority")`.
  There is no credential-denial observable, and a request for one is `UNACHIEVABLE_PREMISE`.
- **Scope.** There are no live probes, no provider calls, no new persisted aggregate, no RAI
  wiring and no sibling work. The new `evidence_learning` modules import neither
  `installation` nor `composition`.

## Independent adversarial reviews (fresh read-only subagent sessions; not the BIU verifier)

- **Review 1 (of `dc6d16d`):** 5 MEDIUM and 7 LOW findings.
  - The premise id was unbound.
  - Null or empty readback was accepted.
  - The mapping was unpinned.
  - Crashes on malformed input.
  - An undeclared artifact was silently dropped.
  - Vacuous refusal passes.
  - Duplicate keys were accepted.
  - A target gap was mislabelled.
  - Contract drift.
  - A relative-import gap.
  - Half-configuration was accepted.

  All were fixed except L5 (the aggregate `ok` is not a mapped predicate), which is recorded
  as an accepted residual. The PRODUCER also excluded the constant-true
  `no_project_identity_other…` check (SF-REQ-014-AC-02).
- **Review 2 (of `97ade24`):** confirmed the fixes. It found 2 MEDIUM and 4 LOW findings,
  all fixed:
  - Unhashable mapping values.
  - A surrogate `UnicodeEncodeError`.
  - Recursion, NUL and path escapes.
  - The doctor branch masking gaps.
  - An import-name gap.
- **Review 3 (of `a8b7aab`, a fuzz of about 28.6k cases):** 2 MEDIUM and 2 LOW findings, all
  fixed:
  - An empty artifact key.
  - Symlink, device, FIFO and oversize reads.
  - Type-inexact readback.
  - Substring detail predicates.
- **Review 4 (of `3c04a67`):** **no material findings**. Its 2 LOW findings and 1
  informational note are closed in `936a991`:
  - A prefix-only pattern.
  - `NaN` readback.
  - A stat/open race.

Accepted residuals, recorded in contract Revisions 1–3:

- The aggregate PY-09B `ok` is not consulted.
- Readback values are not shape-checked beyond being read. Examples are `0`, `[null]` and a
  malformed but equal digest string.
- The regular-file guard has a unit case but no mutation control, because the fault hangs.

VERIFIER judgment note (SF-REQ-051): `every_project_operation_targeted_the_configured_project`
retains one observed Project operation, recorded before the projection writes.

## Commands and results at `936a991`

| Command | Exit | Result | Retained log (sha256) |
|---|---|---|---|
| `PYTHONPATH=src python3 tools/evidence/fx_u3_evidence.py --output docs/evidence/wo-220203-fx-u3` | 0 | 22/22 controls discriminated (intact 0; fault nonzero with `FAIL:`; restored 0) | `wo-220203-fx-u3/report.json` (`f625b7e8…70e5b`), 66 per-phase logs, 66 observation objects |
| `PYTHONPATH=src python3 -m unittest tests.evidence_learning.test_premise_evidence -v` | 0 | 25 tests OK | `regression/unittest-premise-evidence.log` (`e79666a1…21ac`) |
| `PYTHONPATH=src python3 -m pytest -q tests/evidence_learning tests/execution_coordination/test_evidence_verdict_bridge.py tests/composition/test_evidence_profile.py` (S1, unchanged) | 0 | 58 passed | `regression/s1-regression.log` (`2851aa04…ece0`) |
| `python3 tools/fitness/check_architecture.py --root src/alienintent --check all` | 0 | PASS | `regression/architecture.log` (`395cf0ad…d57ba`) |
| `PYTHONPATH=src python3 -m pytest -q tests` | 0 | 551 passed (baseline 526 + 25 new) | `regression/python-tests.log` (`89302e38…d818`) |
| `node scripts/check.mjs all` | 0 | 340 + 18 + 3 passed | `regression/node.log` (`70d4fff6…387e`) |
| `python3 -m pytest -q tools` | 1 | 668 passed. The 1 failure is the known non-hermetic baseline debt `tools/orchestration/test_director.py::test_substantial_technical_analysis_routes_to_codex_primary` (out of scope, unmodified). | `regression/python-tools-known-baseline-debt.log` (`ce6f1923…a511`) |

The 22 negative controls each apply the fault once in the fault phase and not at all in the
intact and restored phases:

1. `missing-observable-accepted`
2. `unsatisfied-observation-accepted`
3. `digest-pin-removed`
4. `target-binding-removed`
5. `credential-denial-premise-accepted`
6. `doctor-precondition-removed`
7. `doctor-required-checks-removed`
8. `outside-state-comparison-removed`
9. `absent-check-invented`
10. `composition-disconnected` (the design's `014-composition` proven-red: disconnect the
    composed caller while the domain stays green)
11. `premise-bridge-import-added`
12. `premise-identity-unbound`
13. `mapping-pin-removed`
14. `mapping-validation-removed`
15. `empty-readback-accepted`
16. `detail-predicate-removed`
17. `duplicate-key-accepted`
18. `absent-target-accepted`
19. `path-confinement-removed`
20. `symlink-confinement-removed`
21. `type-exact-comparison-removed`
22. `detail-pattern-anchoring-removed`

## Acceptance trace

| Criterion | Tests | What it proves |
|---|---|---|
| AC-U3-01 (composed) | `test_composed_profile_reads_retained_doctor_evidence_as_isolation_premise` | `UpstreamProfile.premises` yields `PlatformIsolationPremise` for `AlienLogicLab/alienintent-sandbox`. It has all four observables, 8 satisfied observations, exact artifact and mapping digests, and a doctor ref. Retained artifacts are byte-identical after reading. |
| AC-U3-02 (missing premise) | `missing_outside_state_artifact`, `tampered_artifact`, `absent_mapped_check`, `failed_out_of_scope_rejection`, `changed_outside_state`, `unobserved_outside_state`, `null_or_empty_readback`, `vacuous_…refusal`, `negated_refusal_detail`, `doctor_evidence_…full_pass`, `malformed_doctor_or_target_evidence`, `unreadable_artifact_target`, `evidence_for_another_target`, `configured_target_must_match`, `unpinned_or_missing_mapping`, `malformed_mapping`, `hostile_artifact_content`, `artifact_paths_cannot_escape…`, `readback_comparison_is_type_exact`, `non_standard_json_constants` | Each case returns `InfeasibleProof` with the pinned reason (`MISSING_PREMISE`, `UNSATISFIED_PREMISE`, `DOCTOR_EVIDENCE_UNAVAILABLE`, `TARGET_MISMATCH` or `MAPPING_UNAVAILABLE`). None returns a premise, a denial observation or an exception. |
| AC-U3-03 (unachievable premise) | `test_credential_denial_premise_is_unachievable_not_waived`, `test_premise_id_is_bound_to_the_pinned_mapping` | Requesting `CREDENTIAL_DENIAL` gives `UNACHIEVABLE_PREMISE`. Omitting an observable gives `INCOMPLETE_PREMISE_REQUEST`. Another premise id gives `PREMISE_MISMATCH`. |
| AC-U3-04 (boundary) | `test_premise_modules_import_no_installation_or_composition`, `test_premise_evidence_requires_a_configured_target` | The new `evidence_learning` modules import no `installation` or `composition` module, including relative and name imports. Half-configuration is refused. The existing `UpstreamProfile` callers are unchanged. |

## Measurements and limits

- **Tokens and cost:** UNKNOWN. Invocation billing telemetry is unavailable, and these values
  are not zero.
- **Cycles:** this record is PRODUCER cycle 1 of 3.
- **Proof scope:** proof level is LOCAL_COMPOSED_OR_MECHANICAL on a disposable local fixture
  profile. There was no live operation.
- **Not done here:**
  - No worker was launched.
  - No provider or doctor probe was run.
  - No requirement or DAG was changed.
  - No sibling node was implemented.
  - The withdrawn edge table was not adopted.
  - RAI remains unwired.
- **Semantic truth:** architecture fitness checks and FX-U3 do not certify premise truth.
- **Independent verdict:** pending the separate VERIFIER invocation (JC on Codex). The VERIFIER
  must retrieve the exact published SHA and judge the predicate mapping independently.

## Repair cycle 2: raw-log custody (JC R1)

This section supplements the record above and removes none of it.

- **Finding.** The JC verification of `dcdc4aaa14640fe631bb363f8fe91a615d7e2476` (invocation
  `AlienLogicLab/alienintent#81:VERIFIER:ae92c58f-a092-49db-9235-5ce338b607c1`, receipt
  `docs/evidence/wo-220203-jc-verification.md` at `36aec44`) rejected R1. The 66 phase logs
  named in `report.json` and the 6 regression logs cited above were missing from the published
  candidate. The repository-wide `*.log` rule in `.gitignore` had kept them out of the commit.
- **Originals, not reruns.** The original files still existed, untracked and ignored, in the
  cycle-1 PRODUCER worktree `b-disp/7603a51e-bcd3-4f98-b44a-45bd7cf7b205`. Their mtimes
  (15:43:10–15:45:08 +0700) fall between the proven revision `936a991` (15:43:02) and the
  evidence commit `dcdc4aa` (15:46:26). They were copied with `cp -p`. Nothing was rerun,
  regenerated or edited.
- **Byte check before commit.**
  - All 66 phase logs: `sha256(file)` equals the observation's `raw_output_sha256` in
    `report.json`. Each digest also appears inside the matching immutable object under
    `evidence/objects/`. Result: 66 match, 0 mismatch.
  - All 6 regression logs: each full sha256 matches the abbreviated digest in the table above
    (`e79666a1…21ac`, `2851aa04…ece0`, `395cf0ad…d57ba`, `89302e38…d818`, `70d4fff6…387e`,
    `ce6f1923…a511`).
- **Durable fix.** `docs/evidence/wo-220203-fx-u3/.gitignore` adds `!*.log`, so the cited logs
  in this directory can no longer be silently ignored.
- **Unchanged.** `report.json`, the 66 immutable objects, the contract, the frozen mapping, the
  implementation, the tests and S1 are byte-identical to `dcdc4aa`. This repair adds files only.
- **Tokens and cost:** UNKNOWN, not zero. This is PRODUCER cycle 2 of 3, invocation
  `AlienLogicLab/alienintent#81:PRODUCER:256beca2-8401-4672-9cef-f92057ec53e9`.
