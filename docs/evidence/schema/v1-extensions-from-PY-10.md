# v1 extensions observed from PY-10

**No v1 schema change is made here.** Both v1 schemas allow additional properties, and the PY-10
records use that allowance rather than redesigning the format. This file documents every field and
event type added beyond the v1 vocabulary so the additions are explicit rather than silent. It
extends, and does not supersede, [`v1-observed-gaps-from-PY-04.md`](v1-observed-gaps-from-PY-04.md)
and [`v1-extensions-from-PY-05-to-PY-09.md`](v1-extensions-from-PY-05-to-PY-09.md).

PY-10's records describe something earlier trajectories did not: a **live run of the factory over
other BIUs**, rather than the lifecycle of the BIU that produced them. The record at
[`PY-10-sandbox-run.jsonl`](../execution-trajectories/PY-10-sandbox-run.jsonl) therefore uses
`biu_id` for the *sandbox* BIUs the factory consumed (`SB-01`…`SB-06`), with `PY-10` reserved for
run-level observations, and `project` naming the sandbox Project rather than AlienIntent. The
`scope` field on the derived Quality Evidence states that distinction so a reader cannot mistake
these measures for PY-10's own lifecycle.

## Execution Trajectory — added event types

All are factual observations. No conclusion is encoded in an event type.

| Event type | Records |
|---|---|
| `DOCTOR_PASSED` | the pre-autonomy validation gate ran and what it disposed, before any autonomous start |
| `ISOLATION_OBSERVED` | the two isolation controls as they were read back at run time — permission-enforced repository scope and configuration-enforced Project addressing, with the refusal a foreign identity met |
| `PROCESS_LOSS_INJECTED` | a deliberate, operator-caused loss of the running control plane, with the signal used and the reservation held at that moment. Distinct from a liveness gap, which is observed rather than caused. |
| `CONTENTION_PROBE_REFUSED` | an independent attempt to take a resource the factory held, and its refusal. This turns a concurrency limit from an absence of contention into an observed exclusion. |
| `PROJECTION_CONFIRMED` | downstream projections were read back from the provider after the run, rather than inferred from the writer's own receipt |

`UNKNOWN_EFFECT_PARKED` was considered and not added: the existing `HUMAN_DECISION_REQUIRED` already
carries it, with the parking stated in `description`.

## Execution Trajectory — added fields

| Field | Meaning |
|---|---|
| `acceptance_criteria` | the numbered acceptance criteria this event is evidence for. Lets a criterion be traced to named events rather than to a narrative, and lets an unevidenced criterion be found mechanically. |
| `wip_observed` | the number of simultaneously held mutating reservations at the moment of the event, as sampled from the durable store |

`invocation_id`, `branch`, `commit_sha`, `candidate_ref`, `candidate_type`, `candidate_diff`,
`authority_ref`, `lifecycle_from`/`lifecycle_to`, `observation_type`, `verified`, `recorder`,
`token_usage` and `cost` are all existing v1 or PY-05–PY-09 fields and are used unchanged.

## Quality Evidence — added fields

| Field | Meaning |
|---|---|
| `scope` | what these measures describe. Required here because the record is about a run over other BIUs, not about this BIU's lifecycle. |
| `acceptance_criteria_total`, `acceptance_criteria_verified`, `acceptance_criteria_unmet` | the acceptance list as a count and, where any failed, by number |
| `biu_seeded`, `biu_done`, `biu_failed`, `dispatches_observed` | the run's throughput, separated from its acceptance |
| `distinct_priorities`, `dependency_edges` | the shape of the backlog that was consumed, so an ordering claim can be read against what was there to order |
| `maximum_concurrent_mutating_invocations` | with its definition: the highest number of simultaneously held reservations across every sampled moment |
| `process_losses_injected` | deliberate losses caused by the run, kept distinct from `liveness_incidents`, which are losses observed |
| `duplicate_executions_after_restart` | with its definition, because "no duplicate" is the claim a restart must survive |
| `candidates_published`, `candidates_independently_read_back` | kept separate: publication is not retrieval |
| `doctor_disposition` | the pre-autonomy gate's result |
| `guards_proven_red`, `guards_not_proven_red` | the SWF-24 measure as a count and, where any guard could not be made to fail, by name. A guard that cannot go red is reported, never omitted. |
| `offline_tests` | the offline suite's own summary line, as the suite printed it |

## Still open for a future schema review

1. **`acceptance_criteria` is a per-BIU-contract numbering.** It means "criterion 4 of *this* BIU's
   list" and does not resolve outside it. A stable criterion identity — contract plus ordinal, or a
   named criterion — would let coverage be compared across BIUs.
2. **The three open items from PY-05–PY-09 remain open**: `recorded_at` overloading, a finding as a
   first-class entity, and `repair_mode` being authored rather than derived. PY-10 had no repair
   cycles, so it adds no evidence either way.
3. **A run is not a first-class entity.** PY-10's events all belong to one coherent run, and that is
   expressed only by their shared `recorder` and adjacent timestamps. A `run_id` would make "these
   facts came from one run" checkable rather than inferred — which matters precisely because the
   acceptance list requires them to be from one run.
