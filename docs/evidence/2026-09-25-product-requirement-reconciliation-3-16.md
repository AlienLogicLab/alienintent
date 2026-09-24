# Product Requirement reconciliation: #3–#14 and #16 (cohort record)

Status: retained Factory Director record, 2026-09-25. Authority: Founder direction
`founder-backlog-reconciliation-20260924T132525Z` (Director inbox). It set the closure rule:

> A Product Requirement may reach DONE only when all currently authorized acceptance criteria are
> covered by retained executable feature-level regression evidence. Future or deferred extent
> must remain explicit and prevents full closure.

Method: for each requirement, one fresh bounded read-only specialist examined the evidence, and
the Factory Director validated the result. The Director rejected unsupported conclusions and
re-checked the cited evidence and tests. Each per-requirement record is an Issue comment. #3 was
reconciled by episode `factory-director-04b0d96a70f1423cac9fcc70ed9e238e`. #4–#14 and #16 were
reconciled by episode `factory-director-3b19543ca543423f8ef9791f7be8c90b`. Baseline `036c5fc`,
with no source change through `675cf10`. Director re-runs in this episode:
- `tests/execution_coordination/test_operational_store.py`, `test_decision_inbox.py` and
  `test_github_delivery_ingress.py`: 53 passed;
- `tests/control_plane` and `tests/installation/test_doctor.py`: 88 passed;
- the #4 specialist's run of 130 scheduling and release-admission tests also passed.

## Result

| Issue | Requirement | Classification | Reason not DONE / closure | Record |
|---|---|---|---|---|
| #3 | SF-REQ-001 continuous drain | PROVEN (bounded) + residual | Repeated nonterminal outcomes are routed to the proposed SF-REQ-022 extension (POSTW1-DECIDE-007A), a pending future extent | [#3](https://github.com/AlienLogicLab/alienintent/issues/3#issuecomment-5816932386) |
| #4 | SF-REQ-002 READY scheduling | PARTIAL | Canonical admission-gate migration is DEFERRED (BOOTSTRAP-M15); regression residuals go to #104 | [#4](https://github.com/AlienLogicLab/alienintent/issues/4#issuecomment-5823690498) |
| #5 | SF-REQ-003 Solve for N | PARTIAL | Configurable N is not reachable at feature level; captured as #103 | [#5](https://github.com/AlienLogicLab/alienintent/issues/5#issuecomment-5823697534) |
| #6 | SF-REQ-004 rolling refill | PROVEN + residual | Replayable live-adapter refill regression goes to #104 | [#6](https://github.com/AlienLogicLab/alienintent/issues/6#issuecomment-5823690868) |
| #7 | SF-REQ-005 Work Management abstraction | **PROVEN → DONE** | No deferred extent | [#7](https://github.com/AlienLogicLab/alienintent/issues/7#issuecomment-5823748767) |
| #8 | SF-REQ-006 human decision escalation | **PROVEN → DONE** | No deferred extent | [#8](https://github.com/AlienLogicLab/alienintent/issues/8#issuecomment-5823749155) |
| #9 | SF-REQ-007 candidate custody | **PROVEN → DONE** | No deferred extent; SWF-30 adds no obligation | [#9](https://github.com/AlienLogicLab/alienintent/issues/9#issuecomment-5823784631) |
| #10 | SF-REQ-008 crash-safe execution | PROVEN (current scope) | Proposed durability extension pending (POSTW1-DECIDE-007A) | [#10](https://github.com/AlienLogicLab/alienintent/issues/10#issuecomment-5823809219) |
| #11 | SF-REQ-009 deterministic kernel | PARTIAL | SWF-32 cycle counter is canonicalized but unscheduled (DEFERRED) | [#11](https://github.com/AlienLogicLab/alienintent/issues/11#issuecomment-5823828116) |
| #12 | SF-REQ-010 BIU contract model | PARTIAL (narrow) | Per-field rejection regression goes to #104 | [#12](https://github.com/AlienLogicLab/alienintent/issues/12#issuecomment-5823858422) |
| #13 | SF-REQ-034 Operator Control Plane | PARTIAL | P5 polish (replay, synthetic events, events/evidence/cost inspection) DEFERRED to Wave 6 | [#13](https://github.com/AlienLogicLab/alienintent/issues/13#issuecomment-5823870526) |
| #14 | SF-REQ-035 Decision Inbox | PROVEN (current scope) | Linked BOOTSTRAP-M05 `NEEDS_DECISION` and M04 SF-REQ-053 integration dependency remain open | [#14](https://github.com/AlienLogicLab/alienintent/issues/14#issuecomment-5823870897) |
| #16 | SF-REQ-038 doctor / validation | PARTIAL | The 2026-09-22 external-capability amendment is UNPROVEN; captured as #102 | [#16](https://github.com/AlienLogicLab/alienintent/issues/16#issuecomment-5823878894) |

## Cohort-level decisions

1. **Consistent closure treatment.** An open future extent attached to the requirement blocks full
   closure. This covers pending amendments (POSTW1-DECIDE-007A), canonicalized-but-unscheduled
   amendments (SWF-32), Wave 6 polish, and linked bootstrap-migration rows that are still open
   (M05 `NEEDS_DECISION`, M15). This is the conservative reading of "future or deferred extent
   must remain explicit and prevents full closure." #3, #10 and #14 therefore stay open even
   though their currently authorized criteria are PROVEN.
2. **Closure taken.** #7, #8 and #9 are fully PROVEN by retained executable feature regressions,
   backed by retained PY-10 live proof, and no deferred extent is attached to any of them. They
   were moved TASKS → DONE on Project #1, and canonical read-back was verified. The Issues stay
   open, which is the same open-DONE convention as LRN-016. Retained historical live proof was
   not invalidated merely because it was not rerun.
3. **Deduplicated Proposal Intake.** Only genuine gaps that no existing route covers were taken
   in, each at CAPTURE with canonical read-back:
   - #102: doctor validation of configured external capabilities (SF-REQ-038 amendment);
   - #103: reachable configurable concurrency policy (SF-REQ-003). The capability only; live WIP
     stays 1;
   - #104: feature-regression hardening for SF-REQ-002/004/010.

   No BIU was manufactured, and Wave placement remains Founder-reserved.
4. **Specialist conclusions rejected or corrected.**
   - "Closure-eligible" for SF-REQ-009, rejected because SWF-32 is deferred.
   - A proposed SF-REQ-034 `replay` verb as a new gap, rejected because it is already explicit
     P5 extent (PY-08 line 57).
   - An SF-REQ-010 "Founder question" about field enforcement, rejected: the enforcement is
     owned by sibling requirements.
   - SF-REQ-009 selection credit to the unwired `select_admissible`, re-credited to the
     production coordinator.
   - SF-REQ-004 live row PARTIAL, aligned with the #3 convention.
5. **No new Founder question and no hold.** The open decisions already exist on record:
   POSTW1-DECIDE-006A, POSTW1-DECIDE-007A, SWF-32 scheduling, and Wave placement of #102–#104.
   Nothing in current execution waits on them.

## Routing

Each specialist was a Claude Code Explore subagent with `sonnet` requested: the least-cost tier
tried first, with no capability escalation. Served model identifiers are not separately exposed.
Per-specialist tokens, tool uses and duration are recorded on each Issue; cost is UNKNOWN.
Lesson: JUDGMENT_ONLY. Separate retained feature proof, deferred extent and requirement closure.
No new enforcement is claimed.
