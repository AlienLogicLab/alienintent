# WO-220201 producer execution record

## Authority and scope

Executed Issue #76's RELEASED assignment from admission baseline
`901d17444aa0aa1e5098017c3726d0d0daad1442`. Proof contract was committed first
as `9817679`; implementation is `25b1ab8ba506192b1a2614ed1f21c460fbf81db9`.
The runtime resource/active records bind this exact invocation to the assigned
branch, with active WIP count one. Morty / morty-worker identity and #76's
three-cycle / one-replacement-per-phase profile binding were read back.

The implementation uses existing context_assembly package locations and the
existing EvidenceRepository and SQLiteOperationalStore. It establishes no new
context boundary or import-direction authority. No live operation, deployment,
source definition rewrite, bootstrap retirement, RAI wiring or other repository
change was performed.

## Delivered behavior

- Explicit versioned Git source manifest, bounded inert blob reads, digest and span
  validation, and preserved source/adapter/contract/provenance metadata.
- All three definition forms and whole-token classification. The source manifest
  independently supplies expected locators; production extraction does not read
  expected requirement IDs. The historical corpus is observation-only.
- Immutable snapshots with exact token/definition ledgers, conflict/unresolved
  records, revision/provenance history, retirement and stale satisfaction links.
  Only affected spans/IDs hold. Equivalence retains dependency meaning and authority
  revision. Inventory eligibility is not compilable authorization.
- Snapshot/manifest Observation objects installed and read back before CAS of only
  the derived current pointer. Stale writes fail; identical snapshots are no-ops.
  Previous objects remain referenced; private history cannot become public through
  a later public revision or an empty manifest.

`historical_manifest` is a regression-fixture translator, not a production source
binding. Its fixed ingestion timestamp is a deterministic fixture clock value.
Production `SourceSpec` requires explicit provenance and namespace/authority binding.
No live source provider integration or vendor conformance beyond this bounded U1
Git/prose extent is claimed. The public API is the Python RequirementSource,
assemble/resolve and InventoryService boundary; no live service is wired to it.

## Review and repairs

A separate read-only reviewer examined the producer work. Initial reproductions
found inline Recorded-as semantic/dependency loss, malformed Markdown prefix salvage,
and missing definition-only token ledgers. Added targeted tests and repaired each.
The follow-up found access downgrading of private historical content and excluded
text influencing Markdown delimiter pairing. Their new regressions passed after
repair. Final focused review reported no unresolved important defects; this is
producer-internal review, not the fresh BIU VERIFIER invocation or an acceptance.

Initial FX-U1 discrimination caught 9/10 mutations: suffix stripping was not caught
by a definition-identity-only assertion. The failure is retained under `initial/`.
The repaired assertion now checks exact reference token bytes as well. The final
run replaces that insufficient proof; no production invariant was weakened.

## Validation and retained evidence

`python3 -m pytest -q`: **480 passed in 69.20s**, exit 0. This executes the repository's
pytest-function suites as well as unittest classes; it supplements the pinned
unittest command rather than omitting those existing suites.

`node scripts/check.mjs all`: exit 0; runtime **332/332**, preflight **PASS**, RAI
**18/18**, policy **3/3**. No Node code changed. Existing FX-S1/FX-S2 evidence remains
unchanged and ancestral to the candidate.

`python3 tools/fitness/check_architecture.py --root src/alienintent --check all`:
**PASS: all architecture fitness checks**, exit 0.

`PYTHONPATH=src python3 tools/evidence/fx_u1_evidence.py --output /tmp/wo-220201-fx-u1-final`:
exit 0; **10/10** independent controls discriminated with 30 intact/fault/restored
observations. All fault applications matched exactly one source site; every fault
exited nonzero on an assertion, every intact/restored execution exited 0. Artifact
hashes and implementation-file digests were checked against the current files.

Retained artifacts: [final report](wo-220201-fx-u1/final/report.json),
[exact historical snapshot](wo-220201-fx-u1/final/historical-snapshot.json),
[manifest](wo-220201-fx-u1/final/historical-manifest.json),
[initial 9/10 report](wo-220201-fx-u1/initial/report.json), and
[Python regression output](wo-220201-fx-u1/python-regression.log).
Raw control logs and immutable evidence objects accompany both reports. The initial
run was an uncommitted experimental state, not proof of the later implementation
commit. The final report binds implementation commit `25b1ab8` and its file digests.
Operational SQLite pointers remain outside the repository in `/tmp`; only portable
fixture artifacts are included in candidate custody. Raw unittest failure logs preserve
their original trailing spaces (seven whitespace warnings in the unfiltered Git check);
all non-log changed files pass `git diff --check`. Raw logs are validated by digest,
not rewritten to satisfy a source-formatting check. Evidence is local composed/mechanical proof. Tokens and cost
are **UNKNOWN**: invocation billing telemetry is unavailable, not inferred zero.

## Custody and closure

Publish only `b-disp/d2edd0f0-1ad0-41d6-911b-5c28c931895d`, read back its full remote
SHA, and record that exact identity on #76. This runtime-managed candidate is retained
for fresh independent retrieval and the existing BIU closure policy. It is not
landed, accepted or released by this producer record. No direct main push.
