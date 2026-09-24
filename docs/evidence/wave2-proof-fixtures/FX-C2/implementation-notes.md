# FX-C2 implementation notes (WO-220302)

## Labelled choices

- **`LABELLED_DERIVATION_RULE_v1` (U-1).** `authorized_next_action_set` probes every action in
  `execution_coordination.domain.lifecycle.transition`'s vocabulary on the decoded pure
  `ExecutionState`. Nothing is committed. Each probe supplies that action's own admission witness:
  an independently read-back candidate for `verify`, and an ACCEPT verdict for `accept`. The set
  therefore names the actions the stage permits; their guards still apply when they are executed.
  `close` needs a bound `BiuContract`, and durable factory state does not carry one, so `close` is
  never offered. `authority-block` and `cancel` always raise, so they are never offered either.
  Terminal items (stage DONE, or outcome `cancelled-by-*`/`failure`/`timeout`) follow
  `FactoryCoordinator.guard_account`: they appear only in `lifecycle`. Blocked items carry typed
  reasons: `AUTHORITY_BLOCK`, `OPEN_DECISION`, `PENDING_ATTENTION:<PENDING|SEEN>`. No stage, action
  or predicate is introduced.
- **`LOCAL_PROCESS_BOUNDARY_SUBSTITUTE_FOR_EPISODE` (U-3).** The predecessor
  (`tests/context_assembly/context_episode.py`) commits the durable SEEN event, pins the manifest,
  reconstructs and exits. Successors are separate `sys.executable` processes. Their argv carries
  only root/project/profile/manifest/invocation, stdin is `/dev/null`, and the environment holds
  only `PATH`/`PYTHONPATH`. C3 re-proves replacement under `053-tenure-fence`.

## Persistence (U-2)

`pin()` enumerates `factory:*`, `release:*`, `attention:*`, `decision-inbox` and
`upstream:requirements:current`, and pins each record by version and canonical digest together with
the evidence bodies they reference: attention history heads and the inventory snapshot. It checks
that those bodies can be retrieved. It then installs the immutable S1 observation
`context.manifest`, reads it back, and CASes `context:manifest:<sha256>` at expected version 0,
reading the pointer back afterwards. A concurrent pin of identical content is equivalent; any other
`VersionConflict` is a typed `VERSION_DRIFT` hold. No store schema, database engine or C1/U1 module
is changed, and the inventory is read through the existing `InventoryService.read`.

## Holds (U-4, U-6)

`reconstruct()` returns `ContextHold` and never raises it:

| Condition | Hold reason |
|---|---|
| pointer absent, or a pinned record deleted | `MISSING_RECORD` |
| store version differs from the manifest, or an enumerated record is created after pinning | `VERSION_DRIFT` |
| same version but different state, or the manifest digest does not match | `DIGEST_MISMATCH` |
| a pinned evidence body is unavailable | `EVIDENCE_UNAVAILABLE` |
| the store cannot serve a read | `STORE_UNAVAILABLE` |
| the raw `decision-inbox` shape is invalid; `DecisionInbox.list_open` is unchanged | `MALFORMED_DECISION_INBOX` |
| the inventory pointer or snapshot is unavailable | `INVENTORY_UNAVAILABLE` |
| undecodable manifest or attention bodies | `INVALID_MANIFEST` / `MALFORMED_RECORD` |

The runner exits 0 RECONSTRUCTED/EQUAL, 1 MISMATCH, 2 HOLD, and 3 ERROR, so an unexpected failure
is never reported as a mismatch or a pass.

## Review

An independent read-only review of `0261ec4` found nothing blocking and four should-fix defects:
- untyped exceptions escaping for a non-string inbox option and for non-JSON or NaN manifest and
  attention bodies;
- an untyped `VersionConflict` when two pins race;
- runner crashes that exited with the MISMATCH code;
- rule-text precision about witnesses and `close`.

All four are repaired with regression tests
(`test_malformed_inputs_hold_rather_than_raise`, `test_concurrent_pin_of_identical_state_is_equivalent`,
`test_runner_errors_are_not_mismatches`). Those five cases failed on `0261ec4` and pass after the repair.

## Residuals

- `M_CONTEXT_SHADOW_DEFERRED`: there is no comparison with the live bootstrap checkpoint, and no
  handoff or retirement. These belong to R5/FX-R5 under POSTW1-DECIDE-006A.
- `DECISION_INBOX_LIST_OPEN_SILENT_EMPTY`: `DecisionInbox.list_open` still returns `()` for a
  malformed aggregate. This is recorded for its C1 owner and not repaired here.
