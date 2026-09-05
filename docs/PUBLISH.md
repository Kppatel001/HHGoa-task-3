# FaceProof — Publish Readiness

## Verified working (live QA)
- Full pipeline: FACE → SEARCH → MATCH → FINGERPRINT → BLOCKCHAIN → VERIFY
- Happy path → **VERIFIED** (similarity 1.0, blockchain confirmed, integrity 100%)
- Tamper → **TAMPERED** (integrity 0%)
- Error handling: no-face → 422, wrong file type → 415, no match → clear message
- Health/status endpoints, ~1.3s pipeline latency, CORS + SPA routing correct
- Frontend + serverless backend deployed on Vercel

## Two ways to publish

### A. Demo mode — ready to publish now (best for judging)
Fully working end-to-end with the bundled sample. Set on the backend:
```
SEARCH_PROVIDER=demo
BLOCKCHAIN_MODE=memory
```
Runs on Vercel (serverless) or Render. Every stage works; results are clearly
labeled "DEMO DATASET". This is the recommended configuration for a hackathon
demo / judging.

### B. Genuine public search — needs the Render backend
Genuine cross-photo face recognition needs the **InsightFace (ArcFace)** model,
which does not fit Vercel serverless. Deploy the backend on **Render** (Docker),
where the image installs InsightFace:
```
SEARCH_PROVIDER=google_cse
GOOGLE_CSE_CX=<your engine id>
GOOGLE_CSE_API_KEY=<your AIza key>   # Custom Search JSON API must be ENABLED
BLOCKCHAIN_MODE=memory
FIREBASE_DB_URL=<optional, for durable records>
```
Then point the Vercel frontend's `VITE_API_BASE_URL` at the Render URL + `/api`.

Requirements for genuine mode to actually match:
1. **Custom Search JSON API enabled** on the key's Google Cloud project.
2. **Google billing / quota** — free tier is 100 searches/day.
3. **Render instance with enough RAM** — InsightFace + onnxruntime may exceed the
   512 MB free tier; use a larger instance if the service OOMs on first scan.

## Go / no-go
- **Judging / controlled demo:** READY (demo mode).
- **Open public with genuine matching:** READY once deployed on Render with
  InsightFace + Custom Search enabled + billing + (recommended) Firebase.

## Before an open public launch
- Lock Firebase rules (don't leave Test mode open); set `FIREBASE_DB_SECRET`.
- Keep the on-page privacy notice (authorized/public images only; "potential match").
- Consider stricter rate limits and a Google billing cap.
