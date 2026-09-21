# Sandbox isolation standard — SWF-34

Date: 2026-09-21. Status: **Founder decision — binding** for the PY-09B / PY-10 sandbox.
Source: direct Founder instruction, resolving the single owner clarification raised by PY-09B's
2026-09-21 Agent-Ready assessment ([`NEEDS_CLARIFICATION`](../work-units/python/PY-09B.assessment.2026-09-21-needs-clarification.json)).

## The contradiction this resolves

PY-09B as first drafted required evidence that the sandbox installation *"targets only the sandbox
repository, profile and Project identities"*. The sandbox provisioning record simultaneously documents,
as verified fact, that the sandbox token **can** reach every Project in the `AlienLogicLab`
organization including production Project #1 — because `organization_projects` is an
organization-scoped permission with no per-project scope — while another binding rule fixes that same
grant as required least privilege.

An implementer could not satisfy both, and could not weaken a rule marked not-delegated. The
acceptance criterion described a property the platform cannot provide.

## Decision

**Option (a): amend to the strongest isolation the current GitHub permission model can actually prove.
No separate organization is provisioned.**

```
GitHub permission layer:       repository isolation   = hard (enforced)
configuration/domain layer:    Project #2 targeting   = deterministic, fail-closed
live-proof evidence:           Project #1 unchanged   = compensating verification
```

### Repository boundary — permission-enforced

Prove: the installation uses selected-repository scope; `AlienLogicLab/alienintent-sandbox` is
included; no production repository is granted; the sandbox profile resolves only that repository
identity. GitHub enforces this, so the evidence is a permission fact.

### Project boundary — configuration-enforced

**Do not claim or attempt to prove that the token reaches only Project #2.** That is false under the
platform's model, and an acceptance criterion asserting it would be unprovable by construction.

Prove instead: the profile names the exact Project #2 identity; every Project read and every Project
write targets Project #2; identity resolution **fails closed** on mismatch or ambiguity; no production
Project identity appears in sandbox configuration; the implementation never enumerates or
opportunistically selects an alternate Project; and evidence identifies the exact Project targeted by
every relevant operation.

### Compensating control

**PY-10 AC 16 remains intact and is not weakened**: the live proof must verify that the live AlienIntent
Project and the Node bootstrap were demonstrably unaffected — production Project #1 unchanged during
the run.

## Why this is not a weakening

The contract moves from

> prove the token reaches only Project #2

to

> prove AlienIntent deterministically targets only Project #2, and independently prove Project #1
> remained untouched.

No realizable control is relaxed. An impossible acceptance claim is removed and replaced with the
strongest technically valid control available under the already-approved topology. The previous wording
did not make the system safer; it made the BIU unimplementable.

## Residual risk — accepted

> Because GitHub App organization-project permission is organization-wide, credential compromise or a
> sufficiently defective or malicious adapter could address other Projects in the same organization.
> PY-09B's configuration and domain controls reduce accidental misuse; PY-10 AC 16 detects unintended
> production-Project mutation during the approved live proof. Hard token-level Project isolation would
> require a different organization boundary.

Accepted **for the Wave 1 live-proof sandbox**. This decision does **not** establish that the same
topology suffices for any future deployment or security profile; higher-assurance deployments may
require a separate organization or account boundary.

## Durable lessons

> **Resource addressing, configuration isolation and permission isolation are three different controls.
> A system must not claim permission isolation merely because it deterministically addresses one
> configured resource.**

> **Acceptance criteria must describe properties the underlying platform can actually enforce or prove.**

The second is the one that nearly cost a repair cycle. The unprovable criterion was written by the
coordinator and would have reached a producer intact; Agent-Ready caught it before release, as the
readiness gate exists to. It is the same class as SWF-24's rule about checks that cannot fail — a
criterion that cannot be satisfied is no more useful than a check that cannot go red.

## Scope

Amends PY-09B binding rule 6, scope item 8 and acceptance criterion 10. Changes no PY-10 acceptance
criterion, no completed BIU, no App permission, and no Node/B-DISP semantics. The prior
`NEEDS_CLARIFICATION` assessment is preserved as historical evidence; this record is the clarification,
and PY-09B is reassessed against the amended contract before any release — the gate is not bypassed
because the clarification came from the Founder.
