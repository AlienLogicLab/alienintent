"""Independent FDH-01 regressions; run explicitly with python3 -m pytest -q this_file."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/orchestration"))
from factory_director_host import DirectorInputs, FactoryDirectorHost, InMemoryDirectorLauncher


def make_host(tmp_path):
    launcher = InMemoryDirectorLauncher()
    values = DirectorInputs(True, True, True, False, False, False, False, False, False)
    return FactoryDirectorHost(tmp_path, lambda: values, launcher), launcher


def test_exit_before_wait_reconciles_without_interval_delay(tmp_path):
    host, launcher = make_host(tmp_path)
    try:
        episode = host.reconcile()
        launcher.finish(episode.episode_id)
        sleeps = []
        result = host.wait_for_change(60, sleep=sleeps.append)
        assert (result, sleeps) == ("EPISODE_EXITED", [])
    finally:
        host.shutdown()


def test_missing_required_key_with_extra_metadata_refuses_without_crash(tmp_path):
    host, launcher = make_host(tmp_path)
    try:
        host.reconcile()
        path = tmp_path / "lease.json"
        lease = json.loads(path.read_text())
        del lease["pid"]
        path.write_text(json.dumps(lease))
        result = host.reconcile()
        assert result.reason == "AMBIGUOUS_LEASE"
        assert len(launcher.launched) == 1
    finally:
        host.shutdown()
