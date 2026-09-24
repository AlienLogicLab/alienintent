# FDH-92 — Issue #92: treat runtime claims at or above the WIP limit as intentionally full

This is the bounded work of existing Issue **#92**, "FDH-01 follow-up P2: treat runtime claims >= wipLimit
as WIP intentionally full", run through #92's own lifecycle. It is a follow-up to FDH-01 (#89). It is not a
Wave 2 DAG node and adds no new Issue.

Baseline: `origin/main` @ `0eda915`.

## Intent

A transient worker handoff overlap must be classified as the idle reason `WIP_INTENTIONALLY_FULL`. It must
not be recorded as a refusal, or as having no eligible work. This is one of the two remaining conditions on
the Factory Director Host retirement threshold (Founder direction, 2026-09-24).

## Authority

- Issue #92: its defect statement, bounded scope and the evidence comment
  https://github.com/AlienLogicLab/alienintent/issues/92#issuecomment-5811652927.
- Founder direction 2026-09-24, relayed through Director inbox entries `founder-operating-mode-20260924T091522Z`
  (P2) and `founder-priority-91-92-20260924T104141Z`: make #91 and #92 the next priority, and prove each fix
  with a discriminating test.

## Current state (evidence)

- `tools/orchestration/factory_director_inputs.py` `derive()` sets
  `executable_capacity = runtime.claims < wip_limit` and `wip_intentionally_full = runtime.claims == wip_limit`.
  When `claims > wip_limit`, both are false.
- `FactoryDirectorHost._idle_reason` in `tools/orchestration/factory_director_host.py` then falls through.
  With worker work pending it returns `EXECUTION_CAPACITY_UNAVAILABLE` (REFUSED). With no control required it
  returns `NO_ELIGIBLE_AUTHORIZED_WORK`.
- Runtime contract `docs/operations/factory-director-runtime-contract.md` §10 documents equality: the
  predicate table says "active runtime claims = WIP limit", and precedence item 6 says "WIP is not exactly
  full (claims exceed the limit)".
- Three live occurrences, each with `activeClaims=2`, `wipLimit=1`: #81 at 08:55:32Z and 08:59:10Z
  (`EXECUTION_CAPACITY_UNAVAILABLE`), and #83 at 09:29:48Z (`NO_ELIGIBLE_AUTHORIZED_WORK`). Evidence:
  `docs/evidence/fdh-01-live-proof/20260924T080401Z/` (`FINDINGS.txt` P2, `P2-diagnostics-0855.json`) and the
  #92 comment above. In no case did the Director launch incorrectly. This is a reason-classification defect.

## Scope (bounded extent)

1. In `derive()`, set `wip_intentionally_full` to `runtime.claims >= wip_limit`. `executable_capacity` stays
   `runtime.claims < wip_limit`, so the two remain exact complements.
2. Keep `_idle_reason` precedence order unchanged. Director-only control (attention, inbox, selection) must
   still never be suppressed by full WIP, including when claims exceed the limit.
3. `EXECUTION_CAPACITY_UNAVAILABLE` stays a recognised reason identifier. It is a persisted compatibility
   marker in `history.jsonl`, so do not delete or rename it. Once the predicates are complements it may
   become unreachable. If so, say that plainly in a code comment and in the contract text. Do not invent a
   new condition for it.
4. Update runtime contract §10 (the predicate table and idle-reason precedence) to say "at or above the
   limit". Keep contract version **1**: this corrects a documented classification and adds no obligation.
5. Tests in `tools/orchestration/test_factory_director_inputs.py` and `test_factory_director_host.py` cover
   `claims > wipLimit` in three cases: worker work pending, no control required, and Director-only control
   pending. Update `test_factory_director_docs.py` if it pins the changed contract text.

## Non-goals

- Changing `wipLimit`, the Node runtime's claim behaviour, the crash-loop guard or the durable-state
  fingerprint.
- Installing, restarting or reconfiguring the live host. Deployment is a separate, recorded Factory Director
  action after landing (see Deployment).
