"""
Register the Warranty Claims Triage Agent (deployed on Vertex AI Agent Runtime /
Agent Engine) into a Gemini Enterprise app.

Metadata (display name, description, starter prompts) is taken verbatim from the
Glean export (Warranty_claims_triage.json) and instructions.md so the Gemini
Enterprise registration mirrors the original Glean agent.

Usage:
    python register_gemini_enterprise.py --reasoning-engine projects/<num>/locations/us-central1/reasoningEngines/<id>
        [--project project-05a72bf9-0da1-467e-b90] [--engine-id <gemini_enterprise_app_id>] [--location global]

If --engine-id is omitted, the script lists the Gemini Enterprise apps in the
project and uses it only if exactly one exists.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GLEAN_JSON_CANDIDATES = [
    os.path.join(os.path.dirname(BASE_DIR), "Warranty_claims_triage.json"),
    os.path.join(BASE_DIR, "Warranty_claims_triage.json"),
]

STARTER_PROMPTS = [
    "Are there recurring issues with Chevrolet Silverado brake failures or loss of assist?",
    "Analyze recent steering lockup complaints and TSB matches for Honda Accord.",
    "Summarize high-severity transmission shudder defect clusters for Ford F-150.",
    "Check open TSBs and recalls for Toyota RAV4 electrical and hybrid cable issues.",
]


def gcloud_token() -> str:
    gcloud = shutil.which("gcloud.cmd") or shutil.which("gcloud") or \
        r"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
    return subprocess.check_output([gcloud, "auth", "print-access-token"], text=True).strip()


def http(method: str, url: str, headers: dict, body: dict = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} for {method} {url}\n{e.read().decode('utf-8', 'replace')}")
        raise


def load_glean_metadata() -> dict:
    for path in GLEAN_JSON_CANDIDATES:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    cache = os.path.join(BASE_DIR, "data", "glean_agent_cache.json")
    with open(cache, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="project-05a72bf9-0da1-467e-b90")
    ap.add_argument("--location", default="global", help="Gemini Enterprise app location (global, us, eu)")
    ap.add_argument("--engine-id", default=None, help="Gemini Enterprise app (engine) ID")
    ap.add_argument("--reasoning-engine", required=True, help="Full Agent Engine resource name")
    args = ap.parse_args()

    glean = load_glean_metadata()
    display_name = glean["name"]
    description = glean["description"]

    host = "discoveryengine.googleapis.com" if args.location == "global" \
        else f"{args.location}-discoveryengine.googleapis.com"
    base = f"https://{host}/v1alpha/projects/{args.project}/locations/{args.location}/collections/default_collection"
    headers = {
        "Authorization": f"Bearer {gcloud_token()}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": args.project,
    }

    engine_id = args.engine_id
    if not engine_id:
        engines = http("GET", f"{base}/engines", headers).get("engines", [])
        print("Gemini Enterprise apps found:")
        for e in engines:
            print(f"  - {e['name'].split('/')[-1]} | {e.get('displayName')} | {e.get('solutionType')}")
        if len(engines) != 1:
            print("Pass --engine-id explicitly (found %d apps)." % len(engines))
            sys.exit(2)
        engine_id = engines[0]["name"].split("/")[-1]

    agents_url = f"{base}/engines/{engine_id}/assistants/default_assistant/agents"

    payload = {
        "displayName": display_name,
        "description": description,
        "starterPrompts": [{"text": p} for p in STARTER_PROMPTS],
        "adkAgentDefinition": {
            "toolSettings": {"toolDescription": description},
            "provisionedReasoningEngine": {"reasoningEngine": args.reasoning_engine},
        },
    }

    # Idempotency: update an existing ADK registration with the same display name.
    existing = None
    for a in http("GET", agents_url, headers).get("agents", []):
        if a.get("displayName") == display_name and "adkAgentDefinition" in a:
            existing = a
            break

    if existing:
        print(f"Updating existing registration: {existing['name']}")
        result = http(
            "PATCH",
            f"https://{host}/v1alpha/{existing['name']}?updateMask=displayName,description,starterPrompts,adkAgentDefinition",
            headers, payload,
        )
    else:
        print(f"Creating new registration in app '{engine_id}'")
        result = http("POST", agents_url, headers, payload)

    print(json.dumps(result, indent=2))
    out = os.path.join(BASE_DIR, "gemini_enterprise_registration.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"\n[OK] Registered '{display_name}' -> {args.reasoning_engine}")
    print(f"     Saved registration to {out}")


if __name__ == "__main__":
    main()
