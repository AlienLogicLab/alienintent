# Canonicalization report — Founder Architecture Decisions and Ubiquitous Language v0.1

Date: 2026-09-22. Author: resident Claude bootstrap coordinator. Source decision document:
`docs/decisions/alienintent-agent-ready-founder-decisions-and-ubiquitous-language-v0.1.md`
(Founder-approved). This is an architecture/authority reconciliation; no implementation, no
Wave 2 execution, no lifecycle or Project state change.

Strategy applied to every decision: find the existing canonical owner → amend it when
semantically correct → cross-reference from consumers → create a new requirement only if no
existing one genuinely owns the responsibility → never invent Priority or Wave → preserve
provenance → mark unresolved follow-up explicitly. **One invariant, one owner.** The Founder
document was not copied wholesale anywhere.

## 1. The finding that reframed the terminology repair

Wave 1 and the post-Wave-1 programme **never invoked the Agent Ready product.** Readiness was
assessed by an *AlienIntent bootstrap assessor*: a coordinator-run prompt (`codex exec` on
`codex-cli 0.155.1`, later `claude -p` on failover) fed a `PY-NN.request.md`, returning the Agent
Ready contract *shape* with AlienIntent-invented dispositions
(`READY / BLOCKED / NEEDS_CLARIFICATION / SPLIT_RECOMMENDED`) and a `provider_evidence` block the
Agent Ready schema rejects (`provider` must be `codex`; Claude provenance fields are not in the
schema). Evidence: `docs/evidence/2026-09-21-agent-ready-provider-failover.md`,
`docs/work-units/python/PY-10.assessment.json`, and Agent Ready's own supported-version list
(exactly `codex-cli 0.153.4`).

Consequences: `BLOCKED` was never a mislabelled Agent Ready `HOLD`; it was a separate vocabulary.
Phase 4's finding G1 ("no Agent-Ready implementation in this repository") was correct and is now
resolved by pointing at the right owner. All historical assessments are preserved verbatim and
labelled as bootstrap-assessor evidence.

## 2. Every Founder decision processed

