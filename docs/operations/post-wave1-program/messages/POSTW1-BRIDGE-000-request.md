# Bridge round-trip proof — coordinator-only question

This is the bootstrap proof that the local Program Director can reach the resident Claude
coordinator directly, without the Founder relaying. It carries a real question rather than a
ping, because a transport proven only on `"hello"` is not proven on anything that matters.

Routing note: `bootstrap_control_review` routes to Tier 3 (claude-bootstrap-coordinator)
because it depends on lived Wave 1 operating context that the durable artifacts do not carry
on their own. Everything deterministic about it was settled before this message was sent.

**Question.** The bootstrap expiry inventory
(`docs/evidence/2026-09-21-bootstrap-expiry-inventory.md`) left two mechanisms at
NEEDS_DECISION: the SWF-21 release-coordinator duty, and the attention waiter. Both were
scoped to "through Wave 1". Wave 1 is closed.

State, in two or three sentences and from lived operating context rather than re-reading the
inventory: **what breaks first if both are switched off today**, and is that breakage
observable or silent? Do not recommend a retirement action — the Founder holds that decision.

Reply with: `FIRST_FAILURE=<one line>` and `OBSERVABLE=yes|no|partial`.
