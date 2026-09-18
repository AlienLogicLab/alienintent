# AlienIntent

**by Alien Logic Lab**

AlienIntent keeps autonomous software engineering aligned with intent, evidence, and outcomes.

Repository: [AlienLogicLab/alienintent](https://github.com/AlienLogicLab/alienintent).

AlienIntent was previously developed under the working name B-DISP.

The standalone runtime admits bounded GitHub Project work, launches independent
producer and verifier identities in disposable Git worktrees, correlates authenticated
Issue results with exact invocations, and handles acceptance and closure. The lifecycle
is CAPTURE → SPECIFY → PLAN → TASKS → READY → IMPLEMENT → VERIFY → REVIEW →
ACCEPT → DONE. The Node execution engine dispatches only IMPLEMENT, VERIFY and ACCEPT.
Merge/landing is a repository operation during closure after ACCEPT, not a lifecycle state.

## Run and verify

Use Node.js 24.15.0 on Linux. Run `npm test` for all required regression groups,
including worker preflight and the offline self-hosting rehearsal. RAI tests run
separately; RAI is not wired into runtime execution.

Run `node bin/alienintent.mjs --help` without credentials. After installing this
package, the public command is `alienintent`. The temporary `b-disp` command and
`bin/b-disp.mjs` entry point are compatibility aliases; migrate scripts to
`alienintent` before a future breaking release removes them.

See [operations](docs/operations.md) and the synthetic
[profile example](config/profile.example.json) for configuration. Keep installation
credentials and operational state outside the repository. Execution requires an
organization-owned repository, Project, and GitHub App installation, with distinct
producer, verifier, and operator identities.

Offline rehearsal is not live self-hosting evidence. Installation and live proof
must be verified independently before operational use.

## Agent instructions

Follow [AGENTS.md](AGENTS.md), the
[governing directive](docs/migration/agent-packages/GOVERNING_AGENT_DIRECTIVE.md),
and the [work-packet template](docs/templates/work-packet.md).
Known authorized uncommitted work does not block progress. Preserve historical
evidence and compatibility identifiers; do not publish private installation history.
