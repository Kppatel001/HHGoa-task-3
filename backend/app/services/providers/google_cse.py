"""Genuine Google Programmable Search (Custom Search JSON API) provider.

This performs a REAL HTTP query against Google's Custom Search JSON API and
returns publicly-accessible web results. There is no hardcoded result.

Note on "reverse image" scope: the Custom Search JSON API searches by keywords,
not by an uploaded face (Google does not expose upload-a-face search via a
public API, and building face-based deanonymization would violate this
project's safety policy). So the genuine flow is:

    1. Google CSE image search using the caller-supplied `query` (keywords
       describing the *authorized* public content/subject) -> real public
       candidate pages + images.
    2. Each candidate image is downloaded (SSRF-guarded) and its face compared
       to the uploaded face with cosine similarity (see matching_service).

That candidate face comparison is where the genuine visual matching happens.
"""
from __future__ import annotations

from typing import List, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.services.providers.base import (
    SearchProvider,
    SearchResult,
    SearchUnavailableError,
)

log = get_logger("faceproof.search.google")

_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


class GoogleCSEProvider(SearchProvider):
    name = "google_cse"
    genuine = True

    def __init__(self) -> None:
        self.api_key = settings.google_cse_api_key
        self.cx = settings.google_cse_cx

    def _configured(self) -> bool:
        return bool(self.api_key and self.cx)

    async def search(
        self, image_path: str, query: Optional[str], max_results: int
    ) -> List[SearchResult]:
        if not self._configured():
            raise SearchUnavailableError(
                "Google CSE not configured. Set GOOGLE_CSE_API_KEY and "
                "GOOGLE_CSE_CX in .env, or switch SEARCH_PROVIDER=demo."
            )
        if not query or not query.strip():
            raise SearchUnavailableError(
                "Google CSE requires a text query describing the authorized "
                "public content to find (it cannot search by a raw face image)."
            )

        num = max(1, min(int(max_results), 10))  # CSE caps at 10 per page
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query.strip(),
            "searchType": "image",
            "num": num,
            "safe": "active",
        }
        log.info("[SEARCH] provider=google_cse q=%r num=%d", query.strip(), num)
        try:
            async with httpx.AsyncClient(timeout=settings.search_http_timeout) as client:
                resp = await client.get(_ENDPOINT, params=params)
        except httpx.HTTPError as exc:
            raise SearchUnavailableError(f"Google CSE request failed: {exc}") from exc

        if resp.status_code != 200:
            raise SearchUnavailableError(
                f"Google CSE returned HTTP {resp.status_code}: {resp.text[:200]}"
            )

        payload = resp.json()
        items = payload.get("items", []) or []
        results: List[SearchResult] = []
        for it in items:
            image_meta = it.get("image", {}) or {}
            context_link = image_meta.get("contextLink") or it.get("link")
            results.append(
                SearchResult(
                    url=context_link or it.get("link", ""),
                    title=it.get("title"),
                    description=it.get("snippet"),
                    image_url=it.get("link"),  # direct image URL
                    platform=it.get("displayLink"),
                    raw_metadata={
                        "mime": it.get("mime"),
                        "width": image_meta.get("width"),
                        "height": image_meta.get("height"),
                        "thumbnail": image_meta.get("thumbnailLink"),
                    },
                )
            )
        log.info("[SEARCH] provider=google_cse candidates=%d", len(results))
        return results
