# Product Requirement reconciliation: cohort summary (#3–#14, #16)

Status: retained Factory Director cohort-level summary, 2026-09-25. Episode
`factory-director-4370af4e4d824430a4f3a580cf207686`.

Authority:
- `founder-backlog-reconciliation-20260924T132525Z` (Director inbox): the campaign, its method and
  its closure rule.
- `founder-reconciliation-completion-rule-20260924T232150Z` (Director inbox): the completion rule and
  the required contents of this summary.

This summary covers the whole cohort. The detailed cohort record is
[`2026-09-25-product-requirement-reconciliation-3-16.md`](2026-09-25-product-requirement-reconciliation-3-16.md)
(landed at `92ea1b5`). Each per-requirement result is a Director-validated Issue comment. This
episode re-read all 13 comments by id. Each exists on its own Issue and was posted by the operator
login `sanookdu`.

Campaign state: **RECONCILIATION_COMPLETE**. All 13 target requirements have a retained,
Director-validated reconciliation result, listed below.

## 1. Per-requirement result

| Issue | Requirement | Classification | Explicit remaining extent | Board | Retained result |
|---|---|---|---|---|---|
| #3 | SF-REQ-001 continuous drain | PROVEN (bounded) + residual | Bounded disposition of repeated nonterminal `ineligible`/`rework` outcomes (the starvation class from PY-10 §7.1). Owned by the proposed SF-REQ-022 extension, POSTW1-DECIDE-007A (pending, unapproved) | TASKS | [comment 5816932386](https://github.com/AlienLogicLab/alienintent/issues/3#issuecomment-5816932386) |
| #4 | SF-REQ-002 READY scheduling | PARTIAL | (a) Canonical release-admission criteria F–K live only in the bootstrap gate. That is DEFERRED under BOOTSTRAP-M15 / POSTW1-DECIDE-006A. (b) Regression residuals E (priority is never invented) and K (no launch after a refused admission) are in #104 | TASKS | [comment 5823690498](https://github.com/AlienLogicLab/alienintent/issues/4#issuecomment-5823690498) |
| #5 | SF-REQ-003 Solve for N | PARTIAL | Configurable N is not reachable at feature level (`ReservationBook(1, 2)` constants; `select_admissible` is unwired). In #103. Live WIP stays 1 | TASKS | [comment 5823697534](https://github.com/AlienLogicLab/alienintent/issues/5#issuecomment-5823697534) |
| #6 | SF-REQ-004 rolling refill | PROVEN + residual | Replayable regression of refill through the real GitHub Work Management adapter. In #104 | TASKS | [comment 5823690868](https://github.com/AlienLogicLab/alienintent/issues/6#issuecomment-5823690868) |
| #7 | SF-REQ-005 Work Management abstraction | PROVEN | None | DONE | [comment 5823748767](https://github.com/AlienLogicLab/alienintent/issues/7#issuecomment-5823748767) |
| #8 | SF-REQ-006 human decision escalation | PROVEN | None | DONE | [comment 5823749155](https://github.com/AlienLogicLab/alienintent/issues/8#issuecomment-5823749155) |
| #9 | SF-REQ-007 candidate custody | PROVEN | None (SWF-30 adds no obligation) | DONE | [comment 5823784631](https://github.com/AlienLogicLab/alienintent/issues/9#issuecomment-5823784631) |
| #10 | SF-REQ-008 crash-safe execution | PROVEN (current scope) | Proposed durability extension: budgets, retries, attention acknowledgements, snapshot/effect receipts. Owned by POSTW1-DECIDE-007A (pending, unapproved) | TASKS | [comment 5823809219](https://github.com/AlienLogicLab/alienintent/issues/10#issuecomment-5823809219) |
| #11 | SF-REQ-009 deterministic kernel | PARTIAL | SWF-32 BIU execution-cycle counter is canonicalized but unscheduled. DEFERRED pending Founder scheduling | TASKS | [comment 5823828116](https://github.com/AlienLogicLab/alienintent/issues/11#issuecomment-5823828116) |
| #12 | SF-REQ-010 BIU contract model | PARTIAL (narrow) | Per-field missing-field rejection regression; the `completion_criteria`/`required_closure_actions` overlap; `candidate_custody_requirements` vs `CandidateRef` cross-check. In #104 | TASKS | [comment 5823858422](https://github.com/AlienLogicLab/alienintent/issues/12#issuecomment-5823858422) |
| #13 | SF-REQ-034 Operator Control Plane | PARTIAL | P5 polish: replay, synthetic events, inspection of events/evidence/cost, dashboards. DEFERRED to Wave 6 (PY-08 line 57; PROP-2026-0010) | TASKS | [comment 5823870526](https://github.com/AlienLogicLab/alienintent/issues/13#issuecomment-5823870526) |
| #14 | SF-REQ-035 Decision Inbox | PROVEN (current scope) | Linked BOOTSTRAP-M05 (`NEEDS_DECISION`) and the M04 SF-REQ-053 integration row are still open | TASKS | [comment 5823870897](https://github.com/AlienLogicLab/alienintent/issues/14#issuecomment-5823870897) |
| #16 | SF-REQ-038 doctor / validation | PARTIAL | The 2026-09-22 external-capability amendment is UNPROVEN, with no existing route. In #102 | TASKS | [comment 5823878894](https://github.com/AlienLogicLab/alienintent/issues/16#issuecomment-5823878894) |

