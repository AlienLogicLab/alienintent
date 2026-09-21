# Wave 2 Design Contracts — POSTW1-DESIGN-009-R2

The [JSON contract](wave2-design-contracts.json) governs this companion. These ten revised design candidates await independent repair review. The [Phase 10 verdict](wave2-design-verification.json) remains unchanged. Phase 8 specifications remain requirements authority; this repair creates or amends no Product Requirement. Four R1 authority gaps remain at SPECIFY; one R2 edge-direction question is recorded for the Founder. A structural checker pass does not close them or approve implementation.

Original design baseline: `3ea566f211a13aa6ec36c2bb8f9a4703d31a1f02`. Repair baseline: `c08fa798a3d9dd37fda30f4d35c9aa18c728a287`. Only these two design files are revised locally; no commit, push, network, lifecycle/Project state change or worker contract change is authorized.

## Historical R1 repair disposition (superseded where R2 specifies)

All 10 requirements and 53 exact acceptance IDs retained. Prior proof obligations retained; withdrawn allocation-input assumption and unauthorized kernel implementation direction explicitly superseded below. No designed probe is claimed executed.

- **DV-1 — ADDRESSED:** Two explicit SPECIFY gaps for shared orchestration and real worker outcome ownership; conditional target, pre-launch live binding gate and real-path probe.
- **DV-2 — ADDRESSED:** Allocation source returned to SPECIFY; current evidence selects compiler-derived initial decomposition, and mandatory external allocation is withdrawn.
- **DV-3 — ADDRESSED:** Fixed context edge table, target-layer restrictions, leaf-type cycles rule and composition-owned premise bridge; enforcement references that rule.
- **DV-4 — ADDRESSED:** Explicit requirement grammar, exact token capture, typed UNVERIFIED conflicts and synthetic nonconforming/extended identity fixtures.
- **DV-5 — ADDRESSED:** LRN-002 composed unbound/unauthorized-stub AssessmentAuthority refusal probe added.
- **DV-6 — ADDRESSED:** Optional observation port; default UNBOUND numeric policy disabled, explicit context events retained; BOUND unusable values terminate, with composition fixtures.
- **DV-7 — ADDRESSED:** Contradiction is authorized operator judgment with typed admission, evidence and exact termination/refusal fixtures.
- **DV-8 — ADDRESSED:** Hosting gap returned to SPECIFY with resolution actor; independent monitor/scan health observations and stale-health fixtures required.

All four advisories are addressed; none declined. Episode age provenance is disclaimed. No finding is disputed. These are designer repairs, not an independent verification verdict.

## Authority gaps returned to SPECIFY

### R1-GAP-039-ORCHESTRATION

- **id**: R1-GAP-039-ORCHESTRATION
- **requirement_id**: SF-REQ-039
- **status**: RETURN_TO_SPECIFY
- **resolution_actor**: Product authority through SPECIFY; Program Director routes the decision. Implementers and this designer may not close it.
- **question**: Which existing requirement authorizes canonical multi-role orchestration and which domain owner maintains it?
- **evidence**: Phase 8 SF-REQ-039 scopes offline proof over SF-REQ-001..010 interfaces; FactoryCoordinator._completed_for_outcome currently collapses successful production through closure. The selected ten contracts do not assign the proposed kernel replacement.
- **design_disposition**: Return requirement/owner mapping to SPECIFY; execution_coordination is the candidate location, not an assigned capability owner. Withdraw permission to implement the replacement under the offline harness requirement.
- **blocks**: Shared-kernel role router/orchestration changes and claims that full 039 scenarios are implementable.

### R1-GAP-039-REAL-OUTCOME

- **id**: R1-GAP-039-REAL-OUTCOME
- **requirement_id**: SF-REQ-039
- **status**: RETURN_TO_SPECIFY
- **resolution_actor**: Product authority through SPECIFY; Program Director routes the decision. Implementers and this designer may not close it.
- **question**: Which existing requirement and owner supply durable RoleOutcomeRecord on the non-scripted worker path, with compatible readback and consumer semantics?
- **evidence**: sandbox_run_profile.py constructs RealWorkerProvider and the shared FactoryCoordinator; github_profile.py uses that coordinator. WorkerOutcome alone supplies no proposed role sidecar binding.
- **design_disposition**: Return to SPECIFY; invocation_runtime is a candidate adapter location only. No worker contract amendment or new Product Requirement here.
- **blocks**: OutcomeEvidencePort activation in shared/live profiles and live-path readiness claims.

### R1-GAP-013-ALLOCATION

- **id**: R1-GAP-013-ALLOCATION
- **requirement_id**: SF-REQ-013
- **status**: RETURN_TO_SPECIFY
- **resolution_actor**: Product authority through SPECIFY; Program Director routes the decision. Implementers and this designer may not close it.
- **question**: Does an authorized upstream allocation producer exist, or must SF-REQ-013 derive initial decomposition under explicit constraints?
- **evidence**: Phase 8 scope and AC-01 start from specified requirements and verified design; dependencies name no allocation producer. canonical-architecture excludes a general task decomposition engine, not the explicitly selected bounded initial compilation obligation.
- **design_disposition**: Evidence selects: SF-REQ-013 must derive the initial decomposition itself; no supported external allocation owner/interface exists. Withdraw mandatory hand-authored allocation input. Return to SPECIFY for authoritative confirmation and decomposition/identity constraints; do not close that product-authority question in design. If authority instead chooses an external producer it must name its owner and interface explicitly.
- **blocks**: Initial decomposition implementation and Wave 2A completion claims; validating allocated candidates alone cannot satisfy 013.

### R1-GAP-MONITOR-HOST

- **id**: R1-GAP-MONITOR-HOST
- **requirement_id**: SF-REQ-053/SF-REQ-056
- **status**: RETURN_TO_SPECIFY
- **resolution_actor**: Product authority through SPECIFY; Program Director routes the decision. Implementers and this designer may not close it.
- **question**: Who owns the persistent monitor/periodic-scan host, supervision and restart policy independent of model invocation?
- **evidence**: SWF-27 and 053 require persistence beyond episodes; 056 G+I assumes functioning scans. Neither this design nor its composition constructor supplies a deployment host/supervisor owner.
- **design_disposition**: Explicit out-of-scope operational ownership gap returned to SPECIFY/Product authority, routed by Program Director. Local service design and fixtures may proceed, but no background shell process or bootstrap waiter is adopted as supervisor.
- **blocks**: Live monitor/scanner adoption and an operational G+I guarantee until host ownership and independent supervision are assigned.

## Fixed shared contracts

### Architecture scope

All named groups are existing Python src/alienintent modules. The legacy bounded_context field records implementation location; FD-02 does not promote these modules to independent bounded contexts. Proposed module/service/command names below are design targets, not claims of existing APIs. Node remains frozen bootstrap authority; no Node adapter/import dependency or sovereignty claim. Existing canonical-architecture.md separates upstream planning from execution; this design accepts authorized definitions and introduces no general planning or requirements-authoring engine. SF-REQ-013 initial decomposition is distinct from general planning; its allocation-source gap returns to SPECIFY, not to implementers.

### Alternatives and selection

Select existing SQLite OperationalStore + separate immutable local evidence, instead of a new service/database or a Git-edited canonical requirement register. This preserves transactional recovery and source authority with fewer mechanisms. Withdraw the mandatory supplied-allocation selection: Phase 8 authorizes initial compilation from requirements/design, not validation of hand-authored BIUs. See R1-GAP-013-ALLOCATION; no decomposition mechanism is authorized by this repair. Select fenced durable effect reuse instead of status-toggle/watch-process deduplication.

### Value contract

New internal ports use frozen Python dataclasses/typed enums and standard-library primitives; serialization schema_version=1 is internal only. Required fields described per contract are mandatory; unknown schema version is SchemaIncompatible, missing referenced authority yields Hold. Ref is (project/profile, logical_id, revision_digest, source locator); Result variants are explicit, never bool success. Existing BiuContract and Agent-Ready external schemas are not replaced.

### Canonical encoding

Canonical digest encoding follows BiuContract: UTF-8 JSON, sorted object keys, compact separators; set-valued collections sorted, sequence-valued collections retain order, no NaN/Infinity. Use sha256:<hex>. Raw external evidence also retains a separate exact-byte digest. UUIDs for attempts/episodes are allocated once at ingress and persisted before dispatch; clock/ID creation only at injected composition boundaries.

### Evidence storage

EvidenceRepository is a port owned by evidence_learning; local adapter stores immutable objects under configured external evidence_root/objects/<sha256>. Write temporary sibling, flush/fsync, atomically install without overwrite, fsync directory, verify digest, then CAS operational reference. Crash before pointer leaves harmless unreferenced artifact; crash after pointer is read-verified. No operational commit references unwritten evidence. Distinct namespaces and access labels separate normative refs, observation bodies and verdicts. All referenced history retained in this wave; no GC/retention automation or new learned-policy store.

### Operational storage

Reuse SQLiteOperationalStore and existing profile-scoped versioned aggregate APIs; upstream:<kind>:<identity>, episode:<objective>, attention:<identity> are new namespaced payloads, not a new engine. schema_version in every new payload; reject incompatible version without mutation. Operational pointer writes use CAS; immutable evidence is never updated in place. Future payload migration requires explicit versioned design and is not implementer freedom.

### Composition graph

evidence_profile builds EvidenceRepository. upstream_profile builds inventory -> ambiguity/proof/design admission -> compilation -> readiness consumer. Proof planning depends on design premise inputs, while final verified design depends on proof feasibility: a draft may be inspected both ways, but final applicability pins both artifact revisions; no recursive auto-approval. control_plane_profile builds attention/context/episode/liveness around existing FactoryCoordinator and store. offline_profile assembles the same applications with local external-system adapters. Installation configuration is read only by composition; domain services receive values/ports.

### Cross contract cycles

011 and 016 share neutral Ref values, not mutual application imports. 014 creates proof plans from candidate design/premises, 051 reviews that exact pair, 013 consumes the verified pair. 053 exposes AttentionPort independently of 056; 056 consumes it and produces ordinary observed events. Ratification of 056 is required only for 056-specific recovery capability, not for generic 053 attention/tenure.

### Failure protocol

Typed Hold includes reason code, affected refs, evidence refs and required authority/action. StoreUnavailable/SchemaIncompatible stop dependent mutations. VersionConflict never changes an old result to fit new state. No auto-retry may exceed existing authorized budget; failed evidence writes prevent admission. Commands propagate nonzero failure, with held/unverified distinctly rendered.

### Interfaces and wiring proof

Every new adapter declares its port; every public composed operation needs intact success and a typed-failure probe against a real temporary SQLite store. LRN-002 is the single reused composition promotion. Static architecture rules do not substitute for runtime reachability or consumer truth.

### Authority boundaries

All ten are design candidates, not release authority. SF-REQ-056 remains AUTHORED_IN_THIS_PHASE and unratified. G1/G2 owner assignment is a real upstream authority prerequisite, not a decision left to implementation. Existing unresolved authority stays explicit even though deferred_to_implementation is empty. No retroactive Wave 1 changes or current worker/lifecycle contract edits. R1-GAP-039-ORCHESTRATION and R1-GAP-039-REAL-OUTCOME block shared-kernel/real-worker changes; R1-GAP-013-ALLOCATION blocks initial compiler decomposition; R1-GAP-MONITOR-HOST blocks operational monitor/scan adoption. These are SPECIFY returns, not deferred implementation choices, approved requirements, or authority granted by this design. Unaffected design remains reviewable. R2-GAP-051-EDGE-AUTHORITY is a Founder question about adoption of the R1 module-direction proposal, not a new requirement or reopening of FD-02; normative direction-dependent admission is held, while established architecture checks remain active.

### Amendments

POSTW1-DECIDE-007A pending SF-REQ-008, 022, 013, adjacent 025 and 029 are not assumed. Initial compilation excludes general replan; reconciliation excludes new exhaustion/retry policy; episode/effect records use existing store primitives; evidence does not promote learning; telemetry normalization remains outside. Therefore no selected contract requires adoption of a pending amendment. If any is adopted, affected design revisions need independent review before use.

### Enforcement counting

Count each contract opportunity entry once; promotion reuse count is entries with phase3_promotion. Repeated LRN-002 entries are distinct consumer probes under the same promotion, not new controls. Seven unique promotions are reused. All opportunities are proposed, not deployed or proven by this design phase.

### Atomic fencing extension

