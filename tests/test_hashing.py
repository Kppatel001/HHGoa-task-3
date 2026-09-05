import pytest

from app.utils.hashing import sha256_bytes, sha256_text, short_hash, to_bytes32


def test_sha256_known_vector():
    # SHA-256("") is a well-known constant.
    assert sha256_text("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_sha256_bytes_and_text_agree():
    assert sha256_bytes(b"hello") == sha256_text("hello")


def test_to_bytes32_roundtrip():
    digest = sha256_text("evidence")
    b = to_bytes32(digest)
    assert isinstance(b, bytes) and len(b) == 32
    assert b.hex() == digest


def test_to_bytes32_accepts_0x_prefix():
    digest = sha256_text("x")
    assert to_bytes32("0x" + digest) == to_bytes32(digest)


def test_to_bytes32_rejects_bad_length():
    with pytest.raises(ValueError):
        to_bytes32("abc")


def test_short_hash():
    assert short_hash("0123456789abcdef", 4, 4) == "0123...cdef"
