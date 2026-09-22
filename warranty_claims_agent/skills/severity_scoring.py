"""
Severity Scoring Skill for Warranty Claims Triage.
Implements the Glean 'severity-scoring' skill.
"""

from typing import Dict, Any, List

SAFETY_KEYWORDS = [
    "lockup", "locked up", "seizure", "fire", "smoke", "loss of power",
    "loss of acceleration", "loss of control", "braking", "steering", "stalling"
]

def calculate_severity_score(
    component: str,
    failure_description: str,
    claim_count: int = 1,
    average_cost: float = 0.0,
    has_open_tsb: bool = False
) -> Dict[str, Any]:
    """
    Computes a standardized Quality Engineering severity score (1-10) and tier.

    Factors:
    - Safety Criticality (up to 4 points)
    - Frequency / Recurrence (up to 3 points)
    - Financial Liability (up to 2 points)
    - Open TSB Correlation (up to 1 point)

    Returns:
        dict containing score, tier, rationale, and recommended action.
    """
    score = 2.0  # baseline
    rationale_points = ["Baseline warranty claim severity (2.0)"]

    # 1. Safety Criticality Assessment
    desc_lower = failure_description.lower()
    matched_safety = [kw for kw in SAFETY_KEYWORDS if kw in desc_lower]
    if matched_safety:
        score += 4.0
        rationale_points.append(f"Safety hazard detected ({', '.join(matched_safety)}): +4.0")
    elif "vibration" in desc_lower or "whining" in desc_lower or "grinding" in desc_lower:
        score += 2.0
        rationale_points.append("Significant mechanical wear / noise detected: +2.0")

    # 2. Recurrence / Frequency
    if claim_count >= 4:
        score += 3.0
        rationale_points.append(f"High recurrence ({claim_count} claims): +3.0")
    elif claim_count >= 2:
        score += 2.0
        rationale_points.append(f"Multiple recurring claims ({claim_count} claims): +2.0")

    # 3. Financial Liability
    if average_cost >= 3000.0:
        score += 2.0
        rationale_points.append(f"High average claim cost (${average_cost:,.2f}): +2.0")
    elif average_cost >= 1500.0:
        score += 1.0
        rationale_points.append(f"Moderate claim cost (${average_cost:,.2f}): +1.0")

    # 4. Open TSB Correlation
    if has_open_tsb:
        score += 1.0
        rationale_points.append("Correlates with an active Open TSB: +1.0")

    # Cap score between 1 and 10
    final_score = min(10.0, max(1.0, round(score, 1)))

    if final_score >= 8.5:
        tier = "CRITICAL"
        action = "Immediate QE escalation: generate QE ticket and alert #warranty-qe Slack channel within 2 hours."
    elif final_score >= 6.5:
        tier = "HIGH"
        action = "High priority: create QE investigation ticket and monitor incoming RO trends."
    elif final_score >= 4.0:
        tier = "MEDIUM"
        action = "Medium priority: track in weekly Quality Engineering review."
    else:
        tier = "LOW"
        action = "Routine warranty processing; no immediate engineering escalation needed."

    return {
        "severity_score": final_score,
        "criticality_tier": tier,
        "rationale": " | ".join(rationale_points),
        "recommended_action": action,
        "escalation_required": final_score >= 6.5
    }
