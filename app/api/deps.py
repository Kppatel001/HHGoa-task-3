from __future__ import annotations

from fastapi import HTTPException

from app.store import ScanState, store


def get_state(scan_id: str) -> ScanState:
    state = store.get(scan_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Unknown scan_id: {scan_id}")
    return state


def build_pipeline_response(state: ScanState) -> dict:
    match = None
    if state.selected is not None:
        threshold = (state.search or {}).get("threshold")
        sim = state.selected.get("similarity")
        match = {
            "status": "potential_match"
            if (sim is not None and threshold is not None and sim >= threshold)
            else "below_threshold",
            "similarity": sim,
            "source_url": state.selected.get("url"),
            "platform": state.selected.get("platform"),
        }
    # Include candidate list in the search block so the UI can render result
    # cards from a single /api/pipeline response (stateless / serverless-safe).
    search = None
    if state.search is not None:
        search = {**state.search, "candidates": state.candidates}
    return {
        "scan_id": state.scan_id,
        "status": state.status,
        "face": state.face,
        "search": search,
        "match": match,
        "fingerprint": state.fingerprint,
        "blockchain": state.blockchain,
        "verification": state.verification,
        "metrics": state.metrics,
        "events": state.events,
    }