- **owner**: execution_coordination; proposed FencedOperationalStore port extends existing OperationalStore without replacing it. SQLite adapter uses the same database and existing aggregates/reservations/effects tables. This is design of existing crash-safe semantics, not adoption of pending SF-REQ-008 elaboration.
- **methods**:
  - commit_guarded(profile, aggregate, expected_version, expected_vector, reservations, state, effect_id, payload) -> new_version: BEGIN IMMEDIATE; verify all relevant aggregate versions and exact reservation owner/fences; reject expired episode/authority ref; perform aggregate update and unique effect insertion in the same transaction; commit.
  - claim_guarded(profile, effect_id, reservations, expected_vector) -> Effect: BEGIN IMMEDIATE; validate all fences and applicable version vector, pending effect and suppression; atomically claim pending to unknown/sending using existing effect status semantics. Duplicate claim is refused.
  - confirm_guarded(profile, effect_id, reservations, receipt_ref) -> confirmation: validate fence and correlated receipt before existing confirmation transition.
- **boundary**: Existing commit_with_effect/claim_effect do not validate a passed reservation fence. They must not be described as sufficient for the new fenced admission. New guarded operations are the mandatory path for episode/liveness effects; old callers remain compatible, but every caller participating in the same episode/lane is routed through guarded operations.
- **dispatch**: Reservation is held from intent through send and readback; do not steal/release it solely on timeout. A consumer validates the invocation/effect/fence before accepting a side effect, deduplicates on effect identity and persists its acceptance/outcome. If consumer cannot fence, use exclusive reservation with no reassignment until correlated completion or independently confirmed process death; ambiguity parks. Releasing reservation while an old sender may still act is forbidden. Local effect consumer journal admission serializes with guarded claim; arbitrary remote exactly-once guarantees are not assumed.
- **crash**: No live-sender lease expiry or unfenced takeover. Unknown effects read back first. Recovery may confirm original outcome under explicitly validated recovery ownership; stale sender cannot confirm under a released fence. If sender death/outcome cannot be established, retain hold and reservation until authorized resolution.
- **lock_order**: For multiple required reservations acquire sorted (profile,scope,key) order; on contention release only reservations newly acquired by that attempt in reverse order and return capacity hold. Never release a retained unknown-effect owner to make progress.

### Input limits

Composition enforces maximum 10 MiB per imported source/evidence JSON object and 256 source documents per inventory request; exceeding limits returns INPUT_LIMIT_HOLD with the offending identity, never truncation or omitted obligations. Paths must resolve within declared permitted roots; UTF-8/JSON decode failure is typed invalid input. Limits are explicit profile policy overrides recorded in the input manifest; changing them cannot change authority.

### Context dependency direction

```json
{
  "status": "DESCRIPTIVE_ONLY; normative module-direction authority unresolved under R2-GAP-051-EDGE-AUTHORITY.",
  "scope": "Observation covers every tracked src/alienintent/**/*.py at baseline_commit, including AST Import/ImportFrom nodes under TYPE_CHECKING and re-export statements. Graph keys are internal module groups, not newly approved bounded contexts. Cross-group absolute alienintent imports are aggregated; no relative cross-group imports were observed. This is a source-import snapshot, not runtime/dynamic-import reachability or permission to add edges. Composition-time data flow is not an import edge.",
  "baseline_commit": "c08fa798a3d9dd37fda30f4d35c9aa18c728a287",
  "observed_on": "2026-09-22",
  "observed_edges": {
    "context_assembly": [],
    "execution_coordination": [
      "control_plane",
      "installation",
      "invocation_runtime"
    ],
    "evidence_learning": [],
    "control_plane": [
      "execution_coordination"
    ],
    "invocation_runtime": [
      "execution_coordination"
    ],
    "installation": [
      "execution_coordination"
    ],
    "composition": [
      "control_plane",
      "execution_coordination",
      "installation",
      "invocation_runtime"
    ]
  },
  "existing_violations_of_withdrawn_r1_table": [
    {
      "path": "src/alienintent/execution_coordination/adapters/github_projects_v2.py",
      "sha256": "f9c58e64692ffb810ffcc55035642908b70deaa751e26fda53ab8ceeab4cf409",
      "source_module": "execution_coordination",
      "target_module": "installation",
      "imports": [
        {
          "line": 20,
          "module": "alienintent.installation.domain.project_identity"
        },
        {
          "line": 21,
          "module": "alienintent.installation.ports.github_transport"
        }
      ]
    },
    {
      "path": "src/alienintent/execution_coordination/adapters/github_repository_api.py",
      "sha256": "62ea73d04ef888370033c55a4e1a327f25dadc70414413e6f4e3956e22b71626",
      "source_module": "execution_coordination",
      "target_module": "installation",
      "imports": [
        {
          "line": 14,
          "module": "alienintent.installation.ports.github_transport"
        }
      ]
    },
    {
      "path": "src/alienintent/execution_coordination/application/local_artifact_custody.py",
      "sha256": "b989fcf929fa5b0b979568c6fa6ef01d4927bcb77683df7e5852dc01643a7d86",
      "source_module": "execution_coordination",
      "target_module": "invocation_runtime",
      "imports": [
        {
          "line": 11,
          "module": "alienintent.invocation_runtime.domain.runtime"
        }
      ]
    },
    {
      "path": "src/alienintent/installation/application/doctor.py",
      "sha256": "5525676b6fcfdab4fbd273f7666aa4e8f0bb375537bf7ead9d41032c4b43600a",
      "source_module": "installation",
      "target_module": "execution_coordination",
      "imports": [
        {
          "line": 10,
          "module": "alienintent.execution_coordination.domain.webhook_authenticity"
        }
      ]
    }
  ],
  "counting": "Four importing-file violations, containing five import statements and three distinct module-pair edges. These violate the withdrawn R1 table, not an established product boundary. All five statements are named; no silent exemption.",
  "withdrawn_r1_proposal": {
    "status": "Historical candidate only; not an allowed-import policy. No implementation or enforcement authority. Any adoption requires a Founder decision and a reviewed design with an executable scope/baseline/expiry predicate.",
    "edges": {
      "context_assembly": [
        "execution_coordination",
        "evidence_learning"
      ],
      "execution_coordination": [
        "context_assembly",
        "evidence_learning",
        "control_plane"
      ],
      "evidence_learning": [
        "context_assembly",
        "execution_coordination"
      ],
      "control_plane": [
        "context_assembly",
        "execution_coordination",
        "evidence_learning"
      ],
      "invocation_runtime": [
        "execution_coordination",
        "control_plane"
      ],
      "installation": [],
      "composition": [
        "context_assembly",
        "execution_coordination",
        "evidence_learning",
        "control_plane",
        "invocation_runtime",
        "installation"
      ]
    },
    "target_layers": "Outside composition, listed cross-context imports target domain values or ports only, never another context application or adapters. Within a context domain imports domain only; ports import domain/ports; application imports domain/ports/application; adapters may implement ports and invoke applications. Domain/application never import adapters; no context imports composition. Existing architecture layering/vendor/configuration/determinism rules also apply. Composition alone may construct applications/adapters across contexts.",
    "typed_cycles": "execution_coordination MAY depend on context_assembly.domain DesignApplicability values through a consumer port; context_assembly MAY depend on execution_coordination.domain BiuContract and ports. These reciprocal context edges permit leaf type references, not cyclic module imports or recursive application calls. Cross-imported value modules must not import back into their consumers. Port arguments reference leaf values; protocols and adapters depend on those leaves, not vice versa. No new shared context is introduced."
  },
  "premise_bridge": "evidence_learning adapters MUST NOT import installation or composition. composition/upstream_profile constructs an adapter implementing evidence_learning PremiseEvidence, invokes the authorized installation doctor/probe callable at that outer boundary, and passes immutable evidence_learning values inward. composition/doctor_probes is reachable only by composition wiring; no inward import of the composition root. Recorded offline observations use the same port. This remains the proposed Wave 2 composition wiring, not evidence that the withdrawn repository-wide edge table is authoritative.",
  "fitness": "051-architecture-boundary retains BLOCKING existing architecture checks repository-wide using tools/fitness/check_architecture.py --root src/alienintent --check all. It must not compare production imports to withdrawn_r1_proposal. For the proposed directional extension, authority status is explicit: without a pinned Founder disposition of R2-GAP-051-EDGE-AUTHORITY return ARCHITECTURE_AUTHORITY_HOLD for affected design admission, never PASS or an empty successful check. The descriptive graph may be regenerated as observation but cannot authorize or reject product imports. Existing approved checks continue independently. No change to the current checker is claimed here.",
  "conditional_probes": "The prior R1 direction/leaf-cycle negative and positive fixtures are retained as conditional candidate-policy tests only, blocked pending Founder disposition and reviewed scope. They cannot certify production conformance or require retroactive source edits. Existing layering/vendor/configuration/determinism checks and composed interface compatibility probes remain unconditional."
}
```

### Monitor liveness

- **authority_gap**: R1-GAP-MONITOR-HOST
- **observation_owner**: control_plane owns durable MonitorHealth values and read-only health inspection; execution_coordination owns scan-progress observation. Host/supervisor operational owner remains unassigned, returned to SPECIFY.
- **record**: MonitorHealth(profile, instance_id, generation, policy_digest, started_at, last_monitor_tick, last_scan_started_at, last_scan_completed_at, last_scan_outcome, next_scan_due, last_error). Persist monitor ticks independently of whether work exists; scan completion advances only after a full attempt, retaining EvidenceHold/error as outcome. Restart uses new instance/generation and preserves old observations.
- **health_rule**: With valid progressing observation clock, no record -> UNVERIFIED; age since last monitor tick > 2*I or overdue last scan completion > 2*I -> STALE; failed/incomplete latest scan -> DEGRADED; otherwise HEALTHY. At exactly 2*I still within bound. Clock regression or unreadable health store -> UNVERIFIED, never healthy. I is the configured scan interval (default 60 seconds for 053 monitor-only operation too). Health is separate from workload quiet/no-gap.
- **supervision**: An independently running authorized host observer must inspect health and alert/restart under its assigned policy; self-heartbeats alone cannot detect a dead host. Until the hosting gap closes, expose read-only inspection and make no live supervision/G+I guarantee. No shell background waiter is adopted.

## SF-REQ-011 — Requirements IR

Requirements IR domain in context_assembly; source decision issuers retain normative ownership.

**Authority:** DESIGN_CANDIDATE; independent Phase 10 verification outstanding Gap references: none newly recorded.

InventorySnapshot: schema_version, source_manifest_digest, definitions indexed by (requirement_id, revision), references, conflicts, unresolved IDs, retired/superseded IDs, dependency edges, BIU satisfaction-link references, prior_snapshot. Each definition has typed SF-REQ-016 role and authority reference. IdentifierShapeConflict records retain raw token, reason, source locator and grammar revision separately from valid-but-undefined IDs.

**Ports and wiring.** RequirementSource.read(manifest) -> tuple[SourceDocument | SourceUnavailable]; manifest fixes repository/source identity, revision, path, digest, locator and access label. RequirementInventory.assemble(documents, authority_records) -> InventorySnapshot; resolve(id, revision) -> Definition | Conflict | Unresolved. Inputs/outputs are immutable context_assembly domain values. InventorySnapshot includes typed identifier_issues under identifier_contract; resolve cannot hide malformed tokens as absent. EvidenceRepository stores snapshot and source manifest; OperationalStore holds current snapshot pointer by expected version. Proposed context_assembly/adapters/versioned_source.py reads supplied local files or Git blobs at explicit revisions, with separate parsers for factory-plan headings, Canonical requirement prose and Recorded as prose. It does not crawl or execute imported text. Proposed context_assembly/adapters/inventory_repository.py binds inventory ports to existing OperationalStore and evidence_learning EvidenceRepository; approved-source manifest provides authority precedence, never file order. Proposed composition/upstream_profile.py constructs source adapters, EvidenceRepository, inventory application and SQLite-backed pointer repository; control_plane CLI exposes the application. SF-REQ-012/013 consume its immutable snapshot, not source adapters.

