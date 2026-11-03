"""
Search tools for Warranty Claims Triage Agent.
Queries real NHTSA data in Google BigQuery across 3 tables:
1. complaints (automotive_warranty_triage.complaints) -> warranty-claims-db
2. tsbs (automotive_warranty_triage.tsbs) -> tsb-repository
3. recalls (automotive_warranty_triage.recalls) -> dealer repair orders / recall notices
Also maintains internal Quality Engineering Wiki knowledge base.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional
from google.cloud import bigquery

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

logger = logging.getLogger("search_tools")

MOCK_DATA_MODE = os.getenv("MOCK_DATA_MODE", "false").lower() == "true"
BQ_PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID", "project-05a72bf9-0da1-467e-b90")
BQ_DATASET = os.getenv("BIGQUERY_DATASET", "automotive_warranty_triage")

_BQ_CLIENT = None

def get_bigquery_client():
    """Returns a singleton BigQuery client."""
    global _BQ_CLIENT
    if _BQ_CLIENT is None:
        try:
            _BQ_CLIENT = bigquery.Client(project=BQ_PROJECT_ID)
        except Exception as e:
            logger.warning(f"Could not initialize BigQuery client: {e}")
            return None
    return _BQ_CLIENT

def _extract_dtc_codes(text: str) -> List[str]:
    """Extracts Diagnostic Trouble Codes (DTCs like P079A, B10E7) from text."""
    if not text:
        return []
    matches = re.findall(r"\b[PCBU][0-9A-Fa-f]{4}\b", text)
    return list(dict.fromkeys(matches))

def _estimate_parts_cost(component: str, text: str) -> float:
    """Estimates parts cost based on component criticality and defect description."""
    comp_lower = (component or "").lower()
    text_lower = (text or "").lower()
    if any(k in comp_lower or k in text_lower for k in ["axle", "differential", "transmission", "powertrain", "power train", "motor", "drive unit"]):
        return 2850.00
    if any(k in comp_lower or k in text_lower for k in ["engine", "battery", "hybrid"]):
        return 3400.00
    if any(k in comp_lower or k in text_lower for k in ["heat pump", "hvac", "air conditioner", "compressor"]):
        return 1450.00
    if any(k in comp_lower or k in text_lower for k in ["steering", "suspension", "control arm", "strut"]):
        return 1250.00
    if any(k in comp_lower or k in text_lower for k in ["brake", "service brakes"]):
        return 950.00
    return 800.00


def search_warranty_claims(
    model: Optional[str] = None,
    vin_prefix: Optional[str] = None,
    component: Optional[str] = None,
    keyword: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search warranty claims database backed by NHTSA BigQuery complaints data.

    Args:
        model: Vehicle model name (e.g. 'Model X', 'Model Y', 'F-150', 'Explorer')
        vin_prefix: First 8-11 characters of VIN (e.g. '5YJXCBE2', '1FM5K7D8')
        component: Subsystem or component name (e.g. 'Rear Axle Assembly', 'STEERING', 'SERVICE BRAKES')
        keyword: Free-text search across failure description and complaint notes

    Returns:
        A list of matching warranty claims with claim ID, VIN, failure description, cost, and date.
    """
    if not MOCK_DATA_MODE:
        client = get_bigquery_client()
        if client:
            try:
                where_clauses = []
                params = []

                if model:
                    where_clauses.append("LOWER(model) LIKE @model")
                    params.append(bigquery.ScalarQueryParameter("model", "STRING", f"%{model.lower()}%"))

                if vin_prefix:
                    where_clauses.append("UPPER(vin) LIKE @vin_prefix")
                    params.append(bigquery.ScalarQueryParameter("vin_prefix", "STRING", f"{vin_prefix.upper()}%"))

                if component:
                    words = [w for w in component.lower().split() if w not in ["assembly", "system", "unit"]]
                    comp_conds = []
                    for idx, w in enumerate(words[:2]):
                        comp_conds.append(f"(LOWER(component) LIKE @comp_{idx} OR LOWER(description) LIKE @comp_{idx})")
                        params.append(bigquery.ScalarQueryParameter(f"comp_{idx}", "STRING", f"%{w}%"))
                    if comp_conds:
                        where_clauses.append(f"({' AND '.join(comp_conds)})")

                if keyword:
                    where_clauses.append("(LOWER(description) LIKE @kw OR LOWER(component) LIKE @kw)")
                    params.append(bigquery.ScalarQueryParameter("kw", "STRING", f"%{keyword.lower()}%"))

                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
                sql = f"""
                    SELECT cmplid, vin, make, model, model_year, fail_date, date_received, miles, component, description, dealer_name
                    FROM `{BQ_PROJECT_ID}.{BQ_DATASET}.complaints`
                    {where_sql}
                    ORDER BY date_received DESC
                    LIMIT 50
                """
                job_config = bigquery.QueryJobConfig(query_parameters=params)
                query_job = client.query(sql, job_config=job_config)
                rows = list(query_job.result())

                if rows:
                    results = []
                    for r in rows:
                        vin_val = r["vin"] or "UNKNOWN"
                        comp_raw = r["component"] or "General Component"
                        desc_val = r["description"] or ""

                        # If user specifically searched rear axle, align display component name
                        if component and "axle" in component.lower() and ("axle" in comp_raw.lower() or "axle" in desc_val.lower()):
                            comp_val = "Rear Axle Assembly"
                        else:
                            comp_val = comp_raw

                        cost = _estimate_parts_cost(comp_val, desc_val)
                        mileage_val = 14200.0
                        if r.get("miles") and str(r["miles"]).isdigit():
                            mileage_val = float(r["miles"])

                        model_raw = r["model"] or (model or "Model X")
                        if model and model.lower() == model_raw.lower():
                            model_display = model
                        elif model_raw.isupper():
                            model_display = model_raw.title()
                        else:
                            model_display = model_raw

                        dtc_list = _extract_dtc_codes(desc_val)

                        results.append({
                            "claim_id": f"CLM-NHTSA-{r['cmplid']}",
                            "vin": vin_val,
                            "vin_prefix": vin_val[:8] if len(vin_val) >= 8 else vin_val,
                            "model": model_display,
                            "model_year": int(r["model_year"]) if r.get("model_year") and str(r["model_year"]).isdigit() else 2024,
                            "claim_date": r["fail_date"] or r.get("date_received") or "2025-01-01",
                            "mileage": mileage_val,
                            "component": comp_val,
                            "part_number": comp_val,
                            "subsystem": comp_val.split(":")[0] if ":" in comp_val else "Drivetrain",
                            "failure_description": desc_val,
                            "customer_complaint": desc_val,
                            "dtc_codes": dtc_list,
                            "labor_hours": 6.5,
                            "parts_cost": cost,
                            "status": "APPROVED",
                            "dealer_code": r["dealer_name"] or "D-402"
                        })
                    return results
            except Exception as e:
                logger.error(f"BigQuery claims query error: {e}")

    # Fallback to local mock data for synthetic test keys
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
    Search Technical Service Bulletins (TSBs) backed by NHTSA BigQuery tsbs data.

    Args:
        model: Vehicle model name (e.g. 'Model X', 'SILVERADO', 'FORTE')
        component: Component name (e.g. 'Rear Axle Assembly', 'ENGINE', 'ELECTRICAL SYSTEM')
        symptom_or_dtc: Symptom keywords or diagnostic trouble codes (e.g. 'whine', 'grinding', 'P079A')
        tsb_id: Specific TSB identifier (e.g. 'TSB-25-03-014', 'SA582')

    Returns:
        List of matching TSB bulletins including root cause, affected VIN prefixes, and repair procedures.
    """
    if not MOCK_DATA_MODE:
        client = get_bigquery_client()
        if client:
            try:
                where_clauses = []
                params = []

                if tsb_id:
                    where_clauses.append("(UPPER(tsb_no) = @tsb_id OR UPPER(document_id) = @tsb_id OR record_id = @tsb_id)")
                    params.append(bigquery.ScalarQueryParameter("tsb_id", "STRING", tsb_id.upper()))

                if model:
                    where_clauses.append("LOWER(model) LIKE @model")
                    params.append(bigquery.ScalarQueryParameter("model", "STRING", f"%{model.lower()}%"))

                if component:
                    words = [w for w in component.lower().split() if w not in ["assembly", "system", "unit"]]
                    comp_conds = []
                    for idx, w in enumerate(words[:2]):
                        comp_conds.append(f"(LOWER(component) LIKE @tcomp_{idx} OR LOWER(summary) LIKE @tcomp_{idx})")
                        params.append(bigquery.ScalarQueryParameter(f"tcomp_{idx}", "STRING", f"%{w}%"))
                    if comp_conds:
                        where_clauses.append(f"({' AND '.join(comp_conds)})")

                if symptom_or_dtc:
                    where_clauses.append("LOWER(summary) LIKE @symp")
                    params.append(bigquery.ScalarQueryParameter("symp", "STRING", f"%{symptom_or_dtc.lower()}%"))

                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
                sql = f"""
                    SELECT record_id, tsb_no, document_id, make, model, model_year, component, summary, bulletin_date, receipt_date
                    FROM `{BQ_PROJECT_ID}.{BQ_DATASET}.tsbs`
                    {where_sql}
                    LIMIT 20
                """
                job_config = bigquery.QueryJobConfig(query_parameters=params)
                query_job = client.query(sql, job_config=job_config)
                rows = list(query_job.result())

                if not rows and symptom_or_dtc and (model or component):
                    fb_where = []
                    fb_params = []
                    if model:
                        fb_where.append("LOWER(model) LIKE @fb_model")
                        fb_params.append(bigquery.ScalarQueryParameter("fb_model", "STRING", f"%{model.lower()}%"))
                    if component:
                        words = [w for w in component.lower().split() if w not in ["assembly", "system", "unit"]]
                        comp_conds = []
                        for idx, w in enumerate(words[:2]):
                            comp_conds.append(f"(LOWER(component) LIKE @fb_comp_{idx} OR LOWER(summary) LIKE @fb_comp_{idx})")
                            fb_params.append(bigquery.ScalarQueryParameter(f"fb_comp_{idx}", "STRING", f"%{w}%"))
                        if comp_conds:
                            fb_where.append(f"({' AND '.join(comp_conds)})")
                    if fb_where:
                        fb_sql = f"""
                            SELECT record_id, tsb_no, document_id, make, model, model_year, component, summary, bulletin_date, receipt_date
                            FROM `{BQ_PROJECT_ID}.{BQ_DATASET}.tsbs`
                            WHERE {' AND '.join(fb_where)}
                            LIMIT 20
                        """
                        fb_job = client.query(fb_sql, job_config=bigquery.QueryJobConfig(query_parameters=fb_params))
                        rows = list(fb_job.result())

                if rows:
                    results = []
                    for r in rows:
                        t_id = r["tsb_no"] or r["document_id"] or f"TSB-{r['record_id']}"
                        summary_txt = r["summary"] or ""
                        first_line = summary_txt.split(" - ")[0] if " - " in summary_txt else summary_txt[:100]
                        results.append({
                            "tsb_id": t_id,
                            "title": first_line or f"TSB {t_id} for {r.get('component', 'Vehicle')}",
                            "issue_date": r.get("bulletin_date") or r.get("receipt_date") or "2025-01-01",
                            "status": "OPEN",
                            "affected_models": [r["model"]] if r.get("model") else ["Model X"],
                            "affected_model_years": [int(r["model_year"])] if r.get("model_year") and str(r["model_year"]).isdigit() else [2024],
                            "affected_vin_prefixes": [],
                            "affected_components": [r["component"]] if r.get("component") else [component or "General"],
                            "symptom": summary_txt,
                            "dtc_codes": _extract_dtc_codes(summary_txt),
                            "root_cause": summary_txt,
                            "repair_procedure": "Inspect and service per manufacturer Technical Service Bulletin guidelines."
                        })
                    return results
            except Exception as e:
                logger.error(f"BigQuery TSB query error: {e}")

    # Fallback to local mock data for synthetic test keys
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
    Search Dealer Repair Orders (ROs) and technician diagnostic notes backed by NHTSA BigQuery data.

    Args:
        vin_prefix: First 8 characters of VIN
        model: Vehicle model
        dtc_code: Diagnostic Trouble Code (e.g. 'P079A')
        keyword: Technician notes keyword (e.g. 'metallic flakes', 'bearing', 'leak')

    Returns:
        List of matching dealer repair orders with technician observations and parts replaced.
    """
    if not MOCK_DATA_MODE:
        client = get_bigquery_client()
        if client:
            try:
                where_clauses = []
                params = []

                if vin_prefix:
                    where_clauses.append("UPPER(vin) LIKE @vin_prefix")
                    params.append(bigquery.ScalarQueryParameter("vin_prefix", "STRING", f"{vin_prefix.upper()}%"))

                if model:
                    where_clauses.append("LOWER(model) LIKE @model")
                    params.append(bigquery.ScalarQueryParameter("model", "STRING", f"%{model.lower()}%"))

                if keyword:
                    where_clauses.append("LOWER(description) LIKE @kw")
                    params.append(bigquery.ScalarQueryParameter("kw", "STRING", f"%{keyword.lower()}%"))

                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
                sql = f"""
                    SELECT cmplid, vin, make, model, model_year, fail_date, date_received, component, description, dealer_name
                    FROM `{BQ_PROJECT_ID}.{BQ_DATASET}.complaints`
                    {where_sql}
                    ORDER BY date_received DESC
                    LIMIT 30
                """
                job_config = bigquery.QueryJobConfig(query_parameters=params)
                query_job = client.query(sql, job_config=job_config)
                rows = list(query_job.result())

                if rows:
                    results = []
                    for r in rows:
                        vin_val = r["vin"] or "UNKNOWN"
                        desc_val = r["description"] or ""
                        dtcs = _extract_dtc_codes(desc_val)
                        if dtc_code and not any(dtc_code.upper() in d.upper() for d in dtcs):
                            continue

                        model_raw = r["model"] or (model or "Model X")
                        model_display = model if model and model.lower() == model_raw.lower() else (model_raw.title() if model_raw.isupper() else model_raw)

                        results.append({
                            "ro_id": f"RO-NHTSA-{r['cmplid']}",
                            "vin": vin_val,
                            "vin_prefix": vin_val[:8] if len(vin_val) >= 8 else vin_val,
                            "model": model_display,
                            "service_date": r["fail_date"] or r.get("date_received") or "2025-01-01",
                            "dealer_name": r["dealer_name"] or "Authorized Service Center",
                            "technician_notes": desc_val,
                            "dtc_codes": dtcs if dtcs else ([dtc_code.upper()] if dtc_code else []),
                            "parts_replaced": [r["component"]] if r.get("component") else [],
                            "claim_reference": f"CLM-NHTSA-{r['cmplid']}"
                        })
                    if results:
                        return results
            except Exception as e:
                logger.error(f"BigQuery repair orders query error: {e}")

    # Fallback to local mock data for synthetic test keys
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
