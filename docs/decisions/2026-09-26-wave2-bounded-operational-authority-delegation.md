# Wave 2 bounded operational authority delegation

Date: 2026-09-26. Status: **Founder decision — binding**.

Recorded via Director inbox handoff `founder-wave2-authority-delegation-20260926T200500Z`
(2026-09-26T20:05:00Z, relayed by a Founder-authorized observing session, not acting as
Factory Director). This channel and phrasing match the precedent already accepted and
acted on for `founder-f4-context-assembly-boundary-20260926T071415Z`,
`founder-live-transport-proof-authority-20260926T070519Z` and
`founder-windows-notification-scope-20260926T070519Z`.

## Decision

**WAVE2_BOUNDED_OPERATIONAL_AUTHORITY_DELEGATION.** For already-approved Wave 2 BIUs,
the Factory Director is delegated authority to bind and authorize operational/live proof
targets, reversible one-writer migration/cutover, installation launch-command migration,
Wave 2 release, and bootstrap-to-canonical replacement work, when those actions are
required by the approved BIU and do not reinterpret product or architecture intent.

POSTW1-DECIDE-006A is disposed for Wave 2 execution paths as follows: retain Node/
bootstrap compatibility mechanisms until their named replacement proof succeeds, but do
not require a new per-BIU Founder decision merely to exercise, prove, migrate, or retire
a bootstrap mechanism within an approved Wave 2 replacement BIU.

SWF-21's Wave 1 release grant is **not** revived; its nine conditions and six admission
preconditions remain retained admission checks under the standing Wave 2 successor
authority [SWF-35](2026-09-22-wave2-incremental-release-authority.md).

EXPLICIT_LIVE_TRANSPORT_PROOF_AUTHORITY, EXPLICIT_SOVEREIGNTY_CUTOVER_AUTHORITY,
EXPLICIT_FUTURE_RELEASE_AUTHORITY, INSTALLATION_MIGRATION_AUTHORITY and
SWF-21_SCOPE_DISPOSITION are therefore satisfied for approved Wave 2 BIUs when the
boundaries below are met, generalizing the narrow per-BIU grant already recorded for
WO-220502 (`founder-live-transport-proof-authority-20260926T070519Z`) to the rest of the
approved Wave 2 plan.

**ATTENTION_ACTIVATION_AUTHORITY** is granted for the existing approved local/operational
attention path needed by Wave 2 proof, consistent with the prior Windows-notification
disposition (`founder-windows-notification-scope-20260926T070519Z`): Windows
notifications are not required. This does not authorize an agent to fabricate a human
acknowledgement, receipt, or judgment; any proof criterion requiring a real human
acknowledgement remains a genuine human action (see Issue #128's retained hold).

## Boundaries (verbatim from the inbox handoff)

Delegation is bounded to the existing approved Wave 2 plan and current product/
architecture intent. Required dependencies, native Agent Ready READY on the exact
revision, release-admission checks, independent verification, candidate custody, durable
evidence/readback, one-writer safety, reversible rollback, and no-loss/no-duplicate-effect
protections remain mandatory. The Director may bind an existing local/configured
operational target and existing authorized provider/runtime budget/custody needed to
execute the BIU, but may not create material new external spend, broaden production
scope, change security posture, alter product requirements, amend architecture authority,
or invent a new business/product decision. Any genuinely new product/architecture/
security/material-budget decision still returns to the Founder. Existing Node/bootstrap
mechanisms remain KEEP_UNTIL_REPLACED: retirement is authorized only after the BIU's
required replacement proof and rollback/readback obligations pass.

## Why

Five Wave 2 BIUs (#123-#126, #129, #130, and downstream #132) received their first
native Agent Ready assessment on 2026-09-26 and returned HOLD naming one or more of the
same recurring Founder-reserved authority items as stop conditions (POSTW1-DECIDE-006A,
EXPLICIT_SOVEREIGNTY_CUTOVER_AUTHORITY, EXPLICIT_LIVE_TRANSPORT_PROOF_AUTHORITY,
EXPLICIT_FUTURE_RELEASE_AUTHORITY, INSTALLATION_MIGRATION_AUTHORITY). Re-routing each one
individually through the Program Director to the Founder would repeat the same decision
per BIU. The Founder instead disposed the recurring authority items once, generally, for
the whole approved Wave 2 plan, while explicitly preserving every independent,
non-authority readiness gap (unpinned fixtures, unconfirmed predecessor proof on a BIU's
own path, unbound operational targets specific to a BIU's own workload, budget/custody,
independent verification) as still-open delegated engineering, not decided by this
record.

## Consequences

This decision does not itself make any Issue READY or eligible. It disposes only the
named authority items on each affected BIU's own Authority/Stop-condition text and its
`founder-holds.json` entry. A fresh native Agent Ready assessment of each updated
revision determines actual disposition. Where that fresh assessment still returns HOLD on
grounds independent of this decision (fixture pinning, predecessor proof confirmation,
operational target binding, budget/custody, independent verification), the Issue's
Founder hold is narrowed to name only those remaining grounds, not removed. Where the
fresh assessment returns READY, the hold is removed and the Issue becomes eligible under
SWF-35 like any other Wave 2 BIU.

Issue #128 (WO-220508, FX-B5) is explicitly unaffected: its retained hold is a real human
acknowledgement gate (Issue comment 5846420730), which this delegation does not and
cannot satisfy.

Affected Issues and their own follow-up records: #123 (WO-220503), #124 (WO-220504),
#125 (WO-220505), #126 (WO-220506), #127 (WO-220507), #129 (WO-220510), #130
(WO-220601), and downstream #132 (WO-220509, unaffected until its named predecessors
reach DONE).
