# Convergent Repair / Monotonic Progress — SWF-23

Date: 2026-09-20. Status: **Founder decision — binding architecture/product authority**.
Source: direct Founder instruction, prompted by the PY-04 repair cycle in which a blocking finding was repaired by replacing the test suite, losing proof for five previously satisfied acceptance criteria.
Predecessors: [SWF-01–07](2026-09-19-software-factory-wave1-founder-decisions.md), [SWF-08–11](2026-09-20-wave1-plan-approval-d1-d2.md), [SWF-12–15](2026-09-20-wave1-execution-decisions.md), [SWF-16–20](2026-09-20-wave1-closure-policy.md), [SWF-21](2026-09-20-wave1-release-coordinator.md), [SWF-22](2026-09-20-py04-custody-transfer.md).

## The invariant

> **Repairs must converge monotonically unless authority explicitly changes the target.**

## 1. Behavioral monotonicity

For a repair cycle in which governing requirements, architecture and acceptance criteria have **not** changed:

- previously verified behavior **must** remain correct;
- a repair **must not** fix one defect by regressing another previously verified property.

## 2. Evidence monotonicity

For a repair cycle in which governing requirements, architecture and acceptance criteria have **not** changed:

- previously valid evidence **must** remain valid or be explicitly superseded;
- a repair **must not** remove, weaken, bypass or silently discard proof for a previously satisfied acceptance criterion.

This applies to evidence including: tests; negative controls; mutation / proven-red checks; architecture fitness; CI checks; custody evidence; lifecycle proof; dependency behavior proof; operational verification.

## 3. Explicit supersession

The only legitimate exception is an **authorized change to the governing target**. If a requirement, design, architecture rule or acceptance criterion changes such that prior evidence no longer applies, the old evidence **must** be explicitly marked superseded.

Supersession must record:

- the evidence being superseded;
- the governing decision/requirement that changed;
- the reason;
- the replacement evidence obligation, where applicable.

**Evidence disappearance without explicit supersession is a regression.**

## 4. Convergent repair principle

A repair preserves known-good behavior and proof while fixing the new finding. Do not trade one verified property for another.

## 5. Product Requirement

Recorded as **SF-REQ-049 — Convergent Repair / Monotonic Progress**: AlienIntent must preserve previously verified behavior and evidence across repair cycles, and must detect and regard regression as a verification failure unless explicit supersession exists.

Priority and wave remain Founder input and are left unset.

## 6. BIU / repair contract model

A repair cycle carries, in addition to the BIU contract it serves:

| Field | Meaning |
|---|---|
| findings to fix | the specific findings this repair addresses |
| previously satisfied acceptance criteria | criteria already proven in the prior candidate |
| evidence that must be preserved | the proof artifacts carrying those criteria |
| evidence explicitly superseded | proof no longer applicable, listed item by item |
| supersession authority | the decision/requirement change that authorizes it |
| replacement proof obligations | what must newly prove the changed target |

Already accepted BIUs are not retrofitted or mutated for this. It applies to future repair cycles.

## 7. Verification enforcement (future requirement)

VERIFY should mechanically compare repair-cycle evidence where possible. Proof regression is blocking, including:

- a previously required acceptance test removed;
- a negative control removed;
- an architecture check weakened;
- mutation / proven-red coverage lost;
- candidate custody proof lost;
- previously verified behavior no longer reproducing;
- CI no longer running a previously required check.

The full mechanism is **not** built during current Wave 1 execution unless already inside an approved BIU. This record is authority, documentation and backlog normalization only.

## 8. Measurement (future factory-yield metrics)

- `behavioral_regression_count`
- `proof_regression_count`
- `repair_convergence_rate`
- `evidence_items_gained_per_cycle`
- `evidence_items_lost_per_cycle`
- `repairs_preserving_all_prior_evidence`
- `supersession_count`

Missing telemetry is **UNKNOWN**, never zero. These extend SF-REQ-024 factory yield metrics; no telemetry subsystem is built for them during Wave 1 (SWF-18).

## 9. Relationship to existing authority

This makes explicit what EOS v1.0 rule 1 (preserve known-good capability) and rule 9 (monotonic accepted progress from S0) already imply, and gives VERIFY a named, enforceable obligation. It is closely related to SF-REQ-019 drift detection, SF-REQ-020 fake-DONE prevention and SF-REQ-024 factory yield.

## 10. Scope

The running PY-04 loop is not interrupted, FactoryChecks is untouched, and no current implementation BIU is expanded to implement this requirement.
