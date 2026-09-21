# PY-09B — Live GitHub transport and projection substrate

**BIU:** PY-09B — Wave 1 S8b, the live-transport prerequisite for the Wave 1 capstone.
**Predecessor:** PY-09 (and PY-05, PY-06, PY-08). **Baseline:** `main` at release, containing this contract and the accepted PY-09 tree.
**Introduced by:** [SWF-33](../../decisions/2026-09-21-py10-transport-split.md), the Founder-approved Wave 1 decomposition amendment. It carries capability that PY-10's 2026-09-21 Agent-Ready reassessment found was deferred to PY-10 by every predecessor and named in no BIU's scope.

## Satisfies

| Requirement | Issue | Extent |
|---|---|---|
| SF-REQ-005 Work Management abstraction | [#7](https://github.com/AlienLogicLab/alienintent/issues/7) | The first **live** GitHub adapter behind the existing port |
| SF-REQ-007 Candidate custody | [#9](https://github.com/AlienLogicLab/alienintent/issues/9) | Live repository access sufficient for custody against the sandbox |
| SF-REQ-038 Doctor / validation | [#16](https://github.com/AlienLogicLab/alienintent/issues/16) | The live transport probes `doctor` needs to establish readiness |

No new Product Requirement is created. These three already own the semantics; PY-09B is where they first meet real infrastructure.

## Intent

Make the provisioned sandbox **reachable by canonical Python**, and prove it independently.

Provisioning satisfied environmental prerequisites — repository, Project, profile, tunnel, App identity, preflight 17/17 — but nothing in canonical Python yet acquires a token, reads a Project, writes a fenced projection, or receives a webhook. This BIU builds exactly that substrate and no more, so that PY-10 enters its single coherent live proof with transport defects already removed from the failure surface.

## Architecture references

- **Architecture Authority** §1 deployment topology and profile isolation, §13 capabilities, §26 evidence retention, §35 observability, §42 Node→Python coexistence.
- **SWF-08** — the dedicated sandbox environment this binds to; its provisioned identities are recorded in [operations/py10-sandbox.md](../../operations/py10-sandbox.md).
- **SWF-33** — this BIU's authority and boundary.
- **FD-01** — AlienIntent is canonical for execution state after release; Work Management receives projections. Projection direction is one-way and is not negotiable by this adapter.
- `docs/architecture/pre-python-gate/control-plane.md` (mutating commands carry actor/authority/expected version/idempotency key), `persistence-and-evidence.md`.

## Binding rules — not delegated

1. **Projection is one-way.** A Project field is written from canonical state and is never read back as execution authority (FD-01).
2. **Projection writes are fenced.** A write carries the expected revision and refuses on conflict; a stale write never silently overwrites newer canonical state.
3. **Credentials are referenced, never embedded.** The App private key and webhook secret resolve through the existing `SecretProvider`. No secret, App ID, installation ID, hostname or private installation detail appears in source, tests, logs, diagnostics or retained evidence.
4. **Least privilege is exact, and is derived from this architecture — not from the bootstrap.** The installation grants exactly `issues: read`, `metadata: read`, `organization_projects: write`, **`contents: write`**, and the events `issue_comment`, `projects_v2_item`. An extra grant fails the check as surely as a missing one.

   `contents: write` is required because canonical Python publishes the candidate and reads it back through the **installation credential** (`git_source_control.publish_and_read_back`), against a private repository: without it the token can neither push nor clone, and `doctor.py`'s source-control probe fails outright. The Node bootstrap needs no such grant because its workers publish with their own GitHub identities — its three-permission set is **not** the correct baseline for this architecture. Least privilege means the minimum authority the approved implementation and its custody invariant actually require; it does not mean the smallest set that happened to work somewhere else. Authorized by the Founder, 2026-09-21.
5. **Webhook admission is authenticated.** An unsigned or wrongly signed delivery is rejected; a replayed delivery is admitted at most once. Signature verification uses the existing ingress rule rather than a second copy of it.
6. **Isolation is proven at the layer that can enforce it** ([SWF-34](../../decisions/2026-09-21-sandbox-isolation-standard.md)). Two different controls, proven differently, and neither may be described as the other:
   - **Repository boundary — permission-enforced.** The App installation is selected-repository scope, includes `AlienLogicLab/alienintent-sandbox`, grants no production repository, and the sandbox profile resolves only that repository identity. GitHub enforces this.
   - **Project boundary — configuration-enforced.** `organization_projects` is an organization-scoped permission, so the sandbox token *can* technically reach other Projects in `AlienLogicLab`, including production Project #1. **Do not claim or attempt to prove that the token reaches only Project #2 — that is false under the platform's model.** Instead: the profile names the exact Project #2 identity; every Project read and every Project write targets Project #2; Project identity resolution **fails closed** on mismatch or ambiguity; no production Project identity appears in sandbox configuration; the implementation never enumerates or opportunistically selects an alternate Project; and evidence identifies the exact Project targeted by every relevant operation.

   The organization-wide Project permission is an **accepted residual risk of the chosen organization topology**, not a defect to engineer around here. PY-10 AC 16 is its compensating end-to-end control.
7. **This BIU does not run the Wave 1 proof.** It neither seeds a backlog nor executes the factory loop; that is PY-10's, and absorbing it here would recreate the coupling SWF-33 split.

## Scope

1. **Installation-token acquisition and use** — mint and refresh a GitHub App installation token from the App identity and private key resolved through the `SecretProvider`, with expiry handling and least-privilege verification.
2. **Live repository access** sufficient for the proof: read repository metadata and issues, and the Git-level access candidate custody requires against the sandbox repository.
3. **Projects v2 read** — resolve the Project, its Status and Priority fields and their option identities, through the existing Work Management port.
4. **Fenced Project projection write** — write lifecycle state to the Project as a projection, carrying the expected revision and refusing a stale write.
5. **Resident webhook ingress** — bind the configured host and port, receive deliveries through the provisioned sandbox endpoint, verify signatures, and admit each delivery at most once. Profile fields carry the bind address, port and secret reference.
6. **Sandbox profile composition** — the profile factory the control plane loads to bind all of the above, from the recorded resource identities and secret references.
7. **Live `doctor` transport probes** — work management reachable, source control reachable, transport (ingress) reachable, provider reachable, each returning a typed outcome distinguishable from `UNAVAILABLE`.
8. **Isolation evidence** — permission-level proof of the repository boundary, and configuration-level proof that Project addressing is deterministic, exclusive to Project #2 and fail-closed (SWF-34).

## Non-goals / excluded

Seeding the PY-10 backlog; running the factory loop; the live proof itself; the proof report; any PY-10 acceptance criterion. Additional Work Management providers; a second transport; retry/backoff policy beyond what the acceptance criteria require; observability beyond the diagnostics these probes emit. No Node, FactoryChecks, credential rotation, deployment or production-profile change. **No change to the production AlienIntent repository, Project #1, its App installation or the Node bootstrap.**

## Iteration surface — why this BIU exists in this shape

[SWF-33](../../decisions/2026-09-21-py10-transport-split.md) requires that this not become a second one-shot live run. Verification is **locally repeatable wherever practical**:

- **Fixture-backed and deterministic** for protocol and projection logic — token expiry and refresh, field/option resolution, fenced-write conflict handling, signature verification, delivery deduplication. These run offline, in the normal suite, as often as repair requires.
- **Bounded live** for what only real infrastructure can establish — credentials, App installation scope, webhook ingress and Project access. Small, cheap, repeatable, and each one individually diagnosable.
- **Proven-red** on the guards that matter (SWF-24): each negative control must be demonstrated failing when the guard it protects is removed.

## Verification-first repair sequencing (SWF-23 §4b)

Before any broad implementation repair on this BIU, in this order:

1. **Confirm the required verification harness exists** — the fixture-backed checks and the bounded live checks, present and executable rather than deferred.
2. **Confirm changed paths are covered by discriminating proof.** A check that cannot fail is not evidence ([SWF-24](../../decisions/2026-09-20-deterministic-failure-class-promotion.md)); coverage of a changed path must go red when that path breaks. Demonstrate it by removing the guard and observing the failure.
3. **Preserve prior proven criteria** — everything already satisfied stays satisfied, with its evidence intact or explicitly superseded.
4. **Then repair remaining implementation defects.**

A repair cycle that widens implementation while the harness for what it touches is still missing is out of order. PY-08 spent five cycles closing findings while shipping new defects, with its proof obligations untouched; one cycle spent building that proof ended it.

## Acceptance criteria

1. An installation token is minted from the App identity and private key resolved through the `SecretProvider`, is used for a live call, and is refreshed rather than reused past expiry. A negative case proves an invalid or missing credential reference fails closed with a typed outcome.
2. The granted permissions and event subscriptions are verified to be **exactly** the least-privilege set of binding rule 4 — including `contents: write`; a simulated extra grant and a simulated missing grant each fail the check, and **`contents: read` alone fails** because read permits the clone half of read-back and not the push half.
3. The sandbox repository is read live — metadata and issues — and the Git access candidate custody requires is exercised against it.
4. The sandbox Project is resolved live, including Status and Priority field and option identities, through the Work Management port.
5. A lifecycle projection is written to the Project and read back as written. A stale write carrying a superseded expected revision is **refused**, proven by a test that fails if the fence is removed.
6. Projection remains one-way: a test proves an externally edited Project field does not alter canonical execution state.
7. A real signed webhook delivery reaches the resident ingress through the provisioned endpoint and is admitted exactly once. An unsigned delivery, a wrongly signed delivery, and a replayed delivery are each rejected or deduplicated, with the wrong-secret case proven red.
8. The sandbox profile composition loads from the recorded identities and secret references and binds every capability above.
9. `doctor` returns typed outcomes for work management, source control, transport and provider against the sandbox, distinguishing `PASS`, `FAIL` and `UNAVAILABLE`; each probe has both a passing and a failing case, and no probe can pass on an adapter-declared flag alone.
10. **Isolation evidence, at the layer each control actually operates:**
    a. **Repository, permission-enforced** — the installation is `repository_selection: selected`, includes the sandbox repository, and grants no production repository; the profile resolves only that repository identity.
    b. **Project, configuration-enforced** — the profile names Project #2 exactly; every Project read and write performed by this capability targets Project #2; identity resolution fails closed on mismatch or ambiguity, proven by a negative case; no production Project identity appears in sandbox configuration; no code path enumerates or opportunistically selects another Project; and the evidence names the exact Project targeted by each operation.
    This criterion does **not** assert token-level Project isolation, which `organization_projects` cannot provide. The residual risk is recorded and accepted under [SWF-34](../../decisions/2026-09-21-sandbox-isolation-standard.md); PY-10 AC 16 compensates.
11. Retained evidence contains no secret, credential, App ID, installation ID, hostname or private installation detail — while still proving the run used the sandbox identity.
12. The Python suite, architecture fitness and the Node suite all pass.

## Verification requirements

- Executable proof, with the offline portion runnable repeatedly in the normal suite and the live portion bounded and individually diagnosable.
- Negative controls for credential failure, permission drift, stale projection write, unsigned/wrong-signature/replayed delivery, and each doctor probe.
- Independent verification by a separate verifier invocation before the capability is considered satisfied. **The verifier executes the bounded live portion itself** on the provisioned host, against the same sandbox identities, rather than accepting the producer's transcript of it — the same independence standard applied to every other Wave 1 BIU. The offline portion is re-run in full.
- Retained evidence: exact revisions, exit statuses, probe outcomes, the admitted delivery's identity, and the redaction applied.

## Required closure actions

Evaluated under the standing ACCEPT → DONE policy ([SWF-17, SWF-19](../../decisions/2026-09-20-wave1-closure-policy.md)).

- **Landing: required.** A normal merge commit of the accepted candidate into `main`, preserving the accepted SHA in ancestry. No rebase, squash or rewrite.
- **Deployment: not required.** The sandbox already exists; this BIU changes no environment.
- **Publication/release: not required.** Candidate-branch publication completes before verification.
- **Live verification: required and already satisfied by acceptance evidence** — closure records it and performs no new live run.
- **BIU-specific:** none beyond retaining the redacted evidence.

**Minimum necessary work (SWF-20 / SF-REQ-048).** Build the smallest substrate that satisfies the criteria above. Mechanically detectable over-scope work is a verification finding.

## Repair cycles (SWF-23)

> **Repairs must converge monotonically unless authority explicitly changes the target.**

Any repair cycle carries findings to fix, previously satisfied criteria, evidence that must be preserved, evidence explicitly superseded with its authority, and replacement proof obligations. Previously verified behaviour must remain correct and previously valid evidence must remain valid or be explicitly superseded. Evidence disappearance without supersession is a regression and a verification failure.

## Capabilities and budget

Capabilities: sandbox repository workspace, Git, Python toolchain, process control, network access to GitHub for the **sandbox installation only**, sandbox App credentials via `SecretProvider`. **No authority over the live AlienIntent Project, the Node profile, FactoryChecks or any deployment target.**
Budget per SWF-09: hard wall-clock, attempts, retries, concurrency and cancellation; token and monetary cost measured and recorded, never assumed zero. Live calls are bounded to the minimum the criteria require.

## Readiness

Agent-Ready assessment: [PY-09B.assessment.json](PY-09B.assessment.json). Dependencies: PY-05, PY-06, PY-08 and PY-09 accepted, and the SWF-08 sandbox provisioned — all satisfied.
