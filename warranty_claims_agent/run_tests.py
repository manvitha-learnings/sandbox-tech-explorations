"""
Standalone test runner for Warranty Claims Triage Agent.
Can run with pytest or standalone via standard python.
"""

import sys
import os
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_agent

test_functions = [
    ("Search claims by model", test_agent.test_search_warranty_claims_by_model),
    ("Search claims by VIN prefix", test_agent.test_search_warranty_claims_by_vin_prefix),
    ("Search claims by component", test_agent.test_search_warranty_claims_by_component),
    ("Search TSB repository", test_agent.test_search_tsb_repository),
    ("Search dealer repair orders", test_agent.test_search_dealer_repair_orders),
    ("Search QE wiki", test_agent.test_search_quality_wiki),
    ("Severity scoring: CRITICAL", test_agent.test_severity_scoring_critical),
    ("Severity scoring: LOW", test_agent.test_severity_scoring_low),
    ("Failure pattern clustering", test_agent.test_failure_pattern_clustering),
    ("Action: Create QE ticket", test_agent.test_create_quality_ticket),
    ("Action: Notify Slack channel", test_agent.test_notify_slack_channel),
    ("Scenario 1: Recurring Model X axle", test_agent.test_trigger_scenario_1_recurring_model_x_axle),
    ("Scenario 2: VIN prefix summary", test_agent.test_trigger_scenario_2_vin_prefix_summary),
    ("Scenario 3: Open TSB matching", test_agent.test_trigger_scenario_3_tsb_matching),
    ("Server: Health endpoint", test_agent.test_server_health),
    ("Server: Triage API endpoint", test_agent.test_server_triage_api),
    ("Server: Glean chat compatibility", test_agent.test_server_glean_chat_compatibility),
]

def main():
    print("=" * 65)
    print(" Running Warranty Claims Triage Agent Test Suite")
    print("=" * 65)

    passed = 0
    failed = 0

    for name, func in test_functions:
        try:
            func()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {str(e)}")
            traceback.print_exc()
            failed += 1

    print("=" * 65)
    print(f" Results: {passed} passed, {failed} failed out of {len(test_functions)} tests.")
    print("=" * 65)

    if failed > 0:
        sys.exit(1)
    else:
        print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
