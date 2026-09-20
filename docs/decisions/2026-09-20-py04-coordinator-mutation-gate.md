# PY-04 coordinator mutation gate — SWF-26 (temporary)

Date: 2026-09-20. Status: **Founder decision — binding, temporary PY-04 bootstrap procedure**.
Source: direct Founder instruction after the PY-04 candidate `1b372c2a` reported one mutation while five of the verifier's twenty-three survived.

## Procedure

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
