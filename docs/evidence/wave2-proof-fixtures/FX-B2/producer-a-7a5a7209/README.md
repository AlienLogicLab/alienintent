# WO-220505 Producer A continuation: isolated proof and live-adapter hold

Issue #125; invocation `AlienLogicLab/alienintent#125:PRODUCER:7a5a7209-de95-4f3f-9fbb-a403f21757a6`.
This record is a Producer A custody record, not phase-2 acceptance or a VERIFY verdict.
The source tree for the isolated run was committed unchanged as
`5bca4b03fdea3df33f33a7503985cfee88e23ade` after the prior Producer A
branch was merged into the runtime-assigned worktree. The earlier diagnostic and
its non-acceptance disposition remain in `diagnostic-1963eb88/`.

## Isolated target

The new profile root is
`/home/netmarine/.local/state/alienintent/fx-b2/7a5a7209-de95-4f3f-9fbb-a403f21757a6/profile`.
The config is in its parent directory and binds the current worktree `src/`,
`fx-b2-liveness-operational`, the same invocation ID and the pinned 300/60/90
second policy. Its SHA-256 is
`3c6f32b224e30a1c3468a5326777c777766bd93fbd019bb85e542cb83c47ecf2`.
A real `StoreLifecycleJournal.enter` seeded generation 1, and
the authority state was committed with a finite expiry before launch.
`tools/live/fx_b2_capture.py --preflight` exited 0 before its guarded
`--launch` exited 0. The host launched under the user systemd unit
`alienintent-monitor-466dd9b8d64bddbb181224bcb6c5ee7d.service` with
launch ID `334153827d174e5bafae823c77a59dab`; its manager timer was active.
A second guarded launch exited 2 with `HOST_ALREADY_OWNED`.

The generation-1 entry time was `1790693863841806` microseconds. A hosted scan
at `1790694174973446` recorded `liveness.gap`,
`liveness.recovery_intent` and `liveness.readback_confirmed`, with
`G_PLUS_I_CLAIMED`. Elapsed time was 311.131640 seconds, within G+I=360.
The direct guarded store readback records one confirmed effect under
`liveness-effect:463f23c7430c68b0abee209e5f02203dfd3ecdd6e6796e073fb7312198161f2d`.
The immutable capture at that point is
`observations/39972549405bc1d6826bdd01a965a997fe04919230c9859f0e02b97d10b8c0f1`.

The exact isolated host was stopped and read back inactive with MainPID 0.
The supervisor observed `FAILED/UNIT_MISSING`, retained an attributable alert,
and restarted through that alert into launch ID
`5c7fe0984502429094fb497f2b478f5d`. A delayed original admission against
the same generation-1 effect key returned `Refused/EFFECT_IDENTITY_USED`.
This first restart tests a duplicate after a settled effect. Generation 2 was
then entered at `1790694287242768` with a correlated `FOUNDER_EXCEPTION`
outcome for the isolated probe. The eleventh suppressed hosted scan was at
`1790694927221594`, 639.978826 seconds after entry, with
`JUDGMENT_UNRESOLVED`; the effect ledger still held only generation 1's one
confirmed effect. Capture:
`observations/f0f08430ba66111ab3b6be41be610461f2b149ce705d81287f126911fe3e7d58`.
One matching C1 judgment item was resolved using an attributed decision
reference `sha256:67a16d10c01cff798ef9a5280addf069000a80d333560fb45a1dc52fa867714f`.
The next hosted scan reported `COMPLETED_AWAITING_PROJECTION`, with no new
effect. Capture:
`observations/5e87557e8f4b322af2ce5a27292beded39c682519124957a3b7e0dd177476e98`.
The separate host-stop alert was retained, not resolved as the judgment item.

