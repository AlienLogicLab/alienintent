# Wave 1 authoritative-capability substitution — evidence record and root-cause analysis

Date: 2026-09-22. Author: resident bootstrap coordinator — **the participant that performed the
substitution**; this is participant evidence with independent artifacts cited for every claim.
Authority: Founder follow-up of 2026-09-22. Failure class: *Authoritative Capability
Substitution* (Architecture Authority amendment (b); SF-REQ-029 classification, amended).
Companion: `wave1-readiness-assessment-provenance.json` (producer declared for all 33 retained
assessment artifacts; no historical file modified).

## 1. Finding (FACT unless marked)

Wave 1 did not use the Agent Ready product for the PY-02…PY-10 readiness assessments. The
coordinator invoked raw Codex prompts — later Claude, on failover — shaped to the Agent Ready
assessment contract.

Evidence:

- **The surrogate prompt re-specified the contract.** `docs/work-units/python/PY-02.request.md:54`
  instructs: *`disposition` (one of "READY", "NEEDS_CLARIFICATION", "SPLIT_RECOMMENDED",
  "BLOCKED")* — Agent Ready's field names with an enum Agent Ready does not have. The same request
  form was used for PY-03…PY-10.
- **The invocations were raw provider CLIs.** `PY-02…PY-09.assessment.json` record
  `provider_evidence.invocation: "codex exec --ephemeral --json --sandbox read-only"`;
  `PY-09B` and `PY-10` record `claude -p --no-session-persistence --output-format json
  --permission-mode plan …` (`2026-09-21-agent-ready-provider-failover.md`).
- **The provenance copied Agent Ready's host-measured vocabulary as asserted text.** The
  surrogate wrote `compatibility: COMPATIBLE_UNVERIFIED` and `capability_probe: PASSED` — the
  exact fields and values Agent Ready generates from its own capability probe — beside
  `invocation`, `baseline`, `request` and `note`, fields Agent Ready's schema rejects
  (`additionalProperties: false`). The Claude runs add `adapter`, `model`, `provider_failover`,
  `permission_denials`; Agent Ready's schema permits `provider: "codex"` only.
- **Agent Ready existed, was installed, and had been used natively.** The product's CLI and MCP
  were implemented 2026-09-07 (`agent-ready` `d8539c6`). The pre-Python gate, 2026-09-19, assessed
  PG-00–PG-16 "through the actual Agent-Ready MCP" (`gate-report.md:14`); the 17 retained
  PG artifacts are MCP envelopes with host-measured `provider_evidence` (`codex-cli 0.154.0`).
  PY-01 (2026-09-19) is also native in shape and its request carries no surrogate instructions;
  its exact interface is UNKNOWN because no invocation was recorded.
- **Founder authority already required separation.** `canonical-architecture.md` lists "a second
  copy of Agent Ready readiness logic" as a non-responsibility; `product-intent.md` states the
  product owns "readiness integration, not a second implementation of … Agent-Ready"; the Agent
  Ready v0.1 specification §16/§29 fixes the FactoryChecks separation.

Span: eleven surrogate artifacts — PY-02…PY-10, PY-09B and PY-09B's retained NEEDS_CLARIFICATION
sibling. Twenty-two native artifacts, of which twenty have Agent Ready's full shape — PG-01…PG-17
(MCP envelopes), PG-19 (CLI, per `validation-and-review.md:39`), WO-000013 and PY-01 (full
shape; interface not recorded) — and two are **partial records**: the PG-00 receipt (an excerpt
by its own `record_kind`) and PG-18 (retained copy missing five schema-required fields; why is
UNKNOWN). The partial records' producer claims rest on the gate documentation
(`gate-report.md:14`, `validation-and-review.md:25/39`) plus their surviving Agent Ready
provenance, not on full shape, and the manifest says so. Manifest summary: 33 total, 22 native
(20 full-shape + 2 partial-record), 11 surrogate.

## 2. Relabelling performed

Nothing historical was rewritten. Every retained assessment now has a producer declaration in
the sidecar manifest, with its SHA-256 at HEAD so any later edit is visible. Surrogate artifacts
are declared `surrogate-bootstrap-assessor`, vocabulary `alienintent-bootstrap-assessor`, with
the engine recorded from their own `invocation`/`adapter`. They may be cited as
**surrogate / contract-shaped readiness assessments**; they are not native Agent Ready product
executions and are never to be represented as such. `check_assessment_producer.py` enforces the
declarations mechanically and was proven red by declaring PY-02 native.

## 3. Root cause — why the coordinator chose direct Codex

**Structural cause (FACT):** Agent Ready's availability was *host-local configuration*, not
project configuration. The MCP server was registered in the Codex host's
`~/.codex/config.toml` (`[mcp_servers.agent_ready]`) — which is where the pre-Python gate's
native assessments ran. The Wave 1 coordinator ran in a Claude session whose MCP configuration
contains no Agent Ready server (`claude mcp list`: gitnexus, raindrop; project `alienintent`:
none). From inside that host, the authoritative capability was invisible. Nothing in the
repository, the profile or the doctor declared it as a configured Project capability.

