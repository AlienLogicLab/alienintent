"""Composition-owned PremiseEvidence bridge over retained installation-doctor evidence.

Only retained, digest-pinned artifacts are read. Nothing here runs the doctor, a probe
or a credential call; the predicate mapping is authority-reviewed data, not code.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re

from alienintent.evidence_learning.domain.premise import (
    IsolationObservable, PremiseObservation, RetainedPremiseEvidence)
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.evidence_learning.ports.premise_evidence import PremiseEvidence
from alienintent.installation.application.doctor import REQUIRED_CHECKS

_ABSENT = object()
_DOCTOR_DETAIL = re.compile(r"disposition=(\w+) exit=(\d+) outcomes=(\{.*\})")


class RetainedDoctorPremiseEvidence(PremiseEvidence):
    def __init__(self, repository_root: Path, mapping_path: Path, project: str, profile: str) -> None:
        self._root, self._project, self._profile = Path(repository_root), project, profile
        self.mapping = json.loads((self._root / mapping_path).read_text(encoding="utf-8"))
        self.target = self.mapping["target"]

    def observe(self) -> RetainedPremiseEvidence:
        artifacts, unavailable = {}, []
        for key, spec in self.mapping["artifacts"].items():
            loaded = self._load(key, spec)
            if loaded is None:
                unavailable.append("artifact:" + key)
            else:
                artifacts[key] = loaded
        doctor_passed, doctor_ref = self._doctor(artifacts)
        observations = []
        for entry in self.mapping["observables"]:
            if entry["artifact"] not in artifacts:
                continue
            observation = self._observe(entry, *artifacts[entry["artifact"]])
            if observation is None:
                # Every mapped predicate is an obligation; an absent one is a missing premise.
                unavailable.append("predicate:" + entry["check"])
            else:
                observations.append(observation)
        return RetainedPremiseEvidence(self.target, doctor_passed, doctor_ref, tuple(observations), tuple(unavailable))

    def _load(self, key: str, spec: dict) -> tuple[object, Ref, str] | None:
        path = self._root / spec["path"]
        if not path.is_file():
            return None
        body = path.read_bytes()
        if sha256(body).hexdigest() != spec["sha256"]:
            return None
        try:
            document = json.loads(body)
        except ValueError:
            return None
        ref = Ref(self._project, self._profile, key, "sha256:" + spec["sha256"], "repository:" + spec["path"])
        return document, ref, self._artifact_target(document, spec.get("target", {}))

    @staticmethod
    def _artifact_target(document: object, locator: dict) -> str:
        if "pointer" in locator:
            value = _pointer(document, locator["pointer"])
        elif "check" in locator:
            check = _check(document, locator["check"])
            value = _evidence(check).get(locator.get("field", ""), _ABSENT) if check is not None else _ABSENT
        else:
            value = _ABSENT
        return value if isinstance(value, str) else ""

    def _doctor(self, artifacts: dict) -> tuple[bool, Ref | None]:
        spec = self.mapping["doctor"]
        if spec["artifact"] not in artifacts:
            return False, None
        document, ref, _ = artifacts[spec["artifact"]]
        check = _check(document, spec["check"])
        match = _DOCTOR_DETAIL.fullmatch(check.get("detail", "")) if check is not None else None
        if check is None or check.get("ok") is not True or match is None:
            return False, None
        try:
            outcomes = json.loads(match[3])
        except ValueError:
            return False, None
        passed = (match[1], match[2]) == ("PASS", "0") and isinstance(outcomes, dict) \
            and set(outcomes) == set(REQUIRED_CHECKS) and all(v == "PASS" for v in outcomes.values())
        return passed, Ref(ref.project, ref.profile, ref.logical_id, ref.revision_digest, ref.locator + "#" + spec["check"])

    def _observe(self, entry: dict, document: object, ref: Ref, target: str) -> PremiseObservation | None:
        observable = IsolationObservable(entry["observable"])
        if "check" in entry:
            check = _check(document, entry["check"])
            if check is None:
                return None
            return PremiseObservation(observable, target, entry["check"], str(check.get("detail", "")),
                                      check.get("ok") is True, _locate(ref, entry["check"]))
        pointers = entry["unchanged"]
        pairs = [(p, _pointer(document, "/before" + p), _pointer(document, "/after" + p)) for p in pointers]
        # A readback is only evidence when both sides were read and agree; a boolean must be
        # True because `observed: false` on both sides is agreement without a readback.
        satisfied = bool(pairs) and all(b is not _ABSENT and b == a and (b is True or not isinstance(b, bool))
                                        for _, b, a in pairs)
        observed = "; ".join(f"{p}: {_show(b)} -> {_show(a)}" for p, b, a in pairs)
        return PremiseObservation(observable, target, "unchanged:" + ",".join(pointers), observed, satisfied,
                                  _locate(ref, "/before,/after"))


def _check(document: object, name: str) -> dict | None:
    checks = document.get("checks") if isinstance(document, dict) else None
    found = [c for c in checks if isinstance(c, dict) and c.get("check") == name] if isinstance(checks, list) else []
    return found[0] if len(found) == 1 else None


def _evidence(check: dict) -> dict:
    detail = check.get("detail", "")
    if not isinstance(detail, str) or not detail.startswith("evidence="):
        return {}
    try:
        value = json.loads(detail[len("evidence="):])
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def _pointer(document: object, pointer: str) -> object:
    value = document
    for part in pointer.strip("/").split("/"):
        if not isinstance(value, dict) or part not in value:
            return _ABSENT
        value = value[part]
    return value


def _show(value: object) -> str:
    return "<absent>" if value is _ABSENT else json.dumps(value, sort_keys=True)


def _locate(ref: Ref, fragment: str) -> Ref:
    return Ref(ref.project, ref.profile, ref.logical_id, ref.revision_digest, ref.locator + "#" + fragment)
