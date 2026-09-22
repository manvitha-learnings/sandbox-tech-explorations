"""
Mock data repository for the Warranty Claims Triage Agent.
Provides realistic sample datasets for:
1. Warranty Claims DB
2. Technical Service Bulletins (TSB) Repository
3. Dealer Repair Orders (ROs)
4. Quality Engineering (QE) Wiki Articles
"""

from typing import List, Dict, Any

WARRANTY_CLAIMS_DB: List[Dict[str, Any]] = [
    {
        "claim_id": "CLM-2026-8801",
        "vin": "1XYZ4A2X8P1098231",
        "vin_prefix": "1XYZ4A2X",
        "model": "Model X",
        "model_year": 2025,
        "claim_date": "2026-09-02",
        "mileage": 14200,
        "component": "Rear Axle Assembly",
        "subsystem": "Drivetrain",
        "failure_description": "High-pitched whining and grinding noise from rear axle under moderate acceleration between 40-55 mph. Differential fluid shows metallic shavings.",
        "customer_complaint": "Loud grinding noise coming from the back of the car when accelerating on highway ramps.",
        "labor_hours": 6.5,
        "parts_cost": 2450.00,
        "status": "APPROVED",
        "dealer_code": "D-402"
    },
    {
        "claim_id": "CLM-2026-8805",
        "vin": "1XYZ4A2X9P1098412",
        "vin_prefix": "1XYZ4A2X",
        "model": "Model X",
        "model_year": 2025,
        "claim_date": "2026-09-05",
        "mileage": 11800,
        "component": "Rear Axle Assembly",
        "subsystem": "Drivetrain",
        "failure_description": "Rear differential pinion bearing premature wear. Severe vibration and grinding noise observed at highway speeds.",
        "customer_complaint": "Severe humming vibration through the floorboards when driving over 45 mph.",
        "labor_hours": 7.0,
        "parts_cost": 2680.00,
        "status": "APPROVED",
        "dealer_code": "D-118"
    },
    {
        "claim_id": "CLM-2026-8819",
        "vin": "1XYZ4A2X3P1098854",
        "vin_prefix": "1XYZ4A2X",
        "model": "Model X",
        "model_year": 2025,
        "claim_date": "2026-09-09",
        "mileage": 16450,
        "component": "Rear Axle Assembly",
        "subsystem": "Drivetrain",
        "failure_description": "Rear drive unit / axle half-shaft spline stripping and differential carrier bearing failure. Metal debris in fluid.",
        "customer_complaint": "Vehicle shuttered and clunked loudly when turning into driveway, loss of acceleration.",
        "labor_hours": 8.5,
        "parts_cost": 3100.00,
        "status": "APPROVED",
        "dealer_code": "D-734"
    },
    {
        "claim_id": "CLM-2026-8842",
        "vin": "1XYZ4A2X6P1099021",
        "vin_prefix": "1XYZ4A2X",
        "model": "Model X",
        "model_year": 2025,
        "claim_date": "2026-09-12",
        "mileage": 9800,
        "component": "Rear Axle Assembly",
        "subsystem": "Drivetrain",
        "failure_description": "Rear differential housing seal failure leading to fluid leakage, catastrophic pinion gear wear and axle seizure.",
        "customer_complaint": "Vehicle locked up momentarily while merging, burning oil smell.",
        "labor_hours": 9.0,
        "parts_cost": 3400.00,
        "status": "UNDER_INVESTIGATION",
        "dealer_code": "D-205"
    },
    {
        "claim_id": "CLM-2026-8790",
        "vin": "2ABC3B1Y4R2044119",
        "vin_prefix": "2ABC3B1Y",
        "model": "Model Y",
        "model_year": 2024,
        "claim_date": "2026-08-28",
        "mileage": 28400,
        "component": "HVAC Heat Pump",
        "subsystem": "Thermal Management",
        "failure_description": "Compressor lock-up due to refrigerant manifold thermal expansion valve sticking in closed position.",
        "customer_complaint": "AC stopped blowing cold air suddenly on a hot afternoon, cabin display threw thermal warning.",
        "labor_hours": 4.5,
        "parts_cost": 1850.00,
        "status": "APPROVED",
        "dealer_code": "D-512"
    },
    {
        "claim_id": "CLM-2026-8822",
        "vin": "2ABC3B1Y7R2044302",
        "vin_prefix": "2ABC3B1Y",
        "model": "Model Y",
        "model_year": 2024,
        "claim_date": "2026-09-04",
        "mileage": 31200,
        "component": "HVAC Heat Pump",
        "subsystem": "Thermal Management",
        "failure_description": "Octovalve coolant bypass actuator failure resulting in intermittent cabin heating.",
        "customer_complaint": "Heater blows cold air intermittently.",
        "labor_hours": 3.0,
        "parts_cost": 920.00,
        "status": "APPROVED",
        "dealer_code": "D-512"
    }
]

