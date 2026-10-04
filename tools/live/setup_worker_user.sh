#!/usr/bin/env bash
# WORKER-CREDENTIAL-BOUNDARY section 1: the one-time, root-run setup of the worker user (Founder-run).
#
# Prints every action and every final check first; applies them only after the Founder types "yes". With
# --dry-run it only prints and changes nothing (no root needed). It creates the system user alienintent-worker,
# one sudoers drop-in checked with visudo, the worker-owned launch folders (worker, results, handoff: mode 0711) and
# the Founder-owned ones (intake.git, intake-bundles, landing: mode 0700; exports: mode 0711), read and traverse
# only ACLs (r-X) on the packets clone, the intake repository and the --read install folders, traverse only (--x, no
# default ACL) on the launch folder, on launch/exports and on every folder from the Founder's HOME down to a needed
# path, removes any worker ACL from every control-plane path first, removes read for others from the Founder's
# credential files, and then checks, as the worker, that no control-plane repository is writable, owned or
# ACL-granted beyond read and traverse and that the App key is unreadable.
#
# It grants NOTHING on the work and readiness databases, the readiness evidence repository or the registry
# configuration (section 0.6b: workers get only their bounded context export). It removes any earlier grant there
# (setfacl -b, and -k on folders) and restores owner-only modes: 0700 on the evidence root and objects/, 0600 on the
# databases and the configuration, so LocalEvidenceRepository's UNSAFE_ROOT check passes; its final checks assert, as
# the worker, that none of them is readable or traversable.
#
# Usage (as root, through sudo, so SUDO_USER names the Founder):
#   sudo tools/live/setup_worker_user.sh --launch <.../launch> --packets <packets clone> --key <App key file> \
#        --configuration <registry project.json> --database <db>... --evidence <evidence root> \
#        [--read <install folder>]... [--founder <user>] [--dry-run]
#   --database: the work database and the readiness database (each kept private to the Founder).
#   --evidence: the readiness evidence repository root (kept private to the Founder).
#   --read: the named install folders of the interpreter and the provider CLI (read and traverse only).
set -euo pipefail

WORKER=alienintent-worker
DROPIN=/etc/sudoers.d/alienintent-worker
LAUNCH="" PACKETS="" KEY="" CONFIGURATION="" EVIDENCE="" FOUNDER=${SUDO_USER:-} DRY=0
READS=() DATABASES=()

usage() { sed -n '2,29p' "$0" | sed 's/^# \{0,1\}//'; }
while [ $# -gt 0 ]; do
  case "$1" in
    --launch) LAUNCH=$2; shift 2 ;;
    --packets) PACKETS=$2; shift 2 ;;
    --key) KEY=$2; shift 2 ;;
    --configuration) CONFIGURATION=$2; shift 2 ;;
    --read) READS+=("$2"); shift 2 ;;
    --database) DATABASES+=("$2"); shift 2 ;;
    --evidence) EVIDENCE=$2; shift 2 ;;
    --founder) FOUNDER=$2; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done
[ -n "$LAUNCH" ] && [ -n "$PACKETS" ] && [ -n "$KEY" ] && [ -n "$CONFIGURATION" ] && [ -n "$EVIDENCE" ] \
  && [ "${#DATABASES[@]}" -gt 0 ] || { usage >&2; exit 2; }
[ -n "$FOUNDER" ] && [ "$FOUNDER" != root ] || { echo "name the Founder (run through sudo, or --founder)" >&2; exit 2; }
FOUNDER_HOME=$(getent passwd "$FOUNDER" | cut -d: -f6 || true)
FOUNDER_HOME=${FOUNDER_HOME:-/home/$FOUNDER}
INTAKE="$LAUNCH/intake.git"

ACTIONS=() CHECKS=()
add() { ACTIONS+=("$(printf '%q ' "$@")"); }      # each action shell-quoted, run with eval
check() { CHECKS+=("$1"$'\t'"$2"); }               # description, then the shell test that must succeed

# 1. The user and the one sudo rule (it grants nothing to the worker, nothing as root or as the Founder).
SUDOERS="Defaults>$WORKER !use_pty, !log_output
$FOUNDER ALL=($WORKER) NOPASSWD: /usr/bin/env, /usr/bin/kill"
install_dropin() {
  local tmp; tmp=$(mktemp)
  printf '%s\n' "$SUDOERS" > "$tmp"
  visudo -c -f "$tmp" >/dev/null
  install -o root -g root -m 0440 "$tmp" "$DROPIN"
  rm -f "$tmp"
}
id "$WORKER" >/dev/null 2>&1 || add useradd --system --create-home --home-dir "/var/lib/$WORKER" --shell /usr/sbin/nologin "$WORKER"
add install_dropin

