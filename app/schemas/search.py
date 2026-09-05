from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: Optional[str] = Field(
        default=None,
        description=(
            "Keywords describing the authorized public content/subject to find. "
            "Required for the google_cse provider (it cannot search by a raw face)."
        ),
    )


class CandidateOut(BaseModel):
    id: int
    url: str
    domain: str = ""
    platform: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[str] = None
    similarity: Optional[float] = None
    face_compared: bool = False
    error: Optional[str] = None
    raw_metadata: Dict[str, Any] = {}


class SearchResultsOut(BaseModel):
    scan_id: str
    provider: str
    genuine: bool = Field(..., description="True only when a real external search ran")
    results_found: int
    threshold: float
    potential_match: bool
    best_candidate_id: Optional[int] = None
    search_time_ms: int
    candidates: List[CandidateOut]


class SelectMatchRequest(BaseModel):
    result_id: int


class MatchOut(BaseModel):
    status: str
    similarity: Optional[float]
    threshold: float
    source_url: Optional[str]
    platform: Optional[str]
