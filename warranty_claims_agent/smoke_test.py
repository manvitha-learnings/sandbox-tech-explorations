"""
Smoke tests for Warranty Claims Triage Agent.
Performs live smoke checks against API endpoints and validates realistic agent triage responses.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def run_smoke_tests():
    print("=" * 70)
    print(" STARTING WARRANTY CLAIMS TRIAGE AGENT SMOKE TESTS")
    print("=" * 70)

    # 1. Health Check Smoke Test
    print("\n[SMOKE TEST 1/4] GET /health")
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed with {res.status_code}"
    health_data = res.json()
    print(f"--> Status: {res.status_code} OK")
    print(f"--> Payload: {json.dumps(health_data, indent=2)}")
    assert health_data["status"] == "healthy"
    assert health_data["agent"] == "warranty_claims_triage_agent"
    print(" SMOKE TEST 1 PASSED: Health endpoint is healthy.")

    # 2. OpenAPI Specification Smoke Test
    print("\n[SMOKE TEST 2/4] GET /openapi.json")
    res = client.get("/openapi.json")
    assert res.status_code == 200, f"OpenAPI failed with {res.status_code}"
    schema = res.json()
    print(f"--> Status: {res.status_code} OK")
    print(f"--> Title: {schema.get('info', {}).get('title')}")
    print(f"--> Available Endpoints: {list(schema.get('paths', {}).keys())}")
    assert "/api/v1/triage" in schema.get("paths", {})
    assert "/chat" in schema.get("paths", {})
    assert "/health" in schema.get("paths", {})
    print(" SMOKE TEST 2 PASSED: OpenAPI schema is fully generated and valid.")

    # 3. Primary Triage API Smoke Test (Glean Trigger 1: Model X Rear Axle)
    print("\n[SMOKE TEST 3/4] POST /api/v1/triage (Recurring Issue Investigation)")
    payload = {
        "query": "Any recurring issues with the Model X rear axle claims this month?",
        "model": "Model X",
        "component": "Rear Axle Assembly"
    }
    res = client.post("/api/v1/triage", json=payload)
    assert res.status_code == 200, f"Triage request failed: {res.status_code}"
    data = res.json()
    print(f"--> Status: {res.status_code} OK")
    print(f"--> Clusters Found: {data['clusters_found']}")
    print(f"--> Severity Tier: {data['severity_assessment']['criticality_tier']} (Score: {data['severity_assessment']['severity_score']}/10)")
    print(f"--> Open TSB Matched: {data['tsb_matches'][0]['tsb_id']} - {data['tsb_matches'][0]['title']}")
    print(f"--> Actions Dispatched: {len(data['actions_taken'])}")
    for a in data["actions_taken"]:
        if a["action"] == "create_qe_ticket":
            t = a["details"]
            print(f"    * QE Ticket Created: {t['ticket_id']} ({t['title']})")
        elif a["action"] == "notify_slack_channel":
            s = a["details"]
            print(f"    * Slack Alert Sent: {s['channel']} - {s['message_headline']}")
    assert data["clusters_found"] >= 1
    assert data["severity_assessment"]["criticality_tier"] in ["HIGH", "CRITICAL"]
    assert len(data["actions_taken"]) >= 2
    print(" SMOKE TEST 3 PASSED: Triage pipeline correctly analyzed claims, matched TSB, and auto-escalated.")

    # 4. Glean Chat Compatibility Smoke Test (Glean Input/Output Format)
    print("\n[SMOKE TEST 4/4] POST /chat (Glean Schema Compatibility)")
    glean_payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Summarize warranty claims for VIN prefix 1XYZ4A2X in the last 30 days"
                    }
                ]
            }
        ]
    }
    res = client.post("/chat", json=glean_payload)
    assert res.status_code == 200, f"Glean chat failed: {res.status_code}"
    chat_data = res.json()
    print(f"--> Status: {res.status_code} OK")
    assert "messages" in chat_data
    assistant_msg = chat_data["messages"][0]["content"][0]["text"]
    print("--> Assistant Response Preview:")
    for line in assistant_msg.split("\n")[:6]:
        print(f"    {line}")
    assert "Warranty Claims Triage Report" in assistant_msg
    print(" SMOKE TEST 4 PASSED: Glean chat format compatibility confirmed.")

    print("\n" + "=" * 70)
    print(" ALL 4 SMOKE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_smoke_tests()
