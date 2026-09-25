"""Mechanically enforce the PY-01 Python architecture boundaries and the scoped coupling checks.

The coupling checks (2026-09-25 Founder coupling disposition) compare source with an explicit
coupling register: every cross-module cycle and cross-module domain import must be declared and
classified, and SQLite tables may only be mutated by their declared owner. The register is an
inventory with stated bases, never an allowed-import table: an edge outside a cycle needs no entry.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from hashlib import sha256
import json
import re
from pathlib import Path
from sys import stdlib_module_names
from typing import Callable, Iterable


COUPLING_CHECKS = ("module-cycle", "domain-import", "persistence-ownership")
CHECKS = ("layering", "vendor-signature", "port-contract", "configuration", "determinism", "private-product",
          *COUPLING_CHECKS)
DEFAULT_REGISTER = Path(__file__).with_name("coupling_register.json")
# The composition root wires every module; it is not a bounded context whose domain imports need classifying.
COMPOSITION_ROOT = "composition"
CLASSIFICATIONS = {"STABLE_VALUE", "PORT_CONTRACT", "DOMAIN_LEAKAGE_HELD"}
SQL_MUTATION = re.compile(r"\b(?:CREATE TABLE(?: IF NOT EXISTS)?|INSERT(?: OR [A-Z]+)? INTO|REPLACE INTO|UPDATE|"
                          r"DELETE FROM|ALTER TABLE|DROP TABLE(?: IF EXISTS)?)\s+([A-Za-z_][A-Za-z0-9_]*)")
# Products AlienIntent integrates only through their published interfaces (C#/contracts/4/architecture_fitness).
PRIVATE_PRODUCT_MODULES = {"agent_ready": "Agent Ready private import"}
INNER_LAYERS = {"domain", "application"}
SIGNATURE_LAYERS = {"domain", "ports"}
STDLIB_MODULES = set(stdlib_module_names)


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    message: str

    def render(self, root: Path) -> str:
        path = self.path.relative_to(root) if self.path.is_relative_to(root) else self.path
        return f"{path}:{self.line}: {self.message}"


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


def check_private_product(path: Path, tree: ast.Module, root: Path) -> list[Violation]:
    """No layer imports a product's implementation; its CLI/MCP contract is bound through composition instead."""
    violations = []
    for node in ast.walk(tree):
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules = [node.module]
        for module in modules:
            message = PRIVATE_PRODUCT_MODULES.get(module.split(".")[0])
            if message:
                violations.append(Violation(path, node.lineno, message))
    return violations


CHECK_FUNCTIONS: dict[str, Callable[[Path, ast.Module, Path], list[Violation]]] = {
    "layering": check_layering,
    "vendor-signature": check_vendor_signature,
    "port-contract": check_port_contract,
    "configuration": check_configuration,
    "determinism": check_determinism,
    "private-product": check_private_product,
}


class RegisterInvalid(ValueError):
    """The coupling register is missing or does not have the pinned schema."""


def _entries(document: dict, key: str, fields: set[str]) -> list[dict]:
    entries = document.get(key)
    if not isinstance(entries, list) or not all(isinstance(e, dict) and set(e) == fields for e in entries):
        raise RegisterInvalid(key)
    for entry in entries:
        if not all(isinstance(v, str) and v.strip() or isinstance(v, list) for v in entry.values()):
            raise RegisterInvalid(key)
    return entries


def load_register(path: Path) -> dict:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise RegisterInvalid(f"unreadable: {type(error).__name__}") from None
    if not isinstance(document, dict) or document.get("schema_version") != 1 \
            or document.get("record_kind") != "CouplingRegister" \
            or set(document) != {"schema_version", "record_kind", "authority", "package", "cycles", "domain_imports",
                                 "persistence"}:
        raise RegisterInvalid("schema")
    for cycle in _entries(document, "cycles", {"modules", "edges", "status", "justification"}):
        if not all(isinstance(e, list) and len(e) == 2 and all(isinstance(m, str) for m in e) for e in cycle["edges"]):
            raise RegisterInvalid("cycles")
    for entry in _entries(document, "domain_imports", {"consumer", "target", "owner", "classification", "basis"}):
        if entry["classification"] not in CLASSIFICATIONS:
            raise RegisterInvalid("domain_imports")
    for entry in _entries(document, "persistence", {"owner", "path", "tables", "basis"}):
        if not entry["tables"] or not all(isinstance(t, str) for t in entry["tables"]):
            raise RegisterInvalid("persistence")
    return document


def module_of(path: Path, root: Path) -> str:
    parts = path.relative_to(root).parts
    return parts[0] if len(parts) > 1 else Path(parts[0]).stem


