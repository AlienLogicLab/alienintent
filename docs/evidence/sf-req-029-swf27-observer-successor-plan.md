# SF-REQ-029 — SWF-27 observer successor PLAN

Status: independently reviewed PLAN decomposition. Owner: SF-REQ-029 / Issue #44.
Consumer: WO-220604/R4 / Issue #136. Source contract:
`docs/evidence/sf-req-029-swf27-observer-successor-specification.md` at
`origin/main` commit `c547b23929c9523e986ed0a7980f9c938768edf3`.
Planning baseline: `origin/main` `8d2f3b7ecaeb90f158bd1e72132bdefdb4e247bc`.
The Founder decision on #136, comment `5872219660`, pulls forward this bounded
observer capability. It does not change #44's P4/Wave 5 metadata, authorize
implementation from the Product Requirement, or authorize an installed service,
live handoff, Node retirement, or R4 release.

## Selected architecture and source contract

The existing Node Dispatcher is the owner of `state.json`; its
`src/runtime/dispatcher.mjs` `save(state)` currently writes a temporary JSON file
and renames it. A poll of that file cannot prove transitions that disappear
between polls. The first task therefore makes an append-only, gap-detectable
Node transition ledger the durable source of admitted `active` and
`diagnostics` changes. A ledger commit is the source admission point; the JSON
file becomes a replayable projection of that committed state. The proposed
source path is `/home/netmarine/.local/state/alienintent/node-state-ledger.jsonl`,
owned by the single configured Dispatcher writer with mode `0600`; the
successor has read-only access. The producer interface is the Dispatcher's
`save(state)` commit boundary; the consumer interface is a complete ordered
ledger record stream plus a cursor `(source revision, sequence, digest)`. The writer must
commit and sync a monotonically numbered record containing the preceding
record digest, source UTC time, source revision, ordered set of changed lanes
and invocations with transition/outcome identities, and the complete canonical
post-state payload and digest **before** replacing the projection. This includes
deliveries, resources, execution limits and other persisted fields, even when
there is no observed `active` or `diagnostics` change. Startup replays the ledger,
repairs an interrupted projection write,
and refuses a corrupt, forked, truncated, or nonconsecutive ledger. Every save
path, including result routing, diagnostics, release, delivery tracking, resource
changes, recovery, and restart, goes through this one commit path. A legacy-state genesis
checkpoint records only the state observed at installation; history before that
checkpoint remains `UNKNOWN`, never reconstructed from the snapshot. The packet
must pin the concrete storage format, fsync and directory-sync points, migration
barrier, state schema compatibility, and single Node writer exclusion. It must
prove that a failed append has no admitted state effect and that a committed
append cannot be lost when projection or acknowledgement fails.

The successor adapter tails that ledger by `(source revision, sequence, digest)`
and submits one stable `source + event_id` to the existing
`trajectory_capture.py` journal. Its cursor may advance only after the journal
commit is read back, and duplicate submission after a lost acknowledgement
must resolve to the original capture identity. `trajectory_receipts.py` currently
produces capture-anomaly attention; it does not produce the incumbent Node
outcome classes. A separate, deterministic Node-outcome attention consumer is
therefore required. It must reconcile with the retained bootstrap attention
queue, acknowledgements, notification-attempt records and rejection streaks.
Existing observation and attention JSONL remain immutable legacy evidence.

The planned capability identity is `sf-req-029/swf27-node-observer-v1`, profile
`alienintent-local-swf27-node-v1`, and user unit
`alienintent-swf27-node-observer.service`. The proposed external configuration
path is `/home/netmarine/.config/alienintent/swf27-node-observer.json`; the
proposed state root is
`/home/netmarine/.local/state/alienintent/swf27-node-observer/`. These are
design identities. No installed adapter, profile, unit, source ledger, or
installation receipt was established at the planning baseline.

## Implementable owner tasks and order

These are three proposed SF-REQ-029-owned BIU packets for the subsequent TASKS
stage, not new Wave 2 DAG nodes or released worker assignments. Each has one
mutation owner and a separate review gate. TASKS materialization must bind exact
candidate paths, fixture and budget before Agent Ready; no task may be
implemented directly from #44 or from this PLAN.

