# Work unit: authorization consistent with launch

**Label:** `AUTHORIZATION-CONSISTENT-WITH-LAUNCH` (a document label; the permanent id is allocated when this draft is registered).
**Status:** Draft revision 2 (item `2232453f-9855-46cd-b155-34c11d88e43c`, at CAPTURE) for independent review, 2026-10-02. Not approved, not assessed, not released.
**Position on the path:** unit 6a, the first of three units the Founder split row 6 into on 2026-10-02 (6a this unit; 6b READY selection, release gate and configurable WIP admission; 6c worker instructions and shared model routing). Builds on `work authorize` (`main` `e8d57a1`).
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## Contract

```json alienintent-contract
{
 "identity": "2232453f-9855-46cd-b155-34c11d88e43c",
 "version": "revision-2",
 "intent": "Make the release record trustworthy at launch: the release record is written only if none exists, using the operational store's existing version check, so competing or conflicting work authorize runs are refused instead of overwriting; and work authorize and the release gate check the same contract and readiness-evidence wording through one shared function.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-02: the concurrent release-record overwrite is a prerequisite to trusting the record for worker launch; fix it with the store's existing version check or by refusing conflicting authorization.",
  "Founder 2026-10-02: apply the same contract-wording checks during authorization and launch.",
  "Reuse existing components; no new store, record, flag or configuration."
 ],
 "authorized_scope": [
  "src/alienintent/execution_coordination/adapters/release_admission.py",
  "src/alienintent/execution_coordination/domain/release.py",
  "src/alienintent/execution_coordination/application/release_admission.py",
  "src/alienintent/context_assembly/application/work_authorization.py",
  "tests/context_assembly/test_work_authorization.py",
  "tests/execution_coordination/domain/test_policy.py",
  "tests/composition/test_release_admission_wiring.py",
  "tests/execution_coordination/test_factory_coordinator.py",
  "tests/support/release_admission.py"
 ],
 "excluded_scope": [
  "READY selection, coordinator composition and WIP admission",
  "worker instructions and model routing",
  "cycle counts",
  "changing the release gate's rules or wording pattern",
  "changing tools/live scripts",
  "changing earlier packets"
 ],
 "dependencies": [],
 "required_capabilities": [
  "python",
  "sqlite"
 ],
 "budget_policy": {
  "maximum_attempts": 3
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-6 pass",
  "architecture fitness passes"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation"
 ],
 "required_evidence": [
  "VERIFIER verdict file",
  "landing record on main"
 ],
 "non_goals": [
  "revoking or superseding an authorization",
  "registry coordinator composition"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by direct merge preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/python-execution-path-20260930.md row 6 (Founder split 2026-10-02, unit 6a)"
 ],
 "target_repositories": [
  "AlienLogicLab/alienintent"
 ],
 "baselines": [
  "main"
 ],
 "required_closure_actions": [
  "direct merge to main",
  "landing record in docs/evidence",
  "remove temporary PRODUCER and VERIFIER worktrees"
 ],
 "stop_escalation_conditions": [
  "a landed interface does not match the packet",
  "a tools/live script depends on overwriting a release record",
  "scope outside the authorized files"
 ]
}
```

## 0. The whole design (plain English)

`work authorize` records the Founder's approval as the release record the release gate reads before a PRODUCER launches. Two gaps make that record untrustworthy at launch:
1. **Competing writes.** `StoredReleaseAuthorizations.record` reads the store version itself just before writing (`execution_coordination/adapters/release_admission.py` lines 48–54), so a second, different `work authorize` that passed its own "no record yet" check overwrites the first instead of being refused.
2. **Different wording checks.** At launch the release gate checks the non-authorization wording of every human-readable text the release request carries — the readiness evidence, the row's metadata and every contract string (`execution_coordination/application/release_admission.py` `_wording`, lines 34–42). `work authorize` checks only its own quote (it passes no wording, `work_authorization.py` lines 118–119), so an authorization can be recorded that the release gate will later refuse.

This unit closes both, reusing what exists: the release record is written only if none exists, through the store's existing version check, and authorization and launch use one shared wording function.

## 1. The changes