**State changes and identity.** PINNED_INPUT -> ASSEMBLED when every readable source is classified; unreadable sources remain UNVERIFIED in a partial snapshot. Conflicting effective definitions -> CONFLICT for that ID; undefined mention -> UNRESOLVED; approved unambiguous definition -> ELIGIBLE_FOR_PREPARATION. Retirement is preserved, not ID deletion. A changed semantic or authority revision publishes a new snapshot and marks dependent design/compilation/readiness references stale; old satisfaction observations stay historical. Requirement identity is the exact supplied requirement ID (case-sensitive; no prefix rewrite, suffix stripping or zero-padding) scoped to the source project. Revision digest uses canonical JSON of semantic fields and authority revision, excluding formatting/locator aliases. Equivalent formats with the same authority revision merge provenance into one revision; genuinely distinct decisions do not collapse. Snapshot identity hashes sorted source manifest and revision keys.

**Failure and recovery.** Heading-only parser omits prose definitions: refuse fixture acceptance. Two incompatible effective definitions: preserve both sources and block only that ID. Source missing/digest mismatch: UNVERIFIED; do not reuse a cached definition as confirmed current. Retired ID reuse: conflict requiring source authority resolution. In-scope unrecognized or ambiguous requirement slot -> typed UNVERIFIED issue; recognized acceptance IDs/compound references are separate kinds. Wrong-kind definition slot -> WRONG_IDENTIFIER_KIND. No prefix truncation, silent omission or namespace authority inferred from shape. Reassemble from the pinned manifest; compare snapshot digest. Repoint only by CAS. A partial or conflicted snapshot can support inspection but cannot supply compilable authorization for affected IDs.

**Operator and evidence.** Proposed upstream inventory show/export accepts a pinned manifest, returns JSON plus derived text, and names exact blocking IDs; it never edits sources or Issues. Manifest, per-form extraction ledger, exact source locators and digests, conflicts, revision graph, retirement links and requirement/BIU links; retain the historical 56 referenced / 53 defined fixture independently of the newly authored 056 revision. The named embedded POSTW1-011-HISTORICAL-CORPUS-R2 manifest pins the exact historical fixture documents, digests and definition locators; counts alone cannot certify extraction completeness. Emit inventory.assembled/held with snapshot digest, referenced/defined/undefined/conflict counts and affected IDs. Count missing input as unknown, not zero.

**Fixed choices.** Compilation accepts only exact unambiguous authorized revisions, never the inventory status alone. No requirements-authoring or planning LLM is introduced: this is import/projection under the selected factory-plan SF-REQ-011. identifier_contract fixes grammar, token capture, namespace validation and typed failures identically across all three prose forms. Grammar changes require reviewed design revision; identity is never inferred from sorted position.

**Identifier contract.**

```json
{
  "grammar": "\\A[A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)*-REQ-[0-9]{3,}(?:[A-Z])?\\Z",
  "meaning": "ASCII, full-token match. One or more uppercase namespace segments, literal -REQ-, at least three ASCII digits, optional single uppercase suffix. SF-REQ-011, SF-REQ-011A, SF-REQ-1000 and TEAM-X-REQ-011 are syntactically recognized. Recognition confers no authority: the pinned approved-source manifest must authorize the exact namespace/project binding; otherwise UNVERIFIED/UNAUTHORIZED_REQUIREMENT_NAMESPACE.",
  "extraction": "Within manifested spans, capture whole heading/Canonical requirement:/Recorded as identifier slots before validation; tokenize reference prose with Markdown-aware delimiters (paired emphasis/backticks/brackets, link labels separate from URLs, terminal prose punctuation). Preserve raw bytes and locator. Classify whole tokens by token_kinds before requirement grammar validation; no conforming substring may rescue an unknown token. A definition slot requires exactly one RequirementIdentifier; empty/ambiguous slots remain typed issues. An AcceptanceCriterionId or CompoundReference in a definition slot is WRONG_IDENTIFIER_KIND, not malformed requirement syntax. Outside declared spans, no requirement-shape issue is emitted; excluded material is not counted as parsed requirements.",
  "typed_failure": "InventorySnapshot.identifier_issues retains IdentifierShapeConflict(status=UNVERIFIED, reason=UNRECOGNIZED_REQUIREMENT_ID, raw_token, source_ref, locator, grammar_revision=2) only for unrecognized tokens in declared requirement/reference spans. Missing/ambiguous slots use MISSING_REQUIREMENT_ID/AMBIGUOUS_REQUIREMENT_ID; wrong-kind definition slots use WRONG_IDENTIFIER_KIND; unauthorized namespace uses UNAUTHORIZED_REQUIREMENT_NAMESPACE. Preserve exact bytes/digest. These block compilation dependent on the affected source spans/IDs, not unrelated sources. Valid undefined requirement references are UNRESOLVED. Recognized acceptance IDs and valid compound/possessive references do not create shape conflicts. Ledger every in-scope token containing -REQ- with its category or issue so omissions cannot pass.",
  "biu_distinction": "Requirement and BIU identifiers are distinct. Wave 1 proposed BIU grammar (docs/evidence/wave1-biu-split-replan-design.json, identity_grammar; not an implemented validator) is \\A(?:(?:PG|PY)-[0-9]{2}|WO-[0-9]{6})(?:[A-Z])?\\Z. Preserve exact identities, including suffixes; neither grammar allocates identity from sorting or ordinal position. No requirements or BIUs are created by parser fixtures.",
  "grammar_revision": 2,
  "corpus_scope": "RequirementSource accepts an explicit versioned source manifest, never an implicit docs/** scan. Each entry pins repository, revision, path, SHA-256, parser form, definition spans, reference spans, namespace/project authority and access label. Only declared spans are requirement-identifier input. Requirements IR production inputs need authorized-source bindings; historical_fixture_manifest below is a read-only regression fixture, not current normative authority. Evidence/reports/prompts/work packets and acceptance/design documents are excluded unless separately manifested with their role and spans; inclusion never promotes observations to definitions. Missing/digest-mismatched source -> SourceUnavailable/UNVERIFIED, not a smaller successful inventory.",
  "token_kinds": {
    "acceptance_criterion_regex": "\\A[A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)*-REQ-[0-9]{3,}(?:[A-Z])?-AC-[0-9]{2,}\\Z",
    "acceptance_disposition": "Full-token AcceptanceCriterionId is classified before RequirementIdentifier; retain exact acceptance ID and its syntactic parent ID as a typed relationship, never a requirement definition or IdentifierShapeConflict. Namespace/authority and parent resolution are separate from syntactic recognition. No requirement reference is invented merely by stripping the AC suffix.",
    "compound_reference": "Reference spans recognize slash lists of full RequirementIdentifier operands (SF-REQ-001/SF-REQ-002), or one full operand followed by slash-separated numeric operands with at least three digits and optional one uppercase suffix (SF-REQ-030/054). Shorthand inherits only the first namespace-REQ- prefix, preserving numeric spelling. Ranges use ASCII .., en dash U+2013 or ASCII hyphen between a full start and full or numeric end (SF-REQ-001–010). Range endpoints must share namespace and digit width, have no letter suffix, and be ascending. Classify as CompoundReference; retain expression and exact endpoints/list operands, never create definitions or identities for unmentioned intermediate values. No range expansion is implied.",
    "unrecognized": "In manifested requirement/reference spans, an otherwise unrecognized whole token containing -REQ- remains IdentifierShapeConflict; malformed suffixes SF-REQ-011AA and SF-REQ-011-extra are not compounds. Missing/ambiguous definition slots and unknown namespaces remain blocking typed issues. Unknown acceptance suffix or malformed compound remains a typed issue, never a salvaged prefix.",
    "order": "AcceptanceCriterionId, full RequirementIdentifier, fully matched CompoundReference, fully matched PossessiveReference, then typed failure. Category recognition confers no source authority.",
    "possessive_reference": "Reference spans recognize a full RequirementIdentifier followed by ASCII apostrophe-s or U+2019-s as PossessiveReference (for example SF-REQ-007's). Retain the raw expression and the exact parent requirement reference; this named whole-expression production is not arbitrary suffix stripping. Definition slots reject it as WRONG_IDENTIFIER_KIND. Other apostrophe suffixes are not accepted."
  },
  "historical_fixture_manifest": {
    "name": "POSTW1-011-HISTORICAL-CORPUS-R2",
    "artifact": "docs/evidence/wave2-design-contracts.json#/contracts/0/identifier_contract/historical_fixture_manifest",
    "repository": "local AlienIntent Git object database",
    "revision": "d83e87e6f2bb4ff90ff4f4f0e3940582f8d5c998",
    "namespace": "SF; regression observation only, no production authority binding",
    "access_label": "repository-local",
    "origin": "docs/operations/post-wave1-program/prework/POSTW1-SPECIFY-008-inputs.json#/requirement_register and derived_at_head",
    "status": "R2 explicitly reconstructed fixture manifest, not a claim that Phase 8 published this manifest. Reproduces the three historical parser forms and their recorded 56/53 expectations. Other decision wording is reference-only for this fixture; this is not a present-day verdict on definition authority.",
    "expected": {
      "referenced_ids": [
        "SF-REQ-001",
        "SF-REQ-002",
        "SF-REQ-003",
        "SF-REQ-004",
        "SF-REQ-005",
        "SF-REQ-006",
        "SF-REQ-007",
        "SF-REQ-008",
        "SF-REQ-009",
        "SF-REQ-010",
        "SF-REQ-011",
        "SF-REQ-012",
        "SF-REQ-013",
        "SF-REQ-014",
        "SF-REQ-015",
        "SF-REQ-016",
        "SF-REQ-017",
        "SF-REQ-018",
        "SF-REQ-019",
        "SF-REQ-020",
        "SF-REQ-021",
        "SF-REQ-022",
        "SF-REQ-023",
        "SF-REQ-024",
        "SF-REQ-025",
        "SF-REQ-026",
        "SF-REQ-027",
        "SF-REQ-028",
        "SF-REQ-029",
        "SF-REQ-030",
        "SF-REQ-031",
        "SF-REQ-032",
        "SF-REQ-033",
        "SF-REQ-034",
        "SF-REQ-035",
        "SF-REQ-036",
        "SF-REQ-037",
        "SF-REQ-038",
        "SF-REQ-039",
        "SF-REQ-040",
        "SF-REQ-041",
        "SF-REQ-042",
        "SF-REQ-043",
        "SF-REQ-044",
        "SF-REQ-045",
        "SF-REQ-046",
        "SF-REQ-047",
        "SF-REQ-048",
        "SF-REQ-049",
        "SF-REQ-050",
        "SF-REQ-051",
        "SF-REQ-052",
        "SF-REQ-053",
        "SF-REQ-054",
        "SF-REQ-055",
        "SF-REQ-056"
      ],
      "defined_count": 53,
      "undefined": [
        "SF-REQ-048",
        "SF-REQ-052",
        "SF-REQ-056"
      ],
      "retired": [
        "SF-REQ-054"
      ],
      "SF-REQ-050_definition_identity_count": 1
    },
    "entries": [
      {
        "path": "docs/decisions/2026-09-19-software-factory-wave1-founder-decisions.md",
        "sha256": "0f32bc672ee20e8cecdbdf66cbbcd395a6b21f1a7f20a0641029685ee3289c83",
        "reference_span": "whole document; token_kinds applies",
        "definition_slots": []
      },
      {
        "path": "docs/decisions/2026-09-20-candidate-worktree-retention.md",
        "sha256": "75d8eda8a716eab9a9668776c93459514c03058ceb7537177657b0e97b0bdf8d",
        "reference_span": "whole document; token_kinds applies",
        "definition_slots": []
      },
      {
        "path": "docs/decisions/2026-09-20-convergence-assistance-willing-convergence.md",
        "sha256": "dcb2e78c179f85bf1ed20b8240b3c6dd26e3b522a6a769bf6bd1271025d6ccc4",
        "reference_span": "whole document; token_kinds applies",
        "definition_slots": []
      },
      {
        "path": "docs/decisions/2026-09-20-convergent-repair-monotonic-progress.md",
        "sha256": "f7b8c8b0122ebe25b90720a71300f1b1c048cc4b3a6684f43db654c3fefcad87",
        "reference_span": "whole document; token_kinds applies",
        "definition_slots": [
          {
            "line": 86,
            "form": "recorded_as",
            "requirement_id": "SF-REQ-049"
          }
        ]
      },
      {
        "path": "docs/decisions/2026-09-20-design-contract-and-design-verification.md",
        "sha256": "b9c4d00bf50280db41fdd9e3a52fef7ecc55e4fce34dcfd58355c305fd814e49",
        "reference_span": "whole document; token_kinds applies",
        "definition_slots": [
          {
            "line": 5,
            "form": "canonical_requirement",
            "requirement_id": "SF-REQ-051"
          }
        ]
      },
      {
        "path": "docs/decisions/2026-09-20-deterministic-failure-class-promotion.md",
        "sha256": "ae7b77fde421abd707eb359d0829ceb51d1730dd510708715eeb2b24c3fd0f11",
        "reference_span": "whole document; token_kinds applies",
        "definition_slots": [
          {
            "line": 5,
            "form": "canonical_requirement",
            "requirement_id": "SF-REQ-050"
          }
        ]
      },
      {
        "path": "docs/decisions/2026-09-20-evidence-and-intake-ratification.md",
        "sha256": "e2da4f8d98c9f028b87c09f78f78ba87390e43f98bf51c236ddeab7506300fc6",
        "reference_span": "whole document; token_kinds applies",
        "definition_slots": []
      },
      {
        "path": "docs/decisions/2026-09-20-liveness-reconciliation.md",
        "sha256": "cf38a1b481c710b1229e1d24c143439ca3c4115b53f636abc4e0aeee68a1f6e6",
        "reference_span": "whole document; token_kinds applies",
        "definition_slots": []
      },
      {
        "path": "docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md",
        "sha256": "87e820775d5ae42ddba84a402553db8409f47409ad9ab771c469d55f06eeefa9",
        "reference_span": "whole document; token_kinds applies",
        "definition_slots": [
          {
            "line": 5,
            "form": "canonical_requirement",
            "requirement_id": "SF-REQ-053"
          }
        ]
      },
      {
        "path": "docs/decisions/2026-09-20-py04-coordinator-mutation-gate.md",
        "sha256": "4245c33a8c737efc8e93a598b6a7dacda6182c1a2379787e1748237260972fe4",
        "reference_span": "whole document; token_kinds applies",
        "definition_slots": []
      },
      {
        "path": "docs/decisions/2026-09-20-wave1-closure-policy.md",
        "sha256": "7c08593da9a81507e4a1cec80c13389be50d18c3f47330f19ae928f326e30fb0",
        "reference_span": "whole document; token_kinds applies",
        "definition_slots": []
      },
      {
        "path": "docs/decisions/2026-09-20-wave1-execution-decisions.md",
        "sha256": "e94def3936395d3322cfd44b6cede30677e7f3391c7d4db1adba855ac420ad57",
        "reference_span": "whole document; token_kinds applies",
        "definition_slots": []
      },
      {
        "path": "docs/decisions/2026-09-20-wave1-plan-approval-d1-d2.md",
        "sha256": "a818239d9d8da818b92d1ad37e09fef4cbfef73f36e3288ea459c6b63c78b45d",
        "reference_span": "whole document; token_kinds applies",
        "definition_slots": []
      },
      {
        "path": "docs/decisions/2026-09-20-wave1-release-coordinator.md",
        "sha256": "732d71e918c16107f94c7a59ea5cd7aa12de8eaa6dc0b19f0898b9282abbd9fb",
        "reference_span": "whole document; token_kinds applies",
        "definition_slots": []
      },
      {
        "path": "docs/decisions/2026-09-21-biu-execution-cycle-counter.md",
        "sha256": "a8aea557829dab270fbb89f26dd8836549d6861f838d318ef676b70ccf3e6533",
        "reference_span": "whole document; token_kinds applies",
        "definition_slots": []
      },
      {
        "path": "docs/decisions/2026-09-21-py10-transport-split.md",
        "sha256": "9556450d30168be28975a2820e168b243f25f9a203abb5c0eda2c77bef93d54c",
        "reference_span": "whole document; token_kinds applies",
        "definition_slots": []
      },
      {
        "path": "docs/decisions/alienintent-software-factory-plan.md",
        "sha256": "6207771dadb6d670e0fb235b68f8df3e726dd04737366198520b4c4e852015bc",
        "reference_span": "whole document; token_kinds applies",
        "definition_slots": [
          {
            "line": 731,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-041"
          },
          {
            "line": 744,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-042"
          },
          {
            "line": 749,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-043"
          },
          {
            "line": 759,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-044"
          },
          {
            "line": 766,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-045"
          },
          {
            "line": 773,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-046"
          },
          {
            "line": 783,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-047"
          },
          {
            "line": 842,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-001"
          },
          {
            "line": 847,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-002"
          },
          {
            "line": 865,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-003"
          },
          {
            "line": 870,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-004"
          },
          {
            "line": 875,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-005"
          },
          {
            "line": 880,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-006"
          },
          {
            "line": 885,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-007"
          },
          {
            "line": 894,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-008"
          },
          {
            "line": 899,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-009"
          },
          {
            "line": 910,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-010"
          },
          {
            "line": 915,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-011"
          },
          {
            "line": 920,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-012"
          },
          {
            "line": 925,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-013"
          },
          {
            "line": 930,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-014"
          },
          {
            "line": 935,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-015"
          },
          {
            "line": 940,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-016"
          },
          {
            "line": 945,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-017"
          },
          {
            "line": 950,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-018"
          },
          {
            "line": 955,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-019"
          },
          {
            "line": 960,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-020"
          },
          {
            "line": 965,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-021"
          },
          {
            "line": 970,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-022"
          },
          {
            "line": 975,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-023"
          },
          {
            "line": 980,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-024"
          },
          {
            "line": 985,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-025"
          },
          {
            "line": 990,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-026"
          },
          {
            "line": 995,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-027"
          },
          {
            "line": 1000,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-028"
          },
          {
            "line": 1005,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-029"
          },
          {
            "line": 1012,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-030"
          },
          {
            "line": 1021,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-054"
          },
          {
            "line": 1027,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-055"
          },
          {
            "line": 1036,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-031"
          },
          {
            "line": 1041,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-032"
          },
          {
            "line": 1046,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-033"
          },
          {
            "line": 1051,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-034"
          },
          {
            "line": 1056,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-035"
          },
          {
            "line": 1061,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-036"
          },
          {
            "line": 1066,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-037"
          },
          {
            "line": 1071,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-038"
          },
          {
            "line": 1076,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-039"
          },
          {
            "line": 1081,
            "form": "factory_plan_heading",
            "requirement_id": "SF-REQ-040"
          }
        ]
      }
    ]
  }
}
```

