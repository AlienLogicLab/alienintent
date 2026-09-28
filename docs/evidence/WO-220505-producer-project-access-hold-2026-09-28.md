# WO-220505 producer project-access hold

## Identity and authority

- Invocation: `AlienLogicLab/alienintent#125:PRODUCER:7ef7de13-0504-4748-a783-b3be00a2b6f3` (Morty).
- Worktree: `/home/netmarine/.local/state/alienintent/worktrees/655dd452-e3ff-4904-8dbd-226493a3d04f`, branch `b-disp/655dd452-e3ff-4904-8dbd-226493a3d04f`; clean on entry.
- Entry commit: `b4d773d5f4468a2e8c5e3c5ee426bc89b6c7ae8a` (current `origin/main`). Release baseline is `af1f2daa96d9fa62624e94a7b428d3b52c645365`; the two intervening commits clarify #125's real-gap acceptance and explicitly keep the real-lane wiring in this BIU's scope.
- Issue authority: Founder YES on #125's own real lane (comment 5872218295), READY and IMPLEMENT release (comments 5873006116 and 5873015705), and Factory Director repair direction (comment of 2026-09-28 15:32:47 UTC). The prior producer preflight is retained on `b-disp/9f9f1d29-6e8d-47a3-b840-7f365cb6f2e3` at `8daef6db1ce0c9a982da79b72ec1db61031053e3`.
- This is a pre-implementation credential and readback gate at 2026-09-28 15:35 UTC. It is neither FX-B2 execution nor operational AC-08 proof.

## Read-only observations

| Check | Exact command | Exit and observation |
| --- | --- | --- |
| Worker identity | `rtk proxy gh api user --jq .login` | 0; `morty-worker`. `rtk git config user.name` and `rtk git config user.email` returned `Morty` and `morty-worker@factorychecks.com`. |
| Bound dispatch | Read-only selection of `active` from `/home/netmarine/.local/state/alienintent/state.json` | The `AlienLogicLab/alienintent#125:PRODUCER` entry records this exact invocation, Issue 125, `IMPLEMENT`, and this worktree. This is a momentary observation, not a live-window admission. |
| Incumbent bootstrap | `rtk proxy env XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus systemctl --user is-active alienintent-liveness.service` | 0; `active`. The bare command without this user-bus environment returned `Failed to connect to bus: No medium found`, which is not a service failure. |
| Project readback | `rtk proxy python3 tools/live/project_materialization.py verify 125 --expect-status IMPLEMENT` | 1; `gh api graphql failed: gh: Resource not accessible by personal access token`. |
| Project API | `rtk proxy gh api graphql -f 'query={ organization(login:"AlienLogicLab") { projectV2(number:1) { id } } }' --jq '.data.organization.projectV2.id'` | 1; Project v2 is `null`, `FORBIDDEN`, `Resource not accessible by personal access token`. |
| Project item list | `rtk proxy gh project item-list 1 --owner AlienLogicLab --format json --limit 200 --jq '.items[] | select(.content.number==125) | {id,title,status,content}'` | 1; `Resource not accessible by personal access token (organization.projectV2)`. |
| Issue access | `rtk proxy gh api repos/AlienLogicLab/alienintent/issues/125 --jq '{number,title,state}'` | 0; Issue 125 is open and readable. |

`gh auth status` identifies the active GitHub account as `morty-worker` under `/home/netmarine/.config/gh-morty/hosts.yml`. The token value is not retained here. No other identity or credential was substituted for Morty.

## Disposition

The Director's adapter and fenced Project consumer remain in scope, but the live procedure requires direct Project #1 readback before any mutation and after the exact effect. Under this invocation's bound credential, even the existing read-only board verifier is denied. A new adapter could be unit-tested locally but cannot prove real Project observation, mutation or exact readback, and the phase-2 one-writer window cannot be opened safely. The isolated FX-B2 root `/home/netmarine/.local/state/alienintent/fx-b2` was also absent at preflight; phase 1 was not run.

No bootstrap stop/start, real gap induction, Project mutation, profile provisioning, provider call, or change to another repository was performed. Preserve the incumbent bootstrap and prior evidence. Restore Project #1 read/write and readback capability to Morty's authorized credential (or bind an explicitly authorized factory credential with the same scope and custody), verify it with `project_materialization.py verify 125 --expect-status IMPLEMENT`, then resume the Director's bounded adapter, fixture and two-phase proof sequence in a fresh producer invocation. This packet is a `FOUNDER_EXCEPTION` protocol disposition for an unavailable external prerequisite, not an assertion that Founder intent is unresolved and not a VERIFY candidate.
