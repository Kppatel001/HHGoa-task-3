"""In-memory runtime state for active scans + an async event bus for SSE.

Transient per-scan state (uploaded image path, the in-process embedding, search
outcome, selected evidence, fingerprint, blockchain result) lives here for the
duration of a scan session. Durable summaries are persisted separately to the
database (app.models). Raw embeddings never leave this process.
"""
from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class ScanState:
    scan_id: str
    created_at: float = field(default_factory=time.time)
    status: str = "created"
    query: Optional[str] = None

    image_path: Optional[str] = None
    image_bytes: Optional[bytes] = field(default=None, repr=False)

    embedding: Optional[np.ndarray] = field(default=None, repr=False)
    face: Optional[Dict[str, Any]] = None

    search: Optional[Dict[str, Any]] = None
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    # index -> raw image bytes of compared candidates (for fingerprint media hash)
    candidate_bytes: Dict[int, bytes] = field(default_factory=dict, repr=False)

    selected: Optional[Dict[str, Any]] = None
    selected_media_sha256: Optional[str] = None

    fingerprint: Optional[Dict[str, Any]] = None
    evidence: Optional[Dict[str, Any]] = None

    blockchain: Optional[Dict[str, Any]] = None
    record_id: Optional[int] = None

    verification: Optional[Dict[str, Any]] = None

    metrics: Dict[str, int] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)

    # SSE plumbing
    _queue: "asyncio.Queue[Dict[str, Any]]" = field(default_factory=asyncio.Queue, repr=False)
    done: bool = False

    def emit(self, event: str, detail: Optional[Dict[str, Any]] = None) -> None:
        payload = {
            "event": event,
            "detail": detail or {},
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self.events.append(payload)
        try:
            self._queue.put_nowait(payload)
        except Exception:
            pass


class ScanStore:
    def __init__(self) -> None:
        self._scans: Dict[str, ScanState] = {}
        self._lock = threading.Lock()

    def create(self, scan_id: str, query: Optional[str] = None) -> ScanState:
        with self._lock:
            state = ScanState(scan_id=scan_id, query=query)
            self._scans[scan_id] = state
            return state

    def get(self, scan_id: str) -> Optional[ScanState]:
        with self._lock:
            return self._scans.get(scan_id)

    def require(self, scan_id: str) -> ScanState:
        state = self.get(scan_id)
        if state is None:
            raise KeyError(scan_id)
        return state

    def all(self) -> List[ScanState]:
        with self._lock:
            return list(self._scans.values())


store = ScanStore()
