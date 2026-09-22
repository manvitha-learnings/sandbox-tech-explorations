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



MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")

# Load dynamic Glean configuration from GCS
glean_config = load_glean_config()

# Standardized triage protocol and tool specifications
TRIAGE_PROTOCOL = """
### Available Tools:
- search_warranty_claims: Queries warranty claims by model, VIN prefix, component, or keyword.
- search_tsb_repository: Queries open and closed TSB bulletins by model, symptom, DTC, or TSB ID.
- search_dealer_repair_orders: Queries dealership technician repair orders and diagnostic notes.
- search_quality_engineering_wiki: Queries QE standard operating procedures and investigation protocols.
- cluster_failure_patterns: Clusters lists of claims into pattern groups by component and VIN prefix.
- calculate_severity_score: Computes an objective 1-10 severity score and criticality tier.
- create_quality_ticket: Generates an official QE investigation ticket in Jira/ticketing system.
- notify_warranty_qe_channel: Dispatches high-priority alert cards to the #warranty-qe Slack channel.

### Triage Protocol:
1. When asked about recurring issues:
   - Search the warranty claims database for the specified model or component.
   - Cross-reference with dealer repair orders to review technician observations.
   - Run cluster_failure_patterns to group failure modes and calculate recurrence rates.
   - Check search_tsb_repository to determine if an active TSB already covers the issue.
   - Run calculate_severity_score to establish the criticality tier (CRITICAL, HIGH, MEDIUM, LOW).
   - If 3 or more recurring claims exist or severity is HIGH/CRITICAL, create a QE ticket and notify the Slack channel.

2. When asked to summarize claims for a VIN prefix:
   - Search claims matching the VIN prefix.
   - Provide a clear breakdown of components affected, total parts cost, labor hours, and mileage distribution.

3. When asked to match a claim against TSBs:
   - Search the TSB repository with the symptoms, DTCs, and component.
   - Clearly state whether an exact match exists, the TSB ID, root cause, and prescribed repair procedure.

Format your responses with professional, structured Markdown including Executive Summary, Failure Cluster Details, Root Cause / TSB Alignment, Severity Assessment, and Action Items.
"""

glean_instructions = glean_config.get("instructions", "").strip()
if glean_instructions:
    AGENT_INSTRUCTIONS = f"{glean_instructions}\n\n{TRIAGE_PROTOCOL}".strip()
else:
    AGENT_INSTRUCTIONS = TRIAGE_PROTOCOL.strip()

# Derive identifier-safe agent name from Glean configuration
agent_name = glean_config.get("name", "warranty_claims_triage_agent").lower().replace(" ", "_")
agent_description = glean_config.get(
    "description",
    "Analyzes incoming warranty claims, dealer repair orders, and TSBs to detect recurring failure patterns."
)

# Root agent export for ADK runtime, server, and CLI tools
root_agent = Agent(
    model=MODEL_NAME,
    name=agent_name,
    description=agent_description,
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
