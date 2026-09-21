# Wave 1 repair-cycle data — factory yield

First extraction 2026-09-21, corrected the same day: **PY-02 through PY-09**, 46 cycles, 8 BIUs. Machine-readable
records in [`wave1-repair-cycles.json`](wave1-repair-cycles.json); regenerate with

```
python3 ~/.local/share/alienintent-bootstrap/cycle_data.py 50 51 52 53 54 55 56 57 \
  --out docs/evidence/wave1-repair-cycles.json
```

This exists because **attention and measurement are different mechanisms**. The attention queue wakes
a coordinator when judgment is needed and deliberately stays quiet during healthy repair; that
threshold must never decide what gets recorded. Every cycle is measured whether anyone was woken or
not. Governing authority: SF-REQ-024 factory yield and [SWF-18](../decisions/2026-09-20-wave1-closure-policy.md)
closure-efficiency measurement — no new requirement.

## What the data says

| Metric | Value |
|---|---|
| Cycles observed | **46** across 8 BIUs |
| Verifier rejections | **31** |
| Authority blocks (`FOUNDER_EXCEPTION`) | **8** |
| **First-pass acceptances** | **0 of 7 accepted BIUs** |
| Rejections per accepted BIU | mean **4.0**, median 4.0, range **1–9** |
| Authority blocks per accepted BIU | mean **1.1** |
| Verification duration | median **530 s**, range 264–2013 s (n=38) |
| Implementation duration | median **690 s**, range 480–1230 s (n=7, PY-06 onward only) |
| Candidate size | median **149** added lines, max 600 (n=43) |

### Per BIU

| BIU | Cycles | Rejections | Authority blocks | Findings trajectory |
|---|---|---|---|---|
| PY-02 | 3 | 1 | 1 | — |
| PY-03 | 3 | 1 | 1 | 4 |
| PY-04 | 12 | **9** | 2 | 1 |
| PY-05 | 3 | 2 | 0 | 6 |
| PY-06 | 6 | 4 | 1 | 5 → 2 |
| PY-07 | 8 | 5 | 2 | 4 → 3 → 5 → 3 → 1 |
| PY-08 | 8 | 6 | 1 | 12 → 14 → 11 → 10 → 8 → **3** → 0 |
| PY-09 | 3 | 3 | 0 | 3 → (unreadable) → (unreadable) — **in flight** |

## Readings worth acting on

**Nothing has ever been accepted first-pass.** Not once in seven accepted BIUs. Rework is not an
exception in this factory, it is the normal path, and the interesting question is not *whether* a BIU
will be rejected but how many cycles it takes to converge.

**The spread is the signal, not the mean.** 1 to 9 rejections is nearly an order of magnitude. PY-04
(9) was the walking skeleton that defined the loop; PY-08 (6) mixed a command surface with proof
obligations. The cheap ones were narrow and well-bounded. Cycle count tracks *breadth of contract*
more than difficulty.

**Authority blocks are common and mostly cheap.** 8 blocks across 7 BIUs, averaging one per BIU. Most
resolved in a single coordinator response. They are not failures — they are the escalation path
working — but each one costs a full invocation, and at least two were caused by incomplete release
records rather than genuine authority gaps, which is what the
[SF-REQ-002 admission preconditions](../decisions/alienintent-software-factory-plan.md) now prevent.

**Verification is fast; implementation is slow.** Verify runs at a median 529 s against implement at
690 s, and verification is the step that catches defects. That ratio is an argument for verifying more
often rather than batching work into larger candidates.

**PY-08's trajectory is the clearest case in the dataset.** Findings rose before they fell
(12 → 14), plateaued (11 → 10 → 8), then fell to 3 and to 0 — the cycle directed to build
verification rather than repair implementation. That single data series is the evidence behind
[SWF-23 §4b verification-first repair sequencing](../decisions/2026-09-20-convergent-repair-monotonic-progress.md).

## Limits of this dataset — read before trusting a number

- **Findings counts are readable for 20 of 46 cycles (43%).** Verifier reports are prose and their
  formatting varies per cycle. Unreadable counts are recorded as **`"UNKNOWN"`** — the sentinel
  SF-REQ-030 and evidence-v1 both use, never `0` — and each record names its own gaps in
  `unknown_metrics`. Aggregates skip UNKNOWN by type, so a mean can never absorb an unmeasured cycle
  as zero.

- **Correction, 2026-09-21.** The first extraction over-counted findings in three cycles, reported by
  the PY-05–PY-09 extraction session. The scan counted finding identifiers wherever they appeared,
  including the sections where a verifier re-lists **prior** findings it is reporting as closed —
  PY-08 cycle 7 read 7 where 3 were open, and disagreed with this coordinator's own contemporaneous
  series (14 → 11 → 10 → 8 → 3). Fixed by counting only within a report's declared open-findings
  section, falling back to excluding recognisable closed sections, with an explicit closure heading
  taking precedence over one that merely mentions findings. PY-08 cycle 7 and PY-06 cycle 6 now
  extract correctly; PY-06 cycle 5 became `"UNKNOWN"` rather than wrong.
- **Implementation durations exist for only 7 cycles.** The observation log starts at PY-06; earlier
  timings are not recoverable. Verification durations come from the result-marker timestamps and cover
  37 cycles.
- **Cycle identity comes from the B-DISP result protocol**, not from report prose. Report titles vary
  across BIUs ("VERIFIER — PY-04 candidate … : ACCEPT", "PY-07 repair verification (cycle 6) — ACCEPT",
  "PY-09 independent verification — REJECT"), and an earlier extraction that keyed on titles silently
  produced records for only 2 of 8 BIUs. The marker is the same for every BIU, so it is the spine.
- **Candidate sizes are computed from Git**, not parsed from prose, and are measured against the
  candidate's parent.
- PY-09 is **in flight**; its row will change.

## What this does not yet measure

Token and monetary cost per cycle (the providers report it; nothing collects it here), first-pass rate
by contract breadth, and defects escaping to a later BIU. Those belong to the canonical factory-yield
capability in SF-REQ-024 rather than to this bootstrap extractor.
