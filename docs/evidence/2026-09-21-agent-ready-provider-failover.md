# Agent-Ready provider failover — PY-10 reassessment

Date: 2026-09-21. Wave 1 bootstrap evidence for post-Wave-1 analysis of Agent-Ready provider
neutrality, capability routing and assessment-evidence comparability. No Product Requirement is
created by this record.

## What happened

PY-10's existing Agent-Ready assessment read **`BLOCKED`**, taken 2026-09-20 at baseline `e25da1f`
with `next_action`: *"Provision the SWF-08 dedicated sandbox, accept PY-05/PY-06/PY-08/PY-09, then
reassess."* Both blockers were resolved — the sandbox passes preflight 17/17, and all four
predecessors are DONE and closed — so a fresh assessment was **mandatory**, not discretionary: SWF-21
condition 2 requires a READY disposition, and a stale BLOCKED result cannot authorize release.

The codex reassessment failed immediately:

```
turn.failed — "You've hit your usage limit … try again at 6:22 PM"
```

**That is a provider-capacity interruption, not a readiness disposition** — the same class as PY-09's
producer interruption earlier the same day, but striking coordinator tooling rather than a worker.

## The failover

Founder-authorized: run the reassessment on the configured `claude` adapter rather than wait ~7.5 hours
for the quota reset.

| | |
|---|---|
| Provider | `claude` (Claude Code CLI, headless) |
| Model | `claude-opus-5[1m]` |
| Invocation | `claude -p --no-session-persistence --output-format json --permission-mode plan --disallowed-tools Edit Write NotebookEdit` |
| Baseline | `85b606037e144e977c1bc1f7b0aa795d97e19d83` |
| Turns / duration | 44 / 401 s |
| Permission denials | none recorded |
| Token and monetary cost | **UNKNOWN** — not reported by this path, never recorded as zero (SWF-09) |

What did **not** change: the PY-10 contract, the request, the assessment semantics, the readiness
criteria, the structured disposition contract, and the SWF-21 release gate.

What did change: **provenance.** PY-01 through PY-09 were all assessed with `codex-cli 0.155.1`. This
one is not provider-identical to them. That is recorded in `PY-10.assessment.json` under
`provider_evidence.provider_failover`, with the superseded assessment named. No binding authority
requires a fixed assessment provider across a wave, so prior codex use is provenance, not a release
precondition.

### Two operational limitations worth keeping

1. **Read-only is enforced differently.** Codex takes `--sandbox read-only`; the Claude path relies on
   `--permission-mode plan` plus disallowed edit tools. Equivalent in effect here — no permission
   denials and no file changes — but it is a different mechanism, not the same flag.
2. **An ambient `ANTHROPIC_API_KEY` broke authentication.** The first attempt returned `401 API key is
   invalid` because the coordinator environment's key took precedence over the subscription login. It
   needed `env -u ANTHROPIC_API_KEY` — which is precisely the ambient-secret filtering the dispatcher's
   worker launcher already performs for workers. Coordinator tooling had no equivalent, and silently
   inherited the wrong credential.

A third, purely mechanical: the CLI's variadic `--disallowed-tools` consumed a trailing positional
prompt as a tool name, producing *"Input must be provided either through stdin or as a prompt
argument"*. The prompt now arrives on stdin.

## Result — the failover worked, and the answer was still no

**Disposition: `SPLIT_RECOMMENDED`.** Rework locality `HIGH`. PY-10 was **not** released.

The finding: the first live GitHub transport (installation token, Projects v2 read and fenced
projection write), a resident webhook ingress bound to the configured host and port, the live doctor
probes, and the sandbox profile composition are **deferred to PY-10 by every predecessor but named in
no BIU's scope — including PY-10's**. Under SWF-20 / SF-REQ-048, unnamed work is a verification
finding, which puts an implementer between under-delivering and failing REVIEW for scope expansion.

Its second point is the sharper one: PY-10 as written is a **single, largely non-repeatable** run over
fourteen coupled acceptance criteria, where a defect surfacing at criterion 11 invalidates the whole
run and forces a re-seed and re-run with real provider spend. PY-05 through PY-09 each needed repair
cycles for adapter work; this contract offers no equivalent iteration surface. That is an argument the
repair-cycle data supports directly — **no BIU in Wave 1 has ever been accepted first-pass**.

Resolving either point amends the PY-02…PY-10 decomposition approved by SWF-08–11, **which SWF-21
forbids the coordinator from deciding**. Recorded and escalated rather than worked around.

## Evidence for the post-Wave-1 questions

- **Provider neutrality:** an Agent-Ready assessment ran to a structurally valid, well-reasoned result
  on a different provider and model with no change to request, semantics or gate. The architecture's
  provider-neutral intent held in practice for this capability.
- **Comparability:** unknown and untested. This assessment is more sceptical than its codex
  predecessor, but the predecessor ran against a *different baseline* and a *different world* (no
  sandbox, predecessors unaccepted), so the difference cannot be attributed to the provider. One
  observation is not a comparison.
- **Capability routing:** the interruption argues for routing an assessment to any provider with
  capacity rather than a fixed one — but the comparability question above must be settled first, or
  routing silently varies the readiness bar.
- **Downstream release behaviour remained valid:** the non-READY result was honoured exactly as a codex
  non-READY result would have been. The failover authorization did not become permission to release.
