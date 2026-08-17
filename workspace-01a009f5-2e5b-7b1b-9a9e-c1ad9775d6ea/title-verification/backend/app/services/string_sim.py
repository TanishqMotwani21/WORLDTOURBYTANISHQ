"""
String-similarity algorithms — pure-Python implementations.

* Levenshtein distance (edit distance) with normalised similarity.
* Jaro-Winkler similarity.

These are implemented from the standard published algorithms so the
prototype has zero hard dependency on native extensions.
"""
from __future__ import annotations


def levenshtein_distance(a: str, b: str) -> int:
    """Classic Levenshtein edit distance (insert / delete / substitute = 1)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur.append(min(cur[-1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[-1]


def levenshtein_similarity(a: str, b: str) -> float:
    """Normalised Levenshtein similarity in [0, 1]."""
    if not a and not b:
        return 1.0
    m = max(len(a), len(b))
    if m == 0:
        return 1.0
    return 1.0 - levenshtein_distance(a, b) / m


def jaro_similarity(s1: str, s2: str) -> float:
    """Jaro similarity."""
    if s1 == s2:
        return 1.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0
    match_dist = max(len1, len2) // 2 - 1
    if match_dist < 0:
        match_dist = 0
    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0
    for i in range(len1):
        start = max(0, i - match_dist)
        end = min(i + match_dist + 1, len2)
        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = s2_matches[j] = True
            matches += 1
            break
    if matches == 0:
        return 0.0
    t = 0
    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            t += 1
        k += 1
    t //= 2
    return (matches / len1 + matches / len2 + (matches - t) / matches) / 3.0


def jaro_winkler_similarity(s1: str, s2: str, prefix_weight: float = 0.1) -> float:
    """Jaro-Winkler similarity — boosts strings sharing a common prefix."""
    j = jaro_similarity(s1, s2)
    prefix = 0
    for c1, c2 in zip(s1, s2):
        if c1 == c2 and prefix < 4:
            prefix += 1
        else:
            break
    return j + prefix * prefix_weight * (1.0 - j)


def combined_string_similarity(a: str, b: str) -> float:
    """Blend of normalised Levenshtein and Jaro-Winkler (both in [0,1])."""
    lev = levenshtein_similarity(a, b)
    jw = jaro_winkler_similarity(a, b)
    return round(0.5 * lev + 0.5 * jw, 4)
