from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import get_state
from app.services import pipeline
from app.services.pipeline import PipelineError
from app.services.providers.base import SearchUnavailableError
from app.schemas.search import SearchRequest, SelectMatchRequest

router = APIRouter(prefix="/scan", tags=["search"])


@router.post("/{scan_id}/search")
async def search(scan_id: str, body: SearchRequest | None = None):
    state = get_state(scan_id)
    query = body.query if body else None
    try:
        summary = await pipeline.do_search(state, query)
    except SearchUnavailableError as exc:
        raise HTTPException(status_code=502, detail={"code": "search_unavailable", "message": str(exc)})
    except PipelineError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})
    return {
        "scan_id": scan_id,
        **summary,
        "candidates": state.candidates,
    }


@router.get("/{scan_id}/results")
def results(scan_id: str):
    state = get_state(scan_id)
    if state.search is None:
        raise HTTPException(status_code=409, detail={"code": "not_searched", "message": "Run search first"})
    return {
        "scan_id": scan_id,
        **state.search,
        "candidates": state.candidates,
    }


@router.post("/{scan_id}/match")
def select_match(scan_id: str, body: SelectMatchRequest):
    state = get_state(scan_id)
    try:
        return pipeline.select_match(state, body.result_id)
    except PipelineError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})
