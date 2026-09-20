"""Reference-only secret resolution boundary."""

from typing import Protocol


class SecretProvider(Protocol):
    def resolve(self, reference: str) -> bytes: ...
    def diagnostic(self) -> str: ...
