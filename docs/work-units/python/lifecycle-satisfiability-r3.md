# Work unit: refuse READY for a packet whose deterministic lifecycle cannot complete

**Label:** `LIFECYCLE-SATISFIABILITY-R3` (a document label; permanent id `PENDING`).
**Status:** Draft revision 3 (at CAPTURE) for independent review, 2026-10-05. Not approved, not assessed, not released.
**Position on the path:** the first fully closed self-build item. Founder 2026-10-05: fix LIFECYCLE-SATISFIABILITY /
READY-REACHABILITY so Agent Ready cannot approve another work item whose deterministic lifecycle is impossible, then
prove READY → PRODUCER → VERIFIER → CLOSURE → automatic exact landing → DONE. Builds on `main`.
**Roles:** launched by the factory: one PRODUCER (self-reviews the complete diff), one fresh VERIFIER on the exact
candidate, CLOSURE through the Landing Authority (landing is on).

## Contract

```json alienintent-contract
{
 "identity": "PENDING",
 "version": "revision-3",
 "intent": "Add one pure satisfiability check over a work item's contract and the host facts, using the same constants the factory coordinator uses, and run it in work assess (before any Agent Ready attempt) and in work authorize (before a release record is written), so a packet whose deterministic lifecycle cannot reach DONE is refused with a hold that names every failing field.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-05: Agent Ready / Work Preparation must reject a packet when its deterministic contract makes successful completion unreachable; required_evidence must be checked against the runtime's actual observable evidence-id vocabulary.",
  "Founder 2026-10-05: do not solve this by adding ad hoc preflight checks one by one; the rules come from the complete gate model in docs/work-units/python/lifecycle-satisfiability-analysis.md.",
  "Founder 2026-10-05: the only priority is autonomous self-building; add no new workflow stage, branch, abstraction or framework beyond what this check needs."
 ],
 "authorized_scope": [
  "src/alienintent/execution_coordination/domain/satisfiability.py",
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/context_assembly/application/packet_assessment.py",
  "src/alienintent/context_assembly/application/work_authorization.py",
  "src/alienintent/composition/work_registry.py",
  "tests/execution_coordination/domain/test_satisfiability.py",
  "tests/context_assembly/test_packet_assessment.py",
  "tests/context_assembly/test_work_authorization.py",
  "tests/composition/test_work_registry.py"
 ],
 "excluded_scope": [
  "any rule not listed in section 2",
  "a change to Agent Ready, the assessment store or its records",
  "a change to coordinator behaviour other than reading the two constants from the new module",
  "landing, closure, worker runtime, routing or board changes",
  "a new workflow stage, state, branch, store or configuration source"
 ],
 "dependencies": [],
 "required_capabilities": [
  "python",
  "filesystem"
 ],
 "budget_policy": {
  "maximum_attempts": 3,
  "hard_wall_clock_seconds": 3600,
  "cancellation_limit": 1
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-6 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "checks of runtime-produced facts (release record, attempt, history, WIP, candidate)",
  "fixing earlier packets"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by the Landing Authority preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/lifecycle-satisfiability-analysis.md"
 ],
 "target_repositories": [
  "AlienLogicLab/alienintent"
 ],
 "baselines": [
  "main"
 ],
 "required_closure_actions": [
  "candidate-published",
  "merged-to-main",
  "landing-record",
  "board-updated",
  "workspaces-cleaned"
 ],
 "stop_escalation_conditions": [
  "a named file, function or constant does not exist at the starting revision",
  "a rule in section 2 would refuse a packet that the gate model shows can complete (rule 3's deliberate refusal excepted)",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

Three launched work items failed on facts that were knowable from the packet and the host before the Founder
authorized them: missing budget limits; an authority reference absent at the immutable pointer commit; and
`required_evidence` values the coordinator can never observe, so ACCEPT was unreachable after a genuine VERIFIER
accept. Today `work assess` never parses the contract, and `work authorize` checks only the gate wording and the
baseline. The full gate model is `docs/work-units/python/lifecycle-satisfiability-analysis.md` (read it through your
`context_command`; its sections 3, 6 and 7 are the basis of this unit).

## 2. The change

1. **New pure module** `src/alienintent/execution_coordination/domain/satisfiability.py`:
   - `ARTIFACT_VERIFIED = "artifact-verified"`, `VERIFIER_EVIDENCE = "independent-verifier-accepted"`,
     `OBSERVABLE_EVIDENCE = frozenset({ARTIFACT_VERIFIED, VERIFIER_EVIDENCE})`;
   - `BASE_CAPABILITIES = frozenset({"python", "filesystem", "process-control"})`;
   - `unsatisfiable(contract, *, landing, present_at_pointer, registered, provider_dimensions) -> tuple[str, ...]`, where
     `contract` is the existing `BiuContract`, `landing` is a bool, `present_at_pointer` and `registered` are callables
     from a string to a bool, and `provider_dimensions` is a `frozenset[str]`. It returns one reason per failing rule, in this order, each starting with the field name and a colon,
     and `()` when every rule holds. It does no I/O itself.
   - The rules:
     1. `required_evidence`: every entry is in `OBSERVABLE_EVIDENCE`.
     2. `release_policy`: equals `explicit-human-off` (the registry releases only explicitly).
     3. `required_capabilities`: every entry is in `BASE_CAPABILITIES`. This refusal is deliberate: a path that needs a
        `work decide` after an authority-block is not a deterministic path (the Founder's readiness rule of 2026-10-05:
        READY means a deterministic path exists, assuming successful cognitive work).
     4. `budget_policy`: `hard_wall_clock_seconds` and `cancellation_limit` are not None, and
        `set(budget_policy.required_dimensions) <= provider_dimensions`.
     5. `required_closure_actions`: `is_fixed(...)` from `execution_coordination/domain/closure.py` holds.
     6. `authority_references`: for each entry, `present_at_pointer(<its first word>)` is true.
     7. `dependencies`: for each entry, `registered(<entry>)` is true.
     8. `landing`: true; otherwise the reason says DONE is unreachable and the item would end at `ready-to-land`.
2. **The coordinator reads the constants** (`factory_coordinator.py`): its existing module constant `VERIFIER_EVIDENCE`
   is imported from the new module (same value), the literal `"artifact-verified"` in `_advance` becomes
   `ARTIFACT_VERIFIED`, and the literal set `{"python", "filesystem", "process-control"}` in `_run` becomes
   `set(BASE_CAPABILITIES)`. No behaviour changes.
3. **`work assess`** (`packet_assessment.py`, `PacketAssessment`): the constructor takes an optional
   `satisfiable: Callable[[bytes, str, str], tuple[str, ...]] | None = None` (packet bytes, the commit holding them,
   the item id), stored as `self.satisfiable`. Immediately before the line `text = instructions_text(record.packet)` in
   `assess`, if `self.satisfiable` is not None, call `reasons = self.satisfiable(record.packet, item.pointer.commit,
   item.id)`; if `reasons` is non-empty, return `Hold(CONTRACT_UNSATISFIABLE, item.id, None, "; ".join(reasons))`. With a
   `revision`, this runs after the pointer has moved, as `set_pointer` does today; it also runs before reuse and before
   recovery. `packet_assessment.py` imports `CONTRACT_UNSATISFIABLE` from `work_authorization.py` in its existing import
   line. With `satisfiable` None nothing changes.
4. **`work authorize`** (`work_authorization.py`, `WorkAuthorization`): `CONTRACT_UNSATISFIABLE = "CONTRACT_UNSATISFIABLE"`
   is defined here, next to `AUTHORIZED_INSTRUCTIONS_FIXED`. The constructor takes the same optional `satisfiable`
   argument, stored as `self.satisfiable`. In `authorize`, right after the contract parses, a non-empty answer for (the
   record's packet, the pointer commit, the item id) returns `AuthorizationResult(item.id, CONTRACT_UNSATISFIABLE,
   detail="; ".join(reasons))`, and no release record is written.
5. **Composition** (`work_registry.py`): the registry passes one `satisfiable` to both services. It parses the contract
   with the existing `contract_block` (a `ContractInvalid` becomes the single reason `contract: <error>`), then calls
   `unsatisfiable` with `landing` = `configuration.github is not None and configuration.github.landing`;
   `present_at_pointer(path)` = `valid_path(path)` and `self.items.read_packet(StoredPointer(repo, path, commit))`
   returns, where `repo` is `self.records.show(identity).item.pointer.repo` (a `WorkIdentityRefused` from it means
   False); the first word of each reference is `(entry.split() or [""])[0]`, exactly as in `WorkContext._reference`;
   `registered(identity)` = the work record exists and is not retired; `provider_dimensions` = `PROVIDER_DIMENSIONS`
   from `composition/sandbox_run_profile.py`. Nothing else in the registry changes.
6. **Imports** (architecture fitness): only `work_registry.py` and `factory_coordinator.py` import `satisfiability`;
   `packet_assessment.py` and `work_authorization.py` must not import it.

## 3. Acceptance checks

1. **Each rule, alone** (`test_satisfiability.py`): with `provider_dimensions` = `PROVIDER_DIMENSIONS`, a contract valid
   for every rule gives `()`; for each of rules 1-8, a contract that fails only that rule gives exactly one reason,
   starting with that field (rule 4 is failed once by a missing limit and once by a hard dimension outside
   `provider_dimensions`). Catches a missing or merged rule.
2. **The real R5 packet**: `contract_block(<the bytes of docs/work-units/python/worker-runtime-doc-correction-r5.md at the
   starting revision>, "8427eb3d-401e-4f4a-8d7c-12abd979c211")`, with
   landing true and `present_at_pointer` and `registered` answering true, gives exactly the `required_evidence:` reason and
   the `required_capabilities:` reason ("git"). Catches a
   rule that would have let R5 through.
3. **`work assess` refuses before Agent Ready** (`test_packet_assessment.py`): an unsatisfiable packet answers
   `CONTRACT_UNSATISFIABLE` naming its reasons, and the producer callable is never called and no attempt is retained; a
   satisfiable packet is assessed exactly as before. Catches a check after the attempt opens.
4. **`work authorize` refuses** (`test_work_authorization.py`): an unsatisfiable packet answers `CONTRACT_UNSATISFIABLE`
   and no release record is written; a satisfiable one authorizes as before. Catches a release record written anyway.
5. **One vocabulary** (`test_satisfiability.py`): the source of `factory_coordinator.py`, parsed with `ast`, has an
   `ImportFrom` of `alienintent.execution_coordination.domain.satisfiability` naming `VERIFIER_EVIDENCE`,
   `ARTIFACT_VERIFIED` and `BASE_CAPABILITIES`, and contains no string constant `"artifact-verified"`,
   `"independent-verifier-accepted"` or `"process-control"`. Catches a second copy of the vocabulary.
6. **Composition and fitness** (`test_work_registry.py`): the registry's assessment and authorization services hold the
   same object as `self.satisfiable`, and a packet whose authority reference is absent at its pointer commit is refused.
   `python -m pytest tests/execution_coordination/domain/test_satisfiability.py tests/context_assembly/test_packet_assessment.py
   tests/context_assembly/test_work_authorization.py tests/composition/test_work_registry.py` passes (no full suite), and `tools/fitness/check_architecture.py --root src/alienintent --check
   all` passes.

## 4. Review record

**Revision 3, replacement work item (2026-10-05).** The packet is unchanged. Its predecessor `dc49e880-0de2-46fd-89a7-bf827f35cccd` (at `docs/work-units/python/lifecycle-satisfiability-r2.md`) reached VERIFY with a good PRODUCER candidate (`c2027fd`) and ended with the final outcome `failure`: the VERIFIER workspace folder was named after its correlation id, which contains ':', and tests that put that folder in PYTHONPATH failed. Fixed by WORKSPACE-FOLDER-NAMES (`6e06e5dc`, landed `5d2f98f`), not in this packet. Its outcome is kept as recorded.

**Revision 2, replacement work item (2026-10-05).** The packet is unchanged. Its predecessor `6cf0fee9-fb15-403d-96d7-64d05067dcc9` (at `docs/work-units/python/lifecycle-satisfiability.md`) reached VERIFY with a good PRODUCER candidate (`866b0bf`) and then ended with the final outcome `failure`: the feature-regression packs run as the worker with `python3 -m pytest`, and the worker's Python had no pytest. Fixed in the deployment (system `python3-pytest`), not in this packet. Its outcome is kept as recorded.

**Revision 1b (2026-10-05).** REVIEWER of `452fa75` (FAIL): B1 the constant lives in `work_authorization.py` (no circular
import); B2 the exact `assess` insertion point; B3 rule 3's refusal is deliberate and excepted from the stop condition;
B4 the exact composition read; S1 rule 4 uses the provider dimensions; S2 import rule; S3-S5 mechanical checks.

**Revision 1 (2026-10-05).** First draft, from the Founder's decisions of 2026-10-05 and the gate model.
