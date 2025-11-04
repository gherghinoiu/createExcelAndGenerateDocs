# app/cleaning.py
import pandas as pd
import re
import os
from app.utils.config import (
    INPUT_FILE_PATH, 
    VALID_FILE_PATH, 
    INVALID_FILE_PATH, 
    PROCESSED_DIR,
    SICAP_ID_HEADER,
    VALID_CODES_WITH_CUI_PATH,
    VALID_CODES_NO_CUI_PATH
)

def clean_excel_file():
    """
    Reads the raw Excel file, cleans the SICAP ID column,
    and saves the results into 'valid_codes.xlsx' and 'invalid_codes.xlsx'
    inside the 'processed' folder.
    """
    print("--- Step 1: Cleaning Raw Excel File ---")
    
    # 1. Create the 'processed' directory if it doesn't exist
    PROCESSED_DIR.mkdir(exist_ok=True)
    
    # 2. Check if the input file exists
    if not INPUT_FILE_PATH.exists():
        print(f"Error: Input file not found at: {INPUT_FILE_PATH}")
        print("Please make sure the file is in the root directory.")
        return False
    
    try:
        df = pd.read_excel(INPUT_FILE_PATH, header=0)
        print(f"Successfully loaded {INPUT_FILE_PATH.name}")
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return False
        
    # 3. Find the target column ('Nr. anunt SICAP')
    if SICAP_ID_HEADER not in df.columns:
        # Fallback to Column C (index 2) if header is not found
        if len(df.columns) > 2:
            col_target = df.columns[2]
            print(f"Warning: '{SICAP_ID_HEADER}' not found. Using Column C ('{col_target}') instead.")
        else:
            print(f"Error: Column '{SICAP_ID_HEADER}' not found and file has < 3 columns.")
            return False
    else:
        col_target = SICAP_ID_HEADER

    # 4. Define the cleaning regex pattern
    pattern = re.compile(r'(DA|DAN|CN|SCN|ADV)\d+')

    def extract_valid_code(value):
        if pd.isna(value):
            return None
        
        # Convert to string and remove all spaces
        clean_value = str(value).replace(' ', '')
        
        match = pattern.search(clean_value)
        if match:
            return match.group(0) # Return the matched valid code
        return None

    # 5. Apply cleaning logic
    df['extracted_code'] = df[col_target].apply(extract_valid_code)

    # 6. Separate valid and invalid rows
    valid_df = df[df['extracted_code'].notna()].copy()
    invalid_df = df[df['extracted_code'].isna()].copy()
    
    if not valid_df.empty:
        # Update target column with the cleaned code
        valid_df[col_target] = valid_df['extracted_code']
    
    # Drop the temporary column
    valid_df = valid_df.drop(columns=['extracted_code'])
    invalid_df = invalid_df.drop(columns=['extracted_code'])

    # 7. Save results to the 'processed' folder
    try:
        valid_df.to_excel(VALID_FILE_PATH, index=False)
        print(f"  > Saved {len(valid_df)} valid rows to: {VALID_FILE_PATH}")
        
        invalid_df.to_excel(INVALID_FILE_PATH, index=False)
        print(f"  > Saved {len(invalid_df)} invalid rows to: {INVALID_FILE_PATH}")
        
        print("--- Cleaning Step Complete ---")
        return True
        
    except Exception as e:
        print(f"Error saving cleaned files: {e}")
        return False


def split_valid_codes_by_cui():
    """
    Reads the 'valid_codes.xlsx' file (after SICAP scraping).
    Splits it into two new files:
    1. 'valid_codes_with_cui.xlsx': A new file with rows that have a CUI.
    2. 'valid_codes_no_cui.xlsx': A new file with rows that DO NOT have a CUI.
    """
    print("--- Step 3: Splitting Valid Codes by CUI ---")
    
    # --- FIX 1: Check for the INPUT file (VALID_FILE_PATH) ---
    if not VALID_FILE_PATH.exists():
        print(f"Error: Input file not found at: {VALID_FILE_PATH}")
        print("Please ensure Step 1 (Cleaning) and Step 2 (Scraping) ran successfully.")
        return False

    try:
        # --- FIX 2: Read from the INPUT file (VALID_FILE_PATH) ---
        df = pd.read_excel(VALID_FILE_PATH, header=0)
        print(f"Successfully loaded {VALID_FILE_PATH.name}")
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return False

    # 2. Check for the 'Ofertant CUI' column
    if 'Ofertant CUI' not in df.columns:
         # --- FIX 3: Refer to the correct file in the error message ---
        print(f"Error: Column 'Ofertant CUI' not found in {VALID_FILE_PATH}.")
        print("This column should have been created during the scraping step.")
        return False
        
    # 3. Create boolean masks for splitting
    # pd.isna() correctly handles both None and np.nan
    mask_no_cui = df['Ofertant CUI'].isna()
    mask_with_cui = df['Ofertant CUI'].notna()

    df_no_cui = df[mask_no_cui].copy()
    df_with_cui = df[mask_with_cui].copy()

    # 4. Save the two new files
    try:
        # --- FIX 4: Save to the correct OUTPUT file (VALID_CODES_WITH_CUI_PATH) ---
        df_with_cui.to_excel(VALID_CODES_WITH_CUI_PATH, index=False)
        print(f"  > Saved {len(df_with_cui)} rows WITH CUI to: {VALID_CODES_WITH_CUI_PATH}")
        
        # Save the file WITH NO CUI (to the new path)
        df_no_cui.to_excel(VALID_CODES_NO_CUI_PATH, index=False)
        print(f"  > Saved {len(df_no_cui)} rows WITH NO CUI to: {VALID_CODES_NO_CUI_PATH}")
        
        print("--- CUI Splitting Step Complete ---")
        return True
        
    except Exception as e:
        print(f"Error saving split files: {e}")
        return False