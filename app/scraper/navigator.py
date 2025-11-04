# app/scraper/navigator.py
import time
from selenium import webdriver
import json
import os
import pandas as pd
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains 
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException

# A class to encapsulate all browser navigation actions
class WebsiteNavigator:
    """
    Manages the Selenium WebDriver and browser interactions.
    """
    def __init__(self, email, password):
        """
        Initializes the navigator with user credentials and sets up the WebDriver.
        """
        self.email = email
        self.password = password
        
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.cookie_path = os.path.join(project_root, 'session', 'cookies.json')
        
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless") # Run in headless mode (no UI)
        options.add_argument("--no-sandbox")
        options.add_argument("--start-maximized")
        
        # --- MODIFICATIONS ---
        # Set a fixed, large window size. This is often more
        # reliable than "--start-maximized" for scraping.
        #options.add_argument("--window-size=1920,1080")
        
        # --- NEW LINE TO SET ZOOM TO 50% ---
        options.add_argument("--force-device-scale-factor=0.5")
        
        options.add_argument("--disable-dev-shm-usage")

        driver_path = os.path.join(project_root, 'drivers', 'chromedriver.exe')
        service = ChromeService(executable_path=driver_path)

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.execute_script("document.body.style.zoom = '50%'")
        print("WebDriver initialized with 50% zoom.")

    def navigate_to_acquisitions(self):
        """
        Navigates to the 'Vizualizare achiziții' page by clicking through the main menu.
        This mimics a real user's navigation flow.
        """
        print("🧭 Starting menu navigation...")
        wait = WebDriverWait(self.driver, 5) # Wait up to 15 seconds for elements

        try:
            # -----------------------------------------------------------------
            # Step 1: Click on the main "Achiziții" menu item
            # -----------------------------------------------------------------
            # We locate the <a> tag that contains a <span> with the text "Achiziții".
            # This is a reliable way to find the correct menu item.
            print("  -> Looking for 'Achiziții' main menu...")
            achizitii_menu_xpath = "//a[.//span[text()='Achiziții']]"
            
            main_menu_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, achizitii_menu_xpath))
            )
            main_menu_button.click()
            print("  -> Clicked 'Achiziții' menu item.")

            # -----------------------------------------------------------------
            # Step 2: Click on the "Vizualizare achiziții" sub-menu item
            # -----------------------------------------------------------------
            # This item appears after the first click. We find it using its unique href.
            print("  -> Looking for 'Vizualizare achiziții' sub-menu...")
            view_acquisitions_selector = "a[href='#/acquisitions/view']"
            
            sub_menu_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, view_acquisitions_selector))
            )
            sub_menu_button.click()
            print("  -> Clicked 'Vizualizare achiziții' sub-menu.")

            # -----------------------------------------------------------------
            # Step 3: Confirm navigation was successful
            # -----------------------------------------------------------------
            # We wait until the URL in the browser contains the expected path.
            wait.until(EC.url_contains("acquisitions/view"))
            print("✅ Successfully navigated to the acquisitions page!")
            return True

        except TimeoutException:
            print("❌ Error: A menu item was not found or clickable in time.")
            self.driver.save_screenshot("menu_navigation_error.png")
            return False
        except Exception as e:
            print(f"❌ An unexpected error occurred during menu navigation: {e}")
            self.driver.save_screenshot("menu_navigation_error.png")
            return False
    
    # app/scraper/navigator.py

