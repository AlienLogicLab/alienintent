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

## 4b. Verification-first repair sequencing (Founder decision, 2026-09-21)

Convergence is not only about preserving what is proven; it depends on the proof existing before the
implementation it protects is repaired. The coordinator enforces this order on a repair cycle:

1. **confirm the required verification harness exists;**
2. **confirm changed paths are covered by discriminating proof;**
3. **preserve prior proven criteria;**
4. **then repair remaining implementation defects.**

Step 2 is [SWF-24](2026-09-20-deterministic-failure-class-promotion.md) applied to repair: a check
that cannot fail is not evidence, so coverage of a changed path must be able to go red when that path
breaks. A cycle that widens implementation while the harness for what it touches is missing is out of
order, and the coordinator says so at the rejection rather than waiting for the defect it predicts.

**Binding for PY-09 and PY-10**, and carried in both contracts. It is not retrofitted into PY-08,
which is released and in flight ([SWF-20](2026-09-20-wave1-closure-policy.md)); the direction PY-08
received in its sixth cycle already embodied it.

### The evidence that produced this rule

PY-08 ran **five** repair cycles in which findings fell (14 → 11 → 10 → 8) while each cycle shipped one
or two fresh defects, including two SWF-23 regressions. Across all five, two contract obligations were
never attempted: AC 4's proof that `explain` reproduces the kernel's own decision, and the verification
requirements' negative-control and backdoor coverage.

Those were precisely the checks that would have caught what kept breaking. The sixth cycle was directed
to build **only** that proof plus the outstanding regression. It closed AC 4, the verification
requirements, the two-cycle AC 7 regression and the removed-diagnostics regression, added five tests,
and introduced **no new defect and no regression** — the verifier's first report in six cycles whose
remaining findings were all carried rather than fresh.

> **When a repair loop keeps trading defects, the missing verification is usually the cause, not a
> parallel debt.**

A secondary finding, recorded because it was nearly mistaken for the primary one: this looked like a
BIU that needed splitting. It was not. The proof obligations were buildable inside PY-08 in a single
cycle once they were sequenced first. **Wrong sequencing imitates wrong decomposition**, and the cheap
test of which one you have is to spend one cycle on verification alone before proposing a split.

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
