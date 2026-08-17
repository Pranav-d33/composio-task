#!/usr/bin/env python3
"""Verification runner. Records per-field agreement for the sampled apps.
Usage: python3 run_verification.py          # process all remaining unverified
       python3 run_verification.py --app 1  # process one app
Each app writes data/verification/NN_name.json with per-field checks.
"""
import json, os, sys, glob
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = json.load(open(os.path.join(BASE, "data", "verification_sample.json")))
ROWS = json.load(open(os.path.join(BASE, "data", "merged_final.json")))["rows"]
by_num = {r["num"]: r for r in ROWS}
OUTDIR = os.path.join(BASE, "data", "verification")
os.makedirs(OUTDIR, exist_ok=True)

FIELDS = ["auth_methods", "self_serve", "api_surface", "mcp", "verdict"]

def load_record(num):
    p = glob.glob(os.path.join(OUTDIR, f"{num:03d}_*.json"))
    return json.load(open(p[0])) if p else None

def save_record(record):
    app = by_num[record["num"]]["app"]
    slug = app.lower().replace(" ", "_").replace("(", "").replace(")", "")
    p = os.path.join(OUTDIR, f"{record['num']:03d}_{slug}.json")
    json.dump(record, open(p, "w"), indent=1)
    return p

def compute_summary():
    """Aggregate per-field accuracy across verified records."""
    records = []
    for f in glob.glob(os.path.join(OUTDIR, "*.json")):
        records.append(json.load(open(f)))
    if not records:
        return None
    total = Counter()
    correct = Counter()
    for rec in records:
        for field in FIELDS:
            total[field] += 1
            if rec.get("checks", {}).get(field) == "correct":
                correct[field] += 1
    return {
        "apps_verified": len(records),
        "per_field": {f: {"correct": correct[f], "total": total[f],
                          "accuracy": round(correct[f] / total[f], 3) if total[f] else 0}
                      for f in FIELDS},
        "overall": round(sum(correct.values()) / sum(total.values()), 3) if total else 0
    }

def main():
    only = None
    if "--app" in sys.argv:
        only = int(sys.argv[sys.argv.index("--app") + 1])
    done = {int(f.split("_")[0]) for f in os.listdir(OUTDIR) if f.endswith(".json")}
    for item in SAMPLE["sample"]:
        num = item["num"]
        if only and num != only:
            continue
        if load_record(num) and not only:
            continue
        print(f"NEEDS_VERIFY {num:3d} {item['app']}  docs={item['docs_url']}")

    if only:
        print("\nTo verify, edit data/verification/NN_name.json with real 'checks' after browser re-check.")
        print("Field values: correct | wrong | unknown")
    print("\n" + json.dumps(compute_summary(), indent=1) if compute_summary() else "\nNo verification records yet.")

if __name__ == "__main__":
    main()