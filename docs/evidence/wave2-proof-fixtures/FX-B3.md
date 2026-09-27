# FX-B3 / FX-B4 — Pre-execution coverage finding (WO-220506, Issue #126, DAG node B3)

**Status: HELD before any operational write. Returned to the scope owner.** Neither phase 1 (FX-B3,
`AlienLogicLab/alienintent-sandbox` / Project #2) nor phase 2 (FX-B4, `AlienLogicLab/alienintent` /
Project #1) was executed. No Issue, Project item, field, comment or status was created or changed on
either board. No worker, provider or model was launched. No FX-B3/FX-B4 operational result is claimed.

## Pinned inputs

| Input | Value |
|---|---|
| Invocation | `AlienLogicLab/alienintent#126:PRODUCER:cf15ef65-25bc-406d-9c9f-bd6263e3279b` (PRODUCER Morty) |
| Baseline | `71b37f210d58aa19e786c63057600d451580516b` (named by the 2026-09-28 release record on #126) |
| Work unit | `docs/work-units/wave2/WO-220506.md`, sha256 `7e5badd1540fca860d9c8677a1045b8e949c86b12c7e990fa658ce7fc1a69976` (equal to the input of the READY assessment `WO-220506.2026-09-27T232551.622371Z`) |
| Node predicate | `docs/evidence/wave2-dependency-dag.json`, node B3 `completion_predicate` and `release_preconditions` |
| Probe | `tools/live/fx_b3_admission_coverage.py`, sha256 `7920febef31518a517d36129a9a2c5bed79ffacea9d69d9a03a320bbdbc709c9` |
| Probe result | `FX-B3/coverage-probe.json`, sha256 `bbdd3a67a7be4b3841a9f3f308baeefb1dccca67116ad59e6c8cd28be214e07f` |
| Command | `PYTHONPATH=src python3 tools/live/fx_b3_admission_coverage.py --out docs/evidence/wave2-proof-fixtures/FX-B3/coverage-probe.json` (Python 3.12.3) |
| Exit status | `1` (4 of 11 cases do not meet the pinned expected outcome) |
| Label | **LOCAL, FX-L1-equivalent.** Not operational evidence; cannot satisfy FX-B3/FX-B4 acceptance. |

The BIU's proof order requires pinning the fixture against the node predicate *before*
implementation and demonstrating discrimination for each mechanical control. The probe does that at
the canonical prelaunch call site the fixture pins (`FactoryCoordinator._run` → `admit_release`,
`factory_coordinator.py:255-268`), composed over the real `SQLiteOperationalStore` and
`GitHubProjectsWorkManagement`. Only the upstream snapshot rows and the worker (a counting double that
answers a correlated `authority-block`) are local. That is sufficient to decide reachability: every
pinned FX-B3/FX-B4 input reaches `admit_release` only through the fields shown below, whichever board
the rows are read from.

## Observations

| Case | Source | Expected starts | Observed starts | Refusing mechanism observed |
|---|---|---|---|---|
| positive control | FX-B3 step 2 | 1 | 1 | admitted, launched once |
| identity replay | FX-B3 step 3 | 1 total | 1 total | recorded-outcome eligibility guard. `release.py:59-61` is **not reached** because the coordinator calls `admit_release({}, …)` with an empty ledger |
| policy/source mismatch | FX-B3 step 4 | 0 | 0 | `admit_release` (`release`-correlated authority-block) |
| readiness digest mismatch | FX-B3 step 5 | 0 | 0 | `admit_release` |
| unsatisfied dependency | FX-B3 step 6 | 0 | 0 | `_eligible` dependency gate. `release.py:71-73` cannot fail here because the call site passes `frozenset(item.dependencies)` as the satisfied set |
| missing capability | FX-B3 step 7 | 0 | 0 | `admit_release` |
| **missing budget dimension** | FX-B3 step 8 | 0 | **1** | **none.** The call site synthesizes `{dimension: 1 for dimension in required_dimensions}` (`factory_coordinator.py:263`), so `release.py:76-78` can never fail |
| eligibility: explicit-human profile, not released | DAG "plus eligibility" | 0 | 0 | `_eligible` release gate |
| **no durable release record / no exact baseline** | DAG B3 preconditions 1-2 | 0 | **1** | **none.** No input carries a release record or requires a named SHA |
| **baseline unresolvable / not ancestral** | DAG B3 preconditions 3-4 | 0 | **1** | **none.** `baselines=("000…0",)` is admitted |
| **unsuperseded denial wording** | DAG B3 precondition 5 | 0 | **1** | **none.** A contract carrying "Implementation is **not** authorized" is admitted |

## Finding

1. **The pinned fixture and the node predicate name different "six preconditions."** B3's
   `release_preconditions` in the approved DAG (and `wave2-technical-plan.md`, R6 row) are the six
   2026-09-21 SWF-21 preconditions:
   - durable release record explicitly authorizes IMPLEMENT;
   - exact baseline named;
   - baseline resolves;
   - baseline reachable from the release point;
   - no stale denial wording without a superseding record;
   - zero launches until those five pass.

   WO-220506.md FX-B3 steps 3-8 map "six preconditions" onto `admit_release`'s own checks
   (`release.py:57-79`) instead. Those checks are replay, policy/source, digest, dependency,
   capability and budget. The two sets are different.
2. **The canonical prelaunch path has no implementation of DAG preconditions 1-5.** They exist only in
   the bootstrap gate `tools/live/release_admission.py`, which is the mechanism B3 → R6 is meant to
   prove a replacement for. `ReleaseRequest` has no field that could carry them. A meaningful invalid
   case for each of them launches an actor at the canonical call site.
3. **Even under the fixture's own mapping, step 8 is unreachable.** Steps 3 and 6 are discharged by a
   different guard than the fixture names. Step 8 cannot refuse at all, so it launches an actor. That
   is a failing discriminating probe, which is a pinned stop condition of this BIU.

The BIU's own scope decides the next step: *"Use existing release requirement authority; if
implementation coverage is missing, return to scope owner, never expand 015 into release
ownership."* Adding release-record, baseline or wording checks, or real budget accounting, to
`admit_release`/`FactoryCoordinator` is release-admission implementation owned by SF-REQ-002, the
canonical owner named in `wave2-specified-requirements.json` BOOTSTRAP-M15. It is not this proof
node's work. The PRODUCER therefore did not implement it.

Running FX-B3/FX-B4 as pinned would write probe items to the sandbox board and to production
Project #1. Those runs would retain four deterministic failures already known here, and would still
not exercise the six predicate preconditions. The phase-2 authorization permits "only the minimum
reversible Project-state writes required to demonstrate the boundary." Because this boundary cannot
be demonstrated as pinned, the minimum here is zero, so no write was made.

## Decision required from the scope owner (via Program Director)

One of the following, recorded durably on #126, is needed before this BIU can resume:

- **(a) Coverage first.** Route the missing canonical coverage (DAG preconditions 1-5 at the
  `FactoryCoordinator` prelaunch boundary, and real available-budget input to `admit_release`) to the
  SF-REQ-002 release-admission owner as its own BIU. This BIU would depend on that BIU and re-pin
  FX-B3/FX-B4 against the DAG's six preconditions.
- **(b) Re-point the boundary.** Decide that the "actual live-profile prelaunch boundary" for B3 is
  the retained bootstrap gate (`tools/live/release_admission.py` in front of b-disp on Project #1).
  Re-pin FX-B3/FX-B4 against it and state explicitly that this does not by itself satisfy R6's
  replacement requirement.
- **(c) Accept a narrowed predicate.** Accept the fixture's `admit_release` mapping as a Founder
  amendment of B3's predicate, including disposition of the step-8 budget gap. Only the Founder can
  make that directional change.

Preserved: the READY assessment, the release record, both phase target bindings and every predecessor
proof are unchanged. This record supersedes nothing.
