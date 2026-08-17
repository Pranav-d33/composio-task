#!/usr/bin/env python3
"""Pattern synthesis across all 100 apps. Produces data/patterns.json with the
clusters and insights the brief asks for (auth domination, self-serve vs gated
by category, most common blockers, easy wins vs outreach)."""
import json, os
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(BASE, "data", "merged_final.json")))["rows"]

def auth_dominance():
    # count apps whose normalized auth includes each method
    counts = Counter()
    for r in rows:
        for a in r.get("auth_methods_normalized", []):
            counts[a] += 1
    return counts.most_common()

def selfserve_by_category():
    cats = defaultdict(Counter)
    for r in rows:
        g = r.get("gate_type", "none")
        cats[r["category"]][g] += 1
    return {c: dict(cnt) for c, cnt in cats.items()}

def verdict_by_category():
    cats = defaultdict(Counter)
    for r in rows:
        cats[r["category"]][r["buildability_verdict"]] += 1
    return {c: dict(cnt) for c, cnt in cats.items()}

def blockers():
    counts = Counter()
    for r in rows:
        if r["buildability_verdict"] != "buildable_today":
            blk = r.get("blocker", "") or ""
            if "no public" in blk.lower() or "no api" in blk.lower() or "undocumented" in blk.lower() or "no developer" in blk.lower():
                counts["No public API / undocumented"] += 1
            elif "gated" in blk.lower() or "sales" in blk.lower() or "partnership" in blk.lower() or "enterprise" in blk.lower():
                counts["Enterprise/partnership gated"] += 1
            elif "auth" in blk.lower():
                counts["Auth complexity"] += 1
            elif "cli" in blk.lower() or "self-host" in blk.lower():
                counts["Not a SaaS (CLI/self-hosted)"] += 1
            else:
                counts["Other"] += 1
    return counts.most_common()

def mcp_coverage():
    off = sum(1 for r in rows if r.get("existing_mcp", {}).get("official"))
    comm = sum(1 for r in rows if r.get("existing_mcp", {}).get("community") and not r.get("existing_mcp", {}).get("official"))
    none = sum(1 for r in rows if not r.get("existing_mcp", {}).get("official") and not r.get("existing_mcp", {}).get("community"))
    return {"official": off, "community_only": comm, "none": none}

def easy_wins():
    """Easy wins = self-serve creds, no blocker, broad API. Outreach = gated."""
    easy, outreach, investigate = [], [], []
    for r in rows:
        if r["buildability_verdict"] == "buildable_today" and r.get("gate_type") in ("none", "paid_plan") and r.get("self_serve") in ("yes", "trial"):
            easy.append(r)
        elif r.get("gate_type") in ("contact_sales", "partnership"):
            outreach.append(r)
        elif r["buildability_verdict"] != "buildable_today":
            investigate.append(r)
    return {"easy": easy, "outreach": outreach, "investigate": investigate}

def time_to_first_call():
    t = Counter(r.get("time_to_first_call", "unknown") for r in rows)
    return dict(t)

def build():
    ew = easy_wins()
    out = {
        "total_apps": len(rows),
        "auth_dominance": auth_dominance(),
        "auth_method_counts": dict(auth_dominance()),
        "self_serve_by_category": selfserve_by_category(),
        "verdict_by_category": verdict_by_category(),
        "verdict_overall": dict(Counter(r["buildability_verdict"] for r in rows)),
        "gate_overall": dict(Counter(r["gate_type"] for r in rows)),
        "top_blockers": blockers(),
        "mcp_coverage": mcp_coverage(),
        "mcp_by_category": {c: dict(Counter(bool(r.get("existing_mcp", {}).get("official")) for r in rows if r["category"] == c)) for c in {r["category"] for r in rows}},
        "easy_wins": [{"num": r["num"], "app": r["app"], "category": r["category"]} for r in ew["easy"]],
        "outreach": [{"num": r["num"], "app": r["app"], "category": r["category"], "gate": r.get("gate_type")} for r in ew["outreach"]],
        "investigate": [{"num": r["num"], "app": r["app"], "category": r["category"], "verdict": r["buildability_verdict"]} for r in ew["investigate"]],
        "time_to_first_call": time_to_first_call(),
        "confidence_mix": dict(Counter(r["confidence"] for r in rows)),
    }
    json.dump(out, open(os.path.join(BASE, "data", "patterns.json"), "w"), indent=1)

    print(f"Total apps: {out['total_apps']}")
    print("\nAUTH DOMINANCE:")
    for k, v in out["auth_dominance"]:
        print(f"  {k}: {v}")
    print("\nVERDICT OVERALL:", out["verdict_overall"])
    print("GATE OVERALL:", out["gate_overall"])
    print("\nTOP BLOCKERS:")
    for k, v in out["top_blockers"]:
        print(f"  {k}: {v}")
    print("\nMCP COVERAGE:", out["mcp_coverage"])
    print("\nTIME-TO-FIRST-CALL:", out["time_to_first_call"])
    print(f"\nEASY WINS ({len(out['easy_wins'])}):")
    for e in out["easy_wins"]:
        print(f"  {e['num']:3d} {e['app']}")
    print(f"\nOUTREACH NEEDED ({len(out['outreach'])}):")
    for e in out["outreach"]:
        print(f"  {e['num']:3d} {e['app']} ({e['gate']})")
    print(f"\nINVESTIGATE / NOT BUILDABLE ({len(out['investigate'])}):")
    for e in out["investigate"]:
        print(f"  {e['num']:3d} {e['app']} ({e['verdict']})")
    print("\nConfidence mix:", out["confidence_mix"])

if __name__ == "__main__":
    build()