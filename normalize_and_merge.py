#!/usr/bin/env python3
"""Normalize auth labels across all 100 rows and build merged_final.json."""
import json, glob, os, re
from collections import Counter

ROWS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "rows")

def norm_auth(label):
    l = label.lower()
    if "oauth2" in l or "oauth 2" in l or "3lo" in l:
        return "OAuth2"
    if "oauth1" in l or "oauth 1" in l:
        return "OAuth1"
    if "basic auth" in l or "basic" in l:
        return "Basic"
    if "bot token" in l:
        return "Bot Token"
    if "bearer" in l and "token" in l:
        return "Bearer Token"
    if "personal access token" in l or "pat" in l.split():
        return "PAT"
    if "api token" in l or "access token" in l:
        return "API Token"
    if "api key" in l or "application key" in l or "private api key" in l or "public key" in l:
        return "API Key"
    if "jwt" in l or "key-pair" in l:
        return "JWT"
    if "sigv4" in l or "signature" in l:
        return "Signed Request"
    if "saml" in l:
        return "SAML"
    if "secret" in l:
        return "API Key"
    if "unknown" in l:
        return "Unknown"
    if "none" in l:
        return "None"
    if "graphql" in l:
        return "API Token"
    if "soap" in l:
        return "SOAP"
    if "token" in l:
        return "API Token"
    return "Other"

def main():
    rows = []
    for f in sorted(glob.glob(os.path.join(ROWS, "*.json"))):
        d = json.load(open(f))
        raw_auths = d.get("auth_methods", [])
        if isinstance(raw_auths, str):
            raw_auths = [raw_auths]
        norm = []
        for a in raw_auths:
            n = norm_auth(a)
            if n not in norm:
                norm.append(n)
        if not norm:
            norm = ["Unknown"]
        d["auth_methods_normalized"] = norm
        rows.append(d)

    rows.sort(key=lambda r: r["num"])

    # gate_type normalization (ensure it's one of the canonical set)
    for d in rows:
        g = d.get("gate_type", "none")
        if g not in ("none", "paid_plan", "admin_approval", "contact_sales", "partnership"):
            # derive from self_serve
            ss = d.get("self_serve", "")
            mapping = {"yes": "none", "trial": "paid_plan", "paid": "paid_plan",
                       "admin": "admin_approval", "partnership": "partnership", "no": "contact_sales"}
            d["gate_type"] = mapping.get(ss, "none")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "merged_final.json")
    json.dump({"generated": __import__("datetime").datetime.now().isoformat(),
               "count": len(rows), "rows": rows}, open(out, "w"), indent=1)
    print(f"Wrote {len(rows)} rows to {out}")
    print("Normalized auth distribution:")
    for k, v in Counter(a for d in rows for a in d["auth_methods_normalized"]).most_common():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()