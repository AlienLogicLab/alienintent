#!/bin/bash
# FX-E1 deterministic worker. The control plane launches this through the shipped
# CliWorkerProvider exactly as it launches the sandbox's own worker/run.sh; the
# only substitution is the author of the work: this script writes the note (as
# PRODUCER) and judges it (as VERIFIER) instead of a provider CLI. FX-E1 proves
# transport, not provider behaviour, and a provider CLI would add model spend and
# its own helper processes to the no-Node observation. The substitution is
# labelled in the FX-E1 record and claims nothing about providers.
set -euo pipefail

invocation="${ALIENINTENT_INVOCATION_ID:?the worker was not told which invocation it is}"
role="${ALIENINTENT_ROLE:-PRODUCER}"
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

if [ "$role" = "VERIFIER" ]; then
  # Judge the exact retrieved candidate against its contract's completion
  # criterion and leave the verdict the shipped RealWorkerProvider reads
  # (.alienintent/verdict.json, bound to this revision). The feature-regression
  # receipt beside it is written by CliWorkerProvider itself, from the sandbox's
  # own tools/verification runner, before this process starts; it is not touched.
  exec python3 - "$biu" "$note" <<'PY'
import json, subprocess, sys
from pathlib import Path

biu, note = sys.argv[1], Path(sys.argv[2])
def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout.strip()
revision = git("rev-parse", "HEAD")
base = git("merge-base", "HEAD", "origin/main")
changed = [p for p in git("diff", "--name-only", f"{base}...{revision}").splitlines() if p]
text = note.read_text(encoding="utf-8") if note.is_file() else ""
findings = []
if not text.startswith(f"# {biu}\n"):
    findings.append(f"{note} does not open with the heading '# {biu}'")
if len([line for line in text.splitlines() if line.startswith("- ")]) != 1:
    findings.append(f"{note} does not carry exactly one bullet line")
if changed != [str(note)]:
    findings.append(f"the candidate changes {changed}, not exactly {note}")
out = Path(".alienintent"); out.mkdir(exist_ok=True)
verdict = {"revision": revision, "verdict": "reject" if findings else "accept", "findings": findings}
(out / "verdict.json").write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
print(f"{verdict['verdict']} {revision}")
PY
fi

hold="$(field hold_seconds)"

# A held worker keeps the effect unresolved long enough for FX-E1 to take the
# process loss while work is in flight.
if [ -n "$hold" ] && [ "$hold" != "0" ]; then sleep "$hold"; fi

mkdir -p "$(dirname "$note")"
printf '# %s\n\n- The AlienIntent Python factory executed %s under invocation %s (FX-E1 deterministic worker).\n' \
  "$biu" "$biu" "$invocation" > "$note"
git add -A
git commit -qm "${biu}: factory candidate for ${invocation}"
