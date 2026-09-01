"""Image decoding, validation and safe loading helpers."""
from __future__ import annotations

import io
from typing import Tuple

import numpy as np
from PIL import Image, ImageFile, UnidentifiedImageError

# Refuse to load absurdly large images (decompression-bomb guard).
Image.MAX_IMAGE_PIXELS = 40_000_000  # ~40 MP
ImageFile.LOAD_TRUNCATED_IMAGES = False


class InvalidImageError(ValueError):
    pass


def load_rgb_array(data: bytes) -> np.ndarray:
    """Decode raw image bytes into an HxWx3 uint8 RGB numpy array.

    Raises InvalidImageError for anything that is not a decodable image or that
    trips the decompression-bomb guard.
    """
    try:
        with Image.open(io.BytesIO(data)) as im:
            im = im.convert("RGB")
            arr = np.asarray(im, dtype=np.uint8)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidImageError(f"Could not decode image: {exc}") from exc
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise InvalidImageError("Decoded image is not 3-channel RGB")
    return arr


def image_dimensions(data: bytes) -> Tuple[int, int]:
    """Return (width, height) without fully decoding pixels where possible."""
    with Image.open(io.BytesIO(data)) as im:
        return im.size  # (width, height)


def to_bgr(rgb: np.ndarray) -> np.ndarray:
    """InsightFace / OpenCV expect BGR ordering."""
    return rgb[:, :, ::-1].copy()


def estimate_quality(rgb: np.ndarray) -> Tuple[str, float]:
    """A cheap image-quality heuristic based on Laplacian variance (sharpness).

    Returns a label ("Good" / "Fair" / "Poor") and the raw sharpness score.
    """
    # Convert to grayscale luminance.
    gray = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]).astype(
        np.float64
    )
    # Discrete Laplacian via convolution (edge energy ~ sharpness).
    lap = (
        -4 * gray[1:-1, 1:-1]
        + gray[:-2, 1:-1]
        + gray[2:, 1:-1]
        + gray[1:-1, :-2]
        + gray[1:-1, 2:]
    )
    score = float(lap.var()) if lap.size else 0.0
    if score >= 120:
        label = "Good"
    elif score >= 30:
        label = "Fair"
    else:
        label = "Poor"
    return label, score
