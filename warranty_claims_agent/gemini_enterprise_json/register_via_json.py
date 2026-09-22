"""
Automated registration script for Gemini Enterprise / Vertex AI Agent Builder.
Registers the Agent manifest, Data Store search tool, and OpenAPI tools using Google Cloud REST APIs.
"""

import os
import sys
import json
import requests
import google.auth
import google.auth.transport.requests

def get_auth_token():
    credentials, project_id = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    return credentials.token, project_id

def register_agent(project_id: str, location: str = "global"):
    token, default_project = get_auth_token()
    project = project_id or default_project
    if not project:
        print("ERROR: Google Cloud Project ID must be provided via GOOGLE_CLOUD_PROJECT env var or argument.")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    base_dir = os.path.dirname(os.path.abspath(__file__))
    manifest_path = os.path.join(base_dir, "agent_manifest.json")

    with open(manifest_path, "r") as f:
        manifest_raw = f.read()

    # Interpolate project and location variables
    manifest_raw = manifest_raw.replace("${PROJECT_ID}", project).replace("${LOCATION}", location)
    manifest = json.loads(manifest_raw)

    print(f"--> Registering Agent in Gemini Enterprise / Vertex AI Agent Builder...")
    print(f"    Project: {project}")
    print(f"    Location: {location}")
    print(f"    Agent: {manifest.get('displayName')}")

    endpoint = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project}/locations/{location}/agents"

    response = requests.post(endpoint, json=manifest, headers=headers)
    if response.status_code in [200, 201]:
        print(" SUCCESS: Agent successfully registered in Gemini Enterprise!")
        print(json.dumps(response.json(), indent=2))
    elif response.status_code == 409:
        print(" NOTICE: Agent already exists in project. Triggering update...")
        update_endpoint = f"{endpoint}/warranty-claims-triage-agent"
        patch_res = requests.patch(update_endpoint, json=manifest, headers=headers)
        if patch_res.status_code == 200:
            print(" SUCCESS: Agent updated successfully!")
        else:
            print(f" ERROR: Failed to update agent: {patch_res.text}")
    else:
        print(f" Registration returned HTTP {response.status_code}: {response.text}")
        print("\nTip: Ensure Vertex AI Agent Builder API (discoveryengine.googleapis.com) is enabled.")

if __name__ == "__main__":
    proj = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    loc = os.getenv("GOOGLE_CLOUD_REGION", "global")
    register_agent(project_id=proj, location=loc)
