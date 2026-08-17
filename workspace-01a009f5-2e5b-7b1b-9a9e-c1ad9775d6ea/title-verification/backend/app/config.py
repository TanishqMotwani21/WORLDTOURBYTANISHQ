"""
Prototype configuration for the AI Title Verification system.

All scoring weights / thresholds are PROTOTYPE DEMONSTRATION values only.
They are configurable via environment variables so the team can tune the
demo live during the hackathon without editing code.

This project is a student prototype for the SIH Internal Hackathon.
It is NOT connected to the official PRGI database.
"""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path(os.getenv("TV_DATA_DIR", BASE_DIR / "data"))
DB_PATH = Path(os.getenv("TV_DB_PATH", DATA_DIR / "titles.db"))

# ---------------------------------------------------------------------------
# Prototype demonstration weights (must sum to 1.0)
# ---------------------------------------------------------------------------
def _f(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


WEIGHTS = {
    "string_similarity": _f("TV_W_STRING", 0.25),
    "phonetic_similarity": _f("TV_W_PHONETIC", 0.20),
    "semantic_similarity": _f("TV_W_SEMANTIC", 0.35),
    "rule_violations": _f("TV_W_RULES", 0.10),
    "existing_overlap": _f("TV_W_OVERLAP", 0.10),
}

# Prototype demonstration thresholds (0-100 composite score)
THRESHOLD_REVIEW = _f("TV_T_REVIEW", 36.0)   # 36-65  -> REVIEW
THRESHOLD_HIGH = _f("TV_T_HIGH", 66.0)       # 66-100 -> HIGH RISK

# Retrieval
TOP_K_CANDIDATES = int(os.getenv("TV_TOP_K", 25))
MAX_MATCHES_SHOWN = int(os.getenv("TV_MAX_MATCHES", 9))

# Title constraints (prototype demo policy)
MIN_TITLE_LEN = int(os.getenv("TV_MIN_LEN", 3))
MAX_TITLE_LEN = int(os.getenv("TV_MAX_LEN", 80))

# ---------------------------------------------------------------------------
# Prototype DEMO rule-engine lists (NOT official PRGI policy)
# ---------------------------------------------------------------------------
import json

DEFAULT_DISALLOWED = [
    "president", "prime minister", "government", "sarkar", "reserve bank",
    "supreme court", "high court", "parliament", " Election Commission".strip().lower(),
    "cbi", "raw", "isi", "police", "army", "navy", "air force", "rbi",
    "national emblem", "ashok chakra", "constitution",
]
DISALLOWED_TERMS = [
    t.strip().lower()
    for t in json.loads(os.getenv("TV_DISALLOWED", json.dumps(DEFAULT_DISALLOWED)))
]

# Generic affixes used by the "common prefix / suffix variation" demo rule
DEMO_PREFIXES = ["the", "new", "daily", "india", "indian", "bharat"]
DEMO_SUFFIXES = ["daily", "times", "express", "news", "india", "today", "post"]

# Semantic engine: "auto" tries sentence-transformers, falls back to demo concepts
SEMANTIC_ENGINE = os.getenv("TV_SEMANTIC_ENGINE", "auto")  # auto | st | demo
ST_MODEL_NAME = os.getenv("TV_ST_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")

TEAM = {
    "name": "CODECRAFTERS",
    "project": "PSS06 — AI-Enabled Title Verification & Similarity Detection System",
    "college": "Thadomal Shahani Engineering College (TSEC)",
    "event": "Smart India Hackathon 2026 — Internal Hackathon · 18–19 August 2026",
}
