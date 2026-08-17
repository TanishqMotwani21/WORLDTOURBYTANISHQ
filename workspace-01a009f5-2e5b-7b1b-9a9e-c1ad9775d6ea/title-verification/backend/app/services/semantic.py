"""
Semantic similarity.

Two engines, selected automatically:

1. ``sentence-transformers`` (preferred when installed) — a multilingual
   embedding model + cosine similarity over title embeddings.

2. DEMO CONCEPT MATCHING (fallback) — a transparent, hand-built multilingual
   concept lexicon. Tokens are mapped to canonical meaning-concepts
   (English / romanised Hindi / Marathi / Gujarati / Devanagari) and titles
   are compared with weighted Jaccard over their concept sets.

   ==> This fallback is a PROTOTYPE DEMONSTRATION of meaning-level matching.
       It is intentionally labelled "DEMO SEMANTIC MATCHING" in the UI and
       does not claim full multilingual understanding.

The prototype never crashes if the embedding model is unavailable.
"""
from __future__ import annotations

import math
import os
import threading

from .. import config
from .string_sim import jaro_winkler_similarity

# ---------------------------------------------------------------------------
# Multilingual concept lexicon (demo fallback)
# ---------------------------------------------------------------------------
CONCEPT_GROUPS: list[set[str]] = [
    {"news", "samachar", "khabar", "khabren", "varta", "batmi", "batmya",
     "समाचार", "खबर", "खबरें", "वार्ता", "बातमी", "बातम्या"},
    {"daily", "dainik", "pratidin", "roz", "roj", "दैनिक", "प्रतिदिन", "रोज", "रोज़"},
    {"evening", "sandhya", "saanjh", "sanjh", "sham", "shaam", "संध्या", "सांझ", "शाम"},
    {"morning", "prabhat", "suprabhat", "sakal", "subah", "saver", "savera",
     "प्रभात", "सुप्रभात", "सकाळ", "सुबह", "सवेरा"},
    {"night", "ratri", "raat", "रात्रि", "रात"},
    {"star", "tara", "taara", "sitara", "तारा", "सितारा"},
    {"sun", "surya", "suraj", "ravi", "bhaskar", "सूर्य", "सूरज", "रवि", "भास्कर"},
    {"moon", "chandra", "chand", "चंद्र", "चाँद"},
    {"times", "samay", "kaal", "kal", "vel", "samaya", "समय", "काल", "वेळ"},
    {"india", "indian", "bharat", "bharatiya", "hindustan", "hindustani",
     "भारत", "भारतीय", "हिन्दुस्तान", "हिंदुस्तान"},
    {"mirror", "darpan", "दर्पण"},
    {"herald", "doot", "sandesh", "संदेश", "दूत"},
    {"voice", "vani", "wani", "awaaz", "awaz", "bol", "वाणी", "आवाज़", "आवाज", "बोल"},
    {"express", "xpress"},
    {"post", "patra", "पत्र"},
    {"mail", "daak", "डाक"},
    {"city", "nagar", "nagari", "shahar", "sheher", "शहर", "नगर", "नगरी"},
    {"light", "deep", "jyoti", "prakash", "ujala", "दीप", "ज्योति", "प्रकाश", "उजाला"},
    {"week", "weekly", "saptah", "saptahik", "hafta", "सप्ताह", "साप्ताहिक", "हफ्ता", "हफ़्ता"},
    {"month", "monthly", "masik", "mahina", "मासिक", "महीना"},
    {"world", "vishwa", "vishva", "jagat", "jag", "duniya", "विश्व", "जगत", "दुनिया"},
    {"business", "vyapar", "udyog", "vanijya", "व्यापार", "उद्योग", "वाणिज्य"},
    {"market", "bazaar", "bazar", "बाज़ार", "बाजार"},
    {"education", "shiksha", "vidya", "gyan", "शिक्षा", "विद्या", "ज्ञान"},
    {"sports", "khel", "krida", "खेल", "क्रीडा"},
    {"food", "bhojan", "anna", "khana", "भोजन", "अन्न", "खाना"},
    {"health", "swasthya", "arogya", "sehat", "स्वास्थ्य", "आरोग्य", "सेहत"},
    {"farmer", "kisan", "krishi", "shetkari", "sheti", "किसान", "कृषि", "शेतकरी", "शेती"},
    {"women", "woman", "mahila", "stri", "महिला", "स्त्री"},
    {"youth", "yuva", "yuvak", "tarun", "युवा", "युवक", "तरुण"},
    {"people", "jan", "jana", "lok", "jansatta", "जन", "लोक"},
    {"national", "rashtriya", "national", "राष्ट्रीय"},
    {"today", "aaj", "आज"},
    {"dawn", "usha", "bhor", "उषा", "भोर"},
    {"leader", "neta", "नेता"},
    {"trust", "vishwas", "bharosa", "विश्वास", "भरोसा"},
    {"truth", "satya", "sach", "sachchai", "सत्य", "सच"},
    {"power", "shakti", "satta", "शक्ति", "सत्ता"},
    {"janata", "public", "janta", "janata", "जनता"},
    {"greeting", "namaskar", "namaste", "नमस्कार", "नमस्ते"},
    {"phoenix", "phoenix", "अमरपक्षी"},          # mythic bird — spelling variants group
    {"guardian", "rakshak", "सुरक्षा", "रक्षक"},
    {"tribune", "manch", "मंच"},
    {"chronicle", "vrittant", "vrittanta", "वृत्तांत"},
    {"standard", "manak", "मानक"},
    {"pioneer", "agrani", "अग्रणी"},
    {"observer", "prekshak", "निरीक्षक"},
    {"desh", "country", "देश"},
    {"money", "paisa", "dhan", "artha", "पैसा", "धन"},
    {"film", "cinema", "chalchitra", "सिनेमा", "फिल्म"},
    {"tech", "technology", "tantra", "तंत्र", "प्रौद्योगिकी"},
    {"science", "vigyan", "विज्ञान"},
    {"law", "kanoon", "vidhi", "कानून", "विधि"},
    {"metro", "mahanagar", "महानगर"},
    {"mumbai", "bombay", "मुंबई"},
    {"delhi", "dilli", "दिल्ली"},
    {"maharashtra", "महाराष्ट्र"},
    {"gujarat", "ગુજરાત", "गुजरात"},
    {"election", "chunav", "nivadnuk", "चुनाव", "निवडणूक"},
    {"weather", "mausam", "hava", "मौसम", "हवा"},
    {"water", "jal", "paani", "pani", "जल", "पानी"},
    {"gold", "sona", "sonu", "सोना"},
    {"standard-times", "standard-times-placeholder-unused"},
]

