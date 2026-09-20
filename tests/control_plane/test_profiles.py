from pathlib import Path


def test_offline_profile_exposes_only_control_plane_dependencies(tmp_path: Path) -> None:
    from alienintent.composition.offline_profile import OfflineProfile

    class Work:
        def import_ready_snapshot(self): return ()
    class Worker:
        def cancel(self, *_args): return "quiesced"
    profile = OfflineProfile(tmp_path / "state.db", Work(), Worker(), tmp_path / "artifacts")

    assert profile.name == "offline"
    assert profile.store.read_state("offline", "missing") == (0, {})
    assert profile.readiness() is False
