# PY-03 execution trajectory

This interpretation is derived from [PY-03.jsonl](PY-03.jsonl); cited Issue comments, Git objects, Actions records, `state.json`, and logs remain authoritative.

## Observed facts

PY-03 was released at 03:31:26Z from baseline `b63a286`. An initial candidate `1aa8bb7` was retained but correctly not sent to VERIFY because its producer identified uncompleted contracted acceptance work. The coordinator directed continuation at 03:41:16Z without changing the contract. Candidate `03f1c67` entered VERIFY and was independently rejected on four findings: port-only conformance, custody-boundary redelivery, reservation recovery, and typed unavailable outcomes. Repair candidate `c3ba58d` was independently accepted at 04:11:07Z.

The next closure invocation failed before a result because its selected model was at capacity. The log does not identify its provider/model or explain the subsequent gap. A later closure invocation made normal merge `d8f80e1`, whose second parent is `c3ba58d`; scoped candidate-content paths were unchanged. Both required Actions workflows succeeded on the merge result. The coordinator then recorded Project DONE and closed Issue #51. Sources: [release](https://github.com/AlienLogicLab/alienintent/issues/51#issuecomment-5747333717), [REJECT](https://github.com/AlienLogicLab/alienintent/issues/51#issuecomment-5747452727), [ACCEPT](https://github.com/AlienLogicLab/alienintent/issues/51#issuecomment-5747544877), [closure](https://github.com/AlienLogicLab/alienintent/issues/51#issuecomment-5748104520), [DONE](https://github.com/AlienLogicLab/alienintent/issues/51#issuecomment-5748121990).

## Derived measurements

- Total release-to-DONE interval: 10,533 seconds.
- Three producer candidate attempts, two verifier cycles, one repair cycle, four blocking REJECT findings, and one `RETURN_TO_IMPLEMENT`.
- The initial authority exception received a coordinator response after 125 seconds; the response found no missing Founder decision.
- Closure measured 8,152 seconds from ACCEPT comment to DONE comment. It includes one observed model-capacity failure; the reason and duration of the remaining gap are UNKNOWN.
- Verifier logs report `firstParty` / `claude-opus-5` and $4.044471 combined list-basis cost. Six completed logs expose native token fields. Producer cost and end-to-end cost are UNKNOWN.

## Candidate learnings — not promoted

- **CANDIDATE LEARNING — NOT PROMOTED:** Distinguish uncompleted contracted work from a genuine authority gap before raising a Founder exception.
- **CANDIDATE LEARNING — NOT PROMOTED:** Port-only conformance needs executable adapter substitution, not only interface annotations.
- **CANDIDATE LEARNING — NOT PROMOTED:** Crash recovery evidence must exercise ordinary redelivery and durable recovery queries, not a privileged repair path.
- **CANDIDATE LEARNING — NOT PROMOTED:** Capacity-failure observability needs later work; this record does not infer why the next closure invocation was delayed.
