"""
Core verification orchestration — the multi-layer prototype pipeline.

  1. Text Normalisation
  2. Rule-Based Validation          (demo rules)
  3. String Similarity              (Levenshtein + Jaro-Winkler)
  4. Phonetic Similarity            (Soundex + Metaphone)
  5. Semantic Similarity            (multilingual ST embeddings, or demo concepts)
  6. Candidate Retrieval            (top-K over the demo index)
  7. Verification Assessment        (transparent weighted prototype score)

Every signal is reported so the result remains explainable.
"""
from __future__ import annotations

import time

from .. import config
from .normalize import normalize_title, tokenize, detect_language
from .phonetic import title_phonetic_similarity
from .rules import evaluate_rules
from .semantic import semantic_similarity, semantic_status
from .string_sim import combined_string_similarity


def _risk_level(score: float) -> str:
    if score < config.THRESHOLD_REVIEW:
        return "LOW RISK"
    if score < config.THRESHOLD_HIGH:
        return "REVIEW"
    return "HIGH RISK"


def _classify_match(string_s: float, phon: dict, sem: dict) -> list[str]:
    kinds = []
    if string_s >= 0.85:
        kinds.append("String")
    if phon["match_detected"] and phon["score"] >= 0.5:
        kinds.append("Phonetic")
    if sem["match"]:
        kinds.append("Semantic")
    if not kinds:
        if string_s >= 0.60:
            kinds.append("String")
    return kinds


