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

> **Superseded in part by candidate cycle 2 (below).** The composition-root statement in this
> subsection described cycle 1 (`596c980`). The VERIFIER rejected it, and cycle 2 wires the gate and
> allocation into the operational profiles. The text is kept as the record of what cycle 1 claimed.

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

The observed result is retained in `FX-B3P/result.json`. It was run against source revision
`596c98068f65fff7657e728fb2a0120eab914209` and records the command, the exit status (0), the output
sha256 and the full case output. All 15 cases match their pinned expectations (`all_match: true`).

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

## Candidate cycle 2 — REJECT repair

Invocation: `AlienLogicLab/alienintent#141:PRODUCER:e63dde70-dfdf-425a-921b-3c6611179fda` (worker Morty).
Cycle 2 builds on cycle-1 candidate `6ba67e9` on branch `b-disp/6897ec54-…`. It answers VERIFIER
invocation `…#141:VERIFIER:69ad8f97-…` (RESULT=REJECT), which raised two findings.

### Finding 2 — the operational profiles did not enforce the gate (repaired)

Implementation commit `d408caf7c6a30367b00800af1d1a14c90a4eb0cd` wires the gate and the allocation
into the operational profiles through a new composition module,
`src/alienintent/composition/release_admission.py`:

- `SandboxRunProfile` is the `alienintent --profile-factory` live profile.
  `GitHubProfileComposition` is the GitHub-backed profile. Both now always build their
  `FactoryCoordinator` with `release_gate` and `allocation` from `compose_release_admission`. Neither
  exposes a way to omit them.
- **Release records** are durable `release-authorization:<BIU>` aggregates in the profile's own
  operational store. They are exposed as `profile.release_records`.
- **Revisions** come from `GitRevisionResolver` over the profile's checkout.
  `GitHubProfileComposition` takes a `checkout`. Without one, no baseline resolves and every
  release is refused.
- **Allocation** comes from the profile document's `release_admission.biu_limits`. For
  `GitHubProfileComposition` it comes from a `ReleaseAdmissionConfig`. This is the Python analogue
  of `execution.biuLimits`. When the section is absent, no BIU has an allocation, so any contract
  with a required budget dimension is refused.
- **Release point** comes from `release_admission.release_point` and defaults to the checkout's
  `HEAD`. That is the control-plane checkout of the baseline branch. An operator whose checkout
  may sit elsewhere configures an explicit ref such as `origin/main`. A malformed section is refused when the profile is composed (`ReleaseAdmissionRejected`).
- **`OfflineProfile`** is the scripted offline double. No operational entry point constructs it;
  `src/` uses it only in the proof harnesses `offline_proof.py` (`OfflineProofSubstrate`) and `lifecycle_capstone.py` (`CapstoneSubstrate`). It takes a supplied `ReleaseAdmission` and forwards it.
  It stays opt-in because the existing `test_factory_coordinator.py` cases drive it without release
  records, and the Issue forbids weakening them.

Consequences for existing fixtures:

- **Fixtures that drain work through the operational profiles** now record what an operator
  supplies. These are the FX-K3 `k3_fixture.py` and the `test_sandbox_run_profile.py` whole-loop
  tests. They record one release authorization per BIU at the checkout's baseline, plus a per-BIU
  allocation, using `tests/support/release_admission.py`. No assertion was changed.
- **The role-binding test** (`test_role_binding.py::test_the_binding_guard_owns_no_state…`) has an
  aggregate-prefix allow-list. It now names `release-authorization:`, the gate's record and not
  the guard's. The source check that the guard writes nothing is unchanged.

Discriminating tests are in `tests/composition/test_release_admission_wiring.py`. They drive the
real `SandboxRunProfile` and `GitHubProfileComposition` constructors, and no case injects a gate.
The unreachable case uses a real side-branch commit. These tests were revised at the evidence commit,
after the `d408caf` fixture run. No `src/` or fixture file changed after that run.

- the profile refuses when there is no record, when no allocation is configured, when the baseline
  is unreachable, or when no checkout exists, each with zero starts;
- a fully authorized profile starts exactly one producer and reaches DONE;
- config parsing and the fail-closed default behave as specified.

