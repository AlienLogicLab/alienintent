# Python-only cutover — disposition of orphaned transition steps 1, 2, 4, 5

Status: **design/SPECIFY only. No AlienIntent service was stopped, started, restarted,
enabled or disabled to produce this record. No DAG node was added.**

Performed under Director inbox handoff
`director-followthrough-python-cutover-gap-design-20260927T0420Z`, itself a self-handoff
carrying forward the follow-on portion of
`director-followthrough-python-cutover-audit-20260927T0340Z` (now processed). That prior
audit is `docs/evidence/python-only-cutover-node-inventory-audit-20260927.md`, which found
transition_plan steps 1, 2, 4 and 5 (`docs/evidence/wave1-bootstrap-retirement-matrix.json`)
had, in its words, "no linkage of any kind — no gate node and no authority-gate reference —
anywhere in the reviewed DAG/matrix text." Investigated by Factory Director episode
`factory-director-2e75cfd340584912a5a773bbc2733632`.

## Correction to the prior audit

The prior audit checked `wave2-dependency-dag.json`'s `bootstrap_replacement_sequence`
(which assigns a `gate_node` to 9 of 17 steps) but did not check the same file's
`source_transition_guards` array, which already carries a named `release_gate` condition
and `plan_disposition: "Preserved condition only; no action executed"` for **every** step,
including 1, 2, 4 and 5. So the correct finding is not "no linkage of any kind" — it is
"a release-gate condition exists and is recorded as not yet satisfied or not yet
triggered", which is a narrower and more actionable gap than the prior audit stated. This
correction does not change the prior audit's bottom line (a real gap existed for a
successor to design), only its precise shape.

## Per-step investigation and disposition

### Step 1 — SWF-26 PY-04 mutation gate: gate condition already satisfied, no BIU needed

- `source_transition_guards` release_gate: "Review confirms PY-04-only scope and retained
  acceptance/mutation evidence; no deletion or live action."
- `transition_plan` recommended_action: "Record the already-expired SWF-26 precedent as
  historical; do not run or reintroduce the gate."
- Evidence: `docs/decisions/2026-09-20-py04-coordinator-mutation-gate.md` states, in its
  own text, "Status: **EXPIRED 2026-09-20** — retained as historical evidence only, not a
  standing gate" and "is **not** applied to PY-05 or any later BIU"; its Boundaries section
  states it "does **not** modify Node/B-DISP behaviour, product requirements, lifecycle
  semantics, or the accepted candidate." `docs/evidence/2026-09-21-bootstrap-expiry-inventory.md`
  §9 independently corroborates: "Expired at PY-04 DONE rather than allowed to persist."
- **Disposition: GATE_ALREADY_SATISFIED.** The review the gate calls for already exists,
  already confirms PY-04-only scope, and the evidence is already retained. Nothing further
  is owed by Wave 2. No DAG node, BIU or Founder action is needed. This closes step 1.

### Step 2 — eighteen external bootstrap modules: gate condition already satisfied by existing per-component work; optional migration is out of scope for this pass

- `source_transition_guards` release_gate: "No bulk import or deletion; preserve release,
  monitoring, attention, notification and evidence dependencies."
- `transition_plan` recommended_action: "...enumerate all 18 modules, consumers, revisions
  and test provenance and obtain a per-component custody decision."
- Evidence: `docs/evidence/2026-09-25-external-bootstrap-custody-refresh.md` already
  performs exactly this enumeration (finding the directory has grown past the historical
  eighteen) and already assigns a per-component custody class to every discovered
  component (its "Initial custody classes" table). `docs/work-units/wave2/WO-220501.md`
  (B0, DAG node `B0`, `docs/evidence/wave2-dependency-dag.json`) already owns the
  `bootstrap_custody_manifest` capability on exactly this read-only inventory/
  classification scope, and already cites the 2026-09-25 refresh as an existing proof
  surface. No bulk import or deletion has occurred; monitoring/attention/notification/
  release-admission dependencies are explicitly preserved live (KEEP_UNTIL_* classes).
