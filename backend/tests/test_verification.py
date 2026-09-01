"""End-to-end crypto/verification test using a fake in-memory chain.

Proves the core claim WITHOUT needing a real EVM node:
    fingerprint -> register -> verify(original) == VERIFIED
    fingerprint -> register -> verify(tampered) == TAMPERED
"""
from dataclasses import dataclass

import app.services.verification_service as vs
from app.services import fingerprint_service


@dataclass
class _Rec:
    fingerprint: str


class FakeChain:
    def __init__(self):
        self._store = {}
        self._n = 0

    def register_hex(self, fp_hex: str) -> int:
        self._n += 1
        self._store[self._n] = fp_hex
        return self._n

    def get_record(self, record_id: int) -> _Rec:
        return _Rec(fingerprint=self._store[record_id])

    def verify_onchain(self, record_id: int, fp_hex: str) -> bool:
        return self._store.get(record_id) == fp_hex


def _make_evidence(caption="original caption"):
    fp = fingerprint_service.generate(
        source_url="https://example.com/post/1",
        platform="Public Web",
        title="Public post",
        caption=caption,
        author="Jane Public",
        published_at="2026-08-20T10:00:00Z",
        media_sha256="abc123",
    )
    return fp


def test_verified_when_untouched(monkeypatch):
    fp = _make_evidence()
    chain = FakeChain()
    rid = chain.register_hex(fp.fingerprint)
    monkeypatch.setattr(vs, "get_blockchain_service", lambda: chain)

    result = vs.verify(fp.evidence, rid)
    assert result.status == "VERIFIED"
    assert result.verified is True
    assert result.match is True
    assert result.integrity_percent == 100
    assert result.current_hash == fp.fingerprint == result.blockchain_hash


def test_tampered_when_content_changed(monkeypatch):
    fp = _make_evidence()
    chain = FakeChain()
    rid = chain.register_hex(fp.fingerprint)
    monkeypatch.setattr(vs, "get_blockchain_service", lambda: chain)

    # Tamper with the evidence AFTER registration.
    tampered_evidence = dict(fp.evidence)
    tampered_evidence["caption"] = "MODIFIED after registration"

    result = vs.verify(tampered_evidence, rid)
    assert result.status == "TAMPERED"
    assert result.verified is False
    assert result.match is False
    assert result.integrity_percent == 0
    assert result.current_hash != result.blockchain_hash


def test_not_verified_without_record():
    fp = _make_evidence()
    result = vs.verify(fp.evidence, None)
    assert result.status == "NOT_VERIFIED"
    assert result.blockchain_hash is None
