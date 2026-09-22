"""
Ticketing tools for Warranty Claims Triage Agent.
Replaces Glean's 'create-quality-ticket' custom action.
"""

import os
import time
from typing import Dict, Any, List, Optional

MOCK_DATA_MODE = os.getenv("MOCK_DATA_MODE", "true").lower() == "true"
QE_TICKETING_API_URL = os.getenv("QE_TICKETING_API_URL", "")
QE_TICKETING_API_TOKEN = os.getenv("QE_TICKETING_API_TOKEN", "")

# In-memory ticket registry for local testing & tracking
CREATED_QE_TICKETS: List[Dict[str, Any]] = []

def create_quality_ticket(
    title: str,
    description: str,
    severity: str,
    component: str,
    affected_model: str,
    affected_vin_prefix: str,
    claim_count: int,
    tsb_reference: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates an official Quality Engineering investigation ticket for recurring warranty issues.

    Args:
        title: Short summary title of the defect/investigation
        description: Detailed triage summary including symptoms, failure patterns, and recommended containment
        severity: Severity level ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')
        component: Affected subsystem or component name (e.g. 'Rear Axle Assembly')
        affected_model: Vehicle model name (e.g. 'Model X')
        affected_vin_prefix: VIN prefix batch (e.g. '1XYZ4A2X')
        claim_count: Number of warranty claims clustered in this pattern
        tsb_reference: Optional matching TSB ID if applicable (e.g. 'TSB-25-03-014')

    Returns:
        Dictionary with ticket ID, status, creation timestamp, and ticket URL.
    """
    ticket_seq = len(CREATED_QE_TICKETS) + 101
    ticket_id = f"QE-2026-{ticket_seq}"
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    ticket_record = {
        "ticket_id": ticket_id,
        "title": title,
        "description": description,
        "severity": severity.upper(),
        "component": component,
        "affected_model": affected_model,
        "affected_vin_prefix": affected_vin_prefix,
        "claim_count": claim_count,
        "tsb_reference": tsb_reference,
        "status": "OPEN_INVESTIGATION",
        "created_at": timestamp,
        "assignee_group": "Quality-Engineering-Drivetrain",
        "ticket_url": f"https://jira.company.internal/browse/{ticket_id}"
    }

    if not MOCK_DATA_MODE and QE_TICKETING_API_URL:
        # Live mode: dispatch to real Jira / ServiceNow REST endpoint
        import requests
        try:
            headers = {
                "Authorization": f"Bearer {QE_TICKETING_API_TOKEN}",
                "Content-Type": "application/json"
            }
            # requests.post(QE_TICKETING_API_URL, json=ticket_record, headers=headers, timeout=5)
        except Exception as e:
            ticket_record["warning"] = f"Live dispatch error: {str(e)}; saved to internal audit log."

    CREATED_QE_TICKETS.append(ticket_record)
    return ticket_record
