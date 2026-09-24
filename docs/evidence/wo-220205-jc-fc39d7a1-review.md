# WO-220205 independent JC verification

Verdict: **REJECT** for producer candidate `c9a8699a8b297be21df27615ce5c8ccf6fd56a4c`,
branch `b-disp/1108187c-0789-4150-a90c-1c83dd6e7673`.
Invocation: `AlienLogicLab/alienintent#97:VERIFIER:fc39d7a1-7c68-40e6-9faa-dc2a68bbb905`.
Reviewer: JC / `jc-worker`, independently invoked in the assigned separate runtime worktree.

## Authority and admission

Authority was reconstructed from Issue #97, release comment 5814787888, candidate submission
5815202259, and the pinned WO-220205 contract, packet, allocation, SF-REQ-051 design and
FX-U5 mapping. The Issue snapshot is retained alongside this report. Scope is U5/FX-U5 local
verification only. The open directional-authority question is required hold behavior, not a
reason to stop this assignment. No other repository is in scope.

The initial worktree was clean at `1f8648b8cc3d9aa707588ab7698ef4f7f368fb4c`.
Git identity was JC / jc-github@factorychecks.com; GitHub authenticated as jc-worker; origin
was AlienLogicLab/alienintent. The published producer branch was fetched, the exact candidate
checked out, and remote `ls-remote` matched. All fresh candidate checks ran before receipt edits.
The assigned verifier branch was then based on that exact candidate to publish evidence only.
Unrelated canonical packet preparation at the initial HEAD was not combined with the candidate.

Admission baseline `7be12188edf632710fe842d95fc70b444e2ed279` is an ancestor of the candidate.
U2 accepted `d0eacfb6dd8626b07ff1d99e9c633294f13d9de4` and U4 accepted
`c8ed707efdb0cd70294bfdb6814ec9f9eb71216d` are ancestors of the admission baseline. Their
Issue ACCEPT receipts 5808965906 and 5814553759 were retrieved. Independent evidence branches
were fetched and receipt commits `4f03da9a2e6107ad1862f5e97ba80f33cf616325` and
`42d521913e7daa7a5c450595fe3553082b5df22d` read. Thirteen pinned input hashes and all 146
producer manifest entries verified. Predecessor implementations and retained evidence are unchanged.

## Blocking finding R1: historical review renews invalidated applicability

Affected code: `src/alienintent/context_assembly/application/design_admission_service.py`,
`inspect` lines 103-114 and `record_review` lines 130-148 at the reviewed candidate.
Authority: AC-05 and BLOCKING `051-review-applicability` require fresh independent review after
invalidation; the approved SF-REQ-051 transition requires a fresh authorized review of exact
checks, and the FX-U5 contract says stale applicability lasts until re-inspected and reviewed afresh.

Reproduction using only public component methods and a disposable composed profile:

1. Inspect design A and admit independent review R at versions 0 and 1.
2. Check a changed required-revision vector. The design becomes durably STALE at version 3;
   readiness refuses, even for the original vector.
3. Re-inspect the original inputs at version 3. The component appends a new report event but
   computes the same content-only mechanical report digest and clears the active review fields.
4. Submit an exact copy of R, including its old reviewer invocation, at version 4. No new review
   has taken place. The result is **ReviewAdmitted**, and readiness returns **admitted=True**.

Observed history: `design.review_required`, `design.verified`, `design.stale`,
`design.review_required`, `design.verified`. The new inspection event is different, but the
review binds only the content digest/vector; no guard distinguishes the historical review from
fresh review after invalidation. The STALE guard has stopped applying because inspection changed
the state back to REVIEW_REQUIRED. This finding concerns replay after invalidation, not rejection
of ordinary duplicate imports in an unchanged VERIFIED state, and does not require store tampering.

`freshness_test.py` is an independently authored regression oracle. On the exact candidate it
exits **1**, with **2 passing controls and 1 failing regression**:

- unchanged VERIFIED duplicate review is idempotent: PASS;
- a new independent reviewer invocation after re-inspection can verify: PASS;
- the old review must not reverify an invalidated design: FAIL (`ReviewAdmitted`, readiness true).

