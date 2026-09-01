# FaceProof — Backend (FastAPI)

Modular FastAPI service implementing the FaceProof pipeline:
**FACE → SEARCH → MATCH → FINGERPRINT → BLOCKCHAIN → VERIFY**.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
python -m scripts.make_demo_data      # optional: populate the demo dataset
uvicorn app.main:app --reload         # docs: http://localhost:8000/api/docs
pytest -q                             # tests
```

## Layout

```
app/
├── main.py                 FastAPI app, CORS, rate limiting, lifespan
├── api/                    routes: health, scan, search, blockchain, verify, pipeline
├── services/
│   ├── face_service.py     InsightFace singleton (detection + 512-d embedding)
│   ├── matching_service.py cosine similarity + threshold
│   ├── search_service.py   provider orchestration + candidate face comparison
│   ├── providers/          base · google_cse (genuine) · demo (labeled fixtures)
│   ├── fingerprint_service.py   SHA-256 over canonical evidence
│   ├── blockchain_service.py    Web3.py register / read / verify
│   ├── verification_service.py  recompute + compare → VERIFIED/TAMPERED
│   └── pipeline.py         stage orchestration + persistence
├── core/                   config · logging (secret redaction) · security (SSRF)
├── utils/                  hashing · canonicalization · image utils
├── models/                 SQLAlchemy models
├── schemas/                Pydantic response models
├── store.py                in-memory scan state + SSE event bus
└── abi/                    contract ABI fallback
scripts/make_demo_data.py   downloads synthetic (non-real) demo faces
```

Privacy: raw embeddings are never returned or logged; uploads are deleted after
the session (`DELETE_UPLOADS_AFTER_SESSION=true`); embeddings are not persisted
unless `STORE_EMBEDDINGS=true`.
