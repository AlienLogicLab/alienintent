# Work unit: main passes its whole suite

**Label:** `MAIN-GREEN` (a document label; permanent id `PENDING-REGISTRATION`).
**Status:** Draft revision 1, 2026-10-06, for independent review. Not registered, not approved, not assessed, not released.
**Position on the path:** this is the second of four in maintenance-required mode (Founder 2026-10-06). It runs after
REGRESSION-GATE (`a38f0cb8`, DONE). It is the first work item judged by the whole-suite gate, through the normal
factory: PRODUCER, a fresh VERIFIER on the exact candidate, then CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "PENDING-REGISTRATION",
 "version": "revision-1",
 "intent": "Make the whole suite (tests/ and tools/) pass on main, under the worker's real conditions, by repairing the causes of the 43 test cases that fail on main 201b2aa, and of the two owned-work tests that fail when two suite runs overlap. No product behaviour changes except the one architecture correction in 2.3.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-06: make main green before the no-change repair and BOUNDED-ROUTINE-LAUNCH; repair the 39 regressions from 057fbc1 and the older failures.",
  "Founder 2026-10-06: DONE is inadmissible if the candidate causes any previously passing applicable repository test or architecture check to fail.",
  "Founder 2026-10-06: do not weaken production satisfiability or architecture rules to make tests pass. Repair the tests and fixtures so they conform to the real contracts.",
  "Founder 2026-10-06: each root cause is repaired at its source and proven independently: unsatisfiable fixture contracts (direct and through the real CLI subprocess), the domain's role vocabulary, the director test's isolation from the real home folder, and unique per-run owned-work markers instead of serializing the suite.",
  "Founder 2026-10-06: this is the first end-to-end proof of the new assurance path: a broken baseline with known debt, a bounded candidate, the whole-suite baseline-versus-candidate comparison with no new regression, then a green main.",
  "Never delete, skip or mark as expected-failure a failing test to make it pass."
 ],
 "authorized_scope": [
  "tests/context_assembly/test_work_contract.py",
  "tests/context_assembly/test_work_authorization.py",
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
  "the regression gate (invocation_runtime/application/regression_gate.py)",
  "the setting `satisfiable = None` in Fx.second (test_work_authorization.py lines 64-70), which the authorization tests use on purpose",
  "any test other than the ones named in section 1"
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
  "acceptance checks 1-8 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation",
  "the VERIFIER runs mutations M1, M2 and M3 of section 3 exactly and records that each makes its named test fail and that reverting makes it pass"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "making the suite faster"
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
  "a failing test listed in section 1 can only pass by changing a product rule outside authorized_scope",
  "the whole suite at the candidate has any failed or error test case that is not in section 1 and also fails at the starting revision",
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

Main has changed since `883e4c5` only in docs and evidence. Five causes:

1. **39 cases: fixture contracts the satisfiability check refuses.** Commit `057fbc1` turned the check off in
   `Fx.second()` (`tests/context_assembly/test_work_authorization.py` lines 64-70) but not where a registry is built
   another way:
   - `Cx.__init__` in `tests/context_assembly/test_work_context.py` (line 38) builds its own `WorkRegistry` (27 cases,
     all `assert 'AUTHORIZATION_STALE' is None` from `Cx.admitted`, line 53);
   - `tests/control_plane/test_cli.py` runs the real CLI in a subprocess (12 cases: `work_assess` `KeyError: 'disposition'`,
     `work_authorize` `TypeError`, `work_context_runs_with_only_the_worker_environment`, and the 9
     `test_the_worker_profile_answers_every_other_command_with_the_stated_er…` cases).
   The packet these fixtures assess (`contract_payload`, `tests/context_assembly/test_work_contract.py` line 18) breaks
   the satisfiability rules, so `work assess` is not READY and `work authorize` answers `AUTHORIZATION_STALE`.
2. **1 case: an old folder name.** `tests/composition/test_sandbox_run_profile.py` line 357 expects
   `launch:SB-01:0`; WORKSPACE-FOLDER-NAMES made it `launch-SB-01-0`.
3. **2 cases: a domain module imports the worker port.** `src/alienintent/context_assembly/domain/work_context.py`
   line 16 imports `CLOSURE, PRODUCER, VERIFIER` from `execution_coordination.ports.worker_provider` (since `d63c10d`).
   That breaks `test_readiness_consumer.py::test_no_new_cross_group_import_pair` (a new cross-group pair) and
   `test_ambiguity.py::AmbiguityTests::test_upstream_composition_has_no_worker_path` (`worker_provider` on the
   question/answer path).
4. **1 case: a test that reads the machine's home folder.** `tools/orchestration/test_director.py` line 62 expects
   `gpt-6-astra`, but `director.resolved_codex_model` (`director.py` line 233) reads `~/.codex/config.toml` of whoever
   runs the suite, with the path fixed at import. On this machine it reads `gpt-6-sol`; as the worker it reads another
   home.
5. **Not failing alone, failing together.** `tests/invocation_runtime/test_owned_work.py` lines 37-51 and 74-84 use
   the fixed markers `launch:AC08:0`, `:1` and `:2`, and `ProcOwnership().owned_work` scans every process on the
   machine. Two suite runs at once see each other's processes, so two gates running at once could reject a good
   candidate.

## 2. The change

1. **A satisfiable fixture contract.** `tests/context_assembly/test_work_contract.py` gains
   `satisfiable_payload(identity, **changes) -> dict`: `contract_payload` with exactly the fields the satisfiability
   rules require (both budget limits, `required_evidence` within the known kinds, `required_capabilities` within the
   known capabilities, the five fixed closure actions, `release_policy` `explicit-human-off`), and an
   `authority_references` entry the fixture commits at the pointer. `Cx` (`test_work_context.py`) and the `test_cli.py`
   fixtures assess that packet, and their fixture configuration turns landing on where the rule requires it. Nothing
   sets `satisfiable = None` outside `Fx.second`.
2. **The folder name.** `test_sandbox_run_profile.py` line 357 expects `launch-SB-01-0`.
3. **Role names owned by the domain.** `context_assembly/domain/work_context.py` defines
   `PRODUCER, VERIFIER, CLOSURE = "PRODUCER", "VERIFIER", "CLOSURE"` itself and drops the import.
   `tests/context_assembly/test_role_names.py` (new) asserts they equal `execution_coordination.ports.worker_provider`'s.
4. **No real home folder in the director test.** `resolved_codex_model` reads its default path when called, not at
   import, and `test_director.py` gives it a temporary `config.toml` holding `gpt-6-astra` (by `monkeypatch` of
   `HOME` or by passing the path). No test reads the real `~/.codex`.
5. **Unique markers.** `test_owned_work.py` builds each marker from a value unique to the test run
   (`f"launch:AC08-{uuid4().hex}:<n>"`), so a concurrent run never matches.

## 3. Acceptance checks

1. **The 39 pass under the real rules:** `python3 -m pytest -q tests/context_assembly/test_work_context.py
   tests/control_plane/test_cli.py` passes, and `grep -n "satisfiable = None"` over `tests/` finds only
   `test_work_authorization.py` lines 64-70.
2. **The fixture contract is satisfiable** (`test_work_contract.py`, test `test_the_satisfiable_fixture_passes_the_rules`):
   `unsatisfiable(...)` on `satisfiable_payload` returns no refusal.
3. **The architecture rules pass:** `tests/context_assembly/test_readiness_consumer.py::test_no_new_cross_group_import_pair`,
   `tests/context_assembly/test_ambiguity.py` and `tests/context_assembly/test_role_names.py` pass.
4. **The director test is independent of the machine:** `test_director.py` passes with `HOME` set to an empty
   temporary folder and with `HOME` set to a folder whose `config.toml` holds another model.
5. **Owned-work tests survive a concurrent run:** two runs of `python3 -m pytest -q tests/invocation_runtime/test_owned_work.py`
   started together both pass.
6. **Mutations, run exactly by the VERIFIER:**
   - M1: in `context_assembly/domain/work_context.py`, restore the import of the three names from
     `execution_coordination.ports.worker_provider`; `python3 -m pytest -q tests/context_assembly/test_readiness_consumer.py -k test_no_new_cross_group_import_pair`
     must FAIL; revert, and it must pass.
   - M3: in `test_work_context.py` `Cx.admitted`, assess `contract_payload` instead of `satisfiable_payload`;
     `python3 -m pytest -q tests/context_assembly/test_work_context.py -k test_a_first_producer_gets_exactly_its_fields_from_the_records`
     must FAIL with `AUTHORIZATION_STALE`; revert, and it must pass.
   - M2: in `test_owned_work.py`, restore the fixed marker `launch:AC08:1` in
     `test_owned_work_outliving_the_wall_clock_is_stopped_with_the_client`; with `PYTHONDONTWRITEBYTECODE=1`, running
     that test while a second run holds a process marked `launch:AC08:1` (the VERIFIER starts one with
     `env ALIENINTENT_INVOCATION_ID=launch:AC08:1 setsid sleep 60`, the variable `INVOCATION_MARKER` names in `invocation_runtime/domain/runtime.py` line 23) must
     FAIL; revert, and it must pass with the same process alive.
8. **No rule is weakened:** `git diff --name-only <starting revision> <candidate>` lists no file under `src/` other than
   `src/alienintent/context_assembly/domain/work_context.py` and `tools/orchestration/director.py`. In those two files,
   the diff removes no check: the role names keep their values (check 3), and `resolved_codex_model` keeps its
   behaviour for a real call (only when its default path is read changes). The satisfiability rules, the packet
   assessment, the work authorization and the regression gate are byte-identical to the starting revision.
7. **Main is green:** the whole suite at the candidate (the regression gate's own candidate run, as the worker) has no
   failed and no error test case. The gate reports no finding.

## 4. Review record

**Revision 1 (2026-10-06).** First draft, from the main session's diagnosis of the 43 failing cases on main 201b2aa.
