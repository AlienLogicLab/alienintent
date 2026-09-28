# FX-B3P — Canonical Python release-admission precondition gate (WO-220611, Issue #141)

PRODUCER invocation `AlienLogicLab/alienintent#141:PRODUCER:7e2b25fe-fb3b-48eb-a1b8-5d7def75be38`
(worker Morty). IMPLEMENT authorized on Issue #141 against baseline
`93dc10d5969a95717e631496b65ea734531d3089`. The candidate branch starts from `912b917`, which adds
only the retained readiness-assessment record on top of that baseline.

## Governing inputs

- Work unit: Issue #141 (DAG node `B3P`, depends on `S0`/WO-220101). Requirement SF-REQ-002, SWF-21
  amendment 2026-09-21 (`docs/decisions/alienintent-software-factory-plan.md`, section "SF-REQ-002",
  preconditions 1-6).
- Readiness: `docs/evidence/wave2-readiness-assessments/WO-220611.2026-09-28T012151.670323Z.assessment.json`
  (READY).
- Basis this BIU closes, retained unchanged on its own evidence branch: the FX-B3 coverage probe
  of PRODUCER Morty for WO-220506/Issue #126 (`tools/live/fx_b3_admission_coverage.py` and
  `docs/evidence/wave2-proof-fixtures/FX-B3.md` on `b-disp/760ff8cd-68a8-40b8-99cd-2d0a8b09cbf6`
  @ `a11e1dd716fef312698c32ba390ff10c722bf649`). That probe found that preconditions 1-5 were absent
  at the canonical call site, and that the FX-B3 step 8 budget refusal was unreachable because
  `factory_coordinator.py:263` synthesized `{dimension: 1}`. This record does not overwrite that
  finding. The FX-B3P fixture is derived from that probe and keeps its attribution.

## What changed, all within `src/alienintent/execution_coordination`

| Layer | Location | Content |
|---|---|---|
| Domain | `domain/release.py` (additive) | `ReleaseAuthorization`, `BaselineEvidence`, `ReleasePreconditionRefused(ValueError)` with a named `check`, and the pure `admit_release_preconditions`. `admit_release` and `ReleaseRequest` are unchanged. |
| Ports | `ports/release_admission.py` | `ReleaseAuthorizationRecords`, `RevisionResolver` and `ExecutionAllocation`. |
| Application | `application/release_admission.py` | `ReleasePreconditionGate(records, revisions, release_point)` and `BiuLimitAllocation(limits)`, the Python analogue of the Node `execution.biuLimits`. |
| Adapters | `adapters/release_admission.py` | `GitRevisionResolver`: `git cat-file -e <rev>^{commit}`, and `merge-base --is-ancestor` against a release point that must resolve. `StoredReleaseAuthorizations`: a new aggregate `release-authorization:<identity>` in the operational store. |
| Call site | `application/factory_coordinator.py` | Two new keyword-only constructor inputs, `release_gate` and `allocation`. The coordinator calls `_run` → `release_gate.check(item)` → `admit_release(...)`, with the budget taken from `_available_budget`. All of this happens before `propose_release`, before the reservation and before `worker.start`. |

Check semantics are pinned in `admit_release_preconditions`. The checks run in order, and the first
failure refuses:

1. `implementation-authorized`: a record exists, has a non-empty `record_ref`, names this BIU, and
   `authorizes_implement` is true.
2. `baseline-named`: the baseline is an exact full revision (40 or 64 hex). A symbolic name such as
   `main` or an abbreviated SHA is refused.
3. `baseline-resolves`: the resolver finds a commit. The null revision is always refused.
4. `baseline-reachable`: the baseline is an ancestor of the configured intended release point.
5. `authority-wording-consistent`: the record's own text never carries non-authorization wording.
   Any other text the request carries must not carry it either, unless the record names an explicit
   `superseding_record` distinct from its own `record_ref`. That other text is every string in the
   contract, the readiness evidence and the item metadata.

   Detection is case-insensitive and matches three forms:

   - "implementation" or "implement", optionally followed by "is", then `not` or `never`, optionally
     "yet" or "currently", then "authorized" or "authorised". This form extends the bootstrap gate's
     pattern.
   - "implementation is unauthorized".
   - "release [is] refused" or "release [is] denied".

   Phrases such as "READY does not itself authorize IMPLEMENT" do not match, and the test suite
   checks that. The adapter's existence check for `superseding_record` is limited to it being
   non-empty and distinct. The durable record source is responsible for holding the superseding
   record itself.
6. The launch-order precondition holds structurally: refusal records `correlation = "release"`,
   `outcome = "authority-block"` and `hold_reason = "release-precondition:<check>"`. It also registers
   the escalation and blocks dependents, and it returns before any worker effect.

