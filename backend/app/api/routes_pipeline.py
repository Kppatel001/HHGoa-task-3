from __future__ import annotations

import time
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.deps import build_pipeline_response
from app.services import pipeline
from app.services.pipeline import PipelineError
from app.services.providers.base import SearchUnavailableError
from app.store import store

router = APIRouter(tags=["pipeline"])


@router.post("/pipeline")
async def run_pipeline(
    file: UploadFile = File(...),
    query: Optional[str] = Form(default=None),
    simulate_tamper: bool = Form(default=False),
):
    """Run the full pipeline end-to-end and return the complete state.

    upload -> face -> embedding -> search -> candidate matching -> select best
    -> fingerprint -> blockchain -> verify. Each stage is genuine; failures are
    reported honestly rather than faked.
    """
    # Business outcomes (no face, no match, search unavailable) are returned as
    # 200 with a `notice` so the browser console stays clean — they're expected
    # results, not server errors. Only genuinely invalid requests use 4xx.
    SOFT = {"no_face", "no_match", "search_unavailable", "invalid_image"}

    started = time.perf_counter()
    data = await file.read()
    scan_id = f"scan_{uuid.uuid4().hex[:16]}"
    state = store.create(scan_id, query=query)

    notice = None
    try:
        pipeline.save_upload(state, file.filename or "upload", data)
        pipeline.analyze_face(state)
        await pipeline.do_search(state, query)

        best_id = (state.search or {}).get("best_candidate_id")
        potential = (state.search or {}).get("potential_match")
        if best_id is None or not potential:
            state.emit("pipeline_failed", {"reason": "no_match"})
            raise PipelineError("no_match", "No sufficiently similar public result found.", 422)

        pipeline.select_match(state, best_id)
        pipeline.make_fingerprint(state)
        pipeline.register_chain(state)
        overrides = {"caption": "TAMPERED — content modified after registration"} if simulate_tamper else None
        pipeline.do_verify(state, overrides)
    except SearchUnavailableError as exc:
        state.emit("pipeline_failed", {"reason": "search_unavailable"})
        notice = {"code": "search_unavailable", "message": str(exc)}
    except PipelineError as exc:
        if exc.code in SOFT:
            notice = {"code": exc.code, "message": exc.message}
        else:
            state.done = True
            raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})
    finally:
        state.metrics["total_ms"] = int((time.perf_counter() - started) * 1000)
        pipeline.cleanup_upload(state)

    state.done = True
    resp = build_pipeline_response(state)
    if notice:
        resp["notice"] = notice
    return resp
