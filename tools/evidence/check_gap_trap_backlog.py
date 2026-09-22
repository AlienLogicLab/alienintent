#!/usr/bin/env python3
"""Contract checker for the Phase 3 promotion backlog (`wave1-gap-trap-promotion-backlog.json`).

Terminology (2026-09-22): the canonical AlienIntent term is *deterministic failure-class
promotion* (SWF-24 / SF-REQ-050). "Gap Trap" is the name of the external project that informed
it and is retained here only because the historical artifact this checker validates carries it.

The canonical principle this serves:

    VERIFY proves what AlienIntent already knows how to check.
    REVIEW discovers what AlienIntent does not yet know how to check.

A promotion moves a recurring known failure class out of REVIEW cognition and into mechanical
enforcement. The failure mode worth guarding is over-promotion: a gate that was never shown to
fail is a prose reminder wearing a gate's clothing, and it consumes the review budget it was
meant to free. So BLOCKING requires a proven-red method and a violation fixture, and every
promotion must name reviewer work that actually disappears.

Absence is written in this repository as "none — <why>", never as the bare word. An exact-match
test for "none" passed two records in Phase 2 that should have failed; `_absent` exists so that
defect is not repeated here.

Usage:
    python3 tools/evidence/check_gap_trap_backlog.py [backlog.json]
        [--candidates prework/POSTW1-GAPTRAP-003-candidates.json]
        [--layers prework/POSTW1-GAPTRAP-003-enforcement-layers.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED = ("learning_id", "failure_class", "cheapest_enforcement_layer", "deterministic_rule",
            "violation_fixture", "proven_red_method", "advisory_or_blocking", "canonical_owner",
            "expected_cognitive_work_removed", "effectiveness_metric")

ENFORCEMENT_CHOICE = ("ADVISORY", "BLOCKING")

CHECKS = ("required_fields", "traceable_to_ledger", "enforcement_layer_known",
          "blocking_needs_proven_red", "removes_cognitive_work", "valid_enum_values",
          "summary_matches_candidates")

_ABSENT_HEADS = ("none", "unknown", "n/a", "not yet", "tbd", "nothing", "no change", "unchanged")


def _absent(value) -> bool:
    """True when a field says, in any of its customary spellings, that there is nothing here."""
    val = str(value or "").strip().lower()
    if not val:
        return True
    head = val.split("—")[0].split(" - ")[0].split(":")[0].strip(" .-")
    return head in _ABSENT_HEADS or head.startswith("none")


def check_backlog(backlog: dict, known_ids: set[str], known_layers: set[str]
                  ) -> tuple[bool, list[str]]:
    failures: list[str] = []
    cands = backlog.get("candidates", [])

    for c in cands:
        cid = c.get("learning_id", "<no id>")

        missing = [f for f in REQUIRED if f not in c]
        if missing:
            failures.append(f"required_fields: {cid} is missing {missing}")
            continue

        if cid not in known_ids:
            failures.append(
                f"traceable_to_ledger: {cid} is not a Wave 1 Learning Ledger lesson; Phase 3 "
                "promotes existing lessons, it does not invent them")

        layer = str(c["cheapest_enforcement_layer"])
        if layer.startswith("NEW:"):
            if _absent(c.get("new_layer_justification")):
                failures.append(
                    f"enforcement_layer_known: {cid} proposes new layer {layer!r} without "
                    "new_layer_justification; a new layer is a cost that must be argued")
        elif layer not in known_layers:
            failures.append(
                f"enforcement_layer_known: {cid} names layer {layer!r}, which is not an existing "
                f"layer; use one of {sorted(known_layers)} or declare it as NEW:<name>")

        if c["advisory_or_blocking"] not in ENFORCEMENT_CHOICE:
            failures.append(
                f"valid_enum_values: {cid} has advisory_or_blocking="
                f"{c['advisory_or_blocking']!r}, not one of {ENFORCEMENT_CHOICE}")

        if c["advisory_or_blocking"] == "BLOCKING":
            if _absent(c["proven_red_method"]):
                failures.append(
                    f"blocking_needs_proven_red: {cid} blocks without a proven-red method; a gate "
                    "never shown to fail must not stop the factory. Demote to ADVISORY or design "
                    "the red case")
            if _absent(c["violation_fixture"]):
                failures.append(
                    f"blocking_needs_proven_red: {cid} blocks without a violation fixture")

        if _absent(c["expected_cognitive_work_removed"]):
            failures.append(
                f"removes_cognitive_work: {cid} removes no reviewer or model work; a promotion "
                "that frees no cognition adds a gate and buys nothing")

    declared = backlog.get("summary", {}).get("promotions")
    if declared is not None and declared != len(cands):
        failures.append(
            f"summary_matches_candidates: summary promotions={declared} but {len(cands)} "
            "candidate(s) present")

    return (not failures), failures


def _load_ids(path: Path) -> set[str]:
    data = json.loads(path.read_text())
    return {c["learning_id"] for c in data.get("candidates", [])}


def _load_layers(path: Path) -> set[str]:
    return set(json.loads(path.read_text()).get("existing_layers", {}))


def main(argv: list[str]) -> int:
    pre = Path("docs/operations/post-wave1-program/prework")
    ap = argparse.ArgumentParser()
    ap.add_argument("backlog", nargs="?",
                    default="docs/evidence/wave1-gap-trap-promotion-backlog.json")
    ap.add_argument("--candidates", default=str(pre / "POSTW1-GAPTRAP-003-candidates.json"))
    ap.add_argument("--layers", default=str(pre / "POSTW1-GAPTRAP-003-enforcement-layers.json"))
    args = ap.parse_args(argv)

    backlog = json.loads(Path(args.backlog).read_text())
    ok, failures = check_backlog(backlog, _load_ids(Path(args.candidates)),
                                 _load_layers(Path(args.layers)))
    print(f"backlog    : {args.backlog}")
    print(f"candidates : {len(backlog.get('candidates', []))}")
    print(f"checks     : {', '.join(CHECKS)}")
    print(f"result     : {'PASS' if ok else 'FAIL'}  ({len(failures)} failure(s))")
    for f in failures:
        print(f"  - {f}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
