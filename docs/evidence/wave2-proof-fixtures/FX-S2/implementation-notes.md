# WO-220103 implementation and proof qualifications

## Guarded path

`FencedOperationalStore` extends the existing port. `SQLiteOperationalStore`
keeps schema 2 and its existing tables; internal schema-1 records occupy the
reserved `__fenced__:` aggregate namespace. Legacy methods remain usable on
unadopted lanes. Guarded operations require an explicit injected clock; omission
fails closed instead of assuming a valid tenure.

A `GuardVector` pins aggregate revisions, authority identity, epoch and invocation.
Authority is an existing versioned aggregate with `schema_version=1`, `active`,
`epoch`, `invocation`, and finite `expires_at`. Its producer is the authorized
caller; this storage extension does not create product or release authority.
`active=False` is the generic suppression/revocation input. An episode/liveness
policy engine is outside S2. Admission compares all revisions and checks authority
inside the same `BEGIN IMMEDIATE` transaction as reservation validation and the
unique intent/claim. Claim also requires the exact vector persisted by intent,
including the target aggregate revision advanced at intent. A caller cannot omit
or refresh a component to resurrect stale work.

The first guarded intent atomically adopts its target aggregate as a lane. All
nonconfirmed legacy work on that lane must already be reconciled. Adoption fixes
the lane's reservation resource set; owner/fences may advance only after safe
completion. Every legacy state/effect mutation, dispatch, confirmation and
unknown-effect override on that lane refuses. The reserved metadata namespace is
also protected from public legacy aggregate writes. Ingress receipt recording
remains compatible; applying it to an adopted lane requires a guarded participant.

`acquire_many` sorts `(scope,key)` under one profile and one transaction. SQLite's
write lock serializes processes. Contention rolls back the attempt, preserving
all previously retained reservations. Pending and unknown guarded effects prevent
release; elapsed time, restart, revoked authority and missing readback do not
permit reassignment. This implementation conservatively supports completion-based
release only; it does not invent a process-death authority adapter.

## Consumer and composition

`FencedProfile` composes the store and `GuardedEffectExecutor` with an explicit
clock. Its effect consumer is **local durable journal delivery**. Admission and
acceptance/outcome commit in the same SQLite transaction. Effect identity is
profile-scoped and unique; concurrent or delayed duplicates return the same
persisted receipt while their authority remains valid. Readback does not send.
The receipt digest binds profile, aggregate, full vector, invocation, reservations,
payload digest and accepted outcome. Confirmation requires the exact persisted
correlated receipt and retained reservation fences. Completion may be confirmed
after tenure expires; expiry cannot admit another delivery.

The local consumer is not a general arbitrary callback or an exactly-once network
transport. No remote provider/lane, existing coordinator or Node bootstrap was
adopted. Any future lane adoption must route every participant through guards and
provide a fencing/dedup/readback contract at its actual effect boundary. Unknown
remote effects must retain exclusive ownership when such a contract is absent.

## M-FENCING and rollback

Old methods, schema/version migrations, profile identity and effect payloads remain
compatible outside adopted lanes. Same-database probes cover guarded intent,
claim, local consumer receipt and confirmation. An adopted lane has no API for
falling back to unguarded dispatch. Operational rollback is not performed or
exposed here: first quiesce all senders, reconcile unknown effects and reservations,
and obtain the applicable migration authority before using an older binary. An
older binary is not claimed to understand guarded metadata.

## Review and preserved proof

A separate read-only local reviewer reproduced one material finding: the initial
consumer digest omitted profile provenance. A failing regression reproduced
cross-profile receipt substitution. Receipts now bind profile, aggregate and full
vector as well as invocation/fences/payload; the regression passes. The reviewer
inspected the repair and independently ran 40 focused tests successfully. Later
coverage adds suppression, expiry at both claim/consumer, pending legacy claim,
and missing-clock refusal. Local review is not the allocated BIU verifier verdict.

Full regression initially reported 464 passed / 1 failed. The failure was the
historical S0 `P11` byte-identity check: the approved S2 extension changes
`sqlite_store.py`, which S0 pins to its own baseline. All other S0 predicates passed.
The S0 production checker, immutable manifest and retained proof are unchanged.
The test-only repair runs the original positive proof in a disposable local clone
at S2 admission `0515444b5c43c83f4a5e26c9ec2c5956f064e1d9`, verifying exact checkout
and manifest bytes. A new current-source negative test requires the full original
predicate set, exactly P11 failing, and exactly `sqlite_store.py` changed among
pinned kernel paths. This preserves the old invariant rather than declaring the
new adapter byte-identical. Independent review approved that separation and ran
both tests successfully. The prior full-suite failure remains retained evidence.

S0's 12 artifact digests and S1's 19 content-addressed artifact hashes were checked;
both accepted candidate SHAs are ancestors of the S2 admission baseline. No prior
observation/verdict is replaced. Success-collapse, platform and local-proof
qualifications remain; these tests establish no live-operation result.

## Custody

Morty owns the runtime-managed candidate branch
`b-disp/e7a6312c-eb0d-4635-af4e-edf0c36b3e9e`. Candidate publication is followed by
remote SHA readback and one exact invocation result comment. Independent workflow
verification is pending; final source-control closure depends on that separate
invocation and the authorized BIU closure phase. Runtime-owned resources remain
retained for that dependency; they must not be manually removed by this active
worker. No direct main push, merge, deployment, service/profile change, bootstrap
retirement, pending policy amendment or other-repository mutation is performed.
