# Pre-Python artifact inventory

Date: 2026-09-19. Inventory is evidence, not adoption of every document.

## Authority and baseline

The requested docs/decisions/2026-09-19-alienintent-architecture-authority.md and docs/decisions/2026-09-19-alienintent-pre-python-implementation-gate.md do not exist at the inspected baseline. The matching binding documents are docs/architecture/alienintent-architecture-authority-2026-09-19.md and docs/work-units/alienintent-pre-python-implementation-gate.md. Both were introduced in AlienIntent a30252d1291c60290577e6d02ee69d53a976404a (docs: architecture decisions). Those contents govern this gate; no duplicate authority files were created. Root /docs/work-units does not exist; repository docs/work-units was inspected in full.

AlienIntent baseline: a30252d1291c60290577e6d02ee69d53a976404a, clean at entry. Node behavior baseline: 2288cef3f49453a28d1c389964f5671ed90705d4. B-DISP archive: the B-DISP archive (local, read-only) at f0e2c0db61129c02fa25582a5c1665da3e17c9a6 (read-only). EOS source: AlienLogicLab/P000-all-eos (private repository) at 79d769228c266064e71b7ab7f556ea831cfc9537, clean, candidate pin with per-document maturity retained. No FactoryChecks repository/config/service/route changes.

## Corpus and evidence layers

| Layer | Material and role | Limits |
|---|---|---|
| Node implementation | bin entrypoints; src/config, runtime, domain, github, providers; scripts/worker-preflight and worker-gh; config example | Shipped bootstrap behavior, not permanent architecture |
| Tests/checks | all test files/helpers, scripts/check.mjs and workflow checks | Historical full regression: 309 runtime, preflight PASS, 18 RAI, 2 policy; not rerun for this docs-only gate; RAI remains unwired |
| Live proof | Issue1 producer SHA ffa3c5f32de12d579dc5372207bfb10790c6bea8; JC ACCEPT5734903116; Morty DONE5734928982 | Node only; no proof of Python, multi-instance or learned policy |
| Proof custody | a private local evidence store outside this repository plus before/after state, delivery receipts, Project readbacks, protected-file hashes and effective JC settings | Private evidence retained locally; no secrets or raw private logs copied to repository |
| AlienIntent active architecture | binding Authority, gate in work-units, reset decision, current strategy, canonical-architecture/interface-contracts/implementation-plan, 40 recommendations | Newer Founder authority supersedes conflicting older sketches; recommendations are not extra decisions |
| Context Engineering | B-DISP near-term-scope §§4–6; canonical role/phase compiler; north-star quality amendment | Existing decisions, not implemented full context compiler |
| Trajectory/Quality Evidence | B-DISP Zed Delta design source §§4–17, north-star amendment §§8–13, community decisions, model cost/quality decision | Observable trajectory distinct from derived measurements; no private reasoning |
| Control Plane | canonical architecture Operator surface; interface contracts; implementation-plan phases1–6; Authority §§36–38 | Existing design recovered; no functioning web control panel found in this corpus; sketches are not shipped commands |
| DDD/language | reset semantic distinctions and Authority §§8–9,17,41; EOS ontology and ADR-0004 | No approved AlienIntent UL/context model found; candidate required |
| Migration/history | B-DISP extraction/configuration/isolation/selfhosting/admission verification, complete decision/failure ledgers, current-baseline/BIU history; AlienIntent lifecycle correction | Preserve historical dates and local-vs-remote proof distinctions; do not inherit old work permissions |
| EOS | Constitution; ontology; ADR0004; Knowledge Lifecycle; Evidence Chains; learning loops, capability and governance material; engineering principles | Accepted records distinguished from directed policy pending review and scaffold |

## Node behavioral reference cases

