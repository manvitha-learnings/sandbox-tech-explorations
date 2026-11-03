"""
Automated Deployment Script for Warranty Claims Triage Agent.
1. Builds Docker container using Google Cloud Build (includes BigQuery, PyYAML, ADK).
2. Deploys container to Google Cloud Run with NHTSA BigQuery and GCS configurations.
3. Retrieves live URL and generates OpenAPI 3.0 schema.
4. Registers and synchronizes the Agent with Gemini Enterprise (Vertex AI Agent Builder).
"""

import os
import sys
import subprocess
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

# Load env
base_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_dir, ".env")
load_dotenv(env_path)

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env file.")
    sys.exit(1)

project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-05a72bf9-0da1-467e-b90")
region = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
service_name = "warranty-claims-triage-agent"
image = f"{region}-docker.pkg.dev/{project_id}/agent-runtime-repo/{service_name}:latest"

# Gemini Enterprise identifiers for project-05a72bf9-0da1-467e-b90
ENGINE_ID = "warranty-claims-triage"
AGENT_ID  = "4765741837975805445"

print("=" * 65)
print(" STARTING CLOUD RUN + GEMINI ENTERPRISE DEPLOYMENT")
print(f" Project: {project_id}")
print(f" Region:  {region}")
print(f" Image:   {image}")
print(f" Engine:  {ENGINE_ID}")
print(f" Agent:   {AGENT_ID}")
print("=" * 65)

gcloud_cmd = r"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
if not os.path.exists(gcloud_cmd):
    gcloud_cmd = "gcloud"

# ── Step 1: Build image with Cloud Build ──────────────────────────────────────
print("\n--> [1/4] Building container in Google Cloud Build...")
build_args = [
    gcloud_cmd, "builds", "submit",
    f"--tag={image}",
    f"--project={project_id}",
    "--suppress-logs",
    base_dir
]
build_res = subprocess.run(build_args, capture_output=True, text=True)
print(build_res.stdout)
if build_res.returncode != 0:
    check_cmd = [gcloud_cmd, "builds", "list", f"--project={project_id}",
                 "--limit=1", "--format=value(status)"]
    check_res = subprocess.run(check_cmd, capture_output=True, text=True)
    if "SUCCESS" in check_res.stdout:
        print("--> Cloud Build status: SUCCESS (log streaming skipped).")
    else:
        print("Build failed with error:")
        print(build_res.stderr)
        sys.exit(build_res.returncode)
else:
    print("--> Cloud Build completed successfully.")

# ── Step 2: Deploy to Cloud Run ───────────────────────────────────────────────
print("\n--> [2/4] Deploying container to Cloud Run...")
env_vars = [
    f"GEMINI_API_KEY={api_key}",
    f"MODEL_NAME={os.getenv('MODEL_NAME', 'gemini-3.5-flash-lite')}",
    f"MOCK_DATA_MODE={os.getenv('MOCK_DATA_MODE', 'false')}",
    "GOOGLE_GENAI_USE_VERTEXAI=false",
    f"GLEAN_AGENT_GCS_URI={os.getenv('GLEAN_AGENT_GCS_URI', 'gs://glean_agent_code/Warranty_claims_triage.json')}",
    f"GLEAN_AGENT_GCS_BUCKET={os.getenv('GLEAN_AGENT_GCS_BUCKET', 'glean_agent_code')}",
    f"GLEAN_AGENT_FILES_URI={os.getenv('GLEAN_AGENT_FILES_URI', 'gs://glean_agent_code/spec.yaml')}",
    f"BIGQUERY_PROJECT_ID={os.getenv('BIGQUERY_PROJECT_ID', project_id)}",
    f"BIGQUERY_DATASET={os.getenv('BIGQUERY_DATASET', 'automotive_warranty_triage')}",
]
for k in ["JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY",
          "SLACK_BOT_TOKEN", "SLACK_CHANNEL_ID"]:
    v = os.getenv(k)
    if v:
        env_vars.append(f"{k}={v}")

deploy_args = [
    gcloud_cmd, "run", "deploy", service_name,
    f"--image={image}",
    f"--region={region}",
    "--platform=managed",
    "--allow-unauthenticated",
    "--memory=1Gi",
    "--cpu=1",
    "--timeout=300",
    f"--set-env-vars={','.join(env_vars)}",
    f"--project={project_id}"
]

