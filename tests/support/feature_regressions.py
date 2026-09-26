"""Seed a disposable fixture repository with the real VERIFY feature-regression runner.

Since the accumulated VERIFY gate (4a9a3b6), ``CliWorkerProvider`` runs
``tools/verification/run_feature_regressions.py`` inside a verifier's fresh
workspace before the verifier process, and a verdict without the receipt that
runner writes reads back as ``feature-regressions-missing``. A disposable
fixture repository therefore carries the repository's own runner and manifest,
byte for byte, so the gate runs for real there; nothing is stubbed or weakened.
"""

from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
VERIFICATION = ("tools/verification/run_feature_regressions.py", "tools/verification/feature_regressions.json")


def seed_verification_runner(checkout: Path) -> None:
    for relative in VERIFICATION:
        target = Path(checkout) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
