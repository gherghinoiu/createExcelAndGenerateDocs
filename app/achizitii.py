import pandas as pd
from pathlib import Path
import re 
import os 
# --- NEW IMPORTS FOR STEP 4 ---
from docxtpl import DocxTemplate, RichText
from docx.shared import Pt # Not strictly needed, but good to know for styling

# --- Configuration ---
BASE_DIR = Path(__file__).parent.parent 
DATA_FILE = BASE_DIR / "achizitii test.xlsx"
TEMPLATE_1_FILE = BASE_DIR / "template1.docx"
TEMPLATE_2_FILE = BASE_DIR / "template2.docx"
PROCESSED_DIR = BASE_DIR / "processed"
FAILED_FILE = PROCESSED_DIR / "failed_rows.xlsx"
NR_ANUNT_SICAP_HEADER = 'Nr. anunt SICAP'
#DEFAULT_PLACEHOLDER_TEXT = "[NO DATA AVAILABLE]"

# --- IMPORTANT: FILL IN THIS MAP ---
# This is where you map your template placeholders
# to your Excel column headers.
#
# 'placeholder_in_word_doc': 'Excel_Header_Name'
#
# Based on your CSV, your headers are:
# 'Nr. crt', 'Apel', 'Nr. anunt SICAP', 'Tip procedură', 
# 'Număr contract', 'Data semnării contractului', etc.
#
PLACEHOLDER_MAP = {
    'nr_crt': 'Nr. crt',
    'apel': 'Apel',
    'nr_anunt_sicap': 'Nr. anunt SICAP',
    'tip_procedura': 'Tip procedură',
    'numar_contract': 'Număr contract',
    'data_semnarii': 'Data semnării contractului',
    'valoare_contract': 'Valoare integrală contract',
    'acord_cadru': 'Acord cadru',
    'criteriu_atribuire': 'Criteriu atribuire',
    'lider_asociere': 'Lider asociere',
    'tert_sustinator': 'Terț susținător',
    'subcontractant': 'Subcontractant',
    'tip_achizitie': 'Tip achizitie',
    'stare_achizitie': 'Stare achiziție',
    'data_transmiterii': 'Data ultimei transmiteri',
    'nume_proiect': 'Nume proiect',
    'nume_aplicant': 'Nume aplicant',
    'cui_aplicant': 'CUI', # Am presupus că acesta este CUI-ul aplicantului
    'cui_autoritate': 'CUI autoritate contractantă',
    'nume_autoritate': 'Denumire autoritate contractantă',
    'sicap_url': 'sicap url',
}
# --- End Configuration ---


def validate_sicap_id(sicap_id):
    # (This function is the same as Step 3)
    if not isinstance(sicap_id, str):
        return False
    cleaned_id = re.sub(r'\s+', '', sicap_id)
    return 5 < len(cleaned_id) < 12

# --- NEW HELPER FUNCTION FOR STEP 5 ---
def get_unique_filepath(directory, filename):
    """
    Checks if a file exists. If so, appends a version number (_v1, _v2).
    
    Args:
        directory (Path): The folder to save the file in.
        filename (str): The desired base filename (e.g., "DA12345.docx").
        
    Returns:
        Path: A unique file path.
    """
    # Create the full path: directory / filename
    # .stem gets the name without extension ("DA12345")
    # .suffix gets the extension (".docx")
    base_name = Path(filename).stem
    extension = Path(filename).suffix
    
    full_path = directory / filename
    version = 1
    
    # Loop as long as the file already exists
    while full_path.exists():
        # Create a new versioned filename
        new_filename = f"{base_name}_v{version}{extension}"
        full_path = directory / new_filename
        version += 1
        
    return full_path

def load_and_filter_data():
    # (This function is the same as Step 3)
    print(f"--- Step 2: Loading and Filtering Data ---")
    PROCESSED_DIR.mkdir(exist_ok=True)
    try:
        df = pd.read_excel(DATA_FILE, engine='openpyxl')
    except FileNotFoundError:
        print(f"Error: Data file not found at {DATA_FILE}")
        return None, None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None
    
    if NR_ANUNT_SICAP_HEADER not in df.columns:
        print(f"Error: Column '{NR_ANUNT_SICAP_HEADER}' not found.")
        return None, None

    is_valid_filter = df[NR_ANUNT_SICAP_HEADER].fillna('').apply(validate_sicap_id)
    valid_rows_df = df[is_valid_filter]
    invalid_rows_df = df[~is_valid_filter]

    print(f"Data processing complete:")
    print(f"  > Found {len(valid_rows_df)} valid rows.")
    print(f"  > Found {len(invalid_rows_df)} invalid rows.")
    print("-----------------------------------------------")
    
    valid_rows_list = valid_rows_df.to_dict('records')
    return valid_rows_list, invalid_rows_df


