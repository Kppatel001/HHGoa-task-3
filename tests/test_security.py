import pytest

from app.core.security import SSRFError, sniff_image_mime, validate_public_url


def test_rejects_localhost():
    with pytest.raises(SSRFError):
        validate_public_url("http://localhost/secret")


def test_rejects_private_ip():
    with pytest.raises(SSRFError):
        validate_public_url("http://127.0.0.1:8000/admin")
    with pytest.raises(SSRFError):
        validate_public_url("http://192.168.1.10/")


def test_rejects_non_http_scheme():
    with pytest.raises(SSRFError):
        validate_public_url("file:///etc/passwd")
    with pytest.raises(SSRFError):
        validate_public_url("gopher://evil/")


def test_sniff_image_mime():
    assert sniff_image_mime(b"\xff\xd8\xff\xe0abcd") == "image/jpeg"
    assert sniff_image_mime(b"\x89PNG\r\n\x1a\n....") == "image/png"
    assert sniff_image_mime(b"RIFF1234WEBPXXXX") == "image/webp"
    assert sniff_image_mime(b"not an image") is None