Board states were read back from Project #1 by this episode on 2026-09-24 at about 23:40Z.

## 2. Deduplicated residual inventory

Each residual is listed once, with the requirements it affects.

| # | Residual | Requirements | Kind | Owner |
|---|---|---|---|---|
| R1 | Bounded disposition of repeated nonterminal outcomes (retry/run budget) | #3 | Substantive capability (unapproved extension) | POSTW1-DECIDE-007A (proposed SF-REQ-022 extension) |
| R2 | Durability of budgets, retries, attention acknowledgements, snapshot/effect receipts | #10 | Substantive capability (unapproved extension) | POSTW1-DECIDE-007A (proposed SF-REQ-008 extension) |
| R3 | Canonical replacement of the bootstrap release-admission gate (criteria F–K) | #4 | Substantive capability (deferred migration) | BOOTSTRAP-M15, KEEP_UNTIL_REPLACED; POSTW1-DECIDE-006A |
| R4 | Reachable configurable concurrency policy (N > 1 when configured) | #5 | Substantive capability (missing) | Proposal #103 (CAPTURE) |
| R5 | Doctor validation of configured external capabilities (Agent Ready first) | #16 | Substantive capability (missing, authorized text) | Proposal #102 (CAPTURE) |
| R6 | SWF-32 BIU execution-cycle counter in the canonical kernel | #11 | Substantive capability (deferred) | SWF-32, pending Founder scheduling |
| R7 | Control-plane P5 polish: replay, synthetic events, events/evidence/cost inspection, dashboards | #13 | Substantive capability (deferred) | Wave 6 (Founder-set); PY-08 line 57; PROP-2026-0010 |
| R8 | Decision Inbox linked bootstrap-migration rows | #14 | Migration / integration dependency | BOOTSTRAP-M05 (`NEEDS_DECISION`); M04 SF-REQ-053 integration row (open) |
| R9 | "Priority is never invented" negative regression | #4 | Closure / regression-proof | Proposal #104 item 1 |
| R10 | "No launch after refused admission" regression | #4 | Closure / regression-proof | Proposal #104 item 1 |
| R11 | Replayable live-adapter refill regression | #6 | Closure / regression-proof | Proposal #104 item 2 |
| R12 | Per-field contract rejection regression, plus the two contract-model observations | #12 | Closure / regression-proof | Proposal #104 item 3 |