def save_invalid_rows(invalid_rows_df):
    # (This function is the same as Step 3)
    print(f"--- Step 3: Saving Invalid Rows ---")
    if invalid_rows_df is None or invalid_rows_df.empty:
        print("No invalid rows to save.")
        print("-----------------------------------------------")
        return

    try:
        invalid_rows_df.to_excel(FAILED_FILE, index=False, engine='openpyxl')
        print(f"Successfully saved {len(invalid_rows_df)} invalid rows to: {FAILED_FILE}")
    except Exception as e:
        print(f"Error: Could not save invalid rows file: {e}")
    print("-----------------------------------------------")


# --- 1. DEDICATED LOGIC FUNCTION (With BOTH custom placeholders) ---
def add_custom_placeholders(data_row, context, doc):
    """
    Takes the raw data row and the existing context,
    calculates all custom logic, and adds it to the context.
    """
    # --- Logic for 'seap_url' (FIXED - Using RichText) ---
    placeholder_name = 'sicap_url'
    default_text = f"[NO DATA AVAILABLE - {placeholder_name}]"
    url_string = data_row.get('url')
    
    if pd.notna(url_string) and str(url_string).strip():
        rt = RichText()
        rt.add(str(url_string), url_id=doc.build_url_id(str(url_string)))
        context[placeholder_name] = rt
    else:
        rt = RichText(default_text)
        context[placeholder_name] = rt
        
    # --- Logic for 'articol_de_lege' ---
    placeholder_name = 'articol_de_lege'
    articol_text = f"[NO DATA AVAILABLE - {placeholder_name}]"
    try:
        raw_value = context.get('valoare_contract')
        if isinstance(raw_value, str) and raw_value.startswith("[NO DATA"):
            pass 
        else:
            valoare = float(raw_value)
            if valoare < 8000:
                articol_text = 'litera d'
            elif 8000 <= valoare <= 14000:
                articol_text = 'litera c'
            else:
                articol_text = '[VALOARE PESTE PLAFON]'
    except (ValueError, TypeError, AttributeError):
        pass 
    context[placeholder_name] = articol_text
    
    
    # --- NEW LOGIC: 'valoare_contract_fara_tva' ---
    placeholder_name = 'valoare_contract_fara_tva'
    default_text = f"[NO DATA AVAILABLE - {placeholder_name}]"
    
    try:
        # Get the source value from the context
        raw_value = context.get('valoare_contract')
        
        # Check if the source value itself is missing
        if isinstance(raw_value, str) and raw_value.startswith("[NO DATA"):
            context[placeholder_name] = default_text
        else:
            # If we have a real value, run the logic
            valoare = float(raw_value)
            
            # --- !! CHANGE 1.19 IF YOUR VAT IS DIFFERENT !! ---
            valoare_fara_tva = valoare / 1.19 
            
            # Format it as a string with 2 decimal places
            context[placeholder_name] = f"{valoare_fara_tva:.2f}"
            
    except (ValueError, TypeError, AttributeError):
        # Catches any conversion errors
        context[placeholder_name] = default_text
    
    
    # --- Add your NEXT custom placeholder logic here ---
    # placeholder_name = 'un_alt_exemplu'
    # ...
        
    return context # Return the *updated* context


# --- 2. YOUR CLEANER, REVISED GENERATION FUNCTION (REVISED) ---
def generate_doc_from_template(data_row, template_path, output_path):
    """
    Generates a .docx file from a template and a single row of data.
    (This version adds dynamic [NO DATA AVAILABLE - placeholder] text)
    """
    try:
        # 1. Load the template
        doc = DocxTemplate(template_path)
        
        # 2. Create the base context dictionary
        context = {}
        for placeholder, header in PLACEHOLDER_MAP.items():
            value = data_row.get(header)
            
            if pd.isna(value) or value is None or str(value).strip() == "":
                # CHANGE 1: Add dynamic default text here
                context[placeholder] = f"[NO DATA AVAILABLE - {placeholder}]"
            else:
                context[placeholder] = value
        
        # 3. Call our function to add all custom logic
        context = add_custom_placeholders(data_row, context, doc)
        
        # 4. Find ALL placeholders in the template
        all_template_vars = doc.get_undeclared_template_variables()
        
        for var in all_template_vars:
            if var not in context:
                # CHANGE 2: Add dynamic default text here
                context[var] = f"[NO DATA AVAILABLE - {var}]"
        
        # 5. Render the document with the *complete* context
        doc.render(context)
        
        # 6. Save the new document
        doc.save(output_path)
        
        return True
        
    except FileNotFoundError:
        print(f"  > ERROR: Template file not found at {template_path}")
        return False
    except KeyError as e:
        print(f"  > ERROR: A placeholder in your template is missing from PLACEHOLDER_MAP.")
        print(f"    Check for: {e}")
        return False
    except Exception as e:
        print(f"  > ERROR: Could not generate document {output_path}: {e}")
        return False


