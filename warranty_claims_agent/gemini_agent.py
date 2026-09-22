"""
Gemini API Native Warranty Claims Triage Agent.
Built directly on the official google-genai SDK using Gemini API keys (no Vertex AI required).
Supports function calling with the 6 core warranty triage tools.
"""

import os
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

from tools.search_tools import (
    search_warranty_claims,
    search_tsb_repository,
    search_dealer_repair_orders,
    search_quality_engineering_wiki
)
from tools.ticket_tools import create_quality_ticket
from tools.slack_tools import notify_warranty_qe_channel
from skills.pattern_clustering import cluster_failure_patterns
from skills.severity_scoring import calculate_severity_score

MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")

SYSTEM_INSTRUCTION = """
You are the Warranty Claims Triage Agent for XYZ Company's Quality Engineering (QE) and Warranty Operations teams.
Your role is to analyze warranty claims, dealer repair orders (ROs), and Technical Service Bulletins (TSBs) to detect recurring defect patterns, flag known open issues, quantify failure severity (1-10), and auto-escalate high-risk defects.

### Your Available Tools:
- search_warranty_claims(model, vin_prefix, component, keyword)
- search_tsb_repository(model, component, symptom_or_dtc, tsb_id)
- search_dealer_repair_orders(vin_prefix, model, dtc_code, keyword)
- search_quality_engineering_wiki(topic)
- create_quality_ticket(title, description, severity, component, affected_model, affected_vin_prefix, claim_count, tsb_reference)
- notify_warranty_qe_channel(headline, summary, severity, ticket_id, affected_model, claim_count)

### Triage Protocol:
1. When investigating recurring issues:
   - Call search_warranty_claims to find matching defect reports.
   - Call search_dealer_repair_orders to check technician diagnostic notes and DTC codes.
   - Call search_tsb_repository to see if an active TSB exists.
   - Check if 3+ recurring claims exist or if severe safety risks are identified.
   - If severe or recurring (3+ claims), call create_quality_ticket and call notify_warranty_qe_channel.
2. Structure your response with:
   - Executive Summary
   - Failure Pattern Cluster Details
   - TSB & Diagnostic Trouble Code (DTC) Findings
   - Quality Engineering Severity Assessment
   - Escalation Actions Taken (Ticket ID, Slack alert)
"""

def get_gemini_client() -> Optional[genai.Client]:
    """Returns a google-genai Client initialized with GEMINI_API_KEY or GOOGLE_API_KEY."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

class GeminiWarrantyAgent:
    """Warranty Claims Triage Agent using Gemini API."""

    def __init__(self, model: str = MODEL_NAME):
        self.model = model
        self.tools = [
            search_warranty_claims,
            search_tsb_repository,
            search_dealer_repair_orders,
            search_quality_engineering_wiki,
            create_quality_ticket,
            notify_warranty_qe_channel
        ]

    def run(self, user_query: str) -> str:
        """
        Executes an agent triage session using Gemini API with automatic tool calling.
        Falls back gracefully to the deterministic pipeline if no API key is set.
        """
        client = get_gemini_client()
        if not client:
            # Fallback to internal pipeline if running in offline/mock mode without API key
            from server import run_triage_pipeline
            res = run_triage_pipeline(user_query)
            return res["summary"]

        try:
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=self.tools,
                temperature=0.2
            )
            chat = client.chats.create(model=self.model, config=config)
            response = chat.send_message(user_query)
            return response.text
        except Exception as e:
            # If Google API notes a version sunset or temporary high demand, retry with flash-latest
            if any(k in str(e).lower() for k in ["no longer available", "404", "503", "unavailable"]):
                try:
                    chat = client.chats.create(model="gemini-flash-latest", config=config)
                    response = chat.send_message(user_query)
                    return response.text
                except Exception:
                    pass
            from server import run_triage_pipeline
            res = run_triage_pipeline(user_query)
            return res["summary"]

agent_instance = GeminiWarrantyAgent()
