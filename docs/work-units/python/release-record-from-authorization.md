# Work unit: the release record, bound to the Founder's authorization

**Label:** `RELEASE-RECORD-FROM-AUTHORIZATION` (a document label; the permanent id is allocated when this draft is registered).
**Status:** Draft revision 2 (item `ae458d9b-4de1-4c67-a333-8eb982248b09`, at CAPTURE) for independent review, 2026-10-02. Not approved, not assessed, not released.
**Position on the path:** unit 5 of [the shortest dependency path](python-execution-path-20260930.md). Builds on the landed identity service, registration, `work assess`, `work link` and the READY view (`main` `7e85b32`).
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## Contract

```json alienintent-contract
{
 "identity": "ae458d9b-4de1-4c67-a333-8eb982248b09",
 "version": "revision-2",
 "intent": "One command, work authorize, turns the Founder's authorization into the existing release-authorization record for a registered work item, after live checks that the item, its instructions at the exact pointer commit, its READY assessment and the starting revision are what was approved; one evidence record binds them on the item; authorized instructions can no longer be moved; no state changes.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "work authorize records the Founder's approval; it does not grant it. The approval is the Founder's own decision, made before the command runs.",
  "The release record is the existing ReleaseAuthorization in StoredReleaseAuthorizations on the registry store, profile registry.",
  "Authorization changes no workflow state and launches nothing.",
  "Cycle counts belong to the IMPLEMENT/VERIFY transition units, not this unit."
 ],
 "authorized_scope": [
  "src/alienintent/context_assembly/application/work_authorization.py",
  "src/alienintent/context_assembly/application/packet_assessment.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/control_plane/adapters/cli.py",
  "src/alienintent/control_plane/application/operator.py",
  "tools/fitness/coupling_register.json",
  "tests/context_assembly/test_work_authorization.py",
  "tests/context_assembly/test_packet_assessment.py",
  "tests/composition/test_work_registry.py",
  "tests/control_plane/test_cli.py"
 ],
 "excluded_scope": [
  "changing workflow state",
  "board Status or any GitHub write",
  "launching or scheduling work",
  "changing the release gate rules",
  "cycle counts",
  "a second authorization store",
  "changing earlier packets"
 ],
 "dependencies": [],
 "required_capabilities": [
  "python",
  "git",
  "sqlite"
 ],
 "budget_policy": {
  "maximum_attempts": 3
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-7 pass",
  "check 8 real use on a registry copy before acceptance",
  "architecture fitness passes"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation",
  "real use inspected before acceptance"
 ],
 "required_evidence": [
  "VERIFIER verdict file",
  "real-use output",
  "landing record on main"
 ],
 "non_goals": [
  "revoking or superseding an authorization",
  "per-item budget limits",
  "release gate composition for the registry"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by direct merge preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/python-execution-path-20260930.md row 5",
  "Founder direction 2026-10-02: bind authorization to identity, instructions, assessment and starting revision"
 ],
 "target_repositories": [
  "AlienLogicLab/alienintent"
 ],
 "baselines": [
  "main"
 ],
 "required_closure_actions": [
  "direct merge to main",
  "landing record in docs/evidence",
  "remove temporary PRODUCER and VERIFIER worktrees"
 ],
 "stop_escalation_conditions": [
  "a landed interface does not match the packet",
  "any GitHub write would be needed",
  "scope outside the authorized files"
 ]
}
```

## 0. The whole design (plain English)

The existing release gate refuses to start implementation unless a durable release record names the item, explicitly authorizes IMPLEMENT and names an exact starting revision that resolves and is reachable (`execution_coordination/domain/release.py` `admit_release_preconditions`). Today nothing writes that record for a registered work item: only old live-proof tools in `tools/live` do. This unit adds one command, `work authorize`, that turns the Founder's authorization into that record — after live checks that the item, its exact instructions, its assessment and the starting revision are what the Founder approved — and binds them together in one evidence record saved on the item. **The command records the Founder's approval; it does not grant it.** The approval is the Founder's own decision; the command writes it down only if the exact packet revision, assessment attempt and starting revision the Founder approved are still the item's current ones, and refuses stale or mismatched evidence. Once an item is authorized, its instructions and its assessment can no longer change. Authorization changes no workflow state and starts nothing.

**Why it matters:** implementation must start only from what the Founder approved — the same item, the same instructions at the same commit, the same assessment, the same starting revision — and nobody may change the instructions after approval.

## 1. Inputs and their sources

