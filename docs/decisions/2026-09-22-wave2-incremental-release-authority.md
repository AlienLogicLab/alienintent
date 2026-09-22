# Wave 2 incremental release authority — SWF-35

Date: 2026-09-22. Status: **Founder decision — binding, standing**.
Source: direct Founder instruction, recorded verbatim by the resident bootstrap coordinator (local Program Director).
Predecessor: [SWF-21](2026-09-20-wave1-release-coordinator.md) (temporary, Wave 1-only release coordinator policy). This record is SWF-21's **Wave 2 successor**: SWF-21's nine release conditions and the 2026-09-21 release-admission preconditions remain in force unchanged; this grant supplies the Founder release authority that SWF-21's Wave 1 scope did not carry over (FD-01 §3; W2-P01).

## Founder decision (verbatim)

> **Founder authorizes READY → IMPLEMENT release for Wave 2 BIUs without a separate per-BIU Founder approval when all of the following are true:**
>
> * the BIU is part of the already-approved Wave 2 plan;
> * the exact current BIU/baseline has a **native Agent Ready `READY`** disposition;
> * the execution packet is fully bound;
> * dependencies are satisfied;
> * no unresolved architecture/product/security/budget authority remains;
> * release-admission checks pass;
> * candidate custody/evidence requirements are active;
> * the release does not introduce new scope or reinterpret approved intent.
>
> This immediately authorizes **WO-220101 READY → IMPLEMENT**.
>
> The grant is **not** blanket authority to release anything merely labeled Wave 2. It is a standing grant for BIUs that satisfy those conditions.
>
> The coordinator should record this as the Wave 2 successor to the Wave-1-only release grant, then release WO-220101 and continue the factory loop autonomously.

## How the conditions are established (binding reading)

| Condition | Evidence required before the transition |
|---|---|
| part of the approved Wave 2 plan | the BIU is a compiled candidate in `docs/evidence/wave2-candidate-bius.json` with a plan node in `wave2-dependency-dag.json` |
| native Agent Ready `READY` at the exact current BIU/baseline | a retained assessment record under `docs/evidence/wave2-readiness-assessments/` produced by the Agent Ready product (producer identity from the installed package, never inferred from shape — `tools/evidence/check_assessment_producer.py`); input fingerprint equal to the submitted work-unit document; any material change to the contract, baseline or authority requires a fresh assessment, never an edit |
| execution packet fully bound | `docs/evidence/wave2-execution-packets/<BIU>.allocation.json` and `<BIU>.packet.json` with limits stated as actually enforced (UNKNOWN never silently zero) |
| dependencies satisfied | every `dependencies` entry of the candidate is DONE with accepted evidence |
| no unresolved authority | candidate `authority_gap_refs` and `authority_gate_refs` empty, or each resolved by a dated record |
| release-admission checks pass | SWF-21's nine conditions and the six 2026-09-21 preconditions, checked mechanically before the transition; a failed check is a refusal |
| custody/evidence active | candidate custody policy and evidence obligations carried in the packet; verifier retrieves the exact candidate SHA in a fresh worktree |
| no new scope | the released text is the assessed text (same input fingerprint) |

## What this does not change

- Readiness is Agent Ready's; release is AlienIntent's; neither is the other (SF-REQ-015 amendment, UL v0.1).
- The transition remains the temporary coordinator duty SWF-21/SWF-15 describe until canonical release (SF-REQ-002 admission amendment) replaces it; replacement, not elapsed time, retires it.
- No worker is launched by the coordinator; the retained bootstrap receives the Project event and launches the PRODUCER.
- Nothing here retires a bootstrap mechanism, changes provider configuration, or authorizes work outside the released BIU's extent.

## First application

WO-220101 — Reusable isolated proof substrate (Project #1 issue #69): released under this grant on 2026-09-22; release record `docs/work-units/wave2/WO-220101.release.md`.
