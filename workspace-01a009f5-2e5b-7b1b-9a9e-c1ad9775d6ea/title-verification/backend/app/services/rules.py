"""
Prototype DEMO rule engine.

These are demonstration policy checks written for the hackathon prototype.
They are NOT official PRGI policy enforcement.
"""
from __future__ import annotations

from .. import config
from .normalize import punctuation_stats


def evaluate_rules(raw_title: str, normalized: str, tokens: list[str],
                   db_titles_norm: list[tuple[str, str]]) -> dict:
    """
    Returns {violations: [...], score: 0..1}
    db_titles_norm: list of (normalized, display_title) from the demo DB.
    """
    violations = []

    # 1. Empty / too short / too long -------------------------------------
    if not normalized:
        violations.append({
            "rule": "EMPTY_TITLE", "severity": "high",
            "message": "Title is empty after normalisation.",
        })
    elif len(normalized) < config.MIN_TITLE_LEN:
        violations.append({
            "rule": "TOO_SHORT", "severity": "high",
            "message": f"Title shorter than {config.MIN_TITLE_LEN} characters — too vague to verify.",
        })
    if len(raw_title) > config.MAX_TITLE_LEN:
        violations.append({
            "rule": "TOO_LONG", "severity": "medium",
            "message": f"Title exceeds {config.MAX_TITLE_LEN} characters (demo limit).",
        })

    # 2. Excessive punctuation --------------------------------------------
    pstats = punctuation_stats(raw_title)
    if pstats["count"] > 3 or pstats["repeated"]:
        violations.append({
            "rule": "EXCESSIVE_PUNCTUATION", "severity": "medium",
            "message": "Excessive or repeated punctuation marks detected (demo rule).",
        })

    # 3. Disallowed demo terms --------------------------------------------
    for term in config.DISALLOWED_TERMS:
        term_tokens = term.split()
        if all(tt in tokens for tt in term_tokens):
            violations.append({
                "rule": "DISALLOWED_TERM", "severity": "high", "term": term,
                "message": f"Demo policy term detected: “{term}”. "
                           f"(Prototype demo list — not official PRGI policy.)",
            })

    # 4. Common prefix / suffix variation of an existing demo title -------
    for norm_existing, display in db_titles_norm:
        ex_tokens = norm_existing.split()
        if not ex_tokens or norm_existing == normalized:
            continue
        # e.g. "the " + existing   →  prefix variation
        for pre in config.DEMO_PREFIXES:
            if tokens == [pre] + ex_tokens:
                violations.append({
                    "rule": "PREFIX_VARIATION", "severity": "medium",
                    "related_title": display,
                    "message": f"Looks like a common prefix variation of existing demo title “{display}”.",
                })
        # e.g. existing + " daily"  →  suffix variation
        for suf in config.DEMO_SUFFIXES:
            if tokens == ex_tokens + [suf]:
                violations.append({
                    "rule": "SUFFIX_VARIATION", "severity": "medium",
                    "related_title": display,
                    "message": f"Looks like a common suffix variation of existing demo title “{display}”.",
                })

    # 5. Numeric-only title ------------------------------------------------
    if normalized and all(t.isdigit() for t in tokens):
        violations.append({
            "rule": "NUMERIC_ONLY", "severity": "high",
            "message": "Title contains only numbers.",
        })

    weight = {"high": 1.0, "medium": 0.6, "low": 0.3}
    score = min(1.0, sum(weight.get(v["severity"], 0.5) for v in violations))
    return {"violations": violations, "score": round(score, 4),
            "passed": len(violations) == 0}