| Input | Source |
| --- | --- |
| the item, its pointer and state | the `work_item` row (`WorkRecordService.show`) |
| the approved packet revision | `--commit <40 hex>`: must equal the row's pointer commit |
| the approved assessment | `--attempt <attempt id>`: must be the attempt whose `raw_ref` equals the row's `assessment_ref`, the latest attempt for the item, READY, with the fingerprint of the current pointer |
| the contract | the packet's contract block at the pointer (`context_assembly/domain/work_contract.py`, landed). A compiler-made item has no block, so it cannot be authorized here. |
| the starting revision | `--baseline <40 hex>` |
| the approver | the contract's `authority_issuer` (no free-form flag) |
| the Founder's words | `--quote <the Founder's exact words>`, required, non-empty |

## 2. Sequence

`work authorize <id or label> --commit <40 hex> --attempt <id> --baseline <40 hex> --quote <text>`:
1. `show`: unknown → `UNKNOWN_IDENTITY`; retired → `IDENTITY_RETIRED`; not at `CAPTURE` or no pointer → `NOT_AUTHORIZABLE` naming why.
2. Approved evidence still current: `--commit` ≠ the pointer commit, or `--attempt` is not the row's assessment attempt, not the latest attempt for the item, not READY, or not of the current pointer's fingerprint → `AUTHORIZATION_STALE` naming which. Nothing is written.
3. Contract: the block must be valid with `identity` equal to the item id → else `CONTRACT_INVALID` naming why.
4. Starting revision: an exact 40-hex commit that resolves in the configured clone of the pointer's repository and is an ancestor of that repository's configured `default_branch`, checked with the existing `GitRevisionResolver` → else `BASELINE_INVALID` naming which.
5. The record to be written — `ReleaseAuthorization(identity=id, record_ref=<the evidence reference's content digest>, authorizes_implement=True, baseline=<baseline>, text=<quote>)` — is first checked with the existing `admit_release_preconditions` (with that resolver and release point); a refusal (for example a quote containing the gate's non-authorization wording) → `GATE_WOULD_REFUSE` naming the check, nothing written.
6. Existing authorization: `release-authorization:<id>` already present with the same content (identity, record_ref, baseline, text) → repeat (step 8); with different content → `ALREADY_AUTHORIZED`, nothing written.
7. Writes, in this order: (a) the evidence record — kind and fixed fields built exactly as the READY view builds its fixed records, content `{identity, pointer {repo, path, commit}, attempt_id, assessment_ref, contract_digest, baseline, approver, quote}`, no time or process value, so the same inputs give the same reference; (b) the release record with `StoredReleaseAuthorizations` (the commit point), read back; (c) `set_evidence(id, "approval", <evidence reference>)` on the row.
8. Repeat: when the release record already matches, only (c) is applied if the row's `approval_ref` differs, which repairs a crash between (b) and (c).

The answer names the item, the evidence reference and the recorded authorization.

**Instructions and assessment fixed after authorization.** `PacketAssessment` refuses with `AUTHORIZED_INSTRUCTIONS_FIXED` when `release-authorization:<id>` exists: `work assess --file --commit` before any pointer move, and a plain `work assess` before opening any new attempt (it may still return the existing reused assessment).

## 3. Components and storage

- **Store:** the registry's existing operational store and evidence folder (the `readiness` entry), profile `"registry"` — the profile the READY view gives its rows, so the later worker-launch unit composes the existing release gate on this store. No new configuration entry.
- **Reused unchanged:** `StoredReleaseAuthorizations`, `ReleaseAuthorization`, `GitRevisionResolver`, `admit_release_preconditions` (its refusals are the specification of what this record must satisfy), `WorkIdentityService.set_evidence`, `work_contract`, the assessment store.
- **Added:** `WorkAuthorization.authorize(...)` (application, `context_assembly/application/work_authorization.py`) with a local `Protocol` for the release records (`record`, `release_authorization`) and the revision resolver, declared in that module the way `packet_assessment.py` declares `ProcessOwnership`; one `tools/fitness/coupling_register.json` entry permitting its import of `execution_coordination.domain.release` (for `ReleaseAuthorization` and `admit_release_preconditions`); its CLI command; the composition wiring; the refusal in `PacketAssessment`.

## 3A. Exact permitted files

Production: `src/alienintent/context_assembly/application/work_authorization.py` (new; declares its own `Protocol` for the release records and uses the `RevisionResolver` port, never the adapters), `src/alienintent/context_assembly/application/packet_assessment.py` (the one refusal), `src/alienintent/composition/work_registry.py` (wiring `StoredReleaseAuthorizations` and `GitRevisionResolver` on the registry store and clone), `src/alienintent/control_plane/adapters/cli.py` and `src/alienintent/control_plane/application/operator.py` (`work authorize`), `tools/fitness/coupling_register.json` (one entry). Tests: `tests/context_assembly/test_work_authorization.py` (new), `tests/context_assembly/test_packet_assessment.py`, `tests/composition/test_work_registry.py`, `tests/control_plane/test_cli.py`.