**Deterministic enforcement.**

- `011-inventory` (BLOCKING, python_unit_integration): Use identifier_contract.historical_fixture_manifest (POSTW1-011-HISTORICAL-CORPUS-R2), asserting exact referenced and definition ID sets, forms and locators, not counts alone. All three definition forms yield baseline 56 references/53 definitions, one 050, retired 054 and unresolved 048/052/056; format aliases retain identity. In each prose form, synthetic fixtures retain SF-REQ-011A, SF-REQ-1000 and authorized TEAM-X-REQ-011 exactly; reject SF-REQ-01, SF-REQ-011AA and SF-REQ-011-extra with UNRECOGNIZED_REQUIREMENT_ID. Unknown namespace has its distinct reason; empty/ambiguous slots retain typed issues. Permuting input order preserves identities. Fixtures are not Product Requirements. Add SF-REQ-053-AC-01, SF-REQ-001/SF-REQ-002, SF-REQ-030/054 and SF-REQ-001–010 in reference spans: exact AcceptanceCriterionId/CompoundReference, zero shape conflicts and zero definitions. The same kinds in a definition slot yield WRONG_IDENTIFIER_KIND. An unmanifested report containing malformed tokens has no effect; manifesting a requirement span containing SF-REQ-011-extra must yield a blocking issue. Recognize SF-REQ-007's and SF-REQ-018’s as PossessiveReference in reference spans only; Markdown [SF-REQ-007](target) contributes its full label token, not URL punctuation. Unknown suffixes still fail. Proven-red obligation: Disable either prose parser and require count/identity assertion failure; introduce conflicting definitions and require no effective definition. Replace full-token grammar with SF-REQ-[0-9]{3}, strip a suffix, or silently drop a malformed token separately: exact identity/typed-reason assertions fail even if baseline 56/53 counts pass. Misclassify an AC as a requirement, drop compound operands, scan an excluded document, or suppress an in-scope malformed token: the corresponding category/scope/exact-ledger assertion must fail. Fixture-source digest mismatch must hold rather than pass by count.

Detailed vocabulary, persistence, concurrency, security, non-goals and exact acceptance traces remain in this requirement’s JSON contract. Shared storage, authority and dependency-direction rules apply in full.

## SF-REQ-012 — Requirements ambiguity detection

Ambiguity application owns findings; existing Founder/decision authority alone resolves product meaning.

**Authority:** DESIGN_CANDIDATE; independent Phase 10 verification outstanding Gap references: none newly recorded.

InspectionReport records required-field presence, contradictions already evidenced by source records, finding IDs, source spans, required decision actor, affected requirement/dependent references, and OPEN/RESOLVED/STALE history.

**Ports and wiring.** AmbiguityInspection.inspect(inventory_revision, supplied_semantic_findings) -> InspectionReport; resolve(finding_id, DecisionRecord, expected_version) -> Resolution | Hold. DecisionResolution port validates actor, authority scope, source revision and decision reference through the existing control_plane DecisionInbox/DecisionAdmission path; it does not mint approvals. Versioned inventory reader uses 011; proposed context_assembly/adapters/decision_resolution.py translates existing DecisionRecord into a source-bound resolution. A semantic-review input adapter imports attributable review findings as observations; no model is invoked by mechanical inspection. composition/upstream_profile.py wires Inventory -> AmbiguityInspection -> DecisionResolution adapter -> existing DecisionInbox; inject the same store/profile and EvidenceRepository. Compilation receives InspectionReport, never a boolean manufactured by the CLI.

**State changes and identity.** Mechanical missing intent/scope/authority/acceptance/dependency meaning creates OPEN finding and branch-local hold. Authorized answer at matching revision appends RESOLVED only for its finding; mismatched answer stays evidence but does not clear it. Changed relevant input makes prior resolution STALE; material ambiguity discovered independently reopens the affected preparation hold. Finding identity is SHA-256(project, requirement revision, rule code, sorted source locators); semantic findings additionally include immutable reviewer finding reference. Resolution identity hashes finding, decision revision and actor.

**Failure and recovery.** Unattributed answer -> AUTHORITY_HOLD. Stale answer -> REVISION_HOLD. Incomplete inspection -> UNVERIFIED, not complete. No decision channel -> durable OPEN finding; unrelated requirements remain inspectable. Replay mechanical inspection idempotently; reattach resolutions only by exact revision and authority match. Resuming preparation is a new validated operation and launches no worker.

**Operator and evidence.** Proposed upstream questions list/show and resolve commands; resolve requires actor, authority ref, finding ID, input revision and expected version. Existing Decision Inbox remains decision authority. Finding, source span, question, missing decision, answer reference/actor/revision, affected work and retained prior status. inspection.completed and finding.opened/resolved/stale include IDs and reason codes; report holds by affected branch, with semantic-review status distinct from mechanical completeness.

**Fixed choices.** Mechanical completeness is not exhaustive natural-language ambiguity detection. Independent semantic review may add findings but may not silently rewrite intent.

**Deterministic enforcement.**

- `012-local-holds` (BLOCKING, python_unit_integration): Each missing-field fixture creates a source-bound local hold; unrelated complete input remains eligible; only matching attributed answer resolves. Proven-red obligation: Remove revision or authority matching, inject stale/unattributed answer, require hold assertion failure.

Detailed vocabulary, persistence, concurrency, security, non-goals and exact acceptance traces remain in this requirement’s JSON contract. Shared storage, authority and dependency-direction rules apply in full.

## SF-REQ-013 — Requirements to BIU compilation: initial decomposition

context_assembly owns the candidate compilation representation and validation design. Decomposition-source authority is explicitly unclosed in R1-GAP-013-ALLOCATION; no upstream allocation producer is assumed.

**Authority:** DESIGN_CANDIDATE_WITH_SPECIFY_HOLD; independent repair review outstanding; affected capability is not implementation-ready Gap references: R1-GAP-013-ALLOCATION.

Compilation candidate records input digest, derived allocation revision, per-unit BiuContract content_digest, obligation coverage, edge/predicate set, validation report, prior candidate and INITIAL_ONLY mode.

