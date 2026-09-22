"""
FastAPI Server for Warranty Claims Triage Agent.
Deployed on Google Cloud Run (Agent Runtime) and exposed to Gemini Enterprise.
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from tools.search_tools import (
    search_warranty_claims,
    search_tsb_repository,
    search_dealer_repair_orders,
    search_quality_engineering_wiki
)
from tools.ticket_tools import create_quality_ticket, CREATED_QE_TICKETS
from tools.slack_tools import notify_warranty_qe_channel, SENT_SLACK_NOTIFICATIONS
from skills.pattern_clustering import cluster_failure_patterns
from skills.severity_scoring import calculate_severity_score

# Explicitly configure Gemini Developer API (not Vertex AI)
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "false"

MOCK_DATA_MODE = os.getenv("MOCK_DATA_MODE", "true").lower() == "true"

app = FastAPI(
    title="Warranty Claims Triage Agent API",
    description="Agent Runtime service for analyzing warranty claims, TSBs, and repair orders, registered with Gemini Enterprise.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Request / Response Schemas -----------------

class TriageRequest(BaseModel):
    query: str = Field(
        ...,
        description="User query or triage instruction (e.g. 'Any recurring issues with Model X rear axle?')"
    )
    model: Optional[str] = Field(None, description="Optional vehicle model filter (e.g. 'Model X')")
    vin_prefix: Optional[str] = Field(None, description="Optional VIN prefix filter (e.g. '1XYZ4A2X')")
    component: Optional[str] = Field(None, description="Optional component filter")

class TriageResponse(BaseModel):
    summary: str = Field(description="Comprehensive triage findings and analysis")
    clusters_found: int = Field(description="Number of failure pattern clusters identified")
    clusters: List[Dict[str, Any]] = Field(description="Clustered failure details")
    severity_assessment: Optional[Dict[str, Any]] = Field(description="Calculated severity score and tier")
    tsb_matches: List[Dict[str, Any]] = Field(description="Correlating open TSBs")
    actions_taken: List[Dict[str, Any]] = Field(description="Created QE tickets and Slack notifications dispatched")

class MessageItem(BaseModel):
    role: str
    content: List[Dict[str, Any]]

class GleanAgentRequest(BaseModel):
    messages: List[MessageItem]

class GleanAgentResponse(BaseModel):
    messages: List[Dict[str, Any]]

# ----------------- Core Triage Engine -----------------

def run_triage_pipeline(query: str, model: Optional[str] = None, vin_prefix: Optional[str] = None, component: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes the multi-source triage pipeline combining claims search, repair orders,
    pattern clustering, TSB correlation, severity scoring, and auto-escalation.
    """
    q_lower = query.lower()

    # Extract intent filters if not explicitly provided
    if not model:
        if "model x" in q_lower:
            model = "Model X"
        elif "model y" in q_lower:
            model = "Model Y"
        elif "model s" in q_lower:
            model = "Model S"

    if not component:
        if "rear axle" in q_lower or "axle" in q_lower:
            component = "Rear Axle Assembly"
        elif "heat pump" in q_lower or "hvac" in q_lower:
            component = "HVAC Heat Pump"
        elif "control arm" in q_lower or "suspension" in q_lower:
            component = "Upper Control Arm"

    if not vin_prefix:
        for token in query.replace(",", " ").replace("?", " ").split():
            if len(token) == 8 and token.isalnum():
                vin_prefix = token.upper()

    # 1. Search claims
    claims = search_warranty_claims(model=model, vin_prefix=vin_prefix, component=component)
    
    # 2. Search dealer repair orders
    ros = search_dealer_repair_orders(model=model, vin_prefix=vin_prefix)

    # 3. Cluster failure patterns
    clusters = cluster_failure_patterns(claims, ros)

    # 4. Search TSBs
    tsb_matches = search_tsb_repository(model=model, component=component)

    # 5. Compute severity scoring
    severity_info = None
    actions_taken = []
    if clusters:
        top_cluster = clusters[0]
        comp = top_cluster["component"]
        all_descs = " ".join([c["failure_description"] for c in claims])
        has_tsb = len(tsb_matches) > 0
        severity_info = calculate_severity_score(
            component=comp,
            failure_description=all_descs,
            claim_count=top_cluster["claim_count"],
            average_cost=top_cluster["average_parts_cost"],
            has_open_tsb=has_tsb
        )

        # Auto-escalation if HIGH or CRITICAL
        if severity_info["escalation_required"] or top_cluster["claim_count"] >= 3:
            ticket = create_quality_ticket(
                title=f"Recurring {comp} Failures on {top_cluster['model']} ({top_cluster['vin_prefix']})",
                description=f"Clustered {top_cluster['claim_count']} warranty claims. Symptoms: {', '.join(top_cluster['primary_symptoms'])}. Severity: {severity_info['criticality_tier']}.",
                severity=severity_info["criticality_tier"],
                component=comp,
                affected_model=top_cluster["model"],
                affected_vin_prefix=top_cluster["vin_prefix"],
                claim_count=top_cluster["claim_count"],
                tsb_reference=tsb_matches[0]["tsb_id"] if tsb_matches else None
            )
            actions_taken.append({"action": "create_qe_ticket", "details": ticket})

            slack_res = notify_warranty_qe_channel(
                headline=f"Defect Spike Alert: {comp} on {top_cluster['model']}",
                summary=f"Identified {top_cluster['claim_count']} claims. Severity is {severity_info['criticality_tier']}. Created {ticket['ticket_id']}.",
                severity=severity_info["criticality_tier"],
                ticket_id=ticket["ticket_id"],
                affected_model=top_cluster["model"],
                claim_count=top_cluster["claim_count"]
            )
            actions_taken.append({"action": "notify_slack_channel", "details": slack_res})

    # 6. Format Markdown Summary
    summary_lines = [
        f"### Warranty Claims Triage Report",
        f"- **Target**: Model: `{model or 'All'}` | Component: `{component or 'All'}` | VIN Prefix: `{vin_prefix or 'All'}`",
        f"- **Claims Analyzed**: {len(claims)}",
        f"- **Dealer Repair Orders**: {len(ros)}",
        f"- **Matching Open TSBs**: {len(tsb_matches)}"
    ]

    if severity_info:
        summary_lines.append(f"- **Severity Tier**: **{severity_info['criticality_tier']}** (Score: {severity_info['severity_score']}/10)")
        summary_lines.append(f"- **Rationale**: {severity_info['rationale']}")

    if actions_taken:
        summary_lines.append(f"- **Escalations Dispatched**: {len(actions_taken)} actions (QE Ticket created and Slack alerted)")

    return {
        "summary": "\n".join(summary_lines),
        "clusters_found": len(clusters),
        "clusters": clusters,
        "severity_assessment": severity_info,
        "tsb_matches": tsb_matches,
        "actions_taken": actions_taken
    }

