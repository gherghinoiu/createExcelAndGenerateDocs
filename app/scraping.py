# app/scraping.py
import pandas as pd
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# --- NEW IMPORT ---
from selenium.common.exceptions import TimeoutException, NoSuchElementException, InvalidSessionIdException

# Import all paths, URLs, and locators from our central config
from app.utils.config import (
    VALID_FILE_PATH,
    DRIVER_PATH,
    URL_MAP,
    SICAP_ID_HEADER,
    INPUT_LOCATORS,
    SEARCH_BUTTON,
    SEARCH_BUTTON_SPINNER,
    LIST_PAGE_LOCATORS,
    # DETAILS_PAGE_LOCATORS is no longer needed
)

# --- 1. Helper Functions (No changes here) ---

def setup_driver():
    """Initializes a new Selenium WebDriver instance."""
    print("  > Setting up Chrome driver...")
    
    if not DRIVER_PATH.exists():
        print(f"Error: chromedriver.exe not found at {DRIVER_PATH}")
        return None

    service = ChromeService(executable_path=str(DRIVER_PATH))
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless")
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(2) 
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        return None

def clean_value(raw_text):
    """
    Cleans text like '9.749,50 RON' to '9.749,50'.
    """
    if pd.isna(raw_text) or not raw_text:
        return pd.NA
    match = re.search(r'^[0-9.,\s]+', raw_text.strip())
    if match:
        return match.group(0).strip()
    return pd.NA

def split_and_clean_ofertant(raw_text):
    """
    Splits 'RO31306086 Uniqit System SRL' OR '47489788 FULOP UNLIMITED'
    into CUI and Name.
    Returns (Ofertant, Ofertant CUI)
    """
    if pd.isna(raw_text) or not raw_text:
        return pd.NA, pd.NA
        
    raw_text = raw_text.strip()
    
    match = re.match(r'^(RO\s*\d+|\d+)\s+(.*)$', raw_text, re.IGNORECASE)
    
    if match:
        cui = match.group(1).replace(" ", "") 
        ofertant = match.group(2).strip()
        return ofertant, cui
    else:
        return raw_text, pd.NA

def safe_get_text(element, locator, clean_func=None, wait_time=2):
    """
    Tries to find a sub-element and get its text.
    'element' can be the driver or a parent element.
    """
    if not locator:
        return pd.NA
        
    try:
        wait = WebDriverWait(element, wait_time)
        sub_element = wait.until(EC.visibility_of_element_located(locator))
        text = sub_element.text.strip()
        
        if not text:
            return pd.NA
        if clean_func:
            return clean_func(text)
        return text
    except (TimeoutException, NoSuchElementException):
        return pd.NA
    except Exception as e:
        return pd.NA

# --- 2. Scraping Functions (No changes here) ---

def scrape_sicap_page(driver, sicap_id, id_type, base_url):
    """
    Orchestrator: Searches, scrapes list, clicks, gets URL.
    Returns a dictionary of all found data.
    """
    try:
        # 1. Go to the correct search page
        driver.get(base_url)
        wait = WebDriverWait(driver, 10) 
        
        # 2. Find correct input field, clear it, and type
        input_locator = INPUT_LOCATORS.get(id_type)
        if not input_locator:
            return {'seap_url': f"No input locator configured for {id_type}"}
            
        input_field = wait.until(EC.visibility_of_element_located(input_locator))
        input_field.clear()
        input_field.send_keys(sicap_id)
        
        # 3. Click the search button
        search_button = wait.until(EC.element_to_be_clickable(SEARCH_BUTTON))
        search_button.click()
        
        # 4. Wait for the spinner to disappear
        wait.until(EC.invisibility_of_element_located(SEARCH_BUTTON_SPINNER))
        time.sleep(0.5) 

        # --- 5. Scrape ALL available data from the list ---
        scraped_data = {} 
        locators = LIST_PAGE_LOCATORS.get(id_type, {})
        
        try:
            # Find the main container for the single result
            item_container = wait.until(EC.visibility_of_element_located(locators.get('item_container')))
            print("    > Found result item container. Scraping list...")

            # Scrape Ofertant and CUI (if available)
            ofertant_raw = safe_get_text(item_container, locators.get('ofertant_raw'))
            scraped_data['Ofertant'], scraped_data['Ofertant CUI'] = split_and_clean_ofertant(ofertant_raw)

            # Scrape Valoare estimata
            scraped_data['Valoare estimata'] = safe_get_text(
                item_container, locators.get('valoare_estimata_raw'), clean_func=clean_value
            )
            
            # Scrape Valoare cumparare directa (if available)
            cumparare_locator = locators.get('valoare_cumparare_raw')
            if cumparare_locator:
                scraped_data['Valoare cumparare directa'] = safe_get_text(
                    item_container, cumparare_locator, clean_func=clean_value
                )

            print(f"    > List scrape complete: {scraped_data}")

            # --- 6. Click the link to get the URL ---
            link_to_click = wait.until(EC.element_to_be_clickable(locators.get('link_to_click')))
            print("    > Clicking result link...")
            driver.execute_script("arguments[0].click();", link_to_click)
            
            # Wait for the URL to change
            wait.until(lambda d: base_url not in d.current_url)
            
            # Get the URL
            scraped_data['seap_url'] = driver.current_url
            print(f"    > Landed on: {scraped_data['seap_url']}")

            # --- 7. Go back for the next loop ---
            print("    > Navigating back to search page.")
            driver.back()
            # Wait for the search page to be ready again
            wait.until(EC.visibility_of_element_located(input_locator)) 
            
            return scraped_data

        except (TimeoutException, NoSuchElementException):
            print("    > FAILED: 0 results found (or item container not found).")
            return {'seap_url': '0 results found'}
            
    # --- NOTE: This 'try' block wraps the one above ---
    # This allows the 'InvalidSessionIdException' logic in run_scraper
    # to catch crashes that happen *during* the scrape.
    except (TimeoutException, NoSuchElementException):
        print("    > FAILED: Page timeout or element not found.")
        return {'seap_url': 'Page timeout'}
    except Exception as e:
        # Re-raise the exception so the 'run_scraper' can catch it
        raise e