Budget: with an allocation configured, `admit_release` receives, for each dimension, the configured
per-BIU limit less the durable consumption. At present the durable consumption is `attempts`, taken
from the recorded verifier `rejections`. A BIU with no configured limits has no budget. The
existing `release.py` budget check therefore refuses an exhausted, absent or zero dimension.

### Compatibility boundary (declared, not hidden)

Both inputs are opt-in constructor inputs, as the Issue requires ("add fields/inputs additively";
"preserve compatible interfaces"):

- A profile constructed without `release_gate` performs no SWF-21 record checks.
- A profile constructed without `allocation` keeps the prior unmetered budget, which admits every
  required dimension. The literal is now isolated in `_available_budget` and documented there.

Default-on enforcement is not possible under this BIU's own constraints. Every existing coordinator
test constructs `FactoryCoordinator` without a release record, and the Issue forbids weakening those
tests.

No composition root (`offline_profile`, `github_profile`, `sandbox_run_profile`) is changed by this
BIU. Wiring the gate and a real allocation source into the operational profile, and re-pinning
FX-B3/FX-B4 against it, remain WO-220506/#126's own follow-on steps. The FX-B3P contrast cases
record this boundary explicitly. The bootstrap gate `tools/live/release_admission.py` is untouched,
and nothing imports it.

### Known limits, recorded from independent review before VERIFY

- Only `attempts` has durable consumption, taken from recorded verifier rejections. Any other
  allocated dimension is checked against its configured limit.
- `GitRevisionResolver` checks existence and ancestry in the configured local checkout against the
  configured release point. An operator who wants remote truth configures a fetched remote-tracking
  ref, for example `origin/main`. An unavailable `git` or checkout fails closed: the revision does
  not resolve.
- A budget refusal goes through the existing `admit_release` refusal path unchanged, so its record
  carries no `hold_reason`. Precondition refusals carry `release-precondition:<check>`.

## Pinned cases and observed result

The fixture command is `PYTHONPATH=src python3 tools/live/fx_b3p_release_preconditions.py --out <file>`,
and its test is `tools/live/test_fx_b3p_release_preconditions.py`. The fixture uses a real
`SQLiteOperationalStore`, `GitHubProjectsWorkManagement` with local snapshot rows,
`StoredReleaseAuthorizations`, and `GitRevisionResolver` over a real temporary git repository:
`baseline` is on `main`, and `diverged` is a side-branch commit that `main` cannot reach. The release
point is `main`.

| Case | Expected starts | Expected refusal |
|---|---|---|
| positive-control | 1 | — |
| p1-no-release-record | 0 | implementation-authorized |
| p1-record-does-not-authorize | 0 | implementation-authorized |
| p2-no-exact-baseline (`main`) | 0 | baseline-named |
| p3-null-baseline (`0`×40) | 0 | baseline-resolves |
| p3-absent-baseline (`b`×40) | 0 | baseline-resolves |
| p4-unreachable-baseline | 0 | baseline-reachable |
| p5-unsuperseded-denial | 0 | authority-wording-consistent |
| p5-superseded-denial | 1 | — |
| budget-exhausted (`attempts: 0`) | 0 | admit_release (budget) |
| budget-unallocated (no limits for this BIU) | 0 | admit_release (budget) |
| budget-allocated (`attempts: 1`) | 1 | — |
| budget-dimension-unallocated (FX-B3 step 8 shape) | 0 | admit_release (budget) |
| contrast-ungated-no-record | 1 | — (no gate configured) |
| contrast-unmetered-dimension | 1 | — (no allocation configured) |

The observed result, with its exact source revision, command and exit status, is retained in
`FX-B3P/result.json`.

Enforcement tests:

- `tests/execution_coordination/domain/test_policy.py` has domain cases for every check. It also
  shows the existing budget check refusing an exhausted attributable allocation.
- `tests/execution_coordination/test_factory_coordinator.py` has call-site cases over real SQLite
  and git. There is one case per precondition with zero invocations, the superseding control, and
  allocation exhaustion or absence against availability. A consumption case shows that a receipted
  rejection exhausts `attempts: 1` but not `attempts: 2`.

No existing test in either file was changed.

Regression pack `canonical-release-precondition-gate` is registered in
`tools/verification/feature_regressions.json`.

## Fixture pinning order

The expected outcomes above are taken one-for-one from the Issue's acceptance criteria and the
FX-B3 probe's pinned cases. They are not derived from observed behaviour.

The fixture code itself was written in the same invocation as the implementation, and after it.
Both land together in this candidate. No separate earlier pin commit exists, and a verifier should
weigh that deviation from the stated proof order.

The contrast cases guard against the fixture passing vacuously: an unconfigured profile still
launches the same invalid inputs.