- **Disposition: GATE_ALREADY_SATISFIED for the release_gate as written.** The custody
  refresh's own item 2 ("provenance-preserving migration of historical utilities" for
  `cycle_data.py`, `py05_py09_quality.py`, `py05_py09_trajectory.py`, `py10_preflight.py`,
  `trajectory_consistency.py` and their tests, into repository custody) is a real,
  low-risk, boundable idea, but it is the custody refresh's own suggestion, not something
  the transition matrix's step-2 release_gate or recommended_action requires — the gate
  only forbids bulk import/deletion and requires dependency preservation, both already
  true. Per the handoff's own boundary ("do not invent nodes speculatively for mechanisms
  that turn out to already be disposed or out of scope"), no new DAG node is added for
  this optional migration. It is recorded here as a deferred, Founder-optional tidying
  item, not built. No BIU or Founder action is required to close step 2 itself.

### Step 4 — PRODUCER-on-Claude temporary profile change: genuine open Founder decision, not an implementation gap

- `source_transition_guards` release_gate: "Founder standing no-profile-change instruction
  must be superseded; prove quiescence, retained work, current original-provider readiness
  and validated exact provider-block diff. Preserve identities and verifier profile; verify
  operational readback after authorized change."
- `transition_plan` recommended_action: "Recommend narrow PRODUCER provider reversion at an
  authorized safe boundary, or obtain a new explicit exception before further use."
- Evidence: `docs/evidence/2026-09-21-bootstrap-expiry-inventory.md` §7 already found this
  authorization "**already exceeded**" as of 2026-09-21 — the PY-09-scoped exception
  expired when PY-09 completed, but PY-09B and PY-10 both ran their producers on `claude`
  regardless, and the live profile (`~/.config/alienintent/self-hosting.json`, read this
  episode) **still** configures `PRODUCER.provider.adapter: "claude"` today, six days
  later, with no recorded reversion or ratification since.
- This is not an implementation gap a BIU can close: the release_gate itself calls for
  superseding a **standing Founder instruction**, which only the Founder can do, and for a
  "narrow ... reversion or ... new explicit exception" decision between two live options
  with real operational consequence (the expiry inventory separately notes PRODUCER and
  VERIFIER now share one Claude subscription, a single point of failure if the status quo
  persists unexamined).
- **Disposition: FOUNDER_DECISION_REQUIRED.** Routed below, alongside steps 8/9/10, rather
  than built as a BIU.

### Step 5 — sandbox ingress tunnel: gate not triggered; currently and correctly retained; a lower-urgency Founder retention question remains open

- `source_transition_guards` release_gate: "Before any shutdown prove no consumer, pending
  delivery/effect or scheduled proof depends on ingress; retain evidence and reproducible
  isolated route. Do not affect production tunnel."
- `transition_plan` recommended_action: "Obtain explicit sandbox tunnel retention/shutdown
  decision reconciling temporary label with contractual retention."
- Evidence: `docs/operations/py10-sandbox.md` records `alienintent-sandbox-tunnel.service`
  as Founder-authorized, Wave-1-provisioned, "test/integration infrastructure only", with no
  stated expiry. It is **not idle**: it is the currently bound, currently active isolated
  ingress for the `AlienLogicLab/alienintent-sandbox` / Project #2 target already reused,
  under explicit Founder-ratified ("no new resource") authorization, by WO-220505/#125's
  FX-B2 fixture, WO-220506/#126's FX-B3 fixture and WO-220502/E1. Shutting it down now would
  violate the release_gate's own precondition ("no consumer ... depends on ingress" is
  false today).
- **Disposition: gate correctly un-triggered; KEEP is the only safe action right now.** No
  DAG node, BIU or urgent Founder action is needed to close step 5 for Wave 2 purposes. The
  matrix's own "reconciling temporary label with contractual retention" question is real
  but not urgent (nothing is blocked on it, and the safe default already matches what the
  release_gate requires); it is routed below as a fourth, lower-priority item alongside
  step 4, for the Founder to dispose whenever convenient rather than as a blocker.

## Founder disposition requested (not decided here)

Per contract §6 (Founder-reserved matters: unresolved product intent, architecture policy,
budget authority) and the handoff's own instruction to route steps 8, 9 and 10 "the same
way SWF-21 was disposed for step 3" (see `docs/work-units/wave2/WO-220506.md` "Authority
disposition"), the following questions remain genuinely open and are not decided by this
Director (step 8 turned out to already be disposed — see below, not listed as open). None
of the open items currently block an eligible, unheld Issue — R7/WO-220607, R9/WO-220609
and B9/WO-220512 have no materialized GitHub Issue yet
(`docs/evidence/python-only-cutover-node-inventory-audit-20260927.md` §3) — so no
per-Issue Founder hold (contract §9) applies; they are recorded here instead so a
successor episode or the Founder can find and dispose them before those BIUs are
materialized and before their own closure.

