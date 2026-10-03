# Work unit: automated closure and cleanup for registry work

**Label:** `AUTOMATED-CLOSURE` (a document label; the permanent id is allocated when this draft is registered).
**Status:** Draft revision 1 for independent review, 2026-10-04. Not approved, not assessed, not released.
**Position on the path:** path row 8, the second of the three connections still missing from the critical path. Row 7 (restart continuation) is landed at `main` `789240c`. Automatic selection and launch of the next eligible item follows.
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it (by hand, because this unit is the one that automates closure).

## 0. The whole design (plain English)

Today a work item that the VERIFIER accepts stops at ACCEPT. `work launch` answers `closure-not-automated`, and a person lands the work. The existing CLOSURE role (`RealWorkerProvider._close`) can attest only `candidate-published`. The coordinator moves a work item to DONE only when every action in the contract's `required_closure_actions` has a receipt (`lifecycle.transition`, action `close`). Packets name those actions in free text, so no receipt can match them.

This unit makes closure a normal launched step:
1. **Fixed closure action names.** There are five: `candidate-published`, `merged-to-main`, `landing-record`, `board-updated` and `workspaces-cleaned`. Each receipt is exact and names the action, the work item and the accepted candidate, as `<action>:<work item id>:<candidate revision>`. A new packet lists these names in `required_closure_actions`. Free-text actions in earlier packets match no receipt, so those work items stay at ACCEPT, as today.
2. **CLOSURE is a fresh, separate session.** This is the B-DISP arrangement. `work launch` at ACCEPT starts the CLOSURE role on the VERIFIER's configured provider and model (the VERIFIER route in `model-routing.json`), in a new session with its own fresh clone. No new provider is added. The session gets the instruction text, its context package and, only when they are configured, the landing credentials. PRODUCER and VERIFIER sessions never get landing credentials.
3. **The CLOSURE session performs; the control plane reads back.** The session merges the exact accepted candidate into the default branch with `--no-ff`, writes the landing record and pushes. The control plane, never the session, issues each receipt after its own read-back:
   - `candidate-published`: today's check;
   - `merged-to-main`: the remote default branch contains a merge whose second parent is the candidate, and its source tree equals the candidate's;
   - `landing-record`: at that pushed commit, the landing record exists, and it names the work item, the full candidate revision and the sha256 of the instructions at the work item's pointer (the same checks `work record-completed` applies);
   - `board-updated`: after the existing `work display`, the card's display text reads back current, and `read_status` reads back DONE after `write_status(DONE)`. Both are required;
   - `workspaces-cleaned`: this work item's retained PRODUCER worktrees, VERIFIER clones, PRODUCER read-back folders and CLOSURE clones are removed under the existing ownership checks. Anything kept is named in `cleanup_diagnostics` with its reason, and then no receipt is issued.
4. **One completion path.** The coordinator's existing `close` transition, ACCEPT to DONE, is the only way a work item completes. In the same closure step, the work registry row moves to DONE through the existing `record_completed` storage method. The evidence is one fixed record of the five receipts and their read-backs, checked as `work record-completed` checks evidence. No second completion command is added.
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
   - The existing `_advance` for `closed` keeps its rule: DONE only when `required_closure_actions` ⊆ receipts.
   - A `closed` outcome with fewer receipts is recorded and leaves the work item at ACCEPT. The answer is `ready-to-land` when every receipt except `merged-to-main` is present, and `closure-incomplete` otherwise. This keeps the WIP slot (the existing rule; it is not a final outcome).
3. **The CLOSURE launch** (`composition/work_registry.py`).
   - The registry preparation resolves the VERIFIER route for the CLOSURE role.
   - It starts a fresh session (new correlation, new clone `<verifier root>/closure-<correlation>`) with the CLOSURE instruction text.
   - It adds the landing credentials only to the CLOSURE session's environment, and only when the registry configuration names a landing identity.
   - The read-backs for each receipt are built in the composition with the existing adapters: GitSourceControl, the work registry, `work display` and the Projects V2 `write_status`/`read_status`.
   - The registry row moves to DONE after the coordinator records DONE, from the receipts record.
4. **The CLOSURE worker** (`invocation_runtime/application/real_worker.py`).
   - `_close` runs the CLOSURE session process in its fresh clone.
   - It then returns `WorkerOutcome.closed(candidate, receipts)` with the receipts the composition's read-backs issue.
   - It never trusts the session's own claims.
5. **The context package for CLOSURE** (`context_assembly/application/work_context.py`). The CLOSURE role gets the VERIFIER's fields plus the accepted verdict, the five action names and the landing record's required content. It never gets the PRODUCER's transcript.

## 3. Exact permitted files

Production:
- `src/alienintent/execution_coordination/domain/closure.py` (new)
- `src/alienintent/execution_coordination/application/factory_coordinator.py`
- `src/alienintent/composition/work_registry.py`
- `src/alienintent/invocation_runtime/application/real_worker.py`
- `src/alienintent/context_assembly/application/work_context.py`

Tests:
- `tests/execution_coordination/test_factory_coordinator.py`
- `tests/composition/test_worker_launch.py`
- `tests/invocation_runtime/test_runtime.py`
- `tests/context_assembly/test_work_context.py`

## 4. Acceptance checks (each names the wrong implementation it catches)

All offline. The provider is fake, from a test routing file. The remote is a local bare repository with a protected-branch stand-in. The board is a fake Projects V2 client.

1. **Exact receipts.** Each receipt names its action, the work item and the full accepted candidate revision. A receipt for another work item or candidate never counts. Catches loose receipts.
2. **Read-back, never trust.** A CLOSURE session that claims success without pushing, pushes a different tree, writes a landing record without the instructions sha256, or leaves the card in another column gets no receipt for that action. Catches a control plane that trusts the session.
3. **CLOSURE is a fresh session on the VERIFIER route.** The CLOSURE command uses the VERIFIER's routed provider and model, in a new clone with a new correlation. Changing the VERIFIER route changes the next CLOSURE command. Catches a reused session and a separate provider.
4. **Credential separation in code.** The landing credentials appear in the CLOSURE session's environment only. The PRODUCER and VERIFIER environments, commands and context packages never contain them. Without a configured landing identity, no session gets them. Catches leaked credentials. This check proves only the code path; the operating-system separation in section 1 is a prerequisite and is not proved here.
5. **One completion path.**
   - All five receipts move the coordinator to DONE, and the registry row to DONE, in the same closure step, with the receipts record as evidence.
   - The WIP slot is released, by the existing DONE rule.
   - No other path sets DONE.

   Catches a second completion path and a row that drifts from the coordinator.
6. **Ready to land.** Without a landing identity, the result is `ready-to-land`. The prepared merge is verified locally, the work item stays at ACCEPT, the WIP slot is kept and nothing is pushed. Catches a fake completion.
7. **Earlier packets are unchanged.** A contract with free-text closure actions stays at ACCEPT with `closure-incomplete`. Catches silently mapped actions.
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

**Revision 1 (2026-10-04).** First draft, against `main` `789240c`, with the Founder's decisions:
- fixed closure action names, each with an exact receipt tied to the work item and the accepted candidate;
- the board update confirms both the display text and the card in DONE;
- no second completion path;
- CLOSURE runs as a fresh, separate session on the VERIFIER's configured provider and model, the B-DISP arrangement, and only it gets the landing credentials;
- the factory App is the proposed CLOSURE identity, pending the Founder's explicit authorization;
- the protected-main landing and credential separation are prerequisites to the real-use proof, not reasons to fall back to a permanent manual push.