def _names_file(root: Path, dotted: str) -> bool:
    parts = dotted.split(".")[1:]
    return bool(parts) and (root.joinpath(*parts).with_suffix(".py").is_file() or root.joinpath(*parts).is_dir())


def package_imports(path: Path, tree: ast.Module, root: Path) -> list[tuple[int, str]]:
    """Every absolute or relative import inside the checked package, resolved to its dotted module."""
    package = root.name
    here = [package, *path.relative_to(root).parts[:-1]]
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = here[:len(here) - node.level + 1] if node.level else []
            module = ".".join([*base, *([node.module] if node.module else [])])
            for alias in node.names:
                candidate = f"{module}.{alias.name}"
                found.append((node.lineno, candidate if _names_file(root, candidate) else module))
    return [(line, name) for line, name in found if name.split(".")[0] == package and "." in name]


@dataclass(frozen=True)
class Site:
    path: Path
    line: int
    target: str


def module_graph(root: Path, trees: dict[Path, ast.Module]) -> dict[tuple[str, str], list[Site]]:
    edges: dict[tuple[str, str], list[Site]] = {}
    for path, tree in trees.items():
        source = module_of(path, root)
        for line, target in package_imports(path, tree, root):
            module = target.split(".")[1]
            if module != source:
                edges.setdefault((source, module), []).append(Site(path, line, target))
    return edges


def cycles(edges: set[tuple[str, str]]) -> list[frozenset[str]]:
    """Strongly connected module groups of more than one module."""
    successors: dict[str, set[str]] = {}
    for source, target in edges:
        successors.setdefault(source, set()).add(target)
    reach: dict[str, set[str]] = {}
    for start in {m for edge in edges for m in edge}:
        seen, pending = set(), [start]
        while pending:
            for target in successors.get(pending.pop(), ()):
                if target not in seen:
                    seen.add(target)
                    pending.append(target)
        reach[start] = seen
    groups = {frozenset(m for m in reach if m == start or m in reach[start] and start in reach[m]) for start in reach}
    return sorted((g for g in groups if len(g) > 1), key=sorted)


def check_module_cycle(root: Path, trees: dict[Path, ast.Module], register: dict, register_path: Path) -> list[Violation]:
    """Any cross-module cycle must be declared exactly, edge for edge; a new edge into a cycle is a new cycle."""
    graph = module_graph(root, trees)
    declared = [(frozenset(c["modules"]), {tuple(e) for e in c["edges"]}) for c in register["cycles"]]
    violations = []
    for group in cycles(set(graph)):
        inner = {e for e in graph if e[0] in group and e[1] in group}
        match = [edges for modules, edges in declared if modules == group]
        for edge in sorted(inner - (match[0] if match else set())):
            site = graph[edge][0]
            violations.append(Violation(site.path, site.line, "undeclared cross-module cycle edge "
                                        f"{edge[0]} -> {edge[1]} in cycle {', '.join(sorted(group))}"))
        for edge in sorted((match[0] - inner) if match else ()):
            violations.append(Violation(register_path, 1, f"declared cycle edge not observed: {edge[0]} -> {edge[1]}"))
    observed = set(cycles(set(graph)))
    for modules, _ in declared:
        if modules not in observed:
            violations.append(Violation(register_path, 1, f"declared cycle not observed: {', '.join(sorted(modules))}"))
    return violations


def domain_imports(root: Path, trees: dict[Path, ast.Module]) -> dict[tuple[str, str], list[Site]]:
    found: dict[tuple[str, str], list[Site]] = {}
    for path, tree in trees.items():
        consumer = module_of(path, root)
        if consumer == COMPOSITION_ROOT or len(path.relative_to(root).parts) < 2:
            continue
        for line, target in package_imports(path, tree, root):
            parts = target.split(".")
            if parts[1] != consumer and len(parts) > 2 and parts[2] == "domain":
                found.setdefault((consumer, target), []).append(Site(path, line, target))
    return found


def check_domain_import(root: Path, trees: dict[Path, ast.Module], register: dict, register_path: Path) -> list[Violation]:
    """Every cross-module domain import is classified with a basis; a raw import is never silently policy."""
    observed = domain_imports(root, trees)
    classified = {(e["consumer"], e["target"]) for e in register["domain_imports"]}
    violations = [Violation(sites[0].path, sites[0].line, f"unclassified cross-module domain import {key[1]}")
                  for key, sites in sorted(observed.items(), key=lambda item: item[0]) if key not in classified]
    violations.extend(Violation(register_path, 1, f"classified domain import not observed: {c} -> {t}")
                      for c, t in sorted(classified - set(observed)))
    return violations