| Retained invariant | Source | Existing checks / proof |
|---|---|---|
| Raw-byte signature verification | bin/alienintent.mjs; src/runtime/dispatcher.mjs | dispatcher/app-cli tests; public valid202/invalid401/tampered401 |
| Exact role/author/invocation/candidate authority | src/github/authority.mjs; dispatcher | github-authority and dispatcher tests; JC actual ACCEPT |
| Reject partial/ambiguous/wrong Project evidence | src/github/app-client.mjs; authority | github-app/github-authority/profile tests |
| Reserve before awaits; exact ownership | dispatcher; worktree-manager | dispatcher/worktree-manager/worktree-lifecycle tests |
| Isolated invocation workspace and safe cleanup | worktree-manager; worker-runner | worktree-lifecycle tests; distinct proof worktrees |
| Durable result before successor; replay/restart safety | dispatcher; state-compatibility | dispatcher/legacy-state/self-hosting tests; proof two-event replay |
| ACCEPT versus closure/DONE/rework | dispatcher; authority | closure tests; Issue1 independent closure |
| Ten lifecycle states, three dispatched phases | domain/lifecycle; profile; dispatcher | profile/github-app/dispatcher tests; lifecycle correction record |
| Sanitized credentials/diagnostics and actual provider auth | app-client; worker-runner; providers | github-app/worker-runner/preflight tests; live proof |
| Historical identity/marker compatibility | state-compatibility; authority | legacy-state tests; exact live invocation markers |

## File-level register

The following register is exhaustive for the inspected categories; hashes and sizes are in artifact-manifest.json. Inclusion is not a claim that every historical file remains authoritative. Large source/strategy/history records were located and searched by relevant sections; only cited sections substantiate gate judgments. No claim is made to audit unrelated FactoryChecks or every organizational project.

### AlienIntent

Root: this repository.

- `README.md`
- `package.json`
- `LICENSE`
- `.gitignore`
- `AGENTS.md`
- `src/config/profile.mjs`
- `src/config/repository-state.mjs`
- `src/config/state-compatibility.mjs`
- `src/domain/lifecycle.mjs`
- `src/domain/rai.mjs`
- `src/github/app-client.mjs`
- `src/github/authority.mjs`
- `src/providers/claude.mjs`
- `src/providers/codex.mjs`
- `src/runtime/dispatcher.mjs`
- `src/runtime/worker-runner.mjs`
- `src/runtime/worktree-manager.mjs`
- `bin/alienintent.mjs`
- `bin/b-disp.mjs`
- `test/app-cli.test.mjs`
- `test/check.test.mjs`
- `test/cli.test.mjs`
- `test/dispatcher.test.mjs`
- `test/github-app.test.mjs`
- `test/github-authority.test.mjs`
- `test/governing-instructions.test.mjs`
- `test/helpers/profile.mjs`
- `test/helpers/self-hosting.mjs`
- `test/legacy-state.test.mjs`
- `test/profile.test.mjs`
- `test/rai.test.mjs`
- `test/repository-state.test.mjs`
- `test/self-hosting.test.mjs`
- `test/worker-preflight.test.sh`
- `test/worker-runner.test.mjs`
- `test/worktree-lifecycle.test.mjs`
- `test/worktree-manager.test.mjs`
- `scripts/check.mjs`
- `scripts/worker-gh`
- `scripts/worker-preflight`
- `config/profile.example.json`
- `.github/workflows/b-disp-tests.yml`
- `docs/README.md`
- `docs/architecture/alienintent-40-architecture-recommendations.md`
- `docs/architecture/alienintent-architecture-authority-2026-09-19.md`
- `docs/architecture/canonical-architecture.md`
- `docs/architecture/implementation-plan.md`
- `docs/architecture/interface-contracts.md`
- `docs/decisions/2026-09-18-alienintent-name-and-organization.md`
- `docs/decisions/alienintent-architectural-reset-and-separation.md`
- `docs/migration/2026-09-18-complete-project-lifecycle.md`
- `docs/migration/agent-packages/GOVERNING_AGENT_DIRECTIVE.md`
- `docs/operations/forward-momentum.md`
- `docs/operations.md`
- `docs/strategy/alienintent-current-strategy.md`
- `docs/templates/work-packet.md`
- `docs/work-units/alienintent-pre-python-implementation-gate.md`
### B-DISP

Root: `the B-DISP archive (local, read-only)`.

