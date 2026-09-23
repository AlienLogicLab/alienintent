# FX-S2 — atomic fencing and durable local consumer journal

Issue #74 / WO-220103; local composed/mechanical evidence only. Independent
workflow verdict is **PENDING**.

- [Pinned definition](FX-S2/fixture-plan.json): committed before implementation at
  `4c8f04b442f5646f1ef443337ed9e2bd7c60f6cb`.
- [Work packet](FX-S2/work-packet.md) and
  [implementation/compatibility qualifications](FX-S2/implementation-notes.md).
- [Execution record](FX-S2/execution-record.json): clean committed source
  `11d4b13d704a0fae15e3ba038673ae9a9ef59c42`; actual invocation supplied explicitly.
  Final evidence-only candidate SHA is recorded on the Issue.

Observed validation:

| Check | Result |
| --- | --- |
| Focused guarded + legacy store + composition | 62 passed, exit 0 |
| FX-S2 fence/vector/expiry/receipt controls | Four controls; each applied once, fault exit 1 with assertion failure, restored exit 0 |
| Full Python suite | 467 passed, exit 0 |
| Architecture fitness | All checks PASS, exit 0 |
| Node regression | 332 runtime, preflight PASS, 18 RAI, 3 policy; exit 0 |

Independent processes compete for intent/claim and deduplicate consumer delivery.
Real SIGKILL boundaries cover uncommitted intent rollback, committed intent,
claimed unknown effect, accepted consumer outcome and readback. Tests cover delayed
senders, tenure expiry/revocation, vector weakening, profile-isolated receipts,
forged confirmation, sorted multi-lock rollback, retained ownership and legacy
lane bypasses. No active guarded lane falls back to unguarded dispatch.

The earlier full-suite failure remains in the record: S0 correctly rejected a
changed SQLite adapter under its historical byte-identity predicate. Its checker,
manifest and 12 retained artifacts are unchanged. Historical positive proof now
runs at the exact pre-S2 admission revision, while current-source negative proof
requires exactly that authorized path change and exactly P11 failure. All other
S0 predicates and qualifications remain. S1's 19 artifacts and accepted ancestor
identity are retained and verified.

Consumer truth is same-database **local journal delivery**, not arbitrary remote
execution or physically exactly-once network delivery. No live profile was
adopted, no bootstrap was retired, and no operational result is claimed. Unmeasured
tokens, cost and provider usage are null with reasons. Local independent code
review supplements the pending separately invoked BIU verifier.
