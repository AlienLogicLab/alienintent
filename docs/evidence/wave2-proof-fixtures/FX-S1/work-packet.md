# WO-220102 implementation plan

Authority: Issue #71 and release comment 5789648516; admission baseline
`7bd7a6e782d8c4c1562f6f1f6813322870935825`. The approved design is
`wave2-design-contracts.json#/contracts/5` plus its shared contracts, within S1.
FX-S1 commands, inputs, outcomes and schema were pinned in the preceding commit.
The runtime assignment identifies Morty as the sole mutation owner of this
isolated `b-disp/b69c44d2-ee8b-47a0-afbf-7a1177e555c7` worktree. Admission was clean.

Use Python 3.12 and the standard library, existing SQLiteOperationalStore and
unchanged evaluate_verdict. No inventory dependency, lifecycle change, RAI,
authority authoring, migration of old source authority, deletion or live operation.
The user authorizes inline execution of the durable assignment; no new design
approval or execution-choice prompt is needed. An independent local code review
supplements, but does not replace, the separately allocated VERIFIER invocation.

## Implementation and checks

1. Add failing tests for neutral `Ref`, frozen Definition/Observation/Verdict
   records, exact scalar roundtrips and authority admission. Implement leaf values
   in `evidence_learning/domain/{refs,records,admission}.py` and the repository
   protocol in `evidence_learning/ports/evidence_repository.py`.
   Definition admission consumes an externally authorized exact digest; evidence
   ingestion cannot create normative authority. Tests assert rejection when a
   worker observation is relabelled, evidence is stale or an evaluator is unknown.
2. Add failing filesystem/SQLite integration tests, then implement
   `evidence_learning/adapters/local_evidence_repository.py` and
   `evidence_learning/application/evidence_service.py`. `put(record) -> Ref`
   durably installs an immutable object; `get(ref, access_scope)` validates exact
   identity/digest. `admit(record, expected_version) -> Admitted` appends a ref to
   the profile catalog through CAS only after durable readback. Read returns the
   catalog version. Catalog history preserves all refs; conflicting observations
   hold applicability. Each operation checks schema and authority without retry.
   Crash tests terminate child processes on both sides of the real CAS commit.
3. Add failing bridge/composition tests. Implement
   `execution_coordination/ports/evidence_verdict.py`,
   `execution_coordination/adapters/evidence_verdict_bridge.py` and
   `composition/evidence_profile.py`. Exact admissible definition/observation
   values map to the existing policy; held/conflicting or stale refs cannot reach
   acceptance. The bridge returns a typed verdict record, not a lifecycle event.
   OfflineProfile accepts an optional evidence profile; no kernel rewiring.
4. Execute C1; add the FX-S1 evidence runner in `tools/evidence/fx_s1_evidence.py`.
   Run independent source mutations for kind, authority and revision gates in
   disposable copies, never disabling production controls in this worktree.
   Each negative control must apply exactly once, fail an acceptance assertion,
   and pass again after restoration. Retain exact source/fixture/profile digests,
   command stdout/stderr/status and immutable observation objects.
5. Execute C3/C4/C5, independent read-only review, and repair in-scope findings.
   Commit implementation, execute and retain evidence at that committed source,
   then commit evidence. Push the assigned candidate branch and read back its full
   SHA. Post exactly one Issue comment with candidate identity and VERIFY marker.
   If a concrete blocker prevents this, retain its evidence and post the exact
   FOUNDER_EXCEPTION marker instead. Runtime-managed resources remain retained
   for BIU custody/closure; no manual removal of this active worktree.

## Acceptance evidence

The pinned fixture plan maps AC01–AC04, durability, types and isolation. Tests use
temporary external roots and real SQLite; unavailable measurements remain null
with a reason. Local results are observations; the independent verdict is pending
until the allocated verifier reviews the exact remotely retrievable candidate.

The predecessor closure URL typo is recorded in the plan with the actual retained
receipt; the assessed work-unit bytes and original evidence remain unchanged.
