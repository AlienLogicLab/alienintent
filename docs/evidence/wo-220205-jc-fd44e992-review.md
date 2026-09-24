# WO-220205 independent JC repair verification

Verdict: **ACCEPT** for producer candidate `6518d1ef09fc99e8abccf1c6234106f860fce7e6`,
branch `b-disp/440039d5-1752-4c7a-940c-56672fd74445`.
Invocation: `AlienLogicLab/alienintent#97:VERIFIER:fd44e992-bd5a-4def-a156-f54680f913f5`.

## Authority and custody

Reconstructed independently from Issue #97 body, release 5814787888, prior JC rejection
5815345624, Director continuation 5815964458 and replacement submission 5816153182.
The pinned WO-220205 contract, packet, allocation, verified SF-REQ-051 design and
FX-U5 Revision 2 govern this bounded local U5 review. Identity: JC,
jc-github@factorychecks.com, GitHub jc-worker. Assigned runtime-managed worktree
started clean at `1f8648b8cc3d9aa707588ab7698ef4f7f368fb4c`; fetched and fast-forwarded
its own branch to the exact candidate. Remote candidate readback matched.

Admission baseline `7be12188edf632710fe842d95fc70b444e2ed279`, accepted U2
`d0eacfb6dd8626b07ff1d99e9c633294f13d9de4`, accepted U4
`c8ed707efdb0cd70294bfdb6814ec9f9eb71216d` and retained repair `98d60b0` are ancestors.
Read U2/U4 ACCEPT comments 5808965906 / 5814553759 and retrieved independent
receipts `4f03da9a2e6107ad1862f5e97ba80f33cf616325` /
`42d521913e7daa7a5c450595fe3553082b5df22d`. All 13 pinned input hashes match.
Original producer, replacement producer and prior JC manifests verify 146, 163 and
154 entries respectively. Prior evidence, predicate mapping and architecture checker
are unchanged. No prior proof is superseded.

## Observation and findings

**R1 closed.** The service checks retained decisions for the reviewer invocation and
exact mechanical report before allowing renewed applicability. The prior JC oracle
is byte-identical to `4dab2234ca3a139d1688bb44a1b05d01450434ac` and passes 3/3 on
this candidate. Replacing only the service with rejected `c9a8699` bytes in a
disposable copy produces exactly one failure in three tests: historical replay is
admitted and restores readiness. This establishes discrimination of the original bug.

An additional independent probe reopens SQLite and the evidence repository after
invalidation. Invalidation persists; changing the historical review's authority text
does not bypass invocation freshness; a new independent review admits; the original
verdict remains retrievable. The probe exits 0. Its output is explicitly retained as
a terminal observation transcription. Duplicate import in unchanged VERIFIED state
remains idempotent. Design revision round trips refuse historical reuse.

Fresh validation on the exact producer candidate:

- Python suite: exit 0, **635 passed in 72.02s**.
- Architecture fitness: exit 0, PASS. Node required checks: exit 0.
- Candidate diff whitespace check: exit 0.
- FX-U5 with this verifier invocation: exit 0, **25/25 QUALIFIED_KILL**;
  75 phase logs independently hash-verified, intact/fault/restored exits and mutation
  application counts 0/1/0. Disconnected domain control stays green. Proof-order
  diagnostics are empty. All 76 immutable objects and 76 raw control logs retained.

Commands, observations, input hashes and custody manifest are in
`wo-220205-jc-fd44e992/`. Operational SQLite state is excluded from publication.

## Independent judgment and acceptance

JUDGMENT by JC under the independent verifier allocation for
`SF-REQ-051/SF-REQ-051-AC-04/premise-review-judgment`: inspected the pinned contract,
approved design, predicate mapping, SWF-34, U3 capability mapping, implementation,
tests and fresh observations. Runnable bindings faithfully implement the bounded
probes, including the repaired freshness requirement. The impossible credential-denial
criterion is rejected despite its otherwise complete checklist: the pinned evidence
establishes organization-wide Project credentials, with application targeting and
outside-state readback as distinct controls. This is a judgment on the retained
fixture evidence, not a new claim about current platform capability or live operation.

The open helper-naming choice is genuinely local under its explicit exclusions of
predicate, identity and persistence changes. The persistence-inapplicability reason
is proportional to the hypothetical read-only change; it is not an exemption for
the admission service's own persisted history. Mechanical field checks alone do not
settle these semantic judgments.

AC-01: complete fields and explained inapplicability; missing fields/reasons hold.
AC-02: material undecided choices and blocking findings hold; bounded local choice
remains open. AC-04: impossible premise rejected with external retained capability
evidence. AC-05: revisions invalidate readiness, fresh review is required and history
persists. AC-06: absent design/review/authority refuses readiness without Project
lifecycle mutation. Both BLOCKING obligations are satisfied by discriminating controls.
No remaining blocking finding was identified. AC-03 is outside the U5 extent.

## Limits and disposition

Directional authority remains `ARCHITECTURE_AUTHORITY_HOLD`; observed edges are not
policy. Conditional withdrawn-R1 fixtures are not claimed. SF-REQ-013/015 consumers
remain sibling-node wiring; this review accepts the U5 gate only. Harness plan-root
and helper metadata retain producer labels; phase observations/report carry this
invocation and this receipt supplies JC's independent judgment. Tokens/cost UNKNOWN.
Local proof only; no live operation or other-repository mutation.

Only verifier evidence is added. Own branch
`b-disp/e8b5c608-cc5e-41cf-bc90-2532f9b42951` is retained under runtime BIU custody,
pending Factory Director SWF-19 merge-at-closure of the exact accepted producer SHA
and disposition of verifier evidence. No PR, baseline push, merge or Project
transition is performed by this verifier.
