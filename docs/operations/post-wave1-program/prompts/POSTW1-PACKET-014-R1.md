# POSTW1-PACKET-014-R1 — final report accuracy repair

Fresh Codex GPT-6 Astra. `workspace-write`, solely for
`docs/operations/post-wave1-program/reports/FINAL-REPORT.md` and
`docs/evidence/wave2-founder-approval-packet.json`.

## 1. The accuracy check, and whose fault the findings are

An independent fresh Claude session checked 108 figures in your report against their sources. It
confirmed the things that mattered most: zero-READY is stated plainly, UNKNOWN is preserved
throughout, no causal claim exceeds HYPOTHESIS, the coordinator's self-assessment is labelled as
participant evidence, and recommendations are marked as recommendations. Full verdict:
`docs/operations/post-wave1-program/reports/POSTW1-PACKET-014-accuracy-raw.txt`.

It returned `CORRECTIONS_REQUIRED` on four figures and three framing points.

**Three of the four are the Director's fault, not yours.** Your three disputes (ORCH014-001,
ORCH014-002, STATE014-001) were all upheld. The Director then corrected the orchestration record
and the programme state *after* you had written the report. Your report accurately described the
record as it stood when you read it; the record then changed underneath it. That is a sequencing
error by the Director, and it is recorded here rather than passed to you as your defect.

## 2. The stale figures — update to current state

- **Disputes.** The report says four dispatched-session disputes, all upheld. The record now says
  **seven raised and seven upheld** — the original four plus your ORCH014-001, ORCH014-002 and
  STATE014-001.
- **Coordinator error count.** The report says the record reports eight errors. The record now
  reports `count: "AMBIGUOUS — corrected"`, with `surface_read_error_count: 8`,
  `logic_error_count: 4`, and `unique_combined_count: "UNKNOWN"` because overlap was never
  assessed. Neither 8 nor 12 is exhaustive; report it as found-not-total.
- **ORCH014-002 is repaired, not live.** The report presents the VERIFY-010 reviewer provenance
  discrepancy as open and needing Founder follow-up. It has been fixed:
  `tasks['POSTW1-VERIFY-010'].routing.model` is now `null` with
  `provider: "claude (fresh session); exact model UNKNOWN"`, and the underlying defect — `route()`
  assigning the resolved Codex model to the fresh-reviewer tier — was fixed in `director.py`
  test-first. Remove it from optional follow-ups and record it as found-and-repaired.
- **STATE014-001** is likewise reconciled: the record now distinguishes the pre-packet population
  (23 tasks, 12 Codex-primary) from current (24, 13).

## 3. The genuine figure error

**Checker attribution.** The report credits this programme with twelve deterministic checkers.
`tools/evidence/check_wave1.py` predates it — it was built during the Phase 0/1 evidence pass.
**Eleven** were built during phases 2–13. Correct the attribution and keep the twelve-passing
figure separate from the eleven-built figure; they are different claims.

## 4. The framing points — all three are fair

- **Programme state was changed.** Your preamble states the task prohibited programme-state
  changes. It did, and you honoured it — but `program-state.json` was modified in the working tree
  by the Director after your run. Say so explicitly rather than leaving a constraint statement that
  the repository contradicts.
- **The two ORCH014 disputes are presented as unreconciled.** They are reconciled. See §2.
- **Section 2 versus Section 5 on the checkers.** Section 2 lists twelve as what "the programme
  produced" while Section 5 calls them "twelve existing programme checkers". Make the two sections
  agree, using the corrected attribution.

## 5. Scope

Revise those two files only. Do not change any evidence artifact, prior deliverable, Wave 1
evidence, lifecycle state, Project state or worker contracts. Do not `git commit`, push, or use
the network. Do not begin Wave 2.

## 6. Acceptance

`python3 tools/evidence/check_wave1.py --negative-controls` must still pass. Do not edit any
checker. **Dispute anything you believe wrong** in `DISPUTED` and leave it unrepaired — seven of
seven disputes in this programme have been upheld, three of them yours.

## 7. Terminal report — this block only

```
DISPUTES_FIGURE=<updated to n>
ERROR_COUNT_FIGURE=<how stated now>
ORCH014_002_STATUS=<repaired | still_listed_open>
CHECKER_ATTRIBUTION=<built n, passing n>
STATE_CHANGE_DISCLOSED=yes|no
SECTIONS_RECONCILED=<n of 3 framing points>
WAVE1_CHECK=PASS|FAIL
DISPUTED=<or NONE>
NOTES=<one line, or NONE>
```
