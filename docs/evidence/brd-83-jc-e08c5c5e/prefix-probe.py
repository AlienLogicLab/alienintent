"""Offline AC3 probe: exit 1 when a wrong-directory citation admits."""
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path.cwd() / "tools/live"))
from test_release_admission_release_point import World
from release_admission import assessment_record_path
rows = []
with tempfile.TemporaryDirectory() as tmp:
    world = World(Path(tmp))
    world.land("docs/work-units/python/PY-05.assessment.json")
    for path in (
        "docs/evidence/elsewhere/docs/work-units/python/PY-05.assessment.json",
        "docs/evidence/wave2-readiness-assessments/ARP/docs/work-units/python/PY-05.assessment.json",
    ):
        world.issue(body=f"Readiness record `{path}`.")
        result = world.admit(workdir=world.work)
        rows.append(dict(citation=path, resolved=str(assessment_record_path(path)),
                         expected_exit=1, actual_exit=result.returncode,
                         stdout=result.stdout))
print(json.dumps(rows, indent=2))
sys.exit(0 if all(r["actual_exit"] == r["expected_exit"] for r in rows) else 1)
