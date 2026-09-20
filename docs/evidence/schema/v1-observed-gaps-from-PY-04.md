# v1 observed gaps from PY-04

No v1 schema change is made here. PY-04 exposes candidate future extensions: structured rejection findings (behavioral/evidence/custody/tooling/authority/process); rejection-to-repair links; authority and coordinator interruption types; provider-capacity interruption; evidence monotonicity/proof regression; mutation battery case/result/duration with `NOT_APPLIED`; publication/identity failure; and convergence/distance-to-DONE measurements.

PY-04 also exposed a reconstruction defect: `recorded_at=2026-09-20T10:30:00Z` was a batch placeholder, not a factual per-event record time, and predates later events. It must not be read as event time or evidence-capture time. No replacement timestamp is fabricated in this corrective pass. A future schema review should distinguish artifact-recorded time, recorder/batch provenance, and source-observed event time. These are observations for later review, not schema authority.
