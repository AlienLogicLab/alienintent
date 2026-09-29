# Python self-building 01 — publish assessed work into the live queue

**Status:** Proposed design for Founder review. Do not release to Claude or place in the live queue.
**Prior assessment:** Agent Ready returned READY for an earlier, less detailed version. That result is retained as history and does not apply to this revision. After Founder review, assess the exact revised text again.
**Source:** Founder direction on 2026-09-29. **Baseline:** pin the current main revision when released, after issue 125 and the separately owned Node shutdown are read back.

## The problem and the required result

Python already has a preparation path that can compile work and consume an Agent Ready assessment. Separately, its sandbox runner has completed six manually seeded work items from a real GitHub Project. There is no proven path that takes the exact assessed output and safely makes it a real AlienIntent Issue in the Project for that runner. This work unit supplies that one handoff. It must not make an unassessed or stale work item executable.

A successful result is one real Issue and one Project item referring to the same **already landed immutable execution contract** and current assessment identity. The Project enters READY only after every reference has been read back. The runner sees the item once, with the intended priority and dependencies. This work unit stops before launching Claude.

## Existing parts to reuse and ownership

- The existing preparation service owns requirements, clarified decisions, approved design, proof obligations, compiled work and readiness applicability. Its `UpstreamIntegration.current` returns eligibility tied to an assessment attempt, contract digest and input fingerprint.
- The execution coordinator owns release, work selection and role transitions. The live work adapter already reads Project entries and checks a per-item contract. Do not add scheduling or assessment decisions to the GitHub adapter.
- The configured GitHub repository reader can fetch a contract at a specified revision. The current Project directory can read items and write status, but its item-creation method makes a **draft**, not a real Issue; it does not add an existing Issue or set priority. Add narrow repository-Issue creation/comment and Project attachment/priority methods at the outer adapter boundary. Never use a draft as the finished work item. The application handoff service belongs to preparation/planning, not the execution coordinator.
- Use the existing durable store and effect-custody conventions for attempts and uncertain outcomes. Do not create a second state owner, copy Agent Ready's rubric, or change Node.

## Fixed handoff input

One invocation receives a compiled work identity, the already landed canonical contract path and exact repository revision, source requirement revisions, approved design identity and digest, proof obligations, governing decisions, dependency identities, inherited priority, target repository/Project identity, a current `ReadinessEligibility` value and the retained raw Agent Ready receipt reference. The contract must have reached that revision through independent review and closure before this handoff starts. It rejects absent or conflicting values. Re-read readiness applicability and the source/design/decision inputs immediately before any external write and again before READY.

The immutable contract is the existing `BiuContract` canonical payload. Its digest must match the eligibility contract digest and the digest the runner computes after retrieving it. The assessment input fingerprint and attempt identity are separate values; neither may be replaced by the contract digest. The requirement/design/proof links remain explicit in the contract or a companion source record. No output claims that readiness itself granted execution authority.

## Required effect order and readback

1. Record an idempotent handoff intent in the existing durable store, keyed by configured profile, work identity, contract digest and assessment attempt. Preserve the source and design references. A conflicting request under the same work identity holds without changing an existing item.
2. Read the already landed contract from its declared path and exact repository revision through the configured credential. Reconstruct the existing contract value and verify identity, content digest, dependencies and source links against the current preparation evidence. The contract path is input, not created by this unit. A branch name or mutable default-branch path alone is insufficient.
3. Create or identify one **real repository Issue**. Its body extends the existing line-based descriptor with exactly these keys: `biu`, `contract`, `contract_revision`, `readiness_digest` (the contract digest), `assessment_attempt`, `assessment_fingerprint`, `source_revision`, `design_digest` and `depends_on`. Reject missing, repeated or conflicting keys. Retain the Issue's immutable GitHub identity, not its title. Post and read back the native Agent Ready assessment receipt under the configured authorized operator identity; its input fingerprint and exact work-unit text must match the retained preparation evidence. Neither the descriptor nor comment may contain credentials.
4. Attach that Issue to the configured Project through its content identity. Read back Project membership, Issue content identity, descriptor and native assessment comment. Write the inherited priority through the configured option identity (the runner accepts only P0 through P5) and read it back. A Project item from another Project or a draft item is a refusal.
5. Recheck current readiness and upstream references. Only then write READY as the **last** external step. Read back the READY value, its update time, priority, Issue identity, native receipt and descriptor. The live reader fetches the contract at its pinned revision, verifies digest and dependencies, and rechecks that the latest authorized assessment applies. The current Project query fetches at most 50 items; paginate to a complete result or refuse it. Never set `complete=True` based on a partial page.
6. Commit the observed Issue/Project identities and effect receipts in the existing store. Identical retries return the same result. A timeout, lost response, partial write or unknown effect stays held until fresh readback establishes whether the exact intended object exists. Never blindly issue a second create call after an uncertain result.