- Retiring, disabling or removing any continuity mechanism, unit or service.
- The live-proof procedure's host env file. That is #91.

## Acceptance criteria

1. With `claims = 2`, `wipLimit = 1` and only worker work pending, the adapter derives
   `wip_intentionally_full = true`, `executable_capacity = false`, and the host's reason is
   `WIP_INTENTIONALLY_FULL` (IDLE).
2. With `claims = 2`, `wipLimit = 1` and no control required, which is the #83 09:29:48Z case, the reason is
   `WIP_INTENTIONALLY_FULL`, not `NO_ELIGIBLE_AUTHORIZED_WORK`.
3. With `claims = 2`, `wipLimit = 1` and an unprocessed inbox entry (and, separately, an unresolved
   escalation), the reason is `None`. The host launches or keeps a Director episode, as it does today at
   `claims == wipLimit`.
4. The `claims == wipLimit` and `claims < wipLimit` behaviour is unchanged. All existing host and adapter
   tests pass.
5. Discriminating proof. Each new test from criteria 1–2 is shown **failing** on the baseline `0eda915`
   code, or on a variant restoring `==`, and **passing** on the candidate. The criterion-3 tests already
   pass on the baseline, because Director-only control is checked before capacity there. They are regression
   guards: they pass on the baseline and the candidate, and are shown **failing** against a deliberately
   wrong variant in which full WIP suppresses Director-only control (the `not values.director_only_control()`
   guard on the `WIP_INTENTIONALLY_FULL` branch removed). Record the commands, exit statuses and counts.
6. Runtime contract §10 and the code agree. `test_factory_director_docs.py` passes.
7. `node scripts/check.mjs all` exits 0. `python3 -m pytest -q tools` shows no new failure. The known baseline
   failure `tools/orchestration/test_director.py::test_substantial_technical_analysis_routes_to_codex_primary`
   is non-hermetic: it reads the live `~/.codex/config.toml`. It is dispositioned as in ARP-01 and must not be
   modified here.

## Verification obligations

An independent VERIFIER retrieves the exact candidate SHA in its own worktree and re-runs criteria 1–7. It
applies the `==` and suppressing-variant negative controls itself and records commands, exit statuses and counts.

## Evidence obligations

Retain the candidate branch and full SHA, the commands, exit codes, test counts and the negative-control
results under `docs/evidence/fdh-92/`.

## Deployment (Factory Director, after landing)

The fix takes effect only in the installed host copy under
`~/.local/share/alienintent-bootstrap/factory-director-host/`. After DONE, the Factory Director refreshes it
through `tools/orchestration/install_factory_director_host.sh` from the landed commit, and restarts the host
service between episodes while no Director episode is live. That is a deliberate, recorded step. It is not a
retirement. "DONE with proof" for the Founder report also looks for an observed handoff overlap that the
deployed host classifies as `WIP_INTENTIONALLY_FULL`. The next BIU's PRODUCER→VERIFIER handoff is the
expected opportunity. Workers do not perform this step.

## Execution packet and allocation

- PRODUCER Morty on Claude; independent VERIFIER JC on Codex (Founder routing policy, 2026-09-24).
- Concurrency 1.
- 3 execution cycles and 1 replacement per phase, bound in `execution.biuLimits` for #92 before release.
- Wall-clock bounded by systemd supervision.

Landing: SWF-19. Merge the accepted candidate branch directly into `main`, preserving the accepted SHA.
**Do not open a pull request.** AlienIntent does not use pull requests.

Release authority is not granted by this document.

## Stop and escalation

Stop on:

- a source revision mismatch;
- any need to change `wipLimit`, Node runtime claim behaviour or idle-reason precedence order;
- any change that would let full WIP suppress Director-only control;
- a criterion 1 or 2 test that does not fail on the baseline, or a criterion-3 guard that does not fail
  against the suppressing variant.

Scope questions go to the Factory Director.