| Order | Proposed task | Owned deliverable | Dependency and independent acceptance |
|---|---|---|---|
| 1 | `SF029-SWF27-LEDGER` | Node's canonical append-only transition ledger, restart replay and admission fence; `state.json` compatibility projection; genesis receipt | Starts from current Dispatcher semantics. Independent verifier proves write ordering, one writer, gap detection, crash recovery, and refusal when the fence or source is unavailable. No live installation. |
| 2 | `SF029-SWF27-CONSUMER` | Ledger-to-capture adapter, committed cursor, Node-outcome attention producer, legacy read/identity mapping and queue reconciliation | Requires accepted task 1 schema and ledger. Independent verifier proves exactly-once source identity and future/pending attention equivalence in an isolated fixture. No live writer authority. |
| 3 | `SF029-SWF27-PROFILE-PROOF` | Versioned user-systemd profile, installation receipt, one-writer handoff/rollback procedure, bounded operational proof and independent verdict | Requires accepted tasks 1 and 2, an explicit live-operation grant for the named target/profile, and current incumbent/source readback. Its fixture result alone cannot authorize cutover or R4. |

### Task 1 — Node source, admission, and recovery

The task's owner changes `src/runtime/dispatcher.mjs` and its focused runtime
tests; any new ledger module belongs under `src/runtime/`. The packet must
specify a versioned record schema and the exact atomic protocol above. It must
enumerate all `save(state)` callers and prove that every persisted mutation,
including `active`, `diagnostics`, deliveries, resources, execution limits and
any fence change, has one committed sequence, while
each constituent transition has a stable occurrence identity. It must
bind the fence to the same durable source revision and check it before worker
launch, webhook-result routing, release/resume, and other authority-bearing
effects. A stopped or stale observer may not be made to look healthy by a
successful `state.json` rename. The runtime must fail closed when it cannot
append, sync, replay, or prove single-writer custody. It must retain current
resource identities and historical state markers. Negative controls interrupt
before ledger append, after ledger commit and before projection, after projection
and before reply, during replay, and at competing-writer admission. They assert
the exact committed sequence and no extra launch/status effect, not merely a
nonzero exit.

### Task 2 — capture and attention equivalence

The adapter consumes only the accepted ledger schema from task 1 and submits to
the current journal through the existing capture interface; it cannot infer an
event from a mutable snapshot. It persists a source cursor and digest tied to
the capture commit, reconciles on startup, and holds on a gap, changed payload,
out-of-order sequence, source-time regression, journal mismatch, or stalled
consumer. Its capture record carries lane, invocation, source occurrence,
source UTC time, revision, sequence, payload digest and capture UTC time;
unknown source times remain unknown.

The Node-outcome consumer owns durable attention items for `DONE_TO_DONE`,
`FOUNDER_EXCEPTION`, `DURABLE_RESULT_MISSING`, `WORKER_IDENTITY_MISMATCH`,
`COMPLETION_ERROR`, and third-or-later `REJECT_TO_IMPLEMENT` for one BIU.
Identity derives from the source event and invocation (or source occurrence
when invocation is absent). It carries the rejection streak across restart,
preserves prior acknowledgements and pending items, appends queue items before
best-effort notification, and records a failed notification attempt without
clearing the item. `LIVENESS_GAP` remains with the independent liveness producer;
capture anomalies remain with `trajectory_receipts.py`. The packet must bind
the installed bootstrap queue
`/home/netmarine/.local/state/alienintent/coordinator-attention.jsonl`
writer/reader interface and a versioned legacy
read adapter or proved migration for `attention_wait.py`, fresh coordinators,
`cycle_data.py` and historical reconstruction over
`/home/netmarine/.local/state/alienintent/coordinator-observations.jsonl`.
Acceptance replays a mixed
Node/lifecycle/liveness queue, including an already handled event, a lost
acknowledgement, failed notification, and a rejection streak spanning restart;
each expected unhandled item is read back once, with no second authoritative
effect or auto-ack.

### Task 3 — installed profile and operational verdict

The exact candidate commit, module and unit digests, external configuration
digest, profile id, systemd InvocationID, PID/start time and state-store identity
form an installation receipt. The profile binds the ledger path/schema,
capture journal, cursor, source and attention consumers, incumbent log/queue
paths, handoff-control lock/generation, Node admission-fence owner and command,
readback commands, and the 60-second maximum protected recovery interval.
Installation and live activation require their separately recorded authority.
An exact, separately authorized bounded proof switch may temporarily stop the
incumbent under the fence, but must restore and read back `LEGACY` before task 3
closes. That proof grant is not permanent cutover or retirement authority.
No secret or operational state is committed to the repository.

