#!/usr/bin/env bash
# RECORD-COMPLETED-WORK acceptance check 5 (Founder-run, before acceptance): record unit 6c-1 (work item
# 5befff2f-a0dd-4cea-9556-54c33ed86c1b) from its actual evidence on a COPY of the work registry, running this
# candidate's code (PYTHONPATH=<this worktree>/src).
#
#   tools/live/record_completed_work_6c1.sh "<the Founder's words for this recording>"
#
# The permanent work.sqlite and readiness.sqlite are only read (`sqlite3 -readonly ... .backup`), readiness-evidence/
# only copied; the repository clone is used in place and only read. The projects.json copy points `database`,
# `readiness.database`, `readiness.evidence_root` (and the profile databases) at the copies and drops the `github`
# entry, which this command does not use. Output: $OUT/output.txt, next to the copies in $OUT/copy/.
# REGISTRY and OUT may be overridden (for a dry run on another copy); by default REGISTRY is the permanent registry.
set -euo pipefail
QUOTE=${1:-}
if [ -z "${QUOTE//[[:space:]]/}" ]; then
  echo "usage: $0 \"<the Founder's words for this recording>\"" >&2
  exit 2
fi
CANDIDATE=$(cd "$(dirname "$0")/../.." && pwd)
REGISTRY=${REGISTRY:-/home/netmarine/.local/state/alienintent/registry}
OUT=${OUT:-/home/netmarine/.local/state/alienintent/manual/record-completed-work-real-use/run-$(date -u +%Y%m%dT%H%M%SZ)}
case "$OUT/" in "$REGISTRY"/*) echo "OUT must not be inside $REGISTRY" >&2; exit 2;; esac

ID=5befff2f-a0dd-4cea-9556-54c33ed86c1b
CANDIDATE_SHA=c36688492487c41aa41aebd4778d54aec7ceeece
LANDING=a5087d71439792a7e1efd96711cdfa85803049ac
RECORD=docs/evidence/work-context-package-landing-c366884.md
VERDICTS=/home/netmarine/.local/state/alienintent/manual/work-context-verification
APPROVAL=$REGISTRY/approvals/$ID.json

mkdir -p "$OUT/copy"
chmod 700 "$OUT" "$OUT/copy"
exec > >(tee "$OUT/output.txt") 2>&1
COPY=$OUT/copy
echo "== RECORD-COMPLETED-WORK check 5: candidate $(git -C "$CANDIDATE" rev-parse HEAD), output $OUT/output.txt"
echo "== permanent registry files before (sha256; must be unchanged at the end)"
PERMANENT="$REGISTRY/work.sqlite $REGISTRY/readiness.sqlite"
sha256sum $PERMANENT | tee "$OUT/permanent.before"
(cd "$REGISTRY/readiness-evidence" && find . -type f | LC_ALL=C sort | xargs -r sha256sum) | sha256sum \
  | tee -a "$OUT/permanent.before"

echo "== copy: work.sqlite, readiness.sqlite (sqlite3 -readonly .backup), readiness-evidence/, profile databases"
sqlite3 -readonly "$REGISTRY/work.sqlite" ".backup '$COPY/work.sqlite'"
sqlite3 -readonly "$REGISTRY/readiness.sqlite" ".backup '$COPY/readiness.sqlite'"
cp -a "$REGISTRY/readiness-evidence" "$COPY/readiness-evidence"
python3 - "$REGISTRY/projects.json" "$COPY" <<'PY'
import json, sqlite3, sys
from pathlib import Path
source, copy = Path(sys.argv[1]), Path(sys.argv[2])
document = json.loads(source.read_text())
entry = document["projects"]["AlienLogicLab/alienintent"]
entry["database"] = str(copy / "work.sqlite")
entry["readiness"]["database"] = str(copy / "readiness.sqlite")
entry["readiness"]["evidence_root"] = str(copy / "readiness-evidence")
for name, path in entry["profiles"].items():  # read-only backups, so nothing opens a permanent profile database
    target = copy / f"profile-{name}.sqlite"
    with sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True) as live, sqlite3.connect(target) as out:
        live.backup(out)
    entry["profiles"][name] = str(target)
entry.pop("github", None)
(copy / "projects.json").write_text(json.dumps(document, indent=1))
(copy / "projects.json").chmod(0o600)
PY

export PYTHONPATH=$CANDIDATE/src
export ALIENINTENT_PROJECT_CONFIGURATION=$COPY/projects.json
export ALIENINTENT_PROJECT=AlienLogicLab/alienintent
cli() { python3 -m alienintent --profile-factory alienintent.composition.work_registry:work_registry_profile --json "$@"; }
show() {
  cli work show "$ID" | python3 -c "import json,sys; d=json.load(sys.stdin)['item']; print(json.dumps({k: d[k] for k in
    ('id','label','state','pointer','approval_ref','verification_ref')}, indent=1))"
}
written() {  # everything the command could write in the copy: both databases and the evidence objects
  { sqlite3 "$COPY/work.sqlite" .dump; sqlite3 "$COPY/readiness.sqlite" .dump; ls "$COPY/readiness-evidence/objects"; } \
    | sha256sum
}
record() {
  cli work record-completed "$ID" --candidate "$CANDIDATE_SHA" --landing "$LANDING" --record "$RECORD" \
    --verification "$VERDICTS/round1-4580d5b/verdict.md" --verification "$VERDICTS/round2-c366884/verdict.md" \
    --approval "$APPROVAL" --quote "$QUOTE"
}

echo "== work show, before"
show
echo "== work record-completed"
record | tee "$OUT/record.json"
echo
echo "== the evidence reference"
python3 -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1]))['evidence_ref'], indent=1))" "$OUT/record.json"
echo "== work show, after (same id, state DONE, verification_ref = the evidence reference)"
show
echo "== the repeat (must answer repeated: true and write nothing)"
before=$(written)
record | tee "$OUT/repeat.json"
echo
after=$(written)
echo "copy before repeat: $before"
echo "copy after repeat:  $after"
[ "$before" = "$after" ] && echo "repeat wrote nothing: yes" || echo "repeat wrote nothing: NO"
echo "== summary"
cli work show "$ID" | python3 -c "
import json, sys
item = json.load(sys.stdin)['item']
first, repeat = (json.load(open(sys.argv[i])) for i in (1, 2))
print('recorded (answer null):', 'yes' if first['answer'] is None and not first['repeated'] else 'NO')
print('same id, state DONE:', 'yes' if (item['id'], item['state']) == (sys.argv[3], 'DONE') else 'NO')
print('verification_ref is the evidence reference:', 'yes' if item['verification_ref'] == first['evidence_ref'] else 'NO')
print('repeat answered repeated:', 'yes' if repeat['answer'] is None and repeat['repeated'] else 'NO')
" "$OUT/record.json" "$OUT/repeat.json" "$ID"
echo "== permanent registry files after"
sha256sum $PERMANENT > "$OUT/permanent.after"
(cd "$REGISTRY/readiness-evidence" && find . -type f | LC_ALL=C sort | xargs -r sha256sum) | sha256sum \
  >> "$OUT/permanent.after"
cat "$OUT/permanent.after"
cmp -s "$OUT/permanent.before" "$OUT/permanent.after" && echo "permanent registry unchanged: yes" \
  || echo "permanent registry unchanged: NO"
