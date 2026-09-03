"""Optional Firebase Realtime Database persistence (durable record/history store).

Uses the RTDB REST API over httpx — no firebase-admin / grpc — so it stays light
enough for serverless (Vercel) and works anywhere. Enabled only when
FIREBASE_DB_URL is set; otherwise the app falls back to local SQLite.

RTDB layout:
    /records/<pushId> = { record_id, scan_id, fingerprint, transaction_hash,
                          block_number, network_chain_id, platform, status,
                          verification_status, similarity, created_at }
"""
from __future__ import annotations

from typing import Any, Dict, List

import httpx

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("faceproof.firebase")


def enabled() -> bool:
    return settings.firebase_enabled


def _url(path: str) -> str:
    base = settings.firebase_db_url.rstrip("/")
    url = f"{base}/{path}.json"
    if settings.firebase_db_secret:
        url += f"?auth={settings.firebase_db_secret}"
    return url


def save_record(record: Dict[str, Any]) -> bool:
    """Append a verification record to Firebase. Returns True on success."""
    if not enabled():
        return False
    try:
        with httpx.Client(timeout=10.0) as c:
            r = c.post(_url("records"), json=record)
        r.raise_for_status()
        log.info("[FIREBASE] record saved id=%s", record.get("record_id"))
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("[FIREBASE] save failed: %s", exc)
        return False


def list_records() -> List[Dict[str, Any]]:
    """Return all stored records, newest first. Empty list on error/none."""
    if not enabled():
        return []
    try:
        with httpx.Client(timeout=10.0) as c:
            r = c.get(_url("records"))
        r.raise_for_status()
        data = r.json() or {}
        recs = list(data.values()) if isinstance(data, dict) else []
        recs.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        return recs
    except Exception as exc:  # noqa: BLE001
        log.warning("[FIREBASE] list failed: %s", exc)
        return []


def health() -> Dict[str, Any]:
    """Quick connectivity check for the status endpoint."""
    if not enabled():
        return {"enabled": False}
    try:
        with httpx.Client(timeout=8.0) as c:
            r = c.get(_url(".info/serverTimeOffset"))
        return {"enabled": True, "connected": r.status_code == 200}
    except Exception as exc:  # noqa: BLE001
        return {"enabled": True, "connected": False, "error": str(exc)}
