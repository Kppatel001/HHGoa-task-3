"""Search orchestration + candidate face analysis.

Flow:
    provider.search(query)  ->  normalized candidates
        -> download each candidate image (SSRF-guarded; local read for demo)
        -> detect + embed candidate face (genuine InsightFace)
        -> cosine similarity vs the input face embedding
        -> rank; pick best; flag potential match by threshold

Nothing here is hardcoded. In demo mode the *candidates* come from a labeled
local dataset, but the face comparison that produces the similarity score is
still a genuine computation on real image bytes.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

import httpx
import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import sniff_image_mime, validate_public_url, SSRFError
from app.services import matching_service
from app.services.face_service import get_face_service
from app.services.providers.base import (
    SearchProvider,
    SearchResult,
    SearchUnavailableError,
    deduplicate,
)
from app.services.providers.demo import DemoProvider
from app.services.providers.google_cse import GoogleCSEProvider
from app.utils.image_utils import InvalidImageError, load_rgb_array

log = get_logger("faceproof.search")

ProgressCb = Optional[Callable[[str, dict], None]]


@dataclass
class Candidate:
    result: SearchResult
    similarity: Optional[float] = None
    face_compared: bool = False
    error: Optional[str] = None
    image_bytes: Optional[bytes] = field(default=None, repr=False)

    def to_public_dict(self) -> dict:
        d = self.result.to_dict()
        d["similarity"] = round(self.similarity, 4) if self.similarity is not None else None
        d["face_compared"] = self.face_compared
        d["error"] = self.error
        return d


@dataclass
class SearchOutcome:
    provider: str
    genuine: bool
    candidates: List[Candidate]
    best: Optional[Candidate]
    threshold: float
    potential_match: bool
    search_time_ms: int
    results_found: int


def _select_provider() -> SearchProvider:
    name = settings.search_provider.lower()
    if name == "google_cse":
        return GoogleCSEProvider()
    if name == "demo":
        return DemoProvider()
    raise SearchUnavailableError(f"Unknown SEARCH_PROVIDER: {settings.search_provider!r}")


async def _fetch_candidate_bytes(cand: SearchResult) -> bytes:
    """Return the candidate image bytes, from local file (demo) or public URL."""
    local_path = cand.raw_metadata.get("local_path")
    if local_path:
        with open(local_path, "rb") as fh:
            data = fh.read(settings.candidate_max_image_bytes + 1)
        if len(data) > settings.candidate_max_image_bytes:
            raise ValueError("Local candidate image exceeds size limit")
        return data

    if not cand.image_url:
        raise ValueError("Candidate has no image URL")

    # SSRF guard for anything fetched from the network.
    validate_public_url(cand.image_url)
    async with httpx.AsyncClient(
        timeout=settings.search_http_timeout, follow_redirects=True
    ) as client:
        async with client.stream("GET", cand.image_url) as resp:
            resp.raise_for_status()
            buf = bytearray()
            async for chunk in resp.aiter_bytes():
                buf.extend(chunk)
                if len(buf) > settings.candidate_max_image_bytes:
                    raise ValueError("Candidate image exceeds size limit")
    data = bytes(buf)
    if sniff_image_mime(data[:16]) is None:
        raise ValueError("Candidate URL did not return a supported image")
    return data


async def run_search(
    *,
    input_embedding: np.ndarray,
    image_path: str,
    query: Optional[str],
    emit: ProgressCb = None,
) -> SearchOutcome:
    """Execute a genuine search + candidate face comparison."""
    start = time.perf_counter()
    provider = _select_provider()
    face_svc = get_face_service()

    if emit:
        emit("search_started", {"provider": provider.name, "genuine": provider.genuine})

    raw = await provider.search(image_path, query, settings.search_max_results)
    raw = deduplicate(raw)
    log.info("[SEARCH] provider=%s results=%d", provider.name, len(raw))

    candidates: List[Candidate] = []
    for res in raw:
        if emit:
            emit("search_result_found", {"url": res.url, "platform": res.platform})
        cand = Candidate(result=res)
        candidates.append(cand)

    # Candidate face comparison.
    if emit:
        emit("candidate_analysis_started", {"count": len(candidates)})

    for idx, cand in enumerate(candidates):
        try:
            data = await _fetch_candidate_bytes(cand.result)
            rgb = load_rgb_array(data)
            analysis = face_svc.analyze(rgb)
            if analysis.primary is None:
                cand.error = "no_face_in_candidate"
                continue
            match = matching_service.compare(input_embedding, analysis.primary.embedding)
            cand.similarity = match.similarity
            cand.face_compared = True
            cand.image_bytes = data
            log.info("[MATCH] candidate=%d similarity=%.4f", idx, match.similarity)
        except (SSRFError, InvalidImageError, ValueError, httpx.HTTPError) as exc:
            cand.error = str(exc)
            log.warning("[MATCH] candidate=%d skipped: %s", idx, exc)

    # Rank by similarity (None sorts last).
    compared = [c for c in candidates if c.similarity is not None]
    compared.sort(key=lambda c: c.similarity or -1.0, reverse=True)
    best = compared[0] if compared else None
    threshold = settings.face_match_threshold
    potential = bool(best and best.similarity is not None and best.similarity >= threshold)

    if emit and best:
        emit(
            "candidate_match_found",
            {"similarity": best.similarity, "url": best.result.url, "potential_match": potential},
        )

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    # Ordered candidates: compared (ranked) first, then the rest.
    ordered = compared + [c for c in candidates if c.similarity is None]
    return SearchOutcome(
        provider=provider.name,
        genuine=provider.genuine,
        candidates=ordered,
        best=best,
        threshold=threshold,
        potential_match=potential,
        search_time_ms=elapsed_ms,
        results_found=len(candidates),
    )
