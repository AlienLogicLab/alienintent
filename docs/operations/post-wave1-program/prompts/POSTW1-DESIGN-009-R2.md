# POSTW1-DESIGN-009-R2 — the repair introduced two defects

Fresh Codex GPT-6 Astra. `workspace-write`, solely for
`docs/evidence/wave2-design-contracts.json` and its `.md` companion.

## 1. Where things stand

Your R1 repair worked on three of four findings. A **second** independent fresh Claude session —
different from the one that wrote the original findings, told explicitly not to assume the first
verdict was right — confirmed **DV-1, DV-2 and DV-4 CLOSED**, with your own text quoted as the
evidence. The 3600 s episode age is accepted as DISCLAIMED.

It then found that the repair introduced two new MATERIAL defects, and it verified both against
the actual repository rather than by reading your design. Full verdict:
`docs/operations/post-wave1-program/reports/POSTW1-VERIFY-010-R1-raw.txt`.

This is not a criticism of the repair. Both defects have the same shape: a rule stated correctly
in the abstract, made BLOCKING, without a scope predicate for the world it will actually run in.

## 2. DV2-1 — the edge table forbids imports the repository already contains

`shared_contracts.context_dependency_direction.allowed_edges` now states an explicit permitted
graph, which is what DV-3 asked for. But the verifier confirmed by reading the files that **four
import edges already present in the repository violate it**, and `051-architecture-boundary` is
BLOCKING on "this exact edge table" with no exemption list, no baseline and no scope predicate.

As written, the deterministic check fails on the existing codebase the moment it is implemented.

Resolve by giving the rule a world to run in. Options, and you choose on the evidence:

- state the table as **intended direction plus a recorded baseline** of existing violations, with
  a remediation obligation and an explicit expiry for the baseline;
- or scope the check to new or changed code with the baseline frozen;
- or narrow the table to what the repository can satisfy today and record the stricter direction
  as a future obligation.

A frozen baseline is acceptable; a silent exemption is not. Whatever you choose, the four
existing violations must be named in the design, not discovered at implementation.

**One authority question you must not answer yourself.** The verifier observed that the
architecture authority lists the bounded-context model as unfinished pre-Python work, and
declined to settle whether the designer holds authority to fix the edge table at all. My R1
instruction directed that the graph be stated, and that instruction may have exceeded what a
design contract may decide. If fixing the normative direction would materially change the
approved product boundary, record it as an authority gap for the Founder and state the
**descriptive** graph (what the code does today) rather than a normative one. Do not create a
requirement to settle it.

## 3. DV2-2 — the identifier contract blocks on legitimate identifiers

`identifier_contract.extraction` requires ledgering every whitespace-delimited token containing
`-REQ-`, and `typed_failure` makes every nonconforming token an `IdentifierShapeConflict` that
blocks dependent source compilation.

The verifier tested your pinned regex mechanically across the corpus: **zero** nonconforming
tokens in the factory plan and the decision records that define requirements, but **104 distinct
nonconforming tokens across `docs/` generally, dominated by acceptance IDs** such as
`SF-REQ-053-AC-01`. Those are legitimate identifiers of a different kind. As written, compilation
blocks on them.

Resolve by giving the contract a scope predicate: which documents are in the requirement-identifier
corpus, and which token shapes are recognised as *something else* rather than as malformed
requirement identifiers. An acceptance-criterion identifier is not a broken requirement
identifier, and treating it as one is the same category error DV-4 was raised to prevent, pointed
the other way.

The verifier also noted it could not establish which documents the historical 56-referenced /
53-defined baseline actually pins, because no manifest artifact is named. If your contract relies
on that baseline, name the manifest.

## 4. DV-3 remains PARTIAL

The missing rule now exists and the fixture is written against it. What is unresolved is exactly
DV2-1 — the rule has no scope predicate. Closing DV2-1 closes DV-3.

## 5. Scope

Revise the two design-contract files only. Do not create, amend or weaken any Product
Requirement; recording an authority gap is in scope, closing one is not. Do not modify the
verification artifacts, prior deliverables, Wave 1 evidence, lifecycle state, Project state or
worker contracts. Do not `git commit`, push, or use the network.

## 6. Acceptance

```
python3 tools/evidence/check_design_contracts.py docs/evidence/wave2-design-contracts.json
python3 tools/evidence/check_wave1.py --negative-controls
```

Both passed before and must still pass — and note that the checker passed every version of this
design including the two that contained material defects. It is a floor.

**Dispute anything you believe is wrong** in `DISPUTED`, and leave it unrepaired. Every dispute
raised in this programme so far has been upheld.

## 7. Terminal report — this block only

```
DV2_1_RESOLVED=<baseline | scoped | narrowed | authority_gap, one line>
EXISTING_VIOLATIONS_NAMED=<n, must be 4 unless you dispute the count>
EDGE_TABLE_AUTHORITY=<designer_decided | founder_gap_recorded>
DV2_2_RESOLVED=<how, one line>
ACCEPTANCE_ID_SHAPE=<how it is recognised as not-a-requirement-identifier>
BASELINE_MANIFEST_NAMED=<yes | not_relied_upon>
DV3_STATUS=<closed | still_partial>
NEW_AUTHORITY_GAPS=<n>
REQUIREMENTS_CREATED=<must be 0>
DESIGN_CHECK=PASS|FAIL
WAVE1_CHECK=PASS|FAIL
DISPUTED=<or NONE>
NOTES=<one line, or NONE>
```
