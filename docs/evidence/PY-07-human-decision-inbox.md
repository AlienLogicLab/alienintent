# PY-07 HumanDecisionRequired and Decision Inbox evidence

This record retains the executable evidence for the PY-07 repair candidate.
It contains no credentials, live Issue mutations, or provider secrets.

## Repair-cycle continuity

- Findings repaired: admission-path and unresolved-effect escalation registration
  and recovery (including the distinct authority-block outcome, reservation
  release, scoped dependent blocking, and normal guarded re-admission); bare
  production-shaped `WorkerOutcome("authority-block")` escalation; non-terminal
  `defer` handling on admission and real SQLite unknown-effect paths; and
  non-resuming `cancel` handling. The real SQLite unknown-effect path atomically
  records the authority block while retaining the effect's `unknown` guard.
  `authorize` changes that guard to its explicitly authorized state; `defer`
  leaves the request open for a later durable authorization. Crash recovery and a lost live
  confirmation use the same authority-block path. PY-05 Work Management decision
  projection wiring, no-op notifier coverage, subprocess restart proof, and
  retained PY-07 evidence remain in scope.
- Previously satisfied proof retained: worker-raised escalation, scoped dependent
  blocking, idempotent decision submission, stale-version rejection, reservation
  release, independent-work continuation, and delivery-failure isolation remain
  in `tests/execution_coordination/test_decision_inbox.py`.
- Superseded evidence: none. The rejected candidate's tests remain present; this
  repair adds proof and does not remove a prior acceptance assertion.
- Supersession authority: Issue #55's released PY-07 contract and its repair
  cycle rule (SWF-23); the verifier's 2026-09-20 REJECT findings identify the
  bounded repair target.
- Replacement proof: an admission refusal opens a complete decision request and
  resumes through normal guards; an unknown effect produces an authority block,
  releases its reservation, blocks only its dependency closure, and is decidable
  through the same normal guards;
  a retry applies a decision that was durably recorded before an interrupted
  re-admission;
  the GitHub Projects adapter delivers a recorded decision-comment fixture; the
  offline notifier leaves the inbox usable; a fresh subprocess submits a stored
  decision and reaches DONE.
  A real-worker authority-block result retains its allocated workspace while its
  mutating reservation is released. A bare production-shaped worker authority
  block now produces the same scoped, decidable behavior, including recovery
  both before and after its authority-block result is recorded; `defer` remains
  open and can be followed by `authorize` for admission and a real unknown
  effect; `cancel` gives the blocked item and its already-blocked transitive
  closure the terminal `cancelled-by-decision` outcome. A decision on an
  unrelated escalation then re-admits only that unrelated work; it cannot
  re-dispatch the cancelled closure.

## Local executable checks

- `python3 -m pytest -q` — exit 0; 129 passed.
- `python3 tools/fitness/check_architecture.py --root src/alienintent --check all`
  — exit 0; `PASS: all architecture fitness checks`.
- `node scripts/check.mjs all` — exit 0; runtime 310/310 passed, preflight
  PASS, RAI 18/18 passed, policy 2/2 passed.

## Retained decision evidence

The Python proofs retain decision-ready escalation payloads in the SQLite
operational store; inbox list/show state; durable decision records keyed by
idempotency key; authority-blocked run summaries; and their exit-status-bearing
test execution. The real subprocess restart proof creates a fresh coordinator
against the same SQLite path, reads the open escalation, records the decision,
and asserts the re-admitted item reaches DONE without a duplicate unblock.

The notifier tests use only recorded local fixtures. The GitHub Projects
projection receives a `HumanDecisionRequired` and returns the fixture receipt
`issue-comment:fixture-55`; no GitHub credential or live Issue comment is used
by the product proof.

The Decision Inbox implementation is in
`control_plane/application/decision_inbox.py`, as required by Scope §4. The
former execution-coordination import path is retained only as a compatibility
import; no scope supersession is claimed.

## FD-05 repair evidence

`test_real_unknown_effect_recovers_as_a_scoped_decidable_authority_block`
creates an actual SQLite `effects.status='unknown'` row and its held
reservation, then starts a fresh coordinator whose worker cannot read the
outcome. It proves the block is durable and decidable, the dependent is scoped,
the unrelated work reaches DONE, and the reservation is released.  The paired
lost-confirmation test exercises the same authority parking during a live run.
`test_lost_effect_confirmation_parks_the_running_item_without_stopping_the_factory`
proves coordinator-to-worker retention for the unknown-effect path, and
`test_real_worker_retains_an_authority_blocked_workspace_while_releasing_capacity`
proves the retained-workspace half of AC 3 at the runtime ownership boundary.

## Closure accounting

- Authority interruptions: none after the coordinator's release authorization.
- Live/deployment actions: none required or performed.
- Token and monetary cost: not reported by local tools; retained as unknown.
- RETURN_TO_IMPLEMENT occurrences: none in this repair cycle.
