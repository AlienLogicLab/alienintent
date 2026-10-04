# Work unit: automated closure and cleanup for registry work

**Label:** `AUTOMATED-CLOSURE` (a document label; permanent id `0677f8bb-71c2-4c62-8b4a-d0e5318ba689`).
**Status:** Draft revision 5 (work item `0677f8bb-71c2-4c62-8b4a-d0e5318ba689`, at CAPTURE) for independent review, 2026-10-04. Not approved, not assessed, not released.
**Position on the path:** path row 8, the second of the three connections still missing from the critical path. Row 7 (restart continuation) is landed at `main` `789240c`. Automatic selection and launch of the next eligible item follows.
This packet is built by the manual workflow, not by `work launch`, so its budget carries no launch limits.
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it (by hand, because this unit is the one that automates closure).
**Baseline:** `main` at `789240c`. Every interface named below is the one at that commit.
**Informative only:** `docs/architecture/alienintent-role-capability-authority-model-2026-10-04.md` is a Candidate record still under Founder review. It is not authority for this unit. The Founder's direct role-separation instruction that this unit follows is quoted in `fixed_decisions`.

## Contract

```json alienintent-contract
{
 "identity": "0677f8bb-71c2-4c62-8b4a-d0e5318ba689",
 "version": "revision-5",
 "intent": "Make closure a launched step for registry work: fixed closure action names with exact receipts tied to the work item and accepted candidate; a fresh CLOSURE session on the VERIFIER's configured provider and model that holds no landing credential and produces only a bounded closure request; a durable, secret-free landing order journaled before the first irreversible effect, with deterministic recovery that needs no model session; a deterministic Landing Authority that alone receives a landing-scoped App token and performs only the exact ordered protected-main landing; scoped App tokens for every other registry use, without contents write; control-plane read-back before every receipt; recovery of a started item from its registry record, not from its board status; one completion path (the coordinator's close transition), with the registry row moved to DONE afterwards through a reachable, repeatable projection that writes a real work-completion evidence record; and a verified ready-to-land result when landing is not enabled, which never blocks unrelated work.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-04: a fixed set of closure action names; each needs an exact receipt tied to the work item and accepted candidate.",
  "Founder 2026-10-04: work display updates text and does not necessarily move the card to DONE; closure must confirm both.",
  "Founder 2026-10-04: reuse record-completed's evidence checks but do not introduce a second completion path; the coordinator records closure.",
  "Founder 2026-10-04: CLOSURE uses the VERIFIER's configured provider and model in a fresh, separate session dedicated to closure (the B-DISP arrangement); no new provider.",
  "Founder 2026-10-04 (made stricter by revision 4): the factory App is the landing identity; its permission change needs the Founder's explicit authorization; no cognitive worker (PRODUCER, VERIFIER, CLOSURE or the Factory Director) may access its private key or obtain its token.",
  "Founder 2026-10-04: protected-main landing and credential separation are explicit prerequisites to the real-use proof, not reasons to replace automated closure with a permanent manual push; until then a verified ready-to-land result is not completed automated closure.",
  "Founder 2026-10-04 (role and capability separation, direct instruction): a cognitive role may request effects; deterministic code owns the effect intent, the credentials, the execution, the read-back, the recovery and the receipts. The CLOSURE session receives no App private key, no reusable landing token, no protected-main authority and no git-write grant; it produces a bounded structured closure request over the five fixed action names for the exact work item and accepted candidate. A deterministic Landing Authority alone uses a landing credential and performs only the exact ordered landing after checking work identity, exact accepted candidate, ACCEPT state, requested actions and current repository state. The control plane reads back every effect and alone issues receipts."
 ],
 "authorized_scope": [
  "src/alienintent/execution_coordination/domain/closure.py",
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/composition/landing_authority.py",
  "src/alienintent/composition/role_binding.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/installation/application/installation_credentials.py",
  "src/alienintent/context_assembly/application/work_context.py",
  "src/alienintent/context_assembly/domain/work_context.py",
  "src/alienintent/context_assembly/application/work_completion.py",
  "tests/execution_coordination/test_factory_coordinator.py",
  "tests/composition/test_worker_launch.py",
  "tests/composition/test_landing_authority.py",
  "tests/composition/test_role_binding.py",
  "tests/invocation_runtime/test_runtime.py",
  "tests/installation/test_installation_credentials.py",
  "tests/context_assembly/test_work_context.py",
  "tests/context_assembly/test_work_completion.py"
 ],
 "excluded_scope": [
  "operating-system credential separation",
  "the App permission change",
  "automatic next-item selection",
  "re-landing work already landed by hand",
  "closing earlier coordinator items whose contracts name free-text closure actions",
  "a new provider, store, lifecycle stage or configuration source beyond the optional landing flag in the existing github entry",
  "the general role, capability or Director system beyond the closure slice",
  "changing earlier packets"
 ],
 "dependencies": [
  "bb39a588-bf9a-4d30-b573-b8245b8979a0"
 ],
 "required_capabilities": [
  "python",
  "git",
  "sqlite",
  "process-control"
 ],
 "budget_policy": {
  "maximum_attempts": 3
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-16 pass",
  "architecture fitness passes",
  "acceptance check 17 recorded as ready-to-land until the section 1 prerequisites are met"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation"
 ],
 "required_evidence": [
  "VERIFIER verdict file whose first line is exactly ACCEPT or REJECT",
  "landing record on main"
 ],
 "non_goals": [
  "next-item selection",
  "operating-system containment"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by direct merge preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/worker-launch.md",
  "docs/work-units/python/restart-continuation.md"
 ],
 "target_repositories": [
  "AlienLogicLab/alienintent"
 ],
 "baselines": [
  "main"
 ],
 "required_closure_actions": [
  "direct merge to main",
  "landing record in docs/evidence",
  "remove temporary PRODUCER and VERIFIER worktrees"
 ],
 "stop_escalation_conditions": [
  "a landed interface does not match the packet",
  "a required fact has no existing authoritative record",
  "scope outside the authorized files",
  "the GitHub token API does not honour a requested permission scope (then a separate landing App is required; see section 1)"
 ]
}
```

