# PY-07 HumanDecisionRequired and Decision Inbox evidence

This record retains the executable evidence for the PY-07 repair candidate.
It contains no credentials, live Issue mutations, or provider secrets.

## Repair-cycle continuity

- Findings repaired: admission-path and unresolved-effect escalation registration;
  PY-05 Work Management decision projection wiring; no-op notifier coverage;
  subprocess restart proof; retained PY-07 evidence.
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
  resumes through normal guards; unknown-effect handling registers a request;
  the GitHub Projects adapter delivers a recorded decision-comment fixture; the
  offline notifier leaves the inbox usable; a fresh subprocess submits a stored
  decision and reaches DONE.

## Local executable checks

- `python3 -m pytest -q` — exit 0; 118 passed.
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

## Closure accounting

- Authority interruptions: none after the coordinator's release authorization.
- Live/deployment actions: none required or performed.
- Token and monetary cost: not reported by local tools; retained as unknown.
- RETURN_TO_IMPLEMENT occurrences: none in this repair cycle.
