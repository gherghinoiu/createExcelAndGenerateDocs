# run_workflow.py
from app.cleaning import clean_excel_file, split_valid_codes_by_cui
from app.scraping import run_scraper
from app.pnrr_scraper import run_beneficiary_scraper
# --- 1. ADD NEW IMPORTS ---
from app.doc_generator import run_document_generation
from app.utils.config import VALID_CODES_WITH_CUI_PATH_TEST, VALID_CODES_WITH_CUI_PATH, VALID_CODES_NO_CUI_PATH

def main_workflow():
    print("--- Workflow Started ---")
    
    # --- STEP 1: CLEANING ---
    step_1_success = clean_excel_file()
    if not step_1_success:
        print("Workflow stopped: Cleaning step failed.")
        return

    # --- STEP 2: SCRAPING ---
    step_2_success = run_scraper()
    if not step_2_success:
        print("Workflow stopped: Scraping step failed.")
        return

    # --- STEP 3: SPLIT CUI FILE ---
    print("\n--- Step 3: Splitting file by CUI ---")
    step_3_success = split_valid_codes_by_cui()
    if not step_3_success:
        print("Workflow stopped: CUI splitting step failed.")
        return

    # --- STEP 4: SCRAPE BENEFICIARIES ---
    print("\n--- Step 4: Scraping Beneficiary Data (PNRR) ---")
    step_4_success = run_beneficiary_scraper()
    if not step_4_success:
        print("Workflow stopped: Beneficiary scraping step failed.")
        return

    # --- 2. UPDATE STEP 5 ---
    print("\n--- Step 5: Document Generation ---")
    # We create a list of all files we want to process.
    files_to_process = [VALID_CODES_WITH_CUI_PATH]
    
    step_5_success = run_document_generation(files_to_process)
    if not step_5_success:
        print("Workflow stopped: Document generation step failed.")
        return

    print("\n--- Workflow Finished ---")

if __name__ == "__main__":
    main_workflow()