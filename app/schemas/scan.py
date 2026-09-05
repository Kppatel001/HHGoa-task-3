from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class BBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class ScanCreated(BaseModel):
    scan_id: str
    status: str


class FaceResult(BaseModel):
    face_detected: bool
    face_count: int
    confidence: float = Field(..., description="Detector confidence for the primary face")
    bbox: Optional[BBox] = None
    embedding_dimension: int
    embedding_id: str = Field(..., description="Non-invertible id; the raw vector is never exposed")
    model: str
    quality: str
    processing_time_ms: int
    image_width: int
    image_height: int
    warning: Optional[str] = None