# 2. The launch folders: the worker's (0711, so the control plane can traverse to exact files) and the Founder's.
for name in worker results handoff; do add install -d -o "$WORKER" -g "$WORKER" -m 0711 "$LAUNCH/$name"; done
for name in intake.git intake-bundles landing; do add install -d -o "$FOUNDER" -m 0700 "$LAUNCH/$name"; done
add install -d -o "$FOUNDER" -m 0711 "$LAUNCH/exports"

# 3. First remove any worker ACL entry, access or default, from every control-plane-owned path.
for path in "$PACKETS" "$INTAKE" "$LAUNCH/intake-bundles" "$LAUNCH/landing"; do
  add setfacl -R -x "u:$WORKER" "$path"
  add find "$path" -type d -exec setfacl -x "d:u:$WORKER" '{}' +
done
for path in "$LAUNCH" "$LAUNCH/exports"; do
  add setfacl -x "u:$WORKER" "$path"
  add setfacl -x "d:u:$WORKER" "$path"
done

# 3b. The canonical stores stay private: every ACL entry removed (access, and default on folders), owner-only modes.
owner_only() {  # each path that exists (a SQLite -wal or -shm file may not): no ACL entry, mode 0600
  local path
  for path; do [ -e "$path" ] || continue; setfacl -b "$path"; chmod 0600 "$path"; done
}
for path in "${DATABASES[@]}" "$CONFIGURATION"; do
  add setfacl -b "$path"
  add chmod 0600 "$path"
done
for path in "${DATABASES[@]}"; do add owner_only "$path-wal" "$path-shm"; done
add setfacl -R -b "$EVIDENCE"
add find "$EVIDENCE" -type d -exec setfacl -k '{}' +
add chmod 0700 "$EVIDENCE" "$EVIDENCE/objects"

# 4. Read and traverse only (r-X, access and default) on the packets clone and the intake repository; traverse only
#    (--x, no default ACL) on the launch folder and on each folder from the Founder's HOME down to a needed path.
for path in "$PACKETS" "$INTAKE"; do
  add setfacl -R -m "u:$WORKER:r-X" "$path"
  add find "$path" -type d -exec setfacl -d -m "u:$WORKER:r-X" '{}' +
done
add setfacl -m "u:$WORKER:--x" "$LAUNCH"
add setfacl -m "u:$WORKER:--x" "$LAUNCH/exports"
declare -A TRAVERSED=()
traverse() {
  local dir
  dir=$(dirname "$1")
  while [ "$dir" != "/" ] && [ "${dir#"$FOUNDER_HOME"}" != "$dir" ]; do
    if [ -z "${TRAVERSED[$dir]:-}" ] && [ "$dir" != "$LAUNCH" ]; then
      TRAVERSED[$dir]=1
      add setfacl -m "u:$WORKER:--x" "$dir"
    fi
    dir=$(dirname "$dir")
  done
}
for path in "$LAUNCH" "$PACKETS" "${READS[@]}"; do traverse "$path"; done
for path in "${READS[@]}"; do add setfacl -R -m "u:$WORKER:r-X" "$path"; done

# 5. No read for others on the Founder's credential files, and no worker ACL entry on them.
for path in "$FOUNDER_HOME/.git-credentials" "$FOUNDER_HOME/.netrc" "$FOUNDER_HOME/.gitconfig" \
            "$FOUNDER_HOME/.config/gh" "$FOUNDER_HOME/.ssh" "$(dirname "$KEY")"; do
  add chmod -R o-rwx "$path"
  add setfacl -R -x "u:$WORKER" "$path"
done

