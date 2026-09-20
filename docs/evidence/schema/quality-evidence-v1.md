# Quality Evidence v1

Quality Evidence is a derived, single-JSON-document measurement layer over one or more Execution Trajectory events. It must include `schema_version`, `biu_id`, `derived_from`, and `evidence_refs`; it must not substitute for raw provenance.

Numeric zero means an observed count of zero in the stated scope. Unknown is `"UNKNOWN"` or an object with `status: "UNKNOWN"`; partial observation is an object with `status: "PARTIALLY_OBSERVED"` and an explicit scope; not applicable is `"NOT_APPLICABLE"`. Never encode any of those states as numeric zero.

The v1 comparison vocabulary is optional and includes: first-pass acceptance; producer/verifier/repair counts; findings by class; human decisions and blocked seconds; elapsed intervals; custody, architecture, reproducibility, and test-effectiveness counts; return-to-IMPLEMENT counts; final verdict; landed/DONE flags; provider/model, token, cost, and unknown-metric disclosures. Each derived interval or scoped count must state its definition when ambiguity is possible.

`final_verdict` is a conclusion derived from cited trajectory events. `landed` and `done` are lifecycle/closure conclusions, not raw events. `known_provider_model` reports only known scopes and must not imply provider uniformity.