Repair obligation: bind fresh review admission to the current inspection/invalidation generation
(or an equivalent durable freshness check) so the retained prior review cannot renew applicability.
Preserve ordinary duplicate-review idempotency, exact-vector checks, a conforming fresh independent
review, and immutable prior history. Add intact/fault/restored coverage for this sequence; do not
weaken the fresh-review obligation or simply change the independent oracle to accept the replay.
The existing `test_stale_design_is_not_reverified_in_place` covers the immediate STALE state but
then accepts a byte-equivalent review after re-inspection; it does not prove freshness.

## Independent judgment and acceptance disposition

JC inspected the specified requirement, approved design, pinned FX-U5 contract and mapping,
U3 premise mapping, SWF-25/SWF-34, implementation and tests, and fresh raw observations.
This is the attributed judgment for `SF-REQ-051/SF-REQ-051-AC-04/premise-review-judgment`.

The impossible permission-denial fixture is faithful to the pinned SWF-34 premise: token-level
per-Project denial is not a realizable requirement in that approved topology. The four distinct
realizable controls remain premise-backed; the impossible criterion is held and its attributed
rejection retained even though other checklist checks are green. This is local use of retained
capability evidence, not a new platform or operational verification.

The fixture's open private-helper naming choice is actually local: its bound excludes predicate,
identity, persistence and authority changes. An open public API decision and a blocking reviewer
finding hold. The persistence-inapplicability reason is proportional to the hypothetical read-only
change it describes; it does not imply that U5 itself has no persistence. An exploratory probe
also observes that `security: {"value": []}` reaches REVIEW_REQUIRED. That empty statement is not
substantive design evidence: an independent reviewer must reject it, and mechanical completeness
alone is not semantic approval. This observation is not the basis for R1 or a claim of automatic
verification.

The mapping preserves judgment rather than assigning it a mechanical PASS. However, its freshness
coverage is insufficient in the concrete R1 sequence, so the overall runnable-binding judgment
and `051-review-applicability` cannot be accepted. Existing AC-01/02/04 probes, architecture-authority
holds, history retention and the lifecycle non-mutation controls remain positive evidence.
AC-05 and the readiness freshness guarantee require R1 repair. AC-03 and withdrawn R1 direction
policy fixtures remain outside this node's claimed extent. No new Project state or approval lane
was introduced, and sibling compiler/readiness consumers remain outside this node.

## Fresh observations and retained proof

See `wo-220205-jc-fc39d7a1/commands.json` for commands, exit codes and raw output filenames.

- `PYTHONPATH=src python3 -m pytest -q tests`: exit 0, **632 passed in 75.52s**.
- Architecture fitness: exit 0, PASS. `node scripts/check.mjs all`: exit 0.
- FX-U5 with this verifier invocation: exit 0, **23/23 QUALIFIED_KILL**. All 69 phase logs hash-verified;
  intact/restored exit 0, fault exit 1; mutation application counts 0/1/0. Domain controls remain
  green with composition disconnected. Proof-order diagnostics empty.
- Plan digest `sha256:2e674e6adc31a288fa49377da52b5c17e193d4fc77e93e31c13c6c5169705f43`.
- Seventy immutable objects and seventy control logs (including the disconnected domain log)
  exported unchanged. The local SQLite execution store is not published.
- Independent freshness regression: exit 1, 2 pass / 1 fail. Diagnostic `probes.py`: exit 0,
  observations only. The initial broader test-discovery run is retained separately, not counted
  as another acceptance suite.

These passing observations do not discharge R1. Preserve all existing obligations and producer/
verifier evidence across repair under SWF-23; no existing proof is superseded by this rejection.
The runner's plan root and fixture helpers retain compiled-in producer attribution. Phase
observations/report use this verifier invocation; this receipt supplies the independent judgment.
The report's inherited pending-verifier text is not a workflow result.

## Custody, limits and next action

Only verifier evidence is added on `b-disp/0425f771-7f5f-4dcb-8c8e-1058e12f5c9d`, owned by
this JC invocation. Its runtime-managed branch/worktree is retained under BIU closure policy,
pending R1 producer repair, independent verification and Factory Director disposition. It is not
an accepted implementation or permission to merge. The Director owns SWF-19 merge-at-closure
and evidence cleanup. Next authorized lifecycle action is return to IMPLEMENT for R1 repair.

No PR, baseline push, merge, live operation, Project transition or other-repository change was
performed by this verifier. Tokens/cost UNKNOWN. Local proof makes no operational-success claim.
