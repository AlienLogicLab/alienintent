# One-time maintenance repair: the factory could not recover its own CLOSURE failure (2026-10-09)

Founder-authorized direct repair on main, outside the Work Item path, because the defect is in the landing path itself:
any Work Item fixing it must pass the same broken CLOSURE (a self-repair deadlock). Principle (Founder): "When the
normal repair path is itself broken in a way that prevents the repair from landing, use the smallest separately reviewed
maintenance repair needed to restore the normal path, then return immediately to normal factory operation." Scope was
expanded exactly once and then frozen: "Include only defects independently demonstrated to prevent recovery of the same
stranded Work Item through the same broken recovery path."

## Incident

NO-CHANGE-CANDIDATE-REFUSED (`77d48c83-af41-40fa-bd0d-a56e7e67fc30`, accepted candidate `6c16563`) twice stopped at
CLOSURE: the session wrote the candidate identity (`revision:https://…@6c16563…@sha256:…`) as the request's `revision`,
not the bare commit. `parse_request` refused it correctly (`request-revision`), but the coordinator made every closure
hold an `authority-block`, so a model's formatting slip needed Founder words. The Founder's one authorized retry
reproduced the slip byte for byte. A rehearsal on a copy of the real state then showed the next `authorize` would be a
silent no-op: at ACCEPT the version never moves, so the second hold's decision reused the first decision's key.

## Changes and why each is needed

1. Instruction (`context_assembly/domain/work_context.py` `CLOSURE_REQUEST`, `composition/work_registry.py`
   `CLOSURE_RESULT`): `revision` is "the bare 40-hex SHA from git rev-parse HEAD", never the package's candidate
   identity. The old template said `<full candidate revision>`, which the model matched to the candidate identity.
2. Classification (`execution_coordination/domain/closure.py` `REQUEST_REFUSALS`;
   `execution_coordination/application/factory_coordinator.py` `_retry_closure`): a `parse_request` refusal is a
   worker failure. The item stays at ACCEPT with outcome `closure-retry` (`closure_retries` carried, `closure_refusal`
   named), the next launch runs a fresh CLOSURE session on the same accepted candidate, and at
   `budget_policy.maximum_attempts` it ends in `failure` / `attempt-budget-exhausted`, the same bound `_rework` uses.
   It never opens a decision request.
3. Decision per hold (`composition/work_registry.py` `decide`; `control_plane/application/decision_inbox.py`): a new
   decision's key names the held launch, `work-decide:{id}:{biu_version}:{correlation}:{choice}`; a repeat with no open
   request reuses the recorded key. `decision:{item}` holds the item's latest decision (written before the key record,
   so a crash between them still replays), and a replay of a superseded key has no effect.

## Proof

- Tests (`tests/composition/test_worker_launch.py`): the seven malformed-request rows of
  `test_the_bounded_request_alone_steers_nothing` now expect a non-authority outcome; new
  `test_a_malformed_closure_request_is_retried_on_the_same_candidate_without_a_decision` (the real slip, then a clean
  landing), `test_malformed_closure_requests_end_in_failure_at_the_attempt_budget_never_a_decision`,
  `test_a_second_hold_at_the_same_stage_gets_its_own_decision_and_a_replay_stays_idempotent`. On main's source 10 of
  them fail; with the repair all pass. Removing the stale-replay guard alone fails the last test.
- Rehearsal of the real `work decide` on a copy of the registry state: main's code leaves `authority-block` with the
  request closed; the repair records `decision-recorded`.
- Two independent adversarial reviews; the second, of the complete repair: SHIP, nothing in scope.
- Whole suite: see the commit message.

## Not in scope (backlog)

`closure_retries` carried across a closure rework; any OSError reading the request is `request-missing`;
`maximum_attempts` 1 gives zero CLOSURE retries; replaying the first decision's key while a second hold is open
(only a pre-repair or hand-keyed command); no DecisionConflict for concurrent different final decisions; release-
precondition holds share correlation `release`; tests for exhaustion WIP/RunSummary, `start()` with `closure-retry`,
the mixed old/new key state. Design requirement for the future Factory Doctor / Maintenance Runtime: "AlienIntent must
retain a minimal trusted recovery path capable of repairing the mechanisms required for ordinary repair and landing."