The Issue and Project are external projections; the durable preparation/assessment evidence remains authoritative. A native assessment comment is a read-back projection of that evidence, not an independently invented assessment. There is no destructive rollback of an uncertain Issue or Project item. A repair first reconciles the exact identities and either finishes the same handoff or escalates a typed conflict.

## Runner boundary

Change the existing reader only as needed to consume the pinned contract revision and the distinct assessment reference. It must check that the Issue and Project identity, contract bytes, digest, assessment applicability, dependency identities, priority and page completeness agree. The current Project query limits results to 50 items; do not label a partial page complete. Paginate through the relevant Project or refuse an incomplete read. A stale assessment or changed source/design must hold before release even if the Project still displays READY.

## Explicit limits and acceptance

This unit does not publish or land the work contract; that is a separate candidate unit. It does not implement new requirement intake, design verification, work splitting, a new coordinator, a new worker provider, automatic landing, code review, or a resident Director. It does not run a live AlienIntent implementation task. Use a disposable, isolated repository and Project for external-effect proof; production mutation awaits later authority.

Acceptance must prove, with exact identities and independent readback:

1. One current assessed work unit becomes one real Issue and one Project item, at the intended priority and dependency set. The runner retrieves the same immutable contract and does not start a worker during handoff.
2. An identical retry creates no duplicate Issue, Project item or assessment comment. A conflicting request under the same work identity holds.
3. Changed requirement, design, decision, proof plan, contract or assessment fails before READY; change after READY fails at runner release. A fabricated, failed, incomplete or stale Agent Ready result cannot pass.
4. Failures or lost responses after Issue creation, native assessment comment, Project attachment, priority write and READY write each recover by exact readback without duplicate effects. A missing or inaccessible already landed contract holds before any Issue creation. Ambiguous results remain held; unrelated eligible work is unaffected.
5. A wrong repository, wrong Project, draft item, duplicate identity, malformed descriptor, mismatched contract revision, missing priority, dependency mismatch, partial Project page or inaccessible credential is refused.
6. Each negative check demonstrably fails when its guard is removed or its input is corrupted. Record the input fingerprint, contract revision and digest, Issue/Project identities, write/readback responses and final state without secrets.

The implementer must use the existing bounded persistence and adapter patterns, declare the owner, maximum growth, retention and cleanup for every new temporary or durable object, and test interruption plus storage pressure. Routine admission must not scan all historical handoffs.

## Implementation and independent review

Claude works in its own isolated working directory after the Founder accepts this design, Agent Ready assesses this exact text, and the work is released against a pinned baseline. Claude may choose internal method names and small helper functions, but may not choose a different authority owner, use draft Issues, omit readback, treat an assessment as release, or weaken failure cases. A discovered need to change these choices returns to design authority before code continues.

Claude publishes an exact candidate revision. A **new Codex review instance**, in a fresh read-only working directory, checks source intent, domain ownership, dependency direction, Python typing and error handling, resource lifetime, concurrency, security, overbuilt or duplicate mechanisms, test strength and every negative case. It records concrete findings. Claude repairs without dropping previously passing behavior or proof.

A **different new Codex closure instance** acts only after an accepted review. It checks the accepted revision and independent evidence, lands precisely that content, verifies required checks and actual outcome on the landed revision, updates the work item to completed, and records external readbacks. It cannot substitute its own review for the independent verdict. A failed check returns to Claude; no silent completion. The cleanup owner then removes only temporary resources whose custody and retention checks pass.

## Founder review points

The proposed choices needing your approval are: require an already independently landed contract; use real Issues rather than drafts; pin that contract's revision in the Issue descriptor; retain a distinct current assessment identity; write READY last; do not launch a live task in this unit; and use a separate Codex closure instance. The previous Agent Ready READY result did not decide these choices. A new assessment is required after this design is accepted.
