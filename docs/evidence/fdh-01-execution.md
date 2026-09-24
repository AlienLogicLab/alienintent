# FDH-01 execution record (PRODUCER)

These are the PRODUCER's own local proof receipts. They are not an independent verdict,
a release, an installation or live operation. The live proof was not executed; it is out
of scope (FDH-01 non-goals).

## Identity and authority

- **Issue:** #89. The RELEASED comment of 2026-09-24T06:35:54Z authorizes IMPLEMENT only
  for FDH-01's bounded extent (scope 1–5). Executing the live proof, and installing or
  enabling the host, are not authorized.
- **Invocation:** `AlienLogicLab/alienintent#89:PRODUCER:27e3cc45-3fb2-4c15-8270-6e7f0ac58238`.
- **Worker:** Morty (`morty-worker`), Claude `claude-opus-5-5`.
- **Branch:** runtime-managed `b-disp/b823a326-c2d8-46f2-9831-207832d4ae6f`.
- **Admission baseline:** `70fa7148939dfcebbcef73d858f9f481869d7214` (clean at admission).
- **Contract:** `docs/work-units/wave2/FDH-01.md`, sha256
  `01a0ab5961dd5877531c4527620c2f2b905763f454af7dbdefb5d29ba24187d1`. This equals the
  `input_sha256` of the native Agent Ready READY assessment
  `docs/evidence/wave2-readiness-assessments/FDH-01.2026-09-24T055203.941687Z.assessment.json`,
  so the assessed contract is unchanged.
- **Chat record §13–§17:** read from the operator file
  `/mnt/d/Projects/alienintent/docs/operations/AlienIntent_Chat_Record_Last_24h_20260923-185454-SGT.md`
  (untracked, sha256 `8c35ff8b2eb023557271b07413114122b2db94f1ed664928d61cb7d132c613a0`).

## Prior implementation (evidence input): kept, modified, replaced

`origin/feature/factory-director-harness` @ `c14aba15dfc4c951c91c01b57299cfc042092aab` was
merged unchanged onto the baseline as `c3a1cf7`.

| Prior commit | Disposition | Reason |
|---|---|---|
| `7dc2b17` host core | **Kept:** `DirectorInputs`, strict `JsonDirectorInputs`, `flock` host ownership, reserve-before-spawn `ACTIVATING` lease, append-only history, `inspect`, in-memory launcher. **Modified:** see the notes below this table. **Replaced:** the hand-written `config/factory-director-host-input.example.json` projection (now produced by the adapter), the episode prompt (now a pointer to the runtime contract) and `docs/operations/factory-director-host.md` (rewritten) | See the notes below this table |
| `1947d41` ownership gaps | **Kept:** `AmbiguousLease`, linked-worktree isolation, indeterminate liveness refuses | Valid fail-closed behaviour. The liveness for a retained child now uses `Popen.poll()`, which also reaps it; `/proc` start-ticks remain for episodes launched before a host restart |
| `02b62bd` lease validation | **Kept**, extended with the `EXITED` status | Valid; exit observation needs a durable state |
| `0846cfd` launch handoff | **Kept** unchanged | Valid; its test was adapted to the new launcher signature only |

Notes on the modifications and replacements of `7dc2b17`:

- **`_idle_reason`.** In the prior code, full worker WIP refused attention, inbox and
  selection work as `EXECUTION_CAPACITY_UNAVAILABLE`. That contradicts chat record §15
  condition 2 ("no additional control work can safely advance").
- **The Codex-only launcher.**
  - It became a Claude/Codex launcher selected by configuration.
  - The model is now explicit. Before, it was read from `~/.codex/config.toml`, which is
    both inference and non-hermetic.
  - Provider output moved out of the Director worktree.
  - The child is retained and reaped, and its exit code is recorded.
- **`main`.** It now uses `--config` and the adapter instead of `--inputs`. The polling
  interval went from 2 s to 60 s, with an immediate wake when the episode exits.
- **Replaced files.** A projection is now written only by the read-only adapter. Keeping
  a hand-editable authority source would bypass it.

## Commits (in order)

1. `c3a1cf7`: merge of the prior branch.
2. `a2bf163`: implementation (adapter, launcher, runtime contract, live-proof procedure,
   tests, discrimination harness).
3. `4ee40f2`: repair of independent review 1.
4. `c09a785`: repair of independent review 2.
5. `efb0bdb`: repair of independent review 3. This is the implementation revision proven
   below.

