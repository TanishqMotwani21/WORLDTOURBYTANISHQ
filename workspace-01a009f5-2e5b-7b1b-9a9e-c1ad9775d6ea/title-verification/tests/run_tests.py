"""
End-to-end acceptance tests for the AI Title Verification prototype.

Runs the seven demonstration scenarios from the hackathon brief against the
live API (default http://localhost:8000) and prints PASS/FAIL per case.

Usage:
    python tests/run_tests.py [base_url]
"""
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


def post(path, payload):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=300) as r:
        return json.loads(r.read())


def has_match(result, needle):
    return any(needle.lower() in m["title"].lower() for m in result.get("matches", []))


results = []

def check(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


# --- health -----------------------------------------------------------------
h = get("/api/health")
check("API healthy with demo dataset", h["status"] == "ok" and h["demo_titles"] >= 100,
      f"{h['demo_titles']} demo titles, semantic={h['semantic_engine']['engine']}")

# --- TEST 1: Indian Xpress -> high similarity with Indian Express ------------
r1 = post("/api/verify", {"title": "Indian Xpress", "language": "auto"})
s = r1["signals"]["string_similarity"]
check("T1 Indian Xpress ↔ Indian Express high string similarity",
      has_match(r1, "Indian Express") and s["score"] >= 90,
      f"score={r1['risk']['score']} level={r1['risk']['level']}")

# --- TEST 2: Namascar -> Namaskar --------------------------------------------
r2 = post("/api/verify", {"title": "Namascar", "language": "auto"})
check("T2 Namascar ↔ Namaskar high spelling similarity",
      has_match(r2, "Namaskar") and r2["signals"]["string_similarity"]["score"] >= 85,
      f"score={r2['risk']['score']} level={r2['risk']['level']}")

# --- TEST 3: Foenix -> phonetic similarity with Phoenix -----------------------
r3 = post("/api/verify", {"title": "Foenix", "language": "auto"})
phm = [m for m in r3["matches"] if m["title"] == "Phoenix"]
check("T3 Foenix ↔ Phoenix phonetic match (Metaphone)",
      bool(phm) and phm[0]["phonetic"]["match_detected"],
      f"phonetic signal={r3['signals']['phonetic_similarity']['score']}")

# --- TEST 4: Daily Evening -> semantic link with Pratidin Sandhya --------------
r4 = post("/api/verify", {"title": "Daily Evening", "language": "auto"})
psm = [m for m in r4["matches"] if m["title"] == "Pratidin Sandhya"]
check("T4 Daily Evening ↔ Pratidin Sandhya meaning-level similarity",
      bool(psm) and psm[0]["semantic"]["score"] >= 0.5,
      f"semantic of pair={psm[0]['semantic']['score'] if psm else 'MISSING'}")

# --- TEST 5: unrelated title -> LOW RISK ---------------------------------------
r5 = post("/api/verify", {"title": "Azure Pelican Quarterly", "language": "auto"})
check("T5 unrelated unique title -> LOW RISK",
      r5["risk"]["level"] == "LOW RISK", f"score={r5['risk']['score']}")

# --- TEST 6: disallowed demo term -> rule violation ------------------------------
r6 = post("/api/verify", {"title": "President News Daily", "language": "auto"})
viol = r6["signals"]["rule_violations"]["violations"]
check("T6 demo disallowed term detected",
      any(v["rule"] == "DISALLOWED_TERM" for v in viol),
      f"violations={[v['rule'] for v in viol]}")

# --- TEST 7: modify & resubmit changes the result --------------------------------
r7 = post("/api/resubmit", {
    "parent_id": r6["id"], "title": "Citizen Chronicle Weekly", "language": "auto"})
check("T7 modify → resubmit recalculates",
      "previous_result" in r7 and r7["risk"]["score"] != r6["risk"]["score"],
      f"{r6['risk']['score']} ({r6['risk']['level']}) → "
      f"{r7['risk']['score']} ({r7['risk']['level']})")

# --- extras: history, similar, error handling -------------------------------------
hist = get("/api/history")
check("History records submissions", hist["count"] >= 7, f"{hist['count']} rows")
item = get(f"/api/history/{r1['id']}")
check("History item re-opens full analysis", item["title"] == "Indian Xpress")
sim = get("/api/similar?title=Indian%20Express")
check("Similar endpoint ranks family", sim["results"][0]["title"] == "Indian Express")
try:
    post("/api/verify", {"title": ""})
    check("Empty title rejected gracefully", False)
except urllib.error.HTTPError as e:
    check("Empty title rejected gracefully", e.code == 400)
try:
    post("/api/verify", {"title": "Some Title", "language": "Klingon"})
    check("Unsupported language rejected gracefully", False)
except urllib.error.HTTPError as e:
    check("Unsupported language rejected gracefully", e.code == 400)

print("=" * 72)
print(f"{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
