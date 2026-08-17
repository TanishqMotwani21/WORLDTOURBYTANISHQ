# Deployment — AI Title Verification (PSS06 · Team CODECRAFTERS · TSEC)

> Internal Hackathon demo: 18–19 August. Prototype / Demonstration —
> representative demo dataset, no official PRGI connection.

---

## 1. FINAL PUBLIC HTTPS URL

**Right now (live):** see [`PUBLIC_URL.txt`](./PUBLIC_URL.txt) — currently:

```
https://tons-sets-herald-exterior.trycloudflare.com
```

**Important honesty note:** the environment this was built in (Arena sandbox) has
**no connected hosting accounts** (checked: no Render/Railway/Vercel/Netlify/Fly/HF/Cloudflare
credentials, no CLIs, no git remotes). Therefore the only URL I can mint *from inside this
session* is a Cloudflare quick tunnel, which lives only **while this sandbox session runs** —
a watchdog process keeps it alive during the session. **For a URL that persists after this
session ends and through 18–19 August, one team member must connect one free account** —
~5 minutes, instructions in §5. The project is 100% prepared for it; nothing needs changing.

## 2. DEPLOYMENT PLATFORM

* **Current live URL:** Cloudflare quick tunnel → app running in the Arena sandbox (session-bound).
* **Recommended permanent platform:** **Render** (Blueprint included: `render.yaml`) or any
  Docker host via the included `Dockerfile` (Railway / Fly.io / Hugging Face Spaces / a VM).

## 3. FRONTEND URL

Same origin as the service — the FastAPI app serves the production React build
(`frontend/dist`) itself: `<BASE>/` (pages: `#/dashboard`, `#/verify`, `#/similar`,
`#/history`, `#/how-it-works`).

## 4. BACKEND URL

Same origin: `<BASE>/api/...` — single origin ⇒ **no CORS issues at all**.
Health endpoint: `<BASE>/api/health`.

## 5. Exact commands / configuration used to deploy

### Current session (what is running right now)
```bash
# app (single origin, production build)
pip install -r requirements.txt
cd frontend && npm ci && npm run build && cd ..
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# public exposure
cloudflared tunnel --url http://localhost:8000 --no-autoupdate
```

### Permanent deployment — Option A: Render (5 minutes, simplest)
1. Push this folder to a GitHub repo:
   ```bash
   git init && git add -A && git commit -m "PSS06 AI Title Verification"
   git remote add origin https://github.com/<your-user>/title-verification.git
   git push -u origin main
   ```
2. render.com → sign up (free, Google/GitHub login) → **New → Blueprint** → select the repo.
   Render reads `render.yaml` automatically:
   * build: `pip install -r requirements.txt && cd frontend && npm ci && npm run build`
   * start: `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   * health check: `/api/health`
3. You get `https://ai-title-verification.onrender.com` — permanent HTTPS URL.

### Option B: anywhere with Docker (Railway / Fly / HF Spaces / VM)
```bash
docker build -t title-verification .          # default light tier (≤512MB RAM)
docker run -p 8000:8000 title-verification
# 2GB+ machines: docker build --build-arg INSTALL_ST=1 -t title-verification .
```

### Environment variables (all optional — no secrets needed)
| Var | Default | Purpose |
|---|---|---|
| `PORT` | 8000 | injected by platform |
| `TV_SEMANTIC_ENGINE` | auto | `auto`/`st`/`demo` |
| `TV_W_*`, `TV_T_*` | spec values | prototype weights/thresholds |
| `TV_DATA_DIR`/`TV_DB_PATH` | ./data | SQLite location |

No API keys are required for any verification feature.

## 6. Will the URL remain available after this Arena session ends?

* **Tunnel URL (current): NO** — it dies with the sandbox. A watchdog
  auto-recreates it during the session and rewrites `PUBLIC_URL.txt` if it changes.
* **Render/Docker URL: YES** — permanent once the team completes §5-A (one account, 5 min).

## 7. Limitations to know before 18–19 August

1. The anonymous tunnel is session-bound (see above) — do not rely on it for judging day.
2. On free/starter tiers (512 MB) the heavy multilingual embedding model is skipped and the
   app uses its labelled **DEMO SEMANTIC MATCHING** engine — by design, never crashes;
   on 2GB+ (`INSTALL_ST=1`) the full `sentence-transformers` engine runs.
3. **SQLite on ephemeral platforms:** the demo dataset (193 titles) re-seeds automatically on
   every boot, so the *demo dataset is safe*. **Submission history resets on redeploy/restart**
   unless a disk is attached (Render: add a persistent disk mounted at `/app/data`; the app
   already uses `TV_DATA_DIR`). This is acceptable for a live prototype demo.
4. Free Render instances cold-start after idle (~30–60 s first-load) — warm it before presenting.

## 8. HOW TO DEMO (team script)

1. Open the URL, land on **Dashboard** (reference scale ~160,000 vs 193-title demo index).
2. Sidebar → **Verify Title** → click example chip **“Indian Xpress”** → **VERIFY TITLE** →
   watch the 7-step pipeline → **HIGH RISK** with `Indian Express` as top match.
3. Point to the indicators: String (Levenshtein + Jaro-Winkler), Phonetic (Soundex/Metaphone),
   Semantic (multilingual) — call them *prototype similarity indicators*.
4. **“Foenix”** → phonetic banner (Metaphone FNKS match with Phoenix, same Soundex family).
5. **“Daily Evening”** → meaning-level banner, `Pratidin Sandhya` in closest matches.
6. Click a match card → “why it matched” per-signal bars.
7. **MODIFY TITLE** → change to something distinct → **RESUBMIT** → show
   Previous → Modified → New strip and the level drop.
8. Sidebar → **Submission History** → reopen any analysis. **How It Works** → 7-layer
   architecture + live weights/thresholds.
9. Reset between runs if needed: delete `data/titles.db` (auto-reseeds on restart).
