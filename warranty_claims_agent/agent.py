"""
Warranty Claims Triage Agent definition using Google ADK.
Dynamically loaded from Glean agent specification in Google Cloud Storage (GCS).
"""

import os
import sys

pkg_dir = os.path.dirname(os.path.abspath(__file__))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from google.adk.agents.llm_agent import Agent

try:
    from .glean_config_loader import load_glean_config
    from .tools.search_tools import (
        search_warranty_claims,
        search_tsb_repository,
        search_dealer_repair_orders,
        search_quality_engineering_wiki
    )
    from .tools.ticket_tools import create_quality_ticket
    from .tools.slack_tools import notify_warranty_qe_channel
    from .skills.pattern_clustering import cluster_failure_patterns
    from .skills.severity_scoring import calculate_severity_score
except (ImportError, ModuleNotFoundError):
    from glean_config_loader import load_glean_config
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


from google.adk.models.google_llm import Gemini

MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.5-flash-lite")
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Force direct Gemini Developer API (zero Vertex AI billing and zero Vertex quota collisions)
model_instance = Gemini(
    model=MODEL_NAME,
    client_kwargs={
        "vertexai": False,
        "api_key": api_key,
        "project": None,
        "location": None
    }
) if api_key else MODEL_NAME

# Load dynamic Glean configuration from GCS
glean_config = load_glean_config()

# Preserved Glean metadata for Gemini Enterprise migration
GLEAN_METADATA = {
    "agent_id": glean_config.get("agent_id") or glean_config.get("id", "wca_4f9c1e2b8a3d"),
    "name": glean_config.get("name", "Warranty Claims Triage Agent"),
    "description": glean_config.get(
        "description",
        "Analyzes incoming warranty claims, dealer repair orders, and TSBs to detect recurring failure patterns, flag claims matching known open issues, and draft triage summaries for Quality Engineering."
    ),
    "status": glean_config.get("status", "published"),
    "created_at": glean_config.get("created_at"),
    "updated_at": glean_config.get("updated_at"),
    "created_by": glean_config.get("created_by"),
    "trigger": glean_config.get("trigger", {}),
}

# Source of truth: Original Glean agent instructions (from GCS instructions.md)
AGENT_INSTRUCTIONS = glean_config.get("instructions", "").strip()

# Human-readable agent display name and description preserved from Glean
AGENT_DISPLAY_NAME = GLEAN_METADATA["name"]
AGENT_DESCRIPTION = GLEAN_METADATA["description"]

# Python identifier for ADK Agent Node (ADK requires Node.name to be a valid Python identifier)
adk_agent_name = glean_config.get("name", "warranty_claims_triage_agent").lower().replace(" ", "_")

# Root agent export for ADK runtime, server, and CLI tools
root_agent = Agent(
    model=model_instance,
    name=adk_agent_name,
    description=AGENT_DESCRIPTION,
    instruction=AGENT_INSTRUCTIONS,
    tools=[
        search_warranty_claims,
        search_tsb_repository,
        search_dealer_repair_orders,
        search_quality_engineering_wiki,
        cluster_failure_patterns,
        calculate_severity_score,
        create_quality_ticket,
        notify_warranty_qe_channel
    ]
)

