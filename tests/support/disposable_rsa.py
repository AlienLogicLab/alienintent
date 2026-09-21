"""A deterministic, disposable RSA key for signing-path tests.

Generated in-process from a fixed seed so no private key material is ever
committed to this repository. It authorizes nothing and is never presented to
GitHub.
"""

from __future__ import annotations

from base64 import b64encode
from functools import lru_cache
import random

_BITS = 1024


def _probably_prime(candidate: int, rounds: int, rng: random.Random) -> bool:
    for small in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if candidate % small == 0:
            return candidate == small
    exponent, remainder = 0, candidate - 1
    while remainder % 2 == 0:
        remainder //= 2
        exponent += 1
    for _ in range(rounds):
        witness = pow(rng.randrange(2, candidate - 1), remainder, candidate)
        if witness in (1, candidate - 1):
            continue
        for _ in range(exponent - 1):
            witness = pow(witness, 2, candidate)
            if witness == candidate - 1:
                break
        else:
            return False
    return True


def _prime(bits: int, rng: random.Random) -> int:
    while True:
        candidate = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
        if candidate % 65537 != 1 and _probably_prime(candidate, 24, rng):
            return candidate


def _der_integer(value: int) -> bytes:
    raw = value.to_bytes((value.bit_length() + 8) // 8, "big") or b"\x00"
    return b"\x02" + _der_length(len(raw)) + raw


def _der_length(length: int) -> bytes:
    if length < 0x80:
        return bytes([length])
    raw = length.to_bytes((length.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(raw)]) + raw


@lru_cache(maxsize=1)
def disposable_private_key() -> bytes:
    """A PKCS#1 `RSA PRIVATE KEY` PEM, identical on every run."""
    rng = random.Random(20260921)
    while True:
        p, q = _prime(_BITS // 2, rng), _prime(_BITS // 2, rng)
        if p == q:
            continue
        modulus, totient = p * q, (p - 1) * (q - 1)
        exponent = 65537
        if totient % exponent == 0:
            continue
        private_exponent = pow(exponent, -1, totient)
        break
    numbers = (0, modulus, exponent, private_exponent, p, q,
               private_exponent % (p - 1), private_exponent % (q - 1), pow(q, -1, p))
    body = b"".join(_der_integer(number) for number in numbers)
    der = b"\x30" + _der_length(len(body)) + body
    encoded = b64encode(der).decode("ascii")
    lines = "\n".join(encoded[index:index + 64] for index in range(0, len(encoded), 64))
    return f"-----BEGIN RSA PRIVATE KEY-----\n{lines}\n-----END RSA PRIVATE KEY-----\n".encode("ascii")
