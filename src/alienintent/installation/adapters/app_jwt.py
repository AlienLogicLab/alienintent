"""RS256 App assertion from a referenced private key, using the standard library only.

The key material arrives as bytes from the `SecretProvider` and never leaves
this module: no path, no PEM body and no signature input is logged or returned.
"""

from __future__ import annotations

from base64 import b64decode, urlsafe_b64encode
from hashlib import sha256
import json

from alienintent.installation.domain.app_credentials import CredentialRejected


_SEQUENCE, _INTEGER, _OCTET_STRING = 0x30, 0x02, 0x04
# EMSA-PKCS1-v1_5 DigestInfo prefix for SHA-256 (RFC 8017 §9.2).
_SHA256_DIGEST_INFO = bytes.fromhex("3031300d060960864801650304020105000420")


def app_assertion(application_id: int, private_key: bytes, issued_at: float, lifetime_seconds: float = 540.0) -> str:
    """A short-lived RS256 assertion proving possession of the App private key."""
    modulus, private_exponent = _rsa_private_numbers(private_key)
    header = _segment(_compact({"alg": "RS256", "typ": "JWT"}))
    claims = _segment(_compact({"iat": int(issued_at) - 60, "exp": int(issued_at) + int(lifetime_seconds), "iss": str(application_id)}))
    signing_input = f"{header}.{claims}".encode("ascii")
    signature = _segment(_sign(signing_input, modulus, private_exponent))
    return f"{header}.{claims}.{signature}"


def _compact(claims: dict[str, object]) -> bytes:
    return json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _segment(raw: bytes) -> str:
    return urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _sign(signing_input: bytes, modulus: int, private_exponent: int) -> bytes:
    size = (modulus.bit_length() + 7) // 8
    digest_info = _SHA256_DIGEST_INFO + sha256(signing_input).digest()
    if size < len(digest_info) + 11:
        raise CredentialRejected("private key is too small to sign an App assertion")
    encoded = b"\x00\x01" + b"\xff" * (size - len(digest_info) - 3) + b"\x00" + digest_info
    return pow(int.from_bytes(encoded, "big"), private_exponent, modulus).to_bytes(size, "big")


def _rsa_private_numbers(private_key: bytes) -> tuple[int, int]:
    """Read the RSA modulus and private exponent from a PKCS#1 or PKCS#8 PEM."""
    return _from_der(_der(private_key))


def _der(private_key: bytes) -> bytes:
    try:
        lines = [line.strip() for line in private_key.decode("ascii").splitlines()]
    except UnicodeDecodeError as error:
        raise CredentialRejected("private key is not PEM encoded") from error
    body = "".join(line for line in lines if line and not line.startswith("-----"))
    if not body:
        raise CredentialRejected("private key is not PEM encoded")
    try:
        return b64decode(body, validate=True)
    except ValueError as error:
        raise CredentialRejected("private key is not PEM encoded") from error


def _from_der(der: bytes) -> tuple[int, int]:
    tag, sequence, _ = _read(der, 0)
    if tag != _SEQUENCE:
        raise CredentialRejected("private key is not a DER sequence")
    offset, integers = 0, []
    while offset < len(sequence):
        tag, value, offset = _read(sequence, offset)
        if tag == _OCTET_STRING:
            return _from_der(value)
        if tag == _INTEGER:
            integers.append(int.from_bytes(value, "big"))
            if len(integers) == 4:
                return integers[1], integers[3]
    raise CredentialRejected("private key carries no RSA modulus and private exponent")


def _read(data: bytes, offset: int) -> tuple[int, bytes, int]:
    if offset + 2 > len(data):
        raise CredentialRejected("private key DER is truncated")
    tag, length, offset = data[offset], data[offset + 1], offset + 2
    if length & 0x80:
        count = length & 0x7F
        length = int.from_bytes(data[offset:offset + count], "big")
        offset += count
    if offset + length > len(data):
        raise CredentialRejected("private key DER is truncated")
    return tag, data[offset:offset + length], offset + length
