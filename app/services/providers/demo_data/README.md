# DEMO DATASET

This folder holds **clearly-labeled demo fixtures** for running the FaceProof
pipeline without configuring a real external search provider.

It is intentionally empty in git. Populate it once:

```bash
cd backend
python -m scripts.make_demo_data
```

That downloads a few **synthetic, GAN-generated faces** (from
thispersondoesnotexist.com — *not real people*) and writes:

- `subject.jpg` — the image you upload in the UI to run the demo
- `gan_*.jpg` — candidate "public posts" (one is the subject → real match)
- `demo_dataset.json` — the manifest the demo provider reads

If the download is blocked on your network, drop your **own authorized** `.jpg`
images here (name the one you'll upload `subject.jpg`) and re-run the script.

> DEMO MODE never pretends a real web search happened. Every result here is
> tagged `DEMO DATASET`. For a genuine search, set `SEARCH_PROVIDER=google_cse`
> and configure `GOOGLE_CSE_API_KEY` / `GOOGLE_CSE_CX` in `.env`.
