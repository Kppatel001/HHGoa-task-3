"""Search provider abstraction + normalized result schema.

Every provider — genuine or demo — returns the same normalized structure so the
rest of the application never depends on a specific search backend.
"""
from __future__ import annotations

import abc
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


@dataclass
class SearchResult:
    url: str
    domain: str = ""
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    platform: Optional[str] = None
    published_at: Optional[str] = None
    author: Optional[str] = None
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.domain and self.url:
            self.domain = urlparse(self.url).netloc
        if not self.platform:
            self.platform = self.domain or "Public Web"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SearchProvider(abc.ABC):
    """Base class. `search` performs a genuine query and returns candidates.

    Providers must NOT fabricate results. If the backend is unavailable they
    should raise SearchUnavailableError.
    """

    name: str = "base"
    genuine: bool = False

    @abc.abstractmethod
    async def search(
        self, image_path: str, query: Optional[str], max_results: int
    ) -> List[SearchResult]:
        raise NotImplementedError


class SearchUnavailableError(RuntimeError):
    """Raised when a genuine provider cannot reach its backend / is misconfigured."""


def deduplicate(results: List[SearchResult]) -> List[SearchResult]:
    seen: set[str] = set()
    unique: List[SearchResult] = []
    for r in results:
        key = (r.url or "").split("#")[0].rstrip("/")
        if key and key not in seen:
            seen.add(key)
            unique.append(r)
    return unique
