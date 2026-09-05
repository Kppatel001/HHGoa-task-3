from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class VerificationOut(BaseModel):
    scan_id: str
    verified: bool
    status: str  # VERIFIED | TAMPERED | NOT_VERIFIED
    current_hash: str
    blockchain_hash: Optional[str] = None
    match: bool
    onchain_verified: Optional[bool] = None
    integrity_percent: int
    verified_at: str
    detail: str


class TamperCheckRequest(BaseModel):
    # Optional overrides that simulate tampering with the evidence, to prove the
    # verification actually detects changes. If omitted, verifies the original.
    caption: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None


class PipelineEventOut(BaseModel):
    event: str
    detail: Dict[str, Any] = {}
    ts: str


class PipelineOut(BaseModel):
    scan_id: str
    face: Optional[Dict[str, Any]] = None
    search: Optional[Dict[str, Any]] = None
    match: Optional[Dict[str, Any]] = None
    fingerprint: Optional[Dict[str, Any]] = None
    blockchain: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    metrics: Dict[str, int] = {}
    events: List[PipelineEventOut] = []
