# FX-B5 — Human attention handoff and acknowledged human receipt (WO-220508, Issue #128)

Status: **PINNED before implementation** by PRODUCER invocation
`AlienLogicLab/alienintent#128:PRODUCER:ce1a2eae-a310-483e-af55-0362eaf166cf` (worker Morty),
admission baseline `62e693932dcbd6b6583a1d37b172f4b418af9256`. This contract is committed before any
source change. Later commits may add evidence but may not weaken these probes. Changing them needs
the authority that owns the node.

## Governing inputs

- Work unit: `docs/work-units/wave2/WO-220508.md`. Agent Ready READY input SHA-256 is
  `d25c25a3c1da356e6cd0e8d58aa649533f268d5db80536a6aa11cdcff2c1500e`.
- Execution packet: `docs/evidence/wave2-execution-packets/WO-220508.packet.json` and `.allocation.json`.
- Requirement: SF-REQ-053. DAG node: B5. Candidate contract sha256
  `5ff729d6d77c6dde3c69fc908c91db138e0fd142601765e4d4590faf554c276a`.
- Founder decisions, recorded on Issue #128 and in the Director inbox:
  - `founder-windows-notification-scope-20260926T070519Z`: no Windows notification and no replacement channel.
  - `founder-attention-receipt-fxb5-scope-20260926T072316Z`: defines human receipt, grants
    ATTENTION_ACTIVATION_AUTHORITY narrowly and names the FX-B5 operational target.
- Predecessors, composed unchanged:
  - WO-220301 / FX-C1: C1 attention, failed delivery stays pending, no unattended activation.
  - WO-220305 / FX-C5: supervised monitor host alerts.
  - WO-220501 / FX-B0: bootstrap custody manifest.

## Surface (no new subsystem)

The authorized surface is the existing Python C1 attention path, as follows.

| Role | Location |
|---|---|
| Service | `src/alienintent/control_plane/application/attention.py` (`AttentionService`) |
| Durable store | `DurableAttentionRepository`: SQLite pointer plus immutable evidence history |
| Composition | `AttentionProfile` |
| Operator surface | A thin command module over the same profile, `python -m alienintent.composition.attention_inbox`, with `list`, `show`, `history` and `acknowledge` |

This work adds no notification channel, no Windows notification, no activation executor and no
external effect. `request_activation` keeps returning a hold.

## Human receipt: the acknowledgement record shape

`AttentionService.acknowledge(identity, actor, expected_version, statement)` writes one new
attention history version. That version has:

- `action = "ACKNOWLEDGED"`.
- `status = "SEEN"`. The existing status vocabulary `{PENDING, SEEN, RESOLVED}` is preserved, and
  an acknowledgement is **not** a resolution.
- `acknowledgement`, an object with these fields:

| Field | Meaning |
|---|---|
| `item_identity` | The acknowledged `attention:` identity. It must equal the item. |
| `item_version` | The exact version the human acknowledged, compare-and-set checked. |
| `item_history_ref` | The immutable history ref of that version, which is what the human was shown. |
| `actor` | A configured named human acknowledger. This is a trusted composition input, never a caller claim. |
| `at` | The UTC timestamp from the service clock. |
| `statement` | The human's explicit non-empty acknowledgement text. |

The history version is an immutable content-addressed evidence Observation, chained through
`preceding_refs`. Its ref is the immutable observation ref of the receipt.

Admission holds that must be enforced:

| Hold | Condition |
|---|---|
| `WRONG_ACKNOWLEDGER` | The actor is not a configured human acknowledger. The notifier, the producer and resolvers are not acknowledgers unless explicitly configured. |
| `STATEMENT_REQUIRED` | The statement is missing or empty. |
| `ALREADY_ACKNOWLEDGED` | The item already has an acknowledgement. There is exactly one acknowledgement per item, and a duplicate never mints a second one. |
| `ALREADY_RESOLVED` | The item is already resolved. |
| `VersionConflict` | The expected version is stale. |

The following never create an acknowledgement:

- queue insertion (`ensure`/`handle`);
- command delivery;
- a `DELIVERED` notification receipt;
- transport success;
- rendering (`list`/`show`);
- `seen()`.

## Probes (local, mechanical; labelled LOCAL, never operational acceptance)

Test module: `tests/control_plane/test_attention_acknowledgement.py`.

| Probe | Predicate |
|---|---|
| B5-01 receipt-distinct | Insertion, `DELIVERED` notification with a correlated receipt, `show`/`list` and `seen()` leave `acknowledgement is None`. Only `acknowledge` sets it. |
| B5-02 receipt-shape | The acknowledgement binds item identity, acknowledged version and history ref, actor, timestamp and statement. The history entry is `ACKNOWLEDGED`, with version +1 and status SEEN. The item stays in `list_pending()` until resolved. |
| B5-03 acknowledger-authority | A non-configured actor (including `notifier` and the producer), an empty statement and a stale version are refused. The item is unchanged. |
| B5-04 zero-duplicate | Repeat `ensure`/`handle` of the same origin yields one item and one notification attempt. A second acknowledge is refused `ALREADY_ACKNOWLEDGED`. Exactly one `ACKNOWLEDGED` entry exists in history. |
| B5-05 judgment-and-done | Both `JUDGMENT` and `DONE` origins are acknowledgeable. A judgment outcome's attention stays unresolved after acknowledgement. |
| B5-06 pending-reconciliation | After a failed delivery the item stays PENDING with a FAILED attempt. A fresh process can acknowledge it and later resolve it, and acknowledgement survives resolution. |
| B5-07 suppression-intact | With a completed judgment outcome, liveness keeps emitting `liveness.suppressed` after acknowledgement, and there is no relaunch. Only a valid resolution lifts it. |
| B5-08 queue-persists | Items, attempts, acknowledgement and history survive a process restart: a new profile instance on the same root reads back identical items. |
| B5-09 operator-surface | The `attention_inbox` command lists pending items, acknowledges one with `--actor/--expected-version/--statement`, refuses a non-configured actor with exit 2, and never resolves. |
| B5-10 no-activation | `request_activation` still returns a hold after acknowledgement. |