**Ports and wiring.** InitialCompilation.compile(inventory, inspection, verified_design, proof_plan, authority_limits) -> CompilationCandidate | CompilationHold. Until R1-GAP-013-ALLOCATION is resolved, return AUTHORITY_GAP_HOLD with the gap reference; no successful initial decomposition is claimed. Candidate allocation representation (output/internal, not prerequisite input): stable unit_key, BIU identity, obligation IDs with scope extents, baseline/repository refs, fixed decisions, capabilities, budgets, dependency edges/predicates, custody/closure/release/escalation duties. These completeness constraints do not define or authorize the missing decomposition/identity derivation. Output contains execution_coordination.domain.contract.BiuContract canonical payloads, exact requirement/design/obligation revisions, DAG and coverage manifest. SF-REQ-015 alone consumes it for lint/assessment. Proposed context_assembly/adapters/compilation_repository.py persists immutable candidate manifest and CAS admission pointer. Use existing BiuContract/BudgetPolicy constructors for SF-REQ-010 validation; source links are stored in manifest and existing authority_references/fixed_decisions, without changing worker serialization here. composition/upstream_profile.py injects 011 inventory, 012 report, 051 applicability and 014 proof plan into InitialCompilation; it passes candidate to 015 lint only. execution_coordination retains release and lifecycle ownership. Gap-open composition returns AUTHORITY_GAP_HOLD; wiring validation helpers is not a complete initial compiler.

**State changes and identity.** R1-GAP-013-ALLOCATION open -> AUTHORITY_GAP_HOLD before proposal creation; validation of a hand-authored candidate cannot count as initial compilation acceptance. PINNED -> VALIDATED_PROPOSAL only after complete coverage, passing current independent design verification, resolved questions and valid DAG. Missing field/edge/authority or incompatible fixed decision -> HELD with no assessed/released state. Existing approved decomposition identity -> OUT_OF_SCOPE_REPLAN; no replacement or mutation. Revised still-unapproved input generates distinct candidate revision. Preserve exact supplied source and existing BIU identities; never derive identities from sorting. Candidate digest binds normalized inputs and derived allocation. New unit/BIU identity assignment constraints are part of R1-GAP-013-ALLOCATION returned to SPECIFY, not implementer freedom; compiler never allocates Issues. No new identity is emitted while that gap is open.

**Failure and recovery.** Cycle -> report concrete cycle edges. Missing endpoint/predicate -> refuse that graph. Unmapped obligation or widened budget/capability -> reject candidate admission. No approved verified design -> design hold. Approved decomposition rewrite -> pending-amendment boundary. Regenerate the same proposal from immutable input; reconcile partial artifact writes by digest before updating pointer. Reassess changed proposals. Never modify approved BIUs during recovery.

**Operator and evidence.** Proposed upstream compile --inputs <manifest> produces a local proposal/coverage report. It has no Issue creation, status mutation or launch operation. Coverage maps every acceptance/proof obligation to explicit unit extents; DAG validation and bounds comparison retained beside exact contract payloads and source refs. compilation.proposed/held reports unmapped IDs, rejected edges, decision conflicts and candidate digest; counts allocation coverage separately from verified satisfaction.

**Fixed choices.** Supersedes the mandatory external-allocation design choice. On current evidence SF-REQ-013 must derive initial decomposition from requirements/design; return the allocation-source question and constraints to SPECIFY via R1-GAP-013-ALLOCATION. A validator-only implementation does not satisfy this requirement. No new planner owner or requirement is invented. SF-REQ-013 pending split/replan amendment (POSTW1-DECIDE-005A/-007A) is expressly excluded, not a dependency of initial compilation.

**Deterministic enforcement.**

- `013-graph-coverage` (BLOCKING, python_unit_integration): BiuContract validation plus total obligation coverage and deterministic DAG check precede proposal admission. With R1-GAP-013-ALLOCATION open, composed compilation must return AUTHORITY_GAP_HOLD and no candidate; graph validators remain separately testable. Proven-red obligation: Drop an obligation, edge endpoint or fixed decision independently; each named refusal must fire. Bypass the authority-gap gate with a complete hand-authored allocation and require the no-candidate assertion to fail.

- `013-dependency-authority` (BLOCKING, python_unit_integration / LRN-016): Reuse dependency-authority promotion at actual contract/admission boundary; open DONE predecessor remains satisfied; closed nonterminal predecessor does not. Proven-red obligation: Mutate to trust Issue closure or omit a declared edge and fail the targeted eligibility assertion.

Detailed vocabulary, persistence, concurrency, security, non-goals and exact acceptance traces remain in this requirement’s JSON contract. Shared storage, authority and dependency-direction rules apply in full.

## SF-REQ-014 — Mechanical verification obligations before implementation

ProofObligation domain owns predicate/evidence plans; reviewers own judgment predicates and premise feasibility.

**Authority:** DESIGN_CANDIDATE; independent Phase 10 verification outstanding Gap references: none newly recorded.

ProofPlan contains stable requirement AC/obligation IDs, predicate kind, input fixture, expected result, observable endpoint, execution command reference, evidence schema, named guard/mutation, platform-premise references, reviewer role for judgment, and preserved prior/replacement obligations.

**Ports and wiring.** ProofPlanning.derive(requirement_revisions, verified_design, approved_predicate_mapping) -> ProofPlan | InfeasibleProof. ProofEvidence.record(obligation_ref, candidate_ref, fixture_digest, invocation, expected, observed, exit_code) -> ObservationRef. PremiseEvidence port reads pinned consumer/platform capability evidence from installation doctor evidence; no credential probe is implicit in plan derivation. Proposed evidence_learning/adapters/proof_repository.py binds EvidenceRepository and operational pointer. composition/upstream_profile constructs the PremiseEvidence bridge around explicitly authorized installation/application/doctor.py and composition/doctor_probes.py callables. evidence_learning adapters receive typed observations through their own port and import neither installation nor composition; local fixture adapters supply recorded observations. composition/upstream_profile.py wires ProofPlanning to typed 016 EvidenceRepository and 051 premise/applicability inputs before 013 compilation. Existing verification runners consume the plan; no second test runner service.

**State changes and identity.** DRAFT -> FEASIBLE_PLAN only when every AC maps to mechanical or judgment obligation and premise evidence is applicable. Mechanical observations -> evaluation candidate; only authorized verdict admission yields proven. Repair appends candidate-bound replay and explicit authorized supersession; missing proof remains a hold. Infeasible premise returns to source authority. Obligation identity uses requirement ID plus supplied AC ID and stable predicate key; revision hashes predicate/expected inputs. Evidence identity adds candidate digest, fixture digest and invocation, never test filename alone.

**Failure and recovery.** Circular oracle derived only from implementation -> refuse plan. Unapplied mutation, timeout or unrelated exception -> not a qualified kill. Unachievable credential-denial premise -> infeasible proof, not waiver. Dropped/skipped prior obligation -> repair evidence failure. Re-run preserved probes against the new candidate; retain all original evidence. Plan correction requires authoritative predicate revision plus replacement proof; infrastructure failure leaves outcome UNVERIFIED.

**Operator and evidence.** Proposed upstream proof show/check exposes predicate mapping and feasibility failures. Human-judgment items name authority and inspection inputs; no generic green aggregate hides them. Per obligation retain controlled input, expected/actual result, exit code, candidate and harness digests, mutation application count, targeted assertion, restored run; judgment carries actor, input refs and decision. proof.plan.held / proof.observed / proof.superseded with obligation and candidate IDs. Report qualified kills separately from harness failures and advisory sequencing diagnostics.

**Fixed choices.** For platform isolation pin four observables: positive target access; configured profile/resource scoping; rejected out-of-scope application request; unchanged outside-state readback. Do not require impossible platform credential denial. Proof plans are derived before implementation; semantic predicate mappings are authority-reviewed input, not inferred from passing source code.

**Deterministic enforcement.**

- `014-discrimination` (BLOCKING, mutation_gate / LRN-001): Reuse approved obligation/guard qualified intact-red-restored battery; constant assertions and untriggered guards are refused. Proven-red obligation: Show unconditional success, zero-application and overdetermined fixtures fail battery evaluation.

- `014-composition` (BLOCKING, python_unit_integration / LRN-002): Reuse named CLI/composition reachability probes with real temporary SQLite, required operation and typed failure postconditions. Proven-red obligation: Disconnect the approved caller while domain tests remain green; composed assertion must fail.

- `014-proof-order` (ADVISORY, evidence_consistency / LRN-003): Reuse advisory attributable harness/red ancestry diagnostics, never infer widening from timestamps. Proven-red obligation: Out-of-order/missing-path evidence produces named advisory diagnostic, ordered control is clean.

- `014-repair-preservation` (BLOCKING, evidence_consistency / LRN-004): Reuse stable prior-obligation replay and authorized supersession comparison. Proven-red obligation: Drop, skip or fail prior B proof; reject each unless authorized replacement and passing replacement proof exist.

Detailed vocabulary, persistence, concurrency, security, non-goals and exact acceptance traces remain in this requirement’s JSON contract. Shared storage, authority and dependency-direction rules apply in full.

## SF-REQ-015 — BIU lint/readiness and Agent-Ready process hardening

Readiness consumer owns lint/applicability/hold handling. Agent-Ready remains assessment authority; G1/G2 ownership is not assigned by this design.

**Authority:** DESIGN_CANDIDATE; independent Phase 10 verification outstanding Gap references: none newly recorded.

Immutable AssessmentAttempt includes attempt ID, raw digest, authority/provider/invocation IDs, input fingerprint, predecessor assessment ref, observed disposition or failure, and lint report. Current applicability is a separate versioned pointer, never an edit to an old assessment.

**Ports and wiring.** ReadinessAdmission.lint(candidate, design_applicability, proof_plan, dependency_snapshot) -> LintReport. DesignApplicability is a leaf context_assembly.domain value under shared_contracts.context_dependency_direction; no upstream application import. AssessmentConsumer.observe(raw_artifact, attempt_metadata, recognized_shape) -> SemanticAssessment | AttemptFailure; consume(assessment, current_input_fingerprint) -> ReadinessEligibility | Hold. This is an internal consumer contract, not a new Agent-Ready wire schema. AssessmentAuthority is an injected boundary accepting a pinned assessment request and returning raw bytes plus invocation metadata; transport/schema implementation is blocked on POSTW1-DECIDE-004A G1/G2 assignment. Proposed execution_coordination/adapters/assessment_consumer.py reads retained direct objects and known MCP envelopes for consumer tests; raw evidence is stored byte-for-byte privately before normalization. Production assessment adapter remains unbound until G1/G2 owner assignment and verified provider contract. The missing adapter returns explicit OWNER_ASSIGNMENT_HOLD; no stub READY or replacement assessment engine. composition/upstream_profile.py wires lint and retained-evidence consumer into readiness admission. Live profile composition must fail closed when AssessmentAuthority is unbound. FactoryCoordinator release consumes applicable evidence through existing admission; it never creates READY.

**State changes and identity.** Lint failure -> HOLD without invoking assessment. READY plus matching inputs -> ELIGIBLE_FOR_SEPARATE_RELEASE_CHECKS; BLOCKED -> prerequisite hold; NEEDS_CLARIFICATION -> attributed-answer hold; SPLIT_RECOMMENDED -> planning-decision hold. Timeout/provider error/no terminal result/unknown or conflicting payload -> ATTEMPT_FAILURE and hold. Material input change invalidates applicability; fresh reassessment links predecessor. Clearing a blocker does not rewrite its outcome. Input fingerprint hashes BiuContract digest, exact baseline, governing decisions, prerequisites and verified design refs. Attempt UUID is assigned and persisted before invocation; replay retains it; a new authorized assessment uses a new UUID and predecessor link.

**Failure and recovery.** MCP error or conflicting direct/text/structured semantics -> attempt failure. No configured assessment contract or ownership -> hold. READY from stale revision -> inapplicable. Zero exit without semantic result -> failure, not readiness. Recover attempt from immutable raw evidence and original metadata. Unknown invocation completion stays held pending readback or separately authorized fresh attempt within existing budget. Historical PY-10 assessment Git blobs remain retrievable by revision.

**Operator and evidence.** Proposed upstream readiness show/lint/observe surfaces attempt lineage and four handling outcomes. Assessment invocation/schema migration stays unavailable until G1/G2 decisions; release remains existing control-plane authority. Raw envelope, parsed observation, all supplied disposition values, input fingerprint, failure reason, predecessor and independent release record; historical sequence BLOCKED -> SPLIT_RECOMMENDED -> fresh READY retained without coercion claim. readiness.lint_held / attempt_failed / observed / stale reports exact attempt and revision; counts READY semantics separately from released work.