# --- 3. Main Execution Function (UPDATED) ---

def run_scraper():
    """
    Main function to run the entire scraping process.
    (This version is resilient to browser crashes)
    """
    print("\n--- Step 2: Running Full Data Scraper ---")
    
    # 1. Load the cleaned data
    if not VALID_FILE_PATH.exists():
        print(f"Error: Cleaned file not found at {VALID_FILE_PATH}")
        return False
        
    try:
        df = pd.read_excel(VALID_FILE_PATH)
        df_original = df.copy() 
    except Exception as e:
        print(f"Error reading {VALID_FILE_PATH}: {e}")
        return False
        
    if df.empty:
        print("  > No valid rows found in valid_codes.xlsx. Skipping scrape.")
        return True

    print(f"  > Loaded {len(df)} valid rows to scrape.")

    # 2. Setup the *first* driver
    driver = setup_driver()
    if driver is None:
        print("  > Driver setup failed. Aborting scrape.")
        return False

    # 3. Prepare for scraping
    results_list = []
    id_type_pattern = re.compile(r'^[A-Z]+')

    # 4. Loop through all valid rows
    for index, row in df.iterrows():
        sicap_id = str(row[SICAP_ID_HEADER]).strip()
        
        print(f"\n  Processing {index + 1}/{len(df)}: {sicap_id}")
        
        match = id_type_pattern.match(sicap_id)
        if not match:
            print("    > FAILED: Could not determine ID type (DA, CN, etc.)")
            results_list.append({'seap_url': 'Invalid ID format'})
            continue
            
        id_type = match.group(0)
        base_url = URL_MAP.get(id_type)
        
        if not base_url:
            print(f"    > FAILED: No URL configured for type '{id_type}'")
            results_list.append({'seap_url': f'No URL for type {id_type}'})
            continue
            
        # --- 5. NEW RESILIENT SCRAPING BLOCK ---
        try:
            # Try to scrape the page
            scraped_data = scrape_sicap_page(driver, sicap_id, id_type, base_url)
            
        except InvalidSessionIdException:
            # This is the error you saw. It means the browser crashed.
            print(f"  > CRITICAL: Browser session crashed (InvalidSessionIdException).")
            print("    > Restarting browser and retrying this item...")
            
            try:
                driver.quit() # Kill the old, dead browser
            except Exception:
                pass # It's already dead, no problem
                
            driver = setup_driver() # Start a new, fresh browser
            if driver is None:
                print("  > Driver restart failed. Skipping item.")
                scraped_data = {'seap_url': 'Driver restart failed'}
            else:
                # Retry the *same item* one more time
                print(f"    > Retrying item: {sicap_id}")
                try:
                    scraped_data = scrape_sicap_page(driver, sicap_id, id_type, base_url)
                except Exception as e:
                    print(f"  > FAILED on retry: {e}")
                    scraped_data = {'seap_url': f'Failed on retry: {e}'}

        except Exception as e:
            # Catch any other unexpected error from scrape_sicap_page
            print(f"  > FAILED: An unexpected error occurred: {e}")
            scraped_data = {'seap_url': f'Error: {e}'}
            
        results_list.append(scraped_data)
            
    # 6. Close the *last* browser
    try:
        driver.quit()
        print("\n  > Scraping Complete.")
    except Exception as e:
        print(f"\n  > (Info) Error quitting final browser: {e}")
    
    # 7. Save results back to the Excel file
    try:
        results_df = pd.DataFrame(results_list)
        
        df_original.reset_index(drop=True, inplace=True)
        results_df.reset_index(drop=True, inplace=True)
        
        final_df = pd.concat([df_original, results_df], axis=1)
        
        final_df.to_excel(VALID_FILE_PATH, index=False)
        print(f"  > Successfully updated {VALID_FILE_PATH} with all scraped data.")
    except Exception as e:
        print(f"  > CRITICAL ERROR: Could not save results to {VALID_FILE_PATH}: {e}")
        return False
        
    print("--- Scraping Step Complete ---")
    return True