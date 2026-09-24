#!/usr/bin/env bash
# Installs the Factory Director Host only.  It deliberately does not enable or start it,
# and it never writes the Director-owned hold record, inbox or pause flag: an absent hold
# record or inbox keeps the host failed closed until the Factory Director creates them.
set -euo pipefail

source_root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd "$source_root/../.." && pwd)
target_root="${HOME}/.local/share/alienintent-bootstrap/factory-director-host"
unit_root="${HOME}/.config/systemd/user"
config_root="${HOME}/.config/alienintent"
state_root="${HOME}/.local/state/alienintent/factory-director-host"
mkdir -p "$target_root" "$unit_root" "$config_root"
install -m 0700 "$source_root/factory_director_host.py" "$target_root/factory_director_host.py"
install -m 0700 "$source_root/factory_director_inputs.py" "$target_root/factory_director_inputs.py"
install -m 0600 "$source_root/codex_session.py" "$target_root/codex_session.py"
install -m 0600 "$repo_root/tools/live/project_materialization.py" "$target_root/project_materialization.py"
install -m 0600 "$source_root/factory-director-episode.md" "$target_root/factory-director-episode.md"
install -m 0644 "$source_root/systemd/alienintent-factory-director-host.service" "$unit_root/alienintent-factory-director-host.service"
if [[ ! -e "$config_root/factory-director-host.json" ]]; then
  install -m 0600 "$repo_root/config/factory-director-host.example.json" "$config_root/factory-director-host.json"
fi
if [[ ! -e "$config_root/factory-director-host.env" ]]; then
  install -m 0600 /dev/null "$config_root/factory-director-host.env"
  printf '%s\n' '# Set FACTORY_DIRECTOR_WORKTREE to a dedicated linked worktree, never main.' \
    '# Set GH_CONFIG_DIR to a gh configuration that can read Project #1 and Issue comments.' \
    >> "$config_root/factory-director-host.env"
fi
cat > "$target_root/factory-director-host.sh" <<SCRIPT
#!/usr/bin/env bash
set -euo pipefail
: "\${FACTORY_DIRECTOR_WORKTREE:?set an isolated linked worktree in factory-director-host.env}"
exec python3 "$target_root/factory_director_host.py" \\
  --state-root "$state_root" \\
  --config "$config_root/factory-director-host.json" \\
  --workdir "\${FACTORY_DIRECTOR_WORKTREE}" \\
  --prompt "$target_root/factory-director-episode.md"
SCRIPT
chmod 0700 "$target_root/factory-director-host.sh"
systemctl --user daemon-reload
printf '%s\n' "installed but not activated: systemctl --user enable --now alienintent-factory-director-host.service"
