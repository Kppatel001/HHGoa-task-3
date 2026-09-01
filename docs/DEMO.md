# FaceProof — Judge Demo Flow

Target time: **under 3 minutes.**

## 0. Start the stack

```bash
docker compose up --build
# then, once, to populate the labeled demo dataset:
docker compose exec backend python -m scripts.make_demo_data
```

Open http://localhost:5173. Check **System Status** — Face Recognition,
Search, Blockchain RPC, Smart Contract and API should read online (Face may be
"cold" for ~1 min while the model downloads).

## 1. Happy path → VERIFIED

1. Go to **New Scan**.
2. Upload the demo subject image (`backend/app/services/providers/demo_data/subject.jpg`,
   created by `make_demo_data`). In genuine mode, upload an authorized image and
   enter a search query.
3. Click **Analyze Face**. Watch the pipeline animate in real time:
   - **Face Detection** → bounding box + confidence
   - **Face Encoding** → 512-d embedding (only an `embedding_id` is shown)
   - **Web Search** → candidates retrieved (labeled `DEMO DATASET` or the real
     provider)
   - **Matching Content** → genuine cosine similarity, best candidate selected
   - **Content Fingerprint** → SHA-256 over canonical evidence
   - **Blockchain Registration** → tx hash, block, record id
   - **Verification** → **VERIFIED ✓**, integrity 100%, current hash == on-chain hash.
4. Scroll the **Audit Trail** for the timestamped pipeline.

## 2. Tamper proof → TAMPERED

1. In the Verification panel, click **Simulate tampering**.
2. The backend recomputes the fingerprint from *modified* evidence and compares
   it to the unchanged on-chain record.
3. The result flips to **TAMPER DETECTED** — current hash ≠ blockchain hash.

This second step is the important one: it proves the on-chain verification is
genuinely functional, not cosmetic.

## 3. Explore

- **Blockchain Records** — every registered fingerprint, tx and block.
- **Verification History** — filter by verified / tampered / pending.
- **API docs** — http://localhost:8000/api/docs to call each stage directly, or
  `POST /api/pipeline` (with `simulate_tamper=true`) to run everything at once.

## Honest failure modes (by design)

- No face in the image → `No detectable face found`.
- Genuine search returns nothing similar → `No sufficiently similar public
  result found`.
- Chain unreachable → `BLOCKCHAIN REGISTRATION FAILED` (fingerprint still shown).

FaceProof never fabricates a `MATCH FOUND` or `VERIFIED` result.
