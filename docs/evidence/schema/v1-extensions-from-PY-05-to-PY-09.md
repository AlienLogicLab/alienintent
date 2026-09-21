# v1 extensions observed from PY-05 to PY-09

**No v1 schema change is made here.** Both v1 schemas allow additional properties, and the PY-05–PY-09 records use that allowance rather than redesigning the format. This file documents every field and event type added beyond the v1 vocabulary so the additions are explicit rather than silent. It extends, and does not supersede, [`v1-observed-gaps-from-PY-04.md`](v1-observed-gaps-from-PY-04.md).

Several of these extensions implement candidates that file already identified: structured rejection findings, rejection-to-repair links, authority and coordinator interruption types, evidence monotonicity and proof regression, and convergence measurement.

## Execution Trajectory — added event types

All are factual observations. No conclusion is encoded in an event type.

| Event type | Records |
|---|---|
| `LIVENESS_GAP_DETECTED` | a liveness watch found a nonterminal state past its grace with no running actor, and what recovery was applied |
| `ATTENTION_ITEM_ENQUEUED` | a durable attention item was created for coordinator or Founder judgment |
| `COORDINATOR_CONVERGENCE_ASSESSMENT` | the coordinator assessed a repair loop and issued direction. The direction is a fact about what was instructed; it is not a verdict on the candidate. |
| `EVIDENCE_SUPERSEDED` | previously valid evidence was removed under explicit SWF-23 §3 supersession, with the authorizing finding |
| `EVIDENCE_ARTIFACT_RETAINED` | a required retained-evidence artifact was created |
| `DISPATCH_LATENCY_OBSERVED` | a measured interval between candidate publication and the next actor launch, with its cause stated or `UNKNOWN` |
| `ISSUE_CLOSED` | the Work Management Issue closed. A bookkeeping projection, explicitly not a lifecycle transition (SWF-31). |
| `PRIOR_LESSON_CARRIED` | a lesson from an earlier BIU is present in this BIU's pre-execution artifacts |
| `EXTRACTION_BOUNDARY` | the record is incomplete because the BIU was active when it was made |

## Execution Trajectory — added fields

| Field | Meaning |
|---|---|
| `recorder` | who or what produced this record, and when. Distinguishes artifact-recorded time from source-observed event time — the exact distinction `v1-observed-gaps-from-PY-04.md` asked a future schema review to make. |
| `blocking_finding_count` | count of findings the verifier itself treated as blocking in that report. The event's `description` states what was counted and what was excluded. |
| `decisive_finding_count` | count of findings the verifier explicitly labelled `(decisive)`. Present only where the verifier used that label. |
| `finding_ids` | the verifier's own finding identifiers, so a count can be traced back to named items |
| `test_count_observed` / `test_count_claimed` | the verifier's reproduced count and the producer's claim, kept separate. Observation is not verdict, and a producer claim is not an independent result. |
| `node_count_observed` / `node_count_claimed` | the same separation for the Node suite, where the two disagreed for four consecutive cycles |
| `candidate_diff` | the verifier's stated diff of the candidate against its own parent |
| `candidate_lineage` | whether a candidate is a descendant repair of the rejected candidate or a re-implementation on the baseline |
| `proof_regression` / `behavioral_regression` | whether that verification reported an SWF-23 regression. Booleans on the verification event, so a regression count reconciles against named events. |
| `closure_command_count` | commands reported by the closure worker, where reported |
| `lifecycle_stage` | the lifecycle state a control-plane observation was made in |

`finding_class` is already a v1 field. PY-05–PY-09 use the classification vocabulary from SF-REQ-029 — `BEHAVIORAL_DEFECT`, `EVIDENCE_PROOF_DEFECT`, `CUSTODY_IDENTITY_DEFECT`, `TOOLING_PUBLICATION_DEFECT`, `PROCESS_INSTRUCTION_ADHERENCE`, `AUTHORITY_REQUIRED`, `FALSE_OR_ESCALATED_AUTHORITY_REQUEST`, `PROVIDER_CAPACITY_INTERRUPTION` — plus `ARCHITECTURE_CONFORMANCE` and `LIVENESS_CONTROL_PLANE`, which are evidence-local labels and **not** SF-REQ-029 authority.

