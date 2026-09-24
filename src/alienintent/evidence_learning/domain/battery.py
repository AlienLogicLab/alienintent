"""Qualified intact/red/restored battery (014-discrimination).

Only a single applied mutation that fails exactly its named assertion, between clean intact
and restored runs, is a qualified kill. Constant success, an untriggered guard, an unrelated
failure or an overdetermined kill is refused as proof.
"""
from dataclasses import dataclass

QUALIFIED_KILL = "QUALIFIED_KILL"
PHASES = ("intact", "fault", "restored")


@dataclass(frozen=True)
class ControlRun:
    phase: str
    exit_status: int | None  # None: timed out, so no result was observed.
    application_count: int
    failed_assertions: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ControlVerdict:
    obligation_id: str
    guard: str
    target_assertion: str
    reason: str

    @property
    def qualified(self) -> bool:
        return self.reason == QUALIFIED_KILL


def _clean(run: ControlRun) -> bool:
    return run.exit_status == 0 and run.application_count == 0 and not run.failed_assertions and not run.errors


def evaluate_control(obligation_id: str, guard: str, target_assertion: str,
                     runs: tuple[ControlRun, ...]) -> ControlVerdict:
    def verdict(reason: str) -> ControlVerdict:
        return ControlVerdict(obligation_id, guard, target_assertion, reason)

    if not target_assertion or sorted(r.phase for r in runs) != sorted(PHASES):
        return verdict("MISSING_PHASE")
    intact, fault, restored = (next(r for r in runs if r.phase == p) for p in PHASES)
    if not _clean(intact):
        return verdict("INTACT_NOT_CLEAN")
    if not _clean(restored):
        return verdict("RESTORED_NOT_CLEAN")
    if fault.application_count == 0:
        return verdict("ZERO_APPLICATION")
    if fault.exit_status == 0:
        return verdict("UNCONDITIONAL_SUCCESS")
    if fault.exit_status is None or fault.errors or target_assertion not in fault.failed_assertions:
        return verdict("UNRELATED_FAILURE")
    if fault.application_count != 1 or set(fault.failed_assertions) != {target_assertion}:
        return verdict("OVERDETERMINED")
    return verdict(QUALIFIED_KILL)
