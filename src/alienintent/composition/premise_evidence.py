"""Composition-owned PremiseEvidence bridge over retained installation-doctor evidence.

Only retained, digest-pinned artifacts are read under a digest-pinned predicate mapping.
Nothing here runs the doctor, a probe or a credential call; the mapping is
authority-reviewed data, not code. Unreadable or malformed input becomes a recorded gap
that the domain turns into InfeasibleProof, never an exception or an invented observation.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat

from alienintent.evidence_learning.domain.premise import (
    IsolationObservable, PremiseObservation, RetainedPremiseEvidence)
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.evidence_learning.ports.premise_evidence import PremiseEvidence
from alienintent.installation.application.doctor import REQUIRED_CHECKS

_ABSENT = object()
_DOCTOR_DETAIL = re.compile(r"disposition=(\w+) exit=(\d+) outcomes=(\{.*\})")
_OBSERVABLES = {o.value for o in IsolationObservable}
MAX_RETAINED_BYTES = 10 * 1024 * 1024


class RetainedDoctorPremiseEvidence(PremiseEvidence):
    def __init__(self, repository_root: Path, mapping_path: Path, mapping_sha256: str, project: str, profile: str) -> None:
        if not all(isinstance(v, str) and v.strip() for v in (project, profile, mapping_sha256)):
            raise ValueError("project, profile and the pinned mapping sha256 must be configured")
        self._root, self._mapping_path, self._mapping_sha256 = Path(repository_root), str(mapping_path), mapping_sha256
        self._project, self._profile = project, profile

    def observe(self) -> RetainedPremiseEvidence:
        mapping, mapping_ref = self._mapping()
        if mapping is None:
            return RetainedPremiseEvidence("", None, "", False, None, (), ("mapping:" + self._mapping_path,))
        artifacts, unavailable = {}, []
        for key, spec in mapping["artifacts"].items():
            loaded = self._load(key, spec)
            if loaded is None:
                unavailable.append("artifact:" + key)
            elif loaded[2] is None:
                unavailable.append("target:" + key)
            else:
                artifacts[key] = loaded
        doctor_passed, doctor_ref = self._doctor(mapping["doctor"], artifacts)
        observations = []
        for entry in mapping["observables"]:
            observation = self._observe(entry, *artifacts[entry["artifact"]]) if entry["artifact"] in artifacts else None
            if observation is None:
                # Every mapped predicate is an obligation; an absent one is a missing premise.
                unavailable.append("predicate:" + entry.get("check", entry["observable"]))
            else:
                observations.append(observation)
        return RetainedPremiseEvidence(mapping["premise_id"], mapping_ref, mapping["target"], doctor_passed, doctor_ref,
                                       tuple(observations), tuple(dict.fromkeys(unavailable)))

    def _mapping(self) -> tuple[dict | None, Ref | None]:
        body = _read_retained(self._root, self._mapping_path)
        if body is None or sha256(body).hexdigest() != self._mapping_sha256:
            return None, None
        mapping = _json(body)
        if not _valid_mapping(mapping):
            return None, None
        return mapping, Ref(self._project, self._profile, "premise-mapping", "sha256:" + self._mapping_sha256,
                            "repository:" + self._mapping_path)

    def _load(self, key: str, spec: dict) -> tuple[object, Ref, str | None] | None:
        body = _read_retained(self._root, spec["path"])
        if body is None or sha256(body).hexdigest() != spec["sha256"]:
            return None
        document = _json(body)
        if document is _ABSENT:
            return None
        ref = Ref(self._project, self._profile, key, "sha256:" + spec["sha256"], "repository:" + spec["path"])
        return document, ref, _artifact_target(document, spec["target"])

    @staticmethod
    def _doctor(spec: dict, artifacts: dict) -> tuple[bool, Ref | None]:
        if spec["artifact"] not in artifacts:
            return False, None
        document, ref, _ = artifacts[spec["artifact"]]
        check = _check(document, spec["check"])
        detail = check.get("detail") if check is not None else None
        match = _DOCTOR_DETAIL.fullmatch(detail) if isinstance(detail, str) else None
        if check is None or check.get("ok") is not True or match is None:
            return False, None
        outcomes = _json(match[3])
        passed = (match[1], match[2]) == ("PASS", "0") and isinstance(outcomes, dict) \
            and set(outcomes) == set(REQUIRED_CHECKS) and all(v == "PASS" for v in outcomes.values())
        return passed, _locate(ref, spec["check"])

    @staticmethod
    def _observe(entry: dict, document: object, ref: Ref, target: str) -> PremiseObservation | None:
        observable = IsolationObservable(entry["observable"])
        if "check" in entry:
            check = _check(document, entry["check"])
            if check is None:
                return None
            detail = check.get("detail")
            detail = detail if isinstance(detail, str) else ""
            pattern = entry.get("detail_pattern")
            satisfied = check.get("ok") is True and (pattern is None or re.fullmatch(pattern, detail) is not None)
            return PremiseObservation(observable, target, entry["check"], detail, satisfied, _locate(ref, entry["check"]))
        pointers = entry["unchanged"]
        pairs = [(p, _pointer(document, "/before" + p), _pointer(document, "/after" + p)) for p in pointers]
        satisfied = all(_read_back(b) and _canonical(b) == _canonical(a) for _, b, a in pairs)
        observed = "; ".join(f"{p}: {_show(b)} -> {_show(a)}" for p, b, a in pairs)
        return PremiseObservation(observable, target, "unchanged:" + ",".join(pointers), observed, satisfied,
                                  _locate(ref, "/before,/after"))


def _valid_mapping(mapping: object) -> bool:
    def text(value: object) -> bool:
        return isinstance(value, str) and bool(value.strip())

    if not isinstance(mapping, dict) or not all(text(mapping.get(k)) for k in ("premise_id", "target")):
        return False
    artifacts, doctor, entries = mapping.get("artifacts"), mapping.get("doctor"), mapping.get("observables")
    if not isinstance(artifacts, dict) or not artifacts or not isinstance(doctor, dict) \
            or not isinstance(entries, list) or not entries:
        return False
    if not all(text(key) for key in artifacts):
        return False
    for spec in artifacts.values():
        locator = spec.get("target") if isinstance(spec, dict) else None
        if not isinstance(spec, dict) or not _repository_path(spec.get("path")) \
                or not isinstance(spec.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", spec["sha256"]) \
                or not isinstance(locator, dict) or not (set(locator) == {"pointer"} and text(locator["pointer"])
                                                         or set(locator) == {"check", "field"} and text(locator["check"]) and text(locator["field"])):
            return False
    if not text(doctor.get("artifact")) or doctor["artifact"] not in artifacts or not text(doctor.get("check")):
        return False
    for entry in entries:
        if not isinstance(entry, dict) or not text(entry.get("observable")) or entry["observable"] not in _OBSERVABLES \
                or not text(entry.get("artifact")) or entry["artifact"] not in artifacts:
            return False
        unchanged = entry.get("unchanged")
        by_check = text(entry.get("check")) and "unchanged" not in entry \
            and ("detail_pattern" not in entry or _pattern(entry["detail_pattern"]))
        by_readback = "check" not in entry and isinstance(unchanged, list) and bool(unchanged) \
            and all(text(p) and p.startswith("/") for p in unchanged)
        if not (by_check or by_readback):
            return False
    return True


def _pattern(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        re.compile(value)
    except (re.error, RecursionError, OverflowError):
        return False
    return True


def _read_retained(root: Path, relative: str) -> bytes | None:
    """Read one bounded regular file that resolves inside the repository root, else a gap.

    Symlinks may not lead outside the root, and devices or FIFOs are refused before open,
    so a hostile path can neither redirect the evidence nor block or exhaust the read.
    """
    try:
        base = root.resolve(strict=True)
        path = (root / relative).resolve(strict=True)
        if not path.is_relative_to(base):
            return None
        status = os.stat(path)
        if not stat.S_ISREG(status.st_mode) or status.st_size > MAX_RETAINED_BYTES:
            return None
        with open(path, "rb") as handle:
            body = handle.read(MAX_RETAINED_BYTES + 1)
    except (OSError, ValueError, RuntimeError):
        return None
    return body if len(body) <= MAX_RETAINED_BYTES else None


def _canonical(value: object) -> str | None:
    """Type-exact comparison: ``true`` is not ``1`` and ``67`` is not ``67.0``."""
    try:
        return json.dumps(value, sort_keys=True)
    except (TypeError, ValueError, RecursionError):
        return None


def _repository_path(value: object) -> bool:
    """Retained evidence is repository-relative: no absolute path, parent step or NUL."""
    if not isinstance(value, str) or not value.strip() or "\x00" in value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts


def _json(body: bytes | str) -> object:
    def unique(pairs: list[tuple[str, object]]) -> dict:
        keys = [k for k, _ in pairs]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate key")
        return dict(pairs)
    try:
        return json.loads(body, object_pairs_hook=unique)
    except (ValueError, UnicodeError, RecursionError):
        return _ABSENT


def _artifact_target(document: object, locator: dict) -> str | None:
    if "pointer" in locator:
        value = _pointer(document, locator["pointer"])
    else:
        check = _check(document, locator["check"])
        value = _evidence(check).get(locator["field"], _ABSENT) if check is not None else _ABSENT
    return value if isinstance(value, str) and value else None


def _check(document: object, name: str) -> dict | None:
    checks = document.get("checks") if isinstance(document, dict) else None
    found = [c for c in checks if isinstance(c, dict) and c.get("check") == name] if isinstance(checks, list) else []
    return found[0] if len(found) == 1 else None


def _evidence(check: dict) -> dict:
    detail = check.get("detail")
    if not isinstance(detail, str) or not detail.startswith("evidence="):
        return {}
    value = _json(detail[len("evidence="):])
    return value if isinstance(value, dict) else {}


def _pointer(document: object, pointer: str) -> object:
    value = document
    for part in pointer.strip("/").split("/"):
        if not isinstance(value, dict) or part not in value:
            return _ABSENT
        value = value[part]
    return value


def _read_back(value: object) -> bool:
    """A readback is only evidence when a value was actually read on that side.

    Absent, null, empty and ``False`` values agreeing before and after are agreement
    without a readback (for example ``observed: false`` on both sides), not an unchanged state.
    """
    if value is _ABSENT or value is None or value is False:
        return False
    return not (isinstance(value, (str, list, dict)) and not value)


def _show(value: object) -> str:
    return "<absent>" if value is _ABSENT else json.dumps(value, sort_keys=True)


def _locate(ref: Ref, fragment: str) -> Ref:
    return Ref(ref.project, ref.profile, ref.logical_id, ref.revision_digest, ref.locator + "#" + fragment)
