# POSTW1-BOOTSTRAP-006 — Bootstrap Retirement / Transition Audit

Fresh Codex GPT-6 Astra. Repository root, `workspace-write`, escalated solely for the two
deliverables in §5. **Risk: HIGH where removing a known protection.** Coordinator review follows.

## 1. Why you are the author and not the coordinator

The program plan routes this phase to you with coordinator review, and the Director's own routing
table was corrected to match after it disagreed. The reason matters: the resident Claude
coordinator **is the mechanism under audit**. Its tenure, its attention waiter, its release
authority and its provider change are all on the audit list. A participant authoring its own
retirement audit is the authorship conflict Phase 2 named. Its lived context is supplied to you
as evidence; it is not authorship, and you should weigh it as testimony.

## 2. Objective

Retire temporary controls safely, and avoid accidental permanent bootstrap architecture.

> **Do not retire by date. Retire by replacement.**

Exit gate: **no temporary mechanism quietly becomes permanent, and no known protection disappears
before its replacement is operational.**

## 3. You may not act. Audit and recommend only.

This phase produces a matrix and a transition plan. It stops no service, changes no profile,
reverts no provider configuration and retires no authority. The Founder's standing instruction
from the pre-mortem is explicit on that point and has not been lifted. The autonomous execution
amendment §9 permits autonomous retirement *only* where existing authority explicitly permits it
and replacement criteria are proven — and where removal would change protection or authority with
no decision authorizing it, the disposition is `NEEDS_DECISION`, not action.

## 4. Inputs

**Live operating state** —
`docs/operations/post-wave1-program/prework/POSTW1-BOOTSTRAP-006-live-state.json`. This is not in
the repository anywhere else: four systemd units are running, the live worker provider
configuration is recorded with the path that reads it, the attention queue is drained, and
eighteen bootstrap modules live outside the repository. Each value names the command that
produced it.

**Prior participant record** — `docs/evidence/2026-09-21-bootstrap-expiry-inventory.md`. Written
by the coordinator during the pre-mortem, labelled participant evidence. Treat its dispositions
as claims to corroborate, not as findings.

**Learning Ledger** — `docs/evidence/wave1-learning-ledger.json`, particularly LRN-020
(temporary-authority-expiry), LRN-026 (bootstrap-mutation-gate-tenure, already BOOTSTRAP_ONLY),
LRN-027 (coordinator-replacement-continuity) and LRN-019 (observation-without-activation).

**Decisions** — SWF-21, SWF-26, SWF-27, SWF-29, SWF-08 and the amendments in `docs/decisions/`.

## 5. Audit at minimum

`SWF-21 release authority` · `SWF-29 liveness reconciliation` · `SWF-27 observer` ·
`attention queue` · `Windows notification` · `session-bound attention waiter` ·
`coordinator checkpoint` · `PRODUCER-on-Claude temporary profile change` ·
`Node/bootstrap execution authority` · **and any other explicitly temporary mechanism you find**.

The live-state file names two the inventory may not cover: the **sandbox ingress tunnel**, whose
unit description says "SWF-08, temporary Wave 1 infrastructure" and which is still running with
Wave 1 and PY-10 closed; and the **eighteen bootstrap modules outside the repository**, which no
repository artifact governs or tests. Decide for yourself whether each is in scope.

### Per mechanism

```
mechanism  purpose  demonstrated_failure_prevented  authority  stated_expiry_condition
replacement_requirement  replacement_implemented  bootstrap_still_operating
recommended_disposition  evidence
```

`demonstrated_failure_prevented` must cite evidence that the mechanism actually prevented
something, or say it did not. A control that never fired has not demonstrated its value, and that
is a finding either way — it does not by itself justify retirement, because an unfired protection
may simply not have been tested.

### Dispositions — exactly one per mechanism

```
RETIRE_CANDIDATE        purpose complete and no protection is lost
KEEP_UNTIL_REPLACED     still the only thing providing this protection
REVERT_TEMPORARY_CHANGE a narrow change outlived its authorization
NEEDS_DECISION          removal changes protection or authority with no decision authorizing it
```

### Specific guidance from the plan

- **SWF-21**: Wave 1 release purpose is likely complete. **Do not assume it carries into Wave 2.**
- **SWF-29**: do not recommend removal before SF-REQ-056 or an equivalent replacement is
  *actually operational* — not merely specified.
- **Session-bound waiter**: may retire with the resident coordinator if no longer needed.
- **Persistent observer / attention queue**: evaluate replacement separately from each other.

## 6. Deliverables

- `docs/evidence/wave1-bootstrap-retirement-matrix.json` (authoritative)
- `docs/evidence/wave1-bootstrap-retirement-matrix.md` (prose companion)

The JSON must carry `mechanisms` (one entry per mechanism with the ten fields), a
`transition_plan` giving the safe order of retirement with its dependencies, and a provenance
block. For every `RETIRE_CANDIDATE`, state explicitly what protection is *not* lost.

## 7. Acceptance

```
python3 tools/evidence/check_retirement_matrix.py docs/evidence/wave1-bootstrap-retirement-matrix.json
python3 tools/evidence/check_wave1.py --negative-controls
```

The checker enforces: all ten fields per mechanism; every listed mechanism covered; a valid
disposition; `RETIRE_CANDIDATE` requires `replacement_implemented` true **or** an explicit
statement that no protection is lost; `REVERT_TEMPORARY_CHANGE` requires a stated expiry
condition; and a transition plan ordering every non-retained mechanism. It treats
`"none — <why>"` as absence.

Do not edit any checker. **If you believe a check is wrong, say so in `DISPUTED` and leave it
failing.** Three predecessors disputed checks; all three were upheld and two found real defects.

## 8. Out of scope

Take no retirement action of any kind. Do not create, amend or weaken any Product Requirement.
Do not modify prior evidence, lifecycle state, Project state, worker contracts or Node/B-DISP
semantics. Do not `git commit`, push, or use the network. Do not begin Phase 7.

## 9. Terminal report — this block only

```
MECHANISMS_AUDITED=<n>
RETIRE_CANDIDATE=<n> KEEP_UNTIL_REPLACED=<n> REVERT_TEMPORARY_CHANGE=<n> NEEDS_DECISION=<n>
STILL_OPERATING=<n>
NEVER_FIRED=<mechanisms with no demonstrated prevented failure, or NONE>
OUT_OF_SCOPE_FOUND=<mechanisms you found that the plan did not list, or NONE>
TRANSITION_PLAN_STEPS=<n>
MATRIX_CHECK=PASS|FAIL
WAVE1_CHECK=PASS|FAIL
DISPUTED=<or NONE>
NOTES=<one line, or NONE>
```
