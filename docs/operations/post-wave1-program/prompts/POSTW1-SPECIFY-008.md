# POSTW1-SPECIFY-008 — Wave 2 Requirement Inventory + SPECIFY

Fresh Codex GPT-6 Astra. Repository root, `workspace-write`, for the deliverables in §6.
Coordinator review is targeted: only where a requirement depends on Wave 1 historical behaviour.

## 1. Objective

Determine the **actual** Wave 2 candidate set — evaluate, do not assume — and fully specify each
selected requirement before any design work.

Exit gate: every selected candidate is sufficiently specified for Design Contract work, and **no
unresolved product intent is hidden in design**.

## 2. Two findings from deterministic prework that shape this phase

`docs/operations/post-wave1-program/prework/POSTW1-SPECIFY-008-inputs.json`.

**There is no single requirement register.** Definitions take three forms: 50 as factory-plan
headings, 3 as "Canonical requirement: **SF-REQ-NNN**" inside decision records, 1 as "Recorded as
**SF-REQ-NNN — …**". 56 ids are referenced; 53 are defined in some form. An inventory that searches
only headings under-counts — the Director's first pass did exactly that and was corrected. Whether
a requirement register is itself a Wave 2 candidate is a fair question for you to raise.

**Three ids are defined in no form at all: `SF-REQ-048`, `SF-REQ-052`, `SF-REQ-056`.** The third is
on your candidate list. SWF-29 names SF-REQ-056 as the capability whose arrival expires the
bootstrap liveness watcher and narrows what it must do, but nothing specifies it — and Phase 6 left
SWF-29 `KEEP_UNTIL_REPLACED` on exactly that basis.

So specifying SF-REQ-056 is **writing** a requirement, not restating one. That is authorized —
amendment §10 permits specifying requirements already in scope, and it is in scope — but it may not
be done **silently**. Mark any requirement you specify from an undefined id with
`definition_status: AUTHORED_IN_THIS_PHASE` and record that Founder ratification is required.

## 3. Candidates to evaluate, not assume

`SF-REQ-051` Design Contract / Design Verification · `SF-REQ-053` persistent control plane /
bounded coordinator episodes · `SF-REQ-056` liveness reconciliation · `SF-REQ-039` fake-agent /
offline factory proof · `SWF-32` execution cycle capability · Agent-Ready process hardening ·
split/replan capability · other approved Wave 2 work.

Rejecting a candidate is a legitimate outcome and must carry a reason.

**Bootstrap replacement needs are a real input.** Phase 6 left 9 mechanisms `KEEP_UNTIL_REPLACED`;
each replacement that does not yet exist is a candidate this phase should at least consider.

## 4. Five amendments are pending, not settled

Phase 7 recommended amendments to SF-REQ-008, SF-REQ-022, SF-REQ-013, and adjacent targets
SF-REQ-025 and SF-REQ-029. **None is approved** — `POSTW1-DECIDE-007A` is open. Specify against
the requirement set as it stands today, and where a specification depends on a pending amendment,
say so explicitly rather than assuming it lands.

## 5. Per selected requirement, specify

```
intent  value  scope  non_goals  dependencies  acceptance_criteria  authority_gaps
security_constraints  operational_constraints  observability_evidence  failure_modes
```

Plus `requirement_id`, `definition_status` ∈ {DEFINED, AUTHORED_IN_THIS_PHASE}, and
`selected` / `rejection_reason`.

`acceptance_criteria` must be verifiable. Wave 1 produced an unsatisfiable acceptance criterion
(PY-09B binding rule 6 demanded proof the platform's permission model cannot give), and SWF-34 was
needed to resolve it. An acceptance criterion that no evidence could satisfy is a defect, not a
high standard.

## 6. Lifecycle goal

Wave 2 must begin making the underused upstream lanes operational: CAPTURE → SPECIFY → DESIGN →
PLAN → TASKS → READY. **Do not mechanically preserve lanes without operational semantics** — a lane
that exists only as a name is worse than an absent one, because it looks like coverage.

## 7. Deliverables

- `docs/evidence/wave2-specified-requirements.json` (authoritative)
- `docs/evidence/wave2-specified-requirements.md` (prose companion)

With `candidates` (every evaluated id, selected or rejected), `lane_semantics` (what each upstream
lane means operationally in Wave 2), `pending_amendment_dependencies`, and provenance.

## 8. Acceptance

```
python3 tools/evidence/check_wave2_specify.py docs/evidence/wave2-specified-requirements.json
python3 tools/evidence/check_wave1.py --negative-controls
```

Enforces: all eleven fields on every selected requirement; every rejection carries a reason;
`definition_status` present and `AUTHORED_IN_THIS_PHASE` flagged for ratification; no invented
Priority or Wave; acceptance criteria non-empty and not self-referential; and every named candidate
from §3 evaluated.

Do not edit any checker. If you believe a check is wrong, say so in `DISPUTED` and leave it failing.

## 9. Out of scope

Do not begin Phase 9 or write Design Contracts. Do not enact any amendment. Do not assign Priority
or Wave. Do not modify prior deliverables, Wave 1 evidence, lifecycle state, Project state or
worker contracts. Do not `git commit`, push, or use the network.

## 10. Terminal report — this block only

```
CANDIDATES_EVALUATED=<n> SELECTED=<n> REJECTED=<n>
AUTHORED_IN_THIS_PHASE=<ids, or NONE>
BOOTSTRAP_REPLACEMENTS_CONSIDERED=<n>
LANES_WITH_OPERATIONAL_SEMANTICS=<n of 6>
PENDING_AMENDMENT_DEPENDENCIES=<n>
UNVERIFIABLE_AC_FOUND=<n>
SPECIFY_CHECK=PASS|FAIL
WAVE1_CHECK=PASS|FAIL
DISPUTED=<or NONE>
NOTES=<one line, or NONE>
```
