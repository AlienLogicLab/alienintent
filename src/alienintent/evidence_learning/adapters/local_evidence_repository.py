"""Durable external content-addressed objects, installed atomically without overwrite."""
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import tempfile

from alienintent.evidence_learning.domain.records import Record, canonical_bytes, record_document, record_from_document, record_ref
from alienintent.evidence_learning.domain.refs import EvidenceHold, Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.execution_coordination.ports.operational_store import StoreUnavailable


class LocalEvidenceRepository(EvidenceRepository):
    def __init__(self, root: Path, project: str, profile: str, *, max_bytes: int = 10 * 1024 * 1024) -> None:
        self.root, self.project, self.profile, self.max_bytes = Path(root), project, profile, max_bytes
        if type(max_bytes) is not int or max_bytes <= 0:
            raise EvidenceHold("INPUT_LIMIT_HOLD")
        try:
            if self.root.is_symlink() or (self.root / "objects").is_symlink():
                raise EvidenceHold("UNSAFE_ROOT")
            # The operator supplies an existing durable parent. Recursive mkdir
            # would need to fsync every new ancestor before any pointer commit.
            self.root.mkdir(exist_ok=True, mode=0o700)
            self.objects = self.root / "objects"
            self.objects.mkdir(exist_ok=True, mode=0o700)
            if self.root.stat().st_mode & 0o077 or self.objects.stat().st_mode & 0o077:
                raise EvidenceHold("UNSAFE_ROOT", required_action="use a private external evidence directory")
            self._sync_directory(self.root)
            self._sync_directory(self.root.parent)
        except OSError as error:
            raise StoreUnavailable("evidence directory unavailable") from error

    @staticmethod
    def _sync_directory(path: Path) -> None:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def _path(self, ref: Ref) -> Path:
        if (ref.project, ref.profile) != (self.project, self.profile):
            raise EvidenceHold("REF_SCOPE", (ref,))
        name = ref.revision_digest.removeprefix("sha256:")
        if ref.locator != "objects/" + name:
            raise EvidenceHold("INVALID_LOCATOR", (ref,))
        return self.objects / name

    def put(self, record: Record) -> Ref:
        body = canonical_bytes(record_document(record))
        if len(body) > self.max_bytes:
            raise EvidenceHold("INPUT_LIMIT_HOLD")
        ref = record_ref(record)
        target = self._path(ref)
        temporary = None
        try:
            fd, temporary = tempfile.mkstemp(prefix=".install-", dir=self.objects)
            with os.fdopen(fd, "wb") as stream:
                stream.write(body)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, target)
            except FileExistsError:
                pass
            self._sync_directory(self.objects)
            self.get(ref, frozenset({record.header.access_label}))
            return ref
        except OSError as error:
            raise StoreUnavailable("immutable evidence write failed") from error
        finally:
            if temporary is not None:
                try:
                    os.unlink(temporary)
                except FileNotFoundError:
                    pass

    def get(self, ref: Ref, access_scope: frozenset[str]) -> Record:
        path = self._path(ref)
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise EvidenceHold("INVALID_OBJECT", (ref,))
                body = stream.read(self.max_bytes + 1)
        except FileNotFoundError as error:
            raise EvidenceHold("MISSING_OBJECT", (ref,)) from error
        except OSError as error:
            if path.is_symlink():
                raise EvidenceHold("UNSAFE_OBJECT", (ref,)) from error
            raise StoreUnavailable("immutable evidence read failed") from error
        if len(body) > self.max_bytes:
            raise EvidenceHold("INPUT_LIMIT_HOLD", (ref,))
        if "sha256:" + sha256(body).hexdigest() != ref.revision_digest:
            raise EvidenceHold("HASH_MISMATCH", (ref,))
        try:
            record = record_from_document(json.loads(body))
        except (ValueError, UnicodeError) as error:
            raise EvidenceHold("INVALID_JSON", (ref,)) from error
        if record_ref(record) != ref:
            raise EvidenceHold("REF_IDENTITY", (ref,))
        if record.header.access_label not in access_scope:
            raise EvidenceHold("ACCESS_DENIED", (ref,))
        return record
