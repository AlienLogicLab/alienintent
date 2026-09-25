"""Executable acceptance tests for PY-01 architecture fitness."""

from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "tools" / "fitness" / "check_architecture.py"
FIXTURES = ROOT / "tests" / "fixtures" / "fitness"


def run_check(root: Path, check: str = "all", register: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root), "--check", check,
         *(("--register", str(register)) if register else ())],
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
            "determinism": "direct nondeterministic facility import",
            "private-product": "Agent Ready private import",
        }
        for check, expected in cases.items():
            with self.subTest(check=check):
                result = run_check(FIXTURES / check, check)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stdout)

    def test_layering_rejects_relative_and_absolute_adapter_imports(self) -> None:
        """Domain and application code cannot import adapters through alternate syntax."""
        cases = {
            "relative-import": "domain imports adapters",
            "absolute-import": "application imports adapters",
        }
        for fixture, expected in cases.items():
            with self.subTest(fixture=fixture):
                result = run_check(FIXTURES / "layering" / fixture, "layering")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stdout)

    def test_vendor_signature_rejects_quoted_annotations_and_vendor_bases(self) -> None:
        """Vendor types leak through forward references and inheritance as well as names."""
        for fixture in (
            "quoted-annotation",
            "nested-quoted-annotation",
            "vendor-base-domain",
            "vendor-base-port",
        ):
            with self.subTest(fixture=fixture):
                result = run_check(FIXTURES / "vendor-signature" / fixture, "vendor-signature")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("third-party type in", result.stdout)

    def test_adapter_contract_check_uses_a_path_relative_to_the_checked_root(self) -> None:
        """An ancestor named domain cannot disguise an adapter as a domain file."""
        root = FIXTURES / "path-classification" / "domain" / "alienintent"
        result = run_check(root, "port-contract")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("adapter class has no declared port contract", result.stdout)

    def test_private_product_import_fails_in_every_layer(self) -> None:
        """Agent Ready is bound through its CLI/MCP contract; importing its implementation fails in any layer."""
        for fixture in ("adapter-import", "aliased-submodule-import"):
            with self.subTest(fixture=fixture):
                result = run_check(FIXTURES / "private-product" / fixture, "private-product")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Agent Ready private import", result.stdout)

    def test_standard_library_signature_is_not_a_vendor_violation(self) -> None:
        """Treating a standard-library type as a vendor type breaks valid domain values."""
        result = run_check(FIXTURES / "stdlib-signature", "vendor-signature")
        self.assertEqual(result.returncode, 0, result.stdout)


class CouplingFitnessTests(unittest.TestCase):
    """FX-U6 scoped coupling checks (2026-09-25 Founder disposition); the withdrawn R1 table is never consulted."""

    def fixture(self, check: str, register: str) -> subprocess.CompletedProcess[str]:
        return run_check(FIXTURES / check / "alienintent", check, FIXTURES / check / f"{register}.json")

    def test_introduced_cross_module_cycle_fails(self):
        """Removing the cycle check lets the fixture's alpha/beta back edge pass silently."""
        result = self.fixture("module-cycle", "undeclared")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("undeclared cross-module cycle edge beta -> alpha in cycle alpha, beta", result.stdout)

    def test_cycle_declared_edge_for_edge_is_explicit_not_a_defect(self):
        result = self.fixture("module-cycle", "declared")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_unclassified_domain_import_fails(self):
        """A raw cross-module domain import is never silently treated as policy."""
        result = self.fixture("domain-import", "unclassified")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unclassified cross-module domain import alienintent.beta.domain.model", result.stdout)
        self.assertEqual(self.fixture("domain-import", "classified").returncode, 0)

    def test_classification_of_an_absent_import_is_stale(self):
        """A register entry that matches no import would otherwise grow into an allow-list."""
        result = self.fixture("domain-import", "stale")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("classified domain import not observed: alpha -> alienintent.beta.domain.retired", result.stdout)

    def test_table_mutated_outside_its_owner_fails(self):
        result = self.fixture("persistence-ownership", "register")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("table ledger owned by alpha/adapters/store.py is mutated outside its owner", result.stdout)
        self.assertNotIn("alpha/adapters/store.py:", result.stdout)

    def test_missing_register_fails_closed(self):
        for check in ("module-cycle", "domain-import", "persistence-ownership"):
            with self.subTest(check=check):
                result = run_check(ROOT / "src" / "alienintent", check, FIXTURES / "absent-register.json")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("coupling register unavailable", result.stdout)

    def test_inventory_is_the_observed_graph_plus_the_register(self):
        completed = subprocess.run([sys.executable, str(CHECKER), "--root", str(ROOT / "src" / "alienintent"),
                                    "--inventory"], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stdout)
        inventory = json.loads(completed.stdout)
        register = json.loads((ROOT / "tools" / "fitness" / "coupling_register.json").read_text())
        self.assertIn(["execution_coordination", "installation"], inventory["edges"])
        self.assertEqual(inventory["cycles"], [sorted(c["edges"]) for c in register["cycles"]])
        self.assertNotIn("withdrawn_r1_proposal", completed.stdout)
        self.assertNotIn("allowed_edges", json.dumps(register))


if __name__ == "__main__":
    unittest.main()
