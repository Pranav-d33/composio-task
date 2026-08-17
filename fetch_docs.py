#!/usr/bin/env python3
"""Fetch docs pages for all 100 apps concurrently, cache to data/raw_docs/."""
import json, os, sys, re, time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "data", "raw_docs")
APPS = json.load(open(os.path.join(BASE, "data", "apps_input.json")))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

DOC_URL_OVERRIDES = {
    "Salesforce": "https://trailhead.salesforce.com/content/learn/modules/api_basics",
    "HubSpot": "https://developers.hubspot.com/docs/api/overview",
    "Pipedrive": "https://developers.pipedrive.com/docs/api/v1",
    "Attio": "https://docs.attio.com",
    "Twenty": "https://docs.twenty.com",
    "Podio": "https://developers.podio.com",
    "Zoho CRM": "https://www.zoho.com/crm/developer/docs/api/v6/",
    "Close": "https://developer.close.com",
    "Copper": "https://developer.copper.com",
    "DealCloud": "https://api.docs.dealcloud.com",
    "Zendesk": "https://developer.zendesk.com/api-reference/",
    "Intercom": "https://developers.intercom.com/",
    "Freshdesk": "https://developers.freshdesk.com/api/",
    "Front": "https://dev.frontapp.com/reference/introduction",
    "Pylon": "https://docs.usepylon.com",
    "LiveAgent": "https://www.liveagent.com/api/",
    "Plain": "https://docs.plain.com",
    "Help Scout": "https://developer.helpscout.com/help-desk-api/",
    "Gorgias": "https://developers.gorgias.com/reference/getting-started",
    "Gladly": "https://developer.gladly.com",
    "Slack": "https://api.slack.com/docs",
    "Twilio": "https://www.twilio.com/docs/usage/api",
    "Zoho Cliq": "https://www.zoho.com/cliq/help/restapi/v2/",
    "Lark (Larksuite)": "https://open.larksuite.com/document/",
    "Pumble": "https://pumble.com/help/",
    "Discord": "https://discord.com/developers/docs/intro",
    "Telegram": "https://core.telegram.org/bots/api",
    "WhatsApp Business": "https://developers.facebook.com/docs/whatsapp/cloud-api",
    "Aircall": "https://developer.aircall.io/api-references/",
    "Vonage": "https://developer.vonage.com/en/api/messages",
    "Google Ads": "https://developers.google.com/google-ads/api/docs/start",
    "Meta Ads": "https://developers.facebook.com/docs/marketing-apis/",
    "LinkedIn Ads": "https://learn.microsoft.com/en-us/linkedin/marketing/",
    "GoHighLevel": "https://highlevel.stoplight.io/docs/integrations",
    "Mailchimp": "https://mailchimp.com/developer/marketing/api/",
    "Klaviyo": "https://developers.klaviyo.com/en/reference",
    "systeme.io": "https://systeme.io/help/",
    "Pinterest": "https://developers.pinterest.com/docs/get-started/introduction/",
    "Threads (Meta)": "https://developers.facebook.com/docs/threads",
    "SendGrid": "https://docs.sendgrid.com/api-reference",
    "Shopify": "https://shopify.dev/docs/api/admin",
    "WooCommerce": "https://woocommerce.github.io/woocommerce-rest-api-docs/",
    "BigCommerce": "https://developer.bigcommerce.com/docs/start",
    "Salesforce Commerce Cloud": "https://developer.salesforce.com/docs/commerce",
    "Magento (Adobe Commerce)": "https://developer.adobe.com/commerce/webapi/rest/",
    "Squarespace": "https://developers.squarespace.com/commerce-apis",
    "Ecwid": "https://api-docs.ecwid.com",
    "Gumroad": "https://gumroad.com/api",
    "Amazon Selling Partner": "https://developer-docs.amazon.com/sp-api/docs/welcome",
    "fanbasis": "https://fanbasis.com",
    "DataForSEO": "https://docs.dataforseo.com",
    "SE Ranking": "https://seranking.com/api/",
    "Ahrefs": "https://ahrefs.com/api/documentation",
    "MrScraper": "https://docs.mrscraper.com",
    "Apify": "https://docs.apify.com/platform/api",
    "Firecrawl": "https://docs.firecrawl.dev",
    "Bright Data": "https://docs.brightdata.com",
    "Sherlock": "https://github.com/sherlock-project/sherlock",
    "Waterfall.io": "https://waterfall.io",
    "Clay": "https://docs.clay.com",
    "GitHub": "https://docs.github.com/en/rest",
    "Vercel": "https://vercel.com/docs/rest-api",
    "Netlify": "https://docs.netlify.com/api/get-started/",
    "Cloudflare": "https://developers.cloudflare.com/api/",
    "Supabase": "https://supabase.com/docs/reference/javascript/introduction",
    "Neo4j": "https://neo4j.com/docs/api/python-driver/current/",
    "Snowflake": "https://docs.snowflake.com/en/developer-guide/",
    "MongoDB Atlas": "https://www.mongodb.com/docs/atlas/api/",
    "Datadog": "https://docs.datadoghq.com/api/latest/",
    "Sentry": "https://docs.sentry.io/api/",
    "Notion": "https://developers.notion.com/docs/getting-started",
    "Airtable": "https://airtable.com/developers/web/api/introduction",
    "Linear": "https://developers.linear.app/docs/graphql/working-with-the-graphql-api",
    "Jira": "https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/",
    "Asana": "https://developers.asana.com/docs",
    "Monday.com": "https://developer.monday.com/api-reference/docs",
    "ClickUp": "https://clickup.com/api",
    "Coda": "https://coda.io/developers/apis/v1",
    "Smartsheet": "https://smartsheet.redoc.ly/",
    "Harvest": "https://help.getharvest.com/api-v2/",
    "Stripe": "https://stripe.com/docs/api",
    "Plaid": "https://plaid.com/docs/api/",
    "Binance": "https://developers.binance.com/docs/binance-spot-api-docs/rest-api/overview",
    "Paygent Connect": "https://nmi.com",
    "iPayX": "https://ipayx.ai/docs",
    "QuickBooks": "https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/invoice",
    "Xero": "https://developer.xero.com/documentation/api/accounting/overview",
    "Brex": "https://developer.brex.com",
    "Ramp": "https://docs.ramp.com/reference",
    "PitchBook": "https://pitchbook.com/products/research-api",
    "NotebookLM": "https://notebooklm.google.com",
    "Otter AI": "https://help.otter.ai/",
    "Fathom": "https://fathom.video/",
    "Consensus": "https://consensus.app/",
    "Reducto": "https://docs.reducto.ai",
    "Devin": "https://docs.devin.ai/",
    "higgsfield": "https://higgsfield.ai/",
    "Mermaid CLI": "https://github.com/mermaid-js/mermaid-cli",
    "YouTube Transcript": "https://transcriptapi.com/",
    "Grain": "https://grain.com/",
}