Mechanical controls follow intact/fault/restored discrimination, with one per material failure
class. Each is applied once in a disposable copy by `tools/evidence/fx_b5_evidence.py`.

| Control | Failure class | Mutation |
|---|---|---|
| `delivery_counts_as_receipt` | Command delivery or transport mistaken for human receipt | A `DELIVERED` notification writes an acknowledgement. |
| `acknowledger_unchecked` | Acknowledgement by a non-human or unconfigured actor | Drop the acknowledger check. |
| `duplicate_acknowledgement` | Duplicate handling | Drop the `ALREADY_ACKNOWLEDGED` guard. |
| `acknowledgement_resolves` | Suppression broken, or acknowledgement confused with resolution | The acknowledgement writes `status=RESOLVED`. |

The intact and restored runs must pass. The fault run must fail with an `AssertionError` that
contains the pinned assertion text.

## Commands (pinned)

1. Local proof runner, which writes a new output directory with immutable observations:

   ```
   PYTHONPATH=src:. python3 -B tools/evidence/fx_b5_evidence.py --output <new dir> --invocation <exact invocation>
   ```

   It runs:
   - `python3 -B -m pytest -q -p no:cacheprovider tests/control_plane/test_attention_acknowledgement.py`
   - `python3 -B -m pytest -q -p no:cacheprovider tests/control_plane/test_attention.py tests/execution_coordination/test_liveness_reconciliation.py tests/control_plane/test_monitor_host.py tests/composition/test_bounded_control_capstone.py`
   - `python3 -B tools/fitness/check_architecture.py --root src/alienintent --check all`
   - `python3 -B -m pytest -q -p no:cacheprovider tools/verification/test_feature_regressions.py`
   - the four mutation controls above.

   Expected outcome: exit 0, `run_state=COMPLETE`, all probes PASS, all four controls discriminating.

2. Operational target preparation, on the authorized existing Python attention surface. The
   operational root is outside the repository, by default `~/.local/state/alienintent/fx-b5/attention`:

   ```
   PYTHONPATH=src python3 -B tools/live/fx_b5_operational.py prepare --root <root> --acknowledger <named human> --invocation <exact invocation>
   ```

   This ensures one `JUDGMENT` and one `DONE` item for Issue #128 with origin identities
   `fx-b5:operational:judgment:1` and `fx-b5:operational:done:1`. It is idempotent: rerunning never
   duplicates. It performs no notification and no activation.

3. Human acknowledgement, performed **only by the named human**:

   ```
   PYTHONPATH=src python3 -B -m alienintent.composition.attention_inbox --config <root>/attention-inbox.json list
   PYTHONPATH=src python3 -B -m alienintent.composition.attention_inbox --config <root>/attention-inbox.json acknowledge <attention id> --actor <named human> --expected-version <n> --statement "<text>"
   ```

4. Operational readback:

   ```
   PYTHONPATH=src python3 -B tools/live/fx_b5_operational.py readback --root <root> --output docs/evidence/wave2-proof-fixtures/FX-B5/operational/<UTC ts>
   ```

   Expected outcome: `OPERATIONAL_READBACK_COMPLETE`. That requires the JUDGMENT item to carry an
   acknowledgement by a configured human, and the readback to bind, for each item:
   - the item identity and origin;
   - the acknowledgement record;
   - the transition from the prior history version to the ACKNOWLEDGED version, with immutable
     refs and evidence object digests;
   - the unresolved queue state and zero duplicates.

   Without a human acknowledgement the result is `HOLD: HUMAN_ACKNOWLEDGEMENT_ABSENT`. That is
   never a PASS, and never replaced by an agent-made acknowledgement.

## Evidence schema

The output directory contains:

- `execution-record.json`, which holds:
  - `fixture`, `biu`, `invocation`;
  - `source_candidate` (git HEAD, with a digest of each touched source file);
  - `admission_baseline`;
  - `commands[]`, where each command has `argv`, `exit_status` and an `observation` ref;
  - `probes{}` with PASS/FAIL/HOLD;
  - `holds[]`, `run_state` and `exit_status`.
- `proven-red.json`, which records the controls with intact/fault/restored observation refs and
  application counts.
- `run-report.json`, which maps acceptance criteria to probes.
- `digest-manifest.json`, which records the sha256 of every file in the run.
- `observations/<sha256>`, which holds immutable canonical JSON.

The operational readback uses the same observation layout plus `readback.json`. Missing or
unavailable measurements are recorded as holds, never as zero or PASS.

## Non-claims

- Local probe results are labelled LOCAL and do not satisfy operational acceptance.
- An acknowledgement made by an agent, test or fixture is never human receipt. Only the named
  human's own `acknowledge` on the operational root counts.
- There is no release, no cutover, no Node/bootstrap retirement, no Windows notification, no
  replacement channel and no unattended activation.
