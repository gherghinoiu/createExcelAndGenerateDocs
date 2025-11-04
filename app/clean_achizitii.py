import pandas as pd
import re
import os

# Option 1: Look for the file in the same directory as the script
file = 'export_achizitii_2025-10-20T12_03_21.815970182_2012.xlsx'

# Option 2: If the file is elsewhere, uncomment and update this line with the full path
# file = r'D:\Daniel GHERGHINOIU\1.Date User\Documents\YOUR_ACTUAL_FOLDER\export_achizitii_2025-10-20T12_03_21.815970182_2012.xlsx'

# Check if file exists
if not os.path.exists(file):
    print(f"Error: File not found at: {file}")
    print(f"Current working directory: {os.getcwd()}")
    print("Please place the Excel file in the same folder as this script,")
    print("or update the 'file' variable with the full path to your Excel file.")
    exit()

df = pd.read_excel(file, header=0)

# Target column C (index 2)
col_c = df.columns[2]

# Pattern: DA, DAN, CN, SCN, or ADV followed by digits
# This pattern will extract the valid code from anywhere in the text
pattern = re.compile(r'(DA|DAN|CN|SCN|ADV)\d+')

def extract_valid_code(value):
    """
    Extract valid SICAP code from a string.
    Returns the cleaned code if found, otherwise None.
    """
    if pd.isna(value):
        return None
    
    # Convert to string and remove all spaces
    clean_value = str(value).replace(' ', '')
    
    # Try to find a valid pattern
    match = pattern.search(clean_value)
    if match:
        return match.group(0)  # Return the matched valid code
    return None

# Apply extraction to column C
df['extracted_code'] = df[col_c].apply(extract_valid_code)

# Separate valid (where we found a code) and invalid (no code found)
valid_df = df[df['extracted_code'].notna()].copy()
invalid_df = df[df['extracted_code'].isna()].copy()

# Update column C in valid_df with the cleaned extracted code
valid_df[col_c] = valid_df['extracted_code']

# Drop the temporary extraction column from both dataframes
valid_df = valid_df.drop(columns=['extracted_code'])
invalid_df = invalid_df.drop(columns=['extracted_code'])

# Save results
valid_df.to_excel('valid_codes.xlsx', index=False)
invalid_df.to_excel('invalid_codes.xlsx', index=False)

print(f"Processing complete!")
print(f"Valid entries (cleaned): {len(valid_df)}")
print(f"Invalid entries (no valid code found): {len(invalid_df)}")
