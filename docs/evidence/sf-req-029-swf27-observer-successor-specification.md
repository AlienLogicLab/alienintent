# SF-REQ-029 — bounded SWF-27 observer successor specification

Status: **accepted bounded SPECIFY contract for PLAN decomposition** after
independent read-only review in Factory Director episode
`factory-director-7ca2ba3636144f7795d8e89c53d7298d`. This is not acceptance
of an installed successor or of R4 operational proof. Owner: SF-REQ-029, Issue #44.
Dependency consumer: WO-220604/R4, Issue #136. Baseline: `origin/main`
`fd95f651c30ffa9eedc0c845f3072882fbfe99f5` (2026-09-28). This document
specifies a capability to build and prove; it does not assert that a successor is
installed, accepted, or authorized for live cutover.

## Authority and boundary

The Founder advanced the already-planned canonical observer capability for the
Node-retirement critical path on #136, comment `5872219660`. The existing Wave 2
specification assigns BOOTSTRAP-M03/SWF-27 observer replacement to SF-REQ-029 and
leaves provider-neutral progress/capacity normalization deferred. This slice covers
the local Node lifecycle observer, its observation record, and its attention handoff.
It does not claim the full Wave 5 Engineering Trajectory requirement, alter the Wave 2
DAG, transfer ownership to SF-REQ-053, normalize provider telemetry, or authorize
service mutation. Product planning must decompose this specification through PLAN,
TASKS, and Agent Ready before implementation.

## Current operational contract and source inventory

The **incumbent** is the active user unit `alienintent-observer.service`, installed at
`/home/netmarine/.config/systemd/user/alienintent-observer.service`, with ExecStart
`/usr/bin/python3 /home/netmarine/.local/share/alienintent-bootstrap/observer.py`.
Read-only `systemctl --user show` on 2026-09-28 UTC returned `ActiveState=active`,
`MainPID=1183`. These are observations, not successor proof. Installed source SHA-256:
`observer.py` `fe01d46f4ae41bf4410f92a54dd1b9c4ec135e1d14e7e0a922dae1761cb4cc5e`;
`attention.py` `14e2f9ba92ac996f116d44fcfd45ae94e94c4ad6620a7db170099d001d27475f`;
unit `320e18a06e8ee2cd7226c962090e7c5a116abf7749ab84433cc71ba76cfd1866`.
Re-pin all three immediately before any operational proof.

| Surface | Incumbent behavior and consumer |
|---|---|
| Input | Polls `/home/netmarine/.local/state/alienintent/state.json` every 30 seconds. Compares `active` role/status/invocation/PID and `diagnostics` outcome/at/invocation by lane. An unreadable snapshot is skipped. |
| Exclusion | Takes an exclusive nonblocking flock on `/home/netmarine/.local/state/alienintent/coordinator-observer.lock`. This protects only another process using that lock. |
| Observation | Appends `OBSERVER_STARTED`, `INVOCATION_ACTIVE`, `INVOCATION_ENDED`, and `OUTCOME_RECORDED` JSONL records to `/home/netmarine/.local/state/alienintent/coordinator-observations.jsonl`; stamps `observed_at` and `observer`. Stdout also goes to the unit journal. |
| Attention | Calls installed `attention.py` after the observation append. That module classifies outcomes and appends items/acks/notification attempts to `/home/netmarine/.local/state/alienintent/coordinator-attention.jsonl`; an item is keyed by the underlying event, with invocation identity when present. Notification is best effort. `attention_wait.py` and fresh coordinators consume the outstanding queue. |
| Other readers | Bootstrap `cycle_data.py` and historical trajectory reconstruction read the observation JSONL. They require preserved, attributable historical records. |

The incumbent polls a snapshot, so transitions that appear and disappear between
polls cannot be reconstructed from its log alone. The successor must prove coverage
against an authoritative durable source event sequence, or explicitly report the
unmeasured interval as `UNKNOWN` and refuse the no-loss verdict. A same-shape poller
alone cannot discharge this specification.

Repository components at this baseline are `src/alienintent/composition/trajectory_capture.py`
and `trajectory_receipts.py`. Capture accepts a JSON submission only after a journal
commit; it has no buffer while down. Its journal and receipt chain support replay,
ordering, anomaly records, and deterministic attention identities. These components
are **local compositions**, not a live binding to the incumbent Node state, observation
JSONL, bootstrap attention queue, or an installed SWF-27 service. FX-R4 is explicitly
a disposable preparation fixture and provides no live cutover verdict.

## Selected successor target and profile

The planned operational target is this host's **user systemd** instance, with
`alienintent-observer.service` retained as the incumbent. The successor capability
identity is `sf-req-029/swf27-node-observer-v1`; its profile id is
`alienintent-local-swf27-node-v1`. Its proposed unit identity is
`alienintent-swf27-node-observer.service`. Its configuration is to be installed **outside the
repository** at `/home/netmarine/.config/alienintent/swf27-node-observer.json`, with
durable state rooted at `/home/netmarine/.local/state/alienintent/swf27-node-observer/`.
Its source identity is the exact repository commit and installed module digest used
for its executable adapter; its runtime identity is the configured profile digest,
systemd unit/InvocationID, process PID/start time, and evidence-store identity.
Implementation must pin these in an installation receipt before operational testing.
No such configuration, adapter, unit, or installation receipt is present at this
baseline; its current operational status is **UNAVAILABLE**.

