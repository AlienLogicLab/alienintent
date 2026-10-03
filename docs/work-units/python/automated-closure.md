# Work unit: automated closure and cleanup for registry work

**Label:** `AUTOMATED-CLOSURE` (a document label; permanent id `0677f8bb-71c2-4c62-8b4a-d0e5318ba689`).
**Status:** Draft revision 3 (work item `0677f8bb-71c2-4c62-8b4a-d0e5318ba689`, at CAPTURE) for independent review, 2026-10-04. Not approved, not assessed, not released.
**Position on the path:** path row 8, the second of the three connections still missing from the critical path. Row 7 (restart continuation) is landed at `main` `789240c`. Automatic selection and launch of the next eligible item follows.
This packet is built by the manual workflow, not by `work launch`, so its budget carries no launch limits.
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it (by hand, because this unit is the one that automates closure).

## Contract

```json alienintent-contract
{
 "identity": "0677f8bb-71c2-4c62-8b4a-d0e5318ba689",
 "version": "revision-3",
 "intent": "Make closure a launched step for registry work: fixed closure action names with exact receipts tied to the work item and accepted candidate, a fresh CLOSURE session on the VERIFIER's configured provider and model that alone receives landing credentials, control-plane read-back before every receipt, one completion path (the coordinator's close transition, with the registry row moved to DONE after it through the existing record_completed), and a verified ready-to-land result when no landing identity is configured.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-04: a fixed set of closure action names; each needs an exact receipt tied to the work item and accepted candidate.",
  "Founder 2026-10-04: work display updates text and does not necessarily move the card to DONE; closure must confirm both.",
  "Founder 2026-10-04: reuse record-completed's evidence checks but do not introduce a second completion path; the coordinator records closure.",
  "Founder 2026-10-04: CLOSURE uses the VERIFIER's configured provider and model in a fresh, separate session dedicated to closure (the B-DISP arrangement); only that session receives landing credentials; no new provider.",
  "Founder 2026-10-04: the factory App is the proposed CLOSURE identity; its permission change needs the Founder's explicit authorization; PRODUCER and VERIFIER must not be able to access its private key or obtain its write token.",
  "Founder 2026-10-04: protected-main landing and credential separation are explicit prerequisites to the real-use proof, not reasons to replace automated closure with a permanent manual push; until then a verified ready-to-land result is not completed automated closure."
 ],
 "authorized_scope": [
  "src/alienintent/execution_coordination/domain/closure.py",
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/context_assembly/application/work_context.py",
  "src/alienintent/context_assembly/domain/work_context.py",
  "src/alienintent/context_assembly/application/work_completion.py",
  "src/alienintent/composition/role_binding.py",
  "tests/execution_coordination/test_factory_coordinator.py",
  "tests/composition/test_worker_launch.py",
  "tests/invocation_runtime/test_runtime.py",
  "tests/context_assembly/test_work_context.py",
  "tests/context_assembly/test_work_completion.py"
 ],
 "excluded_scope": [
  "operating-system credential separation",
  "the App permission change",
  "automatic next-item selection",
  "re-landing work already landed by hand",
  "a new provider, store, record kind or configuration source beyond the landing identity entry",
  "changing earlier packets"
 ],
 "dependencies": [
  "bb39a588-bf9a-4d30-b573-b8245b8979a0"
 ],
 "required_capabilities": [
  "python",
  "git",
  "sqlite",
  "process-control"
 ],
 "budget_policy": {
  "maximum_attempts": 3
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-8 pass",
  "architecture fitness passes",
  "acceptance check 9 recorded as ready-to-land until the section 1 prerequisites are met"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation"
 ],
 "required_evidence": [
  "VERIFIER verdict file whose first line is exactly ACCEPT or REJECT",
  "landing record on main"
 ],
 "non_goals": [
  "next-item selection",
  "operating-system containment"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by direct merge preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/worker-launch.md",
  "docs/work-units/python/restart-continuation.md"
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
  "scope outside the authorized files"
 ]
}
```

## 0. The whole design (plain English)

Today a work item that the VERIFIER accepts stops at ACCEPT. `work launch` answers `closure-not-automated`, and a person lands the work. The existing CLOSURE role (`RealWorkerProvider._close`) can attest only `candidate-published`. The coordinator moves a work item to DONE only when every action in the contract's `required_closure_actions` has a receipt (`lifecycle.transition`, action `close`). Packets name those actions in free text, so no receipt can match them.

