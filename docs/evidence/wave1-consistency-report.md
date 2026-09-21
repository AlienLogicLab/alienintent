# Wave 1 deterministic consistency report

Result: **PASS**. 1075 checks; 0 failures. Negative controls: 13/13 killed.

Command: `rtk proxy python3 tools/evidence/check_wave1.py --negative-controls --report`.

Offline consistency against retained GitHub/runtime source capture and current Git objects/origin refs; not a fresh product verdict or re-execution of live proof.

Covers population/mapping, complete Project pages, source verdict counts, candidate/merge ancestry, timestamp semantics/order, cycle/attempt separation, first-pass status, UNKNOWN preservation, source/trajectory/quality reconciliation, historical supersession, v1 terminal schema validity, readiness/preflight history and sandbox remote custody.

Finding-group semantics are a source-cited human classification; the checker validates their propagation and directly recounts PY-06 headed IDs. It does not claim to mechanically interpret arbitrary verifier prose. Historical schema/time ambiguities are disclosed in [reconciliation](wave1-evidence-reconciliation.md).

- derived rejection count: KILLED
- UNKNOWN to zero: KILLED
- impossible chronology: KILLED
- Issue mismatch: KILLED
- false first-pass: KILLED
- provider failure counted as repair: KILLED
- retry increments cycle: KILLED
- fabricated finding count: KILLED
- Issue closure conflated with DONE: KILLED
- seventh candidate: KILLED
- nonexistent merge: KILLED
- unreachable accepted candidate: KILLED
- supersession removed: KILLED

Full discriminating failure reasons: [JSON](wave1-consistency-report.json).