# concept id lookup
_CONCEPT_OF: dict[str, int] = {}
for idx, group in enumerate(CONCEPT_GROUPS):
    for w in group:
        _CONCEPT_OF.setdefault(w, idx)

_LEXICON_WORDS = list(_CONCEPT_OF.keys())


def _lookup_concept(token: str) -> int | None:
    """Exact lexicon hit, else tolerate a 1-2 char misspelling (JW >= 0.90)."""
    if token in _CONCEPT_OF:
        return _CONCEPT_OF[token]
    best, best_score = None, 0.0
    for word in _LEXICON_WORDS:
        if abs(len(word) - len(token)) > 2 or not word.isascii() or not token.isascii():
            continue
        s = jaro_winkler_similarity(token, word)
        if s > best_score:
            best, best_score = word, s
    if best_score >= 0.90 and best is not None:
        return _CONCEPT_OF[best]
    return None


def concept_set(tokens: list[str]) -> set[int]:
    out = set()
    for t in tokens:
        c = _lookup_concept(t)
        if c is not None:
            out.add(c)
    return out


def _semantic_units(tokens: list[str]) -> tuple[set[int], set[str]]:
    """Concept ids + raw fallback tokens (so unmatched words still cost score)."""
    concepts, raw = set(), set()
    for t in tokens:
        c = _lookup_concept(t)
        if c is None:
            raw.add(t)
        else:
            concepts.add(c)
    return concepts, raw


