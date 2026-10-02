# Work unit: the release record, bound to the Founder's authorization

**Label:** `RELEASE-RECORD-FROM-AUTHORIZATION` (a document label; the permanent id is allocated when this draft is registered).
**Status:** Draft revision 1 for independent review, 2026-10-02. Not approved, not assessed, not released.
**Position on the path:** unit 5 of [the shortest dependency path](python-execution-path-20260930.md). Builds on the landed identity service, registration, `work assess`, `work link` and the READY view (`main` `7e85b32`).
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## 0. The whole design (plain English)

The existing release gate refuses to start implementation unless a durable release record names the item, explicitly authorizes IMPLEMENT and names an exact starting revision that resolves and is reachable (`execution_coordination/domain/release.py` `admit_release_preconditions`). Today nothing writes that record for a registered work item: only old live-proof tools in `tools/live` do. This unit adds one command, `work authorize`, that turns the Founder's authorization into that record — after live checks that the item, its exact instructions, its assessment and the starting revision are what the Founder approved — and binds them together in one evidence record saved on the item. Once an item is authorized, its instructions can no longer be moved. Authorization changes no workflow state and starts nothing.

**Why it matters:** implementation must start only from what the Founder approved — the same item, the same instructions at the same commit, the same assessment, the same starting revision — and nobody may change the instructions after approval.

## 1. Inputs and their sources

