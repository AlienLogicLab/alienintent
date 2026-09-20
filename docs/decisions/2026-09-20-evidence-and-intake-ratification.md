# Evidence-derivation and proposal-intake ratification — SWF-28

Date: 2026-09-20. Status: **Founder decision — binding**.
Source: direct Founder instruction resolving the intake findings on PROP-2026-0004 and PROP-2026-0005.

## 1. Priority and wave assignments

| Requirement | Issue | Priority | Wave |
|---|---|---|---|
| SF-REQ-048 Minimum necessary work invariant | [#59](https://github.com/AlienLogicLab/alienintent/issues/59) | P1 | 3 |
| SF-REQ-049 Convergent Repair / Monotonic Progress | [#60](https://github.com/AlienLogicLab/alienintent/issues/60) | P1 | 3 |
| SF-REQ-055 Proposal Intake as a Product Capability | [#66](https://github.com/AlienLogicLab/alienintent/issues/66) | P1 | 3 |

No other priority or wave is assigned by this record.

## 2. PROP-2026-0005 ratified

[PROP-2026-0005](../proposals/PROP-2026-0005-proposal-intake-as-product-capability.md) carried `authority_level: unresolved`. It is **ratified as product authority**. Its canonical requirement **SF-REQ-055** is Founder-approved product authority rather than a captured candidate.

## 3. PROP-2026-0004 ratified as a capability, folded into SF-REQ-030

The capability proposed by [PROP-2026-0004](../proposals/PROP-2026-0004-execution-evidence-derivation-and-consistency-verification.md) is **ratified**. It is **not** retained as a separate overlapping Product Requirement.

**SF-REQ-030 is the canonical owner of Execution Evidence Derivation and Consistency Verification.**

SF-REQ-054's remaining unique obligation is folded into SF-REQ-030: deterministic consistency verification must itself have discriminating negative-control / proven-red evidence where practical.

The amended SF-REQ-030 preserves all of:

- derived metrics mechanically reconcile to factual ExecutionTrajectory where facts permit;
- UNKNOWN is never silently converted to zero;
- contradictory derived evidence fails verification;
- verifier-cycle, RETURN_TO_IMPLEMENT, rejection-class, authority, landed/DONE and similar derivable counts reconcile to underlying events;
- the reconciliation mechanism must itself be shown capable of failing on meaningful inconsistency.

### Exact amendment added to SF-REQ-030

> The deterministic consistency verification must itself carry discriminating negative-control / proven-red evidence where practical: altering a derived count, substituting zero for UNKNOWN telemetry without evidence, or introducing an impossible timestamp relation must cause the applicable check to fail. A consistency check that cannot fail is not evidence (SWF-24). Folded from PROP-2026-0004 by Founder decision of 2026-09-20; SF-REQ-030 is the canonical owner of Execution Evidence Derivation and Consistency Verification.

## 4. SF-REQ-054 retired

SF-REQ-054 is retired as duplicate/superseded. Issue #65 is closed with that disposition. The ID is not reused and its history is not deleted: the plan retains a retirement entry pointing at SF-REQ-030, and [PROP-2026-0004](../proposals/PROP-2026-0004-execution-evidence-derivation-and-consistency-verification.md) is preserved unchanged as provenance.

`docs/proposals/INDEX.md` maps PROP-2026-0004 to the SF-REQ-030 amendment rather than to a separate active requirement, so exactly one canonical requirement owner exists.

## 5. Scope

No BIU is created and no implementation is authorized. No live Wave 1 lifecycle state is changed, PY-06 execution is untouched, and no additional priority or wave is invented.