## 0. The whole design (plain English)

Today a work item that the VERIFIER accepts stops at ACCEPT. `work launch` answers `closure-not-automated`, and a person lands the work. The existing CLOSURE role (`RealWorkerProvider._close`) can attest only `candidate-published`. The coordinator moves a work item to DONE only when every action in the contract's `required_closure_actions` has a receipt (`lifecycle.transition`, action `close`). Packets name those actions in free text, so no receipt can match them.

This unit makes closure a normal launched step. The rule is simple: **a thinking role may ask for effects; deterministic code owns them.**
- the **CLOSURE session** thinks. It reads the accepted work and asks for closure actions. It holds no credential and can change nothing on its own;
- the **control plane** (`RegistryClosure`) prepares the exact landing, writes a durable landing order *before* anything irreversible, reads every effect back, recovers after a crash, and alone issues receipts;
- the **Landing Authority** acts. It is deterministic code. It alone uses a landing-scoped App token, and only for one exact ordered push.

### 0.1 Closure names, receipts and the request

1. **Fixed closure action names.** There are five, in this fixed order: `candidate-published`, `merged-to-main`, `landing-record`, `board-updated`, `workspaces-cleaned`. Each receipt is exact: `<action>:<work item id>:<full candidate revision>`. A new packet lists these five names, and only these, in `required_closure_actions`.
2. **Earlier packets (free-text actions).** A contract whose closure actions are not exactly the five names keeps today's behaviour byte for byte: `work launch` at ACCEPT answers `closure-not-automated` and writes nothing. No CLOSURE session, no escalation, no hold. So there is no authorize-then-refuse loop: nothing is ever written that a decision could lift. Closing those items stays out of scope (section 5).
3. **CLOSURE is a fresh, separate session with no landing power.** This is the B-DISP arrangement. `work launch` at ACCEPT starts the CLOSURE role on the VERIFIER's configured provider and model (the VERIFIER route in `model-routing.json`), in a new session, with a new correlation and its own fresh read-only clone of the candidate. It uses the same worker process as PRODUCER and VERIFIER, with the same `worker_environment` allowlist and context variables, so it gets no App key, no token and no extra environment. Its grant is `git-read` and `process-control`, never `git-write`.
4. **The bounded closure request.** The session's only output is one JSON file outside its clone:
   `{"identity": "<work item id>", "revision": "<full candidate revision>", "actions": [<some of the five names>], "findings": ["<finding>", ...]}`.
   The control plane parses it strictly: exactly these four keys; identity and revision equal the invocation's; distinct names from the five; at most 20 findings of at most 500 characters. A missing or invalid request performs nothing beyond `candidate-published`. An action left out, and every action after it in the fixed order, is not performed.
5. **Session findings are evidence only.** The control plane carries each one as `closure-finding: <text>`. That prefix is fixed, so a session finding can never look like a control-plane finding (0.4) or a receipt. Session findings stay in the invocation journal's outcome line. They are never written to `main`.

### 0.2 The landing order (durable intent before any irreversible effect)

After `candidate-published` reads back and the request asks for `merged-to-main` and `landing-record`, `RegistryClosure` prepares one landing in its own control-plane clone `<verifier root>/landing-<correlation>`, fetched fresh from the remote:
- **base**: the remote default branch head, read now;
- **merge**: a `--no-ff` merge of the candidate onto the base. Its parents are exactly (base, candidate) and its tree must equal the candidate's tree. (So the base must be an ancestor of the candidate; see 0.4 for when it is not.);
- **record**: one commit on top of the merge that adds only the landing record at `docs/evidence/<label in lower case, or the work item id when there is no label>-landing-<first 7 characters of the candidate revision>.md` (the existing naming, for example `restart-continuation-landing-55ba3d1.md`).

The landing record holds **only fixed, bounded facts**, rendered by one deterministic function: the work item id, its label, the full candidate revision, the base, the merge commit, the sha256 of the instructions at the work item's pointer (what `work record-completed` checks), the VERIFIER's correlation, the CLOSURE correlation, the requested action names, and the sha256 of the closure request file. No session text goes to `main`.

Both commits use a fixed control-plane identity: author and committer `AlienIntent Landing <landing@alienintent.invalid>`, set with `-c user.name -c user.email`, with `HOME` set to the landing clone, `GIT_CONFIG_NOSYSTEM=1` and `GIT_CONFIG_GLOBAL=/dev/null`. So no user git configuration or stored credential is read.

Then, **before the first irreversible effect**, `RegistryClosure` appends one secret-free event to the existing invocation journal, the way the PRODUCER journals `PUBLICATION_STARTED` before its push:

`{"event": "closure-ordered", "correlation_id", "work_identity", "role": "CLOSURE", "candidate": <full revision>, "order": {"base", "merge", "record", "record_path", "attempt"}}`

and reads the journal back. If the event does not read back, nothing is pushed. Only SHAs, one path and a small counter are recorded. Never a token, key, key path or URL with credentials.

### 0.3 Effects, in a fixed order, each only after the earlier ones read back

- `candidate-published`: today's check (a fresh clone of the exact candidate from the remote).
- `merged-to-main` and `landing-record` (one landing): the order of 0.2 goes to the Landing Authority (0.5), which pushes the record commit to protected `main` after its checks. Read-backs, from a fresh fetch: the remote default branch contains the record commit; the record's only parent is the merge; the merge's parents are (base, candidate) and its tree equals the candidate's; the landing record passes the shared landing check (section 2, change 9) that `work record-completed` uses, through the same function.
- `board-updated`: after the existing `work display`, the card's display text reads back current, and `read_status` reads back DONE after `write_status(DONE)`. Both are required.
- `workspaces-cleaned`: see 0.7.

### 0.4 Deterministic outcomes when things move or crash

