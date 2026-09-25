from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

SCRIPT = Path(__file__).with_name("run_feature_regressions.py")
spec = spec_from_file_location("feature_regressions", SCRIPT)
module = module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def manifest():
    import json
    return json.loads(Path(__file__).with_name("feature_regressions.json").read_text())


def test_priority_feature_pack_is_selected_by_every_owned_boundary():
    owned = (
        "tools/live/project_materialization.py",
        "tools/live/release_admission.py",
        "src/alienintent/execution_coordination/adapters/github_work_management.py",
        "src/alienintent/execution_coordination/application/factory_coordinator.py",
        "src/alienintent/context_assembly/application/readiness_service.py",
    )
    for path in owned:
        assert [p["id"] for p in module.selected_packs(manifest(), (path,))] == [
            "requirement-priority-continuity"
        ]


def test_unrelated_change_does_not_select_priority_pack():
    assert module.selected_packs(manifest(), ("docs/README-unrelated.md",)) == []
