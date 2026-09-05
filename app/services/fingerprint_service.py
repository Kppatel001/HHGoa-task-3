"""Evidence fingerprinting.

Turns a selected piece of discovered public content into a deterministic
SHA-256 fingerprint over a canonical representation of its metadata + media
hash. This is the value registered on-chain.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.utils.canonicalization import build_evidence, canonical_json, fingerprint
from app.utils.hashing import sha256_bytes, sha256_text, short_hash

log = get_logger("faceproof.fingerprint")


@dataclass
class FingerprintResult:
    algorithm: str
    fingerprint: str          # 64-char hex, no 0x
    canonical_json: str
    media_sha256: Optional[str]
    evidence: Dict[str, Any]

    @property
    def short(self) -> str:
        return short_hash(self.fingerprint)


def compute_media_hash(image_bytes: Optional[bytes], text: Optional[str]) -> Optional[str]:
    """Media hash for the discovered content.

    If an image is present, hash the raw bytes. Otherwise, for text-only
    content, hash the canonical text. Returns None if neither exists.
    """
    if image_bytes:
        return sha256_bytes(image_bytes)
    if text:
        return sha256_text(text.strip())
    return None


def generate(
    *,
    source_url: str,
    platform: str,
    title: Optional[str],
    caption: Optional[str],
    author: Optional[str],
    published_at: Optional[str],
    media_sha256: Optional[str],
) -> FingerprintResult:
    evidence = build_evidence(
        source_url=source_url,
        platform=platform,
        title=title,
        caption=caption,
        author=author,
        published_at=published_at,
        media_sha256=media_sha256,
    )
    canon = canonical_json(evidence)
    fp = fingerprint(evidence)
    log.info("[HASH] fingerprint=%s", short_hash(fp))
    return FingerprintResult(
        algorithm="SHA-256",
        fingerprint=fp,
        canonical_json=canon,
        media_sha256=media_sha256,
        evidence=evidence,
    )
