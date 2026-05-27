import json
import requests
import time
from typing import Dict, List, Any
import os
from openpyxl import load_workbook, Workbook

# ==========================================
# REAL ESTATE ETL ENGINE (ZILLOW API)
# ==========================================



def export_real_estate_to_excel(categorized_leads: dict, filename: str = "leads.xlsx"):
    """
    Appends or creates a dedicated 'Real Estate Leads' worksheet 
    inside the main workbook, tracking investment strategy types.
    """
    sheet_name = "Real Estate Leads"
    
    # 1. Initialize or Load Workbook
    if os.path.exists(filename):
        wb = load_workbook(filename)
        # Grab existing sheet or create it fresh if it doesn't exist
        if sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
        else:
            ws = wb.create_sheet(title=sheet_name)
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name

    # 2. Setup Headers if the sheet is completely empty
    headers = [
        "Strategy", "ZPID", "Address", "Price", 
        "Property Type", "Beds", "Baths", 
        "Days on Market", "Zestimate", "URL", "Notes"
    ]
    if ws.max_row == 1 and ws.cell(row=1, column=1).value is None:
        ws.append(headers)

    # 3. Flatten and append the categorized dictionaries
    row_count = 0
    for strategy, properties in categorized_leads.items():
        for prop in properties:
            row_data = [
                strategy.replace("_", " ").upper(),
                prop.get("zpid", "N/A"),
                prop.get("address", "N/A"),
                prop.get("price", 0),
                prop.get("property_type", "N/A"),
                prop.get("beds", 0),
                prop.get("baths", 0),
                prop.get("days_on_market", -1),
                prop.get("zestimate", "N/A"),
                prop.get("url", "N/A"),
                prop.get("wholesale_trigger", "")  # Holds keyword/DOM trigger context
            ]
            ws.append(row_data)
            row_count += 1

    # 4. Save workbook state back safely
    wb.save(filename)
    print(f"[INFO] Successfully exported {row_count} real estate leads to sheet: '{sheet_name}' inside {filename}")

def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Loads configuration schema safely."""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read config file: {e}")
        return {}

def fetch_zillow_properties(location: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Polls RapidAPI Zillow endpoint using search parameters.
    Handles primary list-view retrieval.
    """
    api_key = config.get("rapidapi_key")
    api_host = config.get("rapidapi_host", "zillow56.p.rapidapi.com")
    
    if not api_key or api_key == "YOUR_RAPIDAPI_KEY_HERE":
        print("[ERROR] Valid RapidAPI key missing from config.json")
        return []

    url = f"https://{api_host}/search"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": api_host
    }
    
    # Generic parameter injection covering core location targets
    querystring = {
        "location": location, 
        "status": "FOR_SALE",
        "page": "1"
    }

    try:
        print(f"[INFO] Extracting Zillow raw data for location: {location}...")
        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        
        if response.status_code == 429:
            print("[WARN] Rate-limited (429). Exponential backoff triggered...")
            time.sleep(5)
            return []
            
        if response.status_code != 200:
            print(f"[ERROR] API failed with status {response.status_code}: {response.text}")
            return []
            
        data = response.json()
        return data.get("results", [])
        
    except requests.exceptions.RequestException as e:
        print(f"[CRITICAL] Network drop or timeout during API hit: {e}")
        return []

