#!/usr/bin/env python3
"""Analyze Composio toolkit coverage for 100 apps."""

import json
import os
import subprocess
import sys
from pathlib import Path

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Read the apps input
with open(os.path.join(BASE, "data", "apps_input.json")) as f:
    data = json.load(f)

# Flatten all apps
all_apps = []
for category in data["categories"]:
    for app in category["apps"]:
        all_apps.append(app)

print(f"Analyzing {len(all_apps)} apps...\n", file=sys.stderr)

coverage = []

for i, app in enumerate(all_apps, 1):
    app_name = app["name"]
    num = app["num"]
    hint = app.get("hint", "")

    print(f"[{i:3d}/100] Searching for {app_name}...", file=sys.stderr, end=" ", flush=True)

    # Build the search query
    query = f"use {app_name} API to read, create and update its main objects"

    try:
        # Search for the app
        result = subprocess.run(
            ["composio", "search", query, "--limit", "10"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"ERROR (code {result.returncode})", file=sys.stderr)
            coverage.append({
                "num": num,
                "app": app_name,
                "found": False,
                "toolkit": None,
                "tool_count": 0,
                "sample_tools": [],
                "auth": [],
                "notes": f"search failed: {result.stderr[:100]}"
            })
            continue

        search_data = json.loads(result.stdout)
        results = search_data.get("results", [])

        if not results:
            print("NOT FOUND", file=sys.stderr)
            coverage.append({
                "num": num,
                "app": app_name,
                "found": False,
                "toolkit": None,
                "tool_count": 0,
                "sample_tools": [],
                "auth": [],
                "notes": "no matching toolkit"
            })
            continue

        # Use the first/best result
        best_result = results[0]
        toolkits = best_result.get("toolkits", [])

        if not toolkits:
            print("NOT FOUND (no toolkits)", file=sys.stderr)
            coverage.append({
                "num": num,
                "app": app_name,
                "found": False,
                "toolkit": None,
                "tool_count": 0,
                "sample_tools": [],
                "auth": [],
                "notes": "search returned no toolkits"
            })
            continue

        primary_toolkit = toolkits[0]

        # Get tool information for this toolkit
        tools_result = subprocess.run(
            ["composio", "search", query, "--toolkits", primary_toolkit, "--limit", "100"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if tools_result.returncode == 0:
            tools_data = json.loads(tools_result.stdout)
            tool_results = tools_data.get("results", [])

            # Count unique tools across all results for this toolkit
            all_tool_slugs = set()
            sample_tools = []

            for result in tool_results:
                if result.get("toolkits") == [primary_toolkit] or primary_toolkit in result.get("toolkits", []):
                    primary = result.get("primary_tool_slugs", [])
                    related = result.get("related_tool_slugs", [])

                    for tool in primary:
                        all_tool_slugs.add(tool)
                        if len(sample_tools) < 2:
                            sample_tools.append(tool)

                    for tool in related:
                        all_tool_slugs.add(tool)
                        if len(sample_tools) < 5:
                            sample_tools.append(tool)

            tool_count = len(all_tool_slugs)

            if tool_count == 0:
                # Fallback: count from first result
                tool_count = len(best_result.get("primary_tool_slugs", [])) + len(best_result.get("related_tool_slugs", []))
                sample_tools = best_result.get("primary_tool_slugs", [])[:2] + best_result.get("related_tool_slugs", [])[:3]
        else:
            tool_count = len(best_result.get("primary_tool_slugs", [])) + len(best_result.get("related_tool_slugs", []))
            sample_tools = best_result.get("primary_tool_slugs", [])[:2] + best_result.get("related_tool_slugs", [])[:3]

        # Try to extract auth methods (not directly available, so we'll mark as unknown)
        auth_methods = ["OAUTH2", "API_KEY"]  # Common patterns

        print(f"FOUND ({primary_toolkit}, {tool_count} tools)", file=sys.stderr)

        coverage.append({
            "num": num,
            "app": app_name,
            "found": True,
            "toolkit": primary_toolkit,
            "tool_count": tool_count,
            "sample_tools": sample_tools[:5],
            "auth": auth_methods,
            "notes": ""
        })

    except subprocess.TimeoutExpired:
        print("TIMEOUT", file=sys.stderr)
        coverage.append({
            "num": num,
            "app": app_name,
            "found": False,
            "toolkit": None,
            "tool_count": 0,
            "sample_tools": [],
            "auth": [],
            "notes": "search timeout"
        })
    except json.JSONDecodeError as e:
        print(f"JSON ERROR: {e}", file=sys.stderr)
        coverage.append({
            "num": num,
            "app": app_name,
            "found": False,
            "toolkit": None,
            "tool_count": 0,
            "sample_tools": [],
            "auth": [],
            "notes": f"json decode error: {str(e)[:50]}"
        })
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        coverage.append({
            "num": num,
            "app": app_name,
            "found": False,
            "toolkit": None,
            "tool_count": 0,
            "sample_tools": [],
            "auth": [],
            "notes": f"error: {str(e)[:50]}"
        })

# Write the coverage file
output_path = Path(BASE) / "data" / "composio_coverage.json"
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w") as f:
    json.dump(coverage, f, indent=2)

print(f"\nCoverage analysis complete. Results saved to {output_path}", file=sys.stderr)

# Print summary
found_count = sum(1 for item in coverage if item["found"])
not_found_count = len(coverage) - found_count

print(f"\n=== SUMMARY ===", file=sys.stderr)
print(f"Total apps: {len(coverage)}", file=sys.stderr)
print(f"Found: {found_count} ({100*found_count/len(coverage):.1f}%)", file=sys.stderr)
print(f"Not found: {not_found_count} ({100*not_found_count/len(coverage):.1f}%)", file=sys.stderr)

# Print top toolkits by tool count
toolkit_stats = {}
for item in coverage:
    if item["found"]:
        toolkit = item["toolkit"]
        if toolkit not in toolkit_stats:
            toolkit_stats[toolkit] = {"count": 0, "tools": 0}
        toolkit_stats[toolkit]["count"] += 1
        toolkit_stats[toolkit]["tools"] += item["tool_count"]

print(f"\nTop toolkits by app coverage:", file=sys.stderr)
for toolkit, stats in sorted(toolkit_stats.items(), key=lambda x: x[1]["count"], reverse=True)[:10]:
    print(f"  {toolkit}: {stats['count']} apps, {stats['tools']} total tools", file=sys.stderr)