This unit makes closure a normal launched step:
1. **Fixed closure action names.** There are five: `candidate-published`, `merged-to-main`, `landing-record`, `board-updated` and `workspaces-cleaned`. Each receipt is exact and names the action, the work item and the accepted candidate, as `<action>:<work item id>:<candidate revision>`. A new packet lists these names in `required_closure_actions`. Free-text actions in earlier packets match no receipt, so those work items stay at ACCEPT, as today.
2. **CLOSURE is a fresh, separate session.** This is the B-DISP arrangement. `work launch` at ACCEPT starts the CLOSURE role on the VERIFIER's configured provider and model (the VERIFIER route in `model-routing.json`), in a new session with its own fresh clone. No new provider is added. The session gets the instruction text, its context package and, only when they are configured, the landing credentials. The control plane never gives landing credentials to PRODUCER or VERIFIER sessions. Until the section 1 separation exists, they can still read the key from disk.
3. **The CLOSURE session performs; the control plane reads back.** The session merges the exact accepted candidate into the default branch with `--no-ff`, writes the landing record and pushes. The control plane, never the session, issues each receipt after its own read-back:
   - `candidate-published`: today's check;
   - `merged-to-main`: the remote default branch contains a merge whose second parent is the candidate, and its source tree equals the candidate's;
   - `landing-record`: at that pushed commit, the landing record exists, and it names the work item, the full candidate revision and the sha256 of the instructions at the work item's pointer (the same checks `work record-completed` applies);
   - `board-updated`: after the existing `work display`, the card's display text reads back current, and `read_status` reads back DONE after `write_status(DONE)`. Both are required;
   - `workspaces-cleaned`: this work item's retained PRODUCER worktrees, VERIFIER clones, PRODUCER read-back folders and CLOSURE clones are removed under the existing ownership checks. Anything kept is named in `cleanup_diagnostics` with its reason, and then no receipt is issued.
4. **One completion path.** The coordinator's existing `close` transition, ACCEPT to DONE, is the only way a work item completes. After the coordinator's DONE reads back, the work registry row moves to DONE through the existing `record_completed`. Its reference is the landing record at the pushed merge commit, an existing reference kind. `record_completed` is idempotent for the same reference, so `work launch` recovery repeats it for a work item whose coordinator record is DONE and whose row is not. `work record-completed` refuses any work item that has a coordinator record, so it is never a second path for coordinator-closed work.
5. **"Ready to land" without credentials.** When no landing identity is configured, the CLOSURE session still merges and writes the landing record in its clone, but it cannot push. The control plane issues the receipts it can read back. The work item stays at ACCEPT, because `merged-to-main` is missing, and the answer is `ready-to-land`, naming the prepared merge commit. This is a verified intermediate state. It is not completed closure.

## 1. Prerequisites for the real-use proof (not for building or testing)

The offline tests below prove the whole unit. The real landing on the protected `main` needs two things first, and the unit's real-use check waits for them:
- **The Founder's explicit authorization of the CLOSURE identity's permission change.** The factory GitHub App (4990774, installation 162769625) needs write access to repository contents and a bypass of `main`'s branch protection for the App alone.
- **Established credential separation.** PRODUCER and VERIFIER sessions can neither read the App's private key nor obtain its write token. Today they cannot be prevented: workers run as the Founder's Unix user, which can read the registry's `projects.json` and the key it names. Separation needs the key held by a different Unix user, or PRODUCER and VERIFIER sessions run as a separate Unix user. That is separate work, to be decided by the Founder.

Neither prerequisite is a reason to replace automated closure with a permanent manual push.

## 2. The changes

1. **Closure action names** (`execution_coordination/domain/closure.py`, new). The five names, and the receipt format, with one function to build and one to parse.
2. **CLOSURE at ACCEPT** (`execution_coordination/application/factory_coordinator.py`).
   - `launch(identity)` at ACCEPT runs the CLOSURE role through the existing `_run`, instead of answering `closure-not-automated`.
   - `_advance` for `closed` parses each receipt with the parse function in `closure.py`. It keeps only receipts that name this work item and the full revision of the custodied candidate, and passes their action names to the existing `close` transition. DONE only when `required_closure_actions` ⊆ those action names. `lifecycle.py` is unchanged.
   - A `closed` outcome for the custodied candidate, whose contract's `required_closure_actions` are exactly the five fixed names, and with a receipt for every one except `merged-to-main`, is recorded with outcome `ready-to-land`, not `authority-block`. The work item stays at ACCEPT, no escalation is registered, no dependent is blocked and the WIP slot is kept. `_eligible` already admits a work item at ACCEPT with outcome `ready-to-land`. `work launch` runs CLOSURE again for it only when a landing identity is configured. Without one, it starts no session and answers `ready-to-land` from the recorded outcome. So a work item never reruns a model session on every launch.
   - Any other incomplete `closed` outcome, and a `closed` outcome for another candidate, stay the existing `authority-block`, with an escalation naming the missing actions. A work item whose contract lists free-text closure actions therefore stops once instead of rerunning CLOSURE on every launch. This unit gives it no completion path. Neither the coordinator nor `work record-completed` can complete it. How it completes is outside this unit.
