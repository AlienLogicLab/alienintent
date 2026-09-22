# Critical bootstrap invocation-duration repair plan

> For agentic workers: use subagent-driven-development and test-driven-development.
> Source repair is authorized under Architecture Authority §42, SWF-01 and the
> governing directive. Live activation is a separate recorded admission.

**Goal:** Make an explicitly bounded bootstrap invocation enforceable independently
of dispatcher event-loop progress, including ordinary orphaned/session-detached
descendants, so SWF-09 admission can be satisfied without a waiver.

**Architecture:** Add an opt-in Linux systemd transient-service execution adapter
behind the existing launcher. Bind each unit to an existing immutable invocation
identity; persist intent before launch and read back exact ownership. Use the
existing dispatcher/result path. No new scheduler, lifecycle policy, provider
routing, canonical Python capability, or bootstrap retirement.

**Tech stack:** existing Node runtime/tests; host GNU/Linux unified cgroups and
systemd 255 user manager. No new package dependency or credential.

## Design constraints

- Preserve current Git/GitHub identities, compatibility markers, provider argv,
  sandbox flags, authentication home, environment allowlist, worktree and logs.
- Existing direct-mode installations and historical resources remain readable;
  absent enforcement is explicitly unbounded, never eligible evidence for a new
  hard-bound packet. Systemd mode requires all positive limits and executable
  bindings and must not silently fall back to direct mode.
- No silent default budget. Configure positive integer runtime and stop-grace
  milliseconds; document that the final allowance includes cancellation grace.
- One deterministic collision-resistant unit name per invocation. Record launch
  intent before the effect. Reject existing unmatched units. Read back exact
  manager identity, invocation binding and cgroup; missing/unavailable/mismatched
  readback holds. Capture terminal observations before metadata collection.
- Terminal metadata retention clarification: use `RemainAfterExit=yes`. An exact
  `active/exited` observation plus independently empty owned cgroup permits a
  durable terminal receipt, not ownership release. Persist the unit, manager and
  systemd InvocationID, cgroup and stop intent; stop only the still-matching unit.
  Release requires inactive/empty readback, or receipt-backed disappearance after
  confirmed owned stop and an empty cgroup. Missing metadata before that receipt
  remains HOLD. Receipts never authorize a different manager or unit invocation.
  This avoids systemd's immediate collection of successful transient services.
- Transient service properties: Type=exec, ExitType=cgroup, Restart=no,
  RuntimeMaxSec and bounded TimeoutStopSec, RuntimeRandomizedExtraSec=0,
  KillMode=control-group, SendSIGKILL=yes; bound startup. Do not use a scope.
- Do not inherit additional manager environment into the provider. Keep manager
  connection environment confined to the launcher; disable argument expansion.
- A systemd-run client PID/exit is transport evidence, not worker ownership.
  Preserve ownership until the exact unit is inactive and its cgroup empty.
  Never delete worktree/retry because a client died while owned work is live.
- Keep exact durable Issue results authoritative. Timeout or exit status cannot
  supply VERIFY, ACCEPT or DONE. No automatic new retry entitlement.
- No protection against deliberate privileged/same-user cgroup migration is
  claimed. Ordinary descendants including setsid remain within the unit.
- Do not stop/restart live services, change installation profiles, invoke real
  providers, touch operational resources, or mutate Project state in this task.

## Task 1 — implementation and discriminating evidence

Files: `src/runtime/worker-runner.mjs`, `src/runtime/dispatcher.mjs`,
`src/config/profile.mjs`; a focused runtime supervision adapter module and
corresponding `test/` modules; relevant example profile and operations docs only.

- [ ] Read current launcher, resource lifecycle, completion, recovery and strict
  config handling. Preserve unrelated changes; use an isolated repair worktree.
- [ ] Define adapter operations for planned invocation ownership, bounded launch,
  owned-unit readback and cancellation. Inject manager transport for deterministic
  tests; real disposable tests must exercise the production adapter.
- [ ] Write failing tests before production edits. Validate missing/zero/negative/
  fractional/nonfinite/excessive limits; exact argv/environment/cwd (literal `$`,
  quotes/spaces); unit collision, wrong ownership and unavailable manager refusal.
- [ ] Add lifecycle tests: client exit cannot release an active unit, admit a
  replacement or delete its worktree; terminal receipt survives cleanup; authentic
  durable results retain their existing semantics; exit 0 alone never advances.
- [ ] Implement the smallest adapter and ownership integration that passes those
  tests. Do not relax unrelated identity/custody admission to fit old fixtures.
- [ ] Add disposable host tests: blocked dispatcher loop still times out;
  TERM-resistant child is killed; early-exiting parent leaves a setsid descendant
  with closed stdio and it is still bounded; unrelated sentinel survives; client
  death/recovery does not permit duplicate work or cleanup. Report unavailable
  user-manager permission as a blocked host proof, not PASS or an automatic skip.
- [ ] Run targeted Node tests, then `rtk proxy node scripts/check.mjs all`.
  Retain red/green commands, exit statuses and actual host evidence. No S0 Python
  fixture, implementation, readiness or independent verification is repeated.
- [ ] Commit source repair on its isolated branch; request fresh independent
  review against this plan and the exact diff. Repair findings and revalidate.

## Task 2 — closure and activation admission

- [ ] Validate and LAND reviewed source under repository closure rules if no
  blocker remains; remote-readback and remove actor-owned temporary state.
- [ ] Prepare exact installation-only configuration/diff and numeric allocation,
  proof receipts, idle guard, rollback and post-activation checks before requesting
  any genuinely missing live authority. No speculative live action.
- [ ] Activate only within established operational authority, with no active work
  interrupted. Then bind S1 packet at the current baseline, obtain native Agent
  Ready assessment, run SWF-35 release admission and use normal dispatch.

## Current checkpoint

S0 is DONE and its accepted evidence remains unchanged. Main before this packet:
`9174849713df2685117de7a8150126d916a4b644`. Independent design review
`/root/s1_admission_review` supports the critical-repair exception and the above
ownership requirements. Source implementation and host proof have not started.
