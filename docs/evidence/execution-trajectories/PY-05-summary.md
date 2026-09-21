# PY-05 execution trajectory

PY-05 ran from release at 2026-09-20T12:31:38Z to DONE at 13:43:20Z — 4,302 seconds. Three candidates, three independent verifications, two rejections, no authority interruption, no liveness incident, no operator intervention. Accepted candidate `761bc21c` landed by normal merge `5b617a3e` and the Issue was closed one second after the DONE comment so the native blocked-by graph would admit PY-06.

Raw events: [`PY-05.jsonl`](PY-05.jsonl). Derived measures: [`../quality/PY-05-quality-evidence.json`](../quality/PY-05-quality-evidence.json).

## Baseline

The release comment states two different revisions and they are not interchangeable. The **BIU baseline** is `main` @ `3e57749`. The **Agent-Ready assessment baseline** is `0170af0`, the PY-04 landing merge. The earlier [`PY-05-release-snapshot.md`](PY-05-release-snapshot.md) reported `0170af0` as the release baseline; that is the assessment baseline, and this record supersedes that reading. The dispatcher state record independently confirms `3e5774967a16728542eed8a21b38471009dd28db` as the allocation baseline of the first two producer worktrees.

The release comment also records that SWF-26 — the temporary PY-04 coordinator mutation gate — expired at PY-04 DONE and does not apply here, and that generalizing it belongs to SF-REQ-050 through the normal requirement path.

## Cycles

| Cycle | Candidate | Verifier | Verdict | Blocking findings | pytest | Candidate vs parent |
|---|---|---|---|---:|---:|---|
| 1 | `deb4da34` | `3ad13d79` | REJECT | 6 | 79 | 12 files, +472/−5 |
| 2 | `66bd3c15` | `0922fe90` | REJECT | 1 | 87 | 13 files, +634/−6 |
| 3 | `761bc21c` | `a8768b3b` | **ACCEPT** | 0 | 87 | 13 files, +636/−6 |

The suite was green at every cycle. Both rejections are about what the green suite proves, not about a failing test.

Cycle 1's six findings were five behavioural defects plus one proof gap. Two of them are the same shape as the PY-02 lesson that was recorded as a candidate learning and never promoted: an acceptance criterion carried by an assertion that cannot fail. Finding 2 — the Anti-Corruption Layer rejecting any many-to-one upstream-to-neutral status mapping as ambiguous — foreclosed the BIU's primary function while every test passed.

Cycle 2's single finding is the sharpest evidence-quality observation in the BIU: production behaviour for AC 6's stale-revision fence was **correct**, confirmed by direct probe, but the test's stale call used an unmapped state so the assertions were overdetermined. Deleting the fence left all 87 tests green. The verifier applied the same standard it had applied to finding 1 the cycle before.

Cycle 3's repair was three insertions and one deletion in a single test. The verifier re-derived its own thirteen-mutation battery rather than trusting the previous cycle's table, confirmed the fence negative control now fails on the real defect, and checked the test inventory at both revisions: 77 each, none removed, none renamed.

## Evidence monotonicity

One test was removed between cycle 1 and cycle 2 — `test_many_to_one_status_mapping_is_rejected_as_ambiguous`, which locked in the inverted semantics that finding 2 identified. The verifier recorded it as **explicitly superseded and authorized** under SWF-23 §3 rather than as an evidence regression. That is the only supersession in PY-05 and the only one across PY-05–PY-09.

## Landing

Normal merge `5b617a3e`, parents `3d1e6dd` and the accepted SHA. Re-verified in this extraction: the accepted candidate is reachable from `origin/main`, the merge has exactly two parents with the accepted SHA as the second, and `git diff 761bc21c 5b617a3e -- src tests` is empty. Required merge-result Actions — offline verification (run 35514111318) and Python architecture fitness (run 35514111319) — both succeeded.

## Observation and verdict kept distinct

The producer reported `npm test` as 310 passing in all three result comments. The verifier independently observed 330 pass / 0 fail in all three verifications. Exit status was 0 either way and the verifier recorded the discrepancy as non-blocking each time. Both numbers are observations; neither is a verdict. The same discrepancy recurs through PY-06.

## Telemetry not available

The dispatcher state record carries no provider or model field, so the identity of the model that ran each invocation is **UNKNOWN**. Token usage and monetary cost are **UNKNOWN**. The coordinator attention queue does not begin until 2026-09-20T17:08:53Z, after PY-05 reached DONE, so attention coverage for this BIU does not exist — that is absent telemetry, not an observed count of zero.