FX-B3P gains five `profile-*` cases through the production `GitHubProfileComposition` constructor.
They supply only configuration and durable records, never a gate:

| Case | Expected starts | Expected refusal |
|---|---|---|
| profile-no-release-record | 0 | implementation-authorized |
| profile-unreachable-baseline | 0 | baseline-reachable |
| profile-no-allocation | 0 | admit_release (budget) |
| profile-unmetered-dimension (FX-B3 step 8 shape) | 0 | admit_release (budget) |
| profile-positive-control | 1 | — |

The `contrast-*` cases stay at the bare `FactoryCoordinator` level. They show that the refusals come
from the gate. The `profile-unmetered-dimension` case shows the same shape is now refused through
the operational profile.

Observed result: `FX-B3P/result-cycle2.json`. It was produced by running the fixture against
`d408caf` on a clean tree:

- exit status 0
- `all_match: true` across all 20 cases
- the command, output sha256, source tree and fixture blob are recorded in the file

The cycle-1 observation `FX-B3P/result.json` is retained unchanged.

The regression pack `canonical-release-precondition-gate` now also selects the composition roots,
the wiring test and the fixture support. It runs `tests/composition/test_release_admission_wiring.py`.

### Finding 1 — no committed `.alienintent/feature-regressions.json` (custody rule)

A commit cannot carry a receipt that names its own SHA. For that reason, the landed custody rule
does not track the receipt. That rule is in [FX-C.md](../FX-C/FX-C.md#feature-regression-receipt-custody)
and was reaffirmed by FX-E1 (`5a98c26`). The runtime (`CliWorkerProvider._feature_regressions`)
writes the receipt into the verifier's checkout of the exact candidate. Otherwise the verifier
produces it at the retrieved SHA:

```
python3 tools/verification/run_feature_regressions.py --base 93dc10d5969a95717e631496b65ea734531d3089 \
  --candidate HEAD --receipt .alienintent/feature-regressions.json
```

The PRODUCER records its own receipt for the published SHA on Issue #141 for comparison. That
receipt does not replace the verifier-side one.

## Cycle 3 — verifier REJECT of `29c8e45` (receipt custody only)

Verifier `AlienLogicLab/alienintent#141:VERIFIER:d94eaf5b-3b32-4822-9ebc-38fe34711145` gave no
finding against the implementation, fixture or wiring. Both applicable packs passed at `29c8e45`.
It rejected only because `.alienintent/feature-regressions.json` was absent from the published tree.
It had written the receipt it generated to `/tmp`, not to that path in its own checkout.

A tracked receipt cannot satisfy the admission check. `read_verdict`
(`src/alienintent/invocation_runtime/application/real_worker.py`) accepts a receipt only when its
`candidate` field equals the verified revision. A receipt committed in revision C records C's
parent, so the check always refuses it. The admissible receipt for revision C is therefore the one
present at `.alienintent/feature-regressions.json` in the verifier's own checkout of C, beside
`.alienintent/verdict.json`, where `read_verdict` reads it. Either the runtime writes it there, or,
when the runtime is not the launcher, the verifier generates it there at the retrieved SHA with the
command above (`--receipt .alienintent/feature-regressions.json`, not a path outside the checkout).
The same custody repair led to ACCEPT on Issue #129 (verifier `3fe3223f`) and Issue #140 (verifier
`8f914881`).

Cycle 3 changes only this document. `src/`, `tests/`, `tools/` and the retained results
`result.json` and `result-cycle2.json` are byte-identical to `29c8e45`.

### Remaining known limits (unchanged from cycle 1, plus one)

- **Durable consumption.** It exists only for `attempts`, taken from recorded verifier rejections.
- **Budget refusals.** They keep the untagged `admit_release` refusal record.
- **Populating release records.** Nothing yet copies release records from the Issue's
  release-record comments into a profile's store. An operator or tool records them through
  `profile.release_records`. Until one is recorded, the operational profiles refuse release,
  which is the fail-closed behaviour SWF-21 requires. Automating that population is operational
  wiring for WO-220506/#126, together with the FX-B3/FX-B4 re-pin, and is not claimed here.
