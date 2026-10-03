# Work unit: record completed work for an existing work item

**Label:** `RECORD-COMPLETED-WORK` (a document label; permanent id `cfd57b7e-c296-4f39-ae8c-7f134e5fa2e0`).
**Status:** Draft revision 2 (work item `cfd57b7e-c296-4f39-ae8c-7f134e5fa2e0`, at CAPTURE) for independent review, 2026-10-03. Not approved, not assessed, not released.
**Position on the path:** groundwork for truthful dependencies, ordered before unit 6c-2's real-provider check. The Founder decided on 2026-10-03: the bookkeeping gap is real; record the actual approval, accepted candidate, verification and landing evidence for an existing work item, preserving its identity, without fabricated transitions. It must reuse the existing import rules and storage. It is not a new completion framework. Builds on `main` `a5087d7`.
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## Contract

```json alienintent-contract
{
 "identity": "cfd57b7e-c296-4f39-ae8c-7f134e5fa2e0",
 "version": "revision-2",
 "intent": "Record, for an existing registered work item and preserving its identity, the actual approval, accepted candidate, verification and verified landing on the default branch, moving the row straight to DONE under the existing import rule with no fabricated transition; and let dependency admission count such a recorded completion, while conflicting records (a row at DONE while the coordinator records active work) stop admission.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-03: the bookkeeping gap is real; prepare a small record-completed-work unit preserving the existing identity and recording the actual approval, accepted candidate, verification and landing evidence, without fabricated transitions; do not bypass the dependency check or invent workflow events.",
  "Founder 2026-10-03: DONE requires verified landing evidence, not merely a verification reference.",
  "Founder 2026-10-03: conflicting records must stop dependency admission, for example a registry row at DONE while the coordinator records active work.",
  "Founder 2026-10-03: reuse the existing import rules and storage; this is necessary groundwork for truthful dependencies, not another completion framework."
 ],
 "authorized_scope": [
  "src/alienintent/context_assembly/application/work_completion.py",
  "src/alienintent/context_assembly/application/work_identity_service.py",
  "src/alienintent/context_assembly/ports/work_item_repository.py",
  "src/alienintent/context_assembly/adapters/work_item_repository.py",
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/control_plane/adapters/cli.py",
  "src/alienintent/control_plane/application/operator.py",
  "tools/live/record_completed_work_6c1.sh",
  "tests/context_assembly/test_work_completion.py",
  "tests/context_assembly/test_work_identity_service.py",
  "tests/composition/test_work_registry.py",
  "tests/execution_coordination/test_factory_coordinator.py",
  "tests/control_plane/test_cli.py"
 ],
 "excluded_scope": [
  "a new store, table, state, transition or workflow event; the only new record is the one work-completion evidence record in the existing evidence repository, built like work-authorization",
  "writing a factory coordinator record",
  "updating GitHub, the board or the card display",
  "recording any work item other than 6c-1 in this unit's real use",
  "changing work import, the release record or the release gate",
  "changing earlier packets"
 ],
 "dependencies": [],
 "required_capabilities": [
  "python",
  "git",
  "sqlite"
 ],
 "budget_policy": {
  "maximum_attempts": 3
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-6 and 3a pass",
  "architecture fitness passes"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation",
  "VERIFIER reviews the Founder-run real-use output"
 ],
 "required_evidence": [
  "VERIFIER verdict file",
  "real-use output on a registry copy",
  "landing record on main"
 ],
 "non_goals": [
  "a completion framework",
  "back-filling other hand-built work items"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by direct merge preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/worker-launch.md",
  "docs/work-units/python/work-context-package.md"
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
  "a required fact has no existing authoritative record",
  "scope outside the authorized files",
  "the real-use run fails"
 ]
}
```

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

   A row at DONE while the coordinator records active work is a conflict. A conflict stops dependency admission; `guard_account` reports it as `dependencies-incomplete`. A row at DONE with only some other verification reference does not count.

