# C1 implementation boundaries and review

The approved C1 design is implemented as an explicitly composed local service.
`AttentionProfile` creates the existing SQLite store and S1 immutable evidence
repository under a caller-selected external directory, with injected clock,
attempt IDs, resolver grants, notification channel and optional activation-policy
input. It does not install itself into a live coordinator or bootstrap writer.

`AttentionService.ensure` accepts an already-classified DONE/judgment origin.
Its identity hashes project, profile, work, canonical origin event and kind,
never observation time. Identical origins reuse the current item; conflicting
payloads hold. Each handling mutation uses expected-version CAS; competing
producers either observe the same item or receive VersionConflict, with no blind
decision retry. Notification attempts are written before channel invocation.
A crash leaves an inspectable UNCONFIRMED attempt and does not auto-resend.

Delivery outcomes have separate immutable `attention-delivery:` identities and
CAS pointers. They can complete while a consumer records SEEN or RESOLVED,
without overwriting that handling state or repeating the external notification.
Fresh reads compose the attention history and correlated delivery observations.
The attention version fences handling; delivery observations have their own
versions. The composed `history()` returns the attention chain followed by
delivery chains in attempt order, not a total chronological order across writers.
Notification receipts are advisory delivery evidence, not decision authority or
a claim of arbitrary remote exactly-once delivery. S2's accepted guards remain
unchanged; C1 introduces no authority-bearing episode/liveness effect or lane
adoption. Thus no live guarded sender or automatic activation path is added.

Resolution requires both an applicable composition-supplied resolver grant and
a retrievable immutable Observation with method `attention-resolution`, observer
equal to the resolver, evidence ID equal to the attention identity, current
history input reference, and canonical JSON value containing `item_identity`,
`actor`, `authority`, `work_revision`, `lane`, and `expected_version`. The
Observation records the supplied decision; it does not itself confer authority.
Wrong actor/authority/revision/lane, stale CAS, missing/corrupt evidence, unrelated
records and incorrect correlation refuse resolution. DecisionInbox is untouched.
The composition boundary must supply authenticated actor/authority bindings;
this library API does not authenticate an arbitrary remote caller.

Unbound activation returns a typed hold without invoking the injected launch
capability. An explicitly supplied policy is checked against profile, item,
version, actor, authority, revision and lane; even a matching policy leaves the
episode executor unbound because its fenced admission belongs to later scope.
Zero launches is a measured local spy result, not inferred provider telemetry.

M-ATTENTION reads the bootstrap `item`/`notification`/`ack` append-only schema
(plus explicit SEEN history) from a declared permitted root, with a 10 MiB input
limit. Snapshots retain exact bytes, raw digest, records, stable one-to-one source
aliases and attributed historical states in a separate staging namespace.
Later snapshots must extend the earlier byte history. Historical ACK disposition
never resolves an active product item. Comparison identifies source drift and
pending identities; rollback leaves source and aliases intact and reports the
pending source-owned effects. No switchover, active import, protection retirement,
program mailbox merge or production migration is exposed.

## Preparatory review

A separate read-only code reviewer found two important issues in the initial
implementation: concurrent handling could lose a known delivery outcome, and
resolution accepted an unverified same-scope reference. Ten regression cases
were observed failing before repair. The outcome journal and immutable decision
checks above repair those findings. The second review reported no remaining
critical/important source findings, with 31 focused tests and architecture checks
passing. This is preparatory review, not the fresh BIU verifier verdict.

The development fixture at `development-run/` is preserved as historical evidence:
all ten fault controls discriminated and launch count was zero, but its dirty
source correctly produced HOLD. It must not be cited as clean-candidate acceptance.
The final execution record is generated after source commit; its exact source SHA
and input digests bind the implementation. The later evidence-only commit and
published branch/SHA are bound in the producer Issue result. Reproductions use a
new output directory and the caller's own exact invocation.

Required command:

```sh
rtk proxy python3 tools/evidence/fx_c1_evidence.py --output /tmp/fx-c1-fresh --invocation <exact-invocation>
```

It runs the focused suite, Python regression, architecture checks and Node checks;
then applies each fault exactly once in a disposable source copy, requires the
corresponding assertion failure and restored success, and records durable
readback, raw observations and digest manifest. Any failed command or missing
measurement holds. All evidence remains local composed/mechanical proof; provider
tokens/cost remain UNKNOWN when unavailable. Retained S1/S2 evidence is unchanged.
