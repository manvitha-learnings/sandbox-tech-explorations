"""
End-to-End Test Suite for Migrated Warranty Claims Triage Agent.
Tests the complete pipeline:
  User Query -> Search Tools -> Pattern Clustering -> Severity Scoring -> Output Formatting
Verifies 7 scenarios matching original Glean agent behavior:
1. Single claim
2. Multiple related claims
3. High-severity pattern (safety keywords / escalation)
4. Low-severity pattern (minor non-safety issues)
5. VIN/model-specific search
6. TSB-related query
7. No matching claims
"""

import os
import sys
import json

# Ensure live BigQuery mode is active
os.environ["MOCK_DATA_MODE"] = "false"

from server import run_triage_pipeline
from tools.search_tools import (
    search_warranty_claims,
    search_tsb_repository,
    search_dealer_repair_orders,
    search_quality_engineering_wiki
)
from skills.pattern_clustering import cluster_failure_patterns
from skills.severity_scoring import calculate_severity_score


def run_e2e_tests():
    print("=" * 70)
    print(" STARTING END-TO-END TEST SUITE (7 SCENARIOS)")
    print("=" * 70)

    # --------------------------------------------------------------------------
    # Scenario 1: Single Claim (Safety vs Non-safety Noise Discard)
    # --------------------------------------------------------------------------
    print("\n[Scenario 1] Single Claim Triage...")
    # Single claim with safety keyword must be preserved per Glean Rule 3
    safety_claim = [{
        "claim_id": "CLM-S1-01",
        "component": "Service Brakes",
        "model": "Model Y",
        "vin_prefix": "5YJYGAEE",
        "model_year": 2024,
        "mileage": 8500,
        "parts_cost": 950.0,
        "failure_description": "Sudden brake pedal stiffness and loss of braking power while driving on highway."
    }]
    clusters = cluster_failure_patterns(safety_claim)
    assert len(clusters) == 1, "Single safety claim was improperly discarded"
    sev = calculate_severity_score(
        component=clusters[0]["component"],
        failure_description=safety_claim[0]["failure_description"],
        claim_count=1,
        average_cost=clusters[0]["average_parts_cost"]
    )
    assert sev["severity_band"] == "High", f"Expected High severity for safety claim, got {sev['severity_band']}"
    assert sev["escalation_required"] is True, "Safety claim must require escalation"
    print(f"  -> Single safety claim identified: {clusters[0]['cluster_label']}")
    print(f"  -> Severity: {sev['severity_band']} | Rationale: {sev['rationale']}")
    print("  -> Result: PASS")

    # --------------------------------------------------------------------------
    # Scenario 2: Multiple Related Claims
    # --------------------------------------------------------------------------
    print("\n[Scenario 2] Multiple Related Claims...")
    query = "Summarize recurring warranty claims for Model X rear axle"
    res = run_triage_pipeline(query, model="Model X", component="Rear Axle Assembly")
    assert res["status"] == "success"
    assert res["clusters_found"] >= 1
    top_cluster = res["clusters"][0]
    assert top_cluster["component"] == "Rear Axle Assembly"
    assert top_cluster["claim_count"] >= 1
    print(f"  -> Claims analyzed: {len(res['clusters'])} cluster(s) found")
    print(f"  -> Top Cluster: {top_cluster['cluster_label']} (Count: {top_cluster['claim_count']})")
    print("  -> Result: PASS")

    # --------------------------------------------------------------------------
    # Scenario 3: High-Severity Pattern (Axle Seizure / Lockup)
    # --------------------------------------------------------------------------
    print("\n[Scenario 3] High-Severity Pattern...")
    high_sev_query = "Recurring rear axle assembly failure with catastrophic lockup on Model X"
    claims = search_warranty_claims(model="Model X", component="Rear Axle Assembly")
    ros = search_dealer_repair_orders(model="Model X")
    cl_list = cluster_failure_patterns(claims, ros)
    # Inject safety narrative to evaluate High-severity auto-escalation
    sev_high = calculate_severity_score(
        component="Rear Axle Assembly",
        failure_description="Axle lockup and wheel seizure causing sudden loss of control at highway speed.",
        claim_count=len(claims),
        average_cost=3100.0,
        has_open_tsb=True
    )
    assert sev_high["severity_band"] == "High"
    assert sev_high["escalation_required"] is True
    assert "safety keyword" in sev_high["rationale"].lower()
    print(f"  -> Severity Band: {sev_high['severity_band']}")
    print(f"  -> Rationale: {sev_high['rationale']}")
    print(f"  -> Action: {sev_high['recommended_action']}")
    print("  -> Result: PASS")

    # --------------------------------------------------------------------------
    # Scenario 4: Low-Severity Pattern (Minor Non-Safety Wear)
    # --------------------------------------------------------------------------
    print("\n[Scenario 4] Low-Severity Pattern...")
    sev_low = calculate_severity_score(
        component="Interior Trim",
        failure_description="Minor cosmetic dashboard clip squeak over pavement.",
        claim_count=1,
        average_cost=120.0,
        has_open_tsb=False
    )
    assert sev_low["severity_band"] == "Low"
    assert sev_low["escalation_required"] is False
    assert "Low" in sev_low["severity_band"]
    print(f"  -> Severity Band: {sev_low['severity_band']}")
    print(f"  -> Rationale: {sev_low['rationale']}")
    print(f"  -> Action: {sev_low['recommended_action']}")
    print("  -> Result: PASS")

    # --------------------------------------------------------------------------
    # Scenario 5: VIN/Model-Specific Search
    # --------------------------------------------------------------------------
    print("\n[Scenario 5] VIN/Model-Specific Search...")
    vin_res = run_triage_pipeline("Summarize warranty claims for VIN prefix 1XYZ4A2X in the last 30 days")
    assert vin_res["status"] == "success"
    assert vin_res["clusters_found"] >= 1
    top_vin = vin_res["clusters"][0]
    assert top_vin["vin_prefix"] == "1XYZ4A2X"
    assert top_vin["model"] == "Model X"
    print(f"  -> Filtered Model: {top_vin['model']} | VIN Prefix: {top_vin['vin_prefix']}")
    print(f"  -> Total Parts Cost: ${top_vin['total_parts_cost']:,.2f}")
    print("  -> Result: PASS")

    # --------------------------------------------------------------------------
    # Scenario 6: TSB-Related Query
    # --------------------------------------------------------------------------
    print("\n[Scenario 6] TSB-Related Query...")
    tsb_res = run_triage_pipeline("Does this claim match any open TSB for Model X rear axle whine?")
    assert tsb_res["status"] == "success"
    assert len(tsb_res["tsb_matches"]) >= 1
    match_tsb = tsb_res["tsb_matches"][0]
    assert match_tsb["status"] == "OPEN"
    assert match_tsb["tsb_id"] is not None
    print(f"  -> Matched TSB: {match_tsb['tsb_id']} ({match_tsb['title'][:60]}...)")
    print(f"  -> DTC Codes: {match_tsb.get('dtc_codes')}")
    print("  -> Result: PASS")

    # --------------------------------------------------------------------------
    # Scenario 7: No Matching Claims
    # --------------------------------------------------------------------------
    print("\n[Scenario 7] No Matching Claims...")
    empty_res = run_triage_pipeline("Any warranty claims for Spaceship Zero hyperdrive?")
    assert empty_res["status"] == "success"
    assert empty_res["clusters_found"] == 0
    assert len(empty_res["clusters"]) == 0
    assert "0 failure cluster(s) identified" in empty_res["summary"] or "All" in empty_res["summary"]
    print(f"  -> Handled empty results cleanly: clusters_found={empty_res['clusters_found']}")
    print(f"  -> Summary output:\n{empty_res['summary']}")
    print("  -> Result: PASS")

    print("\n" + "=" * 70)
    print(" ALL 7 END-TO-END SCENARIOS VALIDATED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_e2e_tests()