Nothing else changes: no new store, table, state, transition or workflow event; the one new evidence record is built like `work authorize`'s.

## 1. The changes

**1. The command.** `work record-completed <id> --candidate <sha> --landing <commit> --record <path> --verification <file> --approval <file> --quote "<the Founder's words>"` is added in `control_plane/adapters/cli.py` and `control_plane/application/operator.py`. It calls a new `WorkCompletion.record(...)` in `context_assembly/application/work_completion.py`. That service is shaped like `WorkAuthorization` (`work_authorization.py`). `--verification` may be given more than once. The approver is the contract's `authority_issuer`, as in `work authorize`.

**2. Checks.** They run in this fixed order, and each failure answers with its code and writes nothing. The pointer repository is the item's `pointer.repo` clone, with its configured default branch, exactly as `work authorize` resolves them. The checks use the existing `GitRevisionResolver` (`resolves`, `is_reachable`). The landing record is read with the repository adapter's existing `read_packet(StoredPointer(repo, path, landing))`, as `work context` reads authority references; no new git call is added.
1. The row exists, is not retired and has a pointer, and its packet's contract block is valid. Otherwise `NOT_RECORDABLE`, or `CONTRACT_INVALID`.
2. The registry coordinator (the `readiness` store, profile `registry`, aggregate `factory:<id>`, the record `WorkRegistry.cycles` reads) has no record for the item, or that record is at DONE. A record in any other stage is active work, so the answer is `CONFLICTING_RECORDS`, naming the stage.
3. **Verified landing.**
   - The landing commit is a full 40-character SHA (the commit that holds the landing record, at or after the merge). It resolves, and is reachable from the default branch (`is_reachable(repo, landing, <default branch>)`).
   - The candidate is a full 40-character SHA and is an ancestor of the landing commit (`is_reachable(repo, candidate, landing)`).
   - The landing record file exists at the landing commit, through `git show <landing>:<path>`, and contains both the work item's identity and the full candidate SHA.
   - The landing record also contains the full sha256 of the instructions at the row's pointer (the bytes of `git show <pointer commit>:<pointer path>`). This is how the record binds the accepted candidate to the approved instructions. The VERIFIER verdict is bound to the candidate only (step 4). Otherwise `LANDING_UNVERIFIED` (`instructions`).

   Otherwise `LANDING_UNVERIFIED`, naming the check.
4. **Verification.** At least one `--verification` file's first line is exactly `ACCEPT`, and that file contains both the full candidate SHA and the work item's identity. Otherwise `VERIFICATION_MISSING`.
5. **Approval.** The `--approval` file is a JSON object. Its top-level `item` is the work item's identity, and its top-level `commit` is the row's pointer commit, as the full 40-character SHA. Otherwise `APPROVAL_MISSING`, naming the field. `--quote` holds the Founder's words for this recording and is not empty; otherwise `APPROVAL_MISSING` (`quote`).

**3. One evidence record, then the row.** The existing evidence repository holds one fixed evidence record, kind `work-completion`. It is built the way `work authorize` builds its record, so the same inputs give the same reference. It holds:
- the identity;
- the pointer;
- the contract digest;
- the candidate SHA;
- the landing commit, the default branch, and the landing record path and its bytes;
- each verification file's resolved absolute path and bytes;
- the approval file's resolved absolute path and bytes;
- the approver and the quote.

The contract digest is the digest of the contract block at the row's pointer, read in step 1. No other digest is read or compared: the row and the approval file hold none.

