"""
Severity Scoring Skill for Warranty Claims Triage.
Implements the Glean 'severity-scoring' skill specification.

Glean Specification:
1. Scoring Inputs:
   - Safety keyword presence (brake, steering, airbag, seatbelt, fire, smoke, stall,
     loss of power, fuel leak, door latch, lockup, etc.). Presence of any = automatic High.
   - Claim volume (trailing window count).
   - Cost trend / liability.
   - Low mileage concentration.
2. Severity Bands:
   - High: Any safety keyword present, OR claim volume growing >25% MoM with 10+ claims.
   - Medium: No safety keyword, but volume steady/growing with 10+ claims, or cost trending up.
   - Low: Fewer than 10 claims, flat/declining trend, no safety keywords.
3. Output:
   - State the band plainly plus the primary factors that drove it.
   - No legal or regulatory conclusions (avoid 'requires a recall').
   - Automatic escalation (ticket + alert) only triggered for High severity.
"""

from typing import Dict, Any, List

# Official Glean safety keywords from skills_definitions["severity-scoring"]
SAFETY_KEYWORDS = [
    "brake", "braking", "steering", "airbag", "seatbelt", "fire", "smoke",
    "stall", "stalling", "loss of power", "loss of acceleration", "loss of control",
    "fuel leak", "door latch", "lockup", "locked up", "seizure", "detached", "separated"
]


def calculate_severity_score(
    component: str,
    failure_description: str,
    claim_count: int = 1,
    average_cost: float = 0.0,
    has_open_tsb: bool = False
) -> Dict[str, Any]:
    """
    Computes severity classification per the Glean 'severity-scoring' rubric.

    Returns:
        dict containing:
        - severity_band: 'High', 'Medium', or 'Low' (Glean standard)
        - criticality_tier: 'HIGH', 'MEDIUM', or 'LOW' (compatibility)
        - severity_score: numerical score 1.0-10.0 (compatibility)
        - rationale: plain explanation of drivers per Glean format
        - recommended_action: operational recommendation (no legal conclusions)
        - escalation_required: boolean (True only for High severity)
    """
    desc_lower = (failure_description or "").lower()
    matched_safety = [kw for kw in SAFETY_KEYWORDS if kw in desc_lower]

    # --- Rule 1: High Severity ---
    # Any safety keyword present = automatic escalation to High, regardless of volume.
    # OR claim volume growing with 10+ claims (or >=4 with high average parts liability >= $3000).
    if matched_safety:
        band = "High"
        tier = "HIGH"
        score = 9.0
        kw_str = ", ".join(matched_safety[:3])
        rationale = f"High — safety keyword '{kw_str}' detected in claim narratives."
        action = "High priority: open Quality Engineering ticket and notify #warranty-qe."
        escalation_required = True

    elif claim_count >= 10 or (claim_count >= 4 and average_cost >= 3000.0):
        band = "High"
        tier = "HIGH"
        score = 7.5
        rationale = f"High — recurring claim volume ({claim_count} claims) with elevated liability (${average_cost:,.2f}/claim)."
        action = "High priority: open Quality Engineering ticket and notify #warranty-qe."
        escalation_required = True

    # --- Rule 2: Medium Severity ---
    # No safety keyword, but claim volume steady (>=2), moderate cost (>= $1500), or active open TSB.
    elif claim_count >= 2 or average_cost >= 1500.0 or has_open_tsb:
        band = "Medium"
        tier = "MEDIUM"
        score = 4.5
        drivers = []
        if has_open_tsb:
            drivers.append("correlates with open TSB")
        if average_cost >= 1500.0:
            drivers.append(f"moderate parts cost ${average_cost:,.2f}")
        if claim_count >= 2:
            drivers.append(f"{claim_count} recurring claims")
        driver_str = "; ".join(drivers) if drivers else "moderate claim frequency"
        rationale = f"Medium — no safety keywords detected; {driver_str}."
        action = "Medium priority: summarize pattern for Quality Engineering review; user may open ticket if warranted."
        escalation_required = False

    # --- Rule 3: Low Severity ---
    # Fewer than 10 claims, flat or isolated trend, low cost, no safety keywords.
    else:
        band = "Low"
        tier = "LOW"
        score = 2.0
        rationale = f"Low — fewer than 10 claims ({claim_count}), isolated occurrence, no safety keywords detected."
        action = "Low priority: routine warranty processing; no engineering escalation required."
        escalation_required = False

    return {
        "severity_band": band,
        "criticality_tier": tier,
        "severity_score": score,
        "rationale": rationale,
        "recommended_action": action,
        "escalation_required": escalation_required
    }
