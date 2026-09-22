# Codex-primary activation — activated; ACCEPT-only closure completed

## Closure read-back — 2026-09-22T16:35Z

Successor `5efc665c-4bd2-4566-a548-c7dc02a79c1b` published
[DONE](https://github.com/AlienLogicLab/alienintent/issues/69#issuecomment-5780228636)
at 16:34:42Z. The dispatcher recorded `DONE_TO_DONE` at 16:34:49.116Z;
live Project read-back confirmed DONE. Accepted candidate was merged by
[PR #70](https://github.com/AlienLogicLab/alienintent/pull/70) into
`9174849713df2685117de7a8150126d916a4b644`, preserving its full SHA and all 24
candidate paths. Both exact-merge CI workflows succeeded (35754774665,
35754774927). The Director checked ancestry and then closed Issue #69 as SWF-31
bookkeeping; no lifecycle transition was made by the Director.

The worker exited at 16:34:58.218Z. Its runtime resource is `REMOVED` with no cleanup
diagnostic, and active claims are empty. The old capacity attention item
`att-16e105ede481` was acknowledged only after DONE was read back. No other
service restart, worker termination or new IMPLEMENT/VERIFY invocation occurred.

S1 is the next dependency-satisfied unit. Its distinct admission hold is recorded
in [the budget decision record](../operations/post-wave1-program/reports/2026-09-22-s1-admission-budget-hold.md).
This hold does not qualify the successful activation or completed S0 closure.

## Recovery addendum — 2026-09-22T16:29Z

The historical blocked record below is preserved. Founder subsequently authorized
targeted termination after identity/ownership validation, required a stale-tree
absence check, and authorized continuation from ACCEPT only.

Recovered local receipt `/tmp/py10-orphan-termination-evidence.json` records
SIGTERM at 16:19:24Z to PID 933588, start ticks 20643711, exact pytest argv and
`/tmp/py10-proven-red-9ths3bmz/tree` cwd, the dispatcher cgroup, empty active
claims and no associated registered invocation. It records process disappearance.
This resumed session did not send another signal. Fresh host execution of
`/tmp/check_py10_tree_gone.py` at 16:25:39Z exited 0: target absent, no remaining
tree processes, no unreadable candidate processes. Protected system processes
predating the stale parent were recorded separately.

The prior session had also prepared the profile at 16:20:41Z. Its private archive
is `/home/netmarine/.local/state/alienintent/codex-primary-activation-20260922/`;
`prepared.json` records that only the two provider blocks changed and preserves
the original permission and identity boundaries. Both roles select Codex,
`gpt-6-astra`. The profile digest is
`d65c1ebea1de57fcc8ea9bde96a967b796ea361426d7dca164d81cad0a5b5f77`.

Fresh full Project and host idle checks at 16:25:48Z passed: only #69 ACCEPT was
startup-actionable; active claims, live registered worker PIDs and service children
were empty. HEAD, local origin/main and live remote main all read back
`9ee0ccd397147f20c57cb4077e7db6de4b260e6a`. Existing program-state edits and two
untracked operator reports remained intact.

[ACCEPT-only continuation](https://github.com/AlienLogicLab/alienintent/issues/69#issuecomment-5780107470)
was published before restart. The retained helper repeated remote and idle checks,
verified the prepared profile digest, and restarted only `alienintent.service` at
16:26:23Z. MainPID changed from 822833 to 1206384, active. The startup entrypoint
loads the profile once before reconciliation; no subsequent profile edit was made.

Startup reconciliation admitted exactly one new PRODUCER at ACCEPT:
`AlienLogicLab/alienintent#69:PRODUCER:5efc665c-4bd2-4566-a548-c7dc02a79c1b`,
16:28:44.893Z, resource `ef8f11d7-248c-4adb-bd1c-7b69e36d7938`.
Host `/proc` read-back confirmed PID 1207613, PPID 1206384, start ticks 31123482,
dispatcher cgroup, its registered worktree, and executable command
`node /home/netmarine/.local/bin/codex exec ... --model gpt-6-astra` with the
post-ACCEPT closure prompt. The worker log records thread
`01a0c9f2-efd1-7cc3-8753-dfef151160bf`. This proves actual Codex PRODUCER use;
VERIFIER configuration was loaded but no new verifier invocation was requested.

Activation and ACCEPT-only admission are observed. Closure is still RUNNING at
this checkpoint, not DONE. Implementation, readiness and independent verification
were not repeated by the Director. Historical worktree cleanup warnings were
retained without deleting their resources. The open attention item
`att-16e105ede481` concerns the prior capacity interruption; acknowledgement waits
for recovery evidence. Ten unacknowledged bridge replies concern completed older
program tasks, not new dispatch requests.

The current DAG identifies S1 / WO-220102 after S0, but the full Project read-back
has no S1 issue yet. Do not dispatch it before S0 is DONE and SWF-35 admission is
satisfied at the then-current baseline.

Authority: Founder direction to make Codex the default cognitive worker, followed by
explicit approval of the bounded plan and an **idle-only** dispatcher restart.
Resume WO-220101 from ACCEPT only; no repeat implementation, assessment or verification.

## Scope and provenance

- Starting repository HEAD: `175cccff7a52a60cee2c1fe0764faa4f06212cff`.
- Local Program Director remains the orchestration role. Only local routing policy changes;
  no provider choice is added to the AlienIntent product domain.
- Existing modified `program-state.json` and two untracked operator reports were preserved
  and excluded from this task's commits. No temporary branch or worktree was created.
- Plan: [bounded activation](../operations/post-wave1-program/codex-primary-activation-plan.md).
- Route receipt: [WO-220101 closure intent](../operations/post-wave1-program/WO-220101-codex-closure-routing.json).
  LOW risk applies only to ordinary post-ACCEPT closure of the already accepted candidate;
  this receipt neither reopens review nor grants launch permission past the idle gate.

## Routing implementation and verification

`tools/orchestration/director.py` now defaults all ordinary cognitive tasks, including
bounded extraction and historical tasks without a specific context need, to Codex.
Deterministic work still uses no model. Local models remain reserved until canonical
Allocation proves capability. Resident Claude requires a nonempty task-specific context
reason; fresh Claude review requires a nonempty diversity reason. Independent review
defaults to a fresh Codex context without author private reasoning.

Known Claude unavailability falls back to Codex under the same task contract unless
Claude is explicitly indispensable. Required-provider waiting and unavailable Codex
return `dispatch_allowed=false`; route CLI exits 3. No model is invoked by routing.
Optional immutable receipts preserve task identity, availability inputs and rationale.
They explicitly describe routing intent, not actual invocation provenance. The Director
must honor the decision; this is not an autonomous capacity detector or retry daemon.

- Red: 9 routing failures observed before implementation (including the new unavailable
  provider input and existing cheap-model/context/blank-reason defects).
- Red: 2 real CLI tests failed on missing arguments before CLI implementation.
- Green: `rtk proxy python3 -m pytest tools/orchestration -q`: **102 passed**, exit 0.
- Node regression: `rtk proxy node scripts/check.mjs all`: exit 0; runtime **310/310**,
  worker preflight PASS, RAI **18/18**, policy **2/2**. No Node source changed.
- `rtk git diff --check`: exit 0.
- Fresh independent review `/root/routing_review`: no blocking findings; independently
  ran the 102-test suite. Provider: Codex/OpenAI; actual model and session/thread ID:
  **UNKNOWN** (not exposed by this collaboration invocation). No author reasoning was
  supplied. Review covered routing code/docs, not runtime activation.

## WO-220101: preserve accepted work

Issue [#69](https://github.com/AlienLogicLab/alienintent/issues/69) read back OPEN,
Project **ACCEPT**. Accepted candidate:
`761a3cb4d6e24dc24ec370de45e25fe8c505eeda`.
Independent ACCEPT: [comment 5777072691](https://github.com/AlienLogicLab/alienintent/issues/69#issuecomment-5777072691),
verifier `f38d718d-1b28-401d-9a53-e63c4acb1347`, `2026-09-22T13:07:33Z`.

The subsequent closure PRODUCER `8a8d6385-600b-4cb7-908e-34580067209b` was allocated
`13:07:42.158Z`, exited `13:09:21.560Z`, and has `DURABLE_RESULT_MISSING` with exit 1.
Its terminal provider record has `is_error=true` and result
`You've hit your session limit · resets 10:30pm (Asia/Bangkok)`.
Classification: **PROVIDER_CAPACITY_INTERRUPTION**, not verifier rejection or task failure.
No additional repair cycle. Source: installation log
`logs/AlienLogicLab%2Falienintent%2369%3APRODUCER%3A8a8d6385-600b-4cb7-908e-34580067209b.log`.
Its earlier producer/verification results and all resources remain unchanged by this task.

## Idle-only activation guard: refused before mutation

Read-only checks confirmed installed `codex-cli 0.155.1`, existing ChatGPT login,
configured `gpt-6-astra`, Git author `netmarine <sanuk.du@gmail.com>`, GitHub
operator `sanookdu`. No CLI install or authentication change was made.

The current live profile still names Claude for both roles. Planned configuration
would restore the retained pre-recovery Codex provider contract for both roles,
including its existing permission mode, while preserving GitHub/Git identity and
credential boundaries. **That profile change has NOT occurred.**

One-shot activation helper: `/tmp/activate_codex_primary.py` (local temporary artifact,
not a product facility). It checks full Project read-back (only #69 ACCEPT actionable),
all active claims, recorded resource PIDs, dispatcher children and service cgroup
membership before preparing any profile patch. It repeats idle checks before restart.
Both preparation attempts failed with `DISPATCHER_CHILD_OR_CGROUP_MEMBER: [933588]`.
No backup/profile patch/restart step was reached.

Host evidence, 2026-09-22:

| Observation | Value |
|---|---|
| Dispatcher | `alienintent.service`, MainPID `822833`, active |
| Service stop behavior | `KillMode=control-group` |
| Runtime active claims | `{}` |
| Only unresolved diagnostic | #69 PRODUCER, ACCEPT, missing durable result |
| Surviving cgroup process | PID `933588`, PPID `385`, `python3` |
| Process start | `2026-09-21 18:22:17 +0700`; `/proc/933588/stat` start ticks `20643711` |
| Command | `/usr/bin/python3 -m pytest -q -p no:cacheprovider tests/composition/test_sandbox_run_profile.py::test_the_profile_drains_a_prioritised_backlog_with_a_dependency_and_an_escalation` |
| Working directory | `/tmp/py10-proven-red-9ths3bmz/tree` |
| Cgroup | `/user.slice/user-1000.slice/user@1000.service/app.slice/alienintent.service` |

The process appears associated with an old PY-10 proof run, but its termination is
not authorized by an idle-only restart. An empty active map is **not** sufficient
proof that restarting a control-group service interrupts nothing. A sandbox-local
`ps` did not show this PID; host-level inspection confirmed it remained live.
No conclusion that it exited is warranted. No process was killed or suspended.

## Disposition and next authorized boundary

Routing code/docs: validated for repository LAND. Operational activation:
**BLOCKED**, so the full Codex-primary transition is **not complete** and WO-220101
has **not** been resumed by this task.

Founder decision required: authorize targeted disposition of the identified surviving
PY-10 test process, or provide an alternative that leaves it unaffected. Before any
termination, revalidate PID plus start ticks, command/cwd and cgroup to prevent PID-reuse
mistakes. Do not kill a generic process pattern or all service processes.

After resolving that boundary, rerun the full idle/profile checks, publish the
ACCEPT-only continuation record **before** restart, and let existing startup
reconciliation create at most one Codex closure successor. Do not manually launch
Codex, toggle lifecycle state, repeat verification or acknowledge recovery as handled
before the successor is observed. Archive non-secret operational evidence and retain
actual provider/model/session provenance from the successor's durable logs.
