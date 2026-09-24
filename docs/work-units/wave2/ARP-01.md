# ARP-01 — Agent Ready provenance reader: provider-generic native evidence validation

Bounded bootstrap compatibility repair. It is **not** a Wave 2 DAG node and changes no DAG node.
It is prepared as standalone bounded work, like Issue #83 and FDH-01.

Baseline: `origin/main` @ `674b78d2db17`.

## Intent

AlienIntent must recognise every genuine Agent Ready result as native, whichever supported provider
Agent Ready used. The reader must also go on refusing every surrogate that only imitates Agent
Ready's shape.

## Why now

The Agent Ready candidate `fix/claude-capability-probe` (sanookdu/agent-ready) makes Claude-backed
assessments carry host-measured `provider_evidence` with `provider: "claude"`. AlienIntent's reader
hard-requires `provider == "codex"`. Once that candidate lands, every Claude-backed assessment
would be classified non-native and recorded as `EXECUTION_FAILURE`, which blocks FDH-01 and all
later readiness work while Codex capacity is rationed.

## Authority

- Founder direction 2026-09-24: bounded repair, and the only authorised Codex use is **one**
  Codex-backed Agent Ready assessment of this contract. It is a bootstrap compatibility bridge,
  not a new Codex dependency, and not a precedent for bypassing provider neutrality.
- Founder invariant 2026-09-22 (Architecture Authority amendment (b)): a compatible output shape
  is not evidence that the authoritative capability produced the result. This repair must keep
  that invariant intact.

## Scope (bounded extent)

Change only native-Agent-Ready provenance validation in
`tools/evidence/check_assessment_producer.py` (`looks_native_agent_ready` and
`native_provenance_only`), its module documentation, and its tests
`tools/evidence/test_check_assessment_producer.py`.

`provider_evidence`, when present, is native only if it satisfies the **Agent Ready contract** for
provider evidence:

- exactly the keys `provider`, `version`, `compatibility`, `capability_probe`;
- `provider` is a provider Agent Ready supports. This set must not be a new hard-coded answer. It
  comes from one declared source that names each supported provider with its version format, and
  the existing `PROVIDERS` in `tools/orchestration/readiness_assessment.py` must agree with it;
- `version` matches **that provider's** version format:
  - `codex`: `codex-cli <major>.<minor>.<patch>[-+suffix]`;
  - `claude`: `<major>.<minor>.<patch>[-+suffix] (Claude Code)`;
- (`compatibility`, `capability_probe`) is exactly `SUPPORTED`/`REVIEWED_VERSION` or
  `COMPATIBLE_UNVERIFIED`/`PASSED`.

Everything else about native recognition is unchanged:

- the twelve contract fields;
- the MCP envelope;
- the Agent Ready dispositions;
- the refusal of runner-asserted fields;
- the partial-record rules;
- the treatment of assessments with no `provider_evidence`.

## Non-goals

- Changing the readiness adapter, release admission, the dispatcher, any Wave 2 node, or Agent
  Ready itself.
- Reclassifying, editing or deleting any historical assessment or provenance manifest entry. All
  failed, blocked and surrogate evidence is preserved exactly as retained.
- Treating Claude as a special case, or accepting any provider evidence Agent Ready does not emit.

## Dependencies

None open. The reader is independent of the Agent Ready candidate landing: it is correct whether
or not any Claude-backed assessment exists yet.

## Acceptance criteria

1. Valid Codex evidence is accepted, for both `SUPPORTED`/`REVIEWED_VERSION` and
   `COMPATIBLE_UNVERIFIED`/`PASSED`.
2. Valid Claude evidence is accepted, for both pairs, e.g. version `2.1.281 (Claude Code)`.
3. Malformed or unknown evidence is rejected. At least:
   - an unknown provider;
   - a version in the other provider's format;
   - `claude` with version `x`;
   - an invalid compatibility/probe pair;
   - a missing key;
   - an extra key;
   - non-dict evidence.
4. Native provenance stays mandatory:
   - the retained Wave 1 surrogates `docs/work-units/python/PY-09B.assessment.json`,
     `PY-09B.assessment.2026-09-21-needs-clarification.json` and `PY-10.assessment.json` (16-key
     Claude evidence) are still not native;
   - an object carrying runner-asserted fields is still not native;
   - a bootstrap-assessor disposition is still not native;
   - the provenance manifest check passes unchanged on the committed manifests.
5. `native_provenance_only` applies the same provider-generic rule to partial records, with the
   same negative controls.
6. Each new rejection test is shown failing against a deliberately permissive variant before
   passing. A check that cannot fail is not evidence.
7. `node scripts/check.mjs all` exits 0, and the evidence and orchestration Python tests pass at
   the candidate.

## Verification obligations

An independent VERIFIER retrieves the exact candidate SHA in its own worktree. It re-runs criteria
1–7 and applies each negative control. It records the command, exit status and counts. It confirms
that no historical evidence file changed (`git diff --stat` of `docs/` is empty apart from this
BIU's own records).

## Evidence obligations

- Retain the candidate branch and full SHA, the commands, exit codes, test counts and
  negative-control application counts.
- Record this BIU's Agent Ready assessment with its actual provider (`codex`) and state that it is
  the single authorised Codex bridge use.

## Execution packet and allocation

- Configured PRODUCER and an independent VERIFIER.
- Concurrency 1.
- 3 execution cycles and 1 replacement per phase, bound in `execution.biuLimits` before release.
- Wall-clock bounded by systemd supervision.

Landing: SWF-19. Merge the accepted candidate branch directly into the baseline branch, preserving
the accepted SHA. **Do not open a pull request.** AlienIntent does not use pull requests.

Release authority is not granted by this document. Release is additionally held behind the open
worker-credential hold (worker accounts still hold pull-request write) until replacement tokens
pass `worker_credential_probe.sh`.

## Candidate custody

The PRODUCER pins the contract, the baseline, the candidate branch and its full SHA. It publishes
the candidate and records the exact branch and SHA on the Issue before RESULT=VERIFY. A fresh
independent VERIFIER retrieves that exact SHA in its own worktree.

## Stop and escalation

Stop on:

- a source revision mismatch;
- unavailable evidence;
- a failing discriminating probe;
- any need to modify historical evidence.

Scope questions go to the Factory Director. Only a genuine Founder-reserved boundary goes to the
Founder.
