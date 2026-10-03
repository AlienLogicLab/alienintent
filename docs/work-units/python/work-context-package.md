# Work unit: the per-role context package for a registered work item

**Label:** `WORK-CONTEXT-PACKAGE` (a document label; the permanent id is allocated when this draft is registered).
**Status:** Draft revision 1 for independent review, 2026-10-03. Not approved, not assessed, not released.
**Position on the path:** unit 6c-1. The Founder split unit 6c on 2026-10-03 into two dependency-ordered units: 6c-1 (this unit) assembles each role's context package; 6c-2 launches the PRODUCER and the VERIFIER with it, from the release record's starting revision, with runtime-injected model assignments. Builds on units 6a and 6b (`main` `14ffb44`).
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## 0. The whole design (plain English)

A PRODUCER or VERIFIER must not reconstruct the project by searching. Before either is launched, this unit assembles its **context package**: one read-only document, built only from existing authoritative records, containing everything that role needs for one work item, and stating how to call the deterministic context API for any further fact. The package is the one specified in `docs/architecture/interface-contracts.md` §6 (context isolation: the VERIFIER gets the work item, the exact candidate and the proof requirements, never the PRODUCER's transcript) and §7 (every worker context states its goal, allowed scope, required evidence, stop condition and escalation condition). Missing or conflicting required facts produce a typed hold that names the field; no package is produced, so nothing can be launched. The unit also gives the PRODUCER's self-review a home: an evidence record in the existing evidence repository, bound to the exact candidate commit, which the VERIFIER's package carries. This unit launches nothing; unit 6c-2 does.

## 1. The package

`WorkContext.assemble(identity, role, candidate=None) -> ContextPackage | ContextHold` (application, `context_assembly/application/work_context.py`), for role PRODUCER or VERIFIER. Every field comes from the named existing record; nothing is inferred.

| Field | Source |
| --- | --- |
| identity, label, role | the `work_item` row; the role asked for |
| goal | the contract's `intent` |
| instructions | the packet bytes at the row's pointer commit (`WorkRecordService.show`), with repository, path and commit |
| contract | the packet's contract block (`work_contract.contract_block`), with its `content_digest` |
| assessment | the row's `assessment_ref` and the matching READY attempt (attempt id, fingerprint of the current pointer) |
| release record | `release_authorization(identity)` on the registry store, and its evidence record (pointer, attempt id, assessment ref, contract digest, baseline, approver, quote) |
| starting revision | the release record's `baseline` |
| allowed scope | the contract's `authorized_scope` and `excluded_scope` |
| dependencies | the contract's `dependencies` |
| design rules | the contract's `fixed_decisions` and `authority_references` |
| stop and escalation conditions | the contract's `stop_escalation_conditions` |
| current attempt and earlier findings | the coordinator state `factory:<identity>` on the registry store, decoded by `FactoryCoordinator.decode`: stage, version, `implement_cycles`, `verify_cycles`, `rejections`, `findings` |
| required verification evidence | the contract's `verification_obligations`, `required_evidence`, `completion_criteria` |
| resources and cleanup | the work item's WIP reservation and the repository reservation (owner and fence, from `recovery_reservations`); the contract's `required_closure_actions` and `candidate_custody_requirements` |
| **VERIFIER only** | the exact candidate (locator and revision) from the coordinator state, which must equal the `candidate` argument; the PRODUCER's self-review evidence for that candidate revision (section 3) |
| context API | the read-only calls a role may make for further facts, as exact command lines with this work item's identity: `alienintent work show <id>`, `alienintent explain <id>` (registry profile), and the deterministic context reconstruction runner (`composition/context_reconstruction.py reconstruct` with the registry store's root, project, profile and manifest arguments) |

The VERIFIER's package never contains the PRODUCER's transcript or invocation output; only the self-review evidence record and the candidate.

## 2. Holds: missing or conflicting facts prevent launch