- **Create-only release record.** `StoredReleaseAuthorizations.record` commits with expected version 0 (the store's existing check, `sqlite_store.py` `_commit`): if any release record already exists for the identity, the store raises `VersionConflict` (`execution_coordination/ports/operational_store.py`) and nothing is overwritten.
- **Authorization handles the conflict.** In `WorkAuthorization.authorize`, a `VersionConflict` from `record` is followed by one re-read: a record equal to this authorization is a repeat (the existing repeat path); any other record → `ALREADY_AUTHORIZED`, with this run's evidence left in the evidence repository unreferenced. `approval_ref` is set, as today (`work_authorization.py` lines 131-132), only when the stored release record equals this run's authorization. That is true after this run's own write reads back, or on a repeat, including a repeat found after a VersionConflict. A run whose authorization differs from the stored record never sets it. The loser's answer has the same shape as today's `ALREADY_AUTHORIZED` (`authorization=asdict(stored)`). Update the comment at `work_authorization.py` line 33: `ALREADY_AUTHORIZED` after a lost VersionConflict leaves this run's evidence object unreferenced; every other refusal writes nothing.
- **One wording function.** A public `release_wording(contract, readiness_evidence, metadata)` in `execution_coordination/domain/release.py` yields exactly what `_wording` yields today (the readiness evidence, every metadata value, every string and string-tuple entry of the contract's canonical payload). The release gate's `_wording(item)` returns `release_wording(item.contract, item.readiness_evidence, item.metadata or {})`. `work authorize` passes `release_wording(contract, item.assessment_ref.logical_id, {})` to its existing `admit_release_preconditions` check — the same contract and the same readiness evidence the READY view will put on the row (`readiness` = the `assessment_ref` logical id). Metadata on registry rows holds only system values (`wave`, `upstream_status`, `source_version`, `contract_location`, set by `_translate`), never the Founder's text; the packet records this as the one difference between the two calls.

Nothing else changes: no new store, record, flag or configuration.

## 2. Who relies on overwriting today

`record` is also called by tests and by the live proof tools `tools/live/fx_b3_release_admission_proof.py` and `tools/live/fx_b3p_release_preconditions.py`. Each call that writes a second, different record for the same identity in one store must be found: tests are updated to use a fresh identity or store; a `tools/live` script that depends on overwriting is reported as a stop condition, not changed. Checked at `e8d57a1`: no test or `tools/live` caller overwrites, so the three test files listed only for that reason are expected unchanged; touching them needs a stated reason.

## 3. Exact permitted files

Production: `src/alienintent/execution_coordination/adapters/release_admission.py` (`record` create-only), `src/alienintent/execution_coordination/domain/release.py` (`release_wording`), `src/alienintent/execution_coordination/application/release_admission.py` (`_wording` uses it), `src/alienintent/context_assembly/application/work_authorization.py` (conflict handling, wording). Tests: `tests/context_assembly/test_work_authorization.py`, `tests/execution_coordination/domain/test_policy.py` (`release_wording`), `tests/composition/test_release_admission_wiring.py`, `tests/execution_coordination/test_factory_coordinator.py`, `tests/support/release_admission.py` — the last three only where they write a second record for one identity.

## 4. Acceptance checks (each names the wrong implementation it catches)

1. **No overwrite.** With a release record present, `record` of a different authorization raises `VersionConflict` and the stored record is unchanged. Catches the read-then-commit overwrite.
2. **Competing authorizations.** Two `work authorize` runs with different baselines, interleaved so both pass the "no record yet" check before either writes: exactly one release record exists afterwards, the other run answers `ALREADY_AUTHORIZED`, and the row's `approval_ref` names the winning run's evidence. Catches the race.
3. **Same wording at authorization and launch.** End to end: a contract string containing the gate's non-authorization wording is refused by `work authorize` (`GATE_WOULD_REFUSE`), and the same contract is refused by the release gate at launch; a contract without such wording passes both. The readiness-evidence and metadata branches are covered by a `release_wording` unit test in `tests/execution_coordination/domain/test_policy.py` (the readiness evidence is always the system value `readiness/<uuid>/<attempt>/raw`). Catches an authorization the release gate later refuses.
4. **Unchanged release gate.** `_wording` yields the same sequence as before for every existing release-gate test; repeats of `work authorize` with the same inputs still answer as repeats.
5. **Fitness.** The changed test files and `check_architecture.py --check all` pass.
6. **Crash, then compete, then retry.** The winning `work authorize` writes its release record, then fails before setting `approval_ref`. A competing run with a different baseline then answers `ALREADY_AUTHORIZED`: the release record is unchanged and `approval_ref` is still unset. A competing run that loses at `record` (VersionConflict) gives the same result. The winner's retry with the same inputs answers as a repeat and sets `approval_ref` to the winner's evidence. The existing crash-repair test stays unchanged. Catches: a competitor that overwrites the record or sets its own `approval_ref`, and a design that sets `approval_ref` only on a fresh write.

## 5. Excluded

READY selection, coordinator composition and WIP admission (unit 6b); worker instructions and model routing (unit 6c); cycle counts; changing the release gate's rules or wording pattern; changing `tools/live` scripts; changing earlier packets.

## 6. Review record

**Revision 2 (2026-10-02).** The REVIEWER's review of `c16a789` (FAIL, text only): the Founder's crash–compete–retry case is acceptance check 6; when `approval_ref` is set is stated as today's rule; the loser's evidence and answer shape are stated; check 3 tests the contract end to end and the other wording branches with a unit test; no overwrite caller exists.

**Revision 1 (2026-10-02).** First draft, against `main` `e8d57a1`, after the Founder's split of row 6.
