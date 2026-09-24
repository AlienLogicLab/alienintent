# FX-C2 implementation plan (WO-220302, DAG node C2, SF-REQ-053-AC-01)

Pinned by the PRODUCER before implementation, against the contract
`docs/work-units/wave2/WO-220302.md` § "Pinned proof packet"
(sha256 `ddfb512eb8e478ca69067f131f52f663edc5882ab4eccfef4239d9a350e80059`) at admission
baseline `036c5fc2d2c7f1699b23ac171e9e019aa8d4fc98`. Proof level
`LOCAL_COMPOSED_OR_MECHANICAL`; disposable local profiles only.

## Admission read-back (verified before this plan)

| Input | Expected | Observed |
|---|---|---|
| baseline | `036c5fc2…8fc98` = `origin/main` | equal |
| `wave2-design-contracts.json` | `56676dd9…f056242` | equal |
| `wave2-dependency-dag.json` | `f99c0a7a…2b1e8d` | equal |
| `wave2-candidate-bius.json` | `61f9324e…4f677f7` | equal |
| `WO-220302.packet.json` / `.allocation.json` | `9ae65adb…202944` / `bbaac7bc…ca37e` | equal |
| FX-C1 `execution-record.json` | `da3c7951…34be55` | equal |
| C1 candidate `8c810d2d…` and U1 candidate `43ea5e2b…` | ancestors of baseline | both ancestors |
| C1 verdict/closure #78 5794214610 / 5794268196 | JC ACCEPT / Morty LANDED | retrievable |
| U1 verdict/closure #76 5792843472 / 5792906393 | JC ACCEPT / Morty DONE | retrievable |

## Interfaces (module splits are implementation-local)

- `context_assembly/domain/reconstruction.py`: pure manifest pinning, record validation,
  `LABELLED_DERIVATION_RULE_v1` derivation, the canonical document and the comparator.
- `context_assembly/ports/context_assembler.py`: `ContextAssembler.pin() -> manifest_ref`;
  `reconstruct(manifest_ref) -> ReconstructedContext | ContextHold`.
- `context_assembly/application/reconstruction_service.py`: reads the existing
  `OperationalStore` and `EvidenceRepository`; installs the immutable S1 `context.manifest`
  observation and then the `context:manifest:<sha256>` pointer aggregate (expected version 0,
  read back); retains `context.reconstruction` observations.
- `composition/control_plane_profile.py`: compatible addition. `AttentionProfile.context`
  shares the store/evidence; `ContextProfile` opens an existing profile read-only for a
  successor and never creates a store.
- `composition/context_reconstruction.py`: the fresh-invocation runner.
  `reconstruct` exits 0 RECONSTRUCTED / 2 HOLD; `compare` exits 0 EQUAL / 1 MISMATCH / 2 HOLD.

Canonical document fields: `authorized_next_action_set`, `blocked_set`, `current_work`,
`unresolved_decisions`, `pending_attention`, `evidence_refs`, `lifecycle`.

## Commands (all `rtk proxy`, `PYTHONPATH=src`)

1. `python3 -B -m pytest -q tests/context_assembly/test_context_reconstruction.py`
2. `python3 -B tools/evidence/fx_c2_evidence.py --output <new-dir> --invocation <exact-invocation>`
3. `python3 -B -m pytest -q`; `python3 -B tools/fitness/check_architecture.py --root src/alienintent --check all`; `node scripts/check.mjs all`

## Probes and expected outcomes

| Test | Expected |
|---|---|
| `test_fresh_invocations_equal` | predecessor process commits a durable event, pins, reconstructs, exits; successors A and B (separate `sys.executable` processes, argv = root/project/profile/manifest/invocation only) return byte-equal documents with equal digests; `compare` exits 0 |
| `test_mismatch_is_failure` | a planted store change after pinning: the pinned manifest holds (exit 2); a re-pinned successor differs and `compare` exits 1 naming the differing fields |
| `test_conversation_not_input` | present versus absent `transcript.jsonl` and `ALIENINTENT_CONVERSATION` → equal digests; runner inputs never name the transcript |
| `test_list_order_independent` | reversed `list_states` order → equal manifest and document digests |
| `test_derivation_rule_uses_lifecycle` | every authorized action is accepted by `lifecycle.transition` on the item's decoded state; blocked items carry typed reasons |
| `test_seen_is_not_resolved` | SEEN attention stays in `blocked_set` and `pending_attention`; only DecisionInbox entries appear in `unresolved_decisions` |
| `test_unavailable_state_holds[missing\|drift\|digest\|evidence\|store\|malformed_inbox\|inventory]` | typed `ContextHold` with reason and affected refs in process, and runner exit 2 |

## Discriminating controls (intact 0 → fault 1 at the named assertion → restored 0; application_count 1)

`manifest_digest_pin`, `missing_record_hold`, `store_unavailable_hold`, `version_fence`,
`malformed_inbox_hold`, `canonical_order`, `conversation_isolation`, `context_item_omitted`,
`mismatch_as_failure`, `lifecycle_rule_bypassed`, `seen_not_resolved`, `queue_distinct`,
`adapter_import_added` (architecture check must exit nonzero). Each is applied once to a disposable
copy by `tools/evidence/fx_c2_evidence.py`. A non-discriminating mutation, an application count
other than 1 or a missing observation is a HOLD, not a PASS.

## Evidence schema

`docs/evidence/wave2-proof-fixtures/FX-C2/` in the FX-C1 layout: `execution-record.json`,
`run-report.json`, `proven-red.json`, `observations/<sha256>`, `digest-manifest.json`, with
labels `LABELLED_DERIVATION_RULE_v1` and `LOCAL_PROCESS_BOUNDARY_SUBSTITUTE_FOR_EPISODE`, residuals
`M_CONTEXT_SHADOW_DEFERRED` and `DECISION_INBOX_LIST_OPEN_SILENT_EMPTY`,
`independent_verdict: PENDING_FRESH_BIU_VERIFIER`, `live_proof: NOT_ESTABLISHED`, and tokens/cost
`null` with an `UNKNOWN` reason.

## Boundaries

There is no resident or bootstrap handoff, no checkpoint retirement and no M-CONTEXT cutover. No
live store, provider, network, model launch or RAI is used. No C3/C4 scope (tenure, epochs,
EpisodeControl) is implemented. C1/U1 behaviour is unchanged.