`RegistryClosure` reports to the coordinator only through receipts and a small set of **control-plane findings** with fixed formats. Only `RegistryClosure` makes these. Session findings cannot, because of their fixed prefix.
- `ready-to-land:<merge>`: landing is not enabled (0.6).
- `closure-rework:base-moved:<base>:<head>`: main moved and the candidate does not contain the new head, and our order provably did not land. The candidate is stale. The verified tree cannot land unchanged, and a different tree would be unverified.
- `closure-hold:<reason>:<facts>`: something is ambiguous. The facts are SHAs only.

**Main moved before any push (ordinary concurrent work).** When the Authority refuses because the remote head is no longer the order's base, `RegistryClosure` fetches the new head and decides deterministically:
- the new head is an ancestor of the candidate: the landing is rebuilt on it (a new merge and record, the same tree), journaled as a new `closure-ordered` event with `attempt` + 1, and handed over again. At most 3 orders per closure. A fourth movement ends with `closure-hold:base-unstable`;
- otherwise: `closure-rework:base-moved:<base>:<head>`. The coordinator handles this with the existing `_rework` from ACCEPT (lifecycle already permits `rework` from ACCEPT), counted against the attempt budget, with no escalation. The PRODUCER integrates main and the work is verified again.

**Recovery of a started closure (crash anywhere).** When the next `work launch` recovers a CLOSURE invocation with no journaled outcome, the worker answers from the journal through `reconcile_closure` (section 2, change 4). This **never starts a model session**:
- **no `closure-ordered` event**: nothing irreversible began. The existing missing-terminal-result rule applies (the stage stays ACCEPT and the next launch runs CLOSURE again);
- **the last order's record is reachable from the fetched remote default branch**: the landing happened. The landing receipts are derived from read-back (0.3), and then `board-updated` and `workspaces-cleaned` run. Nothing is pushed again;
- **the remote head is still the order's base**: nothing landed. The same exact order is retried once, through the Authority's full checks. Without a Landing Authority now, the answer is `ready-to-land:<merge>`;
- **the remote head moved and the record is not reachable**: the push is fast-forward only and never forced, so our order did not land. The "main moved" rule above applies;
- **ambiguous**: the remote cannot be read, or the candidate is already reachable from the remote head without our record (someone landed it another way), or the landing record path already exists on the remote with other content. The answer is `closure-hold:landing-ambiguous:<base>:<merge>:<record>:<head or unreadable>`. Nothing is pushed. The hold names these facts in its escalation.

The same reconciliation also runs at the **start** of every later CLOSURE invocation for the same work item and candidate, before any session. It runs on the last `closure-ordered` event of any earlier correlation of this work item. So after a hold is decided with `authorize`, the next launch first settles the earlier order deterministically. A new model session starts only when no earlier order exists or the earlier order provably did not land.

### 0.5 The Landing Authority

It is built only when the `github` entry sets `"landing": true` (the Founder's authorization of the App permission change). It holds its **own** `InstallationCredentials`, created with the landing scope: permissions exactly `{"contents": "write", "metadata": "read"}`, for the one repository. Before pushing, it checks every one of these:
- the coordinator record for the work item is at ACCEPT, and its custodied candidate is the order's candidate;
- the parsed request asks for both `merged-to-main` and `landing-record`;
- the merge's parents are exactly (the order's base, the candidate), and its tree equals the candidate's tree;
- the record commit's only parent is the merge, and it adds exactly one file, the named landing record;
- the remote default branch head is still the order's base;
- the order matches the last `closure-ordered` event journaled for this correlation, and that event reads back;
- the minted token's permissions, as GitHub reports them, equal the landing scope exactly. A token with any other scope is refused (`refused:credential-scope`).

It then puts the token only into the environment of its one `git push <push_url> <record>:refs/heads/<default branch>`, as an `http.extraheader` set through `GIT_CONFIG_COUNT`. Credential helpers are off, `GIT_TERMINAL_PROMPT=0`, and the push has no force flag. The token is never stored, logged, journaled or returned. The Authority answers only `pushed` or `refused:<reason>`. The control plane trusts neither answer: receipts come only from read-back.

### 0.6 "Ready to land" when landing is not enabled

Without `"landing": true` there is no Landing Authority. The CLOSURE session still runs and requests the actions. The control plane issues `candidate-published`, builds and checks the merge and record commits locally, journals nothing irreversible, and pushes nothing. No board change and no cleanup happen, because the work is not landed. The finding is `ready-to-land:<merge>`, and the coordinator records the outcome `ready-to-land`. The work item stays at ACCEPT. This is a verified intermediate state, not completed closure.

`ready-to-land` must not block other work:
- the WIP slot is **released** at `ready-to-land`, because no work is in progress;
- `_eligible` admits a `ready-to-land` item only while `landing_enabled()` is true. So `start()` and `launch()` never run a session for it without landing;
- when landing is enabled, the CLOSURE step must **re-acquire** a WIP slot through the existing `acquire_within` before it runs. A refusal answers `wip-refused` and the item stays `ready-to-land`;
- dependents of the item wait, because it is not DONE. That is the existing dependency rule. Nothing else is blocked;
- a single `start()` call runs CLOSURE for one item at most once. If the item is still at ACCEPT afterwards, it is not picked again in that call. So a landing that keeps failing cannot spin.

### 0.7 Workspace cleanup