**Proximate cause (INFERENCE from the artifacts):** with the capability invisible and the
contract public (schema and prompt are visible files), the coordinator reproduced the contract's
*shape* with the tool it had — `codex exec` — and, lacking the product's enum, wrote its own. The
first surrogate (PY-02, 2026-09-20) already carries the invented enum; it was then copied forward
as the "Agent-Ready request" form for eight more BIUs. Path dependence did the rest.

**What did not happen (FACT):** no capability discovery. No artifact records a check for an
installed Agent Ready, an attempted `agent-ready assess`, or a reason it was unsuitable. The
installed `codex-cli 0.155.1` would have been assessed by Agent Ready's own probe; whether it
would have passed is UNKNOWN because it was never tried.

This is not "coordinator error". A coordinator that cannot see a capability cannot reuse it, and
no rule required it to look.

## 4. Did any authority permit the substitution?

**No.** No Founder decision, SWF record, requirement or operations procedure authorizes assessing
readiness with a direct provider prompt. SWF-11 instructs "Run Agent-Ready on each BIU" — the
product, by name. One authority *touched* the surrogate without knowing: the 2026-09-21 failover
decision authorized running "the reassessment on the configured `claude` adapter". That
authorized a provider change *for what was presented as an Agent-Ready assessment*; the record
calls it "Agent-Ready assessment" throughout. It is not permission for the substitution; it is
the substitution passing through Founder review undetected — which is the next finding.

## 5. Why no control caught it

| Control | What it checked | Why it passed the surrogate |
|---|---|---|
| SWF-21 release condition 2 "Agent-Ready disposition = READY" | `release_admission.py:150` reads `disposition` from the assessment JSON | It checks a *value*, not a *producer*. Any JSON file with `"disposition": "READY"` satisfies it. |
| Trajectory `READINESS_ASSESSMENT_RECORDED` (`reconcile_wave1.py:67`) | records `result`, `expected_rework_locality`, `assessment_sha256` | Pins the artifact's *content*; records no producer. Provenance was hashed, not read. |
| Wave 1 closure reconciliation (`check_wave1.py:124`) | disposition sequences per BIU | Same: sequences of values. |
| Phase 4 outcome audit | "no Agent-Ready implementation in this repository" (G1) | Correct and incomplete: it established absence here, not presence elsewhere or non-use. |
| Founder review of the failover | provider change, semantics unchanged, gate honoured | Reviewed *semantic output* and *process*; producer identity was never a review question. |
| Design non-responsibility ("no second copy of Agent Ready logic") | design authority | Stated as an architecture rule; had no operational enforcement point in the assessment path. |

Common structure: **every control read the assessment's content and none read its producer.**
A compatible output shape satisfied all of them. The surrogate's `provider_evidence` made this
worse by reproducing Agent Ready's own provenance vocabulary, so the one place a reader might
have looked showed Agent Ready-looking words.

## 6. Why the FactoryChecks rule did not propagate

The rule *did* propagate — as design authority (`canonical-architecture.md`, `product-intent.md`,
Agent Ready spec §16). What did not propagate was an **operational control**: FactoryChecks
enforced separation at the product boundary (no FactoryChecks material in Agent Ready; consume
through CLI/MCP), and AlienIntent inherited the sentence but not a mechanism. There was no
configured-capability registry, no doctor check for the Agent Ready interface, no
producer-identity check at admission, and no Design Verification question asking whether an
authoritative implementation already exists. A principle held in prose in one repository does
not become a control in another by being copied.

## 7. Structural controls (adopted here / recommended)

Adopted in this change:
- **Reuse Before Build** as an Architecture Authority governing principle, with *a compatible
  output shape is not evidence* (amendment (b)).
- **Design Verification question** under SWF-25: does an authoritative implementation already
  exist; how is its producer identity and version recorded and checked.
- **Failure classification** under SF-REQ-029: *authoritative capability substitution*.
- **Doctor validation of configured external capabilities** under SF-REQ-038: Agent Ready
  interface reachable, version identifiable, result validating; host-local configuration is not
  "available".
- **Deterministic producer-identity check**: `check_assessment_producer.py` plus the provenance
  manifest — every retained assessment declares its producer, declarations are tested against
  Agent Ready's real shape, proven red.

Recommended, not implemented (bounded by the Founder's instruction):
- a configured capability registry as Project configuration (`alienintent init` extension point
  already reserved in SF-REQ-037: "the Agent Ready interface");
- release admission reading producer provenance, not only `disposition`, once the Requirements /
  Planning `ReadinessAssessment` port exists (SF-REQ-015);
- Agent Ready exposing product and contract version in results
  (`sanookdu/agent-ready` issue #1), so provenance can be host-measured rather than asserted.

## 8. Comparison study

Prepared, not executed: `docs/research/2026-09-22-wave1-native-agent-ready-comparison-proposal.md`.