3. **The CLOSURE grant** (`composition/role_binding.py`). `ROLE_OPERATIONS` for CLOSURE becomes `{"process-control", "git-write"}`. `_close` requires `process-control` before the session runs, as the VERIFIER does. The grant states authority; the landing credentials, when configured, give the ability to push.

4. **The CLOSURE launch** (`composition/work_registry.py`).
   - The registry preparation resolves the VERIFIER route for the CLOSURE role.
   - It starts a fresh session (new correlation, new clone `<verifier root>/closure-<correlation>`) with the CLOSURE instruction text.
   - It builds a second CliWorkerProvider for CLOSURE alone. Its environment is `worker_environment(root)`, the context command's variables and, only when the registry configuration names a landing identity, the landing credentials. The PRODUCER and VERIFIER process is unchanged. `cli_worker.py` is unchanged.
   - `prepare` passes the custodied candidate for CLOSURE too, and `deliver` gives CLOSURE its own result text.
   - The read-backs for each receipt are built in the composition with the existing adapters: GitSourceControl, the work registry, `work display` and the Projects V2 `write_status`/`read_status`.
   - The registry row moves to DONE after the coordinator's DONE reads back, through `record_completed`, with the landing record at the pushed merge commit as its reference.
5. **The CLOSURE worker** (`invocation_runtime/application/real_worker.py`).
   - RealWorkerProvider takes an optional `closure_process`. Only `_close` uses it; without it `_close` runs no session and attests only `candidate-published`, as today.
   - `_close` runs the CLOSURE session process in its fresh clone.
   - It then returns `WorkerOutcome.closed(candidate, receipts)` with the receipts the composition's read-backs issue.
   - It never trusts the session's own claims.
6. **The context package for CLOSURE** (`context_assembly/domain/work_context.py` and `application/work_context.py`). `FIELDS` gains CLOSURE: the VERIFIER's fields without `producer_self_review`, plus the accepted verdict, the five action names and the landing record's required content. It never gets the PRODUCER's transcript or self-review.
7. **One completion path** (`context_assembly/application/work_completion.py`). Check 2 of `work record-completed` (today: no coordinator record, or one at DONE; otherwise `CONFLICTING_RECORDS`) becomes: no coordinator record. Any coordinator record, at any stage, is refused with `COORDINATOR_OWNED`, and nothing is written. The module docstring changes to match. Work closed by the coordinator completes only through the coordinator's `close` transition.

## 3. Exact permitted files

Production:
- `src/alienintent/execution_coordination/domain/closure.py` (new)
- `src/alienintent/execution_coordination/application/factory_coordinator.py`
- `src/alienintent/composition/work_registry.py`
- `src/alienintent/invocation_runtime/application/real_worker.py`
- `src/alienintent/context_assembly/application/work_context.py`, `src/alienintent/context_assembly/domain/work_context.py`
- `src/alienintent/context_assembly/application/work_completion.py`
- `src/alienintent/composition/role_binding.py`

Tests:
- `tests/execution_coordination/test_factory_coordinator.py`
- `tests/composition/test_worker_launch.py`
- `tests/invocation_runtime/test_runtime.py`
- `tests/context_assembly/test_work_context.py`
- `tests/context_assembly/test_work_completion.py`

## 4. Acceptance checks (each names the wrong implementation it catches)

All offline. The provider is fake, from a test routing file. The remote is a local bare repository with a protected-branch stand-in. The board is a fake Projects V2 client.

