"""Executable acceptance tests for PY-01 architecture fitness."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "tools" / "fitness" / "check_architecture.py"
FIXTURES = ROOT / "tests" / "fixtures" / "fitness"


def run_check(root: Path, check: str = "all") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root), "--check", check],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class ArchitectureFitnessTests(unittest.TestCase):
    def test_skeleton_satisfies_all_fitness_checks(self) -> None:
        """Removing a boundary check must make a future violating fixture pass."""
        result = run_check(ROOT / "src" / "alienintent")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS: all architecture fitness checks", result.stdout)

    def test_each_deliberate_violation_fails_its_named_check(self) -> None:
        """Removing a named check must let its real AST violation escape detection."""
        cases = {
            "layering": "domain imports adapters",
            "vendor-signature": "third-party type in domain signature",
            "port-contract": "adapter class has no declared port contract",
            "configuration": "configuration read outside composition",
        }
        for check, expected in cases.items():
            with self.subTest(check=check):
                result = run_check(FIXTURES / check, check)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stdout)

    def test_standard_library_signature_is_not_a_vendor_violation(self) -> None:
        """Treating a standard-library type as a vendor type breaks valid domain values."""
        result = run_check(FIXTURES / "stdlib-signature", "vendor-signature")
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
