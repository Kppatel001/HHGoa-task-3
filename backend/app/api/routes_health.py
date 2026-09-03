from __future__ import annotations

import time

from fastapi import APIRouter

from app.core.config import settings
from app.services.blockchain_service import get_blockchain_service
from app.services.face_service import get_face_service

router = APIRouter(tags=["health"])

_START = time.time()


def _firebase_component():
    from app.services import firebase_store

    if not firebase_store.enabled():
        return {"status": "sqlite", "store": "sqlite (local/ephemeral)"}
    h = firebase_store.health()
    return {
        "status": "online" if h.get("connected") else "offline",
        "store": "firebase-rtdb",
    }


@router.get("/health")
def health():
    face = get_face_service()
    chain = get_blockchain_service()
    chain_status = chain.status()
    return {
        "api": "online",
        "face_service": "online" if face.ready else "cold",
        "search_service": "online",
        "search_provider": settings.search_provider,
        "blockchain": "online" if chain_status.get("connected") else "offline",
        "uptime_s": int(time.time() - _START),
    }


@router.get("/status")
def system_status():
    """Detailed component status + latency snapshot for the System Status page."""
    face = get_face_service()
    chain = get_blockchain_service()
    chain_status = chain.status()
    return {
        "components": {
            "face_recognition": {
                "status": "online" if face.ready else "cold",
                "model": settings.face_model,
                "error": face.load_error,
            },
            "search_service": {
                "status": "online",
                "provider": settings.search_provider,
                "genuine": settings.search_provider.lower() != "demo",
            },
            "blockchain_rpc": {
                "status": "online" if chain_status.get("connected") else "offline",
                "rpc_url": chain_status.get("rpc_url"),
                "latest_block": chain_status.get("latest_block"),
            },
            "smart_contract": {
                "status": "online" if chain_status.get("contract_address") else "offline",
                "address": chain_status.get("contract_address"),
                "chain_id": chain_status.get("chain_id"),
            },
            "api": {"status": "online"},
            "database": _firebase_component(),
        },
        "config": {
            "face_match_threshold": settings.face_match_threshold,
            "explorer_url": settings.block_explorer_url or None,
            "demo_mode": settings.is_demo_search,
        },
    }
