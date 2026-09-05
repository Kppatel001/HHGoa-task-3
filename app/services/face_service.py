"""Face detection & embedding service.

Two engines, chosen automatically at load time:

  1. "insightface"  — preferred. InsightFace FaceAnalysis (buffalo_l, 512-d
     ArcFace embeddings). Best accuracy.
  2. "opencv"       — automatic fallback when InsightFace isn't installed
     (e.g. on Windows without a C++ build toolchain). Uses OpenCV's Haar
     cascade for detection and a deterministic, L2-normalized appearance
     descriptor for comparison. Installs cleanly everywhere (wheels only).

The engine is loaded once (lazily) and reused. Raw embeddings/descriptors are
used only in-process for cosine comparison and are never returned or logged;
only a non-invertible short id is exposed.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger
from app.utils.hashing import sha256_bytes
from app.utils.image_utils import estimate_quality, to_bgr

log = get_logger("faceproof.face")


@dataclass
class DetectedFace:
    bbox: tuple[int, int, int, int]  # x, y, w, h
    det_score: float
    embedding: np.ndarray  # L2-normalized

    @property
    def embedding_dim(self) -> int:
        return int(self.embedding.shape[0])

    @property
    def embedding_id(self) -> str:
        digest = sha256_bytes(np.round(self.embedding, 4).tobytes())
        return f"face_{digest[:12]}"


@dataclass
class FaceAnalysisResult:
    face_detected: bool
    face_count: int
    faces: List[DetectedFace]
    quality_label: str
    quality_score: float
    processing_time_ms: int
    width: int
    height: int
    model_name: str = "unknown"

    @property
    def primary(self) -> Optional[DetectedFace]:
        if not self.faces:
            return None
        return max(self.faces, key=lambda f: f.bbox[2] * f.bbox[3])


class FaceService:
    """Singleton with an InsightFace-preferred, OpenCV-fallback engine."""

    _instance: "FaceService | None" = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._if_app = None          # insightface FaceAnalysis
        self._cv_cascade = None      # opencv Haar cascade
        self._engine: Optional[str] = None
        self._load_error: Optional[str] = None
        self._model_lock = threading.Lock()

    @classmethod
    def instance(cls) -> "FaceService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = FaceService()
        return cls._instance

    # ---- engine lifecycle ----
    def _try_insightface(self) -> bool:
        try:
            from insightface.app import FaceAnalysis

            app = FaceAnalysis(name=settings.face_model, providers=[settings.face_exec_provider])
            app.prepare(ctx_id=0, det_size=(640, 640))
            self._if_app = app
            self._engine = "insightface"
            log.info("[FACE] engine=insightface model=%s", settings.face_model)
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("[FACE] insightface unavailable (%s) — trying OpenCV fallback", exc)
            return False

    def _try_opencv(self) -> bool:
        try:
            import cv2

            path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            cascade = cv2.CascadeClassifier(path)
            if cascade.empty():
                raise RuntimeError("Haar cascade failed to load")
            self._cv_cascade = cascade
            self._engine = "opencv"
            log.info("[FACE] engine=opencv (Haar + appearance descriptor fallback)")
            return True
        except Exception as exc:  # noqa: BLE001
            log.error("[FACE] OpenCV fallback failed: %s", exc)
            return False

    def _ensure_model(self):
        if self._engine is not None:
            return
        with self._model_lock:
            if self._engine is not None:
                return
            if self._try_insightface() or self._try_opencv():
                self._load_error = None
                return
            self._load_error = "No face engine available (install insightface or opencv-python-headless)."
            raise RuntimeError(self._load_error)

    def warmup(self) -> bool:
        try:
            self._ensure_model()
            return True
        except Exception:  # noqa: BLE001
            return False

    @property
    def ready(self) -> bool:
        return self._engine is not None

    @property
    def engine_name(self) -> str:
        return self._engine or settings.face_model

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    # ---- inference ----
    def analyze(self, rgb: np.ndarray) -> FaceAnalysisResult:
        start = time.perf_counter()
        self._ensure_model()
        height, width = rgb.shape[:2]
        if self._engine == "insightface":
            faces = self._analyze_insightface(rgb)
            model_name = f"InsightFace/{settings.face_model}"
        else:
            faces = self._analyze_opencv(rgb)
            model_name = "OpenCV/haar+appearance"

        quality_label, quality_score = estimate_quality(rgb)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        log.info("[FACE] detection completed engine=%s faces=%d %dms", self._engine, len(faces), elapsed_ms)
        return FaceAnalysisResult(
            face_detected=len(faces) > 0,
            face_count=len(faces),
            faces=faces,
            quality_label=quality_label,
            quality_score=quality_score,
            processing_time_ms=elapsed_ms,
            width=width,
            height=height,
            model_name=model_name,
        )

    def _analyze_insightface(self, rgb: np.ndarray) -> List[DetectedFace]:
        bgr = to_bgr(rgb)
        out: List[DetectedFace] = []
        for f in self._if_app.get(bgr):
            if float(f.det_score) < settings.face_det_min_confidence:
                continue
            x1, y1, x2, y2 = [int(v) for v in f.bbox]
            emb = np.asarray(f.normed_embedding, dtype=np.float32)
            out.append(DetectedFace((x1, y1, max(0, x2 - x1), max(0, y2 - y1)), float(f.det_score), emb))
        return out

    def _analyze_opencv(self, rgb: np.ndarray) -> List[DetectedFace]:
        import cv2

        bgr = to_bgr(rgb)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        min_px = max(24, settings.face_min_pixels)
        dets, _, weights = self._cv_cascade.detectMultiScale3(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(min_px, min_px),
            outputRejectLevels=True,
        )
        out: List[DetectedFace] = []
        for (x, y, w, h), wt in zip(dets, weights if len(weights) else [3.0] * len(dets)):
            crop = gray[y : y + h, x : x + w]
            if crop.size == 0:
                continue
            # Deterministic appearance descriptor: 64x64, histogram-equalized,
            # flattened and L2-normalized. Identical images -> similarity ~1.0.
            face64 = cv2.equalizeHist(cv2.resize(crop, (64, 64)))
            vec = face64.astype(np.float32).flatten()
            vec -= vec.mean()
            n = float(np.linalg.norm(vec))
            emb = vec / n if n > 0 else vec
            score = float(min(1.0, 0.5 + float(wt) / 12.0))
            out.append(DetectedFace((int(x), int(y), int(w), int(h)), score, emb))
        return out


def get_face_service() -> FaceService:
    return FaceService.instance()
