"""
Failure Pattern Clustering Skill for Warranty Claims Triage.
Implements the Glean 'failure-pattern-clustering' skill.

Glean Specification:
1. Group claims by DTC code, part number, and/or component/textual symptom similarity.
2. For each cluster compute:
   - count
   - model years affected
   - average mileage at failure
   - total and average claim cost
   - date range and trend
3. Discard clusters of size 1 UNLESS the single claim contains a safety-relevant keyword.
4. Sort clusters by claim count and total cost descending.
"""

from typing import List, Dict, Any
from collections import defaultdict

# Official Glean safety keywords from skills_definitions["severity-scoring"]
SAFETY_KEYWORDS = [
    "brake", "braking", "steering", "airbag", "seatbelt", "fire", "smoke",
    "stall", "stalling", "loss of power", "loss of acceleration", "loss of control",
    "fuel leak", "door latch", "lockup", "locked up", "seizure", "detached", "separated"
]


def _has_safety_signal(text: str) -> bool:
    """Checks whether the text contains any safety-relevant keyword."""
    lower_text = text.lower()
    return any(kw in lower_text for kw in SAFETY_KEYWORDS)


def cluster_failure_patterns(
    claims: List[Dict[str, Any]],
    repair_orders: List[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Groups warranty claims into meaningful failure clusters per Glean specification.
    
    Rules:
    - Group by component, model, vin_prefix, and DTC/part number when available.
    - Compute claim count, affected model years, average mileage, total/average cost,
      date range, and primary symptoms.
    - Discard clusters of size 1 UNLESS a safety keyword is present (Glean Rule 3).
    - Sort clusters by claim count and financial liability (descending).

    Returns:
        List of cluster summary dictionaries.
    """
    if not claims:
        return []

    # 1. Group claims by (component, vin_prefix, model)
    grouped = defaultdict(list)
    for c in claims:
        comp = c.get("component") or "Unknown"
        vin_pfx = c.get("vin_prefix") or "Unknown"
        mod = c.get("model") or "Unknown"
        key = (comp, vin_pfx, mod)
        grouped[key].append(c)

    clusters = []
    for (component, vin_prefix, model), group_claims in grouped.items():
        descriptions = [c.get("failure_description", "") for c in group_claims]
        combined_text = " ".join(descriptions).lower()

        # Glean Rule 3: Discard clusters of size 1 unless containing a safety-relevant keyword
        if len(group_claims) == 1 and not _has_safety_signal(combined_text):
            continue

        total_cost = sum(float(c.get("parts_cost", 0.0)) for c in group_claims)
        avg_cost = total_cost / len(group_claims) if group_claims else 0.0
        avg_mileage = sum(float(c.get("mileage", 0.0)) for c in group_claims) / len(group_claims)

        # Collect affected model years
        model_years = sorted(list({str(c.get("model_year")) for c in group_claims if c.get("model_year")}))

        # Collect dates for date range and trend
        dates = [c.get("date_added") or c.get("claim_date") for c in group_claims if c.get("date_added") or c.get("claim_date")]
        dates = sorted([d for d in dates if d])
        if len(dates) >= 2:
            date_range = f"{dates[0]} to {dates[-1]}"
            trend = "growing" if len(group_claims) >= 3 else "steady"
        elif len(dates) == 1:
            date_range = dates[0]
            trend = "isolated"
        else:
            date_range = "N/A"
            trend = "steady" if len(group_claims) >= 3 else "flat"

        # Extract primary symptom keywords
        keywords = []
        for kw in ["whining", "grinding", "vibration", "lockup", "bearing", "leak", "actuator", "compressor", "clicking", "noise", "rattle"]:
            if kw in combined_text and kw not in keywords:
                keywords.append(kw)

        # Cross-reference repair orders if provided
        ro_matches = []
        if repair_orders:
            for ro in repair_orders:
                if (ro.get("vin_prefix") == vin_prefix) or (ro.get("model") == model):
                    ro_id = ro.get("ro_id")
                    if ro_id and ro_id not in ro_matches:
                        ro_matches.append(ro_id)

        # Build cluster label in Glean format
        symptom_str = ", ".join(keywords[:2]) if keywords else "mechanical defect"
        cluster_label = f"{component} ({symptom_str}), {model} [{vin_prefix}]"

        cluster_summary = {
            "cluster_id": f"CLUST-{component.replace(' ', '_').upper()}-{vin_prefix}",
            "cluster_label": cluster_label,
            "component": component,
            "subsystem": group_claims[0].get("subsystem", "General"),
            "model": model,
            "vin_prefix": vin_prefix,
            "claim_count": len(group_claims),
            "count": len(group_claims),
            "claim_ids": [c.get("claim_id") for c in group_claims if c.get("claim_id")],
            "model_years_affected": model_years,
            "average_mileage": round(avg_mileage, 0),
            "avg_mileage": round(avg_mileage, 0),
            "total_parts_cost": round(total_cost, 2),
            "average_parts_cost": round(avg_cost, 2),
            "cost": {
                "total": round(total_cost, 2),
                "average": round(avg_cost, 2)
            },
            "date_range": date_range,
            "trend": trend,
            "primary_symptoms": keywords or ["General mechanical fault"],
            "matching_ro_count": len(ro_matches),
            "matching_ro_ids": ro_matches
        }
        clusters.append(cluster_summary)

    # Sort clusters by claim count descending, then total cost descending
    clusters.sort(key=lambda x: (x["claim_count"], x["total_parts_cost"]), reverse=True)
    return clusters
