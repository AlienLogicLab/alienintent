# PY-02 execution trajectory

This is a generated interpretation of [PY-02.jsonl](PY-02.jsonl). The JSONL is the local machine-readable record; its cited Issue comments, Git objects, Actions runs, state record, and decision record remain the authority.

## Observed facts

### A. Lifecycle timeline

| UTC time | Observed event | Durable source |
|---|---|---|
| 02:11:06 | Founder release moved PY-02 from READY to IMPLEMENT. | [Issue release](https://github.com/AlienLogicLab/alienintent/issues/50#issuecomment-5746950357) |
| 02:23:32 | Producer published `a82ca4e6` for VERIFY. | [candidate 1](https://github.com/AlienLogicLab/alienintent/issues/50#issuecomment-5747017900) |
| 02:29:11 | Independent verifier REJECTED and returned to IMPLEMENT. | [first review](https://github.com/AlienLogicLab/alienintent/issues/50#issuecomment-5747048805) |
| 02:32:43 | Repair candidate `8689771b` was published for VERIFY. | [candidate 2](https://github.com/AlienLogicLab/alienintent/issues/50#issuecomment-5747068457) |
| 02:37:28 | Fresh independent verifier ACCEPTED `8689771b`. | [second review](https://github.com/AlienLogicLab/alienintent/issues/50#issuecomment-5747096363) |
| 02:40:33 | Closure stopped with `FOUNDER_EXCEPTION`; landing authority was absent. | [authority exception](https://github.com/AlienLogicLab/alienintent/issues/50#issuecomment-5747110661) |
| 03:11:05 | Founder recorded SWF-16 landing authority. | [Founder decision](https://github.com/AlienLogicLab/alienintent/issues/50#issuecomment-5747243829), [decision record](../../decisions/2026-09-20-wave1-closure-policy.md) |
| 03:14:14 | Closure recorded DONE after normal merge and required CI. | [DONE record](https://github.com/AlienLogicLab/alienintent/issues/50#issuecomment-5747257998) |

### B. Producer and verifier attempts

Two IMPLEMENT attempts published candidates. The first producer and first verifier invocations have durable `state.json` records, as do the repair producer and second verifier. The verifier reports a fresh worktree for both reviews. Two later PRODUCER invocations performed closure: the first stopped for authority, and the fresh second invocation completed it. Invocation IDs and timing are in the JSONL event records.

### C. Candidate lineage

`8a82e563` (release baseline) → `a82ca4e6` (rejected candidate) → `8689771b` (accepted repair candidate). Git confirms that `8689771b` is a parent of normal merge `ab4efe5`; its other parent is `c7870bc`. The accepted candidate therefore remains reachable in `main` ancestry. A fresh diff of `ab4efe5^2..ab4efe5` over `src`, `tests`, `pyproject.toml`, workflows, scripts, and `package.json` was empty during this reconstruction.

### D. Blocking B1/B2/B3 findings

- B1: rework lost the immutable bound contract, leaving the ordinary rework-to-DONE path unreachable.
- B2: the producer’s Python command depended on ambient `PYTHONPATH`; the complete PY-02 suite was not reached by CI.
- B3: mutation of WIP-limit logic did not turn the suite red, and equal-priority FIFO was not observed between admissible equal-priority items.

These are verifier observations, not retrospective inference. See the [first independent review](https://github.com/AlienLogicLab/alienintent/issues/50#issuecomment-5747048805).

### E. Repair actions and acceptance evidence

The repair candidate changed lifecycle and budget validation, clean-checkout pytest configuration, the Python CI workflow, and lifecycle/scheduling/trust tests. The second verifier independently reported that the B1 recovery path reached DONE, B2 clean-environment collection passed and CI reached the full suite, and B3 mutations each caused failure. See [candidate 2](https://github.com/AlienLogicLab/alienintent/issues/50#issuecomment-5747068457) and [second review](https://github.com/AlienLogicLab/alienintent/issues/50#issuecomment-5747096363).

### F. Authority interruption and closure actions

The first closure did not merge or mutate a Project item. It explicitly requested Founder authority for a normal merge of the exact accepted SHA. SWF-16 then authorized that merge and prohibited rebase, squash, rewriting the SHA, and candidate-content modification. The final closure record reports only the merge and necessary checks; deployment, release/publication, and live operational verification were unnecessary under the PY-02 contract. [Authority exception](https://github.com/AlienLogicLab/alienintent/issues/50#issuecomment-5747110661), [SWF-16](../../decisions/2026-09-20-wave1-closure-policy.md), [DONE record](https://github.com/AlienLogicLab/alienintent/issues/50#issuecomment-5747257998).

### G. Final outcome

Git shows merge `ab4efe54df752a4d7a35f047054435a24a21ddaf` with accepted `8689771b9fccb9f86c7fdcc2e9d4f571408765f2` as second parent. GitHub Actions independently reports both workflows successful on that merge: [Python architecture fitness](https://github.com/AlienLogicLab/alienintent/actions/runs/35485988926) and [offline verification](https://github.com/AlienLogicLab/alienintent/actions/runs/35485988931). The current Issue project item reports `DONE`.

## Derived measurements

- Total trajectory time: 3,788 seconds (release comment at 02:11:06Z to DONE comment at 03:14:14Z).
- Human-authority wait: 1,832 seconds (FOUNDER_EXCEPTION at 02:40:33Z to Founder authority at 03:11:05Z).
- Repair interval: 212 seconds (first REJECT comment to repair-candidate comment).
- Closure interval: 2,206 seconds (ACCEPT comment to DONE comment), including the authority wait.
- Initial and repair producer active durations sum to 978 seconds from `state.json`; this excludes verifier work, dispatch, and queue time.
- Closure command count: 46, as reported by the final closure worker.

These are timestamp arithmetic over cited observations. They are not worker cost or productivity measurements.

## Available cost and token evidence

The two verifier logs identify `firstParty` / `claude-opus-5`, with list-basis costs of $2.2140815 and $1.7851975 ($3.999279 known subtotal). All four producer logs also contain token-use fields, but do not provide provider/model identity or cost. The JSONL retains each invocation's native token fields and log path. Because producer costs are absent and the token schemas differ, end-to-end cost and a summed comparable token total are **UNKNOWN**.

## Unresolved or unknown data

- Producer provider-model identities and producer monetary cost are not recorded in the examined logs; end-to-end monetary cost is **UNKNOWN**, not zero.
- The local post-merge test/fitness/Node results are durable worker claims in the DONE comment, but this retrospective did not rerun them; Actions success is independently verified.
- No independent raw command transcript was needed to establish final candidate lineage or merge-result CI; where log content is referenced, its durable path is recorded in JSONL.
