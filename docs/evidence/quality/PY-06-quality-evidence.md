# PY-06 quality evidence

Derived from [PY-06-quality-evidence.json](PY-06-quality-evidence.json), reconciled against [the trajectory](../execution-trajectories/PY-06.jsonl) by a deterministic consistency check. Not a raw authority source.

## What it was trying to prove

The Python invocation runtime for real CLI workers under explicit grants and fail-closed budgets, with candidate custody enforced in the control plane — VERIFY requires an exact published revision independently read back from a fresh checkout. SF-REQ-007 primary.

## Verdict

`ACCEPTED_AND_DONE` after one authority interruption, four independent rejections and four repair cycles. Landed by normal merge `896c0fe5`; both required merge-result Actions succeeded.

| Measure | Value |
|---|---:|
| Verifier cycles / rejections | 5 / 4 |
| Blocking findings by cycle | 9 → 6 → 5 → 2 → 0 |
| Tests dropped in any cycle | 0 |
| Proof regressions | 0 |
| Behavioural regressions | 0 |
| Authority interruptions | 1 |
| Founder decisions required | **0** |
| Liveness incidents | 0 |
| Release → DONE | 7,939 s |
| Tests at landing | 110 |

## How difficult convergence was

Steady and monotonic. Findings fell every cycle, no test was ever dropped, and every prior finding was independently re-executed as closed rather than accepted on the producer's word. The final repair was five source lines across two files. Repair mode: **CONVERGING**.

## Major failure classes

Nine `BEHAVIORAL_DEFECT`, seven `EVIDENCE_PROOF_DEFECT`, four `ARCHITECTURE_CONFORMANCE`, two `CUSTODY_IDENTITY_DEFECT`. Two non-delegated binding rules were violated in the real path at cycle 1 — a cleanup failure erasing a published candidate, and grant expiry dead behind a hardcoded `now=0`.

**The recurring class is the one worth acting on:** *a correct domain object, a unit test of that object, and no executed path that uses it.* Named by the verifier in three consecutive cycles. It is mechanically expressible and has not been mechanized.

## What verification contributed

Everything material. Each rejection was proven by execution against real worktrees, a real remote and a real fresh clone, not by reading. Cycle 4's two findings were **latent** — byte-identical to the previous candidate and concealed by a negative control the previous verifier had already flagged as weak. A weak negative control hid a real defect for a full cycle.

## Regressions and monotonicity

None. Zero tests dropped across four repair cycles, verified by inventory diff each time. The accepting verifier proved both new tests red by reverting only the two repaired source files.

## Founder authority

None required. The single `FOUNDER_EXCEPTION` was a producer refusing a release record whose baseline SHA had never existed. The coordinator classified it as its own transcription error, not a missing-authority gap, and supplied the correct baseline in 106 seconds. The producer's refusal was judged correct.

## Did the factory malfunction

Yes, twice, both outside the BIU's own scope:

- the coordinator wrote a nonexistent baseline SHA into a durable contract field;
- worktree cleanup treated gitignored `.pytest_cache/` as uncommitted work, making every worktree that ran the suite permanently un-removable. Audited while PY-06 was live.

And one unexplained control-plane interval: **1,653 seconds** between candidate publication and the next verifier launch, cause **UNKNOWN**.

## Lessons

- **CANDIDATE LEARNING — NOT PROMOTED:** candidate-identity discipline applies to the *baseline* as well as the candidate. A release record naming an unresolvable revision should be refused mechanically. *(Since mechanized for release admission — see the factory-incident record.)*
- **CANDIDATE LEARNING — NOT PROMOTED:** a production symbol unreachable from any composition root is not implemented, whatever its unit tests say.
- **CANDIDATE LEARNING — NOT PROMOTED:** a negative control that passes for the wrong reason conceals the defect it appears to cover. Flagging one as "weak" should oblige repair, not a note.

## Unknown

Provider and model identity of the PRODUCER and VERIFIER invocations, end-to-end token usage and monetary cost are **UNKNOWN**. The only token figures observed (21,038 in / 56 out) are one bounded `codex exec` provider smoke, not the BIU. Attention-queue coverage for PY-06's window does not exist.
