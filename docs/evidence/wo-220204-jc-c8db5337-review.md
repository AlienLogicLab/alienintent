# WO-220204 independent JC review

Disposition: **REJECT** for producer candidate `53833f57833455573a5c6f731d97cf14882e728e`,
published branch `b-disp/284920a7-9cf9-4ced-997d-2c9e5ab4e035`.
Invocation: `AlienLogicLab/alienintent#94:VERIFIER:c8db5337-1ac1-4849-bf0c-9f7787e57e3d`.

## Authority and custody

Read AGENTS.md, governing directive, work packet and forward-momentum guidance. Reconstructed
authority from Issue #94 body, release comment 5813333147, continuation 5813788187 and producer
submission 5813953829; the pinned WO-220204 contract, packet, allocation and SF-REQ-014
specification/design govern. Scope is U4/FX-U4 only. Authenticated as jc-worker, local identity
JC / jc-github@factorychecks.com. Candidate fetched from origin and remote ref readback matched.
Review ran at the exact candidate in assigned separate worktree
`3daacd5c-b183-4926-aea3-a49066a5dea9`, initially clean.

Admission baseline `4b94f2d1d7d40c1889af79596e8f92c737e55d7e` is ancestral. Read back the
independent predecessor verdicts on #76 (5792843472), #80 (5808965906), #81 (5811071942).
Their exact accepted candidates, respectively `43ea5e2b745be02df6aebaf5ba1e328f4c75fa5e`,
`d0eacfb6dd8626b07ff1d99e9c633294f13d9de4`, `3e8dc7032dc7e61aac48b66ea9d08a3e789757ad`,
are retrievable locally and ancestral. No predecessor implementation/evidence was changed.

## Blocking finding R1: structured empty history forgets prior obligations

Priority HIGH, `014-repair-preservation` and SF-REQ-014-AC-04.
`src/alienintent/evidence_learning/application/proof_planning_service.py:42-44` accepts a
state with no plan events whenever both pointers are null. `read()` checks version only for
the literal empty dictionary, so a fully shaped state with `history=[]`, `plan_ref=None`,
`plan_digest=None` passes at a nonzero version. `current()` then returns None and `derive()`
calls the domain with no prior plan.

Independent reproduction uses the candidate's composed fixture and real temporary SQLite:

1. Derive the genuine five-obligation plan.
2. Commit the structured empty-history state at the next expected version, modelling the
   same persisted-state loss already covered by the candidate's state-corruption tests.
3. Remove `mapping-faithfulness-judgment` and re-pin the mapping using the existing fixture
   helper, without adding any supersession.
4. Derive again: **ProofPlan**, no judgment obligation, `prior_plan_digest=None`.

The identical predicate deletion with intact state returns **PRIOR_OBLIGATION_DROPPED**;
the restored independent fixture also returns that hold. Thus this is a fail-open recovery
path, not just an unavailable historical lookup. No live state or source was modified.

Reproduction: `PYTHONPATH=src:. python3 docs/evidence/wo-220204-jc-c8db5337/reproduce.py`.
Exit 0 means the script reproduced the reported bad behavior; it is not an acceptance pass.
The raw output is retained alongside it. The first-derivation case separately confirms the
producer-disclosed per-AC coverage limitation; the blocking finding relies on an already
persisted prior plan and requires no interpretation of first-derivation policy.

Required repair: refuse or safely recover a nonzero-version state whose prior history was
erased, preserving genuine initial held-plan histories. Add discriminating coverage for this
structured form and re-run existing guards. Do not erase or supersede earlier proof without
authority. Retain the prior judgment obligation unless explicitly superseded.

## Fresh checks and retained evidence

All commands below ran on the exact producer SHA, before this evidence-only commit:

- `PYTHONPATH=src python3 -m pytest -q tests`: exit 0, **601 passed in 63.84s**.
- `python3 tools/fitness/check_architecture.py --root src/alienintent --check all`: exit 0, PASS.
- `node scripts/check.mjs all`: exit 0, all required groups passed.
- `git diff --check 4b94f2d..HEAD`: exit 0.
- `PYTHONPATH=src python3 tools/evidence/fx_u4_evidence.py --output /tmp/wo-220204-jc-c8db5337/controls --invocation AlienLogicLab/alienintent#94:VERIFIER:c8db5337-1ac1-4849-bf0c-9f7787e57e3d`:
  exit 0, **29/29 QUALIFIED_KILL**, intact/restored exit 0, fault exit 1, application counts
  0/1/0. Disconnected composition leaves domain tests green. Advisory diagnostics empty.
- Independently hash-checked **88/88 raw logs** in both producer and verifier reports.
- Producer's 88 referenced immutable objects are absent from the Git candidate, but **88/88
  exist and hash correctly** at the explicitly recorded external run location
  `/tmp/fx-u4-final/state/evidence`. They are not claimed unavailable. Temporary retention
  is a custody limitation; preserve/export them before cleanup.

The adjacent evidence directory exports this verifier's report, raw logs, reproduction,
regression outputs and **88 immutable objects**, with a SHA-256 manifest. SQLite and live
operational state are excluded. The runner's plan observation retains its compiled-in
producer invocation; phase observations/report carry this exact verifier invocation. This
review supplies attribution and verdict rather than relabelling inherited observations.

## Independent mapping-faithfulness judgment

Inputs: the pinned predicate mapping (`aed79fa4dcb1bed44b493b015b0a3e14e1d042fcc24d3dab3c76856874aae00c`),
FX-U4 contract, SF-REQ-014 specification and design, POSTW1-VERIFY-010 final VERIFIED record,
version history and actual probes. Reviewer: independent JC under WO-220204 allocation.
Decision record: this review and the exact invocation's Issue #94 result comment.

The four mechanical predicate statements match the verified design probes. Commit
`875eba6ec4403a6fe6f32ba8dcbf379884ff5b36` pins the mapping and expected behavior before
implementation `1396a16`. U3's four observables remain distinct, with no credential-denial
oracle. The separate judgment predicate identifies reviewer, inputs and decision record and
does not claim mechanical PASS. Commands reach composed SQLite-backed behavior, and the
discrimination controls execute as reported. These positive observations remain valid.

Acceptance is nevertheless withheld: R1 demonstrates that the promised preservation of
that judgment predicate fails under structured state loss. The producer's accepted residuals
do not authorize waiving this blocking obligation. Green mechanical results do not override
this independently reproduced failure.

## Disposition

Only verifier evidence is added on `b-disp/3daacd5c-b183-4926-aea3-a49066a5dea9`; producer
implementation is unchanged. Return R1 to IMPLEMENT under normal BIU policy. This verifier
branch/worktree remains runtime-managed and retained for BIU repair/closure; the Factory
Director owns SWF-19 landing/evidence disposition and eventual cleanup. No PR, baseline push,
merge, live operation or other-repository change. Tokens and cost UNKNOWN. Local proof only.