def transform_and_evaluate(properties: List[Dict[str, Any]], re_config: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Runs extraction, schema transformation, and evaluates matches across 
    investment, wholesaling, and target premium buy strategies.
    """
    categorized_leads = {
        "investment_buy_hold": [],
        "wholesaling": [],
        "buying_premium": []
    }
    
    strategies = re_config.get("strategies", {})
    allowed_types = re_config.get("property_types", ["SINGLE_FAMILY", "MULTI_FAMILY", "LAND"])

    for prop in properties:
        # Standardize properties layout safely from variable API schemas
        home_type = prop.get("homeType", "UNKNOWN")
        price = prop.get("price", 0)
        beds = prop.get("bedrooms", 0)
        baths = prop.get("bathrooms", 0)
        days_on_zillow = prop.get("daysOnZillow", -1)
        description = prop.get("description", "").lower()
        zestimate = prop.get("zestimate")
        year_built = prop.get("yearBuilt", 0)
        zpid = prop.get("zpid")

        # Global Baseline Type Constraint Check
        if home_type not in allowed_types and len(allowed_types) > 0:
            continue

        # Normalized Payload for clean processing down-funnel
        normalized_lead = {
            "zpid": zpid,
            "address": prop.get("address", "N/A"),
            "price": price,
            "property_type": home_type,
            "beds": beds,
            "baths": baths,
            "days_on_market": days_on_zillow,
            "zestimate": zestimate,
            "url": f"https://www.zillow.com/homedetails/{zpid}_zpid/" if zpid else "N/A"
        }

        # 1. Strategy Evaluation: Investment (Buy & Hold)
        ib_cfg = strategies.get("investment_buy_hold", {})
        if (price <= ib_cfg.get("max_price", 9999999) and 
            beds >= ib_cfg.get("min_bedrooms", 0) and 
            baths >= ib_cfg.get("min_bathrooms", 0)):
            if not ib_cfg.get("requires_zestimate") or zestimate is not None:
                categorized_leads["investment_buy_hold"].append(normalized_lead)

        # 2. Strategy Evaluation: Wholesaling (Looking for deep distress metrics)
        ws_cfg = strategies.get("wholesaling", {})
        if price <= ws_cfg.get("max_price", 9999999):
            # Keyword triggers for deep value-add properties
            has_keyword = any(kw in description for kw in ws_cfg.get("keywords", []))
            # Stale listings often reveal highly motivated sellers
            is_stale = days_on_zillow >= ws_cfg.get("max_days_on_zillow", 90)
            
            if has_keyword or is_stale:
                normalized_lead["wholesale_trigger"] = "Keyword Match" if has_keyword else "High Days on Market"
                categorized_leads["wholesaling"].append(normalized_lead)

        # 3. Strategy Evaluation: Premium Buy Criteria
        bp_cfg = strategies.get("buying_premium", {})
        if (bp_cfg.get("min_price", 0) <= price <= bp_cfg.get("max_price", 9999999) and 
            year_built >= bp_cfg.get("min_year_built", 0)):
            categorized_leads["buying_premium"].append(normalized_lead)

    return categorized_leads

def run_real_estate_pipeline():
    """Main execution block hook for pipeline orchestrator."""
    config = load_config()
    re_config = config.get("real_estate_config", {})
    
    if not re_config:
        print("[WARN] No real_estate_config blocks found. Execution halted.")
        return

    all_extracted_leads = {
        "investment_buy_hold": [],
        "wholesaling": [],
        "buying_premium": []
    }

    # Iterate structural parameters built inside current config loops
    for location in config.get("locations", []):
        raw_properties = fetch_zillow_properties(location, config)
        if not raw_properties:
            continue
            
        segmented = transform_and_evaluate(raw_properties, re_config)
        
        for strategy in all_extracted_leads.keys():
            all_extracted_leads[strategy].extend(segmented[strategy])
            
        # Throttling to prevent API execution blockades across rapid loops
        time.sleep(1.5)

    # Output analytical matrix breakdown
    # print("\n================== PIPELINE SUMMARY ==================")
    # for strategy, leads in all_extracted_leads.items():
    #     print(f"Strategy [{strategy.upper()}]: Found {len(leads)} viable properties matches.")
    # print("======================================================")
    
    # --- NEW EXPORT TRIGGER ---
    if config.get("excel_export", True):
        export_real_estate_to_excel(all_extracted_leads, filename="leads.xlsx")
    
    # Ready for integration into your downstream excel_export or messaging modules.
    return all_extracted_leads