def demo_semantic_similarity(tokens_a: list[str], tokens_b: list[str]) -> dict:
    """
    Weighted Jaccard over meaning units: mapped concept-ids plus raw tokens
    for words outside the demo lexicon (so unmatched wording lowers score).
    """
    ca, ra = _semantic_units(tokens_a)
    cb, rb = _semantic_units(tokens_b)
    ua, ub = ca.union(("t", r) for r in ra), cb.union(("t", r) for r in rb)
    shared_concepts = ca & cb
    union = ua | ub
    if not union:
        return {"score": 0.0, "shared_concepts": [], "match": False}
    score = len(ua & ub) / len(union)
    labels = []
    for cid in sorted(shared_concepts):
        rep = sorted(CONCEPT_GROUPS[cid],
                     key=lambda w: (not w.isascii(), len(w)))[0]
        labels.append(rep)
    return {
        "score": round(score, 4),
        "shared_concepts": labels,
        "match": len(shared_concepts) > 0 and score >= 0.34,
    }


# ---------------------------------------------------------------------------
# Optional sentence-transformers engine
# ---------------------------------------------------------------------------
class STEngine:
    def __init__(self):
        self.available = False
        self.error: str | None = None
        self._model = None
        self._cache: dict[str, list[float]] = {}
        self._lock = threading.Lock()
        try:
            from sentence_transformers import SentenceTransformer  # noqa: F401
            self._load()
        except Exception as exc:  # pragma: no cover - environment dependent
            self.error = f"{type(exc).__name__}: {exc}"

    def _load(self):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(config.ST_MODEL_NAME)
        self.available = True

    def encode(self, text: str) -> list[float]:
        with self._lock:
            if text in self._cache:
                return self._cache[text]
        vec = self._model.encode([text], normalize_embeddings=True)[0].tolist()
        with self._lock:
            self._cache[text] = vec
        return vec

    def cosine(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1.0
        nb = math.sqrt(sum(x * x for x in b)) or 1.0
        return dot / (na * nb)


_engine: STEngine | None = None
_engine_tried = False


def get_st_engine() -> STEngine | None:
    global _engine, _engine_tried
    if _engine_tried:
        return _engine
    _engine_tried = True
    if config.SEMANTIC_ENGINE in ("auto", "st"):
        try:
            _engine = STEngine()
            if not _engine.available:
                _engine = None
        except Exception:
            _engine = None
    return _engine


def semantic_status() -> dict:
    eng = get_st_engine()
    if eng and eng.available:
        return {"engine": "sentence-transformers+demo-lexicon", "model": config.ST_MODEL_NAME,
                "fallback": False,
                "label": f"Multilingual embeddings ({config.ST_MODEL_NAME}) + demo concept lexicon"}
    return {"engine": "demo-concept", "model": None, "fallback": True,
            "label": "DEMO SEMANTIC MATCHING (prototype concept lexicon)"}


def semantic_similarity(tokens_a: list[str], tokens_b: list[str],
                        raw_a: str, raw_b: str) -> dict:
    """
    Unified semantic API.

    When the sentence-transformers model is available we use multilingual
    embeddings as the primary signal, supplemented by the transparent demo
    concept lexicon (prototype hybrid — catches transliterated/demo pairs the
    small model under-rates).  Without the model, demo concepts alone are
    used and clearly labelled.
    """
    demo = demo_semantic_similarity(tokens_a, tokens_b)
    eng = get_st_engine()
    if eng and eng.available:
        try:
            va, vb = eng.encode(raw_a), eng.encode(raw_b)
            cos = max(0.0, min(1.0, eng.cosine(va, vb)))
            hybrid = max(cos, demo["score"])
            return {
                "score": round(hybrid, 4),
                "engine": "sentence-transformers+demo-lexicon",
                "embedding_score": round(cos, 4),
                "concept_boosted": demo["score"] > cos,
                "shared_concepts": demo.get("shared_concepts", []),
                "match": hybrid >= 0.5 or demo["match"],
            }
        except Exception:
            pass  # graceful drop to demo engine
    demo["engine"] = "demo-concept"
    return demo