The profile binds one Node source: the configured runtime state path
`/home/netmarine/.local/state/alienintent/state.json` plus an authoritative,
append-only transition source covering every admitted active/diagnostic change. The
source event format, persistence point, cursor, and ownership must be defined by the
PLAN implementation packet and verified against the running Node version before
the profile is installable. Source events must carry lane, invocation, transition or
outcome, source sequence, source UTC time, and source revision. A snapshot may be used
to reconcile state, never to fabricate a missing event. A source with only a mutable
latest-state map fails the no-loss admission gate. The adapter submits to the
repository capture journal and retains a durable source cursor; acknowledgement is
valid only after the journal commit. The receipt consumer is the sole producer of
corresponding successor attention items. Keep the existing observation and attention
JSONL as immutable legacy evidence; consumers requiring them need an explicit
versioned read adapter or a proven migration before old protection can end. The
PLAN packet must name the executable adapter and its owning BIU; the present capture
and receipt modules alone do not implement this Node source binding or the incumbent
attention policy.

The successor attention producer must preserve the incumbent's future wake-up
behavior as well as existing queue contents. For Node outcomes, it must produce
the same durable item classes as installed `attention.py`: `DONE_TO_DONE`;
`FOUNDER_EXCEPTION`, `DURABLE_RESULT_MISSING`, `WORKER_IDENTITY_MISMATCH`, and
`COMPLETION_ERROR`; and `REJECT_TO_IMPLEMENT` on the third and later rejection
for one BIU, with the durable rejection streak carried across restart. Identity
uses the underlying event and invocation when present, never the new capture time;
an event without invocation needs a stable source occurrence identity. The
`LIVENESS_GAP` producer remains separately owned by bootstrap liveness and must
continue to enqueue its own items during this slice. The successor may not claim
that capture-anomaly attention from `trajectory_receipts.py` substitutes for these
lifecycle items. Queue append must precede best-effort notification; failures of
notification retain an outstanding item and an attempt record. `attention_wait.py`
and fresh coordinators must read back the expected unhandled items once, including
after restart and a lost notification. Existing acknowledgements and streak state
are preserved; no silent reclassification or auto-ack is permitted.

The proposed path and profile id are **specification identities**, not permission to
install a service or write live state. Any change to them creates a new profile
revision and requires renewed independent review and R4 binding.

## One writer, fenced handoff, and recovery

1. Before any live overlap, inventory the incumbent unit, lock owner, process start
   time, code/unit digests, source revision/cursor, observation-log byte offset and
   digest, attention queue offsets, outstanding item identities, rejection-streak
   state, independent attention producers, and all consumers.
   Read each back twice around a bounded quiescence barrier. A missing source cursor,
   unbounded producer, or changed input during a claimed barrier is a hold.
2. A successor may shadow-read under separate state and produce **no authoritative
   observation or attention effects**. It may not write the legacy log or queue while
   the incumbent owns them. The handoff actor must hold a durable generation/fence
   record and an exclusive *handoff-control* lock across the authority switch;
   the incumbent's existing observer lock is separately checked. The incumbent must
   be confirmed stopped, its cgroup empty, and its observer lock released before
   the successor generation becomes authoritative. A stale generation cannot
   publish; the control lock is released only after the new writer and its readback
   are established. Starting the successor is a
   separately authorized live operation, not a consequence of this specification.
3. Reconcile every **Node-derived** incumbent observation through the barrier with
   the source event ledger and successor journal. Reconcile observer lifecycle records
   such as `OBSERVER_STARTED` by their own process/unit identity and legacy log offset;
   they have no Node transition counterpart. Inventory every attention item by its
   producer and queue identity: Node-outcome items map to source events, liveness
   items remain with the independent liveness producer, and notification/ack records
   are conserved as queue effects. Establish a monotonic source cursor, a mapping
   from each Node-derived legacy identity to successor identity, and digests of
   all classes. Preserve existing pending attention items and acknowledgements. Never re-enqueue
   an already handled event, auto-ack a pending item, or create two authority-bearing
   items for one source event. An unknown mapping or gap blocks the switch.
4. The handoff state machine is `LEGACY` → `QUIESCED` → `SUCCESSOR`, or
   `SUCCESSOR` → `RECOVERING` → `LEGACY`. `QUIESCED` and `RECOVERING` are bounded
   protected states only when the authoritative source ledger continues to durably
   accept events and an independently verified admission fence prevents new
   authority-bearing transitions whose observation cannot be safely buffered.
   The exact fence owner, command, readback, and a 60-second maximum recovery
   interval are part of the installed profile receipt. If those cannot be bound and
   tested, live handoff is inadmissible. An elapsed interval is a durable incident
   and leaves admission fenced; it is never a silent PASS.
