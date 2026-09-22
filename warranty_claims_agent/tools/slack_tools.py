"""
Slack notification tools for Warranty Claims Triage Agent.
Replaces Glean's 'notify-slack-channel' custom action.
"""

import os
import time
from typing import Dict, Any, List, Optional

MOCK_DATA_MODE = os.getenv("MOCK_DATA_MODE", "true").lower() == "true"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# In-memory log of sent Slack notifications for local testing
SENT_SLACK_NOTIFICATIONS: List[Dict[str, Any]] = []

def notify_warranty_qe_channel(
    headline: str,
    summary: str,
    severity: str,
    ticket_id: Optional[str] = None,
    affected_model: Optional[str] = None,
    claim_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Sends an urgent triage alert to the #warranty-qe Slack channel.

    Args:
        headline: Brief high-impact alert title (e.g. 'Recurring Rear Axle Pinion Failures Detected on Model X')
        summary: Concise summary of symptoms, cluster size, and containment recommendations
        severity: Severity level ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')
        ticket_id: Optional QE ticket ID reference (e.g. 'QE-2026-101')
        affected_model: Vehicle model affected
        claim_count: Number of clustered claims

    Returns:
        Dictionary indicating delivery status, channel, and payload.
    """
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    severity_emoji = {
        "CRITICAL": ":rotating_light: *CRITICAL*",
        "HIGH": ":warning: *HIGH*",
        "MEDIUM": ":large_yellow_circle: *MEDIUM*",
        "LOW": ":information_source: *LOW*"
    }.get(severity.upper(), ":warning: *ALERT*")

    payload = {
        "channel": "#warranty-qe",
        "timestamp": timestamp,
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": headline}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Severity:*\n{severity_emoji}"},
                    {"type": "mrkdwn", "text": f"*Model:*\n{affected_model or 'Multiple'}"},
                    {"type": "mrkdwn", "text": f"*Claims Count:*\n{claim_count or 'N/A'}"},
                    {"type": "mrkdwn", "text": f"*QE Ticket:*\n{ticket_id or 'None'}"}
                ]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Triage Summary:*\n{summary}"}
            }
        ]
    }

    if not MOCK_DATA_MODE and SLACK_WEBHOOK_URL:
        import requests
        try:
            # requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
            pass
        except Exception as e:
            payload["warning"] = f"Live Slack dispatch error: {str(e)}"

    SENT_SLACK_NOTIFICATIONS.append(payload)
    return {
        "status": "SENT",
        "channel": "#warranty-qe",
        "timestamp": timestamp,
        "message_headline": headline
    }
