import numpy as np

from app.services import matching_service


def test_identical_vectors_similarity_one():
    v = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
    assert matching_service.cosine_similarity(v, v) == pytest_approx(1.0)


def test_orthogonal_vectors_similarity_zero():
    a = np.array([1.0, 0.0], dtype=np.float32)
    b = np.array([0.0, 1.0], dtype=np.float32)
    assert abs(matching_service.cosine_similarity(a, b)) < 1e-6


def test_opposite_vectors_similarity_negative_one():
    a = np.array([1.0, 0.0], dtype=np.float32)
    assert matching_service.cosine_similarity(a, -a) == pytest_approx(-1.0)


def test_threshold_flags_potential_match():
    v = np.array([1.0, 1.0], dtype=np.float32)
    r = matching_service.compare(v, v, threshold=0.5)
    assert r.potential_match is True
    assert r.similarity == pytest_approx(1.0)

    a = np.array([1.0, 0.0], dtype=np.float32)
    b = np.array([0.0, 1.0], dtype=np.float32)
    r2 = matching_service.compare(a, b, threshold=0.5)
    assert r2.potential_match is False


# tiny approx helper to avoid importing pytest.approx at module import time
def pytest_approx(x, tol=1e-5):
    class _A:
        def __eq__(self, other):
            return abs(other - x) <= tol

    return _A()
