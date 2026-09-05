"""API smoke tests. These avoid loading the heavy face model / a live chain by
patching warmup; they verify routing, validation and the health contract."""
import io

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    # Prevent the startup hook from downloading/loading the InsightFace model.
    from app.services.face_service import FaceService

    monkeypatch.setattr(FaceService, "warmup", lambda self: False)
    from app.main import app

    with TestClient(app) as c:
        yield c


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "FaceProof" in r.json()["name"]


def test_health_contract(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    for key in ("api", "face_service", "search_service", "blockchain"):
        assert key in body
    assert body["api"] == "online"


def test_status_contract(client):
    r = client.get("/api/status")
    assert r.status_code == 200
    comps = r.json()["components"]
    assert set(["face_recognition", "search_service", "blockchain_rpc", "smart_contract", "api"]).issubset(comps)


def test_upload_rejects_non_image(client):
    files = {"file": ("bad.txt", io.BytesIO(b"not an image"), "text/plain")}
    r = client.post("/api/scan", files=files)
    assert r.status_code == 415


def test_unknown_scan_404(client):
    r = client.post("/api/scan/does_not_exist/face")
    assert r.status_code == 404
