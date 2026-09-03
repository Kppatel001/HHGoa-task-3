# Connecting Firebase (durable records & history)

By default the backend stores blockchain records + verification history in a
local SQLite file. On serverless hosts (Vercel) that file is ephemeral, so the
History / Blockchain Records pages lose data between restarts. Point the app at
a **Firebase Realtime Database** to make them durable — no SDK needed, just a URL.

## Steps
1. Go to https://console.firebase.google.com/ → **Add project** (or pick one).
2. **Build → Realtime Database → Create Database** → pick a region → start in
   **Test mode** (open rules) for a demo, or set rules later.
3. Copy the database URL, e.g. `https://<project>-default-rtdb.firebaseio.com`.
4. Set env vars on the backend (Vercel project → Settings → Environment Variables,
   or Render → Environment):
   - `FIREBASE_DB_URL = https://<project>-default-rtdb.firebaseio.com`
   - `FIREBASE_DB_SECRET =` *(leave empty in Test mode; set a token if your rules require auth)*
5. Redeploy. Verify: `GET /api/status` → `components.database.store` shows
   `firebase-rtdb`, and `GET /api/blockchain/records` → `"store":"firebase"`.

Records are written under `/records` on each verified scan and read back for the
History and Blockchain Records pages.

> Test mode leaves the database world-readable/writable. Before a real public
> launch, lock it down with Realtime Database rules and use `FIREBASE_DB_SECRET`.
