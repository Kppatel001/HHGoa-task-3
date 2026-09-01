from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import get_state
from app.core.config import settings
from app.db import SessionLocal
from app.models import BlockchainRecord
from app.services import pipeline
from app.services.blockchain_service import get_blockchain_service
from app.services.pipeline import PipelineError

router = APIRouter(tags=["blockchain"])


@router.post("/scan/{scan_id}/fingerprint")
def fingerprint(scan_id: str):
    state = get_state(scan_id)
    try:
        fp = pipeline.make_fingerprint(state)
    except PipelineError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})
    return {"scan_id": scan_id, **fp}


@router.post("/scan/{scan_id}/blockchain")
def register(scan_id: str):
    state = get_state(scan_id)
    try:
        result = pipeline.register_chain(state)
    except PipelineError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})
    return {"scan_id": scan_id, **result}


@router.get("/blockchain/status")
def blockchain_status():
    return get_blockchain_service().status()


@router.get("/blockchain/records")
def list_records():
    chain = get_blockchain_service()
    db = SessionLocal()
    try:
        rows = db.query(BlockchainRecord).order_by(BlockchainRecord.created_at.desc()).all()
        out = []
        for r in rows:
            tx_url = chain.explorer_tx_url(r.transaction_hash) if r.transaction_hash else None
            out.append(
                {
                    "record_id": r.record_id,
                    "scan_id": r.scan_id,
                    "fingerprint": r.fingerprint,
                    "transaction_hash": r.transaction_hash,
                    "transaction_url": tx_url,
                    "block_number": r.block_number,
                    "network_chain_id": r.network_chain_id,
                    "platform": r.platform,
                    "status": r.status,
                    "verification_status": r.verification_status,
                    "created_at": r.created_at.isoformat(),
                }
            )
        return {"records": out, "explorer": settings.block_explorer_url or None}
    finally:
        db.close()
