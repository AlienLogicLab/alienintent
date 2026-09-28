# SF-REQ-057 — durable Founder intake implementation plan

Status: PLAN candidate for Issue #147. This plan does not release a BIU or
authorize live installation. Owner: SF-REQ-057 / Issue #147, Founder priority P0.
Source: `founder-requirement-intake-durability-live-proof-20260929.json`.
Accepted specification: `docs/evidence/sf-req-057-durable-founder-intake-specification.md`
at `82b1915478d0ffbf837e1a8592553ce0815789db`.

## One bounded implementation unit

The implementation owner is the Node Factory Director Host input adapter,
`tools/orchestration/factory_director_inputs.py`. Its existing inbox predicate
already keeps acknowledgement-only receipts pending and retains materialized
requirements until Project `DONE`. Extend that same read-only predicate path to
verify provenance and backlog identity before a receipt counts. Do not create
a second intake service, a new lifecycle, a Wave assignment, or a separate
source of product authority.

Permitted implementation paths are `tools/orchestration/factory_director_inputs.py`,
its focused tests in `tools/orchestration/test_factory_director_inputs.py`, and
the corresponding runtime contract and bounded fixture/evidence under
`docs/operations/` and `docs/evidence/`. The runtime state, credential files,
installed services, and Founder source entry are outside the worker's mutable
scope. The existing #147 receipt is a separately controlled local state
migration, not a repository file for the worker to rewrite opportunistically.

## Ordered work and checks

1. Pin the source entry bytes, digest, current receipt, Issue #147 body, Project
   item `PVTI_lADOEcrpC84Bj5i_zg9UCCU`, priority P0, and canonical artifact at
   `45891e43d7ff14253fe2c38a0af736b981135214`. Fetch and read back the
   revision from the canonical remote branch. Record each read result and its
   failure mode before changing receipt semantics.
2. Define one validation result for a `FOUNDER_REQUIREMENT` receipt. Require a
   full 40-hex revision, canonical artifact path, positive Issue number,
   configured Project number, exact Project item id, and SHA-256 of the complete
   source entry bytes. Check the revision against the fetched canonical remote
   branch; read the artifact at that revision; compare the exact Founder
   requirement and each acceptance string against the artifact and/or Issue;
   retain the supplied title and authority in canonical or immutable
   source-linked provenance. Verify Issue repository, unique Project item,
   item id, and source priority. A failed or unavailable read refuses a
   processed verdict with an attributable reason.
3. Preserve the existing through-`DONE` predicate after materialization
   validation. For every non-`DONE` state, keep the entry pending. Only an
   authoritative, unique Project `DONE` readback can clear it. A later
   disappearance, priority change, conflicting source digest or invalid
   supersession must reopen attention or fail closed, never infer completion.
4. Migrate the existing #147 receipt only after the exact source, remote
   artifact, Issue and Project chain are read back. Atomically enrich that
   receipt with the source-byte digest and provenance evidence while preserving
   its prior contents. A mismatch leaves #147 pending and is recorded for
   Director repair. The migration must be repeatable across interruption and
   must not create another Issue or canonical requirement.

The deterministic readback implementation should reuse the complete Project
reader in `tools/live/project_materialization.py` and configured GitHub
identity, rather than trusting a receipt's own claims. Keep the adapter
read-only with respect to GitHub, Git, inbox entries, runtime state and
configuration. Bound remote reads and make their errors explicit; do not turn
an unavailable external prerequisite into a false `DONE` or idle result.

## Proof fixture and release gates

The focused fixture in `tools/orchestration/test_factory_director_inputs.py`
must distinguish valid and invalid receipt tuples; missing remote revision or
artifact; exact-content, title/authority provenance, Issue, Project item and
priority mismatch; duplicate item; source-byte replacement; interrupted
migration and restart; each non-`DONE` state; and authoritative `DONE`.
Negative controls must show that acknowledgement-only and syntactically valid
but unverified receipts stay pending. Record exact commands, exit codes,
fixture inputs, output counts and the resulting predicate/diagnostic values.

After the plan is accepted, select #147 to TASKS and create a bounded task
packet from this plan. Run native Agent Ready on the exact packet. READY and
IMPLEMENT require their ordinary release, dependency, budget, custody and WIP
gates. A PRODUCER publishes the exact candidate branch and SHA before
`RESULT=VERIFY`; the runtime runs applicable feature regressions before an
independent VERIFIER reviews that SHA. ACCEPT and SWF-19 closure follow normal
evidence gates. The Founder inbox obligation remains active until #147 is
authoritatively `DONE`.

No installed host change, live operation, protected-branch push by a BIU
worker, or retirement follows from this planning artifact. Review the plan's
path ownership and #147 migration boundary before selecting TASKS.

General lesson: **DETERMINISTIC_PREFLIGHT** — prove the source, remote revision,
exact content and unique backlog identity before a materialization receipt
changes the intake predicate.
