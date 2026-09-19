# AlienIntent EOS conformance manifest

Date: 2026-09-19. Status: CONFORMANCE RECORD against a named EOS version.

Conformance baseline: **EOS v1.0**, ratified 2026-09-19 by
`DR-000007-establish-all-eos-version-scheme-and-ratify-v1.md` in repository
`AlienLogicLab/P000-all-eos`. Version contents are authoritatively stated in
`docs/00-foundation/all_eos_versions.md`; this manifest cites that version, not a
bare commit.

AlienIntent project identity: **P007**, registered in
`docs/12-portfolio/current_project_registry.md` (Accepted, in EOS v1.0).
Repository `AlienLogicLab/alienintent`, public by Founder decision and registered
in `ADR-0007-public-project-repositories-as-a-bounded-exception.md`.

BIU: [PG-19](../../work-units/pre-python-gate/PG-19.md). Binding decision:
[Founder decisions FD-02 through FD-06](../../decisions/2026-09-19-pre-python-gate-founder-decisions-fd02-fd06.md)
and the Founder FD-06 normalization decision of 2026-09-19.

## Inherited authority

| EOS v1.0 artifact | Status | AlienIntent requirement / artifact | Translation or deviation |
| --- | --- | --- | --- |
| `CONSTITUTION.md` | Accepted v1.0 | Epistemic integrity, architecture before implementation, knowledge preservation across the gate | None |
| `docs/00-foundation/ontology.md` v0.2 | Accepted v0.2 | Work Order / Claim / Evidence / Decision distinctions preserved in [domain-model.md](domain-model.md) | Translation: EOS `Work Order` is not AlienIntent `BIU`; see below |
| `ADR-0004` domain language translation | Accepted | Project domain language preserved; this manifest is the translation artifact ADR-0004 requires | None |
| `docs/06-knowledge/knowledge_lifecycle.md` | Accepted v0.1 | Provenance, supporting and contradicting evidence, owner, qualitative confidence, review cadence and supersession traceable in [persistence-and-evidence.md](persistence-and-evidence.md) | None |
| `docs/11-capabilities/evidence_chains.md` | Accepted v0.1 | Quality Evidence and Engineering Trajectory must support forward and backward traversal | None |
| `docs/05-artifacts/record_directories_and_numbering.md` | Accepted v0.1 | Status Rules applied to every EOS citation in this gate | None |
| `ADR-0001` + `ADR-0007` | Accepted | Repository custody | **Registered deviation:** `alienintent` is public; ADR-0007 register entry covers it |
| `docs/15-playbook/engineering_principles.md` — Agentic Development Discipline | Adopted policy, `PB-DIR-0001` | Binds AlienIntent engineering; conformance assessed below | Two translation entries |
| `docs/15-playbook/playbook_registry.md` | Accepted v1.0 | Candidate entries are not cited as authority | None |
| `docs/15-playbook/organizational_learning.md` | Accepted v1.0 | Provenance for the discipline; contribution path target | None |
| `cir-000001` … `cir-000008` | Accepted | Cited as organizational knowledge within stated scope | None |

## Excluded from EOS v1.0 and therefore not cited as authority

`cir-000009` … `cir-000019` (Proposed); the seven playbook placeholders including
Decision Principles (Draft); `deployment_discipline.md` (Draft).

**Withdrawn citation.** The G31 row previously cited "engineering discipline" as
supporting evidence. `REVIEW-000004` found `deployment_discipline.md` is not
required as authority for AlienIntent — its subject is manual-versus-CI
deployment gates, not AlienIntent's per-BIU capability and authority model under
FD-03. The citation is withdrawn. No AlienIntent contract depends on it.

**Provenance citation retained.** Agentic Development Discipline rule 1 cites
`cir-000010`, which is Proposed and excluded. EOS Status Rules permit a Proposed
record to guide work without being authoritative, so the citation stands as
historical origin, not as inherited authority.

## Conformance against the Agentic Development Discipline

The ten rules are Adopted policy in EOS v1.0 and bind AlienIntent. Assessed
against AlienIntent's binding Authority and resolved FD-01 through FD-05:

| Rule | AlienIntent position | Result |
| --- | --- | --- |
| 1 Preserve known-good capability before change | Node bootstrap preserved unchanged throughout the gate; Python is not authorized until the gate passes; [conformance-and-sovereignty.md](conformance-and-sovereignty.md) keeps Node authoritative | **Conforms** |
| 2 One active vertical by default | Authority §19: "One active mutating worker per repository is a reasonable starting convention unless safe parallelism is proven"; bounded concurrency globally, per project, per repository | **Conforms** |
| 3 Protect the active vertical | Gate scope held to documentation; no contract widened without a Founder decision | **Conforms** |
| 4 Classify discoveries explicitly | Gate findings carried as numbered items with explicit dispositions rather than silent scope growth | **Conforms** |
| 5 Resolve dependencies before building | Pre-Python Gate exists precisely to resolve contracts before implementation | **Conforms** |
| 6 Require executable proof before declaring readiness | Translation required; see below | **Conforms with translation** |
| 7 Review the delta, not accepted history | PG-17, PG-18 and PG-19 each reviewed their delta; the 159-artifact inventory is not re-derived | **Conforms** |
| 8 Separate outcome from apparatus validity | Gate rows stay BLOCKED on missing adoption, not on failed attempts; assessment receipts retained unmodified | **Conforms** |
| 9 Make accepted progress monotonic | Engineering Trajectory and Quality Evidence (G22) carry accepted capability lineage; FD-05 expected-version writes prevent silent regression | **Conforms** |
| 10 Treat scope change as an authority decision | FD-01 fixes the authority boundary; Authority §45 requires Founder escalation; this gate raised FD-01 … FD-06 rather than deciding them | **Conforms** |

No rule conflicts with AlienIntent's binding Authority or with FD-01 through
FD-05.

## Translation entries required by ADR-0004

**1. `readiness` / `READY`.** Rule 6 requires "the real intended happy path
through the actual components" before declaring readiness. That is *capability*
readiness. AlienIntent's `READY` is *work-unit* readiness — an Agent-Ready
disposition that a BIU is well posed for execution, which FD-03 explicitly says
"is never an unrestricted worker launch." The two are different predicates that
share a word. AlienIntent must not cite its `READY` as satisfying rule 6, and
rule 6 must not be read as forbidding automatic release under FD-03.

**2. `vertical` / `BIU`.** Rule 2's "end-to-end vertical" is a unit of agent work
in progress. AlienIntent's BIU is a released, authorized unit of execution. Rule
2 constrains how many verticals an agent drives at once; it does not cap
AlienIntent's runtime concurrency, which Authority §19 governs. Bounded
concurrent BIU execution does not violate rule 2.

Per ADR-0004 these are translation entries, not deviations: the EOS meaning and
the project meaning both stand, mapped rather than merged.

## Contribution path

An AlienIntent finding links exact source, commit and verification with its
limits, creates a local candidate lesson or CIR proposal, receives engineering
and governance review, and is submitted to EOS through an explicit proposal or
pull request. Acceptance records the EOS version and decision and updates this
manifest. This gate submitted no contribution; the EOS changes it made were
performed directly under `WO-000013` by Founder authority, not through the
project contribution path.

## Version-change discipline

This manifest names `EOS v1.0`. A new EOS version triggers an explicit delta
review before any conformance claim changes. A new EOS version does not silently
overwrite AlienIntent product semantics or approved deployment behaviour. Items
carried into EOS v1.1 that AlienIntent should re-examine: `deployment_discipline.md`
review, and Chief Architect review of `cir-000009` … `cir-000019`.
