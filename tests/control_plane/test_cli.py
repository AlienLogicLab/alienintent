import os
from pathlib import Path
import subprocess
import sys


def test_cli_version_and_sanitized_json_failure_are_subprocess_proof(tmp_path: Path) -> None:
    ok = subprocess.run([sys.executable, "-m", "alienintent", "version", "--json"], text=True, capture_output=True, env=os.environ | {"PYTHONPATH": "src"})
    assert ok.returncode == 0
    assert '"version"' in ok.stdout
    broken = subprocess.run([sys.executable, "-m", "alienintent", "status", "--profile-factory", "missing:factory", "--json"], text=True, capture_output=True, env=os.environ | {"PYTHONPATH": "src"})
    assert broken.returncode != 0
    assert '"error"' in broken.stdout
    assert "Traceback" not in broken.stderr
