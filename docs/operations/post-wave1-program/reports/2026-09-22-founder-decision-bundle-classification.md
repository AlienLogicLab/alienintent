# Founder decision bundles after canonicalization — classification (2026-09-22)

Author: resident bootstrap coordinator acting as local Program Director. Authority: Founder
direction of 2026-09-22 ("Determine which of the previously open Founder decision bundles are now
RESOLVED_BY_FOUNDER / RESOLVED_BY_CANONICALIZATION / REQUIRES_OPERATIONAL_PROOF /
GENUINELY_FOUNDER_DECISION_REQUIRED. Do not ask the Founder to repeat a decision already made … and
canonicalized"). Inputs: `program-state.json` (open subdecisions), FINAL-REPORT §3/§7, the
canonicalization report §2/§6/§7, Architecture Authority amendments A1–A11/(b), the Wave 2
reconciliation delta (`FACT-RECON-002`). Every classification is INFERENCE from the cited
evidence unless marked FACT. Independent verification of this classification is requested as
part of the Wave 2 Design Verification round (`FACT-DV-005`).

**Frontier relevance.** The intended executable frontier is WO-220101 (DAG S0), the only
dependency-free, gap-free, gate-free candidate (FACT: `wave2-candidate-bius.json#/bius/0`). No
open subdecision below is on S0's path; each is noted with the nodes it does hold.

## POSTW1-DECIDE-004A / 005A — DONE (FACT)

Closed by canonicalization on 2026-09-22 (G1/G2 owner = Agent Ready product + SF-REQ-015
integration + SF-REQ-029 serialization; SPLIT-G1 = SF-REQ-013 owns the split transaction).

## POSTW1-DECIDE-006A — seven retirement items → REQUIRES_OPERATIONAL_PROOF (all seven)

| Item | Classification | Evidence |
|---|---|---|
| SWF-21 release authority | REQUIRES_OPERATIONAL_PROOF | Wave 1-only grant; ending it changes nothing until a canonical release mechanism is proven (SF-REQ-002 admission amendment; FINAL-REPORT §3 "Ending Wave 1's SWF-21 grant does not remove admission protection or authorize Wave 2 releases"). No Founder decision is needed to *keep* protection; a Wave 2 release grant is part of the Wave-authorization packet, not a retirement decision. |
| Windows notification | REQUIRES_OPERATIONAL_PROOF | replacement = canonical Decision Inbox notification (SF-REQ-035) — proof by replacement per Founder §11 ("Replacement, not elapsed time, governs retirement"). Risk acceptance would be Founder; none is requested. |
| session-bound attention waiter | REQUIRES_OPERATIONAL_PROOF | replacement = persistent monitoring (SWF-27 / SF-REQ-053, A6). |
| sandbox ingress tunnel | REQUIRES_OPERATIONAL_PROOF | custody/dependency of PY-10 test infrastructure (`py10-sandbox.md`); retire when Wave 2 live proof no longer needs it. |
| eighteen external bootstrap modules | REQUIRES_OPERATIONAL_PROOF | WO-220501 (B0) owns the inventory and per-component custody decisions; those decisions surface individually. |
| resident coordinator multi-BIU tenure | REQUIRES_OPERATIONAL_PROOF | Founder §11 defines the coordinator as temporary scaffolding retired by canonical replacement (SF-REQ-053 bounded episodes). |
| PRODUCER-on-Claude reversion | REQUIRES_OPERATIONAL_PROOF (separate operational authority) | provider change is an Allocation decision under SF-REQ-026 once the Allocator exists; until then the standing instruction "do not revert provider configuration" holds. |

Holds: WO-220501 (B0) and the B-track; not S0.

## POSTW1-DECIDE-007A — R02–R05

| Item | Classification | Evidence |
|---|---|---|
| R02 SF-REQ-008 durable worker-outcome read-back | GENUINELY_FOUNDER_DECISION_REQUIRED (ratify an amendment to a P0 requirement's text) — **not blocking**: WO-220102 (S1) already carries the read-back obligation as design; ratification changes requirement text, not S1's extent | retrospective R02 `ownership_proof`; canonicalization report §7 "four remaining Phase 7 amendments … not addressed by v0.1" |
| R03 SF-REQ-022 nonterminal retry budget | GENUINELY_FOUNDER_DECISION_REQUIRED (amendment to SF-REQ-022, Wave 3) — not blocking Wave 2 | same |
| R04 LRN-022 ownership (coordinator-tool environment / authentication precedence) | GENUINELY_FOUNDER_DECISION_REQUIRED (NEW_CAPABILITY_GAP → new requirement or explicit owner) — not blocking; operationally mitigated by the launchers' credential filtering (`claude_session.py`, `codex_session.py`) | ledger LRN-022; Founder POSTW1-DECIDE-002A allowed genuine NEW_CAPABILITY_GAP findings |
| R05 LRN-023 ownership (provider-neutral started/progress/terminal/capacity normalization) | GENUINELY_FOUNDER_DECISION_REQUIRED — not blocking; the Wave 2 Deterministic Test Worker scenario "provider/capacity failure" exercises the observable without deciding the owner | ledger LRN-023 |

These four travel in the Wave-authorization packet as decisions with recommendations; none stops S0.

## POSTW1-DECIDE-008A — SF-REQ-056 ratification → GENUINELY_FOUNDER_DECISION_REQUIRED

FACT: SF-REQ-056 exists as GitHub issue #67 (P0, Wave 2, CAPTURE) authored in Phase 8 from an
identifier defined nowhere in the factory plan; Founder v0.1 is consistent with it but does not
ratify its text. Holds: WO-220103 (S2) references 056's conditional recovery policy without
ratifying it; K/O capstones. Not S0. Travels in the Wave-authorization packet.

## POSTW1-DECIDE-010A — four design authority gaps

| Gap | Classification | Evidence |
|---|---|---|
| R2-GAP-051-EDGE-AUTHORITY (normative cross-module import-direction table) | GENUINELY_FOUNDER_DECISION_REQUIRED (architecture policy not decided; A5 says implementation must surface it, not invent it) | canonicalization report §6 F7; DV R2 withdrew the unauthorized table; A15 modular-monolith bias does not decide direction |
| R1-GAP-039-ORCHESTRATION (owner of canonical multi-role orchestration) | GENUINELY_FOUNDER_DECISION_REQUIRED (requirement-ownership assignment) — the reconciliation delta confirms it remains open after A9 | `wave2-recon.codex.md` Answer 5; `C39/authority_gap_refs` |
| R1-GAP-039-REAL-OUTCOME (real-worker RoleOutcomeRecord producer) | GENUINELY_FOUNDER_DECISION_REQUIRED (ownership) — same | same |
| R1-GAP-MONITOR-HOST (who owns/supervises the persistent monitor host) | **Not a Founder decision → REQUIRES_OPERATIONAL_PROOF** (independently verified, FACT-DV-005 answer 8, with two corrections applied): the authority question is answered by SWF-27 / SF-REQ-053 (persistent monitoring is operational infrastructure, already applied as `systemd --user` services — `2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md` §Applied), the SF-REQ-037 amendment ("monitoring host" is an `init` extension point) and SF-REQ-038 (doctor validates configured capabilities). AA §14 is *not* the basis (it governs agents changing live environments). What remains is engineering: an SF-REQ-053/056 contract revision naming the supervisor mechanism and doctor probe, plus independent DV; the 12 DAG holds stay until that lands. | AA A6; SWF-27 Applied; SF-REQ-037/038 amendments; DV-005 answer 8; FINAL-REPORT §4 table (MONITOR-HOST alone frees 5 nodes) |

Holds: the 23 gap-blocked nodes (FINAL-REPORT §4). Not S0.

## POSTW1-DECIDE-013A — AR13-CQ-001 concrete answer → REQUIRES_OPERATIONAL_PROOF (engineering)

FACT: the concept half is RESOLVED_BY_CANONICALIZATION (Allocator = SF-REQ-026 amended; Execution
Packet defined in UL). The concrete half — "a specific authorized allocator instance, retained
execution packet, positive limits and remaining allowance for WO-220101" — is constructed by the
Program Director under Founder direction of 2026-09-22 §5 ("bind the canonical Allocator role;
construct the exact bounded execution packet from existing authority and current
budget/configuration where delegated; ask the Founder only if a genuine budget/authority decision
remains"). Budget dimensions follow SWF-09 (hard: wall-clock, attempts, retries, concurrency,
cancellation; measured: tokens/cost, never zero). The one thing that is not delegated is the
**Wave 2 release grant** itself (FD-01 §3; W2-P01), which is the Wave-authorization packet.

## Net effect on the frontier

S0 is held by exactly one thing: a fresh **native Agent Ready** assessment at the revised
baseline after the execution packet is bound (its historical NEEDS_CLARIFICATION verdict is
retained, never edited). Everything the Founder must still decide travels in the
Wave-authorization packet; nothing in it is on S0's path.