| # | Decision | Existing canonical owner found | Action taken | Cross-references |
|---|---|---|---|---|
| §1 | Agent Ready has no `BLOCKED`; disposition ≠ lifecycle state; never project lifecycle vocabulary back | SF-REQ-015 (Agent-Ready remains readiness authority) | **Amended SF-REQ-015**: exact `READY/CLARIFY/SPLIT/HOLD`; process semantics; execution failure ≠ disposition; historical note | UL v0.1 §1; Architecture Authority (AA) A1; new checker |
| §2 | Agent Ready independent product/bounded context; consume via public contract only | canonical-architecture non-responsibility "second copy of Agent Ready readiness logic"; SF-REQ-015 | **AA amendment A1** states the boundary; SF-REQ-015 owns the *integration* via `ReadinessAssessment` port; no AlienIntent requirement claims Agent Ready internals | hexagonal-contracts port row; Agent Ready UL |
| §3 | Historical assessments immutable; preserve provenance fields; read-time projection | AA §15/§26 (durable, immutable evidence); FD-02 Evidence and Learning module | **Amended SF-REQ-029**: Readiness Assessment retained as immutable observation with the listed fields; correction preserves original + provenance. Retention owner ≠ semantics owner | UL "Readiness Assessment"; AA A7 |
| §4 | Feedback contract (Agent Ready) / attributable outcome feedback (consumer); timing unsettled | SF-REQ-030 Quality Evidence (downstream outcomes); SF-REQ-032 governed learning | **Amended SF-REQ-030**: Assessment Feedback derived from Quality Evidence via `AssessmentFeedback` port; never success/failure; **maturity point deliberately unsettled** — Wave 2 learning objective | AA A8; hexagonal-contracts row; Agent Ready UL (roadmap) |
| §5 | Agent Ready owns split judgment; AlienIntent owns split/replan mutation | SF-REQ-013 (Phase 5 recommended amendment; SPLIT-G1) | **Amended SF-REQ-013** to own the split transaction with conservation, deterministic dependency rewriting, lineage, invalidation, integration parent, re-assessment; Phase 5 design named as candidate design; SWF-33 as precedent | UL "Split Transaction"; closes 005A and 007A-R06 |
| §6 | Requirements / Planning bounded context; modular monolith, not microservice | FD-01/FD-02 (two contexts + five modules); AA §41/§44 | **AA amendment A2** establishes the context; **FD-01 refinement** reconciles lane ownership; **FD-02 refinement** records it and defers the `context_assembly` question to Design Contract | UL §1 invariant |
| §7 | Hexagonal integration: `ReadinessAssessmentPort`, CLI/MCP adapters | hexagonal-contracts (candidate ports) | **Port row added**: `ReadinessAssessment`; domain never knows location/subprocess/transport | SF-REQ-015 amendment |
| §8 | Split/replan flow, initial and replanning | SF-REQ-013/015 | Covered by the §5 and §1 amendments; flow recorded in UL §2 CLARIFY/SPLIT/HOLD responses | — |
| §9 | N requirement sources; provider-neutral core; provenance retained | SF-REQ-011 Requirements IR; SF-REQ-005 Work Management; AA §8 | **Amended SF-REQ-011**: `RequirementSource` port distinct from `WorkManagement`; provenance fields; non-identities (Epic ≠ Requirement…). **AA amendment A3** (binding). **Port row added** | UL "Requirement Source", "Source Record"; collision table |
| §10 | Public-use constraint: no FactoryChecks / self-hosting / single-provider assumptions | AA §Governing principles "solve for N" | Folded into AA A3; UL "Project" defines Projects as instances. Checked: no core artifact written here names FactoryChecks except AA §1's existing example | — |
| §11 | Cognizant Allocator; local-model-first | SF-REQ-026 cheapest-capable routing (nearest owner); SF-REQ-002 scheduling kept distinct; plan "Scheduling / Factory Coordinator" | **Amended SF-REQ-026** to own Allocation (attributable decision, inputs, limits, authority, escalation); local-model-first for allocation *cognition*; deterministic trivial cases. **AA A4**. Init/doctor hooks in SF-REQ-037/038 | UL "Allocation", "Allocator", "Execution Packet"; resolves the concept half of 013A |
| §12 | Deterministic Test Worker replaces "fake-agent" | SF-REQ-039 | **Renamed and reframed in place**; former title and text retained in the record; identity, priority, Wave 2 assignment unchanged | UL; AA A9; checker `sf_req_039_identity` |
| §13 | Implementation workers do not invent architecture policy | AA §45 Founder escalation; SWF-25 design-authority boundary; SF-REQ-035 Decision Inbox | **AA amendment A5**: *Architecture Decision Required* is a kind of `HumanDecisionRequired`; no second mechanism | UL |
| §14 | Persistent monitoring outside model sessions | SWF-27 §Bootstrap evidence (already states it); SF-REQ-053/056 | **Cross-referenced only** (AA A6, UL); not duplicated | retirement audit unchanged |
| §15 | Bounded context ≠ microservice; distribution only with evidence | AA KISS principle | **AA governing-principle refinement** with the architectural bias and the evidence list | — |
| §16–17 | First-pass UL, Agent Ready and AlienIntent | none existed for AlienIntent (AA §44(2) outstanding); candidate UL v1 table in domain-model.md | **Created** `docs/architecture/alienintent-ubiquitous-language-v0.1.md`; Agent Ready UL created in its own repository | AA A11 |
| §18 | User-interaction starting model | SWF-25 workflow line; AA §9 | Recorded in UL §3 as accepted starting model; no UX design | — |
| §19 | `alienintent init` / `doctor` extension points | AA §31/§38; SF-REQ-037/038 | **Amended SF-REQ-037** with the extension-point list; doctor already validates capability | AA A10; UL §3 |
| §20–21 | Settled-in-principle list; follow-up canonicalization work | — | This report §6 is the follow-up list | — |