def slugify(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

def fetch_one(app):
    name = app["name"]
    url = DOC_URL_OVERRIDES.get(name, "https://" + app["hint"])
    path = os.path.join(CACHE, f"{app['num']:03d}_{slugify(name)}.html")
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return ("SKIP", app["num"], name, len(open(path).read()))
    try:
        r = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
        r.raise_for_status()
        with open(path, "w") as f:
            f.write(r.text)
        return ("OK", app["num"], name, len(r.text))
    except Exception as e:
        return ("FAIL", app["num"], name, f"{type(e).__name__}: {str(e)[:50]}")

def main():
    os.makedirs(CACHE, exist_ok=True)
    apps = [a for cat in APPS["categories"] for a in cat["apps"]]
    results = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fetch_one, a): a for a in apps}
        for fut in as_completed(futs):
            res = fut.result()
            results.append(res)
            print(f"{res[0]} {res[1]:3d} {res[2]:28s} {res[3]}", flush=True)
    ok = sum(1 for r in results if r[0] == "OK")
    fail = sum(1 for r in results if r[0] == "FAIL")
    skip = sum(1 for r in results if r[0] == "SKIP")
    print(f"\nDONE. OK={ok} FAIL={fail} SKIP={skip} TOTAL={len(results)}", flush=True)

if __name__ == "__main__":
    main()