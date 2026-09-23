#!/usr/bin/env bash
# Installs the temporary host only.  It deliberately does not enable or start it.
set -euo pipefail

source_root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
target_root="${HOME}/.local/share/alienintent-bootstrap/factory-director-host"
unit_root="${HOME}/.config/systemd/user"
config_root="${HOME}/.config/alienintent"
mkdir -p "$target_root" "$unit_root" "$config_root"
install -m 0700 "$source_root/factory_director_host.py" "$target_root/factory_director_host.py"
install -m 0700 "$source_root/codex_session.py" "$target_root/codex_session.py"
install -m 0700 "$source_root/director.py" "$target_root/director.py"
install -m 0600 "$source_root/factory-director-episode.md" "$target_root/factory-director-episode.md"
install -m 0644 "$source_root/systemd/alienintent-factory-director-host.service" "$unit_root/alienintent-factory-director-host.service"
if [[ ! -e "$config_root/factory-director-host-input.json" ]]; then
  install -m 0600 "$(cd "$source_root/../.." && pwd)/config/factory-director-host-input.example.json" "$config_root/factory-director-host-input.json"
fi
if [[ ! -e "$config_root/factory-director-host.env" ]]; then
  install -m 0600 /dev/null "$config_root/factory-director-host.env"
  printf '%s\n' '# Set FACTORY_DIRECTOR_WORKTREE to a dedicated linked worktree, never main.' >> "$config_root/factory-director-host.env"
fi
cat > "$target_root/factory-director-host.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
: "\${FACTORY_DIRECTOR_WORKTREE:?set an isolated linked worktree in factory-director-host.env}"
exec python3 "$target_root/factory_director_host.py" \\
  --state-root "${HOME}/.local/state/alienintent/factory-director-host" \\
  --inputs "$config_root/factory-director-host-input.json" \\
  --workdir "\${FACTORY_DIRECTOR_WORKTREE}" \\
  --prompt "$target_root/factory-director-episode.md"
EOF
chmod 0700 "$target_root/factory-director-host.sh"
systemctl --user daemon-reload
printf '%s\n' "installed but not activated: systemctl --user enable --now alienintent-factory-director-host.service"