**New owners created: none.** Every decision landed on an existing owner or the existing
Architecture Authority.

## 3. Terminology contamination audit and repair

Inventory method: `grep` for `BLOCKED`, `NEEDS_CLARIFICATION`, `SPLIT_RECOMMENDED`, `Gap Trap`
across `docs/` and `tools/`, then classification of each artifact as *active normative*,
*historical record* or *historical evidence*.

| Artifact | Classification | Treatment |
|---|---|---|
| `docs/evidence/wave2-specified-requirements.json` (SF-REQ-015 candidate) | current design authority for Wave 2 | **Repaired** to `READY/CLARIFY/SPLIT/HOLD`; provenance note; pre-repair wording in git history |
| `docs/evidence/wave2-design-contracts.json` (SF-REQ-015 contract) | current design authority | **Repaired** likewise; the historical sequence `BLOCKED → SPLIT_RECOMMENDED → READY` is kept as an explicitly historical fact |
| `docs/evidence/wave2-agent-ready-assessments.json` (46 dispositions) | historical programme evidence | **Not rewritten.** `assessor_vocabulary: alienintent-bootstrap-assessor` and a provenance note added; dispositions untouched |
| `docs/decisions/2026-09-21-py10-transport-split.md` (SWF-33) | historical decision record quoting the assessment acted on | **Not rewritten.** One terminology note at the top |
| `docs/decisions/alienintent-post-wave1-to-wave2-program-plan.md` | completed programme's operating plan | **Not rewritten.** One terminology note under Status |
| `docs/evidence/wave1-*`, `docs/work-units/**`, programme prompts/reports/prework, `wave1-agent-ready-outcome-matrix` | historical evidence | untouched |
| `tools/evidence/check_agent_ready_set.py` | active code | **Refactored**: canonical `AGENT_READY_DISPOSITIONS`; legacy set only for artifacts that declare `assessor_vocabulary`; default is Agent Ready's four. Tests migrated |
| `docs/decisions/2026-09-20-deterministic-failure-class-promotion.md` (SWF-24) | active authority | "Gap Trap / deterministic failure-class promotion" → "Deterministic failure-class promotion" + attribution note |
| `tools/evidence/check_gap_trap_backlog.py` | active code validating a historical artifact | docstring note; file and artifact names retained |
| `docs/proposals/PROP-2026-0002…` | immutable proposal provenance | untouched |
| `BLOCKED` as verdict/lifecycle in the factory plan (lines on Verdict, HumanDecision "explicit BLOCKED reason", SF-REQ-017) | legitimate AlienIntent vocabulary | untouched, by design |

## 4. Conflicts found and how resolved

1. **FD-01 lane ownership vs the new Requirements / Planning context.** FD-01 item 1 says the
   external provider is canonical for CAPTURE…READY. Founder v0.1 assigns specification, planning
   and compilation to AlienIntent. Resolved as a *refinement*: provider = canonical for
   product/work-management state and its human representation; AlienIntent context = performs
   the engineering conversion and projects it. Recorded in FD-01 with the wording tension stated,
   not smoothed. The Founder should confirm this reading (follow-up F1).
2. **Two senses of "allocation".** Founder UL: binding work to a worker (execution). Wave 2
   design / R1-GAP-013-ALLOCATION / AR13-CQ-001: compile-time obligation-to-unit mapping. Resolved:
   execution sense is canonical *Allocation* (SF-REQ-026); compile-time sense renamed *obligation
   mapping* (SF-REQ-013). Existing artifacts keep historical wording.