## Quality Evidence — added fields

| Field | Meaning |
|---|---|
| `blocking_findings_by_cycle`, `decisive_findings_by_cycle`, `test_count_by_cycle`, `candidate_added_lines_by_cycle` | per-cycle series. A total alone cannot distinguish converging from thrashing. |
| `proof_regression_count`, `behavioral_regression_count`, `defects_introduced_by_repair` | the SWF-23 §8 measures, separated. A repair that fixes one defect and introduces another is not the same event as a repair that loses proof. |
| `evidence_superseded_count` | authorized supersessions, kept distinct from regressions |
| `tests_dropped_by_cycle` | where a verifier diffed the test inventory |
| `never_attempted_obligations` | contract obligations untouched across multiple repair cycles. The PY-08 measure that explains its trajectory. |
| `repair_mode` | one of `CONVERGING`, `STAGNATING`, `THRASHING`, `MASKED_DEFECT_REVEALED`, `VERIFICATION_MISSING`, `AUTHORITY_BLOCKED`, `PROVIDER_BLOCKED`, with a `basis` field citing the trajectory evidence. **Analytical, not a product state.** Never inferred from finding count alone. |
| `recurring_failure_class` | a class the verifier named in more than one cycle, with the count of cycles |
| `candidate_lineage` | counts of descendant repairs versus re-implementations |
| `coordinator_defect_authority_blocks` | authority interruptions caused by a defect in the coordinator's own release record, distinct from `human_decisions_required` and from `false_or_escalated_authority_requests` |
| `liveness_incidents`, `operator_interventions`, `attention_items`, `coordinator_convergence_assessments` | control-plane interruption measures |
| `carried_scope_debt_at_accept` | findings the verifier recorded as real but not blocking at ACCEPT, so they are not lost |
| `verification_first_sequencing` | PY-09 only: whether the SWF-23 §4b rule was present before execution, where it was carried, whether the verifier applied step 2, and whether the producer sequenced accordingly |
| `extraction_status` | present when the BIU was active at capture time |
| `issue_closure_lag_seconds`, `unexplained_dispatch_gap_seconds`, `verification_elapsed_seconds` | intervals v1 did not name |

## What v1 handled without extension

Candidate identity as provider-neutral `candidate_ref` with optional `commit_sha`, the `observation_type` distinction between worker claim / independent verification / Git observation / CI observation / state-record observation / derived timestamp arithmetic, `verified` meaning the recorder located the cited evidence rather than reproduced the result, `authority_ref`, `UNKNOWN` and `PARTIALLY_OBSERVED` for telemetry, and `{value, definition}` or `{value, scope}` for every scoped count. None of these needed changing. The `observation_type` vocabulary in particular carried the whole producer-claim versus verifier-observation separation without amendment.

## Still open for a future schema review

1. **`recorded_at` overloading persists.** `recorder` mitigates it; a proper split into artifact-recorded time, recorder provenance and source-observed event time is still the right fix.
2. **A finding is not a first-class entity.** Carried findings are counted once per cycle in which they were reported, so PY-08's 58 measures reported findings, not distinct defects. A stable finding identity across cycles — with `first_reported`, `closed_at`, `carried_cycles`, `recurred_as` — would make "is this converging?" derivable rather than narrated.
3. **`repair_mode` is authored, not derived.** It is stated with a cited basis, and the consistency check verifies the basis exists but not that it entails the label.
4. **No schema for a lesson.** Learning graduation is prose in a separate evidence file. The maturity ladder used there is analytical and has no canonical owner.
