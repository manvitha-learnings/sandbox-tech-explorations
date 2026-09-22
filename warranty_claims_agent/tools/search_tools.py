"""
Search tools for Warranty Claims Triage Agent.
Replaces Glean's 'glean-search' tool across 4 data sources:
1. warranty-claims-db
2. tsb-repository
3. dealer-repair-orders
4. quality-engineering-wiki
"""

import os
from typing import List, Dict, Any, Optional
try:
    from data.mock_data import (
        WARRANTY_CLAIMS_DB,
        TSB_REPOSITORY,
        DEALER_REPAIR_ORDERS,
        QUALITY_ENGINEERING_WIKI
    )
except (ImportError, ModuleNotFoundError):
    from ..data.mock_data import (
        WARRANTY_CLAIMS_DB,
        TSB_REPOSITORY,
        DEALER_REPAIR_ORDERS,
        QUALITY_ENGINEERING_WIKI
    )


MOCK_DATA_MODE = os.getenv("MOCK_DATA_MODE", "true").lower() == "true"

def search_warranty_claims(
    model: Optional[str] = None,
    vin_prefix: Optional[str] = None,
    component: Optional[str] = None,
    keyword: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search warranty claims database by vehicle model, VIN prefix, component name, or keyword.

    Args:
        model: Vehicle model name (e.g. 'Model X', 'Model Y')
        vin_prefix: First 8 characters of VIN (e.g. '1XYZ4A2X')
        component: Subsystem or component name (e.g. 'Rear Axle Assembly', 'HVAC Heat Pump')
        keyword: Free-text search across failure description and customer complaint

    Returns:
        A list of matching warranty claims with claim ID, VIN, failure description, cost, and date.
    """
    if not MOCK_DATA_MODE:
        # In live mode, connect to BigQuery / PostgreSQL
        pass

    results = []
    for claim in WARRANTY_CLAIMS_DB:
        match = True
        if model and model.lower() not in claim["model"].lower():
            match = False
        if vin_prefix and vin_prefix.upper() not in claim["vin_prefix"].upper():
            match = False
        if component and component.lower() not in claim["component"].lower():
            match = False
        if keyword:
            kw = keyword.lower()
            text = f"{claim['failure_description']} {claim['customer_complaint']} {claim['component']}".lower()
            if kw not in text:
                match = False
        if match:
            results.append(claim)

    return results

def search_tsb_repository(
    model: Optional[str] = None,
    component: Optional[str] = None,
    symptom_or_dtc: Optional[str] = None,
    tsb_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search Technical Service Bulletins (TSBs) for open and closed bulletins.

    Args:
        model: Vehicle model name (e.g. 'Model X')
        component: Component name (e.g. 'Rear Axle Assembly')
        symptom_or_dtc: Symptom keywords or diagnostic trouble codes (e.g. 'whine', 'grinding', 'P079A')
        tsb_id: Specific TSB identifier (e.g. 'TSB-25-03-014')

    Returns:
        List of matching TSB bulletins including root cause, affected VIN prefixes, and repair procedures.
    """
    results = []
    for tsb in TSB_REPOSITORY:
        match = True
        if tsb_id and tsb_id.upper() != tsb["tsb_id"].upper():
            match = False
        if model and not any(model.lower() in m.lower() for m in tsb["affected_models"]):
            match = False
        if component and not any(component.lower() in c.lower() for c in tsb["affected_components"]):
            match = False
        if symptom_or_dtc:
            s_lower = symptom_or_dtc.lower()
            text = f"{tsb['title']} {tsb['symptom']} {' '.join(tsb['dtc_codes'])} {tsb['root_cause']}".lower()
            if s_lower not in text:
                match = False
        if match:
            results.append(tsb)

    return results

def search_dealer_repair_orders(
    vin_prefix: Optional[str] = None,
    model: Optional[str] = None,
    dtc_code: Optional[str] = None,
    keyword: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search Dealer Repair Orders (ROs) and technician diagnostic notes.

    Args:
        vin_prefix: First 8 characters of VIN
        model: Vehicle model
        dtc_code: Diagnostic Trouble Code (e.g. 'P079A')
        keyword: Technician notes keyword (e.g. 'metallic flakes', 'bearing')

    Returns:
        List of matching dealer repair orders with technician observations and parts replaced.
    """
    results = []
    for ro in DEALER_REPAIR_ORDERS:
        match = True
        if vin_prefix and vin_prefix.upper() not in ro["vin_prefix"].upper():
            match = False
        if model and model.lower() not in ro["model"].lower():
            match = False
        if dtc_code and not any(dtc_code.upper() in d.upper() for d in ro["dtc_codes"]):
            match = False
        if keyword and keyword.lower() not in ro["technician_notes"].lower():
            match = False
        if match:
            results.append(ro)

    return results

def search_quality_engineering_wiki(
    topic: str
) -> List[Dict[str, Any]]:
    """
    Search Quality Engineering wiki protocols, severity guidelines, and escalation rubrics.

    Args:
        topic: Search query topic (e.g. 'rear axle', 'severity scoring', 'triage protocol')

    Returns:
        List of relevant QE wiki articles and guidelines.
    """
    results = []
    t_lower = topic.lower()
    for article in QUALITY_ENGINEERING_WIKI:
        if t_lower in article["title"].lower() or t_lower in article["content"].lower() or t_lower in article["category"].lower():
            results.append(article)

    return results
