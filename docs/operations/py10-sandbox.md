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
| GitHub App | **PENDING** — see below |

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

## Remaining prerequisite — the GitHub App

**A GitHub App cannot be created through the API.** Creation requires either the web UI or the App
Manifest flow, which needs a browser redirect to obtain the conversion `code`. This is the one step
that needs the Founder.

Create it at **Organization settings → Developer settings → GitHub Apps → New GitHub App**, with
exactly:

| Field | Value |
|---|---|
| Name | `AlienIntent PY-10 Sandbox` |
| Homepage | `https://github.com/AlienLogicLab/alienintent` |
| Webhook URL | `https://alienintent-py10-sandbox.factorychecks.com/` |
| Webhook secret | the contents of `~/.config/alienintent-sandbox/secrets/webhook` |
| Repository permissions | **Issues: Read-only**, **Metadata: Read-only** |
| Organization permissions | **Projects: Read and write** |
| Subscribe to events | **Issue comment**, **Project v2 item** |
| Where can this be installed | Only on this account |

The permission set is **exact, not a minimum**: the App preflight compares the installed permissions
by key count as well as value (`src/github/app-client.mjs`), so an extra grant fails closed just as a
missing one does.

Then **install it on `AlienLogicLab/alienintent-sandbox` only**, generate a private key, and store the
`.pem` outside every working tree (`~/.config/alienintent-sandbox/secrets/` alongside the webhook
secret, mode 600). Finally record `applicationId`, `installationId` and `privateKeyPath` in
`profile.json`, whose `githubApp` block is already stubbed with `status: PENDING`.

A ready-made manifest with these exact values is at `~/.config/alienintent-sandbox/app-manifest.json`
if the manifest flow is preferred — it guarantees the permission set rather than relying on the form
being filled in correctly.

## Validation performed

| Check | Result |
|---|---|
| Public hostname reaches the sandbox port | **Proven** — a token served on `127.0.0.1:8789` was returned by `https://alienintent-py10-sandbox.factorychecks.com/` |
| Production ingress unaffected | `https://alienintent.factorychecks.com/` still answers `401` (signature required) from port 8788 |
| Production tunnel untouched | `/etc/cloudflared/config.yml` unmodified (root-owned, no write access held); root `cloudflared` service never restarted |
| Repository identity unambiguous | private repo, linked to Project 2, distinct name and remote from `alienintent` |
| Project identity unambiguous | distinct node id and number; ten lifecycle Status options plus Priority |
| Profile resolves | `GitHubProfile` constructs from the recorded values; secret reference resolves to 64 bytes |
| Secrets outside the repository | profile, tunnel credentials, webhook secret all under `~/.config/alienintent-sandbox/` or `~/.cloudflared/`, mode 600 |
| Sandbox content runs | `python3 -m pytest -q` → 3 passed in the sandbox repository |
| No production resource referenced | profile records an explicit `must_not_touch` list; no production id appears in the sandbox profile |

One correction worth recording: the first `cloudflared tunnel route dns alienintent-sandbox …` bound
the new hostname to the **production** tunnel id, because the command resolved against the root
config rather than the tunnel named on the command line. It was re-routed immediately with an
explicit tunnel id and `--overwrite-dns`, and the end-to-end probe above confirms the hostname now
terminates on the sandbox tunnel. The production tunnel's own ingress rules never contained the
sandbox hostname, so no traffic could have reached a production handler.

## Can PY-10 reach Agent-Ready once PY-09 is DONE?

Yes, once the App exists. Everything else PY-10's readiness depends on is now real and identified:
repository, Project with the required fields, profile, isolated ingress, and a documented environment
a verifier can reproduce. The remaining dependencies are the ordinary BIU ones — PY-05, PY-06, PY-08
and PY-09 accepted.

The sandbox is **not** seeded with the proof backlog: seeding at least three READY BIUs with
priorities, a dependency and one escalation-raising BIU is PY-10's own scope, not provisioning.