Generation 3 was entered at `1790695061739443`; its hosted scan at
`1790695107365018` reported `WITHIN_GRACE`. The exact host was stopped and
the supervisor retained a second `UNIT_MISSING` alert. After 331.755023
real seconds, a read-only `StoreEffectObservation` plus the canonical pure
`inspect` classified a `Gap`. A separate original-delivery `intend` call
persisted effect
`liveness-effect:d6444c698e8685a9f54abe2acf3a0b76da4bdaa4467b1c92b559d665799dfb41`
as `pending` without delivery. The pre-restart capture is
`observations/cfce7e5994d3f8512b02f96f570b26b59a6716782d2f8029dbdcc2a13b87da20`.
The alert-bound supervisor restart launched
`4b357138f27e48c0860fc6e495b7b41f`; startup reopened the pending intent.
Direct guarded readback then showed exactly one confirmed entry for this key,
receipt `sha256:00e221f1de70795b8a9a7588796f1aa9fde1fe892590a398018df8767a76278d`,
the exact host invocation, and no pending or unknown effects. A delayed
original admission returned `Refused/EFFECT_IDENTITY_USED`; the ledger
remained at the same two total effects for generations 1 and 3. The next
hosted scan reported `COMPLETED_AWAITING_PROJECTION`. Final running and
post-stop captures are
`observations/db1cf3d43c4ce69d9efe3e95f3b3cd1b4a5aa8713e20cda3a3537b8c97033907`
and
`observations/0db3b946a5258f8e22c21141a3715d0205da2103f1467dbe15987b32c0175c79`.
All referenced attention, monitor and host evidence objects are retained
beside these content-addressed captures.

After capture, the isolated host and observer timer both read `inactive`;
the host MainPID was 0. The incumbent `alienintent-liveness.service` was
still `active` with MainPID 2453523. The isolated profile and immutable
capture files are retained for Producer B/verifier readback; no unit remains
running from this fixture. This is local operational mechanics evidence.
Its sequence was driven by recorded shell/Python invocations rather than one
committed run controller with complete command/output receipts, so it is not
represented as a fully admissible phase-1 receipt or an independent verdict.

## Real-lane adapter hold

No real #125 lane, Project item, bootstrap liveness service or other BIU was
mutated for this isolated run. The live adapter is absent from the candidate:
`LivenessProfile` still binds `StoreEffectObservation` to its local SQLite store,
and `CanonicalEffectAdmission` still confirms a local guarded journal effect.
Neither reads the real Node `state.json` and Issue outcome under an exact fresh
Project generation or performs a fenced remote Project recovery mutation.

The existing `GitHubProjectsV2Directory.write_status` calls
`updateProjectV2ItemFieldValue` with project, item, field, and option, then
returns its caller-supplied `expected_revision` whenever a later status read
matches. A focused local probe returned both arbitrary supplied revisions 1
and 999 as confirmed. Live GraphQL schema introspection of
`UpdateProjectV2ItemFieldValueInput` returned only `clientMutationId`,
`projectId`, `itemId`, `fieldId`, and `value`: there is no expected version or
compare-and-set field in this configured mutation. A delayed stale write thus
cannot be fenced by that Project API, and matching status readback cannot prove
which invocation wrote it. The Node dispatcher additionally requires an
authorized operator Status event later than the prior `FOUNDER_EXCEPTION` for
re-admission; a worker-origin Project write cannot silently stand in for it.
The direct Project readback in `project-125-readback.json` still shows this
Issue at `IMPLEMENT`; `dispatcher-readback.json` records this invocation as
its sole active lane and retains earlier exceptions separately. These are
observations only, not authorization to change either source. The live
mutation input schema is in `project-mutation-input-schema.json`.

The pinned contract explicitly parks an effect whose existing consumer cannot
prove idempotence/fencing and durable exact readback. **Disposition: PARKED.**
Owner: this Producer A invocation on its published candidate branch. The
candidate must not be used to open the phase-2 live window, signal VERIFY, or
claim AC-08. The required next control is a reviewed, executable real-lane
effect design with a fence that the Project/dispatcher path can enforce, plus
complete command/output custody for phase 1. The named architecture/Program
Director owner must resolve that interface within this node's authority or
route the gap to SPECIFY/Founder under the work packet's escalation rule.
Only after that may the Director preflight a fresh generation and run the
separate phase-2 window. No live service, Project item, or other BIU is to be
altered to make a gap appear.
