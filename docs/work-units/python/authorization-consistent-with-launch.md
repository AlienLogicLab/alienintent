# Work unit: authorization consistent with launch

**Label:** `AUTHORIZATION-CONSISTENT-WITH-LAUNCH` (a document label; the permanent id is allocated when this draft is registered).
**Status:** Draft revision 1 for independent review, 2026-10-02. Not approved, not assessed, not released.
**Position on the path:** unit 6a, the first of three units the Founder split row 6 into on 2026-10-02 (6a this unit; 6b READY selection, release gate and configurable WIP admission; 6c worker instructions and shared model routing). Builds on `work authorize` (`main` `e8d57a1`).
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## 0. The whole design (plain English)

`work authorize` records the Founder's approval as the release record the release gate reads before a PRODUCER launches. Two gaps make that record untrustworthy at launch:
1. **Competing writes.** `StoredReleaseAuthorizations.record` reads the store version itself just before writing (`execution_coordination/adapters/release_admission.py` lines 48–54), so a second, different `work authorize` that passed its own "no record yet" check overwrites the first instead of being refused.
2. **Different wording checks.** At launch the release gate checks the non-authorization wording of every human-readable text the release request carries — the readiness evidence, the row's metadata and every contract string (`execution_coordination/application/release_admission.py` `_wording`, lines 34–42). `work authorize` checks only its own quote (it passes no wording, `work_authorization.py` lines 118–119), so an authorization can be recorded that the release gate will later refuse.

This unit closes both, reusing what exists: the release record is written only if none exists, through the store's existing version check, and authorization and launch use one shared wording function.

## 1. The changes

- **Create-only release record.** `StoredReleaseAuthorizations.record` commits with expected version 0 (the store's existing check, `sqlite_store.py` `_commit`): if any release record already exists for the identity, the store raises `VersionConflict` (`execution_coordination/ports/operational_store.py`) and nothing is overwritten.
- **Authorization handles the conflict.** In `WorkAuthorization.authorize`, a `VersionConflict` from `record` is followed by one re-read: a record equal to this authorization is a repeat (the existing repeat path); any other record → `ALREADY_AUTHORIZED`, with this run's evidence left in the evidence repository unreferenced. The row's `approval_ref` is set only after this run's own record reads back, so a losing run never sets it.
- **One wording function.** A public `release_wording(contract, readiness_evidence, metadata)` in `execution_coordination/domain/release.py` yields exactly what `_wording` yields today (the readiness evidence, every metadata value, every string and string-tuple entry of the contract's canonical payload). The release gate's `_wording(item)` returns `release_wording(item.contract, item.readiness_evidence, item.metadata or {})`. `work authorize` passes `release_wording(contract, <the assessment reference's logical id>, {})` to its existing `admit_release_preconditions` check — the same contract and the same readiness evidence the READY view will put on the row (`readiness` = the `assessment_ref` logical id). Metadata on registry rows holds only system values (`wave`, `upstream_status`, `source_version`, `contract_location`, set by `_translate`), never the Founder's text; the packet records this as the one difference between the two calls.

Nothing else changes: no new store, record, flag or configuration.

## 2. Who relies on overwriting today

`record` is also called by tests and by the live proof tools `tools/live/fx_b3_release_admission_proof.py` and `tools/live/fx_b3p_release_preconditions.py`. Each call that writes a second, different record for the same identity in one store must be found: tests are updated to use a fresh identity or store; a `tools/live` script that depends on overwriting is reported as a stop condition, not changed.

## 3. Exact permitted files

Production: `src/alienintent/execution_coordination/adapters/release_admission.py` (`record` create-only), `src/alienintent/execution_coordination/domain/release.py` (`release_wording`), `src/alienintent/execution_coordination/application/release_admission.py` (`_wording` uses it), `src/alienintent/context_assembly/application/work_authorization.py` (conflict handling, wording). Tests: `tests/context_assembly/test_work_authorization.py`, `tests/execution_coordination/domain/test_policy.py` (`release_wording`), `tests/composition/test_release_admission_wiring.py`, `tests/execution_coordination/test_factory_coordinator.py`, `tests/support/release_admission.py` — the last three only where they write a second record for one identity.

## 4. Acceptance checks (each names the wrong implementation it catches)

1. **No overwrite.** With a release record present, `record` of a different authorization raises `VersionConflict` and the stored record is unchanged. Catches the read-then-commit overwrite.
2. **Competing authorizations.** Two `work authorize` runs with different baselines, interleaved so both pass the "no record yet" check before either writes: exactly one release record exists afterwards, the other run answers `ALREADY_AUTHORIZED`, and the row's `approval_ref` names the winning run's evidence. Catches the race.
3. **Same wording at authorization and launch.** A contract string or the readiness evidence containing the gate's non-authorization wording is refused by `work authorize` (`GATE_WOULD_REFUSE`), and the same contract and readiness evidence are refused by the release gate at launch; text without such wording passes both. Catches an authorization the release gate later refuses.
4. **Unchanged release gate.** `_wording` yields the same sequence as before for every existing release-gate test; repeats of `work authorize` with the same inputs still answer as repeats.
5. **Fitness.** The changed test files and `check_architecture.py --check all` pass.

## 5. Excluded

READY selection, coordinator composition and WIP admission (unit 6b); worker instructions and model routing (unit 6c); cycle counts; changing the release gate's rules or wording pattern; changing `tools/live` scripts; changing earlier packets.

## 6. Review record

**Revision 1 (2026-10-02).** First draft, against `main` `e8d57a1`, after the Founder's split of row 6.
