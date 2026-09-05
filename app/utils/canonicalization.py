"""Deterministic canonicalization of evidence prior to hashing.

Two independent parties hashing the *same* evidence must produce the *same*
SHA-256. To guarantee that, we serialize evidence into a canonical JSON form:
    * keys sorted
    * no insignificant whitespace
    * UTF-8, ensure_ascii disabled (stable unicode)
    * only the whitelisted evidence fields, in a fixed schema

Changing any field (e.g. tampering with the caption) changes the fingerprint,
which is exactly what the on-chain verification detects.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from app.utils.hashing import sha256_text

# The exact, ordered set of fields that make up a piece of evidence.
EVIDENCE_FIELDS = (
    "source_url",
    "platform",
    "title",
    "caption",
    "author",
    "published_at",
    "media_sha256",
)


def build_evidence(
    *,
    source_url: str,
    platform: str,
    title: str | None,
    caption: str | None,
    author: str | None,
    published_at: str | None,
    media_sha256: str | None,
) -> Dict[str, Any]:
    """Assemble the evidence dict with a stable schema (None -> "")."""
    return {
        "source_url": source_url or "",
        "platform": platform or "",
        "title": title or "",
        "caption": caption or "",
        "author": author or "",
        "published_at": published_at or "",
        "media_sha256": media_sha256 or "",
    }


def canonical_json(evidence: Dict[str, Any]) -> str:
    """Return the canonical JSON string for the whitelisted evidence fields."""
    normalized = {k: str(evidence.get(k, "") or "") for k in EVIDENCE_FIELDS}
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def fingerprint(evidence: Dict[str, Any]) -> str:
    """SHA-256 of the canonical evidence representation (hex, no 0x)."""
    return sha256_text(canonical_json(evidence))