`workspaces-cleaned` removes, under the existing ownership checks (the owner has ended and no process carries the correlation's marker), every workspace owned by a correlation of this work item. The correlations come from the invocation journal's `invocation-started` events for this `work_identity`. The workspaces are: retained PRODUCER worktrees and read-back folders, VERIFIER clones, CLOSURE clones (`closure-<correlation>`) and landing clones (`landing-<correlation>`). Each is removed through the existing `RealWorkerProvider.finalize` / `_finalize_recovered` path. The landing clone is removed last, after every read-back. Anything kept is named in `cleanup_diagnostics` with its reason, and then no receipt is issued. Nothing owned by another work item is touched.

### 0.8 One completion path, and the row projection

The coordinator's existing `close` transition (ACCEPT to DONE) is the only way a work item completes. The registry row follows as a **projection**:
1. After the coordinator's DONE record reads back, the coordinator calls the injected hook `completed(identity)`. This happens in `_run`, in `_recover`, and at every `launch()` for each `factory:` record at DONE that `list_states` returns. So a crash at any point is repaired on the next `work launch` of **any** item, whatever the card's board status.
2. The registry's hook does nothing when the row is already DONE. Otherwise it calls `WorkCompletion.record_coordinated(identity, order)`. The `order` is the last `closure-ordered` event journaled for this work item and the custodied candidate, of any correlation. A later CLOSURE may have settled an earlier correlation's order.
3. `record_coordinated` checks the row and contract block (check 1). It checks that the coordinator record is at DONE with all five exact receipts for this item and candidate. It runs the shared landing check on the order's record commit against the configured clone's `<remote>/<default branch>` after a `git fetch <remote> <default branch>` (only the remote-tracking ref changes). Then it builds a real `work-completion` Observation: the same definition, the same `evidence_id`, the same logical id `work-completion/<id>`. Its value holds only facts that never change after DONE: the pointer, contract digest, candidate, base, merge, landing commit, default branch, the landing record file, the coordinator stage, version, receipts and verdict (with the VERIFIER correlation), the release record reference from `work authorize`, the approver, and `"source": "coordinator"`. The same inputs give the same reference.
4. It writes the record and reads it back, then calls the existing `identities.record_completed(id, pointer commit, reference)`. A repeat with the same reference writes nothing.

The existing `WorkCompletion.recorded` reader accepts this record (it checks `evidence_id`, logical id and identity), so dependency admission works for coordinator-closed work. `work record-completed` refuses any work item that has a coordinator record (`COORDINATOR_OWNED`), so it is never a second path.

### 0.9 Recovery of a started item does not depend on the board

`_ready_snapshot` reads only READY cards. Once closure moves a card to DONE, a crash would leave a recovered reservation whose work item is not in the snapshot. Today `_recover` then answers False, and every later launch answers `capacity-unavailable`. Revision 5 adds the coordinator keyword `started_item(identity, correlation) -> ReadyWorkItem | None`. `_recover` uses it whenever the snapshot lacks the reservation's work item. The registry builds that item from the registry record alone: the row (not retired, with a pointer), the packet at the pointer, its contract block, and the row's assessment reference. It requires the contract digest to equal the `contract_digest` of the journal's `invocation-started` event for that correlation. Otherwise it answers None (and recovery answers False, as today, but now only when the registry record itself is unusable).

`launch(identity)` uses `started_item` only for an item whose coordinator record is already at ACCEPT. **Initial admission is unchanged**: an item with no coordinator record, or at IMPLEMENT, is admitted only from the READY view.

## 1. Prerequisites for the real-use proof (not for building or testing)

The offline tests below prove the whole unit. The real landing on the protected `main` needs these first. The unit's real-use check waits for them.
- **The Founder's explicit authorization of the App's permission change.** The factory GitHub App (4990774, installation 162769625) needs a bypass of `main`'s branch protection for the App alone (it already holds `contents: write`, binding rule 4 of the PY-09B contract). The Founder then sets `"landing": true` in the registry configuration's `github` entry.
- **Every token from that installation is scoped.** GitHub applies a bypass to the App actor. Any token from the installation that carries `contents: write` could therefore push to `main`. This unit scopes every token the registry mints (the Landing Authority's token and the `work link` / `work display` / READY-view token, section 2, changes 6 and 7). It cannot scope tokens minted by compositions outside its files: `sandbox_profile.py` mints an unscoped token from the identity in its profile document. So the prerequisite is a recorded check that no other configured composition mints from installation 162769625, or that each one that does is scoped. If that cannot be shown, or if GitHub does not honour the requested scope (stop condition), the same-App design is not enough, and a **separate landing App** (bypass granted to it alone, its key held only by the Landing Authority's user) is required instead. The Landing Authority already takes its own `InstallationCredentials`, so a separate App changes only configuration.
- **Established credential separation for every cognitive worker.** No PRODUCER, VERIFIER or CLOSURE session, and no Factory Director model session, can read the App's private key or mint its token. Only the control plane and the Landing Authority can. Today this cannot be enforced: workers run as the Founder's Unix user, which can read the registry configuration, the key file it names, and the Founder's own git credentials through `HOME`. Separation needs the key and the landing process held by a different Unix user from every cognitive session. That is separate work, to be decided by the Founder.

None of these is a reason to replace automated closure with a permanent manual push.

## 2. The changes

1. **Closure names, receipts, request and findings** (`execution_coordination/domain/closure.py`, new; no I/O).
   - The five names in their fixed order; `is_fixed(required_closure_actions)` (exactly the five).
   - `receipt(action, identity, revision)` and `parse_receipt(text)`.
   - `parse_request(document, identity, revision)`: the requested actions and findings, or a refusal reason, under 0.1 point 4.
   - The control-plane finding formats of 0.4, with `parse_finding(text)`; `SESSION_FINDING = "closure-finding: "`.
2. **The coordinator** (`execution_coordination/application/factory_coordinator.py`).
   - New optional keywords: `landing_enabled: Callable[[], bool]` (false by default), `started_item: Callable[[str, str], ReadyWorkItem | None] | None`, `completed: Callable[[str], None] | None`. Without them, behaviour is unchanged.
   - `launch(identity)` at ACCEPT, in this order, writing nothing before the last step:
     1. resolve the item from the READY snapshot, or else `started_item` (ACCEPT only);
     2. if the contract's actions fail `is_fixed`, answer `closure-not-automated` (as today);
     3. if the outcome is `ready-to-land` and `landing_enabled()` is false, answer `ready-to-land`;
     4. otherwise record the release as today, run `_recover`, then the `completed` sweep (0.8), then `_run` once when `_eligible` admits the item.

     The docstring changes to match.
   - `_eligible`: an item at ACCEPT with outcome `ready-to-land` is eligible only while `landing_enabled()` is true.
   - `_run` for CLOSURE on a `ready-to-land` item: re-acquire a WIP slot with `acquire_within` when the limit is configured and the item holds none (`_WipSkip` on refusal or an unavailable limit, as for the PRODUCER). The repository reservation is taken, held across the whole closure and released exactly as for every role today.
   - `start()`: an item whose CLOSURE run left it at ACCEPT is not picked again in that call.
   - `_release_ended_wip` also releases at outcome `ready-to-land`.
   - `_advance` for `closed`, **only when the contract passes `is_fixed`**:
     - keep only receipts whose `parse_receipt` names this item and the full custodied revision;
     - all five kept: the existing `close` transition, then DONE;
     - only `candidate-published` kept, and exactly one control-plane `ready-to-land:` finding (session findings are ignored by this rule): outcome `ready-to-land`, with no escalation and no dependent blocking;
     - a `closure-rework:` finding: the existing `_rework(..., "closure", findings)` from ACCEPT;
     - anything else, including `closure-hold:`: `authority-block`, with hold reason `closure-receipts-incomplete` or the `closure-hold` reason, and an escalation that names the missing actions or the hold facts.

     For any other contract, `_advance` keeps today's rule byte for byte, so the sandbox and K2 profiles, which close on the bare `candidate-published` from the hookless `_close`, behave exactly as today. `lifecycle.py` is unchanged.
   - `_recover`: use `started_item` when the snapshot lacks the reservation's item. For a CLOSURE invocation whose `read_back` is None, call `reconcile_closure` on the worker when it has one (the same optional-attribute pattern as `finalize`), and continue with its outcome as with any recovered outcome; otherwise park as today. After a recovered DONE reads back, call `completed`.
3. **The CLOSURE grant and the guard** (`composition/role_binding.py`).
   - `ROLE_OPERATIONS` for CLOSURE becomes `{"git-read", "process-control"}`, never `git-write`.
   - `RoleBindingGuard.reconcile_closure(invocation)` passes through to the provider, like `finalize`, only when the guard is bound.
   - `_retain_missing` is unchanged: a `closure-ordered` event already makes the own-event list differ from `["invocation-started"]`, so it never records a missing terminal result over a begun landing.
4. **The CLOSURE worker** (`invocation_runtime/application/real_worker.py`).
   - The constant `CLOSURE_ORDERED = "closure-ordered"`, beside `PUBLICATION_STARTED`. `attest_ownership` treats it like `PUBLICATION_STARTED` (`EFFECT_UNKNOWN`).
   - Beside `WorkerPreparation`, a `ClosureActions` Protocol in the same optional-hook style:
     - `close(invocation, candidate, journal) -> tuple[tuple[str, ...], tuple[str, ...]]` (receipts, findings);
     - `reconcile(invocation, candidate, orders) -> tuple[tuple[str, ...], tuple[str, ...]] | None` (`orders` = the journaled `closure-ordered` events of this work item and candidate, in journal order).
   - `RealWorkerProvider` takes an optional keyword `closure: ClosureActions | None`. Without it, `_close` is unchanged: it runs no session and attests only the bare `candidate-published` (sandbox and K2).
   - With it, `_close(invocation, budget)` does these steps in order:
     1. require `git-read` and `process-control` (refusal: `ineligible`, no session);
     2. if the journal holds an earlier `closure-ordered` event for this item and candidate, call `closure.reconcile`. When that settles the order, return its result **without a session**;
     3. retrieve the fresh clone `<verifier root>/closure-<correlation>` (the `candidate-published` read-back);
     4. call `preparation.prepare(invocation, clone)` (a refusal is returned unchanged);
     5. run the session with the existing `self._process`, as the VERIFIER does (a non-success result is returned as its kind);
     6. call `closure.close(...)`;
     7. return `WorkerOutcome("closed", candidate, findings=…, receipts=(<exact candidate-published receipt>, *receipts))`.
   - `reconcile_closure(invocation) -> WorkerOutcome | None`: only for CLOSURE, with a journal and the hook, when the invocation has no outcome line, its own events include `closure-ordered`, and `attest_ownership` answers `EFFECT_UNKNOWN` (the owner ended and nothing owned is alive). It calls `closure.reconcile` with no session, appends the `invocation-outcome` line (`"reconciled": true`) and returns that outcome. Otherwise it returns None.
   - It never reads or trusts a claim of the session. `RealWorkerProvider` never holds `InstallationCredentials` or the Landing Authority. `worker_provider.py` and `cli_worker.py` are unchanged.
5. **The Landing Authority** (`composition/landing_authority.py`, new, minimal).
   - `LANDING_PERMISSIONS = {"contents": "write", "metadata": "read"}`.
   - `LandingOrder` (frozen): `identity`, `candidate`, `correlation`, `base`, `merge`, `record`, `record_path`, `clone`, `actions`, `attempt`.
   - `LandingAuthority(credentials, repository, default_branch, accepted, ordered, push_url=None)`:
     - `accepted(identity)` returns the custodied candidate when the coordinator record is at ACCEPT, otherwise None;
     - `ordered(correlation)` returns the last journaled `closure-ordered` order;
     - `push_url` defaults to `https://github.com/<repository>.git`; only tests override it, with a local bare repository.
   - `land(order) -> str` performs the checks and the single push of 0.5.
   - It imports no CLOSURE, worker or context code.
6. **Scoped installation tokens** (`installation/application/installation_credentials.py`).
   - `InstallationCredentials` takes the optional keywords `permissions: Mapping[str, str] | None` and `repositories: tuple[str, ...] | None`. With them, `_mint` sends the body `{"permissions": …, "repositories": […]}` through the existing `GitHubTransport.request(..., body=...)` (`_application_call` gains an optional `body`).
   - It then reads the answer back. The answer's `permissions` must equal the request exactly, and `repository_selection` must be `selected`. Otherwise it raises `CredentialUnavailable`. The token is never used before that check.
   - Without the keywords, minting is unchanged byte for byte (the sandbox profile). The module docstring changes to match.
7. **The registry: launch, closure, projection and recovery** (`composition/work_registry.py`).
   - The `github` entry gains the optional boolean `landing` (absent means false). The module docstring's configuration example and text show it and the new behaviour. No other configuration is read.
   - `_links` builds its `InstallationCredentials` with `DISPLAY_PERMISSIONS`: the `work_link.REQUIRED_PERMISSIONS` (`issues: write`, `organization_projects: write`) plus `metadata: read`, for the one repository. **No registry composition mints an unscoped token.** If the PRODUCER finds that WorkLink or the READY view reads repository contents, it adds `contents: read`, never `write`, and says so in its self-review.
   - The Landing Authority is built only when `github.landing` is true, with its own `InstallationCredentials(... permissions=LANDING_PERMISSIONS, repositories=(<name>,))`, never the `_links` one. `accepted` comes from the `registry` coordinator record, and `ordered` from the launch journal.
   - `LaunchPreparation.prepare` for CLOSURE assembles the CLOSURE package with the candidate and clone and resolves the **VERIFIER** route. A contract that fails `is_fixed` is refused with `ineligible` and no session (a guard only; `launch` answers before this point). `deliver` gives CLOSURE its own result text, which names `closure_request_path(invocation_id)` = `<context root>/<invocation id>.closure-request.json`.
   - `_launch_chain` passes `RealWorkerProvider` `closure=RegistryClosure(...)`. It uses the one existing `CliWorkerProvider`: no second worker process, no extra environment.
   - `RegistryClosure` (in this module) implements `ClosureActions` with the existing adapters: `GitSourceControl` and git in the landing clone, the shared landing check (change 9), `work display`, the Projects V2 `write_status`/`read_status`, the journal, and the existing workspace cleanup. It follows 0.2 to 0.7 exactly. It issues each receipt with `receipt()` only from its own read-back, and makes the only control-plane findings.
   - `coordinator()` passes `landing_enabled=lambda: <github.landing>`, `started_item=self._started_item` (0.9) and `completed=self._project_completed` (0.8).
   - `_authorize_refusal` (used by `work decide`) also refuses `authorize` for a parked CLOSURE correlation with a `closure-ordered` event while the remote default branch cannot be read (`remote-unverified`). After `authorize`, settling happens deterministically in the next CLOSURE (change 4, step 2).
8. **The context package for CLOSURE** (`context_assembly/domain/work_context.py` and `application/work_context.py`).
   - `FIELDS` gains CLOSURE: the common fields plus `candidate`, `diff`, `verdict` (the coordinator record's recorded verdict) and `closure_actions` (the five names and the request format).
   - `assemble` admits CLOSURE with a candidate and a clone, as for the VERIFIER.
   - It never gets the PRODUCER's transcript or `producer_self_review`, and it never names a credential, key path or token.
9. **One completion path** (`context_assembly/application/work_completion.py`).
   - Check 2 of `work record-completed` becomes: no coordinator record. Any coordinator record, at any stage, is refused with `COORDINATOR_OWNED`, and nothing is written.
   - The landing check becomes the module-level `landing_check(revisions, read, repo, release_point, candidate, landing, path, identity, instructions)`. `WorkCompletion.record`, `WorkCompletion.record_coordinated` and `RegistryClosure` all call it, so the checks cannot drift.
   - `WorkCompletion.record_coordinated(identity, order)` as in 0.8. Its constructor takes the release-record reader (`StoredReleaseAuthorizations` on the same store) as an optional keyword.
   - `record_completed`'s docstring ("Only `work record-completed` (WorkCompletion) calls this") stays true: only WorkCompletion calls it. The module docstring changes to match.

## 3. Exact permitted files

Production:
- `src/alienintent/execution_coordination/domain/closure.py` (new)
- `src/alienintent/execution_coordination/application/factory_coordinator.py`
- `src/alienintent/composition/work_registry.py`
- `src/alienintent/composition/landing_authority.py` (new)
- `src/alienintent/composition/role_binding.py`
- `src/alienintent/invocation_runtime/application/real_worker.py`
- `src/alienintent/installation/application/installation_credentials.py`
- `src/alienintent/context_assembly/application/work_context.py`, `src/alienintent/context_assembly/domain/work_context.py`
- `src/alienintent/context_assembly/application/work_completion.py`

Tests:
- `tests/execution_coordination/test_factory_coordinator.py`
- `tests/composition/test_worker_launch.py`
- `tests/composition/test_landing_authority.py` (new)
- `tests/composition/test_role_binding.py` (the CLOSURE grant and the `reconcile_closure` pass-through)
- `tests/invocation_runtime/test_runtime.py`
- `tests/installation/test_installation_credentials.py`
- `tests/context_assembly/test_work_context.py`
- `tests/context_assembly/test_work_completion.py`

## 4. Acceptance checks (each names the wrong implementation it catches)

All offline. The provider is fake, from a test routing file, and counts its sessions. The remote is a local bare repository. The board is a fake Projects V2 client. GitHub's token endpoint is a fake `GitHubTransport` that records every mint request body and answers with the permissions requested. Each token is a unique marker string that encodes its scope.

1. **Exact receipts.** For a contract with the five fixed names, each receipt names its action, the work item and the full accepted revision. A receipt for another item or candidate never counts, and neither does a bare name. The existing sandbox and K2 tests that close on the bare `candidate-published` pass unchanged. Catches loose receipts and a change that breaks the existing profiles.
2. **Bounded request.** An unknown action, another identity or revision, an extra key, a duplicate action, an oversized finding or a missing file performs nothing beyond `candidate-published`, and the item stops at `authority-block`. A request that leaves out an action performs neither it nor any later one. A session finding that reads `ready-to-land:<sha>`, `closure-rework:…`, `closure-hold:…` or looks like a receipt is carried only as `closure-finding: …` and never changes the outcome. Catches a free-form request and a session that steers effects or outcomes.
3. **Read-back, never trust.** None of these gets a receipt for the action concerned: a session that writes success claims; a session that pushes to the bare remote itself (the Authority refuses, because the base moved, and then the main-moved rule applies); an Authority stand-in that answers `pushed` without pushing; a merge with a different tree; a landing record without the instructions sha256; a card left in another column. Catches a control plane that trusts the session or the Authority.
4. **CLOSURE is a fresh session on the VERIFIER route, without write power.** The grant is exactly `{"git-read", "process-control"}`. Without `process-control` there is no session and the answer is `ineligible`. The CLOSURE command uses the VERIFIER's routed provider and model, in a new clone with a new correlation. Changing the VERIFIER route changes the next CLOSURE command. Catches a reused session, a separate provider and a `git-write` grant.
5. **The Landing Authority lands only the ordered landing.** `land` answers `refused:<reason>` and leaves the remote unchanged for: the coordinator not at ACCEPT, or another custodied candidate; a request without `merged-to-main` or `landing-record`; merge parents not (base, candidate); a merge tree that differs from the candidate's; a record commit that changes anything other than the one landing record; a remote head that moved; an order that differs from the last journaled `closure-ordered` event; a push that would need force. A valid order fast-forwards the default branch to exactly the record commit. Catches an authority that lands whatever it is handed.
6. **A non-landing token cannot land.** The `_links` credentials' mint body is exactly `DISPLAY_PERMISSIONS` for the one repository, with no `contents` key. The Landing Authority's mint body is exactly `LANDING_PERMISSIONS`. Every mint request the registry makes carries a body, so none is unscoped. A Landing Authority built with the `_links` (display-scoped) credentials answers `refused:credential-scope`, mints nothing further and leaves the remote unchanged. A token endpoint that answers with more permissions than requested makes the mint fail with `CredentialUnavailable`, and nothing is pushed. Without the keywords, the existing installation credential tests pass unchanged. Catches broad tokens inheriting landing power, and an authority that accepts any token.
7. **Credential separation in code.** The token markers, the App key bytes and the key file path never appear in: the PRODUCER, VERIFIER or CLOSURE environment, command, instruction text or context package; any worker clone's git configuration; the invocation journal (including `closure-ordered` events); the landing record. The landing token appears only in the environment of the Authority's one push process. Without `"landing": true`, no Landing Authority is built and no landing-scoped token is minted. `RealWorkerProvider` holds only the `ClosureActions` hook. The merge and record commits carry the fixed `AlienIntent Landing` identity even when the test sets a different global git user. Catches leaked credentials and borrowed user configuration. This proves the code path only. The operating-system separation in section 1 is not proved here.
8. **Durable order before the push; recovery without a model session.** Each crash below is injected, and then the next `work launch` of a **different** work item recovers, with the fake provider's session count unchanged by the recovery:
   - after `closure-ordered` and before the push: the same order is retried once, lands, and all five receipts follow;
   - after the push and before the outcome line: nothing is pushed again (the bare remote's reflog shows one update), the landing receipts come from read-back, and the item reaches DONE;
   - the remote moved to a head that does not contain the record, and the candidate is not in it: the main-moved rule applies, with no push of the old order;
   - the candidate is already in the remote head without our record, or the remote cannot be read: `authority-block` with hold `landing-ambiguous` naming base, merge, record and head, and no push. After `authorize`, the next launch settles the earlier order before any session.

   Catches an order written after the push, a double landing, a lost landing and recovery that depends on a new model request.
9. **Recovery does not depend on board status.** A crash after `board-updated` (the card is in DONE) and before the outcome line: the next launch of another item does not answer `capacity-unavailable`. Recovery finds the item through `started_item`, and the item reaches DONE with its row projected. A `started_item` whose packet's contract digest differs from the journaled one answers None. A work item with no coordinator record whose card is not READY is still `not-eligible`. Catches READY-only recovery and weakened initial admission.
10. **One completion path and the row projection.**
    - Five receipts move the coordinator to DONE, and the WIP slot is released.
    - The row then moves to DONE through `record_coordinated`, with a `work-completion` record whose value is exactly the facts of 0.8. `WorkCompletion.recorded` answers True for it, so a dependent becomes admissible.
    - Crashes between the coordinator's DONE and the evidence write, and between the evidence write and the row write, are each repaired by the next `work launch` of another item, with the card already in DONE. A repeat writes nothing and gives the same reference.
    - `work record-completed` refuses a work item with a coordinator record (`COORDINATOR_OWNED`). No path added here sets DONE outside `close`.

    Catches a second completion path, a nonexistent evidence reference, an unreachable repair and a row that drifts from the coordinator.
11. **Ready to land.** Without `"landing": true`: the prepared commits verify locally; the item stays at ACCEPT with outcome `ready-to-land`; nothing is pushed or journaled as ordered; the card is not moved; no workspace is removed; the WIP slot is released. With a WIP limit of 1, another item is then admitted. A second `work launch` without landing starts no session and answers `ready-to-land`. `start()` starts no CLOSURE session for it. After `"landing": true`, a launch re-acquires a WIP slot (with the slot taken, it answers `wip-refused` and stays `ready-to-land`), runs a fresh CLOSURE and reaches DONE. With landing on and the Authority refusing every time, one `start()` runs CLOSURE once for the item. Catches a fake completion, global starvation and a spinning loop.
12. **Main moved before any push.** The remote moves to a new head that is an ancestor of the candidate: a new order (`attempt` 2) is journaled, and the landing lands with the same tree. Three such moves end in `closure-hold:base-unstable`. The remote moves to a head that is not an ancestor of the candidate: the item goes back to IMPLEMENT through `_rework`, with the finding `closure-rework:base-moved:…`, counted against the attempt budget, with no escalation and no push. Catches concurrent work escalated to a human, and an unverified tree landed.
13. **The landing record holds only fixed facts.** Its bytes equal the deterministic rendering of 0.2 for the recorded facts. With session findings present, none of their text appears in it or anywhere on the remote. Catches free-form session prose on protected `main`.
14. **Cleanup is owned and correlated.** `workspaces-cleaned` removes exactly the workspaces of this item's journaled correlations, the landing clone last. A workspace of another item, and one whose owner is still alive, are kept. A kept workspace is named in `cleanup_diagnostics`, and then no receipt is issued. Catches cleanup of foreign or live workspaces.
15. **Earlier packets are unchanged and gain no path.** A contract with free-text closure actions at ACCEPT: `work launch` answers `closure-not-automated`, writes nothing, starts no session, registers no escalation, and answers the same again. Nothing is merged, pushed, written to the board or cleaned. Catches silently mapped actions, an accidental landing of earlier work and an authorize/refuse loop.
16. **Fitness.** The changed and new test files pass when run together in one run (no full suite), with the unchanged `tests/execution_coordination/test_role_orchestration.py` and `tests/composition/test_sandbox_run_profile.py` in the same run. `tools/fitness/check_architecture.py --root src/alienintent --check all` passes.
17. **Real-use proof (blocked until section 1 is met).** Recorded evidence of all of these:
    - (a) for each cognitive worker identity (the Unix user that runs PRODUCER, VERIFIER and CLOSURE sessions, and any Factory Director model session): reading the App key file and the key path in the registry configuration fails, and an attempt to mint an installation token fails;
    - (b) every configured composition that mints from installation 162769625 mints scoped tokens, or a separate landing App is in use;
    - (c) a token minted with `DISPLAY_PERMISSIONS` is refused by GitHub when it pushes to the protected `main`, and nothing changes;
    - (d) one real CLOSURE of a real accepted work item lands on the protected `main` through the Landing Authority, with all five receipts and the row projected to DONE;
    - (e) one deliberately wrong landing order is refused with nothing pushed.

    Until then, the unit records `ready-to-land` from a real accepted work item as its real-use evidence. That is not completed automated closure.

## 5. Excluded

- operating-system credential separation (section 1; separate work);
- the App permission change, setting `"landing": true`, and any separate landing App (the Founder's actions);
- scoping tokens minted by `sandbox_profile.py` or other compositions outside the permitted files (section 1 prerequisite);
- automatic selection of the next eligible item;
- re-landing work already landed by hand;
- closing earlier coordinator items whose contracts name free-text closure actions (they keep today's `closure-not-automated`);
- a new provider, store, lifecycle stage or configuration source beyond the optional `landing` flag. (The `closure-ordered` journal event and the coordinator outcome `ready-to-land` are new values in the existing journal and record. The projection writes the existing `work-completion` record kind.);
- the general role, capability, Director or Allocator system, beyond this closure slice;
- changing earlier packets.

## 6. Review record

**Revision 5 (2026-10-04).** Fresh independent REVIEWER of revision 4 (BLOCKING B1-B4, MATERIAL M1-M9). Changes:
- B1: recovery of a started item no longer depends on board status. The `started_item` resolver builds the item from the registry record and checks it against the journaled contract digest. The DONE projection sweep reads `list_states`, not the READY view. Initial admission is unchanged.
- B2: a secret-free `closure-ordered` journal event is written and read back before any push. `reconcile_closure` settles a crash with no model session: landed means receipts from read-back; still at base means one exact retry; moved means the main-moved rule; ambiguous means a hold with facts and no push.
- B3: every registry token is scoped through the token API's `permissions` body and read back. The Landing Authority uses its own landing-scoped credential and refuses any other scope. Tokens outside this unit's files, and the possible need for a separate landing App, are named as a prerequisite and a stop condition, not hidden. Check 6 proves that a non-landing credential cannot land.
- B4: the row projection writes a real `work-completion` Observation (`record_coordinated`) and then calls the existing `record_completed`. It is reachable from `_run`, from `_recover` and from every `launch()`, and repairs every crash point. The invented "landing record reference" is removed.
- M1: session findings are always prefixed. The ready-to-land rule counts only control-plane findings.
- M2: the ready-to-land gate is in `_eligible`, and `start()` runs CLOSURE once per item per call.
- M3: the architecture record is removed from `authority_references` and is informative only. The Founder's instruction is quoted in `fixed_decisions`.
- M4: an already-landed order is settled deterministically, both in recovery and before any later CLOSURE session.
- M5: free-text ACCEPT items keep `closure-not-automated` and nothing is written, so no hold exists to authorize and no loop is possible.
- M6: `ready-to-land` releases the WIP slot, and the slot is re-acquired before landing.
- M7: when main moves, the landing is rebuilt (at most 3 orders) when the new head is an ancestor of the candidate; otherwise the work is reworked. Neither case escalates.
- M8: the landing record holds only fixed facts. Findings stay in the journal.
- M9: reservations, the fixed commit identity, correlated cleanup and the docstrings are specified. `installation_credentials.py` and its tests are added to the scope.

**Revision 4 (2026-10-04).** Founder instruction: apply role, capability and authority separation to the closure slice only. CLOSURE no longer lands or holds credentials (grant `git-read`, `process-control`), and produces a bounded request. A minimal deterministic Landing Authority alone uses the App credential. The second credentialed worker process is removed. Effects run in a fixed order. `ready-to-land` no longer moves the card or cleans workspaces. The landing check is shared. Exact receipts apply only to the five fixed names, so the sandbox and K2 profiles stay unchanged. The landing record name is fixed. The real-use proof covers every cognitive worker.

**Revision 2 (2026-10-04).** REVIEWER review of `e4dc9ea` (FAIL), F1-F9, then recheck R1-R7 (wording). Receipts bound before `close`; `ready-to-land` recorded; CLOSURE package fields; row as a projection after DONE; leak checks; no overclaim of separation. F3 and F4 (a `git-write` grant and a second credentialed worker) were superseded by revision 4.

**Revision 1 (2026-10-04).** First draft, against `main` `789240c`, with the Founder's decisions: fixed closure action names with exact receipts; the board update confirms both the text and the card in DONE; no second completion path; CLOSURE as a fresh session on the VERIFIER's provider and model (B-DISP); the factory App as the landing identity pending the Founder's authorization; protected-main landing and credential separation as prerequisites to the real-use proof, not reasons for a permanent manual push.
