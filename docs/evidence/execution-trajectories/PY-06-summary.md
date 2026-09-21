# PY-06 execution trajectory

PY-06 ran from release at 2026-09-20T13:46:47Z to DONE at 15:59:06Z — 7,939 seconds. One authority interruption before any implementation, then five candidates, five independent verifications, four rejections. Accepted candidate `e6607486` landed by normal merge `896c0fe5`. The Issue stayed open for a further 20,997 seconds, which is the defect SWF-31 records.

Raw events: [`PY-06.jsonl`](PY-06.jsonl). Derived measures: [`../quality/PY-06-quality-evidence.json`](../quality/PY-06-quality-evidence.json).

## The baseline that did not exist

The release comment named `main @ 6a2d1e9`. That revision does not exist: `git cat-file -e 6a2d1e9^{commit}` fails and no ref advertises it. The first producer invocation refused to start, published nothing, and left its worktree clean. The coordinator corrected the record 106 seconds later, confirmed the SHA had never been produced by anything, and named the real baseline `93b9b096` — whose parent is the PY-05 landing merge `5b617a3`.

**Classification: this was not a missing-authority gap.** The coordinator recorded it as a transcription error in a durable contract field and explicitly stated that no Founder decision was required. Its own words: this is the class of defect candidate-identity discipline exists to catch, applied to the baseline rather than to a candidate. The producer's refusal was judged correct.

This is an authority *interruption* with zero Founder decisions. The distinction matters for factory yield: PY-02, PY-03 and PY-04 each consumed a genuine Founder decision; PY-05 through PY-09 consumed none.

## Cycles

| Cycle | Candidate | Verifier | Verdict | Blocking findings | pytest | Candidate vs parent |
|---|---|---|---|---:|---:|---|
| 1 | `e0709658` | `d5c6ca2c` | REJECT | 9 (F1–F9) | 94 | 11 files, +482/−0 |
| 2 | `d9537d1e` | `9a1977c4` | REJECT | 6 (G1–G6) | 99 | 12 files, +613/−1 |
| 3 | `38a317fc` | `3639e749` | REJECT | 5 (H1–H5) | 103 | 13 files, +769/−1 |
| 4 | `a7549b38` | `a09ade1f` | REJECT | 2 (J1–J2) | 107 | 15 files, +908/−2 |
| 5 | `e6607486` | `e006b0d9` | **ACCEPT** | 0 | 110 | 15 files, +962/−2 |

Findings fell 9 → 6 → 5 → 2 → 0 with **zero tests dropped in any cycle**, verified by the verifier diffing the test inventory against each previously rejected candidate. Every cycle's prior findings were independently re-executed as closed rather than accepted on the producer's word.

## The recurring failure class

The verifier named the same pattern in three consecutive cycles: **a correct domain object, a unit test of that object, and no executed path that uses it.** `RetrySchedule` existed with a test of its arithmetic and no call site. The verifier half of `ReservationBook` was correct in isolation and never reached by an invocation. `verify()` allocated a workspace it never used. The composition wiring for scope item 9 was outstanding for three cycles and, when it arrived, raised `TypeError` on its only intended use — passing 103 tests because no test and no caller ever supplied a worker.

This class is mechanically expressible (reachability of a production symbol from a composition root; a wiring path exercised by at least one test). It was discovered by model cognition four times and has not been promoted into a deterministic check. See [the factory-incident record](../wave1-factory-incidents-and-learning-PY-05-to-PY-09.md).

## Custody

PY-06 is where candidate custody proof became strong. At every cycle the verifier ran `git ls-remote` and a fresh `git clone --single-branch` into a clean directory and confirmed HEAD resolved to the exact claimed SHA. PY-05's verifier had retrieved candidates independently but did not perform that read-back, so PY-05's zero custody failures rest on weaker evidence than PY-06's.

Cycle 4's two blocking findings were both in the custody rejection paths and both latent: `J1`, the control-plane gate raising an untyped `FileNotFoundError` for unpublished and mismatched candidates, was byte-identical to the previous candidate and had been concealed by a malformed-locator negative control the previous verifier had already flagged as weak. **Custody still failed closed throughout** — the exception propagated out of `_launch` with no `except`, so no unretrievable candidate was admitted to VERIFY. What was missing was the *typed* rejection the criterion asks for.

## A real provider CLI

From cycle 3 the candidate retained `docs/evidence/PY-06-invocation-runtime.md`, and from cycle 4 the bounded `codex exec --ephemeral --json --sandbox read-only` smoke ran **through `CliWorkerProvider`** rather than beside it. The verifier reproduced that end to end with a real child process, real worktrees, publication and fresh-clone read-back. The reported cost is one bounded smoke invocation: 21,038 input and 56 output tokens, monetary cost unreported and retained as unknown. That is not the BIU's cost, and it is not zero.

## An unexplained gap

Candidate `d9537d1` was published at 14:19:20Z and its producer worktree exited at 14:19:27Z, but the next VERIFIER invocation did not start until 14:47:00Z — 1,653 seconds with no recorded actor. The liveness watch records no gap for issue 54 and the coordinator observation log does not begin until 15:32Z. **The cause is UNKNOWN.** It is the single largest unexplained interval in PY-05–PY-09.

## Landing

Normal merge `896c0fe5`, parents `89c930d1` and the accepted SHA. Re-verified in this extraction: reachable from `origin/main`, two parents, accepted SHA second, and `git diff e6607486 896c0fe5 -- src tests` empty. Required merge-result Actions — offline verification (run 35521121733) and architecture fitness (run 35521121734) — both succeeded.

## Worktree retention

Two PY-06 producer worktrees remain `RUNNING` in the dispatcher state record with the cleanup diagnostic "dirty worktree retained". That is binding rule 7 working as designed at the lifecycle level — a cleanup failure recorded as a resource diagnostic rather than a rewritten lifecycle result, which was F1, the first cycle's main defect. The underlying cause of the diagnostics is separately documented: `worktreeManager.cleanup()` passes `--ignored` to `git status`, so any worktree that has run the Python suite is reported dirty by its own `.pytest_cache/`. See the [worktree retention audit](../2026-09-20-worktree-retention-audit.md), which was conducted while PY-06 was live.
