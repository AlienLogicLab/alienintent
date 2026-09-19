# Pre-Python Gate reclassification — A/B/C

Date: 2026-09-19. Status: CLASSIFICATION RESULT under Founder direction of
2026-09-19, following closure of FD-06 and ratification of EOS v1.0.

## Why this exists

The 34-row matrix was built as an inventory of design work. Treating every
unfinished row as an independent blocker conflated two different things: an
architecture decision that has not been made, and a document that has not been
finished. Only the first can force an implementation agent to invent
architecture.

Founder direction: reclassify the matrix as a design and traceability checklist,
and determine whether any genuinely unresolved Founder-level product or
architecture decision remains.

Test applied to every BLOCKED row: **would starting the first Python
implementation BIU require an agent to decide something the Founder has not
decided?**

- **A — already resolved** by Founder-approved architecture or EOS. Cite it.
- **B — lower-level design detail** completable during normal implementation
  under existing architectural constraints. Not a Python-start blocker; retained
  as a checklist item.
- **C — genuinely unresolved Founder-level decision.** Must be surfaced.

Documentation status is not a blocker. A candidate document whose content is a
consolidation of already-approved authority is category A regardless of its own
label.

## Result

**22 rows category A. 9 rows category B. 0 rows category C.**

## Category A — resolved by approved authority (22)

| Row | Authority that resolves it |
| --- | --- |
| G01 Product Intent | Authority governing principles and §§1–8; §8 canonical work model; binding FD-01. The candidate consolidates reset §§2–13, 26–40 and Authority §§2, 6–9, 22–28 — approved material, not new decisions |
| G03 bounded-context model | **Binding FD-02**: Execution Coordination, Invocation Runtime, Context Assembly, Evidence & Learning and Installation are modules within AlienIntent Execution; Control Plane is application orchestration; promotion requires demonstrated language or invariant boundary |
| G07 BIU/domain execution model | Authority §8 canonical work model, §13 BIU and capability authority; FD-01 ownership split; FD-03 capability envelope |
| G08 lifecycle semantics and external mapping | Authority §9 lifecycle semantics and Ubiquitous Language; **binding FD-01** fixes the ownership boundary, projections and non-configurability |
| G09 automatic-release policy | **Binding FD-03**: automatic release defaults ON and is configurable OFF; neither path bypasses readiness checks; release authority is attributable. Authority §10 execution authorization |
| G10 verifier independence / assurance | Authority §5 verifier independence, §11 assurance policy |
| G11 capability/authority incl. live deployment | Authority §13, §14 deployment authority; **binding FD-03** grants powerful authority when a BIU requires it, with fail-closed budgets |
| G12 optional sandbox/container | Authority §12 sandboxing; FD-03 confirms sandboxing remains optional |
| G13 event-ingress and relay adapters | **Binding FD-04**: end-to-end authenticated events, relay is transport not security authority, deployer-controlled gateway where upstream cannot supply the envelope. Authority §3, §18 |
| G15 internal event model / once-only | Authority §17 domain event vocabulary, §18 delivery guarantees; **binding FD-05** inbox/effect-intent/outbox, expected versions, fencing, idempotency |
| G16 concurrency/cancellation/retry | Authority §19 concurrency, §20 cancellation, §21 async/no-polling/retries; FD-05 |
| G19 Context Engineering v1 | Authority §24 Context Engineering — an existing approved model carried forward, not a new decision |
| G20 memory/state/evidence separation | Authority §15 operational state versus durable learning evidence, §25 memory model, §26 evidence retention |
| G23 community-learning contribution | Authority §28: private and local by default, nothing leaves except through configured adapters, participation explicit and configurable, generalized and anonymized only |
| G24 cost/token governance | Authority §22 cost governance; **binding FD-03**: required budgets fail closed, unknown consumption is not zero, unenforceable limits make a provider path ineligible |
| G25 operator Control Plane model | Authority §36 Operator Control Plane, which enumerates the operator operations |
| G26 control-plane presentation adapters | Authority §37: CLI is the minimum required surface; prior web work is recovered rather than reinvented. FD-04 records that web presentation is a candidate interface and not independently approved. The decision is "CLI now, web not approved" |
| G27 adapter versioning/extensibility | Authority §29 adapter contracts, §30 extensibility, §34 upgrade and compatibility |
| G28 configuration and SecretProvider | Authority §31 configuration, §32 secrets |
| G30 observability | Authority §35 observability, §27 private reasoning |
| G33 Node→Python coexistence | **Authority §42**: Node remains bootstrap and operational authority, coexists in the same repository, is frozen except critical fixes; Python implements shared behavioral contracts |
| G34 Python Sovereignty criteria | **Authority §43** states the criterion verbatim and gates Node retirement on it |

## Category B — implementation detail under fixed constraints (9)

Not Python-start blockers. Each is completed during normal implementation, inside
constraints already approved. Retained as checklist items.

| Row | What remains | Constraint it is completed under |
| --- | --- | --- |
| G02 Ubiquitous Language v1 | Write the glossary with definitions, examples, non-examples, ownership | Terms are fixed by Authority §9 and FD-01/FD-02; this is transcription |
| G04 Hexagonal ports specification | Name the concrete port signatures and their success/rejection/unavailable shapes | Hexagonal direction and no-vendor-types-inward are binding principles; Authority §29 |
| G05 Anti-Corruption Layer rules | Write the concrete GitHub and non-GitHub mappings | Explicit ACLs are a binding principle; FD-01 fixes projection semantics |
| G06 Python engineering standard | Typing, error, async, packaging, migration and test conventions | Authority §41 fixes `src/` layout by approved bounded contexts and layer separation |
| G17 provider capability/routing contract | Concrete capability descriptors and probe admission outcomes | Authority §23 provider routing; G18 routing policy already PASS |
| G21 operational-state persistence design | Concrete schema, tables, indices, migrations | Authority §16 SQLite default with PostgreSQL support; FD-05 fixes the consistency model |
| G22 Trajectory / Quality Evidence persistence | Concrete evidence schema, lineage and retention mechanics | Authority §15, §26, §27 |
| G29 installer/bootstrap design | Concrete step sequence, resumability, rollback | Authority §33 packaging and installation, §38 installer/bootstrap UX |
| G32 architecture fitness rules | Python equivalents of the existing checks | Authority §39 architecture fitness; the Node checks exist and are the reference |

## Category C — genuinely unresolved Founder decisions

**None.**

Every architectural question an implementation agent would hit at the start of
Python work has a Founder-approved answer in the Architecture Authority, in
binding FD-01 through FD-05, or in EOS v1.0. FD-06 is closed.

## Already PASS (3)

G14 no-polling/async (Authority §21), G18 cheapest-capable/local-first routing
(Authority §23), G31 EOS inheritance/contribution (EOS v1.0, FD-06, EOS
`REVIEW-000005`).

## Matrix disposition

The 34-row matrix is preserved unchanged as a design and traceability backlog. It
is no longer a set of 34 independent blockers. Rows retain their acceptance
criteria so completed design work can still be checked against them.

No acceptance criterion was invented, weakened or removed to reach this result,
and no row was reclassified by changing what it requires.
