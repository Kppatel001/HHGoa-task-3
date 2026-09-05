from app.utils.canonicalization import build_evidence, canonical_json, fingerprint


def _evidence(**over):
    base = dict(
        source_url="https://example.com/post/1",
        platform="Public Web",
        title="A public post",
        caption="hello world",
        author="Jane Public",
        published_at="2026-08-20T10:00:00Z",
        media_sha256="deadbeef",
    )
    base.update(over)
    return build_evidence(**base)


def test_canonical_json_is_key_sorted_and_compact():
    cj = canonical_json(_evidence())
    assert cj.startswith("{")
    assert '"author":"Jane Public"' in cj
    # keys must be sorted: author before caption before platform ...
    assert cj.index('"author"') < cj.index('"caption"') < cj.index('"platform"')
    # compact separators: no space after ':' or ',' (values keep their own spaces)
    assert '": "' not in cj and '", "' not in cj


def test_same_evidence_same_fingerprint():
    assert fingerprint(_evidence()) == fingerprint(_evidence())


def test_field_order_does_not_matter():
    a = build_evidence(
        source_url="u", platform="p", title="t", caption="c",
        author="a", published_at="d", media_sha256="m",
    )
    b = build_evidence(
        media_sha256="m", author="a", caption="c", title="t",
        platform="p", source_url="u", published_at="d",
    )
    assert fingerprint(a) == fingerprint(b)


def test_tampering_changes_fingerprint():
    original = fingerprint(_evidence())
    tampered = fingerprint(_evidence(caption="MODIFIED caption"))
    assert original != tampered


def test_media_change_changes_fingerprint():
    assert fingerprint(_evidence(media_sha256="aaaa")) != fingerprint(_evidence(media_sha256="bbbb"))