def run_verification(title: str, language: str = "auto",
                     description: str = "", titles_index: list[dict] | None = None,
                     previous: dict | None = None) -> dict:
    t0 = time.perf_counter()
    pipeline = []

    def step(name, detail="OK"):
        pipeline.append({"step": name, "status": "done", "detail": detail,
                         "ms": round((time.perf_counter() - ts) * 1000, 1)})

    # -- 1 · Normalisation ---------------------------------------------------
    ts = time.perf_counter()
    normalized = normalize_title(title)
    tokens = tokenize(normalized)
    step("Text Normalization", f"“{normalized or '—'}”")

    # -- 2 · Rule-based validation (demo rules) -------------------------------
    ts = time.perf_counter()
    db_norm = [(t["normalized"], t["title"]) for t in (titles_index or [])]
    rules = evaluate_rules(title, normalized, tokens, db_norm)
    step("Rule-Based Validation",
         f"{len(rules['violations'])} demo issue(s)" if rules["violations"] else "No demo policy issue detected")

    # -- language detection ----------------------------------------------------
    language_detected = detect_language(title, tokens) if language in ("auto", "", None) else language

    # -- 6a · Candidate retrieval (top-K cheap pre-rank) -----------------------
    # Hybrid retrieval: fast string pre-rank UNION demo-concept overlap so that
    # meaning-level candidates with different wording still reach deep analysis
    # (this is the slot a vector index like FAISS fills at full scale).
    ts = time.perf_counter()
    from .semantic import demo_semantic_similarity
    candidates = []
    for rec in (titles_index or []):
        rec_norm = rec["normalized"]
        quick = combined_string_similarity(normalized, rec_norm)
        concept = demo_semantic_similarity(tokens, tokenize(rec_norm))["score"]
        if quick >= 0.30 or concept >= 0.34:
            candidates.append((max(quick, concept * 0.9), rec))
    candidates.sort(key=lambda x: x[0], reverse=True)
    top = candidates[: config.TOP_K_CANDIDATES]

    # -- 3/4/5 · Detailed similarity layers over candidates --------------------
    detailed = []
    for quick, rec in top:
        s_ts = time.perf_counter()
        string_s = combined_string_similarity(normalized, rec["normalized"])
        rec_tokens = tokenize(rec["normalized"])
        phon = title_phonetic_similarity(tokens, rec_tokens)
        sem = semantic_similarity(tokens, rec_tokens, normalized, rec["normalized"])
        detailed.append({
            "title": rec["title"], "language": rec["language"],
            "category": rec.get("category", ""), "region": rec.get("region", ""),
            "string": round(string_s, 4), "phonetic": phon, "semantic": sem,
            "ms": round((time.perf_counter() - s_ts) * 1000, 1),
        })

    step("String Similarity", f"Levenshtein + Jaro-Winkler over {len(top)} candidate(s)")
    pipeline.append({"step": "Phonetic Similarity", "status": "done",
                     "detail": "Soundex + Metaphone token matching", "ms": 0})
    pipeline.append({"step": "Semantic Similarity", "status": "done",
                     "detail": semantic_status()["label"], "ms": 0})
    step("Candidate Retrieval", f"Top {len(top)} of {len(titles_index or [])} demo titles")

    # -- signal aggregation -----------------------------------------------------
    def _best(key_fn, default=0.0):
        return max((key_fn(d) for d in detailed), default=default)

    sig_string = _best(lambda d: d["string"])
    sig_phon = _best(lambda d: d["phonetic"]["score"])
    sig_sem = _best(lambda d: d["semantic"]["score"])
    sig_rules = rules["score"]

    # existing-title overlap ------------------------------------------------
    exact = None
    subset_of = None
    for d in detailed:
        if d["string"] >= 0.995:
            exact = d
            break
    if exact is None:
        tset = set(tokens)
        for d in detailed:
            rt = set(tokenize(next(r["normalized"] for r in (titles_index or []) if r["title"] == d["title"])))
            if tset and rt and (tset.issubset(rt) or rt.issubset(tset)):
                subset_of = d
                break
    if exact:
        sig_overlap = 1.0
    elif subset_of:
        sig_overlap = 0.6
    else:
        sig_overlap = 0.0

    # -- 7 · Verification assessment (transparent prototype weights) ----------
    ts = time.perf_counter()
    w = config.WEIGHTS
    composite = (
        100.0 * (
            w["string_similarity"] * sig_string
            + w["phonetic_similarity"] * sig_phon
            + w["semantic_similarity"] * sig_sem
            + w["rule_violations"] * sig_rules
            + w["existing_overlap"] * sig_overlap
        )
    )
    composite = round(composite, 1)
    level = _risk_level(composite)
    step("Verification Assessment",
         f"Composite prototype score {composite}/100 → {level}")

    # -- best matches for the "Similar Titles" panel ---------------------------
    def _composite_match(d):
        return round(100 * (0.38 * d["string"] + 0.20 * d["phonetic"]["score"]
                            + 0.42 * d["semantic"]["score"]), 1)

    for d in detailed:
        d["similarity"] = _composite_match(d)
        d["match_types"] = _classify_match(d["string"], d["phonetic"], d["semantic"])

    matches = sorted(detailed, key=lambda d: d["similarity"], reverse=True)
    matches = [m for m in matches
               if m["similarity"] >= 25 or m["match_types"]][: config.MAX_MATCHES_SHOWN]

    # -- explanations ------------------------------------------------------------
    explanations = _explain(
        level, detailed, rules, exact, subset_of,
        sig_string, sig_phon, sig_sem, language_detected,
    )

    total_ms = round((time.perf_counter() - t0) * 1000, 1)
    sem_stat = semantic_status()

    result = {
        "title": title,
        "normalized": normalized,
        "language": language or "auto",
        "language_detected": language_detected,
        "description": description,
        "risk": {"level": level, "score": composite,
                 "thresholds": {"low": f"0–{int(config.THRESHOLD_REVIEW - 1)}",
                                "review": f"{int(config.THRESHOLD_REVIEW)}–{int(config.THRESHOLD_HIGH - 1)}",
                                "high": f"{int(config.THRESHOLD_HIGH)}–100"}},
        "signals": {
            "string_similarity": {"score": round(100 * sig_string, 1),
                                  "algorithm": "Levenshtein + Jaro-Winkler",
                                  "best_match": _best_title(detailed, lambda d: d["string"])},
            "phonetic_similarity": {"score": round(100 * sig_phon, 1),
                                    "algorithm": "Soundex + Metaphone",
                                    "best_match": _best_title(detailed, lambda d: d["phonetic"]["score"]),
                                    "detail": _best_phon_detail(detailed)},
            "semantic_similarity": {"score": round(100 * sig_sem, 1),
                                    "algorithm": sem_stat["label"],
                                    "engine": sem_stat["engine"],
                                    "best_match": _best_title(detailed, lambda d: d["semantic"]["score"]),
                                    "detail": _best_sem_detail(detailed)},
            "rule_violations": {"score": round(100 * sig_rules, 1),
                                "count": len(rules["violations"]),
                                "violations": rules["violations"]},
            "existing_overlap": {"score": round(100 * sig_overlap, 1),
                                 "exact_duplicate": exact["title"] if exact else None,
                                 "contained_in": subset_of["title"] if subset_of else None},
        },
        "weights": w,
        "matches": matches,
        "explanations": explanations,
        "pipeline": pipeline,
        "engine": {
            "semantic": sem_stat,
            "string": "Levenshtein + Jaro-Winkler",
            "phonetic": "Soundex + Metaphone",
            "demo_titles_indexed": len(titles_index or []),
        },
        "timings": {"total_ms": total_ms},
        "disclaimer": ("Prototype for Internal Hackathon Demonstration. Uses a representative "
                       "demo dataset and prototype scoring logic. Not connected to the official "
                       "PRGI database."),
    }
    if previous:
        result["previous_result"] = {
            "title": previous.get("title"),
            "risk_level": previous.get("risk_level"),
            "risk_score": previous.get("risk_score"),
        }
        result["resubmission"] = True
    return result


