"""Mechanically enforce the PY-01 Python architecture boundaries."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from sys import stdlib_module_names
from typing import Callable, Iterable


CHECKS = ("layering", "vendor-signature", "port-contract", "configuration", "determinism")
INNER_LAYERS = {"domain", "application"}
SIGNATURE_LAYERS = {"domain", "ports"}
STDLIB_MODULES = set(stdlib_module_names)


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    message: str

    def render(self, root: Path) -> str:
        return f"{self.path.relative_to(root)}:{self.line}: {self.message}"


def python_files(root: Path) -> Iterable[Path]:
    return sorted(root.rglob("*.py"))


def layer_for(path: Path, root: Path) -> str | None:
    for part in path.relative_to(root).parts:
        if part in {"domain", "application", "ports", "adapters", "composition"}:
            return part
    return None


def dotted_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else None
    return None


def annotations(node: ast.AST) -> Iterable[ast.expr]:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
            if argument.annotation:
                yield argument.annotation
        if node.args.vararg and node.args.vararg.annotation:
            yield node.args.vararg.annotation
        if node.args.kwarg and node.args.kwarg.annotation:
            yield node.args.kwarg.annotation
        if node.returns:
            yield node.returns
    if isinstance(node, ast.AnnAssign):
        yield node.annotation


def expression_names(expression: ast.expr) -> set[str]:
    names = {item.id for item in ast.walk(expression) if isinstance(item, ast.Name)}
    for item in ast.walk(expression):
        if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
            continue
        try:
            parsed = ast.parse(item.value, mode="eval").body
        except SyntaxError:
            continue
        names.update(candidate.id for candidate in ast.walk(parsed) if isinstance(candidate, ast.Name))
    return names


def check_layering(path: Path, tree: ast.Module, root: Path) -> list[Violation]:
    layer = layer_for(path, root)
    if layer not in INNER_LAYERS:
        return []
    violations = []
    for node in ast.walk(tree):
        module = None
        if isinstance(node, ast.Import):
            module = ",".join(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = ".".join(filter(None, (node.module, *(alias.name for alias in node.names))))
        if module and "adapters" in module.split("."):
            violations.append(Violation(path, node.lineno, f"{layer} imports adapters"))
    return violations


def check_vendor_signature(path: Path, tree: ast.Module, root: Path) -> list[Violation]:
    layer = layer_for(path, root)
    if layer not in SIGNATURE_LAYERS:
        return []
    imported_vendor_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in STDLIB_MODULES:
                    imported_vendor_names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if node.module.split(".")[0] not in STDLIB_MODULES and not node.module.startswith("alienintent"):
                imported_vendor_names.update(alias.asname or alias.name for alias in node.names)
    violations = []
    for node in ast.walk(tree):
        for annotation in annotations(node):
            names = expression_names(annotation)
            if names & imported_vendor_names:
                violations.append(Violation(path, annotation.lineno, f"third-party type in {layer} signature"))
        if isinstance(node, ast.ClassDef):
            names = set().union(*(expression_names(base) for base in node.bases))
            if names & imported_vendor_names:
                violations.append(Violation(path, node.lineno, f"third-party type in {layer} signature"))
    return violations


def check_port_contract(path: Path, tree: ast.Module, root: Path) -> list[Violation]:
    if layer_for(path, root) != "adapters":
        return []
    imported_port_names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module and "ports" in node.module.split("."):
            imported_port_names.update(alias.asname or alias.name for alias in node.names)
    violations = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = {dotted_name(base) for base in node.bases}
            if not bases & imported_port_names:
                violations.append(Violation(path, node.lineno, "adapter class has no declared port contract"))
    return violations


def check_configuration(path: Path, tree: ast.Module, root: Path) -> list[Violation]:
    if layer_for(path, root) == "composition":
        return []
    os_aliases = {"os"}
    environ_aliases: set[str] = set()
    getenv_aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "os":
                    os_aliases.add(alias.asname or "os")
        elif isinstance(node, ast.ImportFrom) and node.module == "os":
            for alias in node.names:
                if alias.name == "environ":
                    environ_aliases.add(alias.asname or "environ")
                if alias.name == "getenv":
                    getenv_aliases.add(alias.asname or "getenv")
    environ_attributes = {f"{alias}.environ" for alias in os_aliases}
    violations = []
    for node in ast.walk(tree):
        name = dotted_name(node.func) if isinstance(node, ast.Call) else None
        reads_environ = isinstance(node, ast.Attribute) and dotted_name(node) in environ_attributes
        reads_configuration = name in {f"{alias}.getenv" for alias in os_aliases}
        reads_configuration = reads_configuration or name in {f"{attribute}.get" for attribute in environ_attributes}
        reads_configuration = reads_configuration or name in getenv_aliases or isinstance(node, ast.Name) and node.id in environ_aliases
        if reads_configuration or reads_environ:
            violations.append(Violation(path, node.lineno, "configuration read outside composition"))
    return violations


def check_determinism(path: Path, tree: ast.Module, root: Path) -> list[Violation]:
    """Keep direct clock, randomness, and identifier generation outside pure layers."""
    if layer_for(path, root) not in INNER_LAYERS:
        return []
    forbidden = {"datetime", "time", "random", "secrets", "uuid"}
    violations = []
    for node in ast.walk(tree):
        imported: set[str] = set()
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported = {node.module.split(".")[0]}
        if imported & forbidden:
            violations.append(Violation(path, node.lineno, "direct nondeterministic facility import"))
    return violations


CHECK_FUNCTIONS: dict[str, Callable[[Path, ast.Module, Path], list[Violation]]] = {
    "layering": check_layering,
    "vendor-signature": check_vendor_signature,
    "port-contract": check_port_contract,
    "configuration": check_configuration,
    "determinism": check_determinism,
}


def run(root: Path, selected: str) -> list[Violation]:
    names = CHECKS if selected == "all" else (selected,)
    violations: list[Violation] = []
    for path in python_files(root):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for name in names:
            violations.extend(CHECK_FUNCTIONS[name](path, tree, root))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--check", choices=("all", *CHECKS), default="all")
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"root does not exist: {args.root}")
    violations = run(args.root.resolve(), args.check)
    if violations:
        for violation in violations:
            print(violation.render(args.root.resolve()))
        return 1
    print(f"PASS: {args.check} architecture fitness checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
