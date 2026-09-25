"""Scan-progress observation owned by execution coordination.

The scan owner reports the start and the full-attempt result of each periodic
scan. The real SF-REQ-056 scan is not composed here; C4 drives this port from an
injected fake scanner only.
"""
from dataclasses import dataclass
from typing import Literal, Protocol


class ScanOutcomeInvalid(ValueError):
    """A reported scan result does not describe a finished attempt."""


@dataclass(frozen=True)
class ScanOutcome:
    status: Literal["COMPLETE", "FAILED", "EVIDENCE_HOLD"]
    error: str | None = None
    active_work: int = 0

    def __post_init__(self) -> None:
        if (self.status not in ("COMPLETE", "FAILED", "EVIDENCE_HOLD")
                or (self.status == "COMPLETE") != (self.error is None)
                or self.error is not None and (not isinstance(self.error, str) or not self.error.strip())
                or type(self.active_work) is not int or self.active_work < 0):
            raise ScanOutcomeInvalid(self.status)


class ScanProgress(Protocol):
    def scan_started(self) -> object: ...
    def scan_finished(self, outcome: ScanOutcome) -> object: ...
