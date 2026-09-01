"""Security helpers: upload validation and SSRF-safe URL fetching.

The backend fetches candidate images from the public web. Any time we act on a
URL that ultimately derives from user input we must guard against SSRF — i.e.
prevent the server from being tricked into fetching internal/private addresses.
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

# Image content types we accept for candidate downloads and uploads.
ALLOWED_IMAGE_MIME = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Magic-byte signatures for a defensive content sniff (never trust extensions).
_MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp",  # RIFF....WEBP
}


class SSRFError(ValueError):
    """Raised when a URL resolves to a disallowed / private address."""


def sniff_image_mime(header: bytes) -> str | None:
    if header[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if header[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "image/webp"
    return None


def _is_public_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_public_url(url: str) -> str:
    """Return the URL if it is http(s) and resolves only to public IPs.

    Raises SSRFError otherwise. Call this before every backend-side fetch of a
    URL that originated from search results or the frontend.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SSRFError(f"Disallowed URL scheme: {parsed.scheme!r}")
    host = parsed.hostname
    if not host:
        raise SSRFError("URL has no host")

    # Reject obvious internal hostnames outright.
    if host in ("localhost",) or host.endswith(".local") or host.endswith(".internal"):
        raise SSRFError(f"Disallowed host: {host}")

    # Resolve and ensure every resolved address is public.
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise SSRFError(f"DNS resolution failed for {host}") from exc

    for info in infos:
        ip_str = info[4][0]
        if not _is_public_ip(ip_str):
            raise SSRFError(f"URL {host} resolves to non-public address {ip_str}")
    return url
