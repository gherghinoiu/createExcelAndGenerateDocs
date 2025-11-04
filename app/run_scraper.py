import pandas as pd
from pathlib import Path
import time
import re

# Selenium Imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# --- Import from our *other* project file ---
# This imports the data loading function and header names
# from your existing achizitii.py script.
try:
    from .achizitii import load_and_filter_data, NR_ANUNT_SICAP_HEADER, BASE_DIR
except ImportError:
    print("Error: Make sure 'achizitii.py' is in the same 'app' folder.")
    exit()

# --- Configuration ---
SCRAPER_URL = "https://e-licitatie.ro/pub/direct-acquisitions/list/1"

# Output files will also go into the 'processed' folder
PROCESSED_DIR = BASE_DIR / "processed"
SUCCESS_FILE = PROCESSED_DIR / "valid_sicap_links.xlsx"
FAIL_FILE = PROCESSED_DIR / "failed_sicap_searches.xlsx"

# --- Selenium Locators ---
INPUT_FIELD = (By.CSS_SELECTOR, "input[ng-model='vm.filter.uniqueIdentificationCode']")
SEARCH_BUTTON = (By.CSS_SELECTOR, "button[ng-click='vm.search()']")
SEARCH_BUTTON_SPINNER = (By.CSS_SELECTOR, "button[ng-click='vm.search()'] i.fa-spinner")
# This XPath finds the span with the total number of results
TOTAL_RESULTS_SPAN = (By.XPATH, "//span[contains(text(), 'rezultate pe pagina dintr-un total de:')]/following-sibling::span")
FIRST_RESULT_LINK = (By.CSS_SELECTOR, "a.title-entity.ng-binding")


def setup_driver():
    """Initializes a new Selenium WebDriver instance."""
    print("Setting up Chrome driver...")
    
    # --- THIS IS THE CHANGE ---
    # Define the path to the driver you just downloaded
    # (BASE_DIR is already imported from achizitii.py)
    DRIVER_PATH = BASE_DIR / "drivers" / "chromedriver.exe"
    
    if not DRIVER_PATH.exists():
        print(f"Error: chromedriver.exe not found at {DRIVER_PATH}")
        print("Please download it and place it in the 'drivers' folder.")
        return None

    # Tell ChromeService to use that specific .exe file
    service = ChromeService(executable_path=str(DRIVER_PATH))
    # --- END OF CHANGE ---

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5)
    return driver


def scrape_sicap_id(driver, sicap_id):
    """
    Searches for a single SICAP ID and returns its status and URL if found.
    (This version fixes the SyntaxError)
    """
    try:
        # 1. Go to the main search page
        driver.get(SCRAPER_URL)
        wait = WebDriverWait(driver, 20) 
        
        # 2. Find input, clear it, and type
        input_field = wait.until(EC.visibility_of_element_located(INPUT_FIELD))
        input_field.clear()
        input_field.send_keys(sicap_id)
        
        # 3. Click the search button
        search_button = wait.until(EC.element_to_be_clickable(SEARCH_BUTTON))
        search_button.click()
        
        # 4. Wait for the spinner to disappear
        print("   > Waiting for search results...")
        wait.until(EC.invisibility_of_element_located(SEARCH_BUTTON_SPINNER))
        
        # 5. Add a short, fixed pause
        time.sleep(0.5) 

        # 6. Count the result links
        result_links = driver.find_elements(FIRST_RESULT_LINK[0], FIRST_RESULT_LINK[1])
        total = len(result_links)
        
        # 7. Apply your logic
        if total == 1:
            # Success!
            print("   > Found 1 result. Attempting to click...")
            link = result_links[0]
            
            # Use a JavaScript click
            driver.execute_script("arguments[0].click();", link)
            
            # --- FIX 1: This is the correct way to wait for the URL to NOT contain something ---
            # We pass a lambda function to wait.until()
            wait.until(lambda d: not EC.url_contains('/list/1')(d))
            # --- END OF FIX 1 ---
            
            # Get the new URL
            final_url = driver.current_url
            
            # Navigate back for the next loop
            print("   > Navigating back to search page...")
            driver.back()
            # Wait for the search page to be ready again
            wait.until(EC.visibility_of_element_located(INPUT_FIELD))
            
            return ('success', final_url)
            
        elif total == 0:
            print("   > Found 0 results.")
            return ('fail', '0 results found')
        else:
            print(f"   > Found {total} results (multiple).")
            return ('fail', f'{total} results found (multiple)')
            
    except TimeoutException:
        return ('fail', 'Page timeout or element not found')
    except NoSuchElementException:
        return ('fail', 'Could not find a required element')
    except Exception as e:
        return ('fail', f'An unexpected error occurred: {e}')


def run_scraper():
    """
    Main function to run the entire scraping process.
    """
    print("--- SCRAPER START ---")
    
    # 1. Load data
    valid_rows_list, _ = load_and_filter_data()
    
    if not valid_rows_list:
        print("No valid rows to scrape. Exiting.")
        return
        
    print(f"Loaded {len(valid_rows_list)} valid rows to scrape.")
    
    # 2. Lists to hold results
    successful_links = []
    failed_searches = []
    
    # 3. Setup driver
    driver = setup_driver()
    
    # --- NEW ERROR CHECK ---
    if driver is None:
        print("Driver setup failed. Exiting script.")
        return
    # --- END NEW CHECK ---
    
    # 4. Loop through all valid rows
    for index, row in enumerate(valid_rows_list):
        sicap_id_raw = row.get(NR_ANUNT_SICAP_HEADER)
        sicap_id = re.sub(r'\s+', '', str(sicap_id_raw))
        
        print(f"\nProcessing {index + 1}/{len(valid_rows_list)}: {sicap_id}")
        
        status, detail = scrape_sicap_id(driver, sicap_id)
        
        if status == 'success':
            print(f"  > SUCCESS: Found URL: {detail}")
            successful_links.append({'sicap_id': sicap_id, 'url': detail})
        else:
            print(f"  > FAILED: {detail}")
            failed_searches.append({'sicap_id': sicap_id, 'reason': detail})
            
    # 5. Close the browser
    driver.quit()
    print("\n--- Scraping Complete ---")
    
    # 6. Save results to Excel files
    if successful_links:
        print(f"Saving {len(successful_links)} successful links to {SUCCESS_FILE}...")
        pd.DataFrame(successful_links).to_excel(SUCCESS_FILE, index=False)
        
    if failed_searches:
        print(f"Saving {len(failed_searches)} failed searches to {FAIL_FILE}...")
        pd.DataFrame(failed_searches).to_excel(FAIL_FILE, index=False)
        
    print("--- SCRIPT FINISHED ---")


# --- This runs the main function when you execute the script ---
if __name__ == "__main__":
    run_scraper()