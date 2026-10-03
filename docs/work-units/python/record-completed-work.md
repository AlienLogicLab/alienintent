# Work unit: record completed work for an existing work item

**Label:** `RECORD-COMPLETED-WORK` (a document label; the permanent id is allocated when this draft is registered).
**Status:** Draft revision 1 for independent review, 2026-10-03. Not approved, not assessed, not released.
**Position on the path:** groundwork for truthful dependencies, ordered before unit 6c-2's real-provider check. The Founder decided on 2026-10-03: the bookkeeping gap is real; record the actual approval, accepted candidate, verification and landing evidence for an existing work item, preserving its identity, without fabricated transitions. It must reuse the existing import rules and storage. It is not a new completion framework. Builds on `main` `a5087d7`.
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## 0. The whole design (plain English)

Work items built by the manual workflow are landed on `main`, but their records never say so:
- their work registry row stays at CAPTURE;
- the coordinator has no `factory:<id>` record for them.

The coordinator counts a dependency as complete only when its `factory:<id>` record is at DONE (`factory_coordinator.py` lines 276 and 578-582). So no work item that depends on hand-built work can ever be launched. Unit 6c-2 depends on 6c-1 in exactly this way.

Nothing that exists today can close this truthfully:
- the row moves only one step at a time through the fixed state table, so walking it to DONE would invent SPECIFY, PLAN, TASKS and the rest;
- `work import` records finished work at DONE with exact evidence and no invented steps, but only as a new row from a GitHub Issue, which would give the work a second identity;
- a `factory:` record can only be built by the coordinator's own lifecycle.

This unit adds the smallest truthful path, reusing the existing import rule and storage:
1. **`work record-completed <id>`.** It records, for an existing work item, the Founder's approval, the accepted candidate, the VERIFIER's verification and the landing on the default branch. Only after checking each of these against Git and the given files does it move the row straight to DONE. That is the same "historical record, no invented step" rule `work import` already follows (`work_identity_service.py` lines 50-63), applied to a row that already exists. The identity is preserved, and no other row is created.
2. **Dependency admission reads it, and stops on a conflict.** A dependency counts as complete when either:
   - its coordinator record is at DONE; or
   - it has no coordinator record, and its row is at DONE with a completion record from step 1.

   A row at DONE while the coordinator records active work is a conflict. A conflict stops dependency admission and is named. A row at DONE with only some other verification reference does not count.

Nothing else changes: no new store, table, record kind, transition or workflow event.

## 1. The changes

**1. The command.** `work record-completed <id> --candidate <sha> --landing <commit> --record <path> --verification <file> --approval <file> --quote "<the Founder's words>"` is added in `control_plane/adapters/cli.py` and `control_plane/application/operator.py`. It calls a new `WorkCompletion.record(...)` in `context_assembly/application/work_completion.py`. That service is shaped like `WorkAuthorization` (`work_authorization.py`). `--verification` may be given more than once. The approver is the contract's `authority_issuer`, as in `work authorize`.

**2. Checks.** They run in this fixed order, and each failure answers with its code and writes nothing. The pointer repository is the item's `pointer.repo` clone, with its configured default branch, exactly as `work authorize` resolves them. The checks use the existing `GitRevisionResolver` (`resolves`, `is_reachable`).
1. The row exists, is not retired and has a pointer, and its packet's contract block is valid. Otherwise `NOT_RECORDABLE`, or `CONTRACT_INVALID`.
2. The coordinator has no record for the item, or that record is at DONE. A record in any other stage is active work, so the answer is `CONFLICTING_RECORDS`, naming the stage.
3. **Verified landing.**
   - The landing commit (the commit that holds the landing record, at or after the merge) resolves and is reachable from the default branch.
   - The candidate is a full 40-character SHA and is an ancestor of the landing commit.
   - The landing record file exists at the landing commit, through `git show <landing>:<path>`, and contains both the work item's identity and the full candidate SHA.

   Otherwise `LANDING_UNVERIFIED`, naming the check.
4. **Verification.** At least one `--verification` file's first line is `ACCEPT`, and that file contains the full candidate SHA. Otherwise `VERIFICATION_MISSING`.
5. **Approval.** The `--approval` file contains the work item's identity, and `--quote` is not empty. Otherwise `APPROVAL_MISSING`.

**3. One evidence record, then the row.** The existing evidence repository holds one fixed evidence record, kind `work-completion`. It is built the way `work authorize` builds its record, so the same inputs give the same reference. It holds:
- the identity;
- the pointer;
- the contract digest;
- the candidate SHA;
- the landing commit, the default branch, and the landing record path and its bytes;
- each verification file's name and bytes;
- the approval file's bytes;
- the approver and the quote.

Then, in one write transaction, the row moves straight to DONE with `verification_ref` set to that record. This is a new repository method, `record_completed(identity, ref)`, beside `import_completed` (`work_item_repository.py` lines 241-243). It uses the same storage and the same rule: no transition and no invented step. It refuses a retired row. It never touches `approval_ref`, which stays the release record's evidence.

Repeats and conflicts:
- a row already at DONE whose `verification_ref` equals this record is a repeat, and writes nothing;
- a row at DONE with any other reference answers `COMPLETION_CONFLICT`, and nothing changes.