Before a switch, inventory the incumbent unit and code, lock/cgroup/process,
ledger cursor, observation-log and queue offsets/digests, outstanding items,
acknowledgements, rejection streak, independent producers and consumers. Read
back twice around a bounded barrier. Shadow mode reads and records proof in
separate state but publishes no authoritative observations or attention. With
the exclusive handoff-control lock held, fence Node admission and commit a new
generation; confirm incumbent stopped, cgroup empty and observer lock released
before successor authority. Reconcile Node-derived observations to ledger
events, `OBSERVER_STARTED` and other lifecycle records to process/legacy-log
identity, and independent attention producers to their own queue identities.
Unknown mappings hold the switch. Lift the fence only after successor writer,
cursor, queue effects and protection state are independently read back.

The operational state machine is `LEGACY` → `QUIESCED` → `SUCCESSOR` and
`SUCCESSOR` → `RECOVERING` → `LEGACY`. `QUIESCED` and `RECOVERING` are protected
only while source acceptance remains durable, admission is fenced, and elapsed
time is within 60 seconds. On rollback, fence the successor generation, read
back its last committed cursor/effects, replay missing source events and queue
effects through one reconciler, confirm successor cgroup empty, then restart and
read back incumbent lock/unit/process and cursors before lifting the fence.
Any failed replay, stale writer, failed restart or overdue recovery remains
fenced and is a failed verdict. Both evidence stores and the handoff ledger are
retained; no automatic truncation or retirement occurs.

## Proof matrix and release boundaries

The independent proof uses the exact installed profile on the authorized
target, with commands, exit codes, immutable raw observations and a reviewer
verdict naming the candidate and profile. It covers intact operation, injected
fault, restored operation, process restart, rollback and a second reconciliation
cycle. At each boundary it records source sequence range, journal/receipt roots,
incumbent log and queue offsets, writer generation, fence state, unit/cgroup/PID
and outstanding attention identities. Every admitted event must appear exactly
once in order, and every pending attention item must remain reachable. The
negative controls include source gap, duplicate with changed payload, lost
acknowledgement, clock regression, consumer failure, stale writer/fence,
interrupted handoff, all incumbent attention classes, retained liveness item,
notification failure, restart-spanning rejection streak and failed
`RECOVERING`. Each control must fail or hold for its intended reason with
counted evidence. An active unit or empty queue is not proof.

The task 3 verdict is an SF-REQ-029 successor acceptance only if the source,
writer, attention and recovery obligations all pass. #136 still needs its own
fresh native Agent Ready assessment and independent R4 operational verdict on
its exact packet. The accepted successor identity/profile and evidence must be
returned to #136 before its release gate is reconsidered. The incumbent
`alienintent-observer.service`, attention queue, Node and bootstrap protection
remain active outside a separately authorized bounded proof window until those
gates and separate cutover/retirement authority are met. During that window,
the verified ledger and admission fence preserve protection while the incumbent
is stopped; failed restoration leaves admission fenced and is a failed verdict.
FX-R4 is a disposable fixture, never the live successor.

## Custody, budget and next lifecycle step

Each TASKS packet must bind one owner, isolated mutable workspace, baseline,
permitted paths, source/profile version, local fixture, feature-regression
applicability, execution budget and independent verifier. WIP remains one.
Producer candidate publication and exact Issue branch/SHA precede VERIFY;
the verifier retrieves that candidate in its own workspace with a passing
feature-regression receipt. A rejected candidate repairs within the same
authorized scope; no self-approval, protected-branch push, live operation or
unbounded budget follows from a local commit. Live service/protected-state
mutation in task 3 needs an exact target, credential, blast radius, rollback,
and separate operational grant before execution.

After independent PLAN review, select #44 from PLAN to TASKS with readback,
materialize the three proposed owner packets under #44 and request native
Agent Ready assessments in dependency order. A HOLD for any missing source,
profile, budget, custody or operational grant is a valid assessment; it cannot
be promoted by this PLAN. Return to #44/#136 with exact accepted identities and
proof, or a concrete blocker. General lesson: **DETERMINISTIC_PREFLIGHT** —
release admission checks the committed source cursor, fenced writer generation,
attention-equivalence readback and measured protection state for the exact
profile before a replacement claim.

## Independent PLAN review

A separate read-only reviewer found two important first-draft gaps: the draft
appeared to prohibit the temporary incumbent stop required for the bounded
operational proof, and its ledger replay promise did not cover Dispatcher
deliveries, resources and limits. The revised plan requires a separate proof
grant with restored `LEGACY` before task closure and a complete post-state
payload for every `save(state)`. On reread the reviewer found both findings
resolved and no remaining important omission or authority contradiction.