The evidence commit that adds this record and `docs/evidence/fdh-01/` is the published
candidate head. The Issue comment records its exact SHA.

## Chosen sources, schemas and precedence

These are documented in `docs/operations/factory-director-runtime-contract.md` §9–§10
and tested.

- **Paths and schemas:**
  - Founder-hold record: `~/.local/state/alienintent/factory-director/founder-holds.json`,
    `{"schemaVersion":1,"holds":[{"issue","reason"}]}`. Required; "no holds" is `[]`.
  - Pause flag: `.../factory-director/PAUSE`, presence only.
  - Inbox: `.../factory-director/inbox/` (required), with `processed/<id>.json` receipts.
  - WIP limit: `wipLimit: 1` in `~/.config/alienintent/factory-director-host.json`.
  - Retained Agent Ready assessment: an `AGENT_READY_ASSESSMENT` marker on the Issue,
    counted only from a self-hosting authorized operator who is also the last editor.
- **Idle-reason precedence:** `AUTHORITATIVE_STATE_UNAVAILABLE` > `FACTORY_PAUSED` >
  `FOUNDER_DECISION_PENDING` > `WIP_INTENTIONALLY_FULL` (only when there is no
  Director-only control) > `NO_ELIGIBLE_AUTHORIZED_WORK` > `EXECUTION_CAPACITY_UNAVAILABLE`.
  A test asserts that the documented order equals the order the host applies.
- **PRODUCER-defined rule awaiting Factory Director sanction.** FDH-01 does not define an
  "unresolved" `limitEscalations` entry, and the Node runtime never removes one. As
  written, one escalation would relaunch episodes forever (review 1, H1). The candidate
  defines an entry as resolved when either:
  - its Issue is `DONE`; or
  - a Director acknowledgement `inbox/escalations/escalation-<digest>.json` exists for
    that exact escalation. These acknowledgements are separate from inbox `processed/`
    receipts.

  Independent review 2 identified this as a departure from the literal contract that
  needs Factory Director sanction.

## Independent adversarial reviews

Each review ran in a fresh read-only subagent session and is not the BIU verifier.

- **Review 1** (of `a2bf163`): 3 HIGH, 5 MEDIUM and 7 LOW findings. Repaired in `4ee40f2`:
  - H1: escalations never resolved.
  - H2: the assessment marker had no provenance.
  - H3: no crash-loop guard, and no per-provider permission validation.
  - M1: the live proof could not run (installer not executable, errexit, racy waits).
  - M3: a pre-bind launch failure left an unleased child.
  - M4: an unreadable pause flag failed open.
  - M5: board rows lacked their repository.
  - L2, L4, L5, L6.

  M2 (Founder exceptions) follows the contract table literally. It is documented as a
  Director obligation: record a hold for each open Founder exception. L1, L3 and L7 are
  residuals (below).