1. **PRODUCER-on-Claude reversion or ratification** (step 4, new, this episode). Should
   PRODUCER revert to its original (non-`claude`) provider now that PY-09's exception has
   long expired, or should the Founder issue a new, explicit, open-ended exception? Either
   answer needs the release_gate's own proof steps executed afterward (quiescence, retained
   work, provider-block diff, identity preservation, operational readback) — that
   execution is delegated engineering once the Founder states which direction to prove.
2. **ATTENTION_ACTIVATION_AUTHORITY** (step 9, pre-existing named gate, inherited by
   R7/R9/B9). Partially disposed already: Director inbox handoff
   `founder-attention-receipt-fxb5-scope-20260926T072316Z` (2026-09-26) grants it "narrowly
   for FX-B5: to activate and exercise the existing Python attention / Decision Inbox path"
   and explicitly states this "does not authorize ... broader unattended product
   activation" (`docs/work-units/wave2/WO-220508.md` "Human-attention receipt surface and
   FX-B5 operational target"). That narrow grant does not close R7/R9/B9's broader need —
   a replacement consumer for new and unresolved attention generally (including
   judgment-required outcomes), or an explicit end of those duties, without losing queue
   durability or liveness suppression — which remains open.
3. **RESIDENT_TENURE_DECISION** (step 10, pre-existing named gate, inherited by R7,
   depends on steps 3/6/7/8/9, still undisposed — no processed inbox entry or decision
   record addresses it). An explicit tenure decision for a bounded resident-coordinator
   handoff, preserving program review/communication duties and independent monitors, with
   a fresh invocation verifying equivalent authority before any unattended activation
   (which needs its own separate authority).

Step 3 (SWF-21) is excluded from this list because it is already substantially disposed
for Wave 2 successor use via SWF-35, per `docs/work-units/wave2/WO-220506.md`'s own
"Authority disposition" section — that disposition is unchanged by this document.

**Step 8 (Windows notification) is not listed above — it is already disposed, and R7's
own citation of it is stale.** Director inbox handoff
`founder-windows-notification-scope-20260926T070519Z` (2026-09-26) recorded a general
Founder product decision: Windows event notifications are not required "for the Python
cutover path", and their absence "must not block ... downstream cutover work" — not a
decision scoped only to WO-220508/#128. `docs/work-units/wave2/WO-220607.md`'s own
"Authority disposition" section still lists `WINDOWS_NOTIFICATION_DISPOSITION` as an open
gate ("these gates remain open pending separate Founder action"), which no longer matches
the already-decided Founder intent. Per the governing directive ("If intended behaviour is
already decided and machinery does not match it, fixing the machinery is delegated
engineering, not a new Founder decision"), this document corrects that citation directly
in WO-220607.md rather than routing it as an open question.

## Net effect on the Wave 2 DAG and R7/R9/B9

No DAG node was added or changed. Steps 1, 2, 5 and 8 are closed for Wave 2 purposes
without new machinery (8 was already Founder-disposed; this pass only corrects a stale
citation). Step 4 is newly identified as a genuine Founder-reserved gap; steps 9 and 10
remain open as before (9 only narrowly, partially disposed). All three open items (4, 9,
10) are named above for Founder disposition. R7 (`WO-220607`) and R9/B9 remain gated on
their remaining open inherited authority references — this document narrows what those
references still require and corrects one (8), it does not close 4, 9 or 10.

## Boundaries observed

No AlienIntent service (Node, Python or `cloudflared`) was stopped, started, restarted,
enabled or disabled. No DAG node, BIU or GitHub Issue was created. No existing evidence
was rewritten; the prior audit is corrected by pointer, not edited. No new external
resource was invented; the sandbox target's continued use is existing, previously
authorized reuse. This is design/SPECIFY only, per the handoff's own boundary. The one
direct edit made outside this document — `docs/work-units/wave2/WO-220607.md`'s stale
`WINDOWS_NOTIFICATION_DISPOSITION` citation — reflects an already-made Founder decision;
it does not make a new one. `docs/work-units/wave2/WO-220605.md`, `WO-220511.md` and
`WO-220509.md` carry the same stale citation and were deliberately left untouched here —
correcting them is unrelated to the four orphaned steps this document was scoped to, so
touching them would exceed this pass's own minimal-footprint boundary; noted here for a
successor rather than done speculatively. R9 (`WO-220609`) and B9 (`WO-220512`) have no
work-unit document yet, so there is nothing to correct for them.