## 4. Repetition, interruption, failure

- **Repeat** with the same inputs returns the existing authorization; nothing changes.
- **Crash after (a):** the rerun produces the same evidence reference and writes (b) and (c).
- **Crash after (b):** the rerun finds the matching release record and applies only (c).
- **Any check fails:** nothing is written.
- **A repeat after the item has left `CAPTURE`** answers `NOT_AUTHORIZABLE`; the existing authorization is unchanged.
- **For unit 6:** the release gate for registry items is composed on the registry's readiness store, profile `"registry"`, with the pointer repository's clone and its configured `default_branch` as release point — the same values this unit checks against.

## 5. Permissions and prohibited actions

Prohibited: changing the item's workflow state; writing board Status or any GitHub data; launching or scheduling work; changing the release gate's rules; cycle counts (the IMPLEMENT/VERIFY transition units own them); a second authorization store; free-form identity, instruction, assessment or revision values (each comes from the record or is checked exactly); changing earlier packets.

## 6. Acceptance checks (each names the wrong implementation it catches)

1. **Binding.** An authorized item's evidence record holds exactly its id, pointer repository, path and commit, attempt id, assessment reference, contract digest, baseline, approver and quote; the row's `approval_ref` names it; `release_authorization(id)` returns a record that `admit_release_preconditions` accepts with a resolving, reachable baseline. Catches an unbound or gate-refused record.
2. **Live and stale checks.** Retired, not at `CAPTURE`, no pointer; `--commit` not the pointer; `--attempt` not the row's attempt, not the latest, not READY or of an older pointer; an invalid contract block; a short, unknown or unreachable baseline; a quote the gate would refuse — each refused with its code and nothing written. Catches recording what was not approved, or what has changed since.
3. **Repeat and crash.** A repeat changes nothing; with a fault after the evidence and before each later write, the rerun completes without a second evidence record. Catches duplicates and half-written authorizations.
4. **Different authorization.** A second call with another baseline or quote → `ALREADY_AUTHORIZED`, and with another attempt or commit → `AUTHORIZATION_STALE`, nothing written in either case; the release record's `record_ref` is the exact evidence digest. Catches silent replacement and an unbound record.
5. **Instructions and assessment fixed.** After authorization, `work assess --file --commit` refuses before moving the pointer, and a plain `work assess` opens no new attempt. Catches instructions or assessment changed under an approval.
6. **No state change.** Before and after, the row's state is `CAPTURE` and no transition, board or GitHub call is made. Catches authorization treated as release.
7. **Wiring.** `work authorize` with and without the `readiness` entry (without it the answer is `readiness-not-configured`); the changed files' tests and `check_architecture.py --check all` pass.
8. **Real use, before acceptance (the Founder runs, the VERIFIER inspects).** Preconditions: this unit's item has a READY `work assess` result; the Founder runs the command outside Claude Code on a copy of the permanent registry (configuration, work database, readiness database and evidence folder, the folder at mode 0700). The Founder authorizes this unit's own registered item with its pointer commit, its attempt and a baseline on `main`; the VERIFIER confirms the evidence record, the row's `approval_ref`, the release record read back and accepted by `admit_release_preconditions`, and that a repeat changes nothing.

## 7. Excluded

Workflow state changes and cycle counts; moving the board card to READY; worker launch and the release gate's composition for the registry (unit 6); per-item budget limits (`biu_limits`); revoking or superseding an authorization; changing earlier packets.

## 8. Review record

**Revision 2b (2026-10-02).** The reviewer's recheck: three one-line fixes (the module's own Protocol named in §3A; check 4's codes; check 1's full field list), plus two clarifying sentences in §4.

**Revision 2 (2026-10-02).** An independent review of `b994de7` failed (three blocking, four medium), fixed: a local Protocol and one coupling-register entry; required `--commit` and `--attempt` so stale or mismatched evidence is refused; `record_ref` is the exact evidence digest; the gate's own preconditions are checked before writing; the authorized assessment must be the latest and later assessments are refused; the clone and release point are named; the evidence record is fixed like the READY view's; the release record is the commit point; the approver comes from the contract. The Founder's addendum is stated: the command records approval and does not grant it.

**Revision 1 (2026-10-02).** First draft, against `main` `7e85b32`.