- **Review 2** (of `4ee40f2`): confirmed every repair. It raised 1 MEDIUM (the escalation
  rule's contract departure) and 6 LOW. Repaired in `c09a785`:
  - acknowledgements moved to `inbox/escalations/`;
  - the streak resets on a legitimate idle;
  - short exits that make progress are not crashes;
  - the exit race is recorded;
  - launch failures back off;
  - the comment editor is checked;
  - live-proof wording.
- **Review 3** (of `c09a785`): found no HIGH, and confirmed the criterion-4 sequence and
  the lease protections. Its 1 MEDIUM and 4 LOW were repaired in `efb0bdb`:
  - progress is judged by a durable-state fingerprint instead of the nine booleans;
  - a brief idle no longer cancels a back-off;
  - an edited comment with an unknown editor is ignored.

  The remaining LOW is the acknowledgement migration. Nothing is installed, so no
  acknowledgements exist yet, and no migration is needed.

## Acceptance evidence at `efb0bdb`

| Criterion | Command | Result |
|---|---|---|
| 1 One true and one false case per predicate | `python3 -m pytest -q tools/orchestration/test_factory_director_inputs.py` | exit 0, **87 passed**. Tests `test_authoritative_state` … `test_explicit_pause` |
| 2 Fail closed, each shown failing against a broken adapter | same file: `test_malformed_or_unavailable_source_fails_closed` (7) and `test_negative_control_the_same_check_fails_against_a_broken_adapter` (7). Plus `PYTHONPATH=src python3 tools/evidence/fdh01_evidence.py --output docs/evidence/fdh-01` | 7/7 fail closed and 7/7 broken adapters fail the same check. There are 20 further inconsistent-source cases. Source-mutation harness: exit 0, **32/32 controls discriminated** (96 observations, intact 0 / fault 1 / restored 0 each, 32 fault applications) |
| 3 Hold and inbox scenarios | `test_hold_on_some_ready_items…`, `test_all_eligible_items_held…`, `test_held_unclaimed_implement…`, `test_pending_inbox_entry_launches_despite_holds…` | pass. Mutation controls `hold-idles-everything`, `hold-covers-ready-only` and `inbox-receipts-ignored` discriminate |
| 4 Offline continuity | `python3 -m pytest -q tools/orchestration/test_factory_director_host.py` | exit 0, **68 passed**. `test_continuity_a_exits_fresh_b_launches_then_b_exits_and_host_idles`; control `successor-reuses-episode-id` discriminates |
| 5 Launcher | same file: command-line, no-resume, permission, isolation and real fake-provider tests for `claude` and `codex` | pass. Controls `claude-session-continued`, `codex-session-persisted`, `isolation-check-disabled`, `provider-model-not-recorded` and `permission-mode-unchecked` discriminate |
| 6 Documents | `python3 -m pytest -q tools/orchestration/test_factory_director_docs.py` | exit 0, **39 passed** (every Scope 3 heading; all 12 live-proof steps with commands and evidence; `bash -n` on every block; wait helpers executed; the prompt points to the contract) |
| 7 Required gates | `node scripts/check.mjs all` | exit 0 (runtime 340/340, preflight passed, rai 18/18, policy 3/3) |
| 7 Python | `python3 -m pytest -q tools/orchestration tools/live` | exit 1: **307 passed, 1 failed**. The failure is `test_director.py::test_substantial_technical_analysis_routes_to_codex_primary`, the known non-hermetic baseline debt named in the RELEASED comment. It is out of scope and unmodified (`git diff 70fa714 HEAD` is empty for `test_director.py` and `director.py`). Every host and adapter test passes |
| — Repository suite | `python3 -m pytest -q tests` | exit 0, **526 passed** |

**Read-only audit.**

- `test_adapter_writes_nothing_but_its_own_projection` shows that every fixture source is
  byte- and mtime-identical after two evaluations.
- `test_adapter_source_contains_no_github_write_or_issue_transition` finds no `mutation`,
  `item-edit`, `item-add`, `create`, `edit`, `close` or `comment` verb, and no
  `STATUS_OPTIONS[` use.
- The adapter's GitHub calls are GraphQL queries only: the board and Issue comments.
- `tools/live/project_materialization.py` changed only its read query and row mapping, to
  add each Issue's repository. It has no new write.

## Measurements

- **Tokens and cost of this PRODUCER invocation:** HOLD (not measured). Billing telemetry
  is not available to the worker. This is not zero.
- **The host's own episodes** record provider-reported tokens and cost when exposed
  (Claude: tokens, cost and models; Codex: tokens only). Otherwise they record
  `measured: false` with a reason.
- **Live GitHub read-back of the new board and comment queries:** HOLD. The worker token
  gets "Resource not accessible" for Project #1. The verifier or Factory Director should
  run `python3 tools/orchestration/factory_director_inputs.py --config <host config>` with
  an operator gh configuration. The Issue #89 Agent Ready comment was fetched with the
  REST API and parsed by `has_retained_assessment` successfully.

## Residuals (recorded and deferred)

- **L1:** active claims above `wipLimit` are handled as `EXECUTION_CAPACITY_UNAVAILABLE`
  or as Director-only launches. They are not treated as unauthoritative state.
- **L3:** an idle reason can be recorded while an episode is live. This is informational
  only; no launch results.
- **L7:** the isolation check accepts any linked worktree. It does not check that the
  worktree belongs to this repository or that no runtime claim owns it.
- **Comment provenance:** only the last editor is checked, not the full
  `userContentEdits` history.
- **Fingerprint:** it can change because of worker-driven board transitions. A fast
  Director exit then counts as progress.

## Repair cycle 1 (after JC's REJECT)

PRODUCER invocation `AlienLogicLab/alienintent#89:PRODUCER:39a17230-3143-4c62-87a6-970061df9dad`
(Morty, Claude `claude-opus-5-5`). Input: rejected candidate `8da68f7` and JC's review
evidence `6c38427` (`docs/evidence/fdh-01-jc/review.md`), merged into this branch
unchanged so the review and its reproducers travel with the candidate. The admission
baseline `70fa714` equals `origin/main`, and the contract hash is unchanged.

| Finding | Disposition | Where |
|---|---|---|
| F1 exit-before-wait sleeps the interval | **Repaired.** `wait_for_change` returns `EPISODE_EXITED` with no sleep when the leased episode has already exited before the wait begins. Crash-loop back-off stays in `reconcile`, so waking early never bypasses it. A host without the host lock, or with unknown liveness, still waits the interval (no spin) | `factory_director_host.py` `wait_for_change`; runtime contract §10 |
| F2 extended lease missing a key crashes | **Repaired.** Lease validation checks required-key containment (`required <= set(value)`), so every required key is enforced whatever extra metadata is present | `factory_director_host.py` `_lease` |
| F3 Codex actual model | **Evidence recorded, Director disposition requested.** See below | `codex_usage`; runtime contract §10 |
| D1 escalation-resolution rule | **Unchanged, awaiting Factory Director sanction.** Defining "unresolved" is a Director decision; the PRODUCER does not self-sanction it | runtime contract §9 |

**F3 probe (Codex CLI 0.155.1, this host, 2026-09-24).** Two minimal `codex exec` runs in
`/tmp` with `--sandbox read-only`:

- `codex exec --ephemeral --json`, the launcher's form. The JSONL events were
  `thread.started` (`thread_id`), `turn.started`, `item.*` and `turn.completed`
  (`usage` token counts only). No event names a model.
- `codex exec --json` without `--ephemeral`. The persisted rollout has
  `session_meta.model_provider` (`openai`) and `turn_context.model`, which equalled the
  client configuration's model. That field records what the client asked for, not what
  was served, so it is no stronger evidence than `requested_model`. Adopting it would
  also give up the `--ephemeral` non-persistence property.

So Codex does not expose the model actually used. The host records
`usage.observed_models: null` with `usage.model_evidence: "NOT_EXPOSED_BY_PROVIDER"` and
never copies `requested_model` into it. Claude records `PROVIDER_REPORTED` from
`modelUsage`. Criterion 5's "model actually used" is therefore satisfiable for Claude
and structurally UNKNOWN for Codex. Accepting that gap, or requiring Claude-only Director
episodes until Codex exposes the model, is a Factory Director disposition.

**Tests added to the maintained host suite** (78 total, was 68):
`test_exit_before_wait_reconciles_at_once_without_sleeping`,
`test_exit_before_wait_still_honours_crash_loop_back_off`,
`test_wait_with_unknown_liveness_or_no_lease_sleeps_the_interval`,
`test_a_host_without_the_lock_waits_the_interval_for_an_exited_episode` and
`test_extended_lease_missing_a_required_key_refuses_without_crash` (one case per
required key). Against the unrepaired host at `8da68f7`, 9 host tests fail: the two
F1 tests, five of the six F2 cases (a missing `started_at` was already refused), and the
two usage-shape assertions. All pass on the repair.

**Source-mutation controls added:** `exit-before-wait-sleeps`, `non-holder-spins-on-exit`
and `lease-keys-strict-subset`. Report: `docs/evidence/fdh-01-repair-1/report.json`.
The earlier report in `docs/evidence/fdh-01/` is kept unchanged.

| Check | Result |
|---|---|
| `python3 -m pytest -q tools/orchestration/test_factory_director_inputs.py tools/orchestration/test_factory_director_host.py tools/orchestration/test_factory_director_docs.py` | exit 0, **204 passed** (87 / 78 / 39) |
| `python3 -m pytest -q docs/evidence/fdh-01-jc/reproduce.py` (JC's reproducers) | exit 0, **2 passed** (were 2 failed at `8da68f7`) |
| `PYTHONPATH=src python3 tools/evidence/fdh01_evidence.py --output <tmp>` | exit 0, **35/35 controls discriminated** (105 observations) |
| `node scripts/check.mjs all` | exit 0 |
| `python3 -m pytest -q tests` | exit 0, **526 passed** |
| `python3 -m pytest -q tools/orchestration tools/live` | exit 1, **317 passed, 1 failed**: the unmodified baseline `test_director.py::test_substantial_technical_analysis_routes_to_codex_primary` |
| `git diff --check 70fa714 HEAD` | exit 0 |

**Measurements.** Tokens and cost of this invocation: UNKNOWN; billing telemetry is not
available to the worker. This is not zero. The two F3 probes consumed a small, unmeasured
amount of Codex usage.
