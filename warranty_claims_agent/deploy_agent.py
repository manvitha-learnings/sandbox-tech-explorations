"""
Automated Deployment Script for Warranty Claims Triage Agent.
1. Builds Docker container using Google Cloud Build.
2. Deploys container to Google Cloud Run configured with GEMINI_API_KEY.
3. Retrieves live URL and generates OpenAPI 3.0 schema.
"""

import os
import sys
import subprocess
import json
from dotenv import load_dotenv

# Load GEMINI_API_KEY
base_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_dir, ".env")
load_dotenv(env_path)

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env file.")
    sys.exit(1)

project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-83b9dd42-537f-47c6-a28")
region = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
service_name = "warranty-claims-triage-agent"
image = f"{region}-docker.pkg.dev/{project_id}/agent-runtime-repo/{service_name}:latest"

print("=" * 65)
print(" STARTING CLOUD RUN DEPLOYMENT")
print(f" Project: {project_id}")
print(f" Region:  {region}")
print(f" Image:   {image}")
print(" Mode:    Google AI Studio Gemini API + Cloud Run")
print("=" * 65)

gcloud_cmd = r"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
if not os.path.exists(gcloud_cmd):
    gcloud_cmd = "gcloud"

# Step 1: Build image with Cloud Build
print("\n--> [1/4] Building container in Google Cloud Build...")
build_args = [
    gcloud_cmd, "builds", "submit",
    f"--tag={image}",
    f"--project={project_id}",
    base_dir
]
build_res = subprocess.run(build_args, capture_output=True, text=True)
print(build_res.stdout)
if build_res.returncode != 0:
    print("Build failed with error:")
    print(build_res.stderr)
    sys.exit(build_res.returncode)

# Step 2: Deploy to Cloud Run
print("\n--> [2/4] Deploying container to Cloud Run...")
deploy_args = [
    gcloud_cmd,
    "run", "deploy", service_name,
    f"--image={image}",
    f"--region={region}",
    "--platform=managed",
    "--allow-unauthenticated",
    f"--set-env-vars=GEMINI_API_KEY={api_key},MOCK_DATA_MODE=true,MODEL_NAME=gemini-2.5-flash,GLEAN_AGENT_GCS_URI=gs://glean_agent/warranty_claims_triage_agent.json",
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

# Step 3: Retrieve live service URL
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

# Step 4: Generate OpenAPI schema
print("\n--> [4/4] Generating live OpenAPI 3.0 schema...")
openapi_schema = {
    "openapi": "3.0.3",
    "info": {
        "title": "Warranty Claims Triage Agent API",
        "description": "Analyzes incoming warranty claims, dealer repair orders, and TSBs to detect recurring defect patterns, flag known open issues, and draft triage summaries for Quality Engineering.",
        "version": "1.0.0"
    },
    "servers": [
        {
            "url": service_url,
            "description": "Cloud Run Agent Endpoint"
        }
    ],
    "paths": {
        "/api/v1/triage": {
            "post": {
                "operationId": "triageWarrantyClaims",
                "summary": "Triage warranty claims, TSBs, and repair orders",
                "description": "Performs defect spike detection, pattern clustering, and severity scoring for vehicle models and VIN prefixes.",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["query"],
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "User question or triage prompt (e.g., 'Any recurring issues with Model X rear axle?')"
                                    },
                                    "model": {
                                        "type": "string",
                                        "description": "Optional vehicle model filter (e.g., 'Model X')"
                                    },
                                    "vin_prefix": {
                                        "type": "string",
                                        "description": "Optional 8-character VIN prefix (e.g., '1XYZ4A2X')"
                                    },
                                    "component": {
                                        "type": "string",
                                        "description": "Optional component name (e.g., 'Rear Axle Assembly')"
                                    }
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
                                        "summary": { "type": "string" },
                                        "clusters_found": { "type": "integer" },
                                        "severity_assessment": { "type": "object" },
                                        "tsb_matches": { "type": "array", "items": { "type": "object" } },
                                        "actions_taken": { "type": "array", "items": { "type": "object" } }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

schema_file = os.path.join(base_dir, "gemini_enterprise_openapi.json")
with open(schema_file, "w", encoding="utf-8") as f:
    json.dump(openapi_schema, f, indent=2)

print(f" Schema saved to: {schema_file}")
print("\n" + "=" * 65)
print(" DEPLOYMENT COMPLETE!")
print(f" Service URL:   {service_url}")
print(f" Web Dashboard: {service_url}/")
print(f" Health Check:  {service_url}/health")
print(f" OpenAPI Docs:  {service_url}/docs")
print(f" OpenAPI JSON:  {service_url}/openapi.json")
print("=" * 65)
