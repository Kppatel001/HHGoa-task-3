"""End-to-end self test: runs the full pipeline against the running app and
prints the results. Works in Docker or the no-Docker (memory-chain) setup."""
import json, httpx, os

BASE = os.environ.get("SELFTEST_BASE", "http://127.0.0.1:8000")
SUBJ = "app/services/providers/demo_data/subject.jpg"


def run(tamper):
    with open(SUBJ, "rb") as f:
        r = httpx.post(
            f"{BASE}/api/pipeline",
            files={"file": ("subject.jpg", f, "image/jpeg")},
            data={"simulate_tamper": str(tamper).lower()},
            timeout=600,
        )
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"raw": r.text[:800]}


sc, js = run(False)
m, b, v = js.get("match") or {}, js.get("blockchain") or {}, js.get("verification") or {}
print("=== PIPELINE (normal) HTTP", sc)
print("match.similarity   =", m.get("similarity"))
print("blockchain.status  =", b.get("status"), "record_id=", b.get("record_id"), "block=", b.get("block_number"))
print("verification.status=", v.get("status"), "integrity=", v.get("integrity_percent"))

sc2, js2 = run(True)
v2 = js2.get("verification") or {}
print("=== PIPELINE (tamper) HTTP", sc2)
print("verification.status=", v2.get("status"))
print("=== SELFTEST_DONE")
