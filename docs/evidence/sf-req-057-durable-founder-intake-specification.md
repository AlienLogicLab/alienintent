# SF-REQ-057 — durable Founder requirement intake specification

Status: accepted SPECIFY contract for PLAN decomposition after independent
read-only review in Factory Director episode
`factory-director-aef6f82e6ee448fb83e454711e8363a0`.
Owner: SF-REQ-057, Issue #147.
Priority: Founder P0. Source: `founder-requirement-intake-durability-live-proof-20260929.json`.
Canonical requirement: `docs/decisions/alienintent-software-factory-plan.md` at
`45891e43d7ff14253fe2c38a0af736b981135214`. Project #1 item:
`PVTI_lADOEcrpC84Bj5i_zg9UCCU`. This document defines acceptance behavior;
it does not release a BIU, assign a Wave, or change the Founder text or priority.

## Required outcome

Every future Founder-authored `FOUNDER_REQUIREMENT` inbox entry remains visible as
an active Director obligation from intake until its exact requirement is durably
recorded in a canonical product artifact and an identified Issue/Project backlog
item, then through that item's normal lifecycle to Project `DONE`. A receipt that
merely acknowledges, defers, or reminds a successor cannot discharge any stage.
The source entry remains immutable and available as provenance. Materialization
is a checkpoint, not completion of the product requirement.

## Intake and identity contract

1. The inbox entry id is the stable source key. Read the complete entry and its
   receipt from the configured inbox paths, with the existing atomic-write and
   fail-closed filename/schema rules. A partial or unreadable source must never
   produce a processed verdict. Retain the exact supplied title, requirement,
   acceptance criteria, priority, and authority; do not infer a Wave, BIU, or
   alternative priority from the Director's judgment.
2. Before a receipt counts as materialized, its `materialization` object names
   the canonical artifact path, a full 40-hex Git revision containing that
   artifact, the positive Issue number, Project number and Project item id.
   Fetch and confirm that revision on the canonical remote branch, then read
   back the artifact at that exact revision, the Issue in the configured
   repository, and exactly that one item on Project #1. Compare the supplied
   requirement and acceptance criteria verbatim with the canonical artifact
   and/or Issue. Preserve the supplied title and authority verbatim in either
   canonical record or an immutable, source-linked provenance record; canonical
   identifiers and display titles may differ when the source title remains
   recoverable. Any paraphrase that narrows or expands Founder intent is a
   mismatch. The Issue/Project must retain the supplied
   priority. A syntactically valid tuple with an unpublished or nonexistent
   revision, missing artifact, wrong Issue or item, duplicate Project item,
   changed content, or changed priority is not proof.
3. Bind a digest of the complete source entry bytes to the receipt and verify
   it after restart. Repeat delivery or restart must reconcile by that source
   key and digest and the recorded canonical identity. Changed bytes under the
   same id are a provenance conflict, not a new requirement or permission to
   overwrite the old one. It must not create another canonical requirement or
   Issue when the original has been materialized. Any identity conflict is an
   explicit hold for Director reconciliation, not a reason to select a new
   identity silently.

## Lifecycle and failure behavior

The Director advances the identified Project item through the existing
`CAPTURE → SPECIFY → PLAN → TASKS` path and, only after normal assessment and
release gates, the worker states to `DONE`. The intake obligation remains active
while the item is at any state short of `DONE`, including after a valid
materialization receipt. Founder priority remains P0 in Project #1 during
selection; no special shortcut overrides dependencies, WIP, Agent Ready, release,
independent verification, or acceptance.

A missing or invalid receipt, Git or GitHub read failure, inconsistent board,
unresolvable provenance, changed priority, or item disappearance must fail closed
with a durable reason for successor control. The host must not turn uncertainty
into `NO_ELIGIBLE_AUTHORIZED_WORK` or an inferred `DONE`. If the canonical target
changes under proper authority, retain the old and new identities and the
authorizing supersession so a restart can follow one unambiguous obligation.

The already materialized #147 entry is a migration case. Its existing receipt
records the artifact, revision, Issue and Project item but predates the
source-byte digest. Its canonical artifact records the exact requirement and
acceptance criteria; the source entry remains the retained exact title and
authority provenance. Before enforcing the stronger receipt rule against this
entry, read back those exact bytes and the existing canonical/Issue/Project
chain, then atomically enrich the receipt with the source digest and the
provenance verification evidence, preserving its prior contents. If any link
fails, leave #147 active and record the mismatch for repair; do not create a
second Issue, mark DONE, or silently grandfather the old receipt. The existing
through-DONE rule keeps this entry active throughout reconciliation.

## Discriminating acceptance evidence

- Negative control: an acknowledgement-only receipt leaves the entry pending.
  An incomplete or fake materialization tuple also leaves it pending.
- Materialization control: exact source content is compared field by field with
  the artifact at a revision read back on the canonical remote branch and the
  Issue; the receipt names the unique Project item id and its matching priority.
  An unpublished revision, mismatched field, duplicate item, or unavailable
  read fails closed.
- Continuity control: with a valid receipt and the Project item at each
  non-`DONE` lifecycle state, the obligation remains active; it clears only
  after authoritative `DONE` readback. Restart between entry creation, partial
  materialization, receipt write, and later lifecycle transitions creates no
  drop or duplicate. Replacing source bytes under the same entry id is detected
  after restart and cannot silently redirect the obligation.
- Priority control: a P0 source remains P0 on the Project item before and after
  materialization. Ordinary priority and dependency selection still applies.
- Evidence distinguishes observed Git revision, Issue, Project status and
  priority from inferred intent. Retain commands, exit status, identities,
  immutable source and receipt bytes, and the independent verdict on the exact
  implementation candidate.

## Current baseline and PLAN boundary

At `origin/main` `af15c6a995f8e19179c081bc44abadffead7ad94`,
`tools/orchestration/factory_director_inputs.py` already leaves a
`FOUNDER_REQUIREMENT` pending for an acknowledgement-only receipt and keeps one
with a structurally valid materialization tuple active until board `DONE`.
`tools/orchestration/test_factory_director_inputs.py` covers those two controls.
The current adapter checks tuple shape and board state; it does not itself
resolve the Git revision/artifact, compare exact source content, or verify the
Issue/Project priority and identity chain for each intake. These are explicit
implementation and proof obligations for PLAN, not current PASS claims.

PLAN must name the owner, bounded implementation slice, deterministic readback
path, failure and recovery behavior, and applicable regression fixture before
TASKS or READY selection. A future worker's candidate must be published with
exact branch/SHA and independently verified under the repository gates.
Nothing here authorizes protected-branch mutation by a BIU worker, live service
operation, or completion of Issue #147 before its normal lifecycle evidence.

General lesson: **DETERMINISTIC_PREFLIGHT** — require resolvable provenance,
unique backlog identity and priority readback before treating materialization as
a valid checkpoint, then retain the obligation until Project `DONE`.

## Independent specification review

A read-only Codex reviewer found four material gaps in the first draft:
canonical remote revision proof, exact Founder content readback, Project item
identity in the receipt, and source-byte continuity across restart. The revised
draft addresses all four. A second rereview identified the existing #147 receipt
as a migration case; the explicit reconciliation paragraph above was then
accepted by a final focused reviewer. These verdicts accept this specification,
not implementation, operational proof, or Issue completion.