# ----------------- API Endpoints -----------------

STATIC_INDEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "index.html")

@app.get("/", tags=["Dashboard"])
def get_dashboard():
    """Serves the interactive Warranty Claims Triage Dashboard UI."""
    if os.path.exists(STATIC_INDEX):
        return FileResponse(STATIC_INDEX)
    return {"message": "Warranty Claims Triage Agent API is running. Visit /docs for OpenAPI interactive documentation."}

@app.get("/health", tags=["System"])
def health_check():
    """Liveness and readiness probe for Google Cloud Run / Agent Runtime."""
    return {
        "status": "healthy",
        "agent": "warranty_claims_triage_agent",
        "version": "1.0.0",
        "mock_data_mode": MOCK_DATA_MODE
    }

@app.post("/api/v1/triage", response_model=TriageResponse, tags=["Triage Agent"])
def triage_endpoint(request: TriageRequest):
    """
    Primary REST endpoint invoked by Gemini Enterprise or enterprise apps.
    Executes claims analysis, TSB lookup, severity scoring, and auto-escalation.
    """
    result = run_triage_pipeline(
        query=request.query,
        model=request.model,
        vin_prefix=request.vin_prefix,
        component=request.component
    )
    return result

@app.post("/chat", response_model=GleanAgentResponse, tags=["Chat"])
def glean_chat_compatibility(request: GleanAgentRequest):
    """
    Compatibility endpoint conforming directly to Glean's input/output schema.
    """
    last_text = ""
    for msg in request.messages:
        for block in msg.content:
            if block.get("type") == "text":
                last_text = block.get("text", "")

    result = run_triage_pipeline(query=last_text)
    
    response_text = f"{result['summary']}\n\n"
    if result["clusters"]:
        response_text += f"#### Identified Failure Clusters:\n"
        for c in result["clusters"]:
            response_text += f"- **{c['component']}** ({c['vin_prefix']}): {c['claim_count']} claims, avg cost ${c['average_parts_cost']:,}. Symptoms: {', '.join(c['primary_symptoms'])}\n"

    if result["actions_taken"]:
        response_text += f"\n#### Actions Executed:\n"
        for a in result["actions_taken"]:
            if a["action"] == "create_qe_ticket":
                t = a["details"]
                response_text += f"- Created QE Ticket **[{t['ticket_id']}]({t['ticket_url']})**: {t['title']} (Severity: {t['severity']})\n"
            elif a["action"] == "notify_slack_channel":
                response_text += f"- Sent alert notification to `#warranty-qe` channel\n"

    return {
        "messages": [
            {
                "role": "assistant",
                "content": [{"type": "text", "text": response_text}]
            }
        ]
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
