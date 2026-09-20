# PY-04 offline candidate custody — SWF-22

Date: 2026-09-20. Status: **Founder decision — binding**.
Source: direct Founder decision answering the PY-04 authority exception ([issue #52](https://github.com/AlienLogicLab/alienintent/issues/52)).
Refines: [SWF-12](2026-09-20-wave1-execution-decisions.md).

## The question

PY-04's runtime cannot make a local artifact immutable against the producing identity: `chattr +i` returns `Operation not permitted`. Digest verification detects later tampering but does not by itself satisfy SWF-12 condition 1 (contents immutable once identified) or condition 9 (retention).

## Clarification of SWF-12 — semantic, not filesystem, immutability

"Immutable once identified" does **not** require Linux `chattr +i`, filesystem immutable flags, or a new durable-storage service.

The invariant is **semantic / content-addressed immutability**: once `CandidateRef` digest **D** has been established, the bytes verified under D must remain exactly those bytes. Any changed bytes constitute a **different candidate identity**.

## Decision — custody transfer to an independently retrieved verifier copy

Immutability is achieved by **custody transfer**, not by filesystem flags.

At independent read-back, the separate process **copies** the artifact into a verifier-owned evidence area, recomputes the digest **on that copy**, and requires it to equal the declared digest. The candidate — and therefore the verdict — binds to that copy.

The producer may still overwrite its own file afterwards; that file is no longer the candidate. Any such mutation yields a different digest and therefore a different candidate identity, which SWF-12 condition 8 already requires.

### Required sequence for PY-04

1. PRODUCER creates the candidate artifact.
2. PRODUCER computes and records its cryptographic digest **D**.
3. `CandidateRef` identifies that candidate by **D**.
4. Before VERIFY, a fresh independent verifier-side process retrieves/copies the artifact into verifier custody.
5. That process recomputes the digest.
6. VERIFY is admissible only if the recomputed digest equals **D**.
7. The verifier operates on the independently retrieved custody copy, not on the producer's mutable working artifact.
8. Subsequent mutation of the producer-side artifact does not mutate Candidate D; it creates different content and therefore a different `CandidateRef`.
9. The verifier custody artifact and evidence are retained according to the required evidence-retention policy.

**Prohibited:** do not introduce a new artifact service, database, daemon, or separately-owned storage subsystem for PY-04 solely to obtain filesystem immutability. "Verifier custody" means an ordinary directory the verifier-side process owns within existing evidence handling — not new infrastructure.

All nine SWF-12 conditions remain in force, satisfied as follows:

| Condition | How it is satisfied |
|---|---|
| 1 immutable once identified | **semantic**: the bytes verified under D are the independently retrieved custody copy; changed bytes are a different identity, not a mutated candidate |
| 2 cryptographic digest | unchanged |
| 3 identity resolves to the digest | unchanged |
| 4 persists independently of the PRODUCER invocation | the copy outlives the invocation |
| 5 fresh independent process retrieves | that process performs the copy |
| 6 recompute and prove identity | recomputed **on the copy** |
| 7 VERIFY inadmissible until read-back succeeds | unchanged |
| 8 mutation yields a new identity | unchanged; the producer's later writes are a different identity |
| 9 retention per evidence policy | the retained artifact is the verifier-owned copy |

No new privileged capability is granted, no new storage subsystem is built, and no SWF-12 condition is weakened or waived. `chattr +i` is neither required nor to be attempted. Custody remains provider-neutral and not semantically tied to Git; this is the local-artifact `CandidateRef` variant. PY-06 remains responsible for production/source-control custody.

## Not affected

The VERIFIER's separate blocking finding stands as ordinary contracted work: scope item 5 requires the scripted worker to deliver all five declared outcomes (success, failure, rework-then-success, timeout, authority block), and a single failure must not abandon independent eligible work.