| Input | Source |
| --- | --- |
| the item, its pointer and state | the `work_item` row (`WorkRecordService.show`) |
| the assessment | the row's `assessment_ref`, matched in `consumer.history(id)` (as the READY view does) |
| the contract | the packet's contract block at the pointer (`context_assembly/domain/work_contract.py`, landed) |
| the starting revision | `--baseline <40 hex>` |
| the Founder's authorization | `--approver <name>` and `--quote <the Founder's exact words>`, both required, both non-empty |

## 2. Sequence

`work authorize <id or label> --baseline <40 hex> --approver <name> --quote <text>`:
1. `show`: unknown → `UNKNOWN_IDENTITY`; retired → `IDENTITY_RETIRED`; not at `CAPTURE` → `NOT_AUTHORIZABLE` naming the state; no pointer → `NOT_AUTHORIZABLE`.
2. Assessment: the entry whose `raw_ref` equals `assessment_ref` must have the fingerprint of the current pointer and a READY outcome → else `ASSESSMENT_MISSING`.
3. Contract: the block must be valid with `identity` equal to the item id → else `CONTRACT_INVALID` naming why.
4. Starting revision: an exact 40-hex commit that resolves in the configured clone and is an ancestor of the default branch, checked with the existing `GitRevisionResolver` → else `BASELINE_INVALID` naming which.
5. Existing authorization: if `release-authorization:<id>` already exists with the same content, return it unchanged (repeat-safe); with different content → `ALREADY_AUTHORIZED`, nothing written.
6. Evidence: one record in the registry's evidence repository with exactly `{identity, pointer {repo, path, commit}, assessment_ref, contract_digest, baseline, approver, quote}` — no time or process value, so a repeat produces the same reference.
7. In one step after the evidence is saved: `set_evidence(id, "approval", <that reference>)` on the row, then `StoredReleaseAuthorizations(<registry store>, "registry").record(ReleaseAuthorization(identity=id, record_ref=<evidence logical id>, authorizes_implement=True, baseline=<baseline>, text=<quote>))`, read back with `release_authorization(id)`.

The answer names the item, the evidence reference and the recorded authorization.

**Instructions fixed after authorization.** `work assess --file --commit` (`PacketAssessment`, step 2a) refuses with `AUTHORIZED_INSTRUCTIONS_FIXED` when `release-authorization:<id>` exists, before any pointer move. A plain `work assess` (no new revision) is unaffected.

## 3. Components and storage

- **Store:** the registry's existing operational store and evidence folder (the `readiness` entry), profile `"registry"` — the profile the READY view gives its rows, so the later worker-launch unit composes the existing release gate on this store. No new configuration entry.
- **Reused unchanged:** `StoredReleaseAuthorizations`, `ReleaseAuthorization`, `GitRevisionResolver`, `admit_release_preconditions` (its refusals are the specification of what this record must satisfy), `WorkIdentityService.set_evidence`, `work_contract`, the assessment store.
- **Added:** `WorkAuthorization.authorize(...)` (application, `context_assembly/application/work_authorization.py`), its CLI command, the composition wiring, and the one refusal in `PacketAssessment`.

## 3A. Exact permitted files

Production: `src/alienintent/context_assembly/application/work_authorization.py` (new; uses the `ReleaseAuthorizationRecords` and `RevisionResolver` ports, never their adapters), `src/alienintent/context_assembly/application/packet_assessment.py` (the one refusal), `src/alienintent/composition/work_registry.py` (wiring `StoredReleaseAuthorizations` and `GitRevisionResolver` on the registry store and clone), `src/alienintent/control_plane/adapters/cli.py` and `src/alienintent/control_plane/application/operator.py` (`work authorize`). Tests: `tests/context_assembly/test_work_authorization.py` (new), `tests/context_assembly/test_packet_assessment.py`, `tests/composition/test_work_registry.py`, `tests/control_plane/test_cli.py`.

## 4. Repetition, interruption, failure

- **Repeat** with the same inputs returns the existing authorization; nothing changes.
- **Crash after the evidence is saved and before the row or store is written:** the rerun produces the same evidence reference (fixed content) and completes both writes.
- **Crash after `set_evidence` and before the release record:** the rerun finds the row's `approval_ref` equal to the reference it would write and completes the release record.
- **Any live check fails:** nothing is written.

## 5. Permissions and prohibited actions

Prohibited: changing the item's workflow state; writing board Status or any GitHub data; launching or scheduling work; changing the release gate's rules; cycle counts (the IMPLEMENT/VERIFY transition units own them); a second authorization store; free-form identity, instruction, assessment or revision values (each comes from the record or is checked exactly); changing earlier packets.

## 6. Acceptance checks (each names the wrong implementation it catches)

1. **Binding.** An authorized item's evidence record holds exactly its id, pointer commit, assessment reference, contract digest, baseline, approver and quote; the row's `approval_ref` names it; `release_authorization(id)` returns a record that `admit_release_preconditions` accepts with a resolving, reachable baseline. Catches an unbound or gate-refused record.
2. **Live checks.** Retired, not at `CAPTURE`, no pointer, no READY assessment of the current pointer, an invalid contract block, a short, unknown or unreachable baseline — each refused with its code and nothing written. Catches authorizing what was not approved.
3. **Repeat and crash.** A repeat changes nothing; with a fault after the evidence and before each later write, the rerun completes without a second evidence record. Catches duplicates and half-written authorizations.
4. **Different authorization.** A second call with another baseline or quote → `ALREADY_AUTHORIZED`, nothing written. Catches silent replacement.
5. **Instructions fixed.** After authorization, `work assess --file --commit` refuses before moving the pointer; a plain `work assess` still works. Catches instructions changed under an approval.
6. **No state change.** Before and after, the row's state is `CAPTURE` and no transition, board or GitHub call is made. Catches authorization treated as release.
7. **Wiring.** `work authorize` with and without the `readiness` entry; the changed files' tests and `check_architecture.py --check all` pass.
8. **Real use, before acceptance (the Founder runs, the VERIFIER inspects).** On a copy of the permanent registry, the Founder authorizes this unit's own registered item with a baseline on `main`; the VERIFIER confirms the evidence record, the row's `approval_ref`, the release record read back and accepted by `admit_release_preconditions`, and that a repeat changes nothing.

## 7. Excluded

Workflow state changes and cycle counts; moving the board card to READY; worker launch and the release gate's composition for the registry (unit 6); per-item budget limits (`biu_limits`); revoking or superseding an authorization; changing earlier packets.

## 8. Review record

**Revision 1 (2026-10-02).** First draft, against `main` `7e85b32`.
