# SF-REQ-057 — durable Founder requirement intake

**Project item:** AlienLogicLab/alienintent#147, Project #1 item `PVTI_lADOEcrpC84Bj5i_zg9UCCU`.
**Founder priority:** P0. **Lifecycle:** TASKS.
**Source:** `~/.local/state/alienintent/factory-director/inbox/founder-requirement-intake-durability-live-proof-20260929.json` (immutable Founder entry).
**Canonical requirement:** `docs/decisions/alienintent-software-factory-plan.md`, SF-REQ-057 at `45891e43d7ff14253fe2c38a0af736b981135214`.
**Accepted specification:** `docs/evidence/sf-req-057-durable-founder-intake-specification.md` at `82b1915478d0ffbf837e1a8592553ce0815789db`.
**Accepted plan:** `docs/evidence/sf-req-057-durable-founder-intake-plan.md` at `5de6a741b549619c78f47a6af563c75ff52a0b97`, independently accepted on Issue #147. The accepted review corrects its owner wording: this is the **Python Factory Director Host input adapter**, not the Node execution runtime.

## Intent and authority

This is the bounded implementation contract for a native Agent Ready assessment at TASKS. Assess whether an agent can implement and verify its fixed behavior without inventing an owner decision. A readiness verdict is separate from the later release admission and does not itself launch work.

Implement the exact Founder requirement: every future Founder requirement entering the Director inbox remains an active obligation through exact canonical materialization and the normal prioritized Project lifecycle to DONE. An acknowledgement, defer note, or successor reminder is not materialization. Preserve the Founder source's title, requirement, acceptance strings, priority and authority without reinterpretation. Do not assign a Wave, change the Wave 2 DAG, or invent a second intake service or lifecycle.

The one repository implementation owner is `tools/orchestration/factory_director_inputs.py`. Reuse its existing read-only inbox predicate, the configured GitHub identity and the complete Project read path in `tools/live/project_materialization.py`. The Node dispatcher, installed host, credentials, operational state, Founder source entry and current #147 receipt are outside the worker's mutable scope. The receipt migration is a separately controlled Director action after readback; a worker must not edit it opportunistically.

## Repository-state admission and scope

At release, name the exact `origin/main` baseline, inspect the isolated producer worktree, classify every pre-existing change by owner and authority, and refuse conflicting mutation. Permit changes only to `tools/orchestration/factory_director_inputs.py`, focused `tools/orchestration/test_factory_director_inputs.py`, the corresponding runtime contract under `docs/operations/`, and bounded fixture/evidence under `docs/evidence/`. A changed path outside these requires a new scope decision before editing.

Pin the complete source bytes and SHA-256, existing receipt, #147 Issue body, unique Project item and P0 priority, and the canonical artifact and revision before changing receipt semantics. Fetch the canonical remote and verify that the exact revision belongs to its main history; read the artifact at that revision. Record observed identities and failures. Do not accept receipt claims as self-verifying evidence.

## Implementation and acceptance

1. Validate one `FOUNDER_REQUIREMENT` receipt as a chain: full 40-hex canonical remote revision, artifact path at that revision, positive Issue number in the configured repository, configured Project number, exact unique Project item id, retained Founder priority, and digest of the complete source entry bytes. Compare the Founder requirement and each acceptance string verbatim against the artifact and/or Issue. Keep the supplied title and authority verbatim in canonical or immutable source-linked provenance. A mismatch, duplicate item, missing revision/artifact, or unavailable read must refuse a processed verdict with an attributable reason.
2. After valid materialization, keep the inbox entry active at every Project status short of authoritative DONE. A missing item, changed priority, changed source bytes under the same id, conflicting supersession, or lost external read must reopen attention or fail closed. Repeat delivery and restart must reconcile to the same source key, digest and backlog identity, without creating another requirement or Issue.
3. Preserve the existing #147 receipt for a separate, atomic Director migration. The worker supplies a deterministic migration check and evidence requirements; the Director first reads back exact source bytes, canonical remote revision and artifact, Issue and unique Project/P0 identity, then enriches the receipt with source digest and provenance evidence while preserving its prior content. Interrupted migration must be repeatable. A mismatch leaves #147 active and calls for repair.
4. Keep the adapter read-only with respect to GitHub, Git, inbox entries, runtime state and configuration. Bound external reads, make their errors explicit, and preserve current compatibility and identity markers.

Acceptance evidence must discriminate acknowledgement-only and incomplete/fake receipts; unpublished revision or missing artifact; exact-content, title/authority, Issue, item, priority and source-byte mismatch; duplicate Project item; restart and interrupted migration; each non-DONE state; and authoritative DONE. Record exact fixture inputs, commands, exit codes, counts and resulting predicates and diagnostics. Do not weaken an applicable feature regression to make a candidate pass.

## Custody and continuation

After a native readiness assessment, the Director handles normal release admission: bind a finite issue-specific execution limit and read it back from the running engine, confirm dependency and WIP capacity, name isolated producer/verifier custody and baseline, and record a RELEASED admission on #147. These are launch controls, not unknown product intent or prerequisites to assessing this packet. The producer publishes its candidate branch and exact SHA before `RESULT=VERIFY`; applicable feature regressions precede an independent verifier. Repair findings monotonically, preserving previously proved behavior and evidence. ACCEPT, SWF-19 landing and Project DONE require their normal gates. The Founder inbox obligation stays active until authoritative Project DONE.

No installed-service change, live cutover, protected-branch push by a BIU worker, or retirement follows from this packet. General lesson: **DETERMINISTIC_PREFLIGHT** — prove exact Founder provenance and unique backlog identity before materialization affects the intake predicate, then keep the obligation active through DONE.
