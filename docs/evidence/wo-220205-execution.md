# WO-220205 (U5, SF-REQ-051) PRODUCER execution record

**Invocation:** `AlienLogicLab/alienintent#97:PRODUCER:a206da1a-2d97-4fe5-86c7-42e8e9eacaa3`.
**PRODUCER:** Morty (`morty-worker`, Claude `claude-opus-5-5`).
**Branch:** `b-disp/1108187c-0789-4150-a90c-1c83dd6e7673`.
**Admission baseline:** `7be12188edf632710fe842d95fc70b444e2ed279`, equal to `origin/main` at admission. The worktree was clean, and baseline pytest passed 602/602.

**Authority:** Issue #97, whose RELEASED comment authorizes IMPLEMENT for U5 only. Direction-dependent admission is implemented as `ARCHITECTURE_AUTHORITY_HOLD`. This BIU does not dispose R2-GAP-051-EDGE-AUTHORITY.

## Sequence

| Step | Commit | Content |
|---|---|---|
| Pin | `d56a18e` | `docs/evidence/wo-220205-fx-u5.md` (contract) and `wo-220205-fx-u5-predicate-mapping.json` (sha256 `e000d1f9…fef3a`), committed before any implementation file |
| Implement | `b5fecee` | domain, port, application, composition adapters, profile wiring, 30 tests, FX-U5 runner, and contract Revision 1 (three PRODUCER self-review guards, recorded before any evidence run) |
| Evidence | this commit | `docs/evidence/wo-220205-fx-u5/`, the run over candidate `b5feceefc7aea14289a68fc2148b4c4b171c34ad` |

## Predecessor admission

The table in the contract lists U2 `d0eacfb` and U4 `c8ed707`. Both are ancestors of the
baseline, and their JC ACCEPT comments and retained JC receipt commits `4f03da9` and `42d5219`
were retrieved. U5 consumes U4 `ProofPlanning`, `derive_plan`, `evaluate_control` and
`proof_order_diagnostics` unchanged, together with the U3 premise reader and the S1 evidence
values. No predecessor file is modified.

## Results at candidate `b5fecee`

All raw output is retained in `docs/evidence/wo-220205-fx-u5/`, and `sha256.json` covers every file.

| Command | Exit | Observed |
|---|---|---|
| `PYTHONPATH=src python3 tools/evidence/fx_u5_evidence.py --output <external>` | 0 | 23/23 controls `QUALIFIED_KILL`; proof-order diagnostics `[]` (`run.out`, `report.json`, 69 control logs) |
| `PYTHONPATH=src python3 -m pytest -q tests` | 0 | 632 passed (602 baseline + 30 FX-U5) (`pytest.out`) |
| `python3 tools/fitness/check_architecture.py --root src/alienintent --check all` | 0 | PASS (`architecture.out`) |
| `node scripts/check.mjs all` | 0 | no failure (`check-all.out`) |

The run identities are:

- FX-U5 plan digest `sha256:2e674e6adc31a288fa49377da52b5c17e193d4fc77e93e31c13c6c5169705f43`, over the 8 obligations of the pinned mapping and the node acceptance IDs AC-01, AC-02, AC-04, AC-05 and AC-06;
- requirement revision `sha256:3030164a…2732c`;
- fixture digest `sha256:39806be3…b244d`;
- contract sha256 at run time `74a71aa8…ffd9` (the contract including Revision 1);
- `report.json` sha256 `6bf467f9…13de`.

The run retained 70 immutable evidence objects: the plan and the 69 control observations, each chained to the plan. They are in `objects/`.

The controls, with their enforcement obligation and the fault each one applies exactly once:

- **051-architecture-boundary:**
  - `authority-hold-bypassed`: the open-authority hold is removed;
  - `observed-edges-as-policy`: a declared edge listed in `observed_edges` is exempted;
  - `architecture-check-ignored`: a failing existing check is ignored; the real checker runs over `tests/fixtures/fitness/layering`;
  - `interface-compatibility-removed`.
- **051-review-applicability:**
  - `review-before-checks-accepted`
  - `self-review-accepted`
  - `shared-invocation-accepted`
  - `stale-design-review-accepted`
  - `unauthorized-reviewer-accepted`
  - `stale-reverified-in-place`
- **AC-01:** `incomplete-design-accepted` and `unexplained-inapplicability-accepted`.
- **AC-02:** `material-decision-open-accepted`, `unbounded-local-choice-accepted`, `blocking-finding-verified` and `prior-rejection-overridden`.
- **AC-04:** `premise-evidence-ignored` (U3 `UNACHIEVABLE_PREMISE` for `CREDENTIAL_DENIAL`, with every other check green) and `held-design-verified`.
- **AC-05:** `stale-vector-accepted`, `history-dropped` and `truncated-history-accepted`.
- **AC-06:** `readiness-gate-bypassed` and `composition-disconnected`. For `composition-disconnected`, the domain test class stayed green during the fault (exit 0).

A dry run before the evidence run found that `history-dropped` was **not** qualified. Its fault
surfaced as a test ERROR, and the U4 battery classified it `UNRELATED_FAILURE`. The test was
repaired to assert the result type first, as the U4 tests do. The committed evidence is the
later full run.

## Judgment retained, not claimed

The JUDGMENT obligation `SF-REQ-051/SF-REQ-051-AC-04/premise-review-judgment` belongs to the
independent VERIFIER, and nothing here discharges it. It covers:

- whether the runnable bindings faithfully realize the SF-REQ-051 probes;
- whether inapplicability reasons are proportional;
- whether a choice labelled local is really local.

The mechanical guards can only refuse. They never produce approval: a VERIFIED state requires an
attributed, authorized, non-self review of the exact design, report and revision vector.

## Boundaries and residuals

- **Scope.** No Project lifecycle state, service, database or approval lane is added. `LifecycleStage` is unchanged, and the store holds only `upstream:design:*` aggregates.
- **Direction policy.** The R1 edge table is not implemented against production. `observed_edges` is read only as descriptive data and is never consulted by admission. The conditional R1 direction fixtures are not run and not claimed. A disposed authority still yields `DIRECTION_SCOPE_UNREVIEWED`, because no reviewed scoped policy exists; that decision belongs to the Founder.
- **Consumer seam.** `DesignReadiness` is the design gate consumed by readiness processing. The SF-REQ-013 compiler and the SF-REQ-015 readiness consumer are sibling nodes and are not implemented or wired here.
- **Measurements.** Tokens and cost are UNKNOWN (no billing telemetry), and are not zero.
- **Local proof only.** No live operation was performed, and no operational success is inferred.