**Fixed choices.** Known MCP parsing: isError=true is failure; collect structuredContent disposition and parseable JSON text-content dispositions. Require at least one recognized terminal value and agreement among every supplied value. Unknown/malformed/conflicting purported result is failure. Preserve wrappers. This fixes intended consumer semantics only. No external versioned serialization, implementation maintainer or CLI is invented; implementation/migration of that boundary requires G1/G2 authority.

**Deterministic enforcement.**

- `015-envelope-applicability` (BLOCKING, python_unit_integration): Equivalent retained direct and known MCP shapes have identical consumer handling; all non-READY/failure/stale cases hold. Proven-red obligation: Use top-level-only parsing, trust exit zero or overwrite prior outcome; corresponding fixture must fail.

- `015-composed-authority` (BLOCKING, python_unit_integration / LRN-002): Reuse LRN-002 at the actual live-profile readiness construction/call boundary with local transport and real temporary SQLite. Unbound AssessmentAuthority or a stub lacking assigned G1/G2 authority must refuse construction or return OWNER_ASSIGNMENT_HOLD before assessment/release; a pinned authorized fixture binding reaches the consumer and still checks semantic outcome. Proven-red obligation: Bind a stub that returns READY without G1/G2 authority, then bypass the unbound-authority guard separately: each must fail the expected OWNER_ASSIGNMENT_HOLD/no-release assertion; intact authorized fixture reaches the consumer.

Detailed vocabulary, persistence, concurrency, security, non-goals and exact acceptance traces remain in this requirement’s JSON contract. Shared storage, authority and dependency-direction rules apply in full.

## SF-REQ-016 — Definition / Observation / Verdict separation

Evidence domain owns typed provenance and linkage. execution_coordination/domain/verdict.py retains execution acceptance policy.

**Authority:** DESIGN_CANDIDATE; independent Phase 10 verification outstanding Gap references: none newly recorded.

Immutable schema_version=1 record envelope: kind, project/profile, logical ID, revision, source refs, authority refs where applicable, payload, access label, preceding/superseded refs. Operational applicability/hold pointers are separate from the evidence body.

**Ports and wiring.** EvidenceRepository.put(record) -> EvidenceRef; get(ref, access_scope) -> typed record; records use a discriminated Definition/Observation/Verdict union. EvidenceAdmission.validate(record, authority_snapshot) -> Admissible | Rejected. Definition requires issuer/ref; Observation requires method, input refs, observed value and uncertainty; Verdict requires definition refs, observation refs, evaluator identity/authority, policy revision and outcome. ExecutionVerdict bridge passes only validated definition/observation values to existing evaluate_verdict; generic evidence records cannot directly transition lifecycle. Proposed evidence_learning/adapters/local_evidence_repository.py implements immutable content-addressed local files and sanitized export. Proposed execution_coordination/adapters/evidence_verdict_bridge.py translates neutral typed records to existing EvidenceDefinition/Observation and leaves evaluate_verdict semantics owned by execution_coordination. Proposed composition/evidence_profile.py builds one EvidenceRepository and access policy per profile; upstream_profile and existing offline_profile receive it. Execution acceptance bridge injects existing evaluate_verdict, never a competing policy.

**State changes and identity.** New record -> structurally validated -> authority/link validated -> admissible typed record. Observation conflict appends competing record and marks impacted applicability held; never overwrites a definition. Verdict with mismatched revision or missing evidence remains UNVERIFIED/refused at acceptance. Authorized supersession appends links. EvidenceRef uses SHA-256 of canonical envelope without self-digest. Logical IDs persist across revisions; source observations retain original invocation/event identity. No role conversion by changing a label on the same digest.

**Failure and recovery.** Observation submitted as Definition without normative authority -> reject. Missing artifact/hash mismatch -> UNVERIFIED and no PASS. Unknown numeric observation -> null plus reason, never zero. Invalid evaluator/source attribution -> verdict refusal. Validate object digest on read; rehydrate operational pointers from retained objects and receipt history. Missing evidence requires recovery from exact pinned source or fresh observation, never reconstruction of a measurement by inference.

**Operator and evidence.** Proposed evidence show/trace/export prints role and provenance chain explicitly; status never collapses observation into verdict. Retain role, exact definition/evidence/policy links, observations in source sequence, conflicts, rejection reasons and evaluator authorization. evidence.admitted/rejected and verdict.inapplicable use typed record IDs/reasons; no secret content or private reasoning in logs.

**Fixed choices.** JSON scalar types and explicit null/uncertainty distinguish unavailable measurements from zero. No learning promotion or RAI wiring; definitions cannot be authored by evidence ingestion.

**Deterministic enforcement.**

- `016-role-boundary` (BLOCKING, python_unit_integration): An observed test pass and worker success claim cannot produce authorized PASS alone; revision and evaluator links required. Proven-red obligation: Remove kind/authority/revision validation individually; injected role promotion or stale evidence must fail acceptance assertion.

Detailed vocabulary, persistence, concurrency, security, non-goals and exact acceptance traces remain in this requirement’s JSON contract. Shared storage, authority and dependency-direction rules apply in full.

## SF-REQ-039 — Fake-agent / offline factory proof

Offline proof composition assembles the real execution_coordination kernel; scripts own external outcomes only.

**Authority:** DESIGN_CANDIDATE_WITH_SPECIFY_HOLD; independent repair review outstanding; affected capability is not implementation-ready Gap references: R1-GAP-039-ORCHESTRATION, R1-GAP-039-REAL-OUTCOME.

Scenario manifest includes authorized BiuContract, exact expected transitions, ordered events, scripted outcome per role/attempt, fake clock and seed. Durable fixture state contains real operational store, local Work Management receipts and worker outcome journal.

**Ports and wiring.** Reuse WorkManagement, WorkerProvider, SourceControl, WorkspaceManager and OperationalStore ports. Scripted WorkerProvider.start/read_back/cancel retains outcome by invocation ID. ScenarioRunner.run(scenario_manifest, injected_clock, profile) -> ordered observations/effect receipts and terminal/hold snapshot. It may deliver inputs but cannot set lifecycle stage. Proposed OutcomeEvidencePort.get(correlation_id) -> immutable RoleOutcomeRecord | Missing. RoleOutcomeRecord fields: role, invocation ID, attempt, exact contract/candidate refs, findings, observation refs, outcome kind, terminal flag, and closure receipts. WorkerOutcome stays compatible; it is insufficient alone for role-specific evidence. Conditional target only after R1-GAP-039-ORCHESTRATION and R1-GAP-039-REAL-OUTCOME are resolved: the application validates the sidecar before transition. A scripted adapter may model it, but no real-path producer is assigned or presumed here. Extend existing composition/offline_profile.py; use real SQLiteOperationalStore, local_artifact_custody and Git source-control/worktree adapters against disposable local bare remote and worktrees. Proposed invocation_runtime/adapters/scripted_worker.py and execution_coordination/adapters/local_work_management.py substitute provider and Work Management transport only. The verifier uses a distinct invocation/process and freshly retrieved candidate/worktree. OfflineProfile owns scenario adapter construction around the existing FactoryCoordinator. _completed_for_outcome currently collapses success through verify/review/accept/close; the proposed separate-role path is blocked by R1-GAP-039-ORCHESTRATION and R1-GAP-039-REAL-OUTCOME. Current-interface fixtures remain valid, but full multi-role acceptance is blocked, not passed by a parallel mock. ScenarioRunner may not change lifecycle stage.

**State changes and identity.** Seed authorized contract -> normal release admission -> producer candidate publication/readback -> VERIFY -> independent scripted verifier result -> REVIEW/ACCEPT policy -> required closure -> DONE. Verifier rejection follows canonical rework transition with findings; subsequent producer uses a distinct authorized attempt. Missing result, authority, custody or judgment-blocked outcome produces existing hold/attention, never a runner-forced transition. Scenario digest plus fixed seed determines fixture identity; actual role-specific invocation IDs remain distinct. Effect identities are the same canonical identities as production, not test-only dedupe keys. Comparison normalizes only declared incidental paths/times, never correlation or authority.

**Failure and recovery.** Network/provider access attempted -> test failure. Script exits zero without result/candidate -> hold. Wrong/unpublished candidate -> custody refusal. Missing fresh verifier or script directly changes stage -> scenario invalid. Kill only the disposable fixture process at named before/after-intent boundaries, reopen the real store and worker journal, and compare authorized action/lifecycle/effect sets. Unknown external effects remain parked.

**Operator and evidence.** Proposed offline scenario <manifest> command returns nonzero for assertion/harness failure and leaves evidence path. Existing production commands are not driven during tests. Scenario manifest, substituted-boundary list, ordered domain transitions, actual worker invocations, candidate branch/SHA and retrieved identity, effect/outcome readbacks, restart comparison and zero-provider-call counter. Run report separates scenario PASS, negative-control qualified failure, substituted boundaries and live-proof NOT_ESTABLISHED. Unexpected network call count must be zero.

**Fixed choices.** The following multi-role target decisions are conditional design constraints, not implementation authorization. SPECIFY must first identify existing requirement authority and owners for orchestration and real-path outcome emission. Do not replace FactoryCoordinator._completed_for_outcome under SF-REQ-039 alone; current worker/lifecycle contracts remain untouched. Closure records only actions actually performed/read back by local adapters; never populate all required_closure_actions merely because producer succeeded. Offline tests exercise the production orchestration path through composition, not a second mocked lifecycle. A composed role router resolves PRODUCER/VERIFIER/CLOSURE from the durable invocation record keyed by correlation_id and injects the role-specific worker implementation. Existing WorkerProvider signatures stay intact; verifier output must reference retrieved candidate and independent invocation. Missing RoleOutcomeRecord holds even when WorkerOutcome.kind is success. On verifier rejection, persist finding refs and invoke existing transition(action=rework) at the current lifecycle version; enforce remaining authorized attempts/budget before producer allocation. REVIEW evaluates exactly required trusted evidence through evaluate_verdict. ACCEPT performs each required closure action and consumes its receipt; no synthesized closure evidence. Before any shared-kernel change lands, both sandbox_run_profile and github_profile constructors must validate assigned authority plus real OutcomeEvidencePort binding for multi-role mode. Missing binding/authority returns ROLE_OUTCOME_BINDING_HOLD before any worker launch, not after every producer success. Existing unmodified profiles are not claimed to enforce this future gate. No mode may claim 039 multi-role proof by falling back to the current success-collapse path. After activation, a missing/miscorrelated sidecar holds the affected transition even on WorkerOutcome success.

**Deterministic enforcement.**

- `039-composed-lifecycle` (BLOCKING, python_unit_integration / LRN-002): Reuse LRN-002 composed-path promotion for OfflineProfile with actual store/adapters and fresh verifier; cover success, rejection, result/custody gaps, duplicate/restart, judgment hold. Full multi-role proof remains blocked on both 039 gaps. After resolution, exercise actual sandbox/github profile constructors with local transport substitutes: absent authority/real outcome binding holds before launch; bound real-worker adapter persists/readbacks correctly correlated RoleOutcomeRecord through success, verifier rejection and restart. Offline scripted records alone cannot discharge the real-path probe. Proven-red obligation: Disconnect verifier invocation or custody readback while unit tests stay green; targeted end-to-end assertion must fail. Bypass construction binding validation or disconnect real-worker record emission independently; pre-launch refusal or correlated real-path outcome assertion must fail.

Detailed vocabulary, persistence, concurrency, security, non-goals and exact acceptance traces remain in this requirement’s JSON contract. Shared storage, authority and dependency-direction rules apply in full.

## SF-REQ-051 — Design Contract and Design Verification

DesignAdmission owns contract completeness and applicability; independent architecture reviewer owns Design Verification judgment.

**Authority:** DESIGN_CANDIDATE_WITH_FOUNDER_HOLD; normative direction unresolved, independent review outstanding. Gap references: R2-GAP-051-EDGE-AUTHORITY.

Design record includes decisions, interfaces, ownership, trust/persistence/recovery constraints, bounded local freedoms and requirements; mechanical and independent review artifacts are separate objects. Applicability state is CANDIDATE, MECHANICALLY_HELD, REVIEW_REQUIRED, VERIFIED or STALE, solely internal semantic gate state.

