# WO-220202 independent verifier receipt

Invocation: `AlienLogicLab/alienintent#80:VERIFIER:40b0973a-b4a9-470e-ae06-e8618735a2f7`.
Worker JC; GitHub identity `jc-worker`. Fresh separate runtime worktree.

Authority: Issue #80 body, RELEASED comment 5808501234, work packet and allocation
for WO-220202. Review limited to DAG node U2 and SF-REQ-012.
Admission baseline: `ec9645adc4013c83b405f9080dde3215af90dcb5`.
Reviewed candidate: `d0eacfb6dd8626b07ff1d99e9c633294f13d9de4` on
`b-disp/329464b3-4928-4c6f-bffb-a58291395b1c`.
Fetched directly from origin and checked out by SHA. Remote ls-remote readback
matched exactly; admission baseline ancestry check exited 0.

## Fresh observations

All commands below were executed with `rtk proxy` in the exact candidate checkout.

| Command | Exit | Observation |
|---|---|---|
| `env PYTHONPATH=src python3 -m pytest -q tests` | 0 | 526 passed in 62.75s |
| `python3 tools/fitness/check_architecture.py --root src/alienintent --check all` | 0 | PASS: all architecture fitness checks |
| `node scripts/check.mjs all` | 0 | Required runtime, preflight, RAI and policy checks passed |
| `python3 -m pytest -q tools` | 1 | 464 passed, 1 known baseline failure in 1.93s |
| `env PYTHONPATH=src python3 tools/evidence/fx_u2_evidence.py --output /tmp/jc-issue80-verifier-fx-u2 --invocation AlienLogicLab/alienintent#80:VERIFIER:40b0973a-b4a9-470e-ae06-e8618735a2f7` | 0 | 15/15 intact/fault/restored controls discriminated |

The tools failure is exactly the predeclared out-of-scope
`tools/orchestration/test_director.py::test_substantial_technical_analysis_routes_to_codex_primary`:
expected `gpt-6-astra`, observed `gpt-5.6-terra`. It reads host configuration.
No tools or host configuration was changed.

Additional independent composed probes used the candidate Harness with four requirements:
missing Scope, unapproved source provenance, an unresolved dependency, and a complete
independent requirement. The first three produced MISSING_SCOPE, MISSING_AUTHORITY,
and AMBIGUOUS_DEPENDENCY and HELD; the fourth remained ELIGIBLE_FOR_PREPARATION.
Assertions passed (exit 0).

U1 inventory domain/application, inventory tests and all `docs/evidence/wo-220201*`
receipts were unchanged against admission baseline. The producer report hash verified
as `fe4e17a19549131f335c126f588581d31e17bb86c8741d6d0df6cbbed0e7f03e`;
all 45 referenced raw log hashes matched. Fresh verifier report hash:
`83eb672d7bf4f6310f4941ad6ac579a6af123e054ebcab2b959592070227c0da`.
All its 45 raw log hashes matched too. Fresh report, logs and observation objects are
retained byte-for-byte under `wo-220202-verifier-fx-u2/`.

Evidence metadata caveat: the runner hardcodes observation observer `Morty` and
report text `independent verifier pending`. Those inherited harness fields are not
this review's identity or verdict. The supplied invocation, exact candidate SHA,
this receipt and the Issue result establish JC's independent execution. An earlier
local run using the default producer invocation also passed; only the second run,
with the explicit verifier invocation, is retained here.

## Independent assessment

AC-01: source-linked OPEN questions and precise branch-local blocked reasons verified.
AC-02: wrong actor, revision and unmatched/unrecorded decisions hold; an exact durable
DecisionInbox answer resolves only its matching finding. Revision changes stale prior
findings; reopened cycles require fresh answers.
AC-03: complete mechanical input remains preparable; independent semantic questions
hold the affected requirement while preserving intent and inventory.
AC-04: unrelated input remains preparable, dependency holds remain local, and question
and answer paths do not launch workers. Composed tests and injected faults discriminate.

No blocking finding. ACCEPT applies only to the reviewed producer candidate SHA above.
STALE questions remaining in the Inbox open list are the disclosed residual: attempts
to answer them cannot resolve stale findings. A withdraw API remains with the
control_plane owner, outside this node. Tokens and monetary cost are UNKNOWN.
Local checks do not establish live operational success.

## Custody and closure

Verifier evidence branch: `b-disp/0e0aaa49-5e76-4faf-8fcb-7af7fe426d1a`.
Owner: JC, this invocation. Unique content: this receipt and fresh FX-U2 raw evidence.
This runtime-managed branch is retained under BIU closure policy, pending Factory
Director SWF-19 closure; it does not replace the accepted producer candidate.
No PR, baseline push, merge into main, release or live operation was performed.
