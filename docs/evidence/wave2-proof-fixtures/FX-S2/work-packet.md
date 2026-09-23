# WO-220103 bounded implementation plan

Authority: Issue #74 release 5791498705 at baseline
`0515444b5c43c83f4a5e26c9ec2c5956f064e1d9`. Runtime state binds the exact
producer invocation, IMPLEMENT, Morty and this isolated worktree. Admission was
clean; active profile limits match the Issue. Existing approved S2 design is the
specification; no redesign or additional approval is needed.

Use the writing-plans and inline execution workflow. Python standard library,
existing OperationalStore schema/tables and retained predecessor evidence.

1. Pin fixture commands/inputs/outcomes/schema in fixture-plan.json and commit
   before product changes. Add failing conformance tests in
   tests/execution_coordination/test_fenced_store.py. Observe missing guarded API.
2. Add frozen guard/vector/consumer receipt values and FencedOperationalStore
   extension in execution_coordination/ports/fenced_store.py. Implement atomic
   commit_guarded, claim_guarded, confirm_guarded, acquire_many, consume_guarded
   and readback in the SQLite adapter, factoring guarded internals into an
   adapter helper if needed. Guard context names exact version vector, authority
   aggregate, epoch and invocation; authority state has schema 1, active flag and
   finite expiry, checked using an injected clock inside the transaction.
3. Persist guard metadata and consumer journal in reserved aggregate namespaces,
   retaining original effect payload and existing tables/schema. Intent atomically
   adopts its target lane and refuses existing unresolved legacy work. Guarded
   claim pins the post-intent vector. Adoption prohibits legacy mutation, claim,
   confirmation and unknown-effect authorization for that lane. Release refuses
   reservations referenced by pending/unknown guarded effects. Sorted batch locks
   share one transaction; contention rolls back only this attempt. No expiry
   takeover or automatic lane rollback.
4. Add GuardedEffectExecutor and explicit local FencedProfile composition. Its
   consumer persists local delivery acceptance/outcome in the same SQLite
   transaction as guard validation, with durable deduplication and readback.
   Reconciliation may confirm after authority expiry using exact original receipt
   and retained fences, but cannot resend. Unfenceable remote consumers are not
   adopted. Existing kernel/bootstrap paths remain outside this local lane.
5. Prove two-process intent/claim competition, process-kill boundaries, vector and
   authority rejection, late sender, receipt correlation, multi-lock rollback,
   profile isolation and every legacy lane bypass. Run focused/full Python tests,
   architecture checks and Node regression checks. Use requesting-code-review for
   a read-only independent code review; repair findings with regression tests.
6. Commit source, run tools/evidence/fx_s2_evidence.py with actual invocation,
   retain hash-addressed raw observations and intact/fault/restored results.
   Negative controls use disposable copies, never disable guards in this worktree.
   Commit evidence, publish assigned branch, read remote SHA back, and post exactly
   one Issue result with the exact invocation marker and candidate SHA. Independent
   BIU verdict remains pending; local review cannot self-approve workflow ACCEPT.

Runtime-managed candidate custody waits for fresh verifier and authorized closure.
No direct main push, merge, live operation, bootstrap retirement or other repository
mutation. Unknown results and telemetry retain explicit uncertainty. Rollback of
an adopted lane first requires quiescence and reconciliation; there is no fallback
API in this bounded additive implementation.