# --- FINAL VERSION OF THE MAIN EXECUTION BLOCK (STEP 5) ---
if __name__ == "__main__":
    
    print("--- SCRIPT START ---")
    
    # Step 2: Load and filter base data
    valid_rows_list, invalid_rows_df = load_and_filter_data()
    
    # Step 3: Save invalid rows
    save_invalid_rows(invalid_rows_df)
    
    # --- NEW STEP: Load and Merge Scraper URLs ---
    scraper_results_file = PROCESSED_DIR / "valid_sicap_links.xlsx"
    if scraper_results_file.exists() and valid_rows_list:
        print(f"Loading scraper results from {scraper_results_file}...")
        try:
            # Load both lists into DataFrames for easy merging
            valid_df = pd.DataFrame(valid_rows_list)
            urls_df = pd.read_excel(scraper_results_file)
            
            # Clean keys for merging (removes spaces)
            valid_df['sicap_id_clean'] = valid_df[NR_ANUNT_SICAP_HEADER].astype(str).str.replace(r'\s+', '', regex=True)
            urls_df['sicap_id_clean'] = urls_df['sicap_id'].astype(str).str.replace(r'\s+', '', regex=True)
            
            # Merge URLs into the valid_df
            valid_df = pd.merge(
                valid_df,
                urls_df[['sicap_id_clean', 'url']],  # Get the 'url' column
                on='sicap_id_clean',
                how='left'  # Keep all rows from valid_df
            )
            
            # Clean up and convert back to list of dicts
            valid_df = valid_df.drop(columns=['sicap_id_clean'])
            valid_rows_list = valid_df.to_dict('records') # Overwrite the list with new merged data
            print("Successfully merged scraper URLs.")
            
        except Exception as e:
            print(f"  > WARNING: Could not load or merge scraper URLs: {e}")
            print("    'seap_url' will be unavailable.")
    else:
        if valid_rows_list:
             print(f"  > WARNING: Scraper file not found: {scraper_results_file}")
             print("    Run 'python -m app.run_scraper' first. 'seap_url' will be unavailable.")
    # --- END OF NEW STEP ---

    if valid_rows_list:
        print(f"\n--- Step 4 & 5: Processing {len(valid_rows_list)} Valid Row(s) ---")
        
        success_count = 0
        fail_count = 0
        
        # Loop through every valid row
        for index, row in enumerate(valid_rows_list):
            
            # 1. Get the base filename
            base_filename_raw = row.get(NR_ANUNT_SICAP_HEADER)
            base_filename = re.sub(r'[^\w\.-]', '', str(base_filename_raw).strip())
            
            print(f"Processing row {index + 1}/{len(valid_rows_list)}: {base_filename}")
            
            # --- 2. Process Template 1 ---
            try:
                output_name_1 = f"{base_filename}.docx"
                unique_path_1 = get_unique_filepath(PROCESSED_DIR, output_name_1)
                
                print(f"  > Generating {unique_path_1.name}...")
                success1 = generate_doc_from_template(row, TEMPLATE_1_FILE, unique_path_1)
                
                if success1: success_count += 1
                else: fail_count += 1
                    
            except Exception as e:
                print(f"  > UNEXPECTED ERROR for template 1: {e}")
                fail_count += 1
                
            # --- 3. Process Template 2 ---
            try:
                output_name_2 = f"{base_filename}_T2.docx"
                unique_path_2 = get_unique_filepath(PROCESSED_DIR, output_name_2)
                
                print(f"  > Generating {unique_path_2.name}...")
                success2 = generate_doc_from_template(row, TEMPLATE_2_FILE, unique_path_2)
                
                if success2: success_count += 1
                else: fail_count += 1
                    
            except Exception as e:
                print(f"  > UNEXPECTED ERROR for template 2: {e}")
                fail_count += 1

        print("-----------------------------------------------")
        print(f"--- SCRIPT COMPLETE ---")
        print(f"Successfully generated: {success_count} documents.")
        print(f"Failed to generate:   {fail_count} documents.")
        
    else:
        print("\nNo valid rows found to process.")
        print("--- SCRIPT COMPLETE ---")