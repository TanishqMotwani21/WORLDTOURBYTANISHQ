"""SQLite persistence for the prototype (demo dataset + submission history)."""
from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager

from . import config
from .seed_data import SEED_TITLES
from .services.normalize import normalize_title

_SCHEMA = """
CREATE TABLE IF NOT EXISTS titles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    normalized TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'English',
    category TEXT DEFAULT '',
    region TEXT DEFAULT '',
    UNIQUE(title, language)
);
CREATE INDEX IF NOT EXISTS idx_titles_norm ON titles(normalized);

CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    normalized TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'auto',
    language_detected TEXT DEFAULT '',
    description TEXT DEFAULT '',
    parent_id INTEGER,
    risk_level TEXT NOT NULL,
    risk_score REAL NOT NULL,
    signals TEXT NOT NULL,          -- JSON blob of all computed signals
    result TEXT NOT NULL,           -- JSON blob of the full response
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sub_created ON submissions(created_at DESC);
"""


@contextmanager
def get_conn():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> int:
    """Create schema + seed the demo dataset (idempotent)."""
    with get_conn() as conn:
        conn.executescript(_SCHEMA)
        cur = conn.execute("SELECT COUNT(*) AS c FROM titles")
        if cur.fetchone()["c"] == 0:
            conn.executemany(
                "INSERT OR IGNORE INTO titles (title, normalized, language, category, region)"
                " VALUES (?,?,?,?,?)",
                [(t, normalize_title(t), lang, cat, reg) for (t, lang, cat, reg) in SEED_TITLES],
            )
        return conn.execute("SELECT COUNT(*) AS c FROM titles").fetchone()["c"]


def fetch_all_titles() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, normalized, language, category, region FROM titles"
        ).fetchall()
    return [dict(r) for r in rows]


def save_submission(record: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO submissions
               (title, normalized, language, language_detected, description,
                parent_id, risk_level, risk_score, signals, result, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                record["title"], record["normalized"], record["language"],
                record.get("language_detected", ""), record.get("description", ""),
                record.get("parent_id"), record["risk_level"], record["risk_score"],
                json.dumps(record["signals"]), json.dumps(record["result"]),
                record.get("created_at", time.time()),
            ),
        )
        return cur.lastrowid


def list_submissions(limit: int = 200) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT id, title, language_detected, risk_level, risk_score,
                      created_at, parent_id FROM submissions
               ORDER BY created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_submission(sub_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM submissions WHERE id = ?", (sub_id,)
        ).fetchone()
    return dict(row) if row else None
