# Wave 1 execution decisions — SWF-12 through SWF-15

Date: 2026-09-20. Status: **Founder decision — binding**.
Source: direct Founder instruction resolving the PY-04 custody question and authorizing Wave 1 execution.
Predecessors: [SWF-01–07](2026-09-19-software-factory-wave1-founder-decisions.md), [SWF-08–11](2026-09-20-wave1-plan-approval-d1-d2.md).

## SWF-12 — PY-04 candidate custody (Option A approved)

For PY-04's offline scripted-worker proof, a durable content-addressed local artifact may satisfy SF-REQ-007 candidate custody.

**This is not an exemption from candidate custody.** The invariant stands: before VERIFY, the exact candidate must be durably identifiable and retrievable by a fresh independent verifier.

For PY-04 specifically, all of the following are required:

1. candidate contents are immutable once identified;
2. the candidate has a cryptographic content digest;
3. candidate identity contains or resolves unambiguously to that digest;
4. the artifact persists independently of the PRODUCER invocation;
5. a fresh independent process can retrieve it;
6. the fresh process recomputes the digest and proves exact identity;
7. VERIFY is inadmissible until that independent read-back succeeds;
8. any mutation produces a new candidate identity;
9. candidate/evidence retention follows the normal evidence policy.

**Candidate custody is not semantically tied to Git.** The architecture must be able to represent `CandidateRef` variants such as local artifact, Git commit, archive, or other durable candidate forms. PY-06 remains responsible for production/source-control candidate custody.

## SWF-13 — PY-09 doctor semantics confirmed

The fail-closed interpretation is confirmed. For Wave 1:

- every doctor prerequisite explicitly listed as required is hard-required;
- FAIL blocks autonomous start;
- UNAVAILABLE also blocks autonomous start;
- FAIL and UNAVAILABLE remain distinct outcomes;
- there is no degraded-autonomy mode in Wave 1.

The documented exit-code distinctions are preserved. No further Founder decision is required on this point.

## SWF-14 — Cognitive-intelligence strategic record

This work must not delay Wave 1. The intended durable split is:

- `docs/research/…prior-art…` — research/evidence;
- `docs/strategy/alienintent-software-cognitive-intelligence-factory.md` — strategic interpretation.
  (**Path amendment, Founder-approved 2026-09-20.** SWF-14 originally named
  `docs/decisions/alienintent-software-cognitive-intelligence-factory-record.md`. Documentation normalization
  relocated the strategic interpretation to the canonical strategy location, because `docs/decisions/` holds
  canonical decision records only. The original path is retained here as historical provenance and all inbound
  references resolve to the normalized path. This amends the path and taxonomy only — not the substance,
  authority or intent of SWF-14, and it is not a new product or architecture decision.)

The strategic record is committed only once it is verified to be the research-backed revision rather than the earlier provisional version. If it is not, it stays uncommitted and the discrepancy is reported rather than reconciled during execution.

**No implementation BIUs or SF-REQs are created from this strategic record as part of Wave 1.**

## SWF-15 — Temporary manual release of PY-02

PY-02 is released from READY into IMPLEMENT by a manual Project transition.

This is a **temporary Node-bootstrap release action**, because the frozen Node bootstrap does not implement automatic release. It is **not** the target AlienIntent operating model, in which a READY BIU satisfying release policy proceeds through an attributable policy release (AA §10, FD-03).

Once PY-02 enters IMPLEMENT, the existing lifecycle executes it:

> IMPLEMENT → PRODUCER → VERIFY → VERIFIER → repair if legitimately rejected → ACCEPT → closure → DONE

The Node AlienIntent bootstrap launches the PRODUCER. The coordinator session does not implement PY-02 and does not hand it to a provider CLI directly. Routine implementation defects and verifier-directed repairs stay inside the factory loop; a genuine Founder/product/architecture authority decision stops the loop and is surfaced.

After PY-02 reaches DONE, the next dependency-eligible BIU advances toward READY and the Wave 1 sequence continues under the existing plan.
