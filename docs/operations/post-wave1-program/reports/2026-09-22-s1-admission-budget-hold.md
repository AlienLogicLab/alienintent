# WO-220102 / S1 admission — budget authority hold

Status: **ENGINEERING_ADMISSION_HOLD**, critical path to S1 → S2 → C1.
Source baseline: `9174849713df2685117de7a8150126d916a4b644`.
This is an operator admission record, not a new BIU, requirement, Agent Ready
assessment or lifecycle verdict.

## Definition

The approved candidate `docs/evidence/wave2-candidate-bius.json` identifies
WO-220102 as S1, typed immutable evidence and neutral references. It depends only
on WO-220101 and has no declared product/design authority gap or gate. Its budget
requires an explicitly authorized execution packet; the planning artifact grants
zero implementation invocations and allocates no numeric execution allowance.

[SWF-09](../../../decisions/2026-09-20-wave1-plan-approval-d1-d2.md#swf-09--d-2-budget-policy)
states: “For current CLI worker providers, the default hard-enforced dimensions
are” and includes “wall-clock duration”. It further states: “a hard-required budget
dimension is never silently downgraded to telemetry.”

[SWF-35](../../../decisions/2026-09-22-wave2-incremental-release-authority.md)
grants standing incremental release only with a fully bound execution packet and
no unresolved budget authority. It does not amend SWF-09. No repeat approval of
SWF-35 is requested.

## Observation

- S0 reached Project DONE, terminal comment
  https://github.com/AlienLogicLab/alienintent/issues/69#issuecomment-5780228636 .
  Issue #69 was then closed under SWF-31. Accepted SHA
  `761a3cb4d6e24dc24ec370de45e25fe8c505eeda` is in main ancestry through PR #70,
  merge `9174849713df2685117de7a8150126d916a4b644`.
- Both exact-merge workflows succeeded: 35754774665 and 35754774927.
- The Project's full 68-item inventory contains no WO-220102 issue. S1 is next by
  the approved S0 → S1 → S2 → C1 chain, but not admitted or READY.
- The live Codex profile retains the same bootstrap launcher. Inspection of
  `src/runtime/worker-runner.mjs` shows `spawn` without a worker-duration timeout;
  `src/providers/codex.mjs` admits model selection but no duration option;
  dispatcher inspection timers check liveness, not a per-invocation deadline.
- S0's allocation explicitly records `wall_clock.status = NOT_ENFORCED` and
  `enforcement = NONE_IN_BOOTSTRAP`. S0 subsequently received explicit Founder
  release. That historical acceptance and completed closure remain intact.
- Searches of current decision records and Director operational records found no
  general waiver applying that duration exception to S1 or later Wave 2 units.

## Verdict and bounded repair

S1's predecessor is satisfied; release admission is held on the mismatch between
the default hard duration requirement and actual provider enforcement. The
Director cannot silently inherit S0's exception or claim a timer exists.

Independent review `/root/s1_admission_review` found that the first draft's
mandatory Founder gate was premature. Architecture Authority §42 and SWF-01
already permit critical bootstrap repairs needed to keep the temporary control
plane operational; the governing directive authorizes in-scope repairs. The
Director verified those exact source passages and accepted the finding.

Disposition: retain SWF-09 and prepare a bounded critical-bootstrap repair with
an explicit positive duration and safe owned-process-tree cancellation/custody.
Required design checks include enforcement independent of a blocked dispatcher,
surviving descendants after provider exit, and no unrelated process termination.
The repair stays outside S1's product extent. Test-first implementation and fresh
independent review precede LAND; actual live configuration/activation remains a
separate authority check against the concrete reviewed change. Do not manufacture
a Founder decision merely because an implementation defect exists.

An alternative requiring explicit Founder risk acceptance would be a **S1-only**
exception to hard duration enforcement, retaining cancellation, concurrency and
attempt/retry controls and recording the enforcement limitation honestly. This
would not waive the requirement for later units. No such waiver is requested
while an authorized engineering repair remains viable.

No S1 implementation, provider invocation, candidate, readiness assessment or
Project mutation was created. After the enforcement prerequisite, bind the packet at the current
baseline, obtain native Agent Ready assessment for S1, run release admission, and
use the existing dispatcher under SWF-35. Do not redo S0 or re-specify the Wave.