3. **Allocator vs scheduling.** The factory plan treats scheduling (SF-REQ-002, "next eligible
   READY BIU") and routing (SF-REQ-026) as distinct components. Allocation was not collapsed into
   scheduling; it was placed with routing, which it extends, and the kernel (SF-REQ-009) keeps
   enforcement. Choice flagged for Founder confirmation (follow-up F2).
4. **`context_assembly` vs Requirements / Planning.** Wave 2 contracts bound SF-REQ-011..013 to
   the `context_assembly` module. Whether that module *is* the new context or a sub-module was
   left to a Design Contract under SF-REQ-051 (FD-02 refinement; follow-up F4). **Resolved
   2026-09-26**: `context_assembly` is an internal module/application capability within the
   Requirements / Planning bounded context, not a separate bounded context. See
   `docs/decisions/2026-09-26-f4-context-assembly-bounded-context-disposition.md`.

## 5. Terminology collisions (full table in UL v0.1 §4 and Agent Ready UL §3)

READY (lifecycle vs disposition) · BLOCKED (verdict/lifecycle vs legacy disposition) · Allocation
(execution vs compile-time) · Requirement Source vs Work Management Provider · Assessment vs
Readiness Assessment · SPLIT vs Split Transaction · Owner Question / Engineering Unknown vs Agent
Ready's established *Owner Unknown / Implementation Unknown* (Agent Ready's win) · Gap Trap ·
fake worker · Verification/Review vs VERIFY/REVIEW · Rework Locality vs rejection locality · the
Assessment Contract has no version identifier · `provider_evidence` is Codex-only.

## 6. Follow-up list — genuine unfinished work only

- **F1 (Founder).** Confirm the FD-01 refinement reading (§4.1).
- **F2 (Founder).** Confirm SF-REQ-026 as the Allocator's canonical owner rather than a distinct
  requirement.
- **F3 (Wave 2 design, SF-REQ-029/015).** Design the retained Readiness Assessment record envelope
  (the two-shape drift Phase 4 found was AlienIntent's envelope, not Agent Ready's schema) and the
  `ReadinessAssessment` port adapters against Agent Ready's actual CLI/MCP contract, including the
  exact-version pins (Codex 0.153.4 / Claude Code 2.1.258).
- **F4 (Design Contract, SF-REQ-051). Resolved 2026-09-26.** `context_assembly` is an internal
  module/application capability within the Requirements / Planning bounded context, not a
  separate bounded context. See
  `docs/decisions/2026-09-26-f4-context-assembly-bounded-context-disposition.md`.
- **F5 (Wave 2 design-learning objective, SF-REQ-030).** *Identify the earliest lifecycle/evidence
  point at which Assessment Feedback is mature enough to be useful without being premature or
  misleading.* Discover empirically during Wave 2; may resolve before Wave 2 completes. No trigger
  invented here.
- **F6 (Agent Ready).** Work packet: feedback contract, corpus roadmap, version identity on CLI and
  MCP, stderr format documentation — see the interface audit and Agent Ready UL §3.
- **F7 (open Founder decisions, unchanged by v0.1).** 006A (seven retirement items), 007A R02–R05
  and LRN-022/023 ownership, 008A SF-REQ-056 ratification, 010A edge authority / 039 orchestration
  / 039 real-outcome / monitor host, 013A concrete allocator answer for WO-220101.
- **F8.** Wave 2 artifacts still reference SF-REQ-039's former title in places; valid by
  identifier, to be refreshed when those artifacts are next revised.

## 7. Decisions not enacted, and why

- Any retirement or provider-configuration change (006A): v0.1 confirms direction, authorizes no
  action; retirement is by proven replacement.
- SF-REQ-056 ratification (008A): v0.1 is consistent with it but does not ratify the authored text.
- The four remaining Phase 7 amendments and the four remaining design gaps: not addressed by v0.1.
- Any UX design, `init` implementation, or code restructuring: explicitly deferred by the Founder.
- Wave 2 execution: not authorized by anything here.

## 8. Validation

`tools/evidence/check_canonical_vocabulary.py` — new; 13 tests including a control that every
check can be made to fail; **proven red against the live repository before repair (11 failures)**
and against the real pre-repair SF-REQ-015 specification text, not only synthetic fixtures.
Results of the full validation run are recorded in the closure commit message.