### 2a. Closure and regression-proof gaps

R9–R12. In each case the behaviour exists and is enforced or proven once, but no discriminating
executable feature regression holds it. All four are deduplicated into one proposal, **#104**.
Closing them adds proof, not product capability.

### 2b. Missing or deferred product capability

R1–R8. Of these, only **R4 (#103)** and **R5 (#102)** had no existing route. R1, R2, R3, R6, R7 and
R8 are already owned by an existing decision, migration row or Wave assignment (section 3), so no
proposal was created for them.

## 3. Existing gates that already own a residual

These already own a residual. They must not be duplicated by a new proposal:

- **POSTW1-DECIDE-007A** (pending): R1 and R2. The specified-requirements record forbids inventing a
  run/retry budget policy or treating the proposed receipt model as approved scope.
- **POSTW1-DECIDE-006A** with **BOOTSTRAP-M15** (KEEP_UNTIL_REPLACED): R3. The 2026-09-22
  release-authority decision says "replacement, not elapsed time, retires it."
- **SWF-32** (canonicalized, scheduling Founder-reserved): R6.
- **Wave 6 / SF-REQ-036** (Founder-set timing): R7.
- **BOOTSTRAP-M05** (`NEEDS_DECISION`) and **M04** (SF-REQ-053 integration, open): R8.

## 4. Confirmations

1. **No Product Requirement was closed merely because implementation BIUs were DONE.** #7, #8 and #9
   moved TASKS → DONE only because every currently authorized criterion is PROVEN by retained
   executable feature-level regressions, backed by retained PY-10 live proof, and no deferred or
   pending extent is attached to any of them. Every other requirement stays open. That includes
   #3, #10 and #14, whose currently authorized criteria are PROVEN but which carry linked open
   extent.
2. **No reconciliation-derived proposal was prioritized before cohort completion.** Intake happened
   once, at cohort level and after all 13 results existed: #102, #103 and #104, each at CAPTURE with
   canonical read-back. Per-requirement records retained their candidates "for deduplicated
   cohort-level Proposal Intake" rather than taking them in individually. By Project #1 read-back
   at this summary, #102, #103 and #104 are still CAPTURE. None has been advanced, placed in a Wave,
   prioritized, or turned into a BIU. No DAG or priority change was made.
3. No new Founder hold was created by the reconciliation. The open decisions in section 3 already
   exist on record.

## 5. Proposal candidates ready for Founder backlog prioritization

After deduplication, the full set is:

| Proposal | Scope | Residuals | Kind |
|---|---|---|---|
| [#102](https://github.com/AlienLogicLab/alienintent/issues/102) | Doctor validation of configured external capabilities (SF-REQ-038 amendment) | R5 | Missing capability; the only authorized criterion with no route |
| [#103](https://github.com/AlienLogicLab/alienintent/issues/103) | Reachable configurable concurrency policy (SF-REQ-003). The capability only; live WIP stays 1 | R4 | Missing capability |
| [#104](https://github.com/AlienLogicLab/alienintent/issues/104) | Feature-regression hardening for SF-REQ-002/004/010 | R9–R12 | Closure / regression proof |

Existing decisions that bear on the remaining requirement closures, which the Founder may choose
to take up at the same time: POSTW1-DECIDE-007A (#3, #10), POSTW1-DECIDE-006A (#4) and SWF-32
scheduling (#11). Wave placement and priority of #102–#104 remain Founder-reserved. This summary
does not authorize lifecycle closure, proposal prioritization or BIU creation.

## 6. Method and lesson

The method was one fresh, bounded, read-only specialist per requirement, with Director validation;
details are in the cohort record. The summary itself is deterministic: it was assembled from the
13 retained Issue comments, the cohort record, and a Project #1 read-back. No specialist was used
for it.

Lesson: JUDGMENT_ONLY. Keep three things separate: retained feature proof, attached deferred
extent, and requirement closure. No new enforcement is claimed.
