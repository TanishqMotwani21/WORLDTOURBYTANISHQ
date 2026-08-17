"""
FastAPI application — AI Title Verification & Similarity Detection (PSS06).

Team CODECRAFTERS · Thadomal Shahani Engineering College (TSEC)
Smart India Hackathon 2026 — Internal Hackathon (18–19 August 2026)

Prototype / Demonstration — NOT connected to the official PRGI database.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config, db
from .services import verifier
from .services.semantic import semantic_status

app = FastAPI(
    title="AI Title Verification API (Prototype)",
    version="1.0.0",
    description="Prototype / Demonstration — representative demo dataset, not the official PRGI database.",
)

# CORS — permissive only when requested explicitly (local dev convenience)
_origins = os.getenv("TV_CORS_ORIGINS", "")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins.split(",") if o.strip()] or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory demo title index (loaded once at startup; refreshed on change)
# ---------------------------------------------------------------------------
_INDEX: list[dict] = []


def _reload_index() -> int:
    global _INDEX
    _INDEX = db.fetch_all_titles()
    return len(_INDEX)


@app.on_event("startup")
def _startup():
    db.init_db()
    _reload_index()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class VerifyRequest(BaseModel):
    title: str = Field(..., max_length=500)
    language: str = Field("auto", max_length=40)
    description: str = Field("", max_length=500)
    parent_id: int | None = None


class ResubmitRequest(BaseModel):
    parent_id: int
    title: str = Field(..., max_length=500)
    language: str = Field("auto", max_length=40)
    description: str = Field("", max_length=500)


class SimilarRequest(BaseModel):
    title: str = Field(..., max_length=500)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _friendly_error(status: int, message: str, hint: str = ""):
    return JSONResponse(
        status_code=status,
        content={"error": True, "message": message, "hint": hint,
                 "disclaimer": "Prototype error handling — no crash, no silent failure."},
    )


def _persist_and_respond(result: dict, parent_id: int | None) -> dict:
    sub_id = db.save_submission({
        "title": result["title"],
        "normalized": result["normalized"],
        "language": result["language"],
        "language_detected": result["language_detected"],
        "description": result.get("description", ""),
        "parent_id": parent_id,
        "risk_level": result["risk"]["level"],
        "risk_score": result["risk"]["score"],
        "signals": result["signals"],
        "result": result,
    })
    result["id"] = sub_id
    result["created_at"] = time.time()
    result["result_saved"] = True
    return result


_VALID_LANGS = {"auto", "English", "Hindi", "Marathi", "Gujarati", "Other",
                "english", "hindi", "marathi", "gujarati", "other"}


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    sem = semantic_status()
    return {
        "status": "ok",
        "version": "1.0.0",
        "demo_titles": len(_INDEX),
        "database": "sqlite",
        "semantic_engine": sem,
        "reference_scale": "~160,000 titles (real-world PSS06 context)",
        "prototype": True,
        "disclaimer": ("Prototype for Internal Hackathon Demonstration — representative "
                       "demo dataset, prototype scoring logic; no official PRGI connection."),
    }


@app.get("/api/config")
def get_config():
    return {
        "weights": config.WEIGHTS,
        "thresholds": {"review": config.THRESHOLD_REVIEW, "high": config.THRESHOLD_HIGH},
        "disallowed_terms_demo": config.DISALLOWED_TERMS,
        "note": "Prototype demonstration weights & demo rules — NOT official PRGI policy.",
    }


@app.post("/api/verify")
def verify(req: VerifyRequest, request: Request):
    raw = (req.title or "").strip()
    if not raw:
        return _friendly_error(400, "Title is empty.",
                               "Enter a proposed title before verification.")
    if len(raw) > config.MAX_TITLE_LEN * 6:
        return _friendly_error(400, "Title is far too long.",
                               f"Keep titles under {config.MAX_TITLE_LEN} characters for the demo.")
    if req.language not in _VALID_LANGS:
        return _friendly_error(400, f"Unsupported language option “{req.language}”.",
                               "Choose Auto Detect, English, Hindi, Marathi, Gujarati or Other.")
    previous = None
    if req.parent_id:
        parent = db.get_submission(req.parent_id)
        if not parent:
            return _friendly_error(404, "Parent submission not found.",
                                   "It may have been cleared from the local history.")
        previous = parent
    try:
        result = verifier.run_verification(
            raw, req.language, req.description, titles_index=_INDEX, previous=previous)
        return _persist_and_respond(result, req.parent_id)
    except Exception as exc:  # never crash the demo
        return _friendly_error(500, "Verification engine error.",
                               f"{type(exc).__name__}: {exc}")


@app.post("/api/resubmit")
def resubmit(req: ResubmitRequest):
    parent = db.get_submission(req.parent_id)
    if not parent:
        return _friendly_error(404, "Original submission not found.",
                               "Verify the title first, then modify & resubmit.")
    raw = (req.title or "").strip()
    if not raw:
        return _friendly_error(400, "Title is empty.",
                               "Enter a modified title before resubmitting.")
    try:
        result = verifier.run_verification(
            raw, req.language, req.description, titles_index=_INDEX, previous=parent)
        return _persist_and_respond(result, req.parent_id)
    except Exception as exc:
        return _friendly_error(500, "Verification engine error.",
                               f"{type(exc).__name__}: {exc}")


@app.get("/api/similar")
def similar(title: str = Query(..., min_length=1, max_length=500)):
    from .services import verifier as v
    from .services.normalize import normalize_title, tokenize
    norm = normalize_title(title)
    if not norm:
        return _friendly_error(400, "Title is empty after normalisation.", "")
    tokens = tokenize(norm)
    scored = []
    for rec in _INDEX:
        from .services.string_sim import combined_string_similarity
        s = combined_string_similarity(norm, rec["normalized"])
        if s >= 0.30:
            from .services.phonetic import title_phonetic_similarity
            from .services.semantic import semantic_similarity
            ph = title_phonetic_similarity(tokens, rec["normalized"].split())
            se = semantic_similarity(tokens, rec["normalized"].split(), norm, rec["normalized"])
            kinds = v._classify_match(s, ph, se)
            scored.append({
                "title": rec["title"], "language": rec["language"],
                "category": rec.get("category", ""),
                "similarity": round(100 * (0.4 * s + 0.25 * ph["score"] + 0.35 * se["score"]), 1),
                "match_types": kinds, "string": round(100 * s, 1),
                "phonetic": round(100 * ph["score"], 1),
                "semantic": round(100 * se["score"], 1),
            })
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return {"query": title, "count": len(scored[:10]), "results": scored[:10],
            "note": "Prototype demo dataset similarity lookup."}


@app.get("/api/history")
def history(limit: int = Query(200, ge=1, le=500)):
    items = db.list_submissions(limit)
    for it in items:
        it["created_at_iso"] = time.strftime("%Y-%m-%d %H:%M:%S",
                                             time.localtime(it["created_at"]))
    return {"count": len(items), "items": items}


@app.get("/api/history/{sub_id}")
def history_item(sub_id: int):
    row = db.get_submission(sub_id)
    if not row:
        return _friendly_error(404, "Submission not found.", "It may have been removed.")
    result = json.loads(row["result"])
    result["id"] = row["id"]
    result["created_at"] = row["created_at"]
    result["created_at_iso"] = time.strftime("%Y-%m-%d %H:%M:%S",
                                             time.localtime(row["created_at"]))
    if row.get("parent_id"):
        parent = db.get_submission(row["parent_id"])
        if parent:
            result["previous_result"] = {
                "id": parent["id"], "title": parent["title"],
                "risk_level": parent["risk_level"], "risk_score": parent["risk_score"],
            }
            result["resubmission"] = True
    return result


@app.get("/api/dataset")
def dataset():
    return {
        "count": len(_INDEX),
        "titles": _INDEX,
        "note": ("Prototype Demo Dataset — representative invented titles. "
                 "NOT official PRGI records."),
    }


# ---------------------------------------------------------------------------
# Static frontend (React build) — served when present
# ---------------------------------------------------------------------------
_FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        # API routes already handled above; anything else → React index.html
        if full_path.startswith("api/"):
            return _friendly_error(404, "Unknown API route.", "")
        candidate = _FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_FRONTEND_DIST / "index.html")
