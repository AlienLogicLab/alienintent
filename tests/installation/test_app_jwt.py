"""Proof that the standard-library App assertion is a real RS256 signature.

The signature is verified by recomputing PKCS#1 v1.5 verification from the
public numbers, so a signer that merely produced well-formed base64 fails.
"""

from __future__ import annotations

from base64 import urlsafe_b64decode
from hashlib import sha256
import json

import pytest

from alienintent.installation.adapters.app_jwt import _rsa_private_numbers, app_assertion
from alienintent.installation.domain.app_credentials import CredentialRejected
from tests.support.disposable_rsa import disposable_private_key

_PUBLIC_EXPONENT = 65537
_SHA256_DIGEST_INFO = bytes.fromhex("3031300d060960864801650304020105000420")


def _decode(segment: str) -> bytes:
    return urlsafe_b64decode(segment + "=" * (-len(segment) % 4))


def test_assertion_carries_the_app_identity_and_a_bounded_lifetime() -> None:
    header, claims, _ = app_assertion(1000001, disposable_private_key(), 1758445000.0).split(".")

    assert json.loads(_decode(header)) == {"alg": "RS256", "typ": "JWT"}
    assert json.loads(_decode(claims)) == {"iat": 1758444940, "exp": 1758445540, "iss": "1000001"}


def test_signature_verifies_against_the_public_numbers_of_the_signing_key() -> None:
    """Removing the modular exponentiation must make this fail."""
    key = disposable_private_key()
    modulus, _ = _rsa_private_numbers(key)
    token = app_assertion(1000001, key, 1758445000.0)
    header, claims, signature = token.split(".")

    size = (modulus.bit_length() + 7) // 8
    recovered = pow(int.from_bytes(_decode(signature), "big"), _PUBLIC_EXPONENT, modulus).to_bytes(size, "big")
    digest_info = _SHA256_DIGEST_INFO + sha256(f"{header}.{claims}".encode("ascii")).digest()

    assert recovered == b"\x00\x01" + b"\xff" * (size - len(digest_info) - 3) + b"\x00" + digest_info


def test_a_tampered_claim_no_longer_verifies_under_the_same_signature() -> None:
    key = disposable_private_key()
    modulus, _ = _rsa_private_numbers(key)
    header, claims, signature = app_assertion(1000001, key, 1758445000.0).split(".")
    size = (modulus.bit_length() + 7) // 8
    recovered = pow(int.from_bytes(_decode(signature), "big"), _PUBLIC_EXPONENT, modulus).to_bytes(size, "big")

    forged = sha256(f"{header}.{claims}x".encode("ascii")).digest()
    assert not recovered.endswith(forged)


@pytest.mark.parametrize("material", [b"", b"not a pem at all", b"-----BEGIN RSA PRIVATE KEY-----\n!!!!\n-----END RSA PRIVATE KEY-----\n"])
def test_unusable_key_material_fails_closed_rather_than_signing_nothing(material: bytes) -> None:
    with pytest.raises(CredentialRejected):
        app_assertion(1000001, material, 0.0)