def _best_title(detailed, key_fn):
    if not detailed:
        return None
    d = max(detailed, key=key_fn)
    if key_fn(d) <= 0:
        return None
    return {"title": d["title"], "language": d["language"]}


def _best_phon_detail(detailed):
    best = None
    best_score = 0.0
    for d in detailed:
        ph = d["phonetic"]
        if ph["match_detected"] and ph["score"] >= best_score and ph["best_pair"]:
            best, best_score = {
                "against": d["title"],
                "pair": [ph["best_pair"]["token_a"], ph["best_pair"]["token_b"]],
                "soundex": list(ph["best_pair"]["codes"]["soundex"]),
                "metaphone": list(ph["best_pair"]["codes"]["metaphone"]),
                "soundex_match": ph["best_pair"]["soundex"],
                "metaphone_match": ph["best_pair"]["metaphone"],
            }, ph["score"]
    return best


def _best_sem_detail(detailed):
    best = None
    best_score = 0.0
    for d in detailed:
        sc = d["semantic"]["score"]
        if sc > best_score and d["semantic"].get("shared_concepts"):
            best = {"against": d["title"],
                    "shared_concepts": d["semantic"]["shared_concepts"]}
            best_score = sc
        elif sc > best_score and not best:
            best = {"against": d["title"], "shared_concepts": []}
            best_score = sc
    if best and best_score <= 0:
        return None
    return best


def _explain(level, detailed, rules, exact, subset_of,
             sig_string, sig_phon, sig_sem, language_detected) -> list[dict]:
    out = []
    if exact:
        out.append({"type": "danger",
                    "text": f"An identical title “{exact['title']}” already exists in the prototype demo dataset."})
    for v in rules["violations"]:
        out.append({"type": "warning", "text": v["message"]})
    best_str = max(detailed, key=lambda d: d["string"], default=None)
    if best_str and best_str["string"] >= 0.80 and (not exact or best_str["title"] != exact["title"]):
        out.append({"type": "danger" if best_str["string"] >= 0.9 else "warning",
                    "text": f"Strong spelling similarity to existing title "
                            f"“{best_str['title']}” ({round(100*best_str['string'])}% string match)."})
    best_ph = max(detailed, key=lambda d: d["phonetic"]["score"], default=None)
    if best_ph and best_ph["phonetic"]["match_detected"] and best_ph["phonetic"]["score"] >= 0.5:
        pair = best_ph["phonetic"]["best_pair"]
        algos = []
        if pair["metaphone"]:
            algos.append(f"Metaphone “{pair['codes']['metaphone'][0]}”")
        if pair["soundex"]:
            algos.append(f"Soundex “{pair['codes']['soundex'][0]}”")
        out.append({"type": "warning",
                    "text": f"Phonetic match with “{best_ph['title']}” — the phonetic "
                            f"representations are similar ({' + '.join(algos)} match on "
                            f"“{pair['token_a']}” / “{pair['token_b']}”)."})
    best_sem = max(detailed, key=lambda d: d["semantic"]["score"], default=None)
    if best_sem and best_sem["semantic"]["match"] and best_sem["semantic"]["score"] >= 0.5:
        shared = best_sem["semantic"].get("shared_concepts")
        extra = f" (shared meaning: {', '.join(shared)})" if shared else ""
        out.append({"type": "warning",
                    "text": f"Meaning-level similarity with “{best_sem['title']}” — similar "
                            f"meaning despite different wording{extra}."})
    if subset_of and not exact:
        out.append({"type": "warning",
                    "text": f"The wording is contained in / contains existing title "
                            f"“{subset_of['title']}” (existing-title overlap)."})
    if not out:
        out.append({"type": "success",
                    "text": "No significant string, phonetic, semantic or rule-based signal "
                            "was detected against the prototype demo dataset."})
    if sig_string < 0.5 and sig_phon < 0.5 and sig_sem < 0.5 and not rules["violations"]:
        out.append({"type": "success",
                    "text": "All prototype similarity indicators are low — the title looks "
                            "distinct within the demo dataset."})
    return out
