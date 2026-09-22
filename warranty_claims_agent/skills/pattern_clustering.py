"""
Failure Pattern Clustering Skill for Warranty Claims Triage.
Implements the Glean 'failure-pattern-clustering' skill.
"""

from typing import List, Dict, Any
from collections import defaultdict

def cluster_failure_patterns(
    claims: List[Dict[str, Any]],
    repair_orders: List[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Clusters claims and dealer repair orders by subsystem, component, and symptom patterns.
    Calculates recurrence rates, total costs, and identifies primary failure modes.

    Returns:
        A list of cluster summaries ordered by claim count (descending).
    """
    if not claims:
        return []

    # Group by (component, vin_prefix)
    grouped = defaultdict(list)
    for c in claims:
        key = (c.get("component", "Unknown"), c.get("vin_prefix", "Unknown"), c.get("model", "Unknown"))
        grouped[key].append(c)

    clusters = []
    for (component, vin_prefix, model), group_claims in grouped.items():
        total_cost = sum(float(c.get("parts_cost", 0.0)) for c in group_claims)
        avg_cost = total_cost / len(group_claims) if group_claims else 0.0
        avg_mileage = sum(float(c.get("mileage", 0.0)) for c in group_claims) / len(group_claims)

        # Extract dominant symptom keywords
        descriptions = [c.get("failure_description", "") for c in group_claims]
        all_text = " ".join(descriptions).lower()

        keywords = []
        for kw in ["whining", "grinding", "vibration", "lockup", "bearing", "leak", "actuator", "compressor"]:
            if kw in all_text:
                keywords.append(kw)

        # Find matching repair orders if provided
        ro_matches = []
        if repair_orders:
            for ro in repair_orders:
                if ro.get("vin_prefix") == vin_prefix or ro.get("model") == model:
                    ro_matches.append(ro.get("ro_id"))

        cluster_summary = {
            "cluster_id": f"CLUST-{component.replace(' ', '_').upper()}-{vin_prefix}",
            "component": component,
            "subsystem": group_claims[0].get("subsystem", "General"),
            "model": model,
            "vin_prefix": vin_prefix,
            "claim_count": len(group_claims),
            "claim_ids": [c.get("claim_id") for c in group_claims],
            "average_mileage": round(avg_mileage, 0),
            "total_parts_cost": round(total_cost, 2),
            "average_parts_cost": round(avg_cost, 2),
            "primary_symptoms": keywords or ["General mechanical fault"],
            "matching_ro_count": len(ro_matches),
            "matching_ro_ids": ro_matches
        }
        clusters.append(cluster_summary)

    # Sort clusters by claim count descending
    clusters.sort(key=lambda x: x["claim_count"], reverse=True)
    return clusters
