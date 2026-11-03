"""
Ticketing tools for Warranty Claims Triage Agent.
Creates an official Quality Engineering investigation ticket in Jira or mock registry.
"""

import os
import time
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

# In-memory ticket registry for local testing & tracking
CREATED_QE_TICKETS: List[Dict[str, Any]] = []


def create_quality_ticket(
    title: str,
    description: str,
    severity: str = "MEDIUM",
    component: Optional[str] = None,
    affected_model: Optional[str] = None,
    affected_vin_prefix: Optional[str] = None,
    claim_count: Optional[int] = None,
    tsb_reference: Optional[str] = None,
    issuetype: str = "Task",
) -> Dict[str, Any]:
    """
    Creates an official Quality Engineering investigation ticket for recurring warranty issues.
    Dispatches to real Jira when MOCK_DATA_MODE is false and credentials are provided,
    otherwise creates a simulated ticket in CREATED_QE_TICKETS.
    """
    mock_data_mode = os.getenv("MOCK_DATA_MODE", "true").lower() == "true"
    jira_url = (os.getenv("JIRA_URL") or os.getenv("QE_TICKETING_API_URL") or "").rstrip("/")
    jira_email = os.getenv("JIRA_EMAIL", "").strip()
    jira_api_token = (os.getenv("JIRA_API_TOKEN") or os.getenv("QE_TICKETING_API_TOKEN") or "").strip()
    jira_project_key = (os.getenv("JIRA_PROJECT_KEY") or "QE").strip()

    ticket_seq = len(CREATED_QE_TICKETS) + 101
    mock_ticket_id = f"QE-2026-{ticket_seq}"
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    sev = (severity or "MEDIUM").upper()
    priority_name = "High" if sev in ("HIGH", "CRITICAL") else "Medium"

    ticket_record = {
        "ticket_id": mock_ticket_id,
        "title": title,
        "description": description,
        "severity": sev,
        "component": component,
        "affected_model": affected_model,
        "affected_vin_prefix": affected_vin_prefix,
        "claim_count": claim_count,
        "tsb_reference": tsb_reference,
        "status": "OPEN_INVESTIGATION",
        "created_at": timestamp,
        "assignee_group": "Quality-Engineering-Drivetrain",
        "ticket_url": f"https://jira.company.internal/browse/{mock_ticket_id}",
    }

    # Live Jira integration when MOCK_DATA_MODE is false and Jira URL is set
    if not mock_data_mode and jira_url:
        import requests
        from requests.auth import HTTPBasicAuth

        # Build detailed description
        full_desc = description
        extras = []
        if component:
            extras.append(f"*Component:* {component}")
        if affected_model:
            extras.append(f"*Model:* {affected_model}")
        if affected_vin_prefix:
            extras.append(f"*VIN Prefix:* {affected_vin_prefix}")
        if claim_count is not None:
            extras.append(f"*Claim Count:* {claim_count}")
        if tsb_reference:
            extras.append(f"*TSB Reference:* {tsb_reference}")
        if extras:
            full_desc = f"{description}\n\n" + "\n".join(extras)

        payload = {
            "fields": {
                "project": {"key": jira_project_key},
                "summary": title,
                "description": full_desc,
                "issuetype": {"name": issuetype},
                "priority": {"name": priority_name},
            }
        }

        try:
            auth = HTTPBasicAuth(jira_email, jira_api_token) if jira_email else None
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            api_endpoint = f"{jira_url}/rest/api/2/issue"

            resp = requests.post(api_endpoint, json=payload, auth=auth, headers=headers, timeout=10)
            if resp.status_code in (200, 201):
                data = resp.json()
                real_key = data.get("key") or mock_ticket_id
                ticket_record["ticket_id"] = real_key
                ticket_record["ticket_url"] = f"{jira_url}/browse/{real_key}"
                ticket_record["status"] = "OPEN_INVESTIGATION"
                ticket_record["live_jira_created"] = True
            else:
                ticket_record["warning"] = f"Jira returned {resp.status_code}: {resp.text}"
        except Exception as e:
            ticket_record["warning"] = f"Live Jira dispatch error: {str(e)}"

    CREATED_QE_TICKETS.append(ticket_record)
    return ticket_record