**4. Dependency admission** (`execution_coordination/application/factory_coordinator.py`). `_is_done(dependency)` also asks an optional, injected `recorded_completion(identity)`. The registry composition (`composition/work_registry.py`) binds it to the work registry row and its evidence. It answers one of three values:
- `complete`: the row is at DONE and its `verification_ref` is a `work-completion` record;
- `absent`;
- `conflict`: the row is at DONE, but the coordinator record for that item exists and is not at DONE.

The dependency is complete when the coordinator record is at DONE, or when there is no coordinator record and the answer is `complete`. A `conflict` is never complete. The coordinator names it through a new read, `dependency_status(identity)`, so a refused admission can say why; unit 6c-2's `not-eligible` answer will carry it. Without the injected reader, behaviour is unchanged.

## 2. Exact permitted files

Production:
- `src/alienintent/context_assembly/application/work_completion.py` (new)
- `src/alienintent/context_assembly/application/work_identity_service.py` (`record_completed`)
- `src/alienintent/context_assembly/ports/work_item_repository.py` and `src/alienintent/context_assembly/adapters/work_item_repository.py` (`record_completed`)
- `src/alienintent/execution_coordination/application/factory_coordinator.py` (`_is_done`, `dependency_status`)
- `src/alienintent/composition/work_registry.py` (wiring)
- `src/alienintent/control_plane/adapters/cli.py` and `src/alienintent/control_plane/application/operator.py` (`work record-completed`)
- `tools/live/record_completed_work_6c1.sh` (new, the real-use script)

Tests:
- `tests/context_assembly/test_work_completion.py` (new)
- `tests/context_assembly/test_work_identity_service.py`
- `tests/composition/test_work_registry.py`
- `tests/execution_coordination/test_factory_coordinator.py`
- `tests/control_plane/test_cli.py`

## 3. Acceptance checks (each names the wrong implementation it catches)

1. **Truthful record, same identity.** In a temporary registry and repository with 6c-1-shaped evidence, `work record-completed` moves the existing row from CAPTURE straight to DONE. The id, label and pointer are unchanged, and no other row is created. `verification_ref` names the `work-completion` record, which holds the approval, accepted candidate, verification and landing exactly as given. No intermediate state was ever recorded. Catches a new row, a walked-through transition, and lost or altered evidence.
2. **DONE requires verified landing evidence.** Each of these is refused with nothing written:
   - a landing commit not on the default branch;
   - a candidate that is not an ancestor of the landing commit;
   - an abbreviated candidate SHA;
   - a landing record that is missing, or that does not name the identity and the full candidate;
   - no `ACCEPT` verification naming the candidate;
   - an approval file without the identity, or an empty quote.

   Catches DONE on a bare reference.
3. **Conflicts stop it.** A coordinator record in an active stage gives `CONFLICTING_RECORDS`. A row already DONE with other evidence gives `COMPLETION_CONFLICT`. The same request twice is a repeat that writes nothing. Catches an overwrite and a record that contradicts active work.
4. **Dependency admission is truthful.** A dependent work item is eligible when its dependency is recorded complete and has no coordinator record. It is not eligible in any of these cases:
   - the dependency row is at DONE with only some other verification reference, such as an imported row;
   - the dependency row is at DONE while the coordinator records active work (`dependency_status` names the conflict);
   - the dependency is at CAPTURE.

   A coordinator record at DONE still counts, as today. Catches a bypassed dependency check, a bare DONE accepted, and a conflict ignored.
5. **Real use (Founder-run, before acceptance), on a copy of the permanent registry.** The PRODUCER prepares `tools/live/record_completed_work_6c1.sh`. It records 6c-1 (work item `5befff2f-a0dd-4cea-9556-54c33ed86c1b`) from its actual evidence:
   - candidate `c36688492487c41aa41aebd4778d54aec7ceeece`;
   - landing commit `a5087d7` (it holds the record `docs/evidence/work-context-package-landing-c366884.md`; the merge is `81cd23c`);
   - the round 1 and round 2 VERIFIER verdict files (the round 2 verdict is the `ACCEPT` naming the candidate);
   - the approval file `registry/approvals/5befff2f-a0dd-4cea-9556-54c33ed86c1b.json`.

   The script works on a copy of the registry and shows the row at DONE with the same id. It also shows that a repeat writes nothing. The Founder runs it with a quote. The VERIFIER reviews its output. Recording 6c-1 in the permanent registry happens only after this unit lands, as a separate Founder-run step, before 6c-2's real-provider check.
6. **Fitness.** The changed test files pass when run together in one run (no full suite), and `tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

## 4. Excluded

- a new store, table, record kind, state, transition or workflow event;
- writing a `factory:` coordinator record;
- updating GitHub, the board or the card display;
- recording any work item other than 6c-1 in this unit's real use (other hand-built units can use the same command later, each with its own evidence);
- changing `work import`, the release record or the release gate;
- changing earlier packets.

## 5. Review record

**Revision 1 (2026-10-03).** First draft, against `main` `a5087d7`, with the Founder's decisions:
- prepare a small "record completed work" unit that preserves the existing identity and records the actual approval, accepted candidate, verification and landing evidence, without fabricated transitions;
- DONE requires verified landing evidence, not merely a verification reference;
- conflicting records stop dependency admission;
- reuse the existing import rules and storage; this is not another completion framework.
