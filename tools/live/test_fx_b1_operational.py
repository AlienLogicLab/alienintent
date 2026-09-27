"""FX-B1 operational driver checks (LOCAL): the read audit and the bound-root guard.

The operational run itself is `tools/live/fx_b1_operational.py run`; these checks prove its two
negative controls discriminate, using a temporary protected directory and a decoy file, never
real factory or observer state.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fx_b1_operational as fx  # noqa: E402

AUDIT = Path(__file__).resolve().parent / "fx_b1_audit.py"


def audited(tmp_path, *arguments):
    log = tmp_path / "audit.log"
    result = subprocess.run([sys.executable, "-B", str(AUDIT), str(log), "-m", *arguments], capture_output=True,
                            text=True, timeout=60)
    return result, [json.loads(line) for line in log.read_text().splitlines()]


def test_the_audit_names_a_protected_read_outside_the_allowed_root(tmp_path):  # B1-09
    protected, allowed = tmp_path / "state", tmp_path / "state" / "fx-b1" / "trajectory"
    allowed.mkdir(parents=True)
    decoy = protected / "coordinator-observations.jsonl"
    decoy.write_text('{"decoy": true}\n')
    inside = allowed / "inside.json"
    inside.write_text('{"inside": true}\n')

    result, touched = audited(tmp_path, "json.tool", str(inside))
    assert result.returncode == 0 and str(inside) in touched
    assert fx.forbidden_touches(touched, protected, (allowed,)) == []

    result, touched = audited(tmp_path, "json.tool", str(decoy))
    assert result.returncode == 0 and str(decoy) in touched
    assert fx.forbidden_touches(touched, protected, (allowed,)) == [str(decoy)]


def test_the_audit_records_sqlite_opens_and_survives_a_failing_module(tmp_path):  # B1-09
    database = tmp_path / "state" / "other.sqlite"
    database.parent.mkdir()
    (tmp_path / "fx_b1_probe.py").write_text(
        f"import sqlite3\nsqlite3.connect({str(database)!r}).close()\nraise SystemExit(5)\n")
    log = tmp_path / "audit.log"
    result = subprocess.run([sys.executable, "-B", str(AUDIT), str(log), "-m", "fx_b1_probe"], cwd=tmp_path,
                            env={**os.environ, "PYTHONPATH": str(tmp_path)}, capture_output=True, text=True,
                            timeout=60)
    touched = [json.loads(line) for line in log.read_text().splitlines()]
    assert result.returncode == 5
    assert fx.forbidden_touches(touched, tmp_path / "state", ()) == [str(database)]


def test_the_root_guard_refuses_before_anything_is_written(tmp_path):  # B1-10
    bound = tmp_path / "fx-b1"
    assert fx.guard_root(bound / "trajectory", bound) == []
    assert not (bound / "trajectory").exists()
    assert fx.guard_root(tmp_path / "elsewhere", bound) == ["ROOT_OUTSIDE_BOUND_TARGET"]
    assert fx.guard_root(bound, bound) == ["ROOT_OUTSIDE_BOUND_TARGET"]
    assert fx.guard_root(bound / ".." / "worktrees", bound) == ["ROOT_OUTSIDE_BOUND_TARGET"]
    used = bound / "used"
    used.mkdir(parents=True)
    (used / "state.json").write_text("{}")
    assert fx.guard_root(used, bound) == ["ROOT_NOT_EMPTY", "ROOT_CONTAINS_FACTORY_STATE"]
    assert (used / "state.json").read_text() == "{}"


def test_the_default_target_is_the_bound_profile_root():
    assert fx.DEFAULT_ROOT == Path.home() / ".local/state/alienintent/fx-b1/trajectory"
    assert fx.PROFILE == "fx-b1-trajectory-operational"
    assert fx.STATE == Path.home() / ".local/state/alienintent"
    assert fx.inside(fx.DEFAULT_ROOT, fx.STATE) and not fx.inside(fx.STATE / "state.json", fx.DEFAULT_ROOT)


def test_the_audit_names_a_protected_path_reached_through_a_child_process_or_symlink(tmp_path):  # B1-09
    protected, allowed = tmp_path / "state", tmp_path / "state" / "fx-b1" / "trajectory"
    allowed.mkdir(parents=True)
    decoy = protected / "state.json"
    decoy.write_text("{}\n")
    link = allowed / "looks-inside.json"
    link.symlink_to(decoy)
    (tmp_path / "fx_b1_child.py").write_text(
        f"import subprocess\nsubprocess.run(['cat', {str(decoy)!r}], capture_output=True)\n")
    log = tmp_path / "audit.log"
    subprocess.run([sys.executable, "-B", str(AUDIT), str(log), "-m", "fx_b1_child"], cwd=tmp_path,
                   env={**os.environ, "PYTHONPATH": str(tmp_path)}, capture_output=True, timeout=60, check=True)
    child = fx.read_audit(log)
    assert fx.forbidden_touches(child["paths"], protected, (allowed,)) == [str(decoy)]
    assert [e[0] for e in child["executions"]] == ["cat"]

    result, _ = audited(tmp_path, "json.tool", str(link))
    assert result.returncode == 0
    linked = fx.read_audit(tmp_path / "audit.log")
    assert str(decoy) in fx.forbidden_touches(linked["paths"], protected, (allowed,))
