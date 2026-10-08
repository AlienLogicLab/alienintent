# Work unit: main passes its whole suite

**Label:** `MAIN-GREEN` (a document label; permanent id `ec72af73-e93c-47e2-b9b5-f8423dbffd2a`).
**Status:** Draft revision 3 (work item `ec72af73-e93c-47e2-b9b5-f8423dbffd2a`, at CAPTURE), 2026-10-08. Reviewed (final check PASS). Not approved, not assessed, not released.
**Position on the path:** this is the second of four in maintenance-required mode (Founder 2026-10-06). It runs after
REGRESSION-GATE (`a38f0cb8`, DONE). It is the first work item judged by the whole-suite gate, through the normal
factory: PRODUCER, a fresh VERIFIER on the exact candidate, then CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "ec72af73-e93c-47e2-b9b5-f8423dbffd2a",
 "version": "revision-3",
 "intent": "Make the whole suite (tests/ and tools/) pass on main, under the worker's real conditions, by repairing the causes of the 43 test cases that fail on main 201b2aa, and of the three owned-work markers that make two suite runs at once fail each other. No product behaviour changes except the architecture correction in 2.3 and the call-time default path in 2.4.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-06: make main green before the no-change repair and BOUNDED-ROUTINE-LAUNCH; repair the 39 regressions from 057fbc1 and the older failures.",
  "Founder 2026-10-06: DONE is inadmissible if the candidate causes any previously passing applicable repository test or architecture check to fail.",
  "Founder 2026-10-06: do not weaken production satisfiability or architecture rules to make tests pass. Repair the tests and fixtures so they conform to the real contracts.",
  "Founder 2026-10-06: each root cause is repaired at its source and proven independently: unsatisfiable fixture contracts (direct and through the real CLI subprocess), the domain's role vocabulary, the director test's isolation from the real home folder, and unique per-run owned-work markers instead of serializing the suite.",
  "Founder 2026-10-06: this is the first end-to-end proof of the new assurance path: a broken baseline with known debt, a bounded candidate, the whole-suite baseline-versus-candidate comparison with no new regression, then a green main.",
  "Founder 2026-10-08: the three context-assembly cases whose state admission now refuses (an unregistered dependency, a reference absent at the pointer) keep testing context assembly's own hold. They reach that state by writing the lower-level record directly, through one narrow helper named seed_invalid_state_for_defense_in_depth_test whose comment says why it goes below admission. No satisfiability rule is turned off for them.",
  "Never delete, skip or mark as expected-failure a failing test to make it pass."
 ],
 "authorized_scope": [
  "tests/context_assembly/test_work_contract.py",
  "tests/context_assembly/test_work_context.py",
  "tests/control_plane/test_cli.py",
  "tests/composition/test_sandbox_run_profile.py",
  "src/alienintent/context_assembly/domain/work_context.py",
  "tests/context_assembly/test_role_names.py",
  "tools/orchestration/director.py",
  "tools/orchestration/test_director.py",
  "tests/invocation_runtime/test_owned_work.py"
 ],
 "excluded_scope": [
  "the satisfiability rules themselves (execution_coordination/domain/satisfiability.py) and every other product rule",
  "the packet assessment, the work authorization and context assembly's application code (context_assembly/application/)",
  "the regression gate (invocation_runtime/application/regression_gate.py)",
  "tests/context_assembly/test_work_authorization.py, including `satisfiable = None` in Fx.second (lines 65-70), which the authorization tests use on purpose",
  "tests/composition/test_work_registry.py, including its own `satisfiable = None` lines 164, 328-329 and 709-710 for legacy fixtures (they pass today and are known debt, recorded in section 4)",
  "any test other than the ones named in sections 1-3"
 ],
 "dependencies": [],
 "required_capabilities": [
  "python",
  "filesystem"
 ],
 "budget_policy": {
  "maximum_attempts": 3,
  "hard_wall_clock_seconds": 3600,
  "cancellation_limit": 1
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-9 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation",
  "the VERIFIER runs mutations M1, M2, M3 and M4 of check 7 exactly and records that each makes its named test fail and that reverting makes it pass"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "making the suite faster",
  "removing the legacy `satisfiable = None` fixtures in test_work_registry.py and Fx.second"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by the Landing Authority preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/regression-gate.md"
 ],
 "target_repositories": [
  "AlienLogicLab/alienintent"
 ],
 "baselines": [
  "main"
 ],
 "required_closure_actions": [
  "candidate-published",
  "merged-to-main",
  "landing-record",
  "board-updated",
  "workspaces-cleaned"
 ],
 "stop_escalation_conditions": [
  "a named function, test or line does not exist at the starting revision",
  "a failing test listed in section 1 can only pass by changing a product rule or a file outside authorized_scope",
  "the whole suite at the candidate has a failed or error test case",
  "scope outside the authorized files"
 ]
}
```

## 1. Why: the failing tests and their causes

The whole suite on main fails 43 test cases, and the set is the same as the worker and as the Founder's user. Two runs
recorded it:
- **As the worker,** through the factory's own environment (`registry/precheck-candidate.py`, main `201b2aa`):
  `43 failed, 2849 passed, 7 skipped`. The junit and the log are `manual/path-to-done/main-green/201b2aa-worker.xml`
  and `.log`.
- **As the Founder's user,** in the REGRESSION-GATE VERIFIER's run of `883e4c5`:
  `manual/path-to-done/main-green/883e4c5-founder-user.xml`.

Main has changed since `883e4c5` only in docs and evidence. By cause (the REVIEWER counted these from the worker junit):

1. **39 cases: fixture contracts the satisfiability check refuses.** Commit `057fbc1` turned the check off in
   `Fx.second()` (`tests/context_assembly/test_work_authorization.py` lines 65-70) but not where a registry is built
   another way. The packet these fixtures assess (`contract_payload`, `tests/context_assembly/test_work_contract.py`
   line 18) breaks the satisfiability rules, so `work assess` is not READY and `work authorize` answers
   `AUTHORIZATION_STALE` or `CONTRACT_UNSATISFIABLE`.
   - **27 in `tests/context_assembly/test_work_context.py`.** `Cx.__init__` (line 41) builds its own `WorkRegistry`
     (line 45), and `Fx.packet` (`test_work_authorization.py` lines 73-75) gives every packet `contract_payload`.
     - 23 cases fail at `Cx.admitted` line 53 (`assert 'AUTHORIZATION_STALE' is None`).
     - `test_each_missing_fact_is_a_hold_naming_it[unauthorized-MISSING_RECORD-refs4]` fails with
       `ContextHold(MISSING_RECORD ...)`: its preparation `unauthorized` (line 199) calls `cx.ready` directly and never
       goes through `admitted`.
     - `[...refs7]`, `[...refs8]` and `[...refs9]` (lines 219-223) ask admission to accept a contract naming an
       unregistered dependency, a reference absent at the pointer, and a free-text reference whose first word (`a`)
       is a valid path absent at the pointer. Both admission and context assembly read only a reference's first
       word, so refs9 tests the same branch as refs8 in another form; no case reaches `valid_path` false, on main or
       after this change. The real rule refuses all three (`satisfiability.py` lines 38-44, composed at
       `work_registry.py` lines 930-944). A
       satisfiable fixture alone cannot reach the state they test.
     - `test_a_first_producer_gets_exactly_its_fields_from_the_records` also asserts the old closure actions
       `["merge"]` at line 150. That assertion fails as soon as the fixture is satisfiable.
   - **12 in `tests/control_plane/test_cli.py`.**
     - `test_cli_work_assess_with_and_without_the_readiness_entry` (line 399): `KeyError: 'disposition'`. The packet it
       assesses has no contract block, and the READY assessment at line 422 assesses the registered pointer, not the
       revision.
     - `test_cli_work_authorize_with_and_without_the_readiness_entry` (line 434): `TypeError`; the contract at line 443
       is `contract_payload`.
     - `test_work_context_runs_with_only_the_worker_environment` (line 568) and the 9
       `test_the_worker_profile_answers_every_other_command_with_the_stated_error` cases (line 618) use `Cx`.
     - The two subprocess tests write their own `projects.json` (`_registry_project`, line 338) with no `github` entry,
       so `landing` is false and the rule refuses (`work_registry.py` lines 946-947).
2. **1 case: an old folder name.** `tests/composition/test_sandbox_run_profile.py` line 357 expects
   `launch:SB-01:0`; WORKSPACE-FOLDER-NAMES made it `launch-SB-01-0`.
3. **2 cases: a domain module imports the worker port.** `src/alienintent/context_assembly/domain/work_context.py`
   line 16 imports `CLOSURE, PRODUCER, VERIFIER` from `execution_coordination.ports.worker_provider` (since `d63c10d`).
   That breaks `test_readiness_consumer.py::test_no_new_cross_group_import_pair` (a new cross-group pair) and
   `test_ambiguity.py::AmbiguityTests::test_upstream_composition_has_no_worker_path` (`worker_provider` on the
   question/answer path). The port defines the same three string values at `worker_provider.py` line 12.
4. **1 case: a test that reads the machine's home folder.** `tools/orchestration/test_director.py` line 62 expects
   `gpt-6-astra`, but `director.resolved_codex_model` (`director.py` line 233) reads `~/.codex/config.toml` of whoever
   runs the suite. Its default path is computed once, at import (`config: Path = Path.home() / ...`), so setting `HOME`
   in a test cannot change it. As the worker it reads another home. The tests at lines 354 and 361 call it with no
   argument too.
5. **Not failing alone, failing together.** `tests/invocation_runtime/test_owned_work.py` lines 37-51 and 74-84 use
   the fixed markers `launch:AC08:0`, `:1` and `:2` (and `:20` as a non-match at line 80), and
   `ProcOwnership().owned_work` scans every process on the machine. Two suite runs at once see each other's
   processes, so two gates running at once could reject a good candidate.

## 2. The change

1. **A satisfiable fixture contract.**
   - `tests/context_assembly/test_work_contract.py` gains `satisfiable_payload(identity=IDENTITY, **changes) -> dict`:
     `contract_payload` with exactly the facts the rules require: `required_evidence` `["independent-verifier-accepted"]`,
     `required_capabilities` `["python"]`, `budget_policy`
     `{"maximum_attempts": 1, "hard_wall_clock_seconds": 60, "cancellation_limit": 1}` (the values
     `test_work_registry.py` line 373 uses; the context fields assert `maximum_attempts` 1), `required_closure_actions` `list(ACTIONS)` (from `execution_coordination.domain.closure`,
     as `test_work_registry.py` line 374 already does), and `release_policy` `explicit-human-off`. `changes` apply last.
   - `Cx` (`test_work_context.py`) overrides `packet` so that, with no `payload` given, it uses
     `satisfiable_payload(item.id, **changes)`. This covers `admitted`, `ready` and `unauthorized` alike. `Cx.__init__`
     adds to `self.document`, before writing the configuration file, this `github` entry, which sends no request:
     `{"repository": "AlienLogicLab/alienintent", "application_id": 1, "installation_id": 1, "private_key_path":
     "<root>/no-key.pem", "project": {"project_id": "PVT_fixture", "project_number": 1, "organization":
     "AlienLogicLab", "status_field_id": "S", "priority_field_id": "P"}, "landing": true}`.
   - Line 150 expects the five fixed closure actions (`list(ACTIONS)`), which are now the fixture's.
   - `test_cli.py` gains `_landing(document, tmp_path)`, which adds the same kind of entry with `"landing": true`
     (the values `test_cli_work_link_and_display_with_and_without_the_github_entry` already uses at line 519, plus
     `landing`). Both subprocess tests call it where they add the `readiness` entry (lines 421 and 458).
     - The assess test's revision (line 407) is the packet plus `block(satisfiable_payload(item["id"],
       authority_references=["docs/packet.md"]))`, and the READY assessment at line 422 passes `--file` and `--commit`
       of that revision.
     - The authorize test's contract (line 443) is `satisfiable_payload(item["id"],
       authority_references=["docs/packet.md"])`.
   - No new `satisfiable = None` anywhere.
2. **The three defense-in-depth cases (Founder 2026-10-08).** `test_work_context.py` gains
   `seed_invalid_state_for_defense_in_depth_test(cx, *, dependency=None, reference=None)`. Its docstring says: normal
   admission now refuses this state; the helper writes the lower-level record directly so that context assembly's own
   hold stays tested on its own; it is not a normal authorized workflow. It admits a satisfiable item through the real
   path while the fact holds, then deletes the one record the fact depends on:
   - `dependency=`: registers a work item labelled `dependency`, admits with `dependencies=[dependency]`, then deletes
     that item's `work_item` row from `<root>/work.sqlite` with `sqlite3`, asserting exactly one row is deleted.
     Context assembly finds no record (`application/work_context.py` lines 289-291).
   - `reference=`: commits a file at the reference's first word (unique content), admits with
     `authority_references=[README, reference]`, then deletes that blob's loose object from the clone's
     `.git/objects`. Context assembly cannot read it at the pointer commit (lines 300-306).
   Cases refs7, refs8 and refs9 call the helper with `dependency="unregistered-dependency"`,
   `reference="docs/not-at-the-commit.md"` and `reference="a vault note, not a path"`, and keep their expected holds
   unchanged. Nothing else calls the helper. Admission's own refusal of these contracts stays tested where it is today
   (`tests/execution_coordination/domain/test_satisfiability.py` lines 49-54 and `test_work_registry.py` lines 365-381).
3. **The folder name.** `test_sandbox_run_profile.py` line 357 expects `launch-SB-01-0`.
4. **Role names owned by the domain.** `context_assembly/domain/work_context.py` defines
   `PRODUCER, VERIFIER, CLOSURE = "PRODUCER", "VERIFIER", "CLOSURE"` itself and drops the import.
   `tests/context_assembly/test_role_names.py` (new) asserts they equal `execution_coordination.ports.worker_provider`'s.
5. **No real home folder in the director test.** `resolved_codex_model(config: Path | None = None)` computes
   `Path.home() / ".codex/config.toml"` when called with no path. This is a production edit, chosen over a test-only
   patch because the cause is the import-time default itself: a test-only patch would have to replace the function in
   two module namespaces and would leave the import-time path for every other caller. A real call reads the same file
   as before. `test_director.py` gains an autouse fixture that sets `HOME` to a temporary folder whose
   `.codex/config.toml` holds `model = "gpt-6-astra"`. No test reads the real `~/.codex`.
6. **Unique markers.** `test_owned_work.py` builds each marker from a value made once per test run:
   `f"launch:AC08-{RUN}:<n>"` with `RUN = uuid4().hex`, keeping `:20` as the non-match of `:2`.

A prototype of 2.1, 2.2 and 2.5 on `201b2aa` passed (not the candidate; for the REVIEWER and PRODUCER only):
`manual/path-to-done/main-green/prototype-rev2-on-201b2aa.diff`, sha256 `f88d27af…16cd5`. With it,
`test_work_context.py`, `test_cli.py`, `test_work_contract.py`, `test_work_authorization.py` and
`test_work_registry.py` gave 186 passed, and `tests/context_assembly/` failed only the two cause-3 cases.

## 3. Acceptance checks

1. **The 39 pass under the real rules:** `python3 -m pytest -q tests/context_assembly/test_work_context.py
   tests/control_plane/test_cli.py` passes. `grep -n "satisfiable = None"` finds nothing in
   `test_work_context.py`, `test_cli.py` or `test_work_contract.py`, and `git diff` shows no change to the existing
   lines in `test_work_authorization.py` and `test_work_registry.py`.
2. **The fixture contract is satisfiable** (`test_work_contract.py`, new test
   `test_the_satisfiable_fixture_passes_the_rules`): `unsatisfiable(contract_from_payload(satisfiable_payload()),
   landing=True, present_at_pointer=lambda _: True, registered=lambda _: True,
   provider_dimensions=PROVIDER_DIMENSIONS)` (from `composition.sandbox_run_profile`) returns `()`. The real callbacks
   (a reference committed at the pointer, the `github` landing entry) are exercised by check 1 through the composed
   registry.
3. **The architecture rules pass:** `tests/context_assembly/test_readiness_consumer.py::test_no_new_cross_group_import_pair`,
   `tests/context_assembly/test_ambiguity.py` and `tests/context_assembly/test_role_names.py` pass.
4. **The director test is independent of the machine:** `test_director.py` passes with `HOME` set to an empty
   temporary folder and with `HOME` set to a folder whose `.codex/config.toml` holds another model.
5. **Owned-work tests survive a concurrent run:** two runs of
   `python3 -m pytest -q tests/invocation_runtime/test_owned_work.py` started together both pass. Timing alone can let
   a wrong implementation pass this; M3 is the deterministic proof of 2.6.
6. **The defense-in-depth cases test context assembly's hold:**
   `python3 -m pytest -q tests/context_assembly/test_work_context.py -k test_each_missing_fact_is_a_hold_naming_it`
   passes, and `grep -rn seed_invalid_state_for_defense_in_depth_test tests tools` finds only its definition and the
   three cases (4 lines).
7. **Mutations, run exactly by the VERIFIER** (each with `PYTHONDONTWRITEBYTECODE=1`; revert after each):
   - M1: in `context_assembly/domain/work_context.py`, restore the import of the three names from
     `execution_coordination.ports.worker_provider`. `python3 -m pytest -q tests/context_assembly/test_readiness_consumer.py -k test_no_new_cross_group_import_pair`
     must FAIL; revert, and it must pass.
   - M2: make `Cx.packet` return `super().packet(item, payload, raw, changes)` (the inherited `contract_payload`
     default).
     `python3 -m pytest -q tests/context_assembly/test_work_context.py -k test_a_first_producer_gets_exactly_its_fields_from_the_records`
     must FAIL with `AUTHORIZATION_STALE`; revert, and it must pass.
   - M3: in `test_owned_work.py`, restore the fixed marker `launch:AC08:1` in
     `test_owned_work_outliving_the_wall_clock_is_stopped_with_the_client`. Running that test while a second process
     holds the marker `launch:AC08:1` must FAIL. The VERIFIER first starts that process in the background:
     `(env ALIENINTENT_INVOCATION_ID=launch:AC08:1 setsid sleep 120 &)` (`INVOCATION_MARKER` in
     `invocation_runtime/domain/runtime.py` line 23 names the variable). Revert, and the test must pass while the same
     process is still alive.
   - M4: in `seed_invalid_state_for_defense_in_depth_test`, skip the direct deletes (the row and the blob).
     `python3 -m pytest -q tests/context_assembly/test_work_context.py -k test_each_missing_fact_is_a_hold_naming_it`
     must fail exactly the refs7, refs8 and refs9 cases; revert, and all must pass.
8. **No rule is weakened:** `git diff --name-only <starting revision> <candidate>` lists only files in
   authorized_scope, and the only production (non-test) files among them are
   `src/alienintent/context_assembly/domain/work_context.py` and `tools/orchestration/director.py`. In those two files
   the diff removes no check: the role names keep their values (check 3), and `resolved_codex_model` reads the same
   file for a real call (only when the default path is computed changes). The satisfiability rules, the packet
   assessment, the work authorization, context assembly's application code and the regression gate are
   byte-identical to the starting revision.
9. **Main is green:** the whole suite at the candidate (the regression gate's own candidate run, as the worker) has no
   failed and no error test case. The gate reports no finding.

## 4. Review record

**Revision 3 (2026-10-08).** Follow-up REVIEWER of `76105b5` (FAIL; F1-F9 fixed; new findings N1-N7). The REVIEWER
ran the prototype with the network off (`unshare -rn`, 126 passed) and confirmed that the helper fits the Founder's
decision of 2026-10-08.
- M2 replaces the override with the inherited default, so it fails for the stated reason, not a `NameError` (N1).
- Check 6's grep is recursive (N2).
- M3 starts the marker process in the background, with time for the revert run (N3).
- excluded_scope allows the tests named in sections 1-3 (N4).
- The `budget_policy` values are stated (N5).
- refs9 is described as what it really tests (N6).
- The satisfiability lines are 38-44, `Fx.second` 65-70 (N7).
- Final check of `483c9aa`: PASS, with one low correction (`list(ACTIONS)` is at line 374) applied.

**Revision 2 (2026-10-08).** REVIEWER of `9ad902a` (FAIL; F1-F9). The Founder decided F2 on 2026-10-08.
- F1: check 1's grep is limited to the files this packet changes. The `satisfiable = None` lines in
  `test_work_registry.py` (164, 328-329, 709-710) are out of scope and recorded as known debt next to `Fx.second`.
- F2: refs7-9 go through `seed_invalid_state_for_defense_in_depth_test` (2.2), with check 6 and mutation M4. The
  REVIEWER's suggestion for refs7 (retire the dependency after authorization) would not reach the hold, because
  context assembly holds only when the record is absent and a retired record is still shown; so the helper deletes
  the row.
- F3: the refs4 case is named, and `Cx` overrides `packet` so `ready` and `unauthorized` get the satisfiable payload.
  M2 (formerly M3) is placed at that override. The line-150 closure-action assertion is named.
- F4: check 8 limits every changed file to authorized_scope and names both production files.
- F5: the exact `github` entries are stated. The prototype ran `test_cli.py` with no network (47 passed).
- F6: checks are numbered 1-9 in order, mutations M1-M4.
- F7: `Cx.__init__` is at line 41 and builds the registry at line 45; the intent names the three markers.
- F8: check 5 names M3 as the deterministic proof; check 2 names its callbacks.
- F9: lines 354 and 361 are named; the autouse fixture covers them; the production edit to `director.py` is explained.
- `test_work_authorization.py` leaves authorized_scope: nothing in it changes.

**Revision 1 (2026-10-06).** First draft, from the main session's diagnosis of the 43 failing cases on main 201b2aa.