**Order of writes.** Every check in section 2 only reads. Then the reference is computed from the evidence record (`record_ref`, as `work authorize` does), and the row is read. A row at DONE whose `verification_ref` equals that reference is a repeat. A row at DONE with any other reference, or none, answers `COMPLETION_CONFLICT`. Both write nothing. Otherwise: (1) the evidence record is written and read back. It is fixed and content-addressed, so the same inputs give the same reference. (2) The row, in one write transaction, by a new repository method `record_completed(identity, pointer_commit, ref)` beside `import_completed` (`work_item_repository.py` lines 241-243). It reads the row again. A retired row is `NOT_RECORDABLE`. A row at DONE whose `verification_ref` equals `ref` is a repeat and writes nothing. A row at DONE with any other reference, or none, answers `COMPLETION_CONFLICT`. Otherwise it sets `state = DONE` and `verification_ref = ref` with `WHERE id = ? AND state = <the state read> AND "commit" = <pointer_commit> AND retired_at IS NULL`, and reads the row back. If that update changes no row (the pointer moved, or the row was retired, after the checks), it answers `NOT_RECORDABLE` (`pointer changed` or `retired`) and nothing changes. This update is the commit point. It uses no transition and invents no step, and it never touches `approval_ref`, which stays the release record's evidence.

**Interrupted write.** If the run stops after (1) and before (2), the row is unchanged. Repeating the same request writes the same evidence record again (no change) and then finishes (2). A request with different inputs, once the row is DONE, answers `COMPLETION_CONFLICT`. Before the row is DONE, nothing is recorded as complete, so a different valid request records that one; the earlier evidence object stays unreferenced, as in `work authorize`.

**4. Dependency admission** (`execution_coordination/application/factory_coordinator.py`). The coordinator takes an optional, injected `recorded_completion(identity) -> bool`. The registry composition (`WorkRegistry.coordinator`, `composition/work_registry.py` line 335) binds it. It answers true only when the row is not retired, is at DONE, and its `verification_ref` reads back from the evidence repository as a `work-completion` record whose `identity` is this row's id. Only the two dependency checks use it (lines 151 and 276), through one private `_dependency_done(identity)`. If the coordinator has a record for the dependency, that record's stage decides, as today: DONE counts, and any other stage does not, whatever the row says. If the coordinator has no record, the reader decides. So a row at DONE while the coordinator records active work never counts. `guard_account` names it `dependencies-incomplete`, as today. `_is_done` for an item's own state (line 588) is unchanged. Without the injected reader, behaviour is unchanged.

## 2. Exact permitted files

Production:
- `src/alienintent/context_assembly/application/work_completion.py` (new)
- `src/alienintent/context_assembly/application/work_identity_service.py` (`record_completed`)
- `src/alienintent/context_assembly/ports/work_item_repository.py` and `src/alienintent/context_assembly/adapters/work_item_repository.py` (`record_completed`)
- `src/alienintent/execution_coordination/application/factory_coordinator.py` (`_dependency_done` with the injected reader)
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
   - an approval file whose `item` is another identity, or whose `commit` is not the row's pointer commit (for example the superseded revision's commit), or an empty quote;
   - a landing record without the sha256 of the instructions at the row's pointer;
   - an abbreviated landing commit, or a branch name given as the landing commit.

   Catches DONE on a bare reference.
3. **Conflicts stop it.** A coordinator record in an active stage gives `CONFLICTING_RECORDS`. A row already DONE with other evidence gives `COMPLETION_CONFLICT`. The same request twice is a repeat that writes nothing. Catches an overwrite and a record that contradicts active work.
3a. **Interrupted write.** Make the row write fail once, after the evidence record is written. The row is still at its earlier state with no `verification_ref`. Repeat the same request: the row is now DONE with the same reference, and the evidence folder holds one object for it. Then repeat with a different verification file: `COMPLETION_CONFLICT`, and nothing changes. Also move the row's pointer between the checks and the write: the update writes nothing and the answer is `NOT_RECORDABLE` (`pointer changed`). Catches a missing commit point, a non-repeatable record, and DONE under unchecked instructions.
4. **Dependency admission is truthful.** A dependent work item is eligible when its dependency is recorded complete and has no coordinator record. It is not eligible in any of these cases:
   - the dependency row is at DONE with only some other verification reference, such as an imported row;
   - the dependency row is at DONE while the coordinator records active work (`guard_account` answers `dependencies-incomplete`);
   - the dependency row is DONE from `work import` with a `--verification` reference shaped like a `work-completion` reference, but its evidence record is missing or names another identity;
   - the dependency row is recorded complete but retired;
   - the dependency is at CAPTURE.

   A coordinator record at DONE still counts, as today. Catches a bypassed dependency check, a bare DONE accepted, and a conflict ignored.