`assemble` returns a `ContextHold` (`context_assembly/domain/reconstruction.py`, reusing its `HoldReason` values; `MISSING_RECORD` and `DIGEST_MISMATCH` are the main ones) naming the field when any required fact is missing or conflicts:
- no row, retired, no pointer, or the packet's bytes unreadable at the pointer;
- no valid contract block, or its identity is not the work item's;
- no READY assessment of the current pointer;
- no release record; or its evidence's pointer commit, attempt id or contract digest differs from the row's pointer commit, the row's assessment attempt or the contract's digest (`DIGEST_MISMATCH`);
- the coordinator state unreadable;
- for the VERIFIER: no candidate in the coordinator state, a `candidate` argument that differs from it, or no self-review evidence for that candidate revision.
Every check runs; the hold lists every failing field. A hold is retained as evidence like the package.

## 3. The PRODUCER's self-review as evidence

`WorkContext.record_self_review(identity, candidate_revision, text) -> Ref` writes one record to the existing evidence repository (the registry's readiness evidence folder), kind `self-review`, logical id `self-review/<identity>/<candidate revision>`, content `{identity, candidate_revision, text}`, with fixed fields only so the same input gives the same reference. A second call for the same identity and revision with different text is refused (`SELF_REVIEW_EXISTS`); with the same text it returns the existing reference. Unit 6c-2's launch path calls it after the PRODUCER publishes its candidate. Nothing is written to the product repository.

## 4. Retention

Each assembled package and each hold is written to the same evidence repository, kind `work-context`, logical id `work-context/<identity>/<role>/<coordinator version>`, so what each role received is provable afterwards. Assembly is otherwise read-only: it changes no record, reservation, state or GitHub data.

## 5. Exact permitted files

Production: `src/alienintent/context_assembly/application/work_context.py` (new), `src/alienintent/context_assembly/domain/work_context.py` (new: the package and hold values, the field list, the conflict rules), `src/alienintent/composition/work_registry.py` (`WorkRegistry.context`, wiring the existing readers and the evidence repository). Tests: `tests/context_assembly/test_work_context.py` (new), `tests/composition/test_work_registry.py`.

## 6. Acceptance checks (each names the wrong implementation it catches)

1. **What each role receives.** For an authorized, admitted work item, the PRODUCER package holds exactly the fields of section 1 with values equal to their source records, and the instructions byte-equal to `git show <pointer>`; the VERIFIER package additionally holds the exact candidate and its self-review, and holds no PRODUCER transcript or invocation output. Catches a static or partial package and leaked PRODUCER output.
2. **Missing facts prevent launch.** Each missing fact of section 2, one at a time, gives a `ContextHold` naming that field and no package. Catches a package assembled from partial facts.
3. **Conflicting facts prevent launch.** A release record whose evidence names another pointer commit, attempt or contract digest; a VERIFIER `candidate` different from the coordinator's — each `DIGEST_MISMATCH` naming the field. Catches stale or mismatched authorization.
4. **Self-review evidence.** Recording returns a reference bound to the candidate revision; the same text again returns it; different text is `SELF_REVIEW_EXISTS`; a VERIFIER package for a different revision does not find it. Catches unbound or replaceable self-reviews.
5. **Context API.** The package's command lines name this work item and the registry profile, and each one, run against a test registry, answers read-only. Catches a static package with no route to further facts.
6. **Deterministic and retained.** Assembling twice with unchanged records gives byte-identical packages and the same evidence reference; the package or hold is retained; no record, reservation or state changes. Catches non-deterministic or mutating assembly.
7. **Fitness.** The test files above and `check_architecture.py --check all` pass.

## 7. Excluded

Launching workers, delivering the package into a workspace, starting the PRODUCER from the starting revision, capturing the self-review from the PRODUCER, model assignment (all unit 6c-2); changing the context reconstruction service, the release gate, WIP admission or the coordinator; a new store or configuration; changing earlier packets.

## 8. Review record

**Revision 1 (2026-10-03).** First draft, against `main` `14ffb44`, with the Founder's decisions: the per-role context package from the design, assembled from authoritative records; missing or conflicting facts prevent launch; the PRODUCER's self-review stored in the existing evidence repository bound to the exact candidate commit and carried in the VERIFIER's package; the package states how to call the deterministic context API; context assembly and worker launch split into 6c-1 and 6c-2.
