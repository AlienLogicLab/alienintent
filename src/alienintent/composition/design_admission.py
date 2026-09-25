"""Outer-boundary inputs of design admission: the existing architecture checker with its scoped coupling checks,
the U3 premise reader and the pinned directional-authority record. None of them can approve a design or dispose
authority."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from alienintent.composition.premise_evidence import _ABSENT, _json, _read_retained, _repository_path
from alienintent.context_assembly.domain.design_admission import (
    COUPLING_CHECKS, DISPOSED, EXISTING_CHECKS, ArchitectureReport, CheckResult, CouplingEvidence, DirectionAuthority,
    PremiseResult)
from alienintent.context_assembly.ports.design_admission import ArchitectureChecks, DirectionAuthoritySource, PremiseCheck
from alienintent.evidence_learning.application.premise_service import PremiseEvidenceReader
from alienintent.evidence_learning.domain.premise import InfeasibleProof
from alienintent.evidence_learning.domain.refs import Ref

EDGE_AUTHORITY_GAP = "R2-GAP-051-EDGE-AUTHORITY"
_OPEN_GAP = "FOUNDER_AUTHORITY_GAP"


class RepositoryArchitectureChecks(ArchitectureChecks):
    """Runs tools/fitness/check_architecture.py once per existing and scoped coupling check, then reads the
    coupling inventory from the same source and register; an unreadable inventory is absent, never empty."""

    def __init__(self, checker: Path, source_root: Path, timeout: float = 120.0, register: Path | None = None) -> None:
        self._checker, self._root, self._timeout = Path(checker), Path(source_root), timeout
        self._register = Path(register) if register is not None else self._checker.with_name("coupling_register.json")

    def _checker_run(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(self._checker), "--root", str(self._root),
                               "--register", str(self._register), *arguments],
                              capture_output=True, text=True, timeout=self._timeout, check=False)

    def run(self) -> ArchitectureReport:
        files = sorted(p for p in self._root.rglob("*.py") if "__pycache__" not in p.parts)
        baseline = sha256(self._checker.read_bytes())
        for path in files:
            baseline.update(path.relative_to(self._root).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
        if self._register.is_file():  # The register is part of the baseline: reclassifying invalidates a design.
            baseline.update(b"coupling-register\0" + self._register.read_bytes() + b"\0")
        results = []
        for name in (*EXISTING_CHECKS, *COUPLING_CHECKS):
            try:
                completed = self._checker_run("--check", name)
                lines = tuple(line for line in completed.stdout.splitlines() if line and not line.startswith("PASS:"))
                results.append(CheckResult(name, completed.returncode == 0,
                                           lines if completed.returncode else ()))
            except (OSError, subprocess.TimeoutExpired) as error:
                results.append(CheckResult(name, False, (f"check did not complete: {type(error).__name__}",)))
        return ArchitectureReport("sha256:" + baseline.hexdigest(), tuple(results), self._inventory())

    def _inventory(self) -> CouplingEvidence | None:
        try:
            completed = self._checker_run("--inventory")
            document = json.loads(completed.stdout) if completed.returncode == 0 else None
            if not isinstance(document, dict) or document.get("record_kind") != "CouplingInventory" \
                    or document.get("schema_version") != 1:
                return None
            return CouplingEvidence(
                document["package"], frozenset((a, b) for a, b in document["edges"]),
                tuple(frozenset((a, b) for a, b in cycle) for cycle in document["cycles"]),
                {(consumer, target): use for consumer, target, use in document["domain_imports"]})
        except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError):
            return None


class PremiseReaderCheck(PremiseCheck):
    """Adapts the U3 retained premise reader; a missing or impossible premise is infeasible, never assumed."""

    def __init__(self, reader: PremiseEvidenceReader) -> None:
        self._reader = reader

    def check(self, premise_id: str, requested: frozenset[str]) -> PremiseResult:
        result = self._reader.read(premise_id, requested)
        if isinstance(result, InfeasibleProof):
            return PremiseResult(premise_id, False, result.reason_code, tuple(result.missing), tuple(result.evidence_refs))
        return PremiseResult(premise_id, True, None, (),
                             tuple(dict.fromkeys((result.mapping_ref, result.doctor_ref,
                                                  *(o.source_ref for o in result.observations)))))


class RetainedDirectionAuthority(DirectionAuthoritySource):
    """Reads the pinned authority_gaps entry and the descriptive observed_edges graph; unreadable is UNAVAILABLE.

    The gap is disposed only by exactly one recorded RESOLVED resolution whose authority document is a readable
    repository file naming the gap; the disposition document's digest is then part of the authority snapshot."""

    def __init__(self, repository_root: Path, path: str, sha256_hex: str, gap_id: str, project: str, profile: str) -> None:
        self._root, self._path, self._sha256, self._gap = Path(repository_root), path, sha256_hex, gap_id
        self._project, self._profile = project, profile

    def read(self) -> DirectionAuthority:
        unavailable = DirectionAuthority(self._gap, "UNAVAILABLE", "Founder", None, {})
        body = _read_retained(self._root, self._path) if _repository_path(self._path) else None
        if body is None or sha256(body).hexdigest() != self._sha256:
            return unavailable
        document = _json(body)
        gaps = document.get("authority_gaps") if isinstance(document, dict) else None
        found = [g for g in gaps if isinstance(g, dict) and g.get("id") == self._gap] if isinstance(gaps, list) else []
        if document is _ABSENT or len(found) != 1 or not isinstance(found[0].get("status"), str):
            return unavailable
        direction = (document.get("shared_contracts") or {}).get("context_dependency_direction") or {}
        observed = direction.get("observed_edges") if isinstance(direction, dict) else None
        ref = Ref(self._project, self._profile, "authority-gap:" + self._gap, "sha256:" + self._sha256,
                  f"repository:{self._path}#authority_gaps[id={self._gap}]")
        # Only the named resolution actor's recorded disposition could change this status; nothing here does.
        status = "OPEN" if found[0]["status"] == _OPEN_GAP else found[0]["status"]
        resolutions = [v for k, v in found[0].items() if k.startswith("resolution_") and isinstance(v, dict)]
        disposition = None
        if resolutions:
            disposition = self._disposition(resolutions)
            if disposition is None:
                return unavailable
            status = DISPOSED
        return DirectionAuthority(self._gap, status, str(found[0].get("resolution_actor", "Founder")), ref,
                                  observed if isinstance(observed, dict) else {}, disposition)

    def _disposition(self, resolutions: list[dict]) -> Ref | None:
        if len(resolutions) != 1 or resolutions[0].get("status") != "RESOLVED":
            return None
        path = resolutions[0].get("authority")
        body = _read_retained(self._root, path) if _repository_path(path) else None
        if body is None or self._gap.encode() not in body:
            return None
        return Ref(self._project, self._profile, "authority-disposition:" + self._gap,
                   "sha256:" + sha256(body).hexdigest(), f"repository:{path}")