5. **Real use (Founder-run, before acceptance), on a copy of the permanent registry.** The PRODUCER prepares `tools/live/record_completed_work_6c1.sh`. It records 6c-1 (work item `5befff2f-a0dd-4cea-9556-54c33ed86c1b`) from its actual evidence:
   - candidate `c36688492487c41aa41aebd4778d54aec7ceeece`;
   - landing commit `a5087d71439792a7e1efd96711cdfa85803049ac` (it holds the record `docs/evidence/work-context-package-landing-c366884.md`; the merge is `81cd23c`);
   - the round 1 and round 2 VERIFIER verdict files (the round 2 verdict is the `ACCEPT` naming the candidate);
   - the approval file `registry/approvals/5befff2f-a0dd-4cea-9556-54c33ed86c1b.json`.

   The script copies `work.sqlite`, `readiness.sqlite` (with `sqlite3 .backup`) and `readiness-evidence/` into a temporary folder. It writes a `projects.json` copy that points `database`, `readiness.database` and `readiness.evidence_root` at the copies, and keeps the repository clone in place, read only. It runs the candidate's code (`PYTHONPATH=<candidate worktree>/src`). It prints `work show` before and after, the evidence reference, and the repeat's answer. It never opens the permanent databases for writing. It shows the row at DONE with the same id. It also shows that a repeat writes nothing. The Founder runs it with a quote. The VERIFIER reviews its output. Recording 6c-1 in the permanent registry happens only after this unit lands, as a separate Founder-run step, before 6c-2's real-provider check.
6. **Fitness.** The changed test files pass when run together in one run (no full suite), and `tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

## 4. Excluded

- a new store, table, state, transition or workflow event; the only new record is the one `work-completion` evidence record in the existing evidence repository, built like `work-authorization`;
- writing a `factory:` coordinator record;
- updating GitHub, the board or the card display;
- recording any work item other than 6c-1 in this unit's real use (other hand-built units can use the same command later, each with its own evidence);
- changing `work import`, the release record or the release gate;
- changing earlier packets.

## 5. Review record

**Revision 2 (2026-10-03).** The REVIEWER's review of `a5ddbbe` (FAIL, text only), with the Founder's two added points. Fixes applied in its wording:
- H1: the approval is bound to the exact instructions. Its `item` and `commit` equal the row's identity and pointer commit, and the landing record holds the sha256 of the instructions at the pointer. The verdict binds the candidate only, because 6c-1's verdict names no packet commit.
- H2: the order of writes, the commit point guarded by the checked pointer, and the interrupted write finished by the same request (check 3a). Plain limit: before the row is DONE, a different valid request is not refused; its earlier evidence object stays unreferenced, as in `work authorize`.
- H3: full 40-character landing and candidate SHAs.
- M1: the one new evidence record is named, not excluded.
- M2: a true-or-false reader on the two dependency checks only; no `dependency_status`.
- M3: the registry coordinator record and the existing `read_packet` are named.
- M4: the real-use script runs the candidate's code on a full registry copy.
- L1-L2: the verdict names the identity; resolved absolute paths.
- REVIEWER recheck of `046724a` (FAIL, text): F1 the reference is computed and the row read before any write, so a repeat or a conflict writes nothing (checks repeated inside the row transaction for the race); F2 the conflict is reported as `dependencies-incomplete`.

**Revision 1 (2026-10-03).** First draft, against `main` `a5087d7`, with the Founder's decisions:
- prepare a small "record completed work" unit that preserves the existing identity and records the actual approval, accepted candidate, verification and landing evidence, without fabricated transitions;
- DONE requires verified landing evidence, not merely a verification reference;
- conflicting records stop dependency admission;
- reuse the existing import rules and storage; this is not another completion framework.