TSB_REPOSITORY: List[Dict[str, Any]] = [
    {
        "tsb_id": "TSB-25-03-014",
        "title": "Model X Rear Axle Pinion Bearing Noise and Fluid Contamination",
        "issue_date": "2025-11-15",
        "status": "OPEN",
        "affected_models": ["Model X"],
        "affected_model_years": [2024, 2025],
        "affected_vin_prefixes": ["1XYZ4A2X"],
        "affected_components": ["Rear Axle Assembly", "Rear Differential", "Drive Unit"],
        "symptom": "Whining, humming, or grinding noise from rear axle assembly between 40-60 mph under light to moderate throttle.",
        "dtc_codes": ["P0730", "P079A"],
        "root_cause": "Sub-supplier metallurgical hardening inconsistency on pinion roller bearing races causing premature surface spalling.",
        "repair_procedure": "Inspect differential fluid for ferrous debris using magnetic drain plug. If debris exceeds 2mm particle size, replace complete rear drive axle subassembly per Bulletin Procedure Step 4."
    },
    {
        "tsb_id": "TSB-24-08-009",
        "title": "Model Y Heat Pump Octovalve Sticking and Intermittent Climate Faults",
        "issue_date": "2024-08-20",
        "status": "OPEN",
        "affected_models": ["Model Y", "Model 3"],
        "affected_model_years": [2023, 2024],
        "affected_vin_prefixes": ["2ABC3B1Y"],
        "affected_components": ["HVAC Heat Pump", "Octovalve", "Coolant Manifold"],
        "symptom": "Loss of cabin cooling or heating, DTC DTC-B10E7 stored in Thermal Controller.",
        "dtc_codes": ["B10E7", "B10E8"],
        "root_cause": "Internal silicone seal swelling under prolonged ethylene-glycol exposure.",
        "repair_procedure": "Flash thermal controller firmware to v24.8.2 and replace octovalve assembly with revised part number Rev C."
    },
    {
        "tsb_id": "TSB-25-01-002",
        "title": "Front Suspension Upper Control Arm Ball Joint Creak",
        "issue_date": "2025-01-10",
        "status": "CLOSED",
        "affected_models": ["Model S", "Model X"],
        "affected_model_years": [2022, 2023],
        "affected_vin_prefixes": ["1XYZ3A1S"],
        "affected_components": ["Front Suspension", "Upper Control Arm"],
        "symptom": "Creaking or squeaking noise when turning steering wheel at low speeds or over speed bumps.",
        "dtc_codes": [],
        "root_cause": "Insufficient grease fill during automated ball joint boot assembly.",
        "repair_procedure": "Inject urethane-safe grease or replace upper control arm with upgraded boot seal."
    }
]

DEALER_REPAIR_ORDERS: List[Dict[str, Any]] = [
    {
        "ro_id": "RO-NY-991204",
        "vin": "1XYZ4A2X8P1098231",
        "vin_prefix": "1XYZ4A2X",
        "model": "Model X",
        "service_date": "2026-09-02",
        "dealer_name": "Metro West Dealership",
        "technician_notes": "Customer states loud whine in rear above 40mph. Verified customer complaint. Drained rear differential fluid - fluid was dark gray with significant metallic flakes. Checked TSB-25-03-014; findings match TSB criteria. Replaced rear drive axle assembly and flushed lines.",
        "dtc_codes": ["P079A"],
        "parts_replaced": ["ASY-RAXLE-09", "FLUID-DIF-SYN-2L"],
        "claim_reference": "CLM-2026-8801"
    },
    {
        "ro_id": "RO-CA-448102",
        "vin": "1XYZ4A2X9P1098412",
        "vin_prefix": "1XYZ4A2X",
        "model": "Model X",
        "service_date": "2026-09-05",
        "dealer_name": "Bay Area Auto Center",
        "technician_notes": "Road tested vehicle, confirmed harsh vibration and grinding under acceleration. Scanned DTCs - found P079A. Removed rear axle inspection cover, found broken pinion bearing cage. Matched open TSB-25-03-014. Full subassembly replacement ordered and installed.",
        "dtc_codes": ["P079A"],
        "parts_replaced": ["ASY-RAXLE-09"],
        "claim_reference": "CLM-2026-8805"
    },
    {
        "ro_id": "RO-TX-773190",
        "vin": "1XYZ4A2X6P1099021",
        "vin_prefix": "1XYZ4A2X",
        "model": "Model X",
        "service_date": "2026-09-12",
        "dealer_name": "Lone Star EV Service",
        "technician_notes": "Towed in. Rear axle locked during low speed maneuver. Pinion gear teeth sheared completely. Contacted Quality Engineering field rep due to severe safety risk (wheel lockup potential). Replaced full axle assembly under warranty.",
        "dtc_codes": ["P0730", "P079A"],
        "parts_replaced": ["ASY-RAXLE-09", "SHAFT-HALF-RR-L", "SHAFT-HALF-RR-R"],
        "claim_reference": "CLM-2026-8842"
    }
]

QUALITY_ENGINEERING_WIKI: List[Dict[str, Any]] = [
    {
        "article_id": "WIKI-QE-042",
        "title": "Rear Axle & Differential Triage Protocol",
        "category": "Drivetrain Guidelines",
        "content": (
            "Drivetrain Quality Engineering protocol: Any recurring claims involving rear axle pinion bearings, "
            "spline stripping, or differential lockup must be flagged immediately as HIGH or CRITICAL severity. "
            "If 3 or more claims occur within a 30-day window on the same VIN prefix batch (e.g. 1XYZ4A2X), "
            "an automated QE investigation ticket must be created and the #warranty-qe Slack channel must be notified "
            "for potential field action review or containment inspection at manufacturing plant."
        )
    },
    {
        "article_id": "WIKI-QE-019",
        "title": "Warranty Severity Scoring Rubric",
        "category": "Standard Operating Procedures",
        "content": (
            "Severity Scoring Scale (1 to 10): "
            "- CRITICAL (9-10): Wheel lockup, loss of motive power at highway speeds, steering loss, fire, or thermal runaway. Immediate QE escalation required within 2 hours. "
            "- HIGH (7-8): Imminent component failure with safety or high financial exposure (claim cost > $3,000 or >3 recurring claims in 30 days). "
            "- MEDIUM (4-6): Functional degradation (AC failure, infotainment freeze, excessive noise/vibration) with manageable warranty liability. "
            "- LOW (1-3): Cosmetic flaws, minor squeaks, or trim alignment."
        )
    }
]
