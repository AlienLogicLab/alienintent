# Verification ceremony must be proportional to risk — Founder requirement

Date: 2026-09-28. Status: **Founder decision — binding, hard Factory Director
requirement.**

Recorded via Director inbox handoff
`founder-verification-proportionality-hard-requirement-20260928`
(entry mtime 2026-09-28T04:02:30Z), a `FOUNDER_ARCHITECTURE_HANDOFF` with
`priority: HARD_FACTORY_DIRECTOR_REQUIREMENT`.

## Decision

Verification ceremony must be proportional to the risk being controlled. Evidence
requirements that cannot change the correctness conclusion, or that create
self-referential candidate churn, must be eliminated or assigned to the actor that can
satisfy them without mutating the artifact under test. This is binding policy for every
Factory Director episode from this date, in the same sense as any other durable Founder
decision recorded on this repository's own decision log.

The handoff names eight standing Director obligations, accepted verbatim as durable
requirements:

1. Detect repeated IMPLEMENT-to-VERIFY cycles caused only by evidence custody or
   placement ceremony while implementation and independent regressions already pass.
2. Do not treat such cycles as ordinary implementation rework.
3. Determine producer-owned versus verifier-owned evidence and enforce the canonical
   custody rule.
4. Prevent self-referential candidate mutation loops.
5. Route exact-candidate verifier receipts to the verifier checkout when the receipt
   must name the immutable candidate SHA.
6. Avoid consuming another implementation cycle when no implementation defect exists.
7. Repair or escalate verifier contract/tooling when verification repeatedly demands
   impossible or non-value-adding evidence placement.
8. Measure and reduce verification ceremony as part of Director efficiency/economy/
   quality improvement.

## The concrete custody rule (obligation 3 and 5)

The mandatory `.alienintent/feature-regressions.json` receipt required by
`AGENTS.md`'s "VERIFY accumulates feature regressions" rule names the exact candidate
SHA it certifies. A receipt naming a candidate cannot be committed inside that same
candidate's own tree without changing the tree, which would change the SHA it names —
a self-referential requirement no producer commit can satisfy. The receipt is therefore
**verifier-owned evidence**: the VERIFIER generates it in its own checkout at the exact
candidate revision and judges the actual implementation and independent regression
results, rather than rejecting because the immutable candidate does not carry a receipt
that only the act of verification itself can produce.

This is a procedural/custody clarification, not a code defect: `read_verdict`
(`src/alienintent/invocation_runtime/application/real_worker.py`) already correctly
requires the receipt's `candidate` field to equal the verified revision. The gap was
that two prior VERIFIER cycles on Issue #141 (WO-220611/B3P) read the custody
requirement as "the candidate must carry the receipt," rejecting cycles 1 and 2 solely
on that placement ground even though both applicable feature-regression packs passed
each time. The cycle-3 VERIFIER applied the corrected reading — generated the receipt
in its own checkout, judged the actual implementation — and returned ACCEPT
(`AlienLogicLab/alienintent#141:VERIFIER:7476be5c-bb4c-4d17-a9da-7aa0e65a7b45`,
2026-09-28T04:01:54Z, candidate `953dda54c5c3ac95ad9e61e85cfa0b4d1cca5eb8`). The
candidate has since reached board `DONE` and is landed on `origin/main`. No further
action was needed on Issue #141 itself; the incident the handoff cites is resolved by
the time this record is written.

## Materialization

This document is the durable Factory Director requirement obligation 8 calls for, so
future episodes do not depend on remembering this incident. No source-code change is
required: the custody invariant this decision describes is already enforced correctly
by `read_verdict`; what needed correcting was which actor (producer vs. verifier)
satisfies it, which is a conduct/procedure matter for the VERIFIER role rather than a
mechanical gate. A future episode that observes a VERIFIER reject solely on
candidate-side receipt placement, with independent regressions otherwise passing,
should treat that as a verifier contract/tooling defect under obligation 7 (repair or
escalate), not as ordinary producer rework, and may cite this record rather than
re-deriving the reasoning.

## Boundaries

This decision does not change `AGENTS.md`'s feature-regression-accumulation rule, the
`read_verdict` candidate-match check, or any BIU's own pinned fixture steps. It records
the Founder's standing direction on evidence proportionality and custody assignment,
and the resolution of the specific incident that prompted it.
