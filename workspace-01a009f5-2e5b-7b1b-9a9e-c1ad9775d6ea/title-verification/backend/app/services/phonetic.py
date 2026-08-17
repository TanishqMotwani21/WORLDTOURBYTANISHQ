"""
Phonetic-similarity algorithms — pure-Python implementations.

* Soundex (classic American Soundex, NARA rules)
* Metaphone (Lawrence Philips' original Metaphone)

Used to detect titles that *sound* alike even when spelled differently
(e.g. "Phoenix" vs "Foenix" share the Metaphone code FNKS).
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Soundex
# ---------------------------------------------------------------------------
_SOUNDEX_MAP = {
    **dict.fromkeys("BFPV", "1"),
    **dict.fromkeys("CGJKQSXZ", "2"),
    **dict.fromkeys("DT", "3"),
    "L": "4",
    **dict.fromkeys("MN", "5"),
    "R": "6",
}


def soundex(word: str) -> str:
    word = re.sub(r"[^A-Za-z]", "", word).upper()
    if not word:
        return ""
    first = word[0]
    codes = []
    prev = _SOUNDEX_MAP.get(first, "")
    for ch in word[1:]:
        code = _SOUNDEX_MAP.get(ch, "")
        if code and code != prev:
            codes.append(code)
        if ch not in "HW":          # H and W do not break adjacency
            prev = code
        else:
            prev = prev             # keep previous code across H/W
    return (first + "".join(codes) + "000")[:4]


# ---------------------------------------------------------------------------
# Metaphone  (compact implementation of the original algorithm)
# ---------------------------------------------------------------------------
_VOWELS = "AEIOU"


def metaphone(word: str) -> str:
    w = re.sub(r"[^A-Za-z]", "", word).upper()
    if not w:
        return ""

    # Drop duplicates except CC
    chars = []
    for i, ch in enumerate(w):
        if i == 0 or ch != w[i - 1] or ch == "C":
            chars.append(ch)
    w = "".join(chars)

    # Initial transformations
    for pre in ("KN", "GN", "PN", "AE", "WR"):
        if w.startswith(pre):
            w = w[1:]
            break
    if w.startswith("WH"):
        w = "W" + w[2:]
    if w.startswith("X"):
        w = "S" + w[1:]

    out = []
    n = len(w)
    i = 0

    def at(pos: int) -> str:
        return w[pos] if 0 <= pos < n else ""

    while i < n:
        ch = w[i]
        nxt = at(i + 1)

        if ch in _VOWELS:
            if i == 0:
                out.append(ch)
        elif ch == "B":
            if not (at(i - 1) == "M" and i == n - 1):   # -MB silent
                out.append("B")
        elif ch == "C":
            if at(i - 1) == "S" and nxt in "EIY":
                pass                                    # SCE/SCI/SCY silent
            elif nxt == "H":
                out.append("X")
                i += 1
            elif nxt in "EIY":
                out.append("S")
            else:
                out.append("K")
        elif ch == "D":
            if nxt == "G" and at(i + 2) in "EIY":
                out.append("J")
                i += 2
            else:
                out.append("T")
        elif ch == "G":
            if nxt == "H":
                if i == 0:
                    out.append("G")                     # GH at start -> G
                # else GH silent
                i += 1
            elif nxt == "N" and (i + 2 >= n or (at(i + 2) == "E" and at(i + 3) == "D")):
                pass                                    # GN / GNED silent
            elif nxt in "EIY":
                out.append("J")
            else:
                out.append("K")
        elif ch == "H":
            # kept only when initial or between/after vowels and before a vowel
            if (i == 0 or at(i - 1) in _VOWELS) and nxt in _VOWELS:
                out.append("H")
        elif ch == "K":
            if at(i - 1) != "C":
                out.append("K")
        elif ch == "P":
            if nxt == "H":
                out.append("F")
                i += 1
            else:
                out.append("P")
        elif ch == "Q":
            out.append("K")
        elif ch == "S":
            if nxt == "H" or (nxt == "I" and at(i + 2) in "AO"):
                out.append("X")
                if nxt == "H":
                    i += 1
            else:
                out.append("S")
        elif ch == "T":
            if nxt == "I" and at(i + 2) in "AO":
                out.append("X")
            elif nxt == "H":
                out.append("0")                         # TH -> theta
                i += 1
            elif not (nxt == "C" and at(i + 2) == "H"):
                out.append("T")
        elif ch == "V":
            out.append("F")
        elif ch == "W" or ch == "Y":
            if nxt in _VOWELS:
                out.append(ch)
        elif ch == "X":
            out.append("KS")
        elif ch == "Z":
            out.append("S")
        elif ch in "FJKLMNR":
            out.append(ch)
        i += 1

    return "".join(out)


# ---------------------------------------------------------------------------
# Word / title level comparison helpers
# ---------------------------------------------------------------------------

def token_phonetic_match(t1: str, t2: str) -> dict:
    """Compare two tokens phonetically with both algorithms."""
    sx1, sx2 = soundex(t1), soundex(t2)
    mp1, mp2 = metaphone(t1), metaphone(t2)
    return {
        "soundex_match": bool(sx1) and sx1 == sx2,
        "metaphone_match": bool(mp1) and mp1 == mp2,
        "codes": {"soundex": (sx1, sx2), "metaphone": (mp1, mp2)},
    }


def title_phonetic_similarity(tokens_a: list[str], tokens_b: list[str]) -> dict:
    """
    Best-alignment token matching between two titles.
    Returns score in [0,1], per-token matches and the winning pair.
    """
    if not tokens_a or not tokens_b:
        return {"score": 0.0, "matches": [], "all_matched": False}
    matches = []
    matched_a: set[int] = set()
    matched_b: set[int] = set()
    best_pair = None
    for i, ta in enumerate(tokens_a):
        for j, tb in enumerate(tokens_b):
            if j in matched_b:
                continue
            r = token_phonetic_match(ta, tb)
            if r["soundex_match"] or r["metaphone_match"]:
                matched_a.add(i)
                matched_b.add(j)
                matches.append({
                    "token_a": ta, "token_b": tb,
                    "soundex": r["soundex_match"], "metaphone": r["metaphone_match"],
                    "codes": r["codes"],
                })
                if best_pair is None or (r["metaphone_match"] and r["soundex_match"]):
                    best_pair = matches[-1]
                break
    coverage = len(matched_a) / max(len(tokens_a), len(tokens_b))
    both = sum(1 for m in matches if m["soundex"] and m["metaphone"])
    score = round(min(1.0, coverage * (0.6 + 0.4 * (both / max(1, len(matches))))), 4)
    return {
        "score": score,
        "matches": matches,
        "best_pair": best_pair,
        "match_detected": len(matches) > 0,
    }
