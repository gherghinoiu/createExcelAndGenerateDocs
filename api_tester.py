import requests
import pandas as pd
import re
import json
import urllib3

# Suppress only the single InsecureRequestWarning from urllib3!
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. Information from your screenshots ---
API_URL_DA = "https://www.e-licitatie.ro/api-pub/DirectAcquisitionCommon/GetDirectAcquisitionList/"
BASE_VIEW_URL_DA = "https://www.e-licitatie.ro/pub/direct-acquisition/view/"

# --- 2. Helper function (from our scraping.py) ---
def split_and_clean_ofertant(raw_text):
    if not raw_text or pd.isna(raw_text): return pd.NA, pd.NA
    raw_text = raw_text.strip()
    match = re.match(r'^(RO\s*\d+|\d+)\s+(.*)$', raw_text, re.IGNORECASE)
    if match:
        cui = match.group(1).replace(" ", "")
        ofertant = match.group(2).strip()
        return ofertant, cui
    else:
        return raw_text, pd.NA

# --- 3. Main API Test Function ---
def get_da_data_via_api(sicap_id):
    print(f"--- Testing API for {sicap_id} ---")

    # --- Use the PAYLOAD structure you provided ---
    payload = {
        "pageSize": 5,
        "showOngoingDa": True,
        "cookieContext": None,
        "pageIndex": 0,
        "sysDirectAcquisitionStateId": None,
        "finalizationDateStart": None,
        "finalizationDateEnd": None,
        # Set to None so the script works on any day
        "publicationDateStart": None,
        "publicationDateEnd": None,
        # Set to the dynamic sicap_id
        "uniqueIdentificationCode": sicap_id 
    }
    
    # --- Use the HEADERS you provided ---
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8,ro;q=0.7",
        "Authorization": "Bearer null",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=UTF-8",
        "Culture": "ro-RO",
        "HttpSessionID": "null",
        "Origin": "https://www.e-licitatie.ro",
        "Referer": "https://www.e-licitatie.ro/pub/direct-acquisitions/list/1",
        "RefreshToken": "null",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    
    try:
        response = requests.post(API_URL_DA, json=payload, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()
        
        if data and data.get('items'):
            item = data['items'][0]
            ofertant_raw = item.get('supplierName')
            ofertant, cui = split_and_clean_ofertant(ofertant_raw)
            view_id = item.get('directAcquisitionId')
            seap_url = f"{BASE_VIEW_URL_DA}{view_id}"
            result = {
                "SICAP ID": sicap_id, "Titlu": item.get('directAcquisitionName'),
                "Ofertant": ofertant, "Ofertant CUI": cui,
                "Valoare estimata": item.get('estimatedValueRon'),
                "Valoare cumparare": item.get('closingValue'),
                "seap_url": seap_url, "Data publicare": item.get('publicationDate')
            }
            print("  > SUCCESS: Found data.")
            return result
        else:
            print(f"  > FAILED: API response for {sicap_id} did not contain 'items'.")
            return {"SICAP ID": sicap_id, "error": "No items found in response"}
    except requests.exceptions.RequestException as e:
        print(f"  > FAILED: API request error for {sicap_id}: {e}")
        return {"SICAP ID": sicap_id, "error": str(e)}

# --- 5. Run the Test ---
if __name__ == "__main__":
    test_ids = ["DA39142545", "DA38262087", "DA38207557"]
    results = []
    for an_id in test_ids:
        data = get_da_data_via_api(an_id)
        results.append(data)
    print("\n--- API Test Complete ---")
    df = pd.DataFrame(results)
    print(df.to_string())