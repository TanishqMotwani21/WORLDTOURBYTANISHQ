"""
Text normalisation + simple language detection for prototype titles.
"""
from __future__ import annotations

import re
import unicodedata

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_GUJARATI = re.compile(r"[઀-૿]")

_LANG_HINTS = {
    "Hindi": {"namaskar", "pratidin", "sandhya", "samachar", "khabar", "dainik",
              "bharat", "desh", "aaj", "raat", "subah", "patrika", "varta"},
    "Marathi": {"batmi", "batmya", "saamna", "sakal", "esakal", "lokmat", "tarun",
                "sandhya", "vritta", "maharashtra", " pudhari".strip()},
    "Gujarati": {"sandesh", "gujarat", "divya", "bhaskar", "janmabhoomi"},
}


def normalize_title(title: str) -> str:
    """Lower-case, strip accents, collapse punctuation/whitespace."""
    if not title:
        return ""
    t = unicodedata.normalize("NFKC", title).strip()
    # keep Devanagari/Gujarati letters; convert fancy punctuation to spaces
    t = re.sub(r"[“”‘’\"'`´]", " ", t)
    t = re.sub(r"[&+_|/\\:;!?.,()\[\]{}*#~^$%@=<>-]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip().lower()


def tokenize(normalized: str) -> list[str]:
    return [tok for tok in normalized.split() if tok]


def detect_language(title: str, tokens: list[str]) -> str:
    """Script-based first, then small lexicon hints. Prototype heuristic."""
    if _DEVANAGARI.search(title):
        return "Hindi/Marathi (Devanagari)"
    if _GUJARATI.search(title):
        return "Gujarati"
    for lang, words in _LANG_HINTS.items():
        if any(tok in words for tok in tokens):
            return lang
    ascii_tokens = [t for t in tokens if t.isascii()]
    if ascii_tokens:
        return "English"
    return "Other"


def punctuation_stats(raw: str) -> dict:
    """Count actual punctuation/symbol characters (Unicode category P*/S*).

    Uses character categories instead of \\w so Devanagari combining marks
    (matras, virama) are never mis-counted as punctuation.
    """
    cats = [unicodedata.category(ch) for ch in raw]
    punct = [c for c in cats if c and c[0] in "PS"]
    repeated = False
    prev = None
    for ch, c in zip(raw, cats):
        if c and c[0] in "PS":
            if ch == prev:
                repeated = True
                break
            prev = ch
    return {"count": len(punct), "repeated": repeated}
