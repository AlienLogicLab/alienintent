# Temporary Factory Director Host

Status: **KEEP_UNTIL_REPLACED.** This is temporary non-cognizant host
infrastructure for the canonical Factory Director while SF-REQ-053 is built. It
is not a Product Requirement, Wave 2 DAG node, policy engine, or a second
cognizant Director.

## What it does

The user-level service owns an exclusive `flock` and a durable lease at
`~/.local/state/alienintent/factory-director-host/lease.json`. It reads one
atomic, externally-produced predicate projection at
`~/.config/alienintent/factory-director-host-input.json`; malformed, missing,
or incomplete input is `AUTHORITATIVE_STATE_UNAVAILABLE` and launches nothing.

When durable inputs say that control is required and execution capacity is
available, absence or exit of the leased bounded Factory Director episode is a
`DIRECTOR_CONTINUITY_FAULT`. The host starts one fresh `codex exec --ephemeral`
episode. When it exits, the host immediately evaluates the same predicates and
starts a successor if control remains. The prompt directs the episode to rebuild
from repository, GitHub, and runtime evidence; it cannot use an earlier
conversation as authority.

The host does not judge work, select product architecture, change lifecycle
state, modify WIP, resolve Founder questions, or change Wave 2 priorities. Its
only durable outputs are lease and append-only `history.jsonl` host receipts.

## Closed predicate

Launch requires every one of: authoritative state, executable capacity, and at
least one of eligible authorized work, Factory Director attention, pending
Director inbox, or lifecycle next-work selection. The only legitimate idle
conditions are no eligible/control work, intentionally full WIP with no other
control action, a pending Founder decision, or explicit pause. Missing state,
ambiguous lease, and unavailable capacity fail closed.

`factory-director-host-input.example.json` is intentionally paused and invalid
for activation. A configured adapter must atomically write all nine booleans;
the file is a projection of existing durable machinery, not a queue, scheduler,
or decision subsystem.

## Installation and inspection

From the repository checkout, run:

```bash
tools/orchestration/install_factory_director_host.sh
```

It copies repository-owned source into the established bootstrap location and
runs `systemctl --user daemon-reload`; it does not enable or start the service.
Before activation, create and configure a dedicated linked Factory Director
worktree in `~/.config/alienintent/factory-director-host.env` as
`FACTORY_DIRECTOR_WORKTREE=/absolute/path`. The host rejects the canonical main
checkout. After an authorized projection has been installed and live coexistence
has been checked against active BIU ownership, activation is explicitly:

```bash
systemctl --user enable --now alienintent-factory-director-host.service
```

Inspect with `systemctl --user status alienintent-factory-director-host` and:

```bash
python3 ~/.local/share/alienintent-bootstrap/factory-director-host/factory_director_host.py \
  --state-root ~/.local/state/alienintent/factory-director-host \
  --inputs ~/.config/alienintent/factory-director-host-input.json \
  --workdir "$FACTORY_DIRECTOR_WORKTREE" \
  --prompt ~/.local/share/alienintent-bootstrap/factory-director-host/factory-director-episode.md \
  --inspect
```

The inspection record reports host/episode state, lease owner and episode id,
last launch reason, last observed exit reason, and latest evaluation reason.

## Retirement gate

Do not retire this host because SF-REQ-053 code or unit tests exist. Retire only
after SF-REQ-053 proves on a real workload that: a fresh no-history episode
activates from a durable factory event; reconstructs authorized state correctly;
advances and persists the next action; exits; and a second fresh episode
continues correctly from that durable state.
