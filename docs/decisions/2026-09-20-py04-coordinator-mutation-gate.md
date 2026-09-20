# PY-04 coordinator mutation gate — SWF-26 (temporary)

Date: 2026-09-20. Status: **EXPIRED 2026-09-20** — retained as historical evidence only, not a standing gate.
Originally: Founder decision, binding, temporary PY-04 bootstrap procedure.
Source: direct Founder instruction after the PY-04 candidate `1b372c2a` reported one mutation while five of the verifier's twenty-three survived.

## Expiry (Founder decision, 2026-09-20)

This procedure **expired when PY-04 reached DONE** at 12:27:21Z. It is retained as historical evidence and is **not** applied to PY-05 or any later BIU.

> A successful bootstrap exception must not silently become architecture.

Generalizing a mutation gate into standing verification belongs to **SF-REQ-050** (deterministic failure-class promotion, [SWF-24](2026-09-20-deterministic-failure-class-promotion.md)), through the normal requirement, design and BIU path — not by extending a temporary exception. The coordinator does not run the battery as a gate on subsequent BIUs.

**Evidence it produced:** on candidate `1b372c2a` the battery reproduced the verifier's five survivors and found a sixth (M1) the verifier's variant could not reach; on the accepted candidate `03896f62` it reported 23 killed / 0 survived / 0 not applied, independently agreeing with the verifier's own red-green check. That evidence is the input to SF-REQ-050, not a licence to keep the gate.

## Procedure (as executed, historical)

For the next PY-04 producer candidate, the producer's claim that mutation proof is complete is **not** relied upon. After the candidate is published, the coordinator independently executes the verifier-defined 23-mutation battery against **that exact candidate**, before another independent VERIFY cycle is allowed to stand.

- **Any mutation survives** → the candidate returns to IMPLEMENT with **only the surviving mutations** named.
- **All 23 killed and the normal required checks pass** → the existing Node workflow proceeds to independent VERIFY untouched.

## Boundaries

This is a temporary bootstrap procedure for PY-04 only. It does **not** modify Node/B-DISP behaviour, product requirements, lifecycle semantics, or the accepted candidate. It grants the coordinator no authority to implement, to launch workers, or to accept a candidate. Independent VERIFY remains the acceptance authority.

The procedure expires when PY-04 completes, or earlier if the equivalent check is promoted into VERIFY under SF-REQ-050.

## Battery provenance and validation

The battery is the verifier's enumerated 23 mutations (issue #52, REJECT of `1b372c2a`), implemented as deterministic source patches with a `NOT_APPLIED` outcome when a pattern no longer matches — an unapplied mutation is never counted as a kill.

Validated against candidate `1b372c2a`, where the verifier had independently reported 18 killed / 5 survived. The coordinator battery reproduced **exactly those five** (M4, M10, M14, M20, M22) and additionally found **M1 surviving**, because the AC 11 test seeds a single dependency-blocked item, so the loop body never executes and an in-loop re-import is never reached. The battery is therefore at least as strict as the verifier's.

## Relationship to existing authority

Implements the SWF-24 principle — evidence is insufficient unless a meaningful violation causes the check to fail — as a temporary manual gate, pending the SF-REQ-050 promotion capability that would make it a permanent deterministic VERIFY check. Evidence preservation remains governed by SWF-23 §2.
