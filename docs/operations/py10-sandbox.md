# PY-10 live-proof sandbox — provisioned resources

Provisioned 2026-09-21 under Founder authorization, satisfying the [SWF-08](../decisions/2026-09-20-wave1-plan-approval-d1-d2.md)
prerequisite of the [PY-10 contract](../work-units/python/PY-10.md). **Test/integration
infrastructure only** — not a product deployment, not a second environment for real work.

No secret value appears here or anywhere in this repository.

## Resource identities

| Resource | Identity |
|---|---|
| Repository | [`AlienLogicLab/alienintent-sandbox`](https://github.com/AlienLogicLab/alienintent-sandbox) — **private**, default branch `main`, initial commit `ab68d3a` |
| Project | **AlienIntent Sandbox — Wave 1 live proof**, org `AlienLogicLab`, number **2**, node id `PVT_kwDOEcrpC84BkIEX` |
| Project Status field | `PVTSSF_lADOEcrpC84BkIEXzhi5x34` — options CAPTURE, SPECIFY, PLAN, TASKS, READY, IMPLEMENT, VERIFY, REVIEW, ACCEPT, DONE |
| Project Priority field | `PVTSSF_lADOEcrpC84BkIEXzhi5x-w` — options P0…P5 |
| Profile | `py10-sandbox` — `~/.config/alienintent-sandbox/profile.json` (mode 600, outside every working tree) |
| Ingress hostname | `https://alienintent-py10-sandbox.factorychecks.com/` |
| Tunnel | `alienintent-sandbox`, id `18070794-2823-44fd-9700-deb9fb93bdf8`, credentials `~/.cloudflared/18070794-….json` (mode 600) |
| Tunnel config / unit | `~/.config/alienintent-sandbox/tunnel.yml` · `alienintent-sandbox-tunnel.service` (`systemd --user`) |
| Local ingress port | **8789** |
| Webhook secret | reference `py10-sandbox-webhook` → `~/.config/alienintent-sandbox/secrets/webhook` (mode 600, 64 hex chars, never committed) |
| GitHub App | `alienintent-py-10-sandbox` — **App id 5014629**, **installation id 163346526**, installed on the sandbox repository only; private key at `~/.config/alienintent-sandbox/secrets/…private-key.pem` (mode 600) |

The profile maps one-to-one onto `alienintent.installation.domain.github_profile.GitHubProfile`;
constructing that type from the recorded values succeeds, and the secret reference resolves through
`ProtectedLocalFileSecretProvider` without exposing the value.

## Isolation — the binding interpretation

Founder decision, 2026-09-21:

> Sharing the existing Cloudflare account and `factorychecks.com` DNS zone is permitted. The DNS zone
> is shared administrative infrastructure only; runtime ingress is isolated.

PY-10 must **not** share, modify, restart or depend on: the FactoryChecks/B-DISP tunnel
(`6127f451-4e3a-4ae4-b968-9d1495471383`), its credentials, its ingress routes, its local ports
(8787, 8788), its root `cloudflared` service, the production GitHub App identity, its webhook secret,
or FactoryChecks application/runtime infrastructure.

Everything above is separate: own tunnel id, own credentials file, own config, own hostname, own
port, own user-level unit, own webhook secret, and (once created) its own App identity.

## GitHub App — provisioned 2026-09-21

Created and installed by the Founder (App creation has no API path; it requires the browser).
Identities were then discovered from `GET /orgs/AlienLogicLab/installations` and verified against the
private key, not taken on trust:

| | |
|---|---|
| App | `alienintent-py-10-sandbox`, id **5014629** |
| Installation | **163346526**, account `AlienLogicLab`, `repository_selection: selected` |
| Repositories | exactly `AlienLogicLab/alienintent-sandbox` |
| Permissions | `issues: read`, `metadata: read`, `organization_projects: write` — **exactly** the set the App preflight enforces |
| Events | `issue_comment`, `projects_v2_item` — exactly |
| Private key | `~/.config/alienintent-sandbox/secrets/alienintent-py-10-sandbox.2026-09-20.private-key.pem`, mode 600, outside every working tree |

The production App (4990774 / installation 162769625) is untouched and appears nowhere in the
sandbox profile.

## Residual risk — organization-scoped Projects permission

`organization_projects` is an **organization** permission. GitHub provides no way to scope a Projects
grant to a single project, so the sandbox installation token **can reach every org Project, including
production Project #1**. This was verified read-only rather than assumed: the sandbox token returns
`PVT_kwDOEcrpC84Bj5i_` ("AlienIntent") when asked.

Repository isolation is genuine — the installation grants exactly the sandbox repository, and no
production repository access exists beyond what any reader of a public repository has. Project
isolation, however, **cannot be enforced by the token**. The compensating controls are:

1. the sandbox profile names `PVT_kwDOEcrpC84BkIEX` (Project 2) and nothing else;
2. PY-10 acceptance criterion 16 already requires evidence that the live AlienIntent Project and the
   Node bootstrap were demonstrably unaffected — no Python-originated event, projection or dispatch.

**Resolved 2026-09-21 by [SWF-34](../decisions/2026-09-21-sandbox-isolation-standard.md).** The Founder
accepted this residual risk for the Wave 1 live-proof sandbox rather than provisioning a separate
organization. The canonical standard: repository isolation is **permission-enforced**, Project
isolation is **configuration-enforced** (deterministic, exclusive, fail-closed addressing of Project
#2), and PY-10 AC 16 is the compensating end-to-end control proving production Project #1 was
unchanged during the live proof. PY-09B must not claim token-level Project isolation, because
`organization_projects` cannot provide it.

The acceptance does not extend beyond this sandbox: higher-assurance deployments may require a
separate organization or account boundary.

## Validation performed

Full preflight: `python3 ~/.local/share/alienintent-bootstrap/py10_preflight.py` — **17/17 checks
pass**, exit 0. It reads and changes nothing, and prints no secret value.

| Check | Result |
|---|---|
| Profile records App identity; key present and mode 600 | PASS |
| Profile loads as `GitHubProfile`; webhook secret resolves (64 bytes) | PASS |
| App authenticates with the private key | PASS — `HTTP 200`, slug `alienintent-py-10-sandbox` |
| App permissions / events exactly least privilege | PASS — extra or missing grants both fail closed |
| Installation belongs to this App, repository-scoped | PASS — `repository_selection: selected` |
| Installation token mints; reaches only the sandbox repository | PASS — `['AlienLogicLab/alienintent-sandbox']` |
| Installation scope excludes the production repository | PASS |
| Sandbox issues readable with the installation token | PASS |
| No production identifier in the sandbox profile | PASS |
| Sandbox tunnel active | PASS |
| Organization Projects permission is org-wide | **NOTE** — recorded above, not a pass disguising a limitation |

**Live webhook delivery, end to end.** A comment on sandbox issue #1 produced delivery
`07400e60-b547-11f1-9366-b6eebd3f7f46`:

| | |
|---|---|
| Event | `issue_comment` |
| Hook target | `5014629` (`integration`) — the sandbox App, not the production one |
| Installation in payload | `163346526` |
| Repository | `AlienLogicLab/alienintent-sandbox` |
| Ingress | arrived on `127.0.0.1:8789` through `alienintent-py10-sandbox.factorychecks.com` |
| Signature | **valid** under the sandbox webhook secret |
| Negative control | the same body and signature verified against a wrong secret is **rejected** |

Earlier, before the App existed, a token served on `127.0.0.1:8789` was returned by the public
hostname, proving the route itself. During both probes `https://alienintent.factorychecks.com/`
continued to answer `401` from port 8788, `/etc/cloudflared/config.yml` stayed unmodified, the root
`cloudflared` service was never restarted, and PY-08 kept running.

Sandbox issue #1 was closed after the probe; it is not part of the PY-10 proof backlog.

## Can PY-10 reach Agent-Ready once PY-09 is DONE?

**Yes.** The App exists, the environment is verified end to end, and everything PY-10's readiness depends on is real and identified:
repository, Project with the required fields, profile, App identity, isolated and proven ingress, and
a documented environment a verifier can reproduce with one command. The remaining dependencies are the
ordinary BIU ones — PY-05, PY-06 accepted, PY-08 and PY-09 to follow.

The sandbox is **not** seeded with the proof backlog: seeding at least three READY BIUs with
priorities, a dependency and one escalation-raising BIU is PY-10's own scope, not provisioning.
