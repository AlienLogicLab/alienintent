#!/bin/bash
# FX-E1 deterministic worker. The control plane launches this through the shipped
# CliWorkerProvider exactly as it launches the sandbox's own worker/run.sh; the
# only substitution is the author of the note: this script writes it instead of a
# provider CLI. FX-E1 proves transport, not provider behaviour, and a provider CLI
# would add model spend and its own helper processes to the no-Node observation.
# The substitution is labelled in the FX-E1 record and claims nothing about providers.
set -euo pipefail

invocation="${ALIENINTENT_INVOCATION_ID:?the worker was not told which invocation it is}"
biu="${invocation#launch:}"
biu="${biu%:*}"
contract="biu/${biu}.json"
test -f "$contract" || { echo "no contract document for ${biu}" >&2; exit 4; }

# The control plane's publication credential must never reach a worker.
if [ -n "${GIT_CONFIG_COUNT:-}" ]; then
  echo "worker inherited a publication credential" >&2
  exit 5
fi

field() { python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["task"].get(sys.argv[2], ""))' "$contract" "$1"; }
note="$(field note)"
hold="$(field hold_seconds)"

# A held worker keeps the effect unresolved long enough for FX-E1 to take the
# process loss while work is in flight.
if [ -n "$hold" ] && [ "$hold" != "0" ]; then sleep "$hold"; fi

mkdir -p "$(dirname "$note")"
printf '# %s\n\n- The AlienIntent Python factory executed %s under invocation %s (FX-E1 deterministic worker).\n' \
  "$biu" "$biu" "$invocation" > "$note"
git add -A
git commit -qm "${biu}: factory candidate for ${invocation}"
