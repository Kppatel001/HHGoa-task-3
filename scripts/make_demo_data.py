"""Populate the DEMO DATASET with synthetic (non-real) faces.

Run once from the backend/ directory:

    python -m scripts.make_demo_data

It downloads a handful of GAN-generated faces (thispersondoesnotexist.com — no
real person) and builds:
    * demo_data/subject.jpg        -> upload THIS in the UI to run the demo
    * demo_data/cand_*.jpg         -> candidate "public posts" (incl. the subject)
    * demo_data/demo_dataset.json  -> the manifest the demo provider reads

The subject is included as one of the candidates so the genuine cosine-similarity
comparison yields a real high-confidence MATCH — nothing is hardcoded.

If the download is blocked on your network, drop your OWN authorized images into
demo_data/ (name the one you'll upload subject.jpg) and re-run — the script will
build the manifest from whatever *.jpg files are present.
"""
from __future__ import annotations

import json
import os
import sys
import time

import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
DEMO_DIR = os.path.join(HERE, "..", "app", "services", "providers", "demo_data")
DEMO_DIR = os.path.abspath(DEMO_DIR)
SOURCE = "https://thispersondoesnotexist.com"
N_FACES = 4


def _download_faces(n: int) -> list[str]:
    paths = []
    with httpx.Client(timeout=20, follow_redirects=True, headers={"User-Agent": "faceproof-demo/1.0"}) as c:
        for i in range(n):
            r = c.get(SOURCE)
            r.raise_for_status()
            p = os.path.join(DEMO_DIR, f"gan_{i}.jpg")
            with open(p, "wb") as fh:
                fh.write(r.content)
            paths.append(p)
            print(f"  downloaded synthetic face {i + 1}/{n}")
            time.sleep(1.0)
    return paths


def _existing_faces() -> list[str]:
    return [
        os.path.join(DEMO_DIR, f)
        for f in sorted(os.listdir(DEMO_DIR))
        if f.lower().endswith((".jpg", ".jpeg", ".png")) and f != "subject.jpg"
    ]


def build_manifest(face_paths: list[str]) -> None:
    if not face_paths:
        raise SystemExit("No face images available to build the demo dataset.")

    # The first face is the subject; copy it to subject.jpg for uploading.
    subject_src = face_paths[0]
    subject_path = os.path.join(DEMO_DIR, "subject.jpg")
    with open(subject_src, "rb") as s, open(subject_path, "wb") as d:
        d.write(s.read())

    entries = []
    # Entry 0: the matching "public post" — same face as the subject.
    entries.append(
        {
            "local_image": os.path.basename(subject_src),
            "url": "https://example.com/demo/press-release-42",
            "image_url": None,
            "platform": "DEMO — Public Web Fixture",
            "title": "Community Volunteer of the Month (DEMO)",
            "caption": "Public appreciation post featuring the demo subject. DEMO DATASET — synthetic face, not a real person.",
            "author": "Demo City News",
            "published_at": "2026-08-20T10:00:00Z",
        }
    )
    # Distractor faces — genuinely different people (low similarity).
    for i, p in enumerate(face_paths[1:], start=1):
        entries.append(
            {
                "local_image": os.path.basename(p),
                "url": f"https://example.com/demo/unrelated-{i}",
                "image_url": None,
                "platform": "DEMO — Public Web Fixture",
                "title": f"Unrelated public photo #{i} (DEMO)",
                "caption": "DEMO DATASET — synthetic face, unrelated distractor.",
                "author": "Demo Wire",
                "published_at": "2026-08-15T09:00:00Z",
            }
        )

    manifest = {
        "label": "DEMO DATASET",
        "note": "Synthetic GAN faces (no real people). Fixtures only — not a real web search.",
        "subject_upload": "subject.jpg",
        "entries": entries,
    }
    with open(os.path.join(DEMO_DIR, "demo_dataset.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"\nWrote manifest with {len(entries)} entries.")
    print(f"Upload this image in the UI to run the demo:\n  {subject_path}")


def main() -> None:
    os.makedirs(DEMO_DIR, exist_ok=True)
    faces = _existing_faces()
    if len(faces) < 2:
        print(f"Downloading {N_FACES} synthetic faces from {SOURCE} ...")
        try:
            faces = _download_faces(N_FACES)
        except Exception as exc:  # noqa: BLE001
            print(f"Download failed: {exc}", file=sys.stderr)
            print(
                "Add your own authorized .jpg images to demo_data/ and re-run.",
                file=sys.stderr,
            )
            raise SystemExit(1)
    build_manifest(faces)


if __name__ == "__main__":
    main()
