"""Pipeline orchestration — the individual stages and the full end-to-end run.

Each stage mutates a ScanState (runtime) and, where appropriate, persists a
durable summary to the database. Routes are thin wrappers over these functions;
the /api/pipeline endpoint chains them all together.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import ALLOWED_EXTENSIONS, sniff_image_mime
from app.db import SessionLocal
from app.models import BlockchainRecord, PipelineEvent, Scan
from app.services import fingerprint_service, firebase_store, verification_service
from app.services.blockchain_service import get_blockchain_service
from app.services.face_service import get_face_service
from app.services.search_service import run_search
from app.store import ScanState
from app.utils.hashing import sha256_text, short_hash
from app.utils.image_utils import InvalidImageError, image_dimensions, load_rgb_array

log = get_logger("faceproof.pipeline")


class PipelineError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


# --------------------------------------------------------------------------- #
# Stage 1 — upload
# --------------------------------------------------------------------------- #
def save_upload(state: ScanState, filename: str, data: bytes) -> None:
    if len(data) > settings.max_upload_bytes:
        raise PipelineError("file_too_large", f"File exceeds {settings.max_upload_size_mb} MB limit", 413)
    ext = os.path.splitext(filename or "")[1].lower()
    if ext and ext not in ALLOWED_EXTENSIONS:
        raise PipelineError("unsupported_file", f"Unsupported file type: {ext}", 415)
    if sniff_image_mime(data[:16]) is None:
        raise PipelineError("unsupported_file", "File is not a supported image (JPG/PNG/WebP)", 415)

    os.makedirs(settings.upload_dir, exist_ok=True)
    safe_ext = ext if ext in ALLOWED_EXTENSIONS else ".img"
    path = os.path.join(settings.upload_dir, f"{state.scan_id}{safe_ext}")
    with open(path, "wb") as fh:
        fh.write(data)
    state.image_path = path
    state.image_bytes = data
    state.status = "uploaded"
    state.emit("scan_started", {"scan_id": state.scan_id, "bytes": len(data)})
    log.info("[SCAN] scan_id=%s uploaded bytes=%d", state.scan_id, len(data))


# --------------------------------------------------------------------------- #
# Stage 2 — face detection + embedding
# --------------------------------------------------------------------------- #
def analyze_face(state: ScanState) -> Dict[str, Any]:
    if state.image_bytes is None:
        raise PipelineError("no_image", "No uploaded image for this scan", 400)
    state.emit("face_detection_started", {})
    try:
        rgb = load_rgb_array(state.image_bytes)
    except InvalidImageError as exc:
        raise PipelineError("invalid_image", str(exc), 422) from exc

    face_svc = get_face_service()
    try:
        analysis = face_svc.analyze(rgb)
    except Exception as exc:  # noqa: BLE001
        raise PipelineError(
            "face_service_unavailable",
            f"Face model unavailable: {exc}",
            503,
        ) from exc

    state.metrics["face_detection_ms"] = analysis.processing_time_ms

    if not analysis.face_detected:
        state.emit("face_detection_completed", {"face_detected": False})
        raise PipelineError(
            "no_face", "No detectable face found. Please upload a clearer image.", 422
        )

    warning = None
    if analysis.face_count > 1:
        warning = "multiple_faces"  # primary (largest) face is used; UI can refine
    primary = analysis.primary
    assert primary is not None
    w, h = primary.bbox[2], primary.bbox[3]
    if min(w, h) < settings.face_min_pixels:
        warning = warning or "low_resolution_face"

    state.embedding = primary.embedding
    face_payload = {
        "face_detected": True,
        "face_count": analysis.face_count,
        "confidence": round(primary.det_score, 4),
        "bbox": {"x": primary.bbox[0], "y": primary.bbox[1], "width": w, "height": h},
        "embedding_dimension": primary.embedding_dim,
        "embedding_id": primary.embedding_id,
        "model": analysis.model_name,
        "quality": analysis.quality_label,
        "processing_time_ms": analysis.processing_time_ms,
        "image_width": analysis.width,
        "image_height": analysis.height,
        "warning": warning,
    }
    state.face = face_payload
    state.status = "face_analyzed"
    state.emit("face_detection_completed", {"face_detected": True, "count": analysis.face_count})
    state.emit("embedding_generated", {"embedding_id": primary.embedding_id, "dim": primary.embedding_dim})
    _persist_scan(state)
    return face_payload


# --------------------------------------------------------------------------- #
# Stage 3 — search + candidate matching
# --------------------------------------------------------------------------- #
async def do_search(state: ScanState, query: Optional[str]) -> Dict[str, Any]:
    if state.embedding is None:
        raise PipelineError("no_embedding", "Run face analysis before searching", 400)
    state.query = query or state.query

    outcome = await run_search(
        input_embedding=state.embedding,
        image_path=state.image_path or "",
        query=state.query,
        emit=lambda ev, detail: state.emit(ev, detail),
    )

    candidates_out = []
    state.candidate_bytes.clear()
    for idx, cand in enumerate(outcome.candidates):
        pub = cand.to_public_dict()
        pub["id"] = idx
        candidates_out.append(pub)
        if cand.image_bytes is not None:
            state.candidate_bytes[idx] = cand.image_bytes

    best_id = None
    if outcome.best is not None:
        best_id = outcome.candidates.index(outcome.best)

    state.candidates = candidates_out
    state.search = {
        "provider": outcome.provider,
        "genuine": outcome.genuine,
        "results_found": outcome.results_found,
        "threshold": outcome.threshold,
        "potential_match": outcome.potential_match,
        "best_candidate_id": best_id,
        "search_time_ms": outcome.search_time_ms,
        "status": "completed",
    }
    state.metrics["search_ms"] = outcome.search_time_ms
    state.status = "searched"
    _persist_scan(state)
    return state.search


# --------------------------------------------------------------------------- #
# Stage 4 — select evidence
# --------------------------------------------------------------------------- #
def select_match(state: ScanState, result_id: int) -> Dict[str, Any]:
    if not state.candidates:
        raise PipelineError("no_results", "No search results to select from", 400)
    if result_id < 0 or result_id >= len(state.candidates):
        raise PipelineError("bad_result_id", f"result_id {result_id} out of range", 400)
    cand = state.candidates[result_id]

    media_sha = None
    img = state.candidate_bytes.get(result_id)
    if img is not None:
        media_sha = fingerprint_service.compute_media_hash(img, None)
    state.selected = cand
    state.selected_media_sha256 = media_sha
    state.status = "match_selected"
    sim = cand.get("similarity")
    threshold = (state.search or {}).get("threshold", settings.face_match_threshold)
    return {
        "status": "potential_match" if (sim is not None and sim >= threshold) else "below_threshold",
        "similarity": sim,
        "threshold": threshold,
        "source_url": cand.get("url"),
        "platform": cand.get("platform"),
    }


# --------------------------------------------------------------------------- #
# Stage 5 — fingerprint
# --------------------------------------------------------------------------- #
def make_fingerprint(state: ScanState) -> Dict[str, Any]:
    if state.selected is None:
        raise PipelineError("no_selection", "Select a matching result before fingerprinting", 400)
    cand = state.selected
    fp = fingerprint_service.generate(
        source_url=cand.get("url", ""),
        platform=cand.get("platform", ""),
        title=cand.get("title"),
        caption=cand.get("description"),
        author=cand.get("author"),
        published_at=cand.get("published_at"),
        media_sha256=state.selected_media_sha256,
    )
    state.fingerprint = {
        "algorithm": fp.algorithm,
        "fingerprint": fp.fingerprint,
        "short": fp.short,
        "canonical_json": fp.canonical_json,
        "media_sha256": fp.media_sha256,
    }
    state.evidence = fp.evidence
    state.status = "fingerprinted"
    state.emit("fingerprint_generated", {"fingerprint": fp.short})
    _persist_scan(state)
    return state.fingerprint


# --------------------------------------------------------------------------- #
# Stage 6 — blockchain registration
# --------------------------------------------------------------------------- #
def register_chain(state: ScanState) -> Dict[str, Any]:
    if state.fingerprint is None:
        raise PipelineError("no_fingerprint", "Generate a fingerprint before registering", 400)
    chain = get_blockchain_service()
    fp_hex = state.fingerprint["fingerprint"]
    source_url = (state.selected or {}).get("url", "")
    content_id = sha256_text(source_url or state.scan_id)
    platform = (state.selected or {}).get("platform", "") or "Public Web"

    state.emit("blockchain_transaction_submitted", {"fingerprint": short_hash(fp_hex)})
    result = chain.register(
        fingerprint_hex=fp_hex,
        content_id_hex=content_id,
        platform=platform[:120],
        source_url=source_url,
    )
    tx_url = chain.explorer_tx_url(result.transaction_hash) if result.transaction_hash else None
    payload = {
        "success": result.success,
        "status": "confirmed" if result.success else "failed",
        "record_id": result.record_id,
        "transaction_hash": result.transaction_hash,
        "transaction_url": tx_url,
        "block_number": result.block_number,
        "network_chain_id": settings.blockchain_chain_id,
        "fingerprint": fp_hex,
        "timestamp": result.timestamp,
        "gas_used": result.gas_used,
        "error": result.error,
    }
    state.blockchain = payload
    state.record_id = result.record_id
    state.metrics["blockchain_ms"] = state.metrics.get("blockchain_ms", 0)
    if result.success:
        state.status = "registered"
        state.emit("blockchain_confirmed", {"record_id": result.record_id, "block": result.block_number})
    else:
        state.emit("blockchain_failed", {"error": result.error})
    _persist_record(state, payload)
    return payload


# --------------------------------------------------------------------------- #
# Stage 7 — verification (with optional tamper simulation)
# --------------------------------------------------------------------------- #
def do_verify(state: ScanState, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if state.evidence is None:
        raise PipelineError("no_evidence", "No evidence to verify", 400)
    state.emit("verification_started", {})
    evidence = dict(state.evidence)
    if overrides:
        for k in ("caption", "title", "author"):
            if overrides.get(k) is not None:
                evidence[k] = overrides[k]
    result = verification_service.verify(evidence, state.record_id)
    payload = result.to_dict()
    state.verification = payload
    state.status = "verified"
    state.emit("verification_completed", {"status": result.status})
    _update_record_verification(state, result.status)
    return payload


# --------------------------------------------------------------------------- #
# Cleanup
# --------------------------------------------------------------------------- #
def cleanup_upload(state: ScanState) -> None:
    if settings.delete_uploads_after_session and state.image_path and os.path.exists(state.image_path):
        try:
            os.remove(state.image_path)
            log.info("[SCAN] scan_id=%s upload deleted", state.scan_id)
        except OSError:
            pass
    state.image_bytes = None


# --------------------------------------------------------------------------- #
# Persistence helpers
# --------------------------------------------------------------------------- #
def _persist_scan(state: ScanState) -> None:
    db = SessionLocal()
    try:
        row = db.get(Scan, state.scan_id)
        if row is None:
            row = Scan(id=state.scan_id)
            db.add(row)
        row.status = state.status
        if state.face:
            row.face_detected = state.face["face_detected"]
            row.face_count = state.face["face_count"]
            row.face_confidence = state.face["confidence"]
            row.embedding_id = state.face["embedding_id"]
            row.embedding_dimension = state.face["embedding_dimension"]
            row.quality_label = state.face["quality"]
        if state.selected:
            row.selected_url = state.selected.get("url", "")
            row.selected_platform = state.selected.get("platform", "") or ""
            row.similarity = state.selected.get("similarity") or 0.0
        if state.fingerprint:
            row.fingerprint = state.fingerprint["fingerprint"]
        row.total_ms = sum(state.metrics.values())
        # Persist newest events not yet stored.
        stored = db.query(PipelineEvent).filter_by(scan_id=state.scan_id).count()
        for ev in state.events[stored:]:
            db.add(PipelineEvent(scan_id=state.scan_id, event=ev["event"], detail=str(ev["detail"])))
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        log.warning("persist scan failed: %s", exc)
    finally:
        db.close()


def _persist_record(state: ScanState, payload: Dict[str, Any]) -> None:
    db = SessionLocal()
    try:
        rec = db.query(BlockchainRecord).filter_by(scan_id=state.scan_id).one_or_none()
        if rec is None:
            rec = BlockchainRecord(scan_id=state.scan_id)
            db.add(rec)
        rec.record_id = payload.get("record_id")
        rec.fingerprint = payload.get("fingerprint", "")
        rec.transaction_hash = payload.get("transaction_hash") or ""
        rec.block_number = payload.get("block_number")
        rec.network_chain_id = payload.get("network_chain_id", 0)
        rec.platform = (state.selected or {}).get("platform", "") or ""
        rec.status = payload.get("status", "pending")
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        log.warning("persist record failed: %s", exc)
    finally:
        db.close()


def _update_record_verification(state: ScanState, status: str) -> None:
    db = SessionLocal()
    try:
        rec = db.query(BlockchainRecord).filter_by(scan_id=state.scan_id).one_or_none()
        if rec is not None:
            rec.verification_status = status
            db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        log.warning("update verification failed: %s", exc)
    finally:
        db.close()

    # Durable persistence to Firebase (survives serverless restarts) when enabled.
    if firebase_store.enabled():
        from datetime import datetime, timezone

        bc = state.blockchain or {}
        firebase_store.save_record(
            {
                "record_id": bc.get("record_id"),
                "scan_id": state.scan_id,
                "fingerprint": bc.get("fingerprint", ""),
                "transaction_hash": bc.get("transaction_hash") or "",
                "block_number": bc.get("block_number"),
                "network_chain_id": bc.get("network_chain_id"),
                "platform": (state.selected or {}).get("platform", "") or "",
                "status": bc.get("status", ""),
                "verification_status": status,
                "similarity": (state.selected or {}).get("similarity"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