# 6. The final checks, as the worker (runuser) where they are about the worker's access.
as_worker() { runuser -u "$WORKER" -- "$@"; }
no_worker_access() {  # $1: a control-plane path; recursive, and every parent folder up to /
  local path=$1 dir
  [ -z "$(find "$path" -user "$WORKER" -print -quit 2>/dev/null)" ] || return 1
  [ -z "$(as_worker find "$path" -writable -print -quit 2>/dev/null)" ] || return 1
  ! getfacl -R -p "$path" 2>/dev/null | grep -Eq "^(default:)?user:$WORKER:.*w" || return 1
  dir=$(dirname "$path")
  while :; do
    [ "$(stat -c %U "$dir")" != "$WORKER" ] && ! as_worker test -w "$dir" || return 1
    ! getfacl -p "$dir" 2>/dev/null | grep -Eq "^(default:)?user:$WORKER:.*w" || return 1
    [ "$dir" = "/" ] && break
    dir=$(dirname "$dir")
  done
}
for path in "$PACKETS" "$INTAKE" "$LAUNCH/intake-bundles" "$LAUNCH/landing"; do
  check "check: not writable, not owned, no ACL beyond read and traverse: $path" "no_worker_access $(printf '%q' "$path")"
done
check "check: App key unreadable: $KEY" "! as_worker head -c1 $(printf '%q' "$KEY") >/dev/null 2>&1"
unreachable() {  # $1: a canonical store path the worker can neither read nor traverse
  ! as_worker head -c1 -- "$1" >/dev/null 2>&1 && ! as_worker ls -a -- "$1" >/dev/null 2>&1 \
    && ! as_worker test -x "$1" -a -d "$1"
}
private_evidence() {  # LocalEvidenceRepository's own UNSAFE_ROOT rule: no symlink, no group or other mode bits
  local path
  for path in "$EVIDENCE" "$EVIDENCE/objects"; do
    [ ! -L "$path" ] && [ -d "$path" ] && [ $(( 0$(stat -c %a "$path") & 077 )) -eq 0 ] || return 1
  done
}
SIDECARS=()
for path in "${DATABASES[@]}"; do SIDECARS+=("$path-wal" "$path-shm"); done
for path in "$CONFIGURATION" "${DATABASES[@]}" "${SIDECARS[@]}" "$EVIDENCE" "$EVIDENCE/objects"; do
  check "check: neither readable nor traversable by the worker: $path" "unreachable $(printf '%q' "$path")"
done
check "check: the evidence repository's privacy check passes (UNSAFE_ROOT): $EVIDENCE" "private_evidence"
check "check: no credential in the packets clone config: $PACKETS/.git/config" \
  "! git config -f $(printf '%q' "$PACKETS/.git/config") --get-regexp '^(credential\\..*|http\\..*\\.extraheader|url\\..*\\.insteadof|url\\..*\\.pushinsteadof)\$' >/dev/null && ! grep -Eq '://[^/@[:space:]]+@' $(printf '%q' "$PACKETS/.git/config")"
check "check: the worker has no sudo rule: sudo -n -l" "! as_worker sudo -n -l >/dev/null 2>&1"

echo "Plan for $WORKER (Founder $FOUNDER, HOME $FOUNDER_HOME):"
echo "sudoers drop-in $DROPIN (mode 0440, checked with visudo -c):"
printf '    %s\n' "$SUDOERS"
for action in "${ACTIONS[@]}"; do echo "${action% }"; done
for entry in "${CHECKS[@]}"; do echo "${entry%%$'\t'*}"; done
[ "$DRY" -eq 1 ] && { echo "dry run: nothing changed"; exit 0; }

[ "$(id -u)" -eq 0 ] || { echo "apply as root (through sudo)" >&2; exit 2; }
for tool in setfacl getfacl visudo runuser; do
  command -v "$tool" >/dev/null || { echo "missing $tool (install the acl and sudo packages)" >&2; exit 2; }
done
read -r -p "Type yes to apply exactly these actions: " answer
[ "$answer" = yes ] || { echo "not applied"; exit 1; }
for action in "${ACTIONS[@]}"; do
  echo "+ ${action% }"
  case "$action" in
    "setfacl -R -x "*|"setfacl -x "*|"find "*|"setfacl -b "*) eval "$action" 2>/dev/null || echo "  (no entry to remove)" ;;
    "chmod -R o-rwx "*|"setfacl -R -x u:$WORKER $FOUNDER_HOME"*) eval "$action" 2>/dev/null || echo "  (absent)" ;;
    *) eval "$action" ;;
  esac
done
failed=0
for entry in "${CHECKS[@]}"; do
  if eval "${entry#*$'\t'}"; then echo "PASS ${entry%%$'\t'*}"; else echo "FAIL ${entry%%$'\t'*}"; failed=1; fi
done
exit "$failed"
