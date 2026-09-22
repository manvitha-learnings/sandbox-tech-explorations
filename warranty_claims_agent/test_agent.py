"""
Comprehensive automated test suite for Warranty Claims Triage Agent.
Tests:
- Search tools across the 4 data sources
- Severity scoring and pattern clustering skills
- Action tools (QE ticket creation, Slack notification)
- End-to-end triage scenarios matching all Glean trigger examples
- FastAPI server endpoints (/health, /api/v1/triage, /chat)
"""

try:
    import pytest
except ImportError:
    pytest = None
from fastapi.testclient import TestClient
from server import app, run_triage_pipeline
from tools.search_tools import (
    search_warranty_claims,
    search_tsb_repository,
    search_dealer_repair_orders,
    search_quality_engineering_wiki
)
from tools.ticket_tools import create_quality_ticket, CREATED_QE_TICKETS
from tools.slack_tools import notify_warranty_qe_channel, SENT_SLACK_NOTIFICATIONS
from skills.severity_scoring import calculate_severity_score
from skills.pattern_clustering import cluster_failure_patterns

client = TestClient(app)

# ----------------- 1. Search Tool Tests -----------------

def test_search_warranty_claims_by_model():
    claims = search_warranty_claims(model="Model X")
    assert len(claims) >= 4
    for c in claims:
        assert c["model"] == "Model X"

def test_search_warranty_claims_by_vin_prefix():
    claims = search_warranty_claims(vin_prefix="1XYZ4A2X")
    assert len(claims) >= 4
    assert all(c["vin_prefix"] == "1XYZ4A2X" for c in claims)

def test_search_warranty_claims_by_component():
    claims = search_warranty_claims(component="Rear Axle")
    assert len(claims) >= 4
    assert all("Axle" in c["component"] for c in claims)

def test_search_tsb_repository():
    tsbs = search_tsb_repository(model="Model X", component="Rear Axle")
    assert len(tsbs) >= 1
    assert tsbs[0]["tsb_id"] == "TSB-25-03-014"
    assert tsbs[0]["status"] == "OPEN"

def test_search_dealer_repair_orders():
    ros = search_dealer_repair_orders(vin_prefix="1XYZ4A2X")
    assert len(ros) >= 3
    assert any("P079A" in ro["dtc_codes"] for ro in ros)

def test_search_quality_wiki():
    articles = search_quality_engineering_wiki("rear axle")
    assert len(articles) >= 1
    assert "WIKI-QE-042" in articles[0]["article_id"]

# ----------------- 2. Skills Tests -----------------

def test_severity_scoring_critical():
    score_res = calculate_severity_score(
        component="Rear Axle Assembly",
        failure_description="Catastrophic pinion gear teeth sheared completely, axle seizure and wheel lockup while driving.",
        claim_count=4,
        average_cost=3100.0,
        has_open_tsb=True
    )
    assert score_res["severity_score"] >= 8.5
    assert score_res["criticality_tier"] in ["HIGH", "CRITICAL"]
    assert score_res["escalation_required"] is True

def test_severity_scoring_low():
    score_res = calculate_severity_score(
        component="Interior Trim",
        failure_description="Slight cosmetic clip rattle over rough pavement.",
        claim_count=1,
        average_cost=150.0,
        has_open_tsb=False
    )
    assert score_res["severity_score"] < 5.0
    assert score_res["criticality_tier"] == "LOW"
    assert score_res["escalation_required"] is False

def test_failure_pattern_clustering():
    claims = search_warranty_claims(model="Model X")
    ros = search_dealer_repair_orders(model="Model X")
    clusters = cluster_failure_patterns(claims, ros)
    assert len(clusters) >= 1
    top = clusters[0]
    assert top["component"] == "Rear Axle Assembly"
    assert top["claim_count"] >= 4
    assert top["vin_prefix"] == "1XYZ4A2X"
    assert top["matching_ro_count"] >= 3

# ----------------- 3. Action Tools Tests -----------------

def test_create_quality_ticket():
    initial_count = len(CREATED_QE_TICKETS)
    ticket = create_quality_ticket(
        title="Test Axle Defect",
        description="Automated unit test defect payload",
        severity="HIGH",
        component="Rear Axle Assembly",
        affected_model="Model X",
        affected_vin_prefix="1XYZ4A2X",
        claim_count=4,
        tsb_reference="TSB-25-03-014"
    )
    assert ticket["ticket_id"].startswith("QE-2026-")
    assert ticket["severity"] == "HIGH"
    assert ticket["status"] == "OPEN_INVESTIGATION"
    assert len(CREATED_QE_TICKETS) == initial_count + 1

def test_notify_slack_channel():
    initial_count = len(SENT_SLACK_NOTIFICATIONS)
    res = notify_warranty_qe_channel(
        headline="Test Slack Alert",
        summary="Test summary message",
        severity="CRITICAL",
        ticket_id="QE-2026-101",
        affected_model="Model X",
        claim_count=4
    )
    assert res["status"] == "SENT"
    assert res["channel"] == "#warranty-qe"
    assert len(SENT_SLACK_NOTIFICATIONS) == initial_count + 1

# ----------------- 4. End-to-End Triage Trigger Scenarios -----------------

def test_trigger_scenario_1_recurring_model_x_axle():
    """Trigger 1: 'Any recurring issues with the Model X rear axle claims this month?'"""
    res = run_triage_pipeline("Any recurring issues with the Model X rear axle claims this month?")
    assert res["clusters_found"] >= 1
    assert len(res["tsb_matches"]) >= 1
    assert res["severity_assessment"] is not None
    assert res["severity_assessment"]["criticality_tier"] in ["HIGH", "CRITICAL"]
    # Escalation actions verified
    assert len(res["actions_taken"]) >= 2
    actions = [a["action"] for a in res["actions_taken"]]
    assert "create_qe_ticket" in actions
    assert "notify_slack_channel" in actions

def test_trigger_scenario_2_vin_prefix_summary():
    """Trigger 2: 'Summarize warranty claims for VIN prefix 1XYZ4A2X in the last 30 days'"""
    res = run_triage_pipeline("Summarize warranty claims for VIN prefix 1XYZ4A2X in the last 30 days")
    assert res["clusters_found"] >= 1
    top_cluster = res["clusters"][0]
    assert top_cluster["vin_prefix"] == "1XYZ4A2X"
    assert top_cluster["claim_count"] >= 4
    assert top_cluster["total_parts_cost"] > 10000

def test_trigger_scenario_3_tsb_matching():
    """Trigger 3: 'Does this claim match any open TSB?'"""
    res = run_triage_pipeline("Does this claim match any open TSB for Model X rear axle whine and vibration?")
    assert len(res["tsb_matches"]) >= 1
    assert res["tsb_matches"][0]["tsb_id"] == "TSB-25-03-014"

# ----------------- 5. Server REST Endpoints Tests -----------------

def test_server_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["agent"] == "warranty_claims_triage_agent"

def test_server_triage_api():
    payload = {
        "query": "Investigate Model X rear axle claims",
        "model": "Model X",
        "component": "Rear Axle Assembly"
    }
    response = client.post("/api/v1/triage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["clusters_found"] >= 1
    assert "Warranty Claims Triage Report" in data["summary"]

def test_server_glean_chat_compatibility():
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": "Any recurring issues with the Model X rear axle claims this month?"}]
            }
        ]
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) > 0
    text = data["messages"][0]["content"][0]["text"]
    assert "Warranty Claims Triage Report" in text
    assert "Rear Axle Assembly" in text