- `docs/architecture/canonical-architecture.md`
- `docs/architecture/implementation-plan.md`
- `docs/architecture/interface-contracts.md`
- `docs/design/2026-09-11-recursive-artifact-improvement-v0.1.md`
- `docs/design/recursive-artifact-improvement.md`
- `docs/decisions/2026-09-16-b-disp-capability-based-provider-compatibility-decision.md`
- `docs/decisions/2026-09-16-b-disp-community-evidence-commons-decisions.md`
- `docs/decisions/2026-09-16-b-disp-community-evidence-service-architecture-decision.md`
- `docs/decisions/2026-09-16-b-disp-field-proving-and-public-release-strategy-decision.md`
- `docs/decisions/2026-09-16-b-disp-model-selection-cost-quality-decision.md`
- `docs/decisions/2026-09-16-b-disp-north-star-and-learning-design-amendment.md`
- `docs/decisions/2026-09-18-alienintent-name-and-organization.md`
- `docs/strategy/2026-09-17-b-disp-near-term-scope-google-new-sdlc-compliance.md`
- `docs/strategy/2026-09-17-b-disp-strategic-evolution-and-causal-evidence-thesis.md`
- `docs/strategy/2026-09-17-b-disp-zed-delta-trajectory-evidence-design-source.md`
- `docs/strategy/alienintent-current-strategy.md`
- `docs/migration/2026-09-15-b-disp-extraction-and-canonicalization-assessment.md`
- `docs/migration/2026-09-15-b-disp-extraction-implementation-plan.md`
- `docs/migration/2026-09-15-b-disp-migration-design-decisions.md`
- `docs/migration/agent-packages/GOVERNING_AGENT_DIRECTIVE.md`
- `docs/migration/agent-packages/PROPAGATE_TO_CODEX_AND_FUTURE_AGENTS.md`
- `docs/migration/agent-packages/README.md`
- `docs/migration/alienintent-rename-transfer-and-live-self-hosting-verification.md`
- `docs/migration/archive/2026-09-15-proposed-migration-design-decisions.md`
- `docs/migration/b-disp-authoritative-regression-baseline.md`
- `docs/migration/b-disp-disposable-worktree-and-runtime-isolation-verification.md`
- `docs/migration/b-disp-extraction-boundary-and-configuration-contract.md`
- `docs/migration/b-disp-mechanical-extraction-verification.md`
- `docs/migration/b-disp-self-hosting-proof-verification.md`
- `docs/migration/b-disp-stale-result-and-admission-gap-verification.md`
- `docs/migration/forward-momentum-propagation-verification.md`
- `docs/migration/mechanical-extraction-execution-plan.md`
- `docs/migration/planning-inputs/2026-09-15-extraction-plan-prompt.md`
- `docs/migration/work-units/Codex_FactoryChecks_Backlog_Reconciliation_Prompt.md`
- `docs/migration/work-units/alienintent-rename-transfer-self-hosting-work-packet.md`
- `docs/migration/work-units/define-b-disp-extraction-boundary-and-generic-configuration-contract.md`
- `docs/migration/work-units/establish-canonical-b-disp-ci-and-begin-mechanical-extraction.md`
- `docs/migration/work-units/freeze-and-diagnose-authoritative-regression-baseline.md`
- `docs/migration/work-units/implement-disposable-per-invocation-worktrees-and-runtime-isolation.md`
- `docs/migration/work-units/prove-standalone-b-disp-self-hosting.md`
- `docs/migration/work-units/reconcile-factorychecks-product-backlog-and-capture-fabspace-improvements.md`
- `docs/migration/work-units/repair-stale-result-and-github-admission-gaps.md`
- `docs/history/b-disp-decision-history.md`
- `docs/history/b-disp-failure-lessons.md`
- `docs/history/b-disp-milestone-reconstruction.md`
- `docs/history/biu-and-agent-workflow-history.md`
- `docs/history/current-b-disp-baseline-candidate.md`
- `docs/history/factorychecks-issue-index.md`
### EOS

Root: `AlienLogicLab/P000-all-eos` (private repository).

