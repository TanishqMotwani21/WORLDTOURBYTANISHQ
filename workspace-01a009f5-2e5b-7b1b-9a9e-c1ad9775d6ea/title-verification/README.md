# AI-Enabled Title Verification & Similarity Detection System — PSS06

> **Prototype / Demonstration** — Smart India Hackathon 2026 · **Internal Hackathon** · 18–19 August 2026
> Team **CODECRAFTERS** — Thadomal Shahani Engineering College (TSEC)

**Prototype for Internal Hackathon Demonstration** — uses a representative demo dataset and
prototype scoring logic. **Not connected to the official PRGI database.** No official verification
probability, accuracy, benchmark, F1 score or government-system access is claimed anywhere in this
project.

| | |
|---|---|
| Problem statement | **PSS06** — AI-Enabled Title Verification & Similarity Detection System |
| Team | Tanishq Motwani (Computer Engineering) · Aayush Chawala (Computer Engineering) · Lavina Chugh (Computer Engineering) · Pooja Hinduja (Artificial Intelligence & Data Science) · Mahek Goklani (Computer Engineering) · Kanisha Bhatia (Computer Engineering) |
| Real-world context | ~160,000 existing registered titles (see *Scalability* below) |

## What it does

Entering a proposed publication title runs a **real, working multi-layer verification pipeline**:

```
ENTER TITLE → TEXT NORMALIZATION → RULE-BASED VALIDATION → STRING SIMILARITY
→ PHONETIC SIMILARITY → SEMANTIC SIMILARITY → CANDIDATE RETRIEVAL
→ VERIFICATION ASSESSMENT → EXPLAINABLE RESULT → MODIFY → RESUBMIT
```

* **String similarity** — Levenshtein distance + Jaro-Winkler (pure-Python implementations)
  e.g. `Indian Express` ↔ `Indian Xpress`
* **Phonetic similarity** — Soundex + Metaphone (pure-Python implementations)
  e.g. `Phoenix` ↔ `Foenix` (both map to Metaphone `FNKS`)
* **Semantic similarity** — multilingual Sentence-Transformers embeddings + cosine similarity
  (`paraphrase-multilingual-MiniLM-L12-v2`) supplemented by a transparent demo concept lexicon;
  if the embedding model cannot be installed the system automatically falls back to the lexicon
  alone, clearly labelled **DEMO SEMANTIC MATCHING**, and never crashes.
  e.g. `Daily Evening` ↔ `Pratidin Sandhya`
* **Rule engine** — demo policy checks (disallowed demo terms, common prefix/suffix variations,
  periodicity-related patterns, existing-title combinations, punctuation/length rules).
  These are **prototype demo rules, not official PRGI policy**.
* **Candidate retrieval** — hybrid top-K pre-rank over a local index (string + concept overlap),
  then detailed analysis only on candidates. This retrieval slot is where a vector index such as
  FAISS is dropped in at full scale.
* **Explainable result** — every flag is generated from the actual computed signals.
* **Modify → Resubmit** — the feedback loop is fully functional and shows previous → new result.

## Prototype decision logic (transparent demonstration values)

| Signal | Weight |
|---|---|
| String similarity | 25% |
| Phonetic similarity | 20% |
| Semantic similarity | 35% |
| Rule violations | 10% |
| Existing-title overlap | 10% |

Thresholds: **0–35 LOW RISK · 36–65 REVIEW · 66–100 HIGH RISK**.
All weights/thresholds are environment-variable configurable (`TV_W_STRING`, `TV_T_HIGH`, …).

## Tech stack

* **Frontend:** React 18 + React Router + Vite (custom dark-navy/cyan design system, zero external UI kits)
* **Backend:** Python · FastAPI · Pydantic (structured JSON APIs, CORS, input validation)
* **Database:** SQLite (`data/titles.db`) — demo dataset + submission history
* **NLP:** sentence-transformers *(optional, graceful fallback)*

## Project structure

```
title-verification/
├── backend/app/
│   ├── main.py            # FastAPI routes (/api/verify, /api/resubmit, /api/similar, /api/history, /api/health…)
│   ├── config.py          # weights, thresholds, demo rules — env-configurable
│   ├── db.py              # SQLite schema + seed + history persistence
│   ├── seed_data.py       # Prototype Demo Dataset (~190 invented representative titles)
│   └── services/
│       ├── normalize.py   # Unicode-aware normalisation + language detect
│       ├── string_sim.py  # Levenshtein, Jaro-Winkler
│       ├── phonetic.py    # Soundex, Metaphone
│       ├── semantic.py    # ST embeddings ↔ demo concept lexicon (auto fallback)
│       ├── rules.py       # demo rule engine
│       └── verifier.py    # multi-layer orchestration + scoring + explanations
├── frontend/              # React SPA (Vite) — built to frontend/dist, served by FastAPI
├── data/                  # SQLite database (auto-created)
├── tests/                 # API acceptance tests + UI flow tests
├── requirements.txt
├── .env.example
└── start.sh               # one-command local run
```

## Running locally

**1. Backend**

```bash
pip install -r requirements.txt
# optional, enables multilingual embedding engine (CPU wheels):
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers

cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**2. Frontend (build once, served by the backend)**

```bash
cd frontend
npm install
npm run build          # outputs frontend/dist — FastAPI serves it at /
```

Open **http://localhost:8000**. For frontend development with hot-reload:
`npm run dev` (Vite on :5173 proxies `/api` to :8000).

`./start.sh` does all of the above automatically.

**Database initialisation:** automatic on first start — schema is created and the
Prototype Demo Dataset is seeded into `data/titles.db` (delete the file to reset).

## Environment variables (`.env.example`)

None are required. Optional knobs: scoring weights/thresholds, demo disallowed-term list,
semantic engine selection (`TV_SEMANTIC_ENGINE=auto|st|demo`), CORS origins, and an optional
external AI key slot. **The core verification system needs no API keys and runs fully offline.**

## Testing

```bash
python tests/run_tests.py                    # 13 API acceptance checks (all 7 brief scenarios)
cd frontend && node tests/ui_render.test.mjs # headless render smoke test (jsdom)
node tests/ui_flow.test.mjs                  # full UI flow test, needs the server running
```

The acceptance suite verifies: high string similarity (`Indian Xpress`), spelling variant
(`Namascar`), phonetic match (`Foenix`), cross-lingual semantic match (`Daily Evening`),
unrelated LOW RISK, demo rule violation detection, Modify→Resubmit recalculation, history,
similar lookup, and graceful error handling.

## Deployment

The app is a **single self-contained FastAPI service** (API + built React SPA + SQLite):

1. `pip install -r requirements.txt`
2. `cd frontend && npm ci && npm run build`
3. `cd ../backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`

Any host that runs Python (Render, Railway, a VM, Hugging Face Spaces…) serves the whole product
from one port. Skip step "sentence-transformers" install for a lightweight deploy — the labelled
demo semantic engine takes over automatically.

## Prototype limitations (honest scope)

* Representative **demo dataset** only — no official PRGI records, APIs or verification.
* “Risk” is a **prototype similarity indicator**, not an official approval probability.
* Language detection is a small script/lexicon heuristic.
* The demo concept lexicon covers demonstration vocabulary, not general multilingual understanding.
* The ~160,000 figure describes the **real-world context** the architecture targets; the prototype
  intentionally does not fabricate 160,000 fake rows.
