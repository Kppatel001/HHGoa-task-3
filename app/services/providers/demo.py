"""DEMO DATASET provider — clearly labeled local fixtures.

This provider does NOT contact the web and does NOT pretend a real search
occurred. Every result it returns is explicitly tagged as demo data so judges
can run the full pipeline (face -> match -> fingerprint -> blockchain -> verify)
without configuring an external search API.

The fixtures live in a manifest (demo_data/demo_dataset.json) referencing local
image files. Populate them once with:  python -m scripts.make_demo_data
(downloads synthetic, non-real faces) — or drop your own AUTHORIZED images in.

If the manifest is missing/empty the provider raises SearchUnavailableError
rather than fabricating a result.
"""
from __future__ import annotations

import json
import os
from typing import List, Optional

from app.core.logging import get_logger
from app.services.providers.base import (
    SearchProvider,
    SearchResult,
    SearchUnavailableError,
)

log = get_logger("faceproof.search.demo")

_DEFAULT_MANIFEST = os.path.join(
    os.path.dirname(__file__), "demo_data", "demo_dataset.json"
)


class DemoProvider(SearchProvider):
    name = "demo"
    genuine = False

    def __init__(self, manifest_path: str | None = None) -> None:
        self.manifest_path = manifest_path or _DEFAULT_MANIFEST

    async def search(
        self, image_path: str, query: Optional[str], max_results: int
    ) -> List[SearchResult]:
        if not os.path.exists(self.manifest_path):
            raise SearchUnavailableError(
                "DEMO dataset not initialized. Run "
                "`python -m scripts.make_demo_data` in backend/ to populate it, "
                "or add authorized images + a manifest to demo_data/."
            )
        with open(self.manifest_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)

        base_dir = os.path.dirname(self.manifest_path)
        entries = manifest.get("entries", [])
        results: List[SearchResult] = []
        for e in entries[:max_results]:
            local_rel = e.get("local_image")
            local_path = os.path.join(base_dir, local_rel) if local_rel else None
            results.append(
                SearchResult(
                    url=e.get("url", ""),
                    title=e.get("title"),
                    description=e.get("caption"),
                    image_url=e.get("image_url") or (f"file://{local_path}" if local_path else None),
                    platform=e.get("platform", "DEMO — Public Web Fixture"),
                    published_at=e.get("published_at"),
                    author=e.get("author"),
                    raw_metadata={
                        "demo": True,
                        "label": "DEMO DATASET",
                        "local_path": local_path,
                    },
                )
            )
        log.info("[SEARCH] provider=demo candidates=%d (DEMO DATASET)", len(results))
        return results
