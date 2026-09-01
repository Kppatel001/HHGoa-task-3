from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import get_state
from app.services import pipeline
from app.services.pipeline import PipelineError
from app.schemas.verification import TamperCheckRequest

router = APIRouter(prefix="/scan", tags=["verify"])


@router.post("/{scan_id}/verify")
def verify(scan_id: str, body: TamperCheckRequest | None = None):
    """Recalculate the fingerprint and compare against the blockchain record.

    Pass caption/title/author overrides to simulate tampering and prove the
    verification actually detects a changed fingerprint (-> TAMPERED).
    """
    state = get_state(scan_id)
    overrides = body.model_dump(exclude_none=True) if body else None
    try:
        result = pipeline.do_verify(state, overrides)
    except PipelineError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})
    return {"scan_id": scan_id, **result}