**Ports and wiring.** DesignAdmission.inspect(contract_ref, requirement_refs, architecture_baseline, interface_manifest, premise_evidence) -> MechanicalReport. DesignAdmission.record_review(design_ref, mechanical_report, review_record, expected_version) -> Applicability | Hold; review_record includes reviewer actor/invocation, producer actor/invocation, reviewed refs, findings, decision and authority. DesignApplicability.check(design_ref, current_revision_vector) -> CurrentVerified | Held | Stale, consumed by 013 and 015. Proposed context_assembly/adapters/design_repository.py uses EvidenceRepository and operational CAS pointer. Read-only architecture/interface adapters load pinned ADR/architecture/EOS references and mechanical results. Reviewer input adapter stores an external fresh reviewer verdict; it does not call the author as reviewer. composition/upstream_profile.py binds DesignAdmission, EvidenceRepository and authority snapshot reader; outputs feed both compiler and readiness consumer so neither can bypass design gate. This phase writes contract candidates only, no review-record import.

**State changes and identity.** Contract complete and compatible -> REVIEW_REQUIRED after mechanical evidence. Missing material decision, authority or infeasible premise -> HELD; return product questions to SPECIFY. Fresh authorized independent review of exact design/checks -> VERIFIED only if no blocking findings. Any required requirement/design/baseline/decision revision change -> STALE downstream; prior verdict retained. Design identity is requirement-set key plus canonical content digest; review identity binds design digest, mechanical report digest and independent actor/invocation. Current applicability includes exact approved architecture/EOS revision, never document title only.

**Failure and recovery.** Self-review/shared producer invocation -> refuse verification admission. Mechanically consistent impossible capability premise -> review rejection. Missing approved EOS/architecture baseline -> explicit conformity hold, not inferred conformance. Unresolved API/persistence/security decision -> design hold. Retain old review; repair produces new design digest and reruns affected mechanical checks plus fresh independent review. Material authority conflict cannot be settled by the checker.

**Operator and evidence.** Proposed upstream design inspect/show and review-record import; import checks identity and applicability but never generates approval. This artifact remains unverified until a separate Phase 10 actor reviews it. Requirement/design refs, interface manifest with producer/consumer ownership, fixed decision inventory, platform capability evidence, mechanical output, reviewer independence/authority and finding disposition. design.mechanical_held / review_required / verified / stale shows input digests and exact refusal; no Project DESIGN status or transition is emitted.

**Fixed choices.** Existing architecture fitness checks are necessary but cannot certify premise truth or semantic compatibility; independent judgment remains required. No new visible lifecycle state, service or approval lane; internal states implement SWF-25 semantic gates within SPECIFY/PLAN.

**Deterministic enforcement.**

- `051-architecture-boundary` (BLOCKING, architecture_fitness): Apply shared_contracts.context_dependency_direction.fitness: run existing repository-wide architecture checks and composed port compatibility probes; return ARCHITECTURE_AUTHORITY_HOLD for direction-dependent admission while R2-GAP-051-EDGE-AUTHORITY is open. observed_edges is descriptive, never a permission table. Do not implement the withdrawn R1 policy against production. Proven-red obligation: Independently bypass the open-authority hold and require refusal assertion failure; treating observed_edges as approved policy must fail. Existing forbidden adapter/vendor import and incompatible consumer input controls still fail. Retain the R1 direction fixtures conditionally after Founder disposition and reviewed scope: execution_coordination -> context_assembly.application, evidence_learning -> installation, evidence_learning -> composition and reciprocal leaf cycle negative controls; execution_coordination -> context_assembly.domain DesignApplicability and composition-owned PremiseEvidence bridge positive controls. These conditional fixtures are not currently runnable production conformance obligations.

- `051-review-applicability` (BLOCKING, python_unit_integration): Require fresh independent review and exact revision vector for downstream compilation/readiness. Proven-red obligation: Replay self-review or stale design review and require downstream hold; conforming independent control passes.

Detailed vocabulary, persistence, concurrency, security, non-goals and exact acceptance traces remain in this requirement’s JSON contract. Shared storage, authority and dependency-direction rules apply in full.

## SF-REQ-053 — Persistent control plane and bounded coordinator episodes

Persistent control-plane application owns episodes/attention; context_assembly builds context, execution_coordination alone owns lifecycle and release.

**Authority:** DESIGN_CANDIDATE_WITH_SPECIFY_HOLD; independent repair review outstanding; affected capability is not implementation-ready Gap references: R1-GAP-MONITOR-HOST.

Episode aggregate: objective, authorized BIU, epoch, ACTIVE/ENDED, start time, tenure policy digest, limits/usage, input version vector, permitted/prohibited commands and end cause. Attention aggregate: stable origin event/outcome, item kind, PENDING/SEEN/RESOLVED, required authority, notification attempts, consumer receipts, resolution refs; every change appended to immutable history.

**Ports and wiring.** EpisodeControl.begin(objective, authority_ref, state_vector, tenure_policy, budget) -> EpisodeContext | Hold; submit(episode_id, epoch, expected_vector, proposal) -> admitted command | stale/authority hold; end(episode_id,cause) -> receipt. AttentionPort.ensure(event_identity, work_ref, kind, authority_needed) -> AttentionRef; seen(item,actor) records delivery only; resolve(item,resolving_decision,expected_version) validates applicable authority. ContextAssembler.reconstruct(snapshot_manifest) -> context plus deterministic authorized_next_action_set/blocked_set; reuse existing DecisionInbox for HumanDecision, never merge queues. AttentionNotifier.notify(item_ref) -> delivery attempt; activation is a separate port requiring explicit policy authority, unbound by default. Use shared_contracts.atomic_fencing_extension for atomic vector/fence/intent admission; read-then-commit of several independent aggregates is insufficient. Optional ContextUsageObservation.read(invocation_id, check_id) -> Usage(used, limit, observed_at, invocation_id, check_id) | Unavailable. Composition declares UNBOUND or BOUND explicitly. This port consumes already available same-invocation observations only; it creates no provider normalization capability. ContradictionObservation.record(episode_id, epoch, state_vector, actor, authority_ref, conflicting_refs, rationale) -> AcceptedContradiction | InvalidJudgment. Existing authorized operator input supplies the judgment; no model prose classifier infers contradictions. MonitorHealth.read(profile) -> health record | Unavailable under shared_contracts.monitor_liveness; tick/scan progress writes use existing store CAS and preserve instance/generation identity. Proposed control_plane/adapters/episode_repository.py and attention_repository.py reuse OperationalStore plus EvidenceRepository. Notification adapter stores attempt before delivery and correlated consumer receipt afterwards. Existing DecisionNotifier behavior is reused for decisions, with a separate attention payload adapter rather than pretending attention is HumanDecisionRequired. Context assembly reads pinned authoritative records and observation summaries only. A read-only bootstrap-import adapter stages checkpoint/attention records for migration comparison. Proposed composition/control_plane_profile.py constructs persistent monitor, EpisodeControl, Attention service, ContextAssembler and notifier with shared store/evidence/profile. Existing offline_profile injects these for proof. Model invocation is a child capability of explicit activation, never owner of monitor or store. 056 calls AttentionPort; 053 does not require 056 to be operational to handle existing outcomes. Optional ContextUsageObservation is explicitly UNBOUND by default; BOUND requires same-invocation evidence adapter injection. An authenticated existing operator surface supplies contradiction judgments. Persistent host/supervisor assignment is blocked by R1-GAP-MONITOR-HOST; constructing services does not supply operational hosting.

**State changes and identity.** Explicit authorized begin -> ACTIVE new epoch; no observer-triggered model start by default. Terminal outcome, objective/authority change, contradiction, stale vector, exhausted context/age/transition/block limit, provider replacement or explicit end -> ENDED; renewal always new episode/epoch and fresh context. Authorized DONE requiring next judgment or judgment-blocked outcome -> ensure durable PENDING before notify. Seen receipt does not clear blocking suppression; only matching resolution or newer correlated nonjudgment outcome allows reevaluation. Episode UUID plus monotonic per-objective epoch fences old invocations. Attention ID hashes (profile, project/work identity, canonical event/outcome identity, attention kind); never observation time. Bootstrap imports preserve original IDs via immutable one-to-one alias map; product attention and program mailbox have distinct namespaces.

**Failure and recovery.** Stale/expired episode -> reject result without authoritative mutation. Missing context record -> hold reconstruction. Notification failure/no receipt -> item pending, delivery failed/unconfirmed. No activation authority -> notify only. Partial migration -> keep old consumer authoritative; no retirement. After crash end any episode whose liveness cannot be established; successor receives new epoch and reconstructs manifest from durable state. Compare deterministic allowed/blocked action sets and lifecycle, not model wording. Rebuild pending attention from retained origin outcomes if notification crashed; idempotent ensure preserves identity.

**Operator and evidence.** Proposed episodes show/end/start and attention list/show/seen/resolve; writes require actor, authority, expected revision, idempotency key. Persistent monitor lifetime is independent of model invocation. Program mailbox remains a separate operator duty. Context manifest, policy/limits, epoch/version vector, proposed/admitted action IDs, termination cause, reconstruction equivalence, attention history, notification/receipt and resolution attribution. Migration fixture covers pending AND handled items and mailbox responsibilities. episode.started/ended/stale_result; attention.pending/delivery_failed/delivery_unconfirmed/resolved; metrics separate pending work, machine receipt, seen, actual resolution and model activation. Publish shared_contracts.monitor_liveness independently of workload activity; missing/stale health is not quiet success. Live supervision is held by R1-GAP-MONITOR-HOST.

**Fixed choices.** Default tenure policy: one BIU, maximum age 3600 seconds, maximum 32 admitted transitions, maximum blocked duration 300 seconds, accepted contradiction count 1, any relevant state-vector mismatch ends tenure. Default context-usage source is UNBOUND and its numeric threshold is disabled; absence of a binding alone does not terminate every episode. All other tenure limits remain active. If explicitly BOUND, threshold is 0.8 and reaching it ends tenure; unavailable, stale, wrong-invocation or invalid measurements terminate conservatively. Monotonic clock within process; persisted UTC deadline for restart; clock regression holds. Values are versioned composition policy, not authority or increased budget. The 3600 seconds is a proposed configurable design default, not a claim that the bootstrap waiter timeout or historical values are canonical; no empirical derivation or inheritance is asserted. Terminal/objective/authority/provider/model changes and explicit request end immediately. Reaching any limit ends, never silently renews; authorized begin of new epoch retains budget accounting. SF-REQ-008 durability elaboration and SF-REQ-029 provider normalization amendments are excluded. Existing store versions/events suffice; no promise of normalized provider telemetry. POSTW1-DECIDE-006A gates actual bootstrap handoff. Tenure checks run on each result/event and an injected deadline timer independent of the model. Epoch expiry prevents new authority-bearing commands but does not fabricate cancellation of already-admitted workers. Relevant authority/source changes advance a durable applicability revision observed by guarded admission; an external source whose freshness cannot be checked causes a hold. For a BOUND context-usage source only, unknown usage is conservative termination; UNBOUND is explicitly recorded and never represented as zero usage or measured-safe context. Context observation validity is decidable: matching current invocation, finite used >= 0, finite limit > 0, and sample from the current tenure check (request correlation must match); unavailable or prior-check samples end tenure when BOUND. Compare used/limit >= 0.8; no normalization or estimated values. Default UNBOUND policy does not claim telemetry-based context safety. Explicit context-exhausted operator/provider events still end tenure; neither they nor the optional fixture close LRN-023. Contradiction is a judgment obligation owned by the authorized episode operator under the episode authority, not an inferred semantic predicate. The operator names conflicting authoritative facts/actions and records rationale and evidence refs. Mechanically count only AcceptedContradiction for the current episode/epoch/vector with authorized actor and nonempty resolvable conflicting_refs/rationale; one ends tenure. Invalid, stale or unauthorized reports produce InvalidJudgment and cannot act as authoritative termination input. Truth of the contradiction requires operator judgment; fixture automation proves admission and termination, not semantic truth.

**Deterministic enforcement.**

- `053-attention-delivery` (ADVISORY, python_unit_integration / LRN-019): Reuse Phase 3 durable-attention-before-notification and correlated consumer receipt probes, preserving advisory delivery diagnostics. Proven-red obligation: Disconnect attention creation then consumer bridge; fail the corresponding assertion; channel failure preserves item.

- `053-tenure-fence` (BLOCKING, python_unit_integration): Exercise every named termination cause and stale-vector/epoch rejection; replacement reconstructs equal allowed/blocked sets from same snapshot. Include composition with no usage source (other causes still enforce), bound just below/at 0.8, bound unavailable/stale/wrong invocation/invalid limit, and explicit context-exhausted event. For contradiction use accepted operator judgment plus stale/unauthorized/missing-ref controls; assert exact termination/refusal cause. Proven-red obligation: Accept old epoch or omit context item and require stale-write/equivalence assertion failure. Treat UNBOUND as zero or as automatic termination, ignore bound Unavailable, or accept an unauthorized contradiction independently; corresponding policy-state/cause assertions must fail.