- `docs/00-foundation/ontology.md`
- `docs/00-foundation/ontology_graph.md`
- `docs/09-decision-making/records/DR-000001-ratify-record-governance-conventions.md`
- `docs/09-decision-making/records/DR-000002-adopt-living-due-diligence-system.md`
- `docs/09-decision-making/records/DR-000003-factorychecks-reasoning-centered-ems-intelligence.md`
- `docs/09-decision-making/records/DR-000004-factorychecks-ems-intelligence-begins-with-reasoning-loop.md`
- `docs/09-decision-making/records/DR-000005-factorychecks-ems-intelligence-uses-recipe-routed-micro-agent-execution.md`
- `docs/09-decision-making/records/DR-000006-factorychecks-mdp-added-to-ubiquitous-language.md`
- `docs/09-decision-making/records/README.md`
- `docs/08-learning-loops/README.md`
- `docs/08-learning-loops/organizational_learning_system.md`
- `docs/08-learning-loops/postmortems/PM-000001-all-eos-factorychecks-organizational-history.md`
- `docs/08-learning-loops/postmortems/README.md`
- `docs/11-capabilities/README.md`
- `docs/11-capabilities/capability_assessment_template.md`
- `docs/11-capabilities/capability_lifecycle.md`
- `docs/11-capabilities/capability_map.md`
- `docs/11-capabilities/capability_model.md`
- `docs/11-capabilities/capability_registry.md`
- `docs/11-capabilities/evidence_chains.md`
- `docs/11-capabilities/improvement-records/README.md`
- `docs/11-capabilities/improvement-records/cir-000001-assimilation-learning-checkpoint.md`
- `docs/11-capabilities/improvement-records/cir-000002-enterprise-context-before-implementation-context.md`
- `docs/11-capabilities/improvement-records/cir-000003-evidence-transformation-as-organizational-capability.md`
- `docs/11-capabilities/improvement-records/cir-000004-separate-record-truth-and-decision-classifications.md`
- `docs/11-capabilities/improvement-records/cir-000005-domain-language-translation-artifacts.md`
- `docs/11-capabilities/improvement-records/cir-000006-strategic-pivots-as-knowledge-assets.md`
- `docs/11-capabilities/improvement-records/cir-000007-confidence-travels-with-assimilation-claims.md`
- `docs/11-capabilities/improvement-records/cir-000008-projects-teach-the-organization.md`
- `docs/11-capabilities/improvement-records/cir-000009-validate-measurement-instruments.md`
- `docs/11-capabilities/improvement-records/cir-000010-preserve-functioning-capability-until-production-replacement.md`
- `docs/11-capabilities/improvement-records/cir-000011-require-owner-capability-and-caller-for-new-implementation.md`
- `docs/11-capabilities/improvement-records/cir-000012-control-scope-expansion-from-nearby-defects.md`
- `docs/11-capabilities/improvement-records/cir-000013-reconcile-intended-and-observed-architecture.md`
- `docs/11-capabilities/improvement-records/cir-000014-reconstruct-agent-context-from-durable-state.md`
- `docs/11-capabilities/improvement-records/cir-000015-separate-production-proof-from-delivery-states.md`
- `docs/11-capabilities/improvement-records/cir-000016-separate-authorization-envelope-and-orchestration-state.md`
- `docs/11-capabilities/improvement-records/cir-000017-preserve-provenance-for-architecture-claims.md`
- `docs/11-capabilities/improvement-records/cir-000018-translation-artifacts-preserve-project-language.md`
- `docs/11-capabilities/improvement-records/cir-000019-use-archframe-as-a-falsifiable-organizational-experiment.md`
- `docs/11-capabilities/improvement-records/cir_template.md`
- `docs/15-playbook/README.md`
- `docs/15-playbook/agentic_engineering.md`
- `docs/15-playbook/context_management.md`
- `docs/15-playbook/decision_principles.md`
- `docs/15-playbook/engineering_principles.md`
- `docs/15-playbook/experiment_design.md`
- `docs/15-playbook/organizational_learning.md`
- `docs/15-playbook/playbook_registry.md`
- `docs/15-playbook/repository_management.md`
- `docs/15-playbook/research_principles.md`
- `CONSTITUTION.md`
- `docs/adr/ADR-0004-domain-language-translation-layers.md`
- `docs/06-knowledge/knowledge_lifecycle.md`
