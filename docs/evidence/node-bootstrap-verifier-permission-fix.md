# Critical Node-bootstrap compatibility fix — Claude VERIFIER permission mode

Date: 2026-09-19. Status: bootstrap compatibility record.
Authority: Founder authorization of 2026-09-19 under Architecture Authority §42,
"Node is frozen except for critical bootstrap fixes".
Origin: AlienIntent Issue #2 (PY-01).

## This is not the canonical Python design

**This record documents a compatibility repair to the frozen Node bootstrap. It is
not, and must not be cited as, the canonical Python AlienIntent capability and
authority design.** That design is governed by binding FD-03: per-BIU capability
profiles with explicit BIU-specific additions, fail-closed budgets, and grants
recorded with target, actions, limits, expiry and revocation. The Node bootstrap
has no such model; it carries a fixed per-worker permission string. Nothing here
constrains or pre-empts the Python capability model, and gate rows G11 and G12
remain unaffected.

## The defect

`src/config/profile.mjs` validated worker permission modes against an adapter-specific
allowlist. For the `claude` adapter the allowlist contained exactly one value:

```js
const modes = w.provider.adapter === "codex"
  ? ["read-only", "workspace-write", "danger-full-access"]
  : ["manual"];
```

`manual` means "ask a human to approve each tool call". Workers are launched
non-interactively with `-p`, and the Claude CLI documents that with `--print` the
permission prompt goes to a host which, absent a prompt answerer, denies
automatically. A `manual` Claude worker therefore cannot execute a single tool call.

The VERIFIER role was consequently non-functional. Invocation
`AlienLogicLab/alienintent#2:VERIFIER:f3a4ff9e-eaa6-42a5-8229-5fff977bd8c2` recorded
eight consecutive permission denials — it could not read `AGENTS.md`, the Issue, or
the repository — then exited 0 without publishing a result. The lifecycle could not
progress past VERIFY for any BIU.

This is critical rather than cosmetic: the bootstrap could not complete a work-unit
lifecycle at all.

## The fix

One line. `manual` is retained; `bypassPermissions` is added.

```js
const modes = w.provider.adapter === "codex"
  ? ["read-only", "workspace-write", "danger-full-access"]
  : ["manual", "bypassPermissions"];
```

Validation is not weakened: codex-only modes and unknown values are still rejected
for the claude adapter.

## Why `bypassPermissions` and not another mode

The installed Claude CLI supports `acceptEdits`, `auto`, `bypassPermissions`,
`manual`, `dontAsk` and `plan`.

- `acceptEdits` auto-accepts file edits only. Every observed denial was a `Bash`
  call, so this does not address the failure.
- `dontAsk` does not prompt but denies anything not pre-approved. Pre-approval lives
  in the Claude settings under the worker's `HOME`, which for this deployment is the
  operator's own shared Claude configuration. That configuration is explicitly out of
  scope, so this mode would reproduce the failure.
- `auto` routes decisions to a model classifier. A verifier that must reliably
  complete cannot depend on a non-deterministic approval gate that may deny
  mid-review.
- `plan` executes no tools.
- `bypassPermissions` is deterministic and prompt-free.

The grant is bounded by what it does not change. The VERIFIER already ran inside an
isolated disposable worktree; its GitHub reach is bounded by a separate per-worker
credential rather than by the Claude permission mode; and the PRODUCER already runs
at `danger-full-access`, which is strictly more powerful because it mutates and
publishes. The deployment's overall authority envelope is therefore unchanged.

## Verification

- Out-of-tree probe reproduced the rejection before the change and acceptance after,
  while confirming `manual` still loads and invalid values are still rejected.
- Complete Node regression suite after the change: runtime 309/309, rai 18/18,
  profile 19/19, preflight exit 0, `scripts/check.mjs all` exit 0.
- Service restarted and reached healthy preflight.
- A fresh VERIFIER launched with `--permission-mode bypassPermissions`.

## Retirement

This record is superseded when the Python implementation supplies the FD-03
capability and authority model and the Node bootstrap is retired at Python
Sovereignty under Authority §43.
