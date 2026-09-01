"""Face matching via cosine similarity between L2-normalized embeddings.

    similarity = dot(A, B) / (||A|| * ||B||)

InsightFace's `normed_embedding` is already unit-length, so the dot product is
the cosine similarity directly. We renormalize defensively anyway.

Important framing: exceeding the threshold yields a *potential* content match,
never a claim of definitive identity. That wording is enforced in the schema
layer and the UI.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.core.config import settings


@dataclass
class MatchResult:
    similarity: float
    threshold: float
    potential_match: bool


def _unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = _unit(np.asarray(a, dtype=np.float32))
    b = _unit(np.asarray(b, dtype=np.float32))
    # Clamp to [-1, 1] to absorb floating-point drift.
    return float(np.clip(np.dot(a, b), -1.0, 1.0))


def compare(a: np.ndarray, b: np.ndarray, threshold: float | None = None) -> MatchResult:
    thr = settings.face_match_threshold if threshold is None else threshold
    sim = cosine_similarity(a, b)
    return MatchResult(similarity=sim, threshold=thr, potential_match=sim >= thr)
