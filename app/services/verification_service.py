"""Verification engine.

Independently recomputes the evidence fingerprint from stored evidence and
compares it against the value recorded on-chain. This is what proves integrity
and detects tampering — never a fabricated result.

    stored evidence -> canonicalize -> SHA-256 (current)
    on-chain record  -> fingerprint (blockchain)
    compare -> VERIFIED | TAMPERED | NOT_VERIFIED
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.services.blockchain_service import get_blockchain_service
from app.utils.canonicalization import canonical_json, fingerprint
from app.utils.hashing import short_hash

log = get_logger("faceproof.verify")

STATUS_VERIFIED = "VERIFIED"
STATUS_TAMPERED = "TAMPERED"
STATUS_NOT_VERIFIED = "NOT_VERIFIED"


@dataclass
class VerificationResult:
    verified: bool
    status: str
    current_hash: str
    blockchain_hash: Optional[str]
    match: bool
    onchain_verified: Optional[bool]
    verified_at: str
    integrity_percent: int
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verified": self.verified,
            "status": self.status,
            "current_hash": self.current_hash,
            "blockchain_hash": self.blockchain_hash,
            "match": self.match,
            "onchain_verified": self.onchain_verified,
            "verified_at": self.verified_at,
            "integrity_percent": self.integrity_percent,
            "detail": self.detail,
        }


def verify(evidence: Dict[str, Any], record_id: Optional[int]) -> VerificationResult:
    """Recompute the fingerprint from `evidence` and compare with the chain."""
    now = datetime.now(timezone.utc).isoformat()
    current = fingerprint(evidence)

    if record_id is None:
        log.info("[VERIFY] result=NOT_VERIFIED (no on-chain record)")
        return VerificationResult(
            verified=False,
            status=STATUS_NOT_VERIFIED,
            current_hash=current,
            blockchain_hash=None,
            match=False,
            onchain_verified=None,
            verified_at=now,
            integrity_percent=0,
            detail="No blockchain record to verify against.",
        )

    chain = get_blockchain_service()
    try:
        record = chain.get_record(record_id)
        onchain_verified = chain.verify_onchain(record_id, current)
    except Exception as exc:  # noqa: BLE001
        log.error("[VERIFY] chain read failed: %s", exc)
        return VerificationResult(
            verified=False,
            status=STATUS_NOT_VERIFIED,
            current_hash=current,
            blockchain_hash=None,
            match=False,
            onchain_verified=None,
            verified_at=now,
            integrity_percent=0,
            detail=f"Unable to independently verify blockchain record: {exc}",
        )

    match = current == record.fingerprint
    if match and onchain_verified:
        status, verified, integrity, detail = (
            STATUS_VERIFIED, True, 100,
            "Recomputed fingerprint matches the on-chain record. Integrity valid.",
        )
    else:
        status, verified, integrity, detail = (
            STATUS_TAMPERED, False, 0,
            "Current fingerprint does not match the blockchain fingerprint. "
            "The evidence has changed since it was registered.",
        )
    log.info("[VERIFY] result=%s", status)
    return VerificationResult(
        verified=verified,
        status=status,
        current_hash=current,
        blockchain_hash=record.fingerprint,
        match=match,
        onchain_verified=onchain_verified,
        verified_at=now,
        integrity_percent=integrity,
        detail=detail,
    )


def canonical_of(evidence: Dict[str, Any]) -> str:
    return canonical_json(evidence)


def short(h: str) -> str:
    return short_hash(h)
