"""Explicit local fenced lane; no implicit bootstrap or remote-consumer adoption."""
from collections.abc import Callable
from pathlib import Path

from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.guarded_effect_execution import GuardedEffectExecutor


class FencedProfile:
    def __init__(self, database: Path, *, name: str, clock: Callable[[], float]) -> None:
        self.name = name
        self.store = SQLiteOperationalStore(database, clock=clock)
        self.executor = GuardedEffectExecutor(self.store)
