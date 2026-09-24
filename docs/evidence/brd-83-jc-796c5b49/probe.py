"""Independent BRD-83 AC3 probe. Exit 1 means invalid citations were admitted.

Run from the repository: python3 docs/evidence/brd-83-jc-796c5b49/probe.py
Uses only temporary repositories and the candidate's fake gh fixture.
"""
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/live"))
from test_release_admission_release_point import World
from release_admission import assessment_record_path

paths = [
    "docs/evidence/elsewhere/WO-220202.s.assessment.json",
    "docs/evidence/wave2-readiness-assessments/../../../WO-220202.s.assessment.json",
    "docs/evidence/wave2-readiness-assessments/ARP/WO-220202.s.assessment.json",
]
results = []
with tempfile.TemporaryDirectory(prefix="brd83-jc-path-") as tmp:
    world = World(Path(tmp))
    world.land("docs/work-units/python/WO-220202.assessment.json")
    for path in paths:
        world.issue(body=f"Readiness record `{path}`.")
        result = world.admit(workdir=world.work)
        results.append({"path": path, "resolved_path": str(assessment_record_path(path)),
                        "expected_exit": 1, "observed_exit": result.returncode,
                        "stdout": result.stdout, "stderr": result.stderr})
print(json.dumps(results, indent=2))
sys.exit(0 if all(r["observed_exit"] == r["expected_exit"] for r in results) else 1)