1. **Exact receipts.** Each receipt names its action, the work item and the full accepted candidate revision. A receipt for another work item or candidate never counts. Catches loose receipts.
2. **Read-back, never trust.** A CLOSURE session that claims success without pushing, pushes a different tree, writes a landing record without the instructions sha256, or leaves the card in another column gets no receipt for that action. Catches a control plane that trusts the session.
3. **CLOSURE is a fresh session on the VERIFIER route.** A CLOSURE grant without `process-control` runs no session and answers `ineligible`. The CLOSURE command uses the VERIFIER's routed provider and model, in a new clone with a new correlation. Changing the VERIFIER route changes the next CLOSURE command. Catches a reused session and a separate provider.
4. **Credential separation in code.** The landing credentials appear in the CLOSURE session's environment only. The PRODUCER and VERIFIER environments, commands and context packages never contain them. The CLOSURE command, its instruction text, its context package and the invocation journal never contain them either. Without a configured landing identity, no session gets them. Catches leaked credentials. This check proves only the code path; the operating-system separation in section 1 is a prerequisite and is not proved here.
5. **One completion path.**
   - All five receipts move the coordinator to DONE. After that DONE reads back, the registry row moves to DONE through `record_completed`, with the landing record at the pushed merge commit as its reference.
   - The WIP slot is released, by the existing DONE rule.
   - No path added by this unit sets DONE, and `work record-completed` refuses a work item with a coordinator record (`COORDINATOR_OWNED`). The existing `work record-completed` for work landed by hand is otherwise unchanged. A crash after the coordinator's DONE and before the row write is repaired by the next `work launch`.

   Catches a second completion path and a row that drifts from the coordinator.
6. **Ready to land.** Without a landing identity, the result is `ready-to-land`. The prepared merge is verified locally, the work item stays at ACCEPT, the WIP slot is kept and nothing is pushed. A second `work launch` after a landing identity is configured runs CLOSURE again and reaches DONE. A second `work launch` with no landing identity starts no session and answers `ready-to-land` again. Catches a fake completion.
7. **Earlier packets are unchanged.** A contract with free-text closure actions stays at ACCEPT with outcome `authority-block` and `hold_reason` `closure-receipts-incomplete`. No receipt counts for a free-text action; the work item stops once as an authority block naming the missing actions, and a further `work launch` does not rerun CLOSURE. Catches silently mapped actions and a rerun loop.
8. **Fitness.** The changed test files pass when run together in one run (no full suite), and `tools/fitness/check_architecture.py --root src/alienintent --check all` passes.
9. **Real-use proof (blocked until section 1 is met).** One real CLOSURE of a real accepted work item lands on the protected `main` through the factory App, with all five receipts. Until then, the unit records `ready-to-land` from a real accepted work item as its real-use evidence. That is not completed automated closure.

## 5. Excluded

- operating-system credential separation (section 1; separate work);
- the App permission change itself (the Founder's action);
- automatic selection of the next eligible item;
- re-landing work already landed by hand;
- a new provider, store, record kind or configuration source beyond the landing identity entry;
- changing earlier packets.

## 6. Review record

**Revision 2 (2026-10-04).** REVIEWER review of `e4dc9ea` (FAIL). Fixes applied:
- F1: receipts parsed and bound to the work item and candidate before the unchanged `close` transition.
- F2: `ready-to-land` is a recorded, rerunnable outcome; any other incomplete closure stays an authority block, so free-text actions stop once instead of looping.
- F3: the CLOSURE grant gains `git-write` (`role_binding.py` in scope).
- F4: a second CliWorkerProvider for CLOSURE alone.
- F5: the CLOSURE package fields (domain file in scope).
- F6: the row is a projection after the coordinator's DONE, repaired by the next launch; `work record-completed` refuses coordinator-owned work.
- F7: leak checks cover the CLOSURE command, text, package and journal.
- F8: no overclaim of separation.
- F9: this packet is built by the manual workflow, so its budget carries no launch limits.
- Recheck of `b20f47d` (FAIL, wording):
  - R1-R2: outcome names and the order of the row update;
  - R3: `ready-to-land` applies only to the five fixed names;
  - R4: no session reruns without a landing identity;
  - R5: the new rule replaces `work record-completed` check 2;
  - R6: free-text work items get no completion path in this unit;
  - R7: numbering.

**Revision 1 (2026-10-04).** First draft, against `main` `789240c`, with the Founder's decisions:
- fixed closure action names, each with an exact receipt tied to the work item and the accepted candidate;
- the board update confirms both the display text and the card in DONE;
- no second completion path;
- CLOSURE runs as a fresh, separate session on the VERIFIER's configured provider and model, the B-DISP arrangement, and only it gets the landing credentials;
- the factory App is the proposed CLOSURE identity, pending the Founder's explicit authorization;
- the protected-main landing and credential separation are prerequisites to the real-use proof, not reasons to fall back to a permanent manual push.
