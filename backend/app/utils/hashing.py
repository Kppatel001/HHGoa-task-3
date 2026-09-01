"""Cryptographic hashing primitives used across the evidence pipeline."""
from __future__ import annotations

import hashlib


def sha256_bytes(data: bytes) -> str:
    """SHA-256 of raw bytes, returned as lowercase hex (no 0x prefix)."""
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    """SHA-256 of UTF-8 encoded text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def to_bytes32(hex_digest: str) -> bytes:
    """Convert a 64-char hex SHA-256 digest into a 32-byte value for on-chain
    bytes32 storage."""
    clean = hex_digest[2:] if hex_digest.startswith("0x") else hex_digest
    if len(clean) != 64:
        raise ValueError(f"Expected 64 hex chars, got {len(clean)}")
    return bytes.fromhex(clean)


def short_hash(hex_digest: str, head: int = 6, tail: int = 4) -> str:
    """Human-friendly abbreviation, e.g. '9f73d3...a4b0'."""
    clean = hex_digest[2:] if hex_digest.startswith("0x") else hex_digest
    if len(clean) <= head + tail:
        return clean
    return f"{clean[:head]}...{clean[-tail:]}"
