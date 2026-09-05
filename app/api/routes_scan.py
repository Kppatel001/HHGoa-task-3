from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.api.deps import build_pipeline_response, get_state
from app.services import pipeline
from app.services.pipeline import PipelineError
from app.store import store

router = APIRouter(prefix="/scan", tags=["scan"])


def _handle(exc: PipelineError):
    raise HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})


@router.post("")
async def create_scan(file: UploadFile = File(...)):
    """Upload an image and create a scan session."""
    data = await file.read()
    scan_id = f"scan_{uuid.uuid4().hex[:16]}"
    state = store.create(scan_id)
    try:
        pipeline.save_upload(state, file.filename or "upload", data)
    except PipelineError as exc:
        _handle(exc)
    return {"scan_id": scan_id, "status": state.status}


@router.post("/{scan_id}/face")
def analyze_face(scan_id: str):
    state = get_state(scan_id)
    try:
        return pipeline.analyze_face(state)
    except PipelineError as exc:
        _handle(exc)


@router.get("/{scan_id}")
def get_scan(scan_id: str):
    state = get_state(scan_id)
    return build_pipeline_response(state)


@router.get("/{scan_id}/events")
async def scan_events(scan_id: str):
    """Server-Sent Events stream of pipeline progress for this scan."""
    state = get_state(scan_id)

    async def event_gen():
        # Replay already-emitted events first so late subscribers catch up.
        for ev in list(state.events):
            yield f"data: {json.dumps(ev)}\n\n"
        while not state.done:
            try:
                ev = await asyncio.wait_for(state._queue.get(), timeout=15.0)
                yield f"data: {json.dumps(ev)}\n\n"
                if ev["event"] in ("verification_completed", "pipeline_failed"):
                    break
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