5. On failure before transfer, restore `LEGACY` with incumbent unit/lock/readback.
   On failure after transfer, fence the successor generation, read back its last
   committed source cursor and attention effects, and enter `RECOVERING` with
   admission fenced. Under the exclusive handoff-control lock, replay any missing
   source events and corresponding queue effects through a single authorized
   reconciler, with deterministic identities, before starting the incumbent.
   Confirm the successor cgroup empty and no stale generation writer, then restart
   the incumbent, read back its lock/unit/process and observation/attention cursors,
   and only then lift the admission fence. Rollback cannot replay an acknowledged
   event as new or silently skip a pending item. Preserve both evidence stores and
   the handoff ledger. If any fence, replay, effect reconciliation, restart, or
   readback fails, remain in `RECOVERING` with intake fenced and report the concrete
   unresolved protection state; do not claim rollback or retire either evidence path.

## Observation and retention contract

Each accepted successor event has a stable `source + event_id` identity derived from
the authoritative transition (not the observer's poll time), source sequence and
source UTC timestamp, and a gapless capture sequence plus capture UTC timestamp.
The committed record includes source revision and immutable payload digest. A
restarted process replays the committed journal and source cursor before accepting a
new event; a lost acknowledgement is a duplicate with the original capture identity.
Out-of-order or missing source sequences, duplicate identity with differing payload,
timestamp regression, capture stall, corrupt/truncated source input, and consumer
interruption become durable anomaly/hold records. Unknown source times remain
unknown; they are never inferred from `observed_at`. The journal, source ledger,
handoff ledger, receipt chain, legacy JSONL, and attention queue remain readable
through the independent R4 verdict and any later retirement decision. Retention
period or deletion requires a separate authorized policy; no automatic truncation is
part of this slice.

## Required proof and acceptance

The owner must retain an exact profile/source/candidate digest, installed unit and
command, source sequence range, incumbent log/queue offsets, handoff generation,
process/unit/cgroup readbacks, journal and receipt roots, commands with exit codes,
raw immutable observations, and an independent reviewer verdict. A proof run must
cover intact, fault, restored, process restart, and rollback paths on the **actual
authorized target**. Negative controls must inject a source gap, lost acknowledgement,
duplicate, clock regression, consumer failure, stale writer/fence, and interrupted
handoff; each must fail or hold with a counted, attributable observation. Replay and
live readback must show every admitted source event exactly once in order, all pending
attention items preserved, and no duplicate authority-bearing effect. At every
measured boundary, protection means either a verified `LEGACY`/`SUCCESSOR` writer
or a verified bounded `QUIESCED`/`RECOVERING` state with durable source acceptance
and the admission fence active. Retain each state transition, fence and writer
readback; an overdue recovery is a failed operational verdict even while intake
remains fenced. Read back after restart
and after a second reconciliation cycle; an empty queue or active unit alone is not
proof. The independent verdict names the exact candidate/profile and distinguishes
source measurements from inferred coverage.

The negative controls also include each incumbent attention class, a retained
unhandled liveness item, rejected notification delivery, a repeated rejection
straddling process restart, and a failure in `RECOVERING` that leaves admission
fenced. A proof must distinguish Node-derived observations from lifecycle and
independent-producer effects rather than demand a false one-to-one source mapping.

`docs/evidence/wave2-proof-fixtures/FX-R4.md` remains preparation only. #136 may
consume this specification as a named dependency **after independent acceptance**,
but remains TASKS/HOLD until an implemented successor is accepted, an authorized
operational R4 target and proof are bound, and its exact revised packet receives a
fresh native Agent Ready assessment. Neither this document nor local fixture success
authorizes READY, worker dispatch, live cutover, or retirement.

## Source references and disposition

- Issue #44: Founder-owned SF-REQ-029 and owner handoff comments `5873374804`,
  `5874394320`, `5874748137`.
- Issue #136: Founder decision `5872219660`, retained Agent Ready HOLD and R4 gate.
- `docs/evidence/wave2-specified-requirements.{md,json}` BOOTSTRAP-M03 and
  SF-REQ-029 ownership; `docs/evidence/wave2-proof-fixtures/FX-R4.md`.
- Repository source paths named above, at the baseline commit; installed source
  digests named above. The installed source and live unit may drift and must be
  re-read at execution.

General lesson: **DETERMINISTIC_PREFLIGHT** — a replacement gate must compare an
authoritative source cursor, both writer generations, observation and attention
effects, and actual protection readback before it may admit a no-loss claim.

## Independent specification review

A fresh read-only reviewer identified three material gaps in the first draft:
future incumbent attention classes, protected rollback while neither observer is
running, and false one-to-one mapping for observer lifecycle and independent
attention records. The revised contract addresses each explicitly. A final reread
also checked the `QUIESCED`/`RECOVERING` proof predicate; the reviewer reported no
remaining important finding and accepted this as a reviewable **specification**,
not an operational successor verdict. The Director retains the PLAN and live-proof
gates above; review of this text cannot satisfy them.
