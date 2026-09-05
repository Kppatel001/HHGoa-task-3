from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class FingerprintOut(BaseModel):
    scan_id: str
    algorithm: str
    fingerprint: str
    short: str
    canonical_json: str
    media_sha256: Optional[str] = None


class BlockchainOut(BaseModel):
    scan_id: str
    success: bool
    status: str
    record_id: Optional[int] = None
    transaction_hash: Optional[str] = None
    transaction_url: Optional[str] = None
    block_number: Optional[int] = None
    network_chain_id: int
    fingerprint: str
    timestamp: Optional[int] = None
    gas_used: Optional[int] = None
    error: Optional[str] = None


class BlockchainRecordOut(BaseModel):
    record_id: Optional[int]
    scan_id: str
    fingerprint: str
    transaction_hash: str
    transaction_url: Optional[str] = None
    block_number: Optional[int]
    network_chain_id: int
    platform: str
    status: str
    verification_status: str
    created_at: str
