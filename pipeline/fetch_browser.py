#!/usr/bin/env python3
"""Fetch JS-rendered docs pages using scrapling Fetcher (playwright under the hood).
Usage: python3 fetch_browser.py --app 73   # fetch one app
       python3 fetch_browser.py             # fetch all apps missing from cache
"""
import os, sys, json, time
import requests

from scrapling.fetchers import DynamicFetcher as Fetcher

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(BASE, "data", "raw_docs")
APPS = json.load(open(os.path.join(BASE, "data", "apps_input.json")))

# URLs to fetch via browser (JS-rendered / protected sites)
BROWSER_URLS = {
    7: "https://www.zoho.com/crm/developer/docs/api/v6/",
    16: "https://www.liveagent.com/api/",
    19: "https://developers.gorgias.com/reference/getting-started",
    20: "https://developer.gladly.com",
    21: "https://api.slack.com/docs",
    24: "https://open.larksuite.com/document/",
    25: "https://pumble.com/help/",
    26: "https://discord.com/developers/docs/intro",
    28: "https://developers.facebook.com/docs/whatsapp/cloud-api",
    30: "https://developer.vonage.com/en/api/messages",
    32: "https://developers.facebook.com/docs/marketing-apis/",
    34: "https://highlevel.stoplight.io/docs/integrations",
    37: "https://systeme.io/help/",
    39: "https://developers.facebook.com/docs/threads",
    44: "https://developer.salesforce.com/docs/commerce",
    48: "https://gumroad.com/api",
    67: "https://docs.snowflake.com/en/developer-guide/",
    72: "https://airtable.com/developers/web/api/introduction",
    73: "https://developers.linear.app/docs/graphql/working-with-the-graphql-api",
    77: "https://clickup.com/api",
    79: "https://smartsheet.redoc.ly/",
    80: "https://help.getharvest.com/api-v2/",
    83: "https://developers.binance.com/docs/binance-spot-api-docs/rest-api/overview",
    85: "https://ipayx.ai/docs",
    86: "https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/invoice",
    87: "https://developer.xero.com/documentation/api/accounting/overview",
    89: "https://docs.ramp.com/reference",
    90: "https://pitchbook.com/products/research-api",
    91: "https://cloud.google.com/gemini/docs",
    94: "https://consensus.app/",
    19: "https://developers.gorgias.com/reference/getting-started",
    80: "https://help.getharvest.com/api-v2/",
    85: "https://ipayx.ai/docs",
    77: "https://docs.clickup.com/en/articles/4361173-clickup-api-overview",
    83: "https://developers.binance.com/docs/binance-spot-api-docs/rest-api/overview",
    73: "https://developers.linear.app/docs",
    79: "https://smartsheet.redoc.ly/",
    25: "https://pumble.com/help/",
    37: "https://systeme.io/help/",
    30: "https://developer.vonage.com/en/api/messages",
    20: "https://developer.gladly.com",
    26: "https://discord.com/developers/docs/intro",
    24: "https://open.larksuite.com/document/",
    21: "https://api.slack.com/docs",
    72: "https://airtable.com/developers/web/api/introduction",
    87: "https://developer.xero.com/documentation/api/accounting/overview",
    48: "https://gumroad.com/api",
}

def slugify(name):
    import re
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

def get_name(num):
    for c in APPS["categories"]:
        for a in c["apps"]:
            if a["num"] == num:
                return a["name"]
    return str(num)

def main():
    only = None
    if "--app" in sys.argv:
        only = int(sys.argv[sys.argv.index("--app") + 1])

    f = Fetcher()

    for num, url in BROWSER_URLS.items():
        if only and num != only:
            continue
        name = get_name(num)
        path = os.path.join(CACHE, f"{num:03d}_{slugify(name)}.html")
        if os.path.exists(path) and os.path.getsize(path) > 1500:
            continue
        try:
            resp = f.fetch(url, headless=True)
            body = resp.html_content if hasattr(resp, "html_content") else (resp.body if hasattr(resp, "body") else resp.text)
            if isinstance(body, bytes):
                body = body.decode("utf-8", errors="ignore")
            if len(body) < 1000:
                print(f"THIN {num:3d} {name:28s} len={len(body)} {url}", flush=True)
                continue
            with open(path, "w") as fh:
                fh.write(body)
            print(f"OK   {num:3d} {name:28s} len={len(body)} {url}", flush=True)
        except Exception as e:
            print(f"FAIL {num:3d} {name:28s} {type(e).__name__}: {str(e)[:70]}", flush=True)
        time.sleep(1)

if __name__ == "__main__":
    main()