# ... (imports and other class methods remain the same) ...

    def scrape_acquisitions(self):
        """
        Navigates to the acquisitions page, sets page size to 100 if needed,
        and scrapes details from each item by processing one full page at a time.
        """
        print("🚀 Starting acquisition scraping process...")
        
        wait = WebDriverWait(self.driver, 5)
        
        if not self.navigate_to_acquisitions():
            print("Could not navigate to acquisitions page. Aborting scrape.")
            return

        # -----------------------------------------------------------------
        # Step 1: Set page size to 100 (if not already set)
        # -----------------------------------------------------------------
        try:
            print("Checking page size...")
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "mat-paginator")))
            page_size_element = self.driver.find_element(
                By.CSS_SELECTOR, "mat-select[aria-label='Elemente pe pagină:'] .mat-select-min-line"
            )

            if "20" not in page_size_element.text:
                print("Page size is not 20. Setting it now...")
                
                # --- SCROLLING LOGIC REMOVED ---
                # We are no longer scrolling here.
                # We assume the 50% zoom makes the paginator visible.
                
                # Now that the paginator is visible, click it
                dropdown_locator = (By.CSS_SELECTOR, "mat-select[aria-label='Elemente pe pagină:']")
                wait.until(EC.element_to_be_clickable(dropdown_locator)).click()

                option_20 = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//mat-option[.//span[contains(text(), '20')]]")
                ))
                option_20.click()

                print("  -> Waiting 3 seconds for table to reload...")
                time.sleep(3)
                print("✅ Page size successfully set to 20.")
            else:
                print("✅ Page size is already set to 20.")

        except Exception as e:
            print(f"❌ An error occurred during page size setup: {e}")
            self.driver.save_screenshot("pagesize_error.png")

        # The rest of the function remains the same...
        page_count = 1
        all_data = []

        while True:
            print(f"\n--- Processing Page {page_count} ---")
            
            try:
                wait.until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "button[mattooltip='Detalii achiziție']")
                ))
                buttons_on_page = self.driver.find_elements(
                    By.CSS_SELECTOR, "button[mattooltip='Detalii achiziție']"
                )
                num_buttons = len(buttons_on_page)

                if num_buttons == 0:
                    print("No items found on this page. Ending process.")
                    break
                
                print(f"Found {num_buttons} items on this page.")
            except TimeoutException:
                print("Could not find any items on the page. Assuming scraping is complete.")
                break

            for i in range(num_buttons):
                print(f"  -> Processing item {i + 1} of {num_buttons}...")
                try:
                    wait.until(EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "button[mattooltip='Detalii achiziție']")
                    ))
                    all_buttons_on_page = self.driver.find_elements(
                        By.CSS_SELECTOR, "button[mattooltip='Detalii achiziție']"
                    )

                    button_to_click = all_buttons_on_page[i]
                    
                    try:
                        # We keep this scroll, as it helps click the correct button
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", button_to_click)
                        time.sleep(1)
                        button_to_click.click()
                    except ElementClickInterceptedException:
                        print("    -> Normal click intercepted. Retrying with JavaScript click.")
                        self.driver.execute_script("arguments[0].click();", button_to_click)

                    time.sleep(1)
                    print("    -> Wait before getting the 'Număr anunț SICAP'.")
                    target_element = wait.until(EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(text(), 'Număr anunț SICAP')]/following-sibling::div//span")
                    ))
                    
                    sicap_value = target_element.text.strip()
                    print(f"    ✅ Success! Scraped data: {sicap_value}")
                    all_data.append(sicap_value)
                    
                    time.sleep(2)
                    self.driver.back()

                except (StaleElementReferenceException, TimeoutException, IndexError) as e:
                    print(f"    ❌ Error on item {i + 1}: {type(e).__name__}. Skipping item.")
                    if "acquisitions/view" not in self.driver.current_url:
                        self.driver.get("https://coordonare.pnrr.gov.ro/#/acquisitions/view") 
                    continue

            print(f"--- Finished processing all items on page {page_count}. ---")
            try:
                # --- SCROLLING LOGIC REMOVED ---
                # We no longer scroll to the paginator.
                # paginator = self.driver.find_element(By.TAG_NAME, "mat-paginator")
                # self.driver.execute_script("arguments[0].scrollIntoView(true);", paginator)
                time.sleep(1)
                
                next_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Următoarea pagină']")
                
                if next_button.get_attribute("disabled"):
                    print("\nLast page reached. All pages have been processed. ✔️")
                    break
                else:
                    next_button.click()
                    page_count += 1
                    time.sleep(3) 
                    
            except NoSuchElementException:
                print("\nCould not find 'Next Page' button. Assuming it's the only page.")
                break
        
        print(f"\nScraping finished. Total items found: {len(all_data)}")
        print("First 10 items scraped:", all_data[:10])

    def scrape_company_beneficiaries(self, cui):
        """
        Navigates to the company details page for a given CUI,
        refreshes the page to load data, and scrapes the
        'Beneficiari reali' names from the correct table.
        
        Assumes the driver is already logged in.
        
        :param cui: The company CUI (e.g., "123456")
        :return: A tuple of (string: names, string: url)
        """
        
        # 1. Construct URL
        target_url = f"https://coordonare.pnrr.gov.ro/#/acquisitions/detalii-companie/{cui}"
        
        print(f"    > Navigating to company page: ...{cui}")
        self.driver.get(target_url)
        
        # --- FIX 1: REFRESH PAGE TO LOAD DATA ---
        print("    > Refreshing page to load data...")
        self.driver.refresh()
        time.sleep(1) 
        
        wait = WebDriverWait(self.driver, 10) 
        
        # --- FIX 2: MORE SPECIFIC LOCATORS ---
        target_table_xpath = "//mat-table[.//mat-header-cell[contains(normalize-space(), 'Dată naștere')]]"
        names_locator = (By.XPATH, 
            f"{target_table_xpath}//mat-cell[contains(@class, 'cdk-column-name')]//span[contains(@class, 'font-weight-600')]"
        )
        no_records_locator = (By.XPATH, 
            f"{target_table_xpath}//span[contains(normalize-space(), 'Nu există înregistrări.')]"
        )
        
        try:
            # 3. Wait for the page to load
            wait.until(
                EC.any_of(
                    EC.presence_of_element_located(names_locator),
                    EC.presence_of_element_located(no_records_locator)
                )
            )

            company_denumire = None
            try:
                # Find the h4 element containing "Denumire:"
                denumire_xpath = "//h4[contains(., 'Denumire:')]//span[not(contains(@class, 'font-weight-600'))]"
                denumire_element = self.driver.find_element(By.XPATH, denumire_xpath)
                company_denumire = denumire_element.text.strip()
                print(f"   > Found Denumire: {company_denumire}")
            except NoSuchElementException:
                print("   > Warning: Could not find 'Denumire' on page")
            except Exception as e:
                print(f"   > Warning: Error extracting Denumire: {e}")
            
            # 4. Try to find the name elements
            name_elements = self.driver.find_elements(*names_locator)
            
            if name_elements:
                # 5.a. Names were found
                names = [el.text.strip() for el in name_elements]
                result = ", ".join(names)
                print(f"    > Found: {result}")
                # --- MODIFICATION: Return URL ---
                return result, target_url, company_denumire
            else:
                # 5.b. No names found
                print("    > No beneficiaries found (Nu există înregistrări).")
                # --- MODIFICATION: Return URL ---
                return pd.NA, target_url, company_denumire

        except TimeoutException:
            # 5.c. Neither element appeared in time
            print("    > FAILED: Page timed out. Beneficiary table or 'no records' message not found.")
            # --- MODIFICATION: Return URL ---
            return pd.NA, target_url, None
        except Exception as e:
            # 5.d. Other unexpected error
            print(f"    > FAILED: An unexpected error occurred: {e}")
            # --- MODIFICATION: Return URL ---
            return pd.NA, target_url, None
    
    def search_acquisition_by_sicap(self, sicap_id, filters=None):
        """
        Navigates to acquisitions search page, applies filters including SICAP ID,
        and retrieves the details page URL for the first result.
        
        :param sicap_id: The SICAP announcement number to search for
        :param filters: Optional dict of additional filters to apply (for future use)
        :return: The acquisition details URL or None if not found
        """
        search_url = "https://coordonare.pnrr.gov.ro/#/acquisitions/view"
        print(f" > Navigating to acquisition search page...")
        self.driver.get(search_url)
        
        wait = WebDriverWait(self.driver, 10)
        
        try:
            # Find and fill the SICAP ID filter input
            print(f" > Filling SICAP ID filter with: {sicap_id}")
            sicap_input_xpath = "//input[@data-placeholder='Filtrează după număr anunț SICAP']"
            sicap_input = wait.until(EC.presence_of_element_located((By.XPATH, sicap_input_xpath)))
            sicap_input.clear()
            sicap_input.send_keys(str(sicap_id))
            
            # TODO: Add additional filters here if provided in the filters dict
            # Example structure for future:
            # if filters:
            #     if 'contract_type' in filters:
            #         # Apply contract type filter
            #     if 'date_range' in filters:
            #         # Apply date range filter
            
            # Click the "Aplică filtre" button
            print(f" > Clicking 'Aplică filtre' button...")
            apply_button_xpath = "//button[.//span[contains(text(), 'Aplică filtre')]]"
            apply_button = wait.until(EC.element_to_be_clickable((By.XPATH, apply_button_xpath)))
            apply_button.click()
            
            # Wait for the info button to appear (means results loaded)
            print(f" > Waiting for search results to load...")
            time.sleep(1)  # Small buffer for Angular to process                                         
            
            # Find the first "Detalii achiziție" info button
            print(f" > Searching for acquisition details button...")
            info_button_xpath = "//button[@mattooltip='Detalii achiziție']"
            info_button = wait.until(EC.presence_of_element_located((By.XPATH, info_button_xpath)))
            
            # Scroll to button and click it
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", info_button)
            
            try:
                info_button.click()
            except ElementClickInterceptedException:
                print(" > Normal click intercepted. Using JavaScript click...")
                self.driver.execute_script("arguments[0].click();", info_button)
            
            # Wait for navigation - look for a unique element on the details page instead of URL
            print(" > Waiting for details page to load...")
            
            details_url = self.driver.current_url
            
            # Verify we're actually on a details page
            if "acquisition-details" in details_url:
                print(f" > ✓ Found acquisition details URL: {details_url}")
                return details_url
            else:
                print(f" > ⚠️ Navigation may have failed. Current URL: {details_url}")
                return None                                                                                                                                 
            
            return details_url
            
        except TimeoutException:
            print(f" > ⚠️ Timeout: Could not find acquisition for SICAP ID {sicap_id}")
            return None
        except NoSuchElementException:
            print(f" > ⚠️ No search results found for SICAP ID {sicap_id}")
            return None
        except Exception as e:
            print(f" > ⚠️ Error during acquisition search: {e}")
            return None



    def login(self):
        """
        Manages the login process by either using saved cookies or performing a new login.
        """
        # The base URL is needed to load cookies properly
        base_url = "https://coordonare.pnrr.gov.ro"
        self.driver.get(base_url)

        # --- This part is the original login logic ---
        login_url = "https://coordonare.pnrr.gov.ro/auth/login"
        print(f"Navigating to {login_url}...")
        self.driver.get(login_url)

        try:
            wait = WebDriverWait(self.driver, 10)
            print("Locating username and password fields...")
            time.sleep(1)
            username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            username_field.send_keys(self.email)
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.password)
            
            #############login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
            login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Autentificare']]")))
            time.sleep(1)
            print("Clicking login button...")
            login_button.click()
            
            #wait.until(EC.not_(EC.url_contains('/auth/login')))
            print("Login successful! Current URL:", self.driver.current_url)

        except Exception as e:
            print(f"An error occurred during login: {e}")
            self.driver.save_screenshot("login_error.png")
            return False
        return True

    def close(self):
        """Closes the browser and quits the driver."""
        if self.driver:
            print("Closing the browser.")
            self.driver.quit()