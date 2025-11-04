# app/utils/config.py
import os
from dotenv import load_dotenv
# app/utils/config.py
from pathlib import Path
from selenium.webdriver.common.by import By

# Fetching credentials from environment variables
load_dotenv() # This tells Python to load variables from the .env file
PNRR_EMAIL = os.getenv("PNRR_EMAIL")
PNRR_PASSWORD = os.getenv("PNRR_PASSWORD")
# --- Base Directories ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = BASE_DIR / "processed"
GENERATED_DOCS_DIR = BASE_DIR / "generated_docs"

# --- 1. CLEANING FILE PATHS ---
INPUT_FILE_NAME = 'export_achizitii_2025-10-20T12_03_21.815970182_2012.xlsx'
INPUT_FILE_PATH = BASE_DIR / INPUT_FILE_NAME
VALID_FILE_PATH = PROCESSED_DIR / "valid_codes.xlsx"
INVALID_FILE_PATH = PROCESSED_DIR / "invalid_codes.xlsx"
VALID_CODES_WITH_CUI_PATH = PROCESSED_DIR / "valid_codes_with_cui.xlsx"
VALID_CODES_WITH_CUI_PATH_TEST = PROCESSED_DIR / "valid_codes_with_cui_test.xlsx"
VALID_CODES_NO_CUI_PATH = PROCESSED_DIR / "valid_codes_no_cui.xlsx"

# --- 2. SCRAPING URL MAP ---
URL_MAP = {
    'DA': "https://www.e-licitatie.ro/pub/direct-acquisitions/list/1",
    'DAN': "https://www.e-licitatie.ro/pub/da-award-notices/list/1",
    'CN': "https://www.e-licitatie.ro/pub/notices/contract-notices/list/2/1",
    'SCN': "https://www.e-licitatie.ro/pub/notices/contract-notices/list/17/1",
    'ADV': "https://www.e-licitatie.ro/pub/adv-notices/list/1",
}

# --- 3. SCRAPING LOCATORS (BASED ON seap result DIVS.txt) ---

# Locators for the SEARCH INPUT field on each page
INPUT_LOCATORS = {
    'DA': (By.CSS_SELECTOR, "input[ng-model='vm.filter.uniqueIdentificationCode']"),
    'DAN': (By.CSS_SELECTOR, "input[ng-model='vm.filter.noticeNo']"),
    'CN': (By.CSS_SELECTOR, "input[name='noticeNoInput']"),
    'SCN': (By.CSS_SELECTOR, "input[name='noticeNoInput']"),
    'ADV': (By.CSS_SELECTOR, "input[ng-model='vm.filter.noticeNo']"),
}

# General locators (same for all pages)
SEARCH_BUTTON = (By.CSS_SELECTOR, "button[ng-click='vm.search()']")
SEARCH_BUTTON_SPINNER = (By.CSS_SELECTOR, "button[ng-click='vm.search()'] i.fa-spinner")

# --- NEW: Locators for the LIST PAGE (for ALL types) ---
# We scrape as much as we can from the list *before* clicking.
LIST_PAGE_LOCATORS = {
    # 'item_container' is the parent div for the whole search result
    'DA': {
        'item_container': (By.CSS_SELECTOR, "div[ng-repeat='row in vm.listItems']"),
        'link_to_click': (By.CSS_SELECTOR, "a.title-entity.ng-binding"),
        # --- UPDATED LOCATOR: Targets the specific 'Suplier' icon ---
        'ofertant_raw': (By.XPATH, ".//i[contains(@sicap-icon, 'Suplier')]/following-sibling::strong"),
        'valoare_estimata_raw': (By.XPATH, ".//i[contains(@class, 'fa-eur')]/following-sibling::strong"),
        'valoare_cumparare_raw': (By.XPATH, ".//div[contains(@class, 'u-items-list__item__value')]/span[contains(@class, 'ng-binding')]"),
    },
    'DAN': {
        'item_container': (By.CSS_SELECTOR, "div[ng-repeat='row in vm.listItems']"),
        'link_to_click': (By.CSS_SELECTOR, "a.title-entity.ng-binding"),
        # --- UPDATED LOCATOR: Targets the specific 'Suplier' icon ---
        'ofertant_raw': (By.XPATH, ".//i[contains(@sicap-icon, 'Suplier')]/following-sibling::strong"),
        'valoare_estimata_raw': (By.XPATH, ".//div[contains(@class, 'u-items-list__item__value')]/span[contains(@class, 'ng-binding')]"),
        'valoare_cumparare_raw': None, # Does not exist on list
    },
    'CN': {
        'item_container': (By.CSS_SELECTOR, "div[ng-repeat='row in vm.listItems']"),
        'link_to_click': (By.CSS_SELECTOR, "a.title-entity.iffyTip"),
        'ofertant_raw': None, # Does not exist on list
        'valoare_estimata_raw': (By.CSS_SELECTOR, "div.u-items-list__item__value.title"),
        'valoare_cumparare_raw': None,
    },
    'SCN': {
        'item_container': (By.CSS_SELECTOR, "div[ng-repeat='row in vm.listItems']"),
        'link_to_click': (By.CSS_SELECTOR, "a.title-entity.iffyTip"),
        'ofertant_raw': None, # Does not exist on list
        'valoare_estimata_raw': (By.CSS_SELECTOR, "div.u-items-list__item__value.title"),
        'valoare_cumparare_raw': None,
    },
    'ADV': {
        'item_container': (By.CSS_SELECTOR, "div[ng-repeat='row in vm.listItems']"),
        'link_to_click': (By.CSS_SELECTOR, "a.title-entity.ng-binding"),
        'ofertant_raw': None, # Does not exist on list
        'valoare_estimata_raw': (By.XPATH, ".//div[contains(@class, 'u-items-list__item__value')]/span[contains(@class, 'ng-binding')]"),
        'valoare_cumparare_raw': None,
    }
}

# --- Locators for the DETAILS PAGE (for CN, SCN, ADV) ---
# We use these *after* clicking to get the data that was missing from the list
DETAILS_PAGE_LOCATORS = {
    'CN': {
        'Ofertant': (By.CSS_SELECTOR, "a[ng-click='vm.searchBySupplier()']"),
        'Ofertant CUI': (By.XPATH, "//*[starts-with(normalize-space(), 'CUI')]/following-sibling::span[contains(@class, 'u-displayfield__field')]"),
    },
    'SCN': {
        'Ofertant': (By.CSS_SELECTOR, "a[ng-click='vm.searchBySupplier()']"),
        'Ofertant CUI': (By.XPATH, "//*[starts-with(normalize-space(), 'CUI')]/following-sibling::span[contains(@class, 'u-displayfield__field')]"),
    },
    'ADV': {
        'Ofertant': (By.CSS_SELECTOR, "a[ng-click='vm.searchBySupplier()']"),
        'Ofertant CUI': (By.XPATH, "//*[starts-with(normalize-space(), 'CUI')]/following-sibling::span[contains(@class, 'u-displayfield__field')]"),
    }
}

# --- 4. TEMPLATES & DRIVERS ---
TEMPLATE_1_FILE = BASE_DIR / "templates" / "template1.docx"
TEMPLATE_2_FILE = BASE_DIR / "templates" / "template2.docx"
DRIVER_PATH = BASE_DIR / "drivers" / "chromedriver.exe"

# --- 5. EXCEL HEADERS ---
SICAP_ID_HEADER = 'Nr. anunt SICAP'