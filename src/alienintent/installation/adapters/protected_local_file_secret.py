"""Protected local-file SecretProvider; values never appear in diagnostics."""

from pathlib import Path
from typing import Mapping

from alienintent.installation.ports.secret_provider import SecretProvider


class ProtectedLocalFileSecretProvider(SecretProvider):
    def __init__(self, references: Mapping[str, Path]) -> None:
        self._references = dict(references)

    def resolve(self, reference: str) -> bytes:
        path = self._references.get(reference)
        if path is None:
            raise KeyError(reference)
        return path.read_bytes()

    def diagnostic(self) -> str:
        return "protected-local-file references=" + ",".join(sorted(self._references))
