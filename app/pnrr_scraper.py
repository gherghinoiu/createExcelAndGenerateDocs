# app/pnrr_scraper.py
import pandas as pd
import re
import time
from app.scraper.navigator import WebsiteNavigator
from app.utils.config import (
    PNRR_EMAIL, 
    PNRR_PASSWORD, 
    VALID_CODES_WITH_CUI_PATH, # Make sure this is the correct variable
    SICAP_ID_HEADER 
)
NO_ACQUISITION_FOUND = "[NU A FOST GASIT URL-UL ACHIZITIEI]"

def recreate_navigator_session(navigator):
    """
    Recreates the browser session if it becomes invalid.
    Returns a new navigator instance with fresh login.
    """
    print(" > ⚠️ Browser session invalid. Recreating session...")
    try:
        navigator.close()
    except:
        pass  # Session already dead
    
    # Create new navigator and login
    new_navigator = WebsiteNavigator(email=PNRR_EMAIL, password=PNRR_PASSWORD)
    login_success = new_navigator.login()
    
    if login_success:
        print(" > ✓ New session created successfully")
        return new_navigator
    else:
        print(" > ✗ Failed to create new session")
        return None


def run_beneficiary_scraper():
    """
    Orchestrates the scraping of "Beneficiari reali" from the PNRR platform.
    
    This function performs the following steps:
    1. Loads the 'valid_codes_with_cui.xlsx' file.
    2. Checks for/creates 'Beneficiari reali' columns.
    3. Initializes the WebsiteNavigator.
    4. Performs a login to the PNRR platform.
    5. Loops through each row in the Excel file.
    6. If a row is missing data or failed, scrapes the beneficiary data and URL.
    7. Updates the DataFrame in-place.
    8. Saves the updated DataFrame back to 'valid_codes_with_cui.xlsx'.
    9. Closes the browser.
    """
    print("--- Step 4: Scraping Real Beneficiaries (PNRR) ---")

    # 1. Load the "with CUI" data file
    if not VALID_CODES_WITH_CUI_PATH.exists():
        print(f"Error: File not found at {VALID_CODES_WITH_CUI_PATH}")
        print("Please ensure Step 3 (CUI Split) ran successfully.")
        return False

    try:
        df = pd.read_excel(VALID_CODES_WITH_CUI_PATH)
    except Exception as e:
        print(f"Error reading {VALID_CODES_WITH_CUI_PATH}: {e}")
        return False

    if df.empty:
        print("  > No data found in valid_codes_with_cui.xlsx. Skipping beneficiary scrape.")
        return True
    
    if 'Ofertant CUI' not in df.columns:
        print("  > Error: 'Ofertant CUI' column not found in file.")
        return False
    
    # Check for Ofertant column
    if 'Ofertant' not in df.columns:
        print(" > Warning: 'Ofertant' column not found. Creating empty column.")
        df['Ofertant'] = pd.NA
        
    # Check for columns and create if they don't exist
    if 'Beneficiari reali' not in df.columns:
        df['Beneficiari reali'] = pd.NA
        print("  > Column 'Beneficiari reali' created.")
        
    if 'Beneficiari reali URL' not in df.columns:
        df['Beneficiari reali URL'] = pd.NA
        print("  > Column 'Beneficiari reali URL' created.")

    if 'Detalii achizitie URL PNRR' not in df.columns:
        df['Detalii achizitie URL PNRR'] = pd.NA
        print(" > Column 'Detalii achizitie URL PNRR' created.")
        
    print(f"  > Loaded {len(df)} companies with CUI to scrape.")

    # 2. Initialize the navigator
    navigator = WebsiteNavigator(email=PNRR_EMAIL, password=PNRR_PASSWORD)
    
    # 3. Perform login
    print("  > Attempting PNRR login...")
    login_successful = navigator.login()
    
    if not login_successful:
        print("  > Login failed. Cannot proceed with beneficiary scraping.")
        navigator.close()
        return False
    
    print("  > Login successful.")

    # 4. Loop through each row and scrape
    
    for index, row in df.iterrows():
        # Restart browser every 250 records to prevent memory issues
        if index > 0 and index % 250 == 0:
            print(f"\n > Restarting browser at record {index} to free memory...")
            navigator.close()
            navigator = WebsiteNavigator(email=PNRR_EMAIL, password=PNRR_PASSWORD)
            navigator.login()
            print(" > Browser restarted successfully")

        cui = row['Ofertant CUI']
        sicap_id = row[SICAP_ID_HEADER]
        
        print(f"\n  Processing {index + 1}/{len(df)}: SICAP ID {sicap_id}")
        
        # --- 1. IMPROVED LOGIC: Check both columns ---
        names_val = row['Beneficiari reali']
        url_val = row['Beneficiari reali URL']
        acquisition_url_val = row['Detalii achizitie URL PNRR']

        is_names_empty = pd.isna(names_val)
        is_names_failed = (str(names_val) == 'SCRAPE FAILED')
        is_url_empty = pd.isna(url_val)
        is_acquisition_url_empty = pd.isna(acquisition_url_val)

        # We need to scrape if ANY of these are true
        we_need_to_scrape = is_names_empty or is_names_failed or is_url_empty or is_acquisition_url_empty

        # If we DON'T need to scrape, skip the row
        if not we_need_to_scrape:
            print(f" > All data already exists for {row['Ofertant CUI']}. Skipping.")
            continue
        
        if is_names_failed:
            print("    > Retrying row that previously failed.")
        # --- End of improved logic ---

        if pd.isna(cui):
            print("    > Skipping row, CUI is empty.")
            df.loc[index, 'Beneficiari reali'] = pd.NA # Ensure it's NA, not 'SCRAPE FAILED'
            df.loc[index, 'Beneficiari reali URL'] = pd.NA
            continue
            
        cui_str = str(cui)
        cui_cleaned = re.sub(r'[^0-9]', '', cui_str) 
        
        print(f"    > (Original CUI: {cui_str}, Cleaned: {cui_cleaned})")
        
        if not cui_cleaned:
            print(f"    > Skipping row, CUI '{cui_str}' became empty after cleaning.")
            df.loc[index, 'Beneficiari reali'] = pd.NA
            df.loc[index, 'Beneficiari reali URL'] = pd.NA
            continue
            
        try:
            # --- 2. NAVIGATION CALL ---
            # This is only reached if the checks above pass
            scraped_names, scraped_url, scraped_denumire = navigator.scrape_company_beneficiaries(cui_cleaned)

            # --- 3. VALIDATE DENUMIRE AGAINST OFERTANT ---
            excel_ofertant = row.get('Ofertant')

            if scraped_denumire:
                scraped_denumire_normalized = scraped_denumire.strip().upper()
                
                if pd.notna(excel_ofertant):
                    excel_ofertant_normalized = str(excel_ofertant).strip().upper()
                else:
                    excel_ofertant_normalized = ""
                
                if scraped_denumire_normalized != excel_ofertant_normalized:
                    print(f" > ⚠️ OFERTANT MISMATCH DETECTED!")
                    print(f"    Excel value: '{excel_ofertant}'")
                    print(f"    Scraped value: '{scraped_denumire}'")
                    print(f" > Updating 'Ofertant' column with scraped value.")
                    df.loc[index, 'Ofertant'] = scraped_denumire
                else:
                    print(f" > ✓ Ofertant matches: '{scraped_denumire}'")
            else:
                print(f" > No 'Denumire' found on PNRR page for CUI {cui_cleaned}")
            
            # Update DataFrame in-place
            df.loc[index, 'Beneficiari reali'] = scraped_names
            df.loc[index, 'Beneficiari reali URL'] = scraped_url

            # --- NEW: SEARCH FOR ACQUISITION DETAILS URL ---
            print(f" > Searching for acquisition details URL...")
            
            # Check if we already have the URL
            existing_url = row.get('Detalii achizitie URL PNRR')
            if pd.notna(existing_url) and str(existing_url).strip():
                print(f" > Acquisition URL already exists. Skipping search.")
            else:
                try:
                    acquisition_url = navigator.search_acquisition_by_sicap(sicap_id)
                    if acquisition_url:
                        df.loc[index, 'Detalii achizitie URL PNRR'] = acquisition_url
                        print(f" > ✓ Saved acquisition URL")
                    else:
                        print(f" > Could not find acquisition URL - marking as not found")
                        df.loc[index, 'Detalii achizitie URL PNRR'] = NO_ACQUISITION_FOUND
                    
                    # Navigate back to prevent issues with next iteration
                    navigator.driver.get("https://coordonare.pnrr.gov.ro/#/acquisitions/view")
                    time.sleep(1)

                except Exception as e:
                    print(f" > Error searching for acquisition: {e}")
                    df.loc[index, 'Detalii achizitie URL PNRR'] = NO_ACQUISITION_FOUND
            
        except Exception as e:
            print(f"    > CRITICAL ERROR during scrape for {cui_cleaned}: {e}")
            print("    > Saving 'SCRAPE FAILED' and continuing...")
            
            # Update DataFrame in-place with error
            df.loc[index, 'Beneficiari reali'] = "SCRAPE FAILED"
            failed_url = f"https://coordonare.pnrr.gov.ro/#/acquisitions/detalii-companie/{cui_cleaned}"
            df.loc[index, 'Beneficiari reali URL'] = failed_url

    # 8. Close the browser
    print("\n  > Scrape complete. Closing browser.")
    navigator.close()

    # 7. Save updated file
    try:
        df.to_excel(VALID_CODES_WITH_CUI_PATH, index=False)
        print(f"\n  > Successfully updated {VALID_CODES_WITH_CUI_PATH} with 'Beneficiari reali' data.")
        print("--- Step 4 Complete ---")
        return True
    except Exception as e:
        print(f"  > CRITICAL ERROR: Could not save final file to {VALID_CODES_WITH_CUI_PATH}: {e}")
        return False