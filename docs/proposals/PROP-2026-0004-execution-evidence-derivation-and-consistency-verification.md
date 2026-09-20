---
proposal_id: PROP-2026-0004
title: Execution Evidence Derivation and Consistency Verification
submitted_by: durability-gap audit
submitted_at: 2026-09-20
proposal_type: product_requirement
authority_level: unresolved
status: submitted
---

# Execution Evidence Derivation and Consistency Verification

## Intent

ExecutionTrajectory is the factual, append-oriented record of what happened.
QualityEvidence is a derived measurement or conclusion. AlienIntent should make
QualityEvidence mechanically reconcilable with its cited ExecutionTrajectory
and other explicitly named evidence wherever the underlying facts permit it.

Derived evidence must not become an independently editable interpretation that
can silently drift from factual observations.

## Proposed capability

QualityEvidence identifies its source trajectory/schema version and explicit
input references. A deterministic consistency check rejects contradictions
rather than silently accepting a plausible narrative.

Where inputs make the result derivable, reconciliation includes:

- verifier-cycle counts from matching trajectory events;
- RETURN_TO_IMPLEMENT counts from lifecycle/control events;
- rejection-class counts from classified events;
- genuine authority gaps separately from false or escalated authority requests;
- blocked human-attention duration from attributable event intervals;
- candidate and merge identity reconciliation with trajectory and available Git
  evidence;
- final verdict, landed state and DONE reconciliation with underlying events;
- detection of impossible timestamp relationships; and
- preservation of UNKNOWN or partial telemetry rather than conversion to zero.

Unavailable telemetry remains UNKNOWN. The capability does not infer a zero,
success, or failure from absent evidence.

## Discriminating verification

The consistency check itself should be discriminating where practical, under
the SF-REQ-050 / SWF-24 principle. Retained negative-control/proven-red evidence
should show that changing a derived verifier count, replacing UNKNOWN
provider-capacity telemetry with zero without evidence, or introducing an
impossible timestamp relation causes the applicable check to fail.

## Boundaries

- No storage implementation, database, event collector, runtime hook, transport
  or telemetry service is prescribed.
- This does not rewrite factual trajectory events or make missing telemetry
  available.
- A derived object cannot declare a lifecycle verdict without referenced facts
  and applicable policy/evidence evaluation.
- Versioned failure-taxonomy and schema design remain subject to normal
  design/architecture authority.

## Relationship to existing authority

SF-REQ-029 records Engineering Trajectory; SF-REQ-030 requires Quality Evidence
derived from trajectories; SF-REQ-016 separates definition, observation and
verdict; SF-REQ-020 rejects unbacked DONE claims; SF-REQ-024 measures factory
yield. This proposal supplies the missing explicit mechanical reconciliation
obligation.

## Desired outcome

Quality Evidence is inspectably derived from cited facts and contradictions are
detected before the evidence informs routing, learning or factory-yield claims.