Detailed vocabulary, persistence, concurrency, security, non-goals and exact acceptance traces remain in this requirement’s JSON contract. Shared storage, authority and dependency-direction rules apply in full.

## SF-REQ-056 — Canonical actor/effect liveness reconciliation

Liveness reconciliation application proposes missing canonical effects; kernel admission owns authorization and effect execution; control_plane owns attention.

**Authority:** DESIGN_CANDIDATE_WITH_SPECIFY_HOLD; independent repair review outstanding; affected capability is not implementation-ready Gap references: R1-GAP-MONITOR-HOST.

Per active factory aggregate retain lifecycle-entry UTC time/revision, expected effect kind and generation, stable effect identity, reservation owner/fence, invocation correlation, pending/completed/unknown effect status, durable outcome/evidence ref and suppression/resolution ref. Store revisions and lifecycle-entry generation are distinct: observation writes cannot create a new launch generation.

**Ports and wiring.** Liveness.inspect(known_active_snapshot, correlated_effect_snapshot, now, policy) -> NoAction | Gap | Suppressed | EvidenceHold. Liveness.reconcile(gap, expected_version, authority_snapshot) -> existing canonical EffectRef | Hold; use OperationalStore reservation/commit_with_effect/claim_effect/confirm_effect and EffectExecutor readback. EffectObservation port supplies active invocation, reservation, pending/unknown effects and latest correlated durable outcome for the SAME work/lane/generation; unavailable data is a typed failure, not an empty set. AttentionPort.ensure/resolve from 053 supplies judgment records; canonical launch and recovery share one effect identity and admission entrypoint. Use shared_contracts.atomic_fencing_extension at intent, claim and receipt; existing unguarded store methods alone do not satisfy the cross-process fence contract. MonitorHealth.read(profile) -> health record | Unavailable under shared_contracts.monitor_liveness; tick/scan progress writes use existing store CAS and preserve instance/generation identity. Proposed execution_coordination/adapters/liveness_observations.py reads existing store and worker read_back plus exact WorkManagement results, without querying backlog discovery. Extend FactoryCoordinator application dispatch entrypoint to share durable lane/effect identity with reconciler; EffectExecutor executes the admitted intent. Provider readback receipts use existing worker port; lack of trustworthy outcome parks. composition policy supplies positive grace/scan/confirmation durations and injected clock; no shell status toggling adapter. composition/control_plane_profile.py binds Liveness, real store observation adapter, FactoryCoordinator canonical effect admission, EffectExecutor and 053 AttentionPort. It scans only already-known active records. OfflineProfile uses identical services with fake clock/local effects. Ratification flag is validated authority input, never a config boolean that confers authorization. Hosting/supervision remains unassigned under R1-GAP-MONITOR-HOST; the profile constructor is not a supervisor. Publish independent scan progress/health per shared_contracts.monitor_liveness.

**State changes and identity.** IMPLEMENT -> expects producer; VERIFY -> verifier; ACCEPT -> each required outstanding closure effect; REVIEW, terminal or ACCEPT with no outstanding closure -> no launch recovery. Age < G -> NO_ACTION; age >= G and complete absence proof -> GAP. Active/pending/correlated completed/unknown effect -> no new launch; unknown -> hold/readback. Judgment outcome -> durable suppression/attention regardless of age. Seen-only receipt leaves suppression. Valid matching resolution or newer same-lane correlated nonjudgment outcome permits reinspection, never unconditional retry. Authorized gap -> reserve -> re-read evidence/admission -> durable intent -> fenced dispatch -> receipt/readback -> normal kernel projection. Canonical effect key is hash(profile, persisted repository/project identity, BIU identity, contract digest, lifecycle-entry generation, role/closure-action key). Original delivery and every scan use this exact key; delivery ID and scan time never enter it. A new generation requires canonical authorized transition/attempt allocation, not scanner mutation. Existing launch:<identity>:<version> records retain identity via immutable alias binding; do not rename in-flight effects.

**Failure and recovery.** Incomplete/unavailable projection or outcome store -> EVIDENCE_HOLD. Stale version/fence -> refuse action, resnapshot. Crash after send before receipt -> UNKNOWN; correlate readback, otherwise park for decision. Completed judgment result -> suppression, not missing actor. Store unavailable -> no launch, explicit failure; cannot promise finite successful recovery. Startup reopens intent/outcome/reservation records. Pending unsent intent may execute through canonical claim; sent/unknown intent must read back with same correlation and preserve fencing, parking if uncertain. Resolutions are checked against current outcome identity/lane/authority. Scans never add retry entitlement; exhausted or unknown authorized budget remains held.

**Operator and evidence.** Proposed liveness inspect is read-only; reconcile uses existing operator actor/authority/version/idempotency requirements and is disabled until 056 ratification and separate operational authorization. Show suppression and evidence hold with actionable refs. Live bootstrap retirement requires independently authorized workload exercise. Inspection snapshot refs, lifecycle-entry time/generation, age/G/I, expected effect, all matched claims/outcomes, gap/refusal, intent key/fence, authority/budget admission, suppression item/resolution, effect receipt and exact readback. liveness.gap/no_action/suppressed/evidence_hold/recovery_intent/readback_confirmed exposes identity and reason. Command success is not recovery confirmation. Detection bound G+I holds only with progressing clock, complete evidence and functioning scans; delivery/confirmation latency is separately reported. Publish shared_contracts.monitor_liveness independently of workload activity; missing/stale health is not quiet success. Live supervision is held by R1-GAP-MONITOR-HOST.

**Fixed choices.** Policy defaults: G=300 seconds, I=60 seconds, confirmation bound C=90 seconds; all configurable positive finite durations, persisted with policy digest and tested just below/at boundaries. These are design defaults, not a claim that historical bootstrap 5 minutes is a canonical invariant. Missing/invalid policy blocks startup. Periodic scan is limited to SF-REQ-056 explicitly specified reconciliation of known active state; it is not a general polling integration or work discovery loop. Effectively-once action requires idempotent/fenced consumer and durable readback; physically exactly-once network delivery is not promised. If an existing provider cannot prove these, park rather than relax the boundary. Depends on POSTW1-DECIDE-008A ratification. Pending SF-REQ-008 and SF-REQ-022 amendments are excluded; no new nonterminal retries or budget reset. Operational replacement and SWF-29 retirement remain separately gated.

**Deterministic enforcement.**

- `056-liveness-classification` (ADVISORY, python_unit_integration / LRN-010): Reuse advisory Phase 3 fake-clock absence classification and bounded correlated recovery confirmation, including pending and judgment controls. With fake clock inspect monitor health while idle, stopped, overdue, restarted and store-unavailable; assert HEALTHY/STALE/UNVERIFIED/DEGRADED separately from work liveness and withdraw G+I claim for nonhealthy scans. Proven-red obligation: Trust exit zero or one early sample; targeted confirmation assertion fails, delayed within-bound control passes. Freeze monitor/scan progress while work remains quiet: health must become STALE; treating quiet or unreadable health as healthy fails the named diagnostic.

- `056-fenced-effect` (BLOCKING, python_unit_integration): Race two store connections, delayed original trigger and restart between intent/send/receipt; require one effective authorized action and judgment suppression. Proven-red obligation: Disable identity/fence guard then judgment suppression in separate isolated runs; corresponding duplicate-action/suppression assertion must fail, restored runs pass.

Detailed vocabulary, persistence, concurrency, security, non-goals and exact acceptance traces remain in this requirement’s JSON contract. Shared storage, authority and dependency-direction rules apply in full.

## Local disposition

- **status**: PARKED
- **branch**: main
- **owner**: Codex GPT-6 Astra / POSTW1-DESIGN-009-R2
- **unique_content**:
  - docs/evidence/wave2-design-contracts.json
  - docs/evidence/wave2-design-contracts.md
- **blocker**: Direct task instruction prohibits commit, push and network; local deliverables intentionally await separate review/disposition.
- **next_action**: Independent R2 review; Program Director routes the existing four SPECIFY gaps and R2 Founder edge-authority gap, and separately owns publication/disposition. No requirement or operational change is authorized here.
- **temporary_branch_or_worktree_created**: False

The deliverables remain in the existing worktree at `/mnt/d/Projects/alienintent/docs/evidence/wave2-design-contracts.json` and `/mnt/d/Projects/alienintent/docs/evidence/wave2-design-contracts.md`. No temporary branch or worktree was created.

## Validation

Command outcomes are recorded in the JSON validation object after fresh execution. All 10 contracts and 53 source acceptance IDs are retained. There are 18 designed enforcement opportunities and nine promotion-reuse entries covering seven distinct Phase 3 promotions. All proposed behavioral probes remain unimplemented and unexecuted; none of these counts establishes semantic approval or runtime behavior. Historical source snapshots and prior Wave 1 evidence are preserved.

Historical R1 acceptance checks both passed (exit 0): design checker, 10 contracts and zero failures; Wave 1 checker, 1,075 checks and 13/13 negative controls killed. Exact acceptance-ID comparison retained all 53 IDs. SHA-256 comparison preserved all 29 files in the R1 snapshot of pre-existing changes and pinned inputs. These checks do not execute the designed behavioral probes or close SPECIFY gaps.

## R2 repair and Founder authority gap

```json
{
  "task_id": "POSTW1-DESIGN-009-R2",
  "baseline_commit": "c08fa798a3d9dd37fda30f4d35c9aa18c728a287",
  "verdict": "docs/operations/post-wave1-program/reports/POSTW1-VERIFY-010-R1-raw.txt",
  "scope": "Only the two design-contract files; no commit, push or network.",
  "supersession": "R1 remains a historical repair record. R2 withdraws normative R1 allowed_edges enforcement and replaces global -REQ- extraction with manifest/span-scoped typed classification. DV-1, DV-2 and DV-4 repairs and the episode-age disclaimer are retained. Prior directional probes are explicitly conditional, not silently dropped.",
  "DV2_1": "authority_gap; four file violations recorded, descriptive graph only",
  "DV2_2": "manifest-bound corpus with acceptance/compound kinds and scoped failures",
  "DV3": "closed as design scope repair; Founder decision remains open, no normative-direction readiness claim",
  "new_authority_gaps": 1,
  "requirements_created": 0,
  "disputed": "NONE"
}
```

```json
{
  "id": "R2-GAP-051-EDGE-AUTHORITY",
  "requirement_id": "SF-REQ-051",
  "status": "FOUNDER_AUTHORITY_GAP",
  "resolution_actor": "Founder; Program Director routes. Designer and implementer may record, but may not settle, this question.",
  "question": "Does the R1 directional restriction merely refine approved internal module design, or materially change the approved responsibility boundary? Is adoption authorized, and under what scope?",
  "evidence": "Architecture authority section 44 lists pre-Python modeling work; later docs/architecture/pre-python-gate/gate-reclassification.md G03 cites binding FD-02 approving internal modules and Control Plane application orchestration. That resolves the module classification, not explicit adoption of R1 allowed_edges. The five imports in four named files demonstrate the practical impact.",
  "design_disposition": "Withdraw R1 allowed_edges as a normative gate. Record observed_edges and the four importing-file violations descriptively. No requirement is created, amended or weakened; no product boundary is decided here.",
  "blocks": "Adoption of the proposed directional extension and affected SF-REQ-051 design-conformity claims until Founder disposition and reviewed scoped design; does not block running existing approved checks or certify the current source against the withdrawn table."
}
```

The historical R1 narrative and validation above remain records of that repair. R2 supersedes its edge-table and extraction scope as stated here. SF-REQ-051 is held for normative-direction adoption; existing checks remain blocking. No implementation probe or Founder decision is claimed.

## Fresh R2 validation

Fresh R2 design check passed (10 contracts, zero failures); Wave 1 check passed (1075 checks, 13/13 negative controls killed). One-off manifest/category predicate check reproduced 56 references/53 definitions from 17 pinned documents with zero unrecognized tokens and separately classified all 53 acceptance IDs. These checks are not independent review or execution of the designed behavioral probes. Four R1 SPECIFY gaps and one R2 Founder gap remain open. Historical R1 snapshot metadata is not presented as fresh R2 proof.