def sql_tables(tree: ast.Module) -> list[tuple[int, str]]:
    return [(node.lineno, table) for node in ast.walk(tree) if isinstance(node, ast.Constant)
            and isinstance(node.value, str) for table in SQL_MUTATION.findall(node.value)
            if table.upper() != "SET"]  # An upsert's DO UPDATE SET names no table.


def imports_sqlite(tree: ast.Module) -> int | None:
    for node in ast.walk(tree):
        modules = [a.name for a in node.names] if isinstance(node, ast.Import) else \
            [node.module or ""] if isinstance(node, ast.ImportFrom) and node.level == 0 else []
        if any(m.split(".")[0] == "sqlite3" for m in modules):
            return node.lineno
    return None


def check_persistence_ownership(root: Path, trees: dict[Path, ast.Module], register: dict,
                                register_path: Path) -> list[Violation]:
    """A table has one declared owning file; only declared owners open SQLite at all."""
    owners = {table: entry["path"] for entry in register["persistence"] for table in entry["tables"]}
    owner_paths = {entry["path"] for entry in register["persistence"]}
    seen: set[str] = set()
    violations = []
    for path, tree in trees.items():
        relative = path.relative_to(root).as_posix()
        line = imports_sqlite(tree)
        if line is not None and relative not in owner_paths:
            violations.append(Violation(path, line, "sqlite3 access outside a declared persistence owner"))
        for line, table in sql_tables(tree):
            if table not in owners:
                violations.append(Violation(path, line, f"undeclared persistence table {table}"))
            elif owners[table] != relative:
                violations.append(Violation(path, line, f"table {table} owned by {owners[table]} is mutated outside "
                                                        "its owner"))
            else:
                seen.add(table)
    violations.extend(Violation(register_path, 1, f"declared persistence table not observed: {table}")
                      for table in sorted(set(owners) - seen))
    return violations


COUPLING_FUNCTIONS: dict[str, Callable[[Path, dict[Path, ast.Module], dict, Path], list[Violation]]] = {
    "module-cycle": check_module_cycle,
    "domain-import": check_domain_import,
    "persistence-ownership": check_persistence_ownership,
}


def parse(root: Path) -> dict[Path, ast.Module]:
    return {path: ast.parse(path.read_text(encoding="utf-8"), filename=str(path)) for path in python_files(root)}


def inventory(root: Path, register_path: Path) -> dict:
    """The observed module graph plus the register, for design admission; descriptive, never permission."""
    register = load_register(register_path)
    trees = parse(root)
    return {"schema_version": 1, "record_kind": "CouplingInventory", "package": root.name,
            "register_sha256": sha256(register_path.read_bytes()).hexdigest(),
            "modules": sorted({module_of(p, root) for p in trees}),
            "edges": sorted(list(e) for e in module_graph(root, trees)),
            "cycles": [sorted(list(e) for e in c["edges"]) for c in register["cycles"]],
            "domain_imports": sorted([e["consumer"], e["target"], e["classification"]]
                                     for e in register["domain_imports"])}


def run(root: Path, selected: str, register_path: Path = DEFAULT_REGISTER) -> list[Violation]:
    names = CHECKS if selected == "all" else (selected,)
    violations: list[Violation] = []
    trees = parse(root)
    for path, tree in trees.items():
        for name in names:
            if name in CHECK_FUNCTIONS:
                violations.extend(CHECK_FUNCTIONS[name](path, tree, root))
    coupling = [name for name in names if name in COUPLING_FUNCTIONS]
    if coupling:
        try:
            register = load_register(register_path)
        except RegisterInvalid as error:
            return [*violations, Violation(register_path, 1, f"coupling register unavailable: {error}")]
        for name in coupling:
            violations.extend(COUPLING_FUNCTIONS[name](root, trees, register, register_path))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--check", choices=("all", *CHECKS), default="all")
    parser.add_argument("--register", type=Path, default=DEFAULT_REGISTER)
    parser.add_argument("--inventory", action="store_true", help="print the coupling inventory as JSON")
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"root does not exist: {args.root}")
    if args.inventory:
        try:
            print(json.dumps(inventory(args.root.resolve(), args.register.resolve()), sort_keys=True))
        except RegisterInvalid as error:
            print(f"coupling register unavailable: {error}")
            return 1
        return 0
    violations = run(args.root.resolve(), args.check, args.register.resolve())
    if violations:
        for violation in violations:
            print(violation.render(args.root.resolve()))
        return 1
    print(f"PASS: {args.check} architecture fitness checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