result = subprocess.run(deploy_args, capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print("Cloud Run deploy output / error:")
    print(result.stderr)
    if "ERROR" in result.stderr:
        print("Deploy failed.")
        sys.exit(result.returncode)

# ── Step 3: Retrieve live URL + generate OpenAPI schema ───────────────────────
print("\n--> [3/4] Retrieving live service URL...")
url_cmd = [
    gcloud_cmd, "run", "services", "describe", service_name,
    f"--region={region}",
    "--format=value(status.url)",
    f"--project={project_id}"
]
url_res = subprocess.run(url_cmd, capture_output=True, text=True)
service_url = url_res.stdout.strip()
print(f" LIVE SERVICE URL: {service_url}")

openapi_schema = {
    "openapi": "3.0.3",
    "info": {
        "title": "Warranty Claims Triage Agent API",
        "description": (
            "Analyzes incoming warranty claims, dealer repair orders, and TSBs "
            "to detect recurring defect patterns, flag known open issues, and "
            "draft triage summaries for Quality Engineering."
        ),
        "version": "1.0.0"
    },
    "servers": [{"url": service_url, "description": "Cloud Run Agent Runtime Endpoint"}],
    "paths": {
        "/api/v1/triage": {
            "post": {
                "operationId": "triageWarrantyClaims",
                "summary": "Triage warranty claims, TSBs, and repair orders",
                "description": "Performs defect spike detection, pattern clustering, and severity scoring against NHTSA BigQuery data.",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["query"],
                                "properties": {
                                    "query": {"type": "string", "description": "User triage question"},
                                    "model": {"type": "string", "description": "Optional vehicle model filter"},
                                    "vin_prefix": {"type": "string", "description": "Optional 8-char VIN prefix"},
                                    "component": {"type": "string", "description": "Optional component name"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Successful triage analysis",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string"},
                                        "summary": {"type": "string"},
                                        "clusters_found": {"type": "integer"},
                                        "severity_assessment": {"type": "object"},
                                        "tsb_matches": {"type": "array", "items": {"type": "object"}},
                                        "actions_taken": {"type": "array", "items": {"type": "object"}}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/chat": {
            "post": {
                "operationId": "gleanCompatibleChat",
                "summary": "Glean-compatible chat endpoint",
                "description": "Accepts Glean message schema and returns triage analysis as assistant message.",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["messages"],
                                "properties": {
                                    "messages": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "role": {"type": "string"},
                                                "content": {"type": "array", "items": {"type": "object"}}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Agent reply in Glean message format"}
                }
            }
        }
    }
}

schema_file = os.path.join(base_dir, "gemini_enterprise_openapi.json")
with open(schema_file, "w", encoding="utf-8") as f:
    json.dump(openapi_schema, f, indent=2)
print(f" OpenAPI schema saved to: {schema_file}")

# ── Step 4: Register and Synchronize with Gemini Enterprise ───────────────────
print("\n--> [4/4] Registering and synchronizing with Gemini Enterprise...")

token_res = subprocess.run(
    [gcloud_cmd, "auth", "print-access-token"],
    capture_output=True, text=True
)
access_token = token_res.stdout.strip()

if not access_token:
    print(" WARNING: Could not retrieve gcloud access token. Skipping Gemini Enterprise sync.")
else:
    # 1. Update Agent instructions in Gemini Enterprise from instructions.md
    instructions_file = os.path.join(base_dir, "data", "instructions.md")
    if os.path.exists(instructions_file):
        with open(instructions_file, "r", encoding="utf-8") as f:
            instructions_content = f.read()
    else:
        from glean_config_loader import load_glean_config
        cfg = load_glean_config()
        instructions_content = cfg.get("instructions", "")

    agent_url = (
        f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}"
        f"/locations/global/collections/default_collection"
        f"/engines/{ENGINE_ID}/assistants/default_assistant/agents/{AGENT_ID}"
    )
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id
    }

    try:
        # Fetch current agent definition
        get_req = urllib.request.Request(agent_url, headers=headers)
        with urllib.request.urlopen(get_req, timeout=30) as resp:
            agent_data = json.loads(resp.read())

        # Update root node instruction
        nodes = agent_data.get("lowCodeAgentDefinition", {}).get("nodes", [])
        if nodes:
            nodes[0]["llmAgentNode"]["instruction"] = instructions_content
        deployed_nodes = agent_data.get("lowCodeAgentDefinition", {}).get("deployedNodes", [])
        if deployed_nodes:
            deployed_nodes[0]["llmAgentNode"]["instruction"] = instructions_content

        # Update draft description
        agent_data["lowCodeAgentDefinition"]["draftDescription"] = (
            "Analyzes warranty claims, dealer repair orders, and TSBs using BigQuery NHTSA data "
            "to detect recurring failure patterns and auto-escalate for Quality Engineering."
        )

        patch_req = urllib.request.Request(
            f"{agent_url}?updateMask=lowCodeAgentDefinition",
            data=json.dumps(agent_data).encode("utf-8"),
            method="PATCH",
            headers=headers
        )
        with urllib.request.urlopen(patch_req, timeout=30) as resp:
            updated = json.loads(resp.read())
            print(f" [OK] Gemini Enterprise Agent instructions synchronized ({len(instructions_content)} chars)")
            print(f" [OK] Display Name: {updated.get('displayName', AGENT_ID)}")

        # Publish the updated agent revision
        pub_req = urllib.request.Request(
            f"{agent_url}:publish",
            data=b"{}",
            method="POST",
            headers=headers
        )
        try:
            with urllib.request.urlopen(pub_req, timeout=30) as pub_resp:
                pub_result = json.loads(pub_resp.read())
                print(f" [OK] Agent revision successfully published: {pub_result.get('name')}")
        except Exception as p_err:
            print(f" Notice: Publish result: {p_err}")
    except Exception as e:
        print(f" Notice: Gemini Enterprise API update encountered: {e}")

print("\n" + "=" * 65)
print(" DEPLOYMENT COMPLETE!")
print(f" Service URL:       {service_url}")
print(f" Web Dashboard:     {service_url}/")
print(f" Health Check:      {service_url}/health")
print(f" OpenAPI Docs:      {service_url}/docs")
print(f" OpenAPI JSON:      {service_url}/openapi.json")
print(f" Gemini Enterprise: https://console.cloud.google.com/gen-app-builder/engines/{ENGINE_ID}/preview?project={project_id}")
print("=" * 65)
