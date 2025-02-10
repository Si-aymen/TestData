import os
import re
import shutil
import pandas as pd
from mapping import extract_flux_sheet_names, flux_mapping,renamed_flux_sheets

FILENAME_PATTERN = re.compile(
    r'(?:(?:ENT-(?:[1-9]|[1][0-9]|[2][0-9]|30))_)?'   # Optional ENT-<number>_
    r'(?:MOD1_)?'                                      # Optional MOD1 part
    r'OCIANE_RC2_\d+_([A-Z_]+(?:_[A-Z_]+)*)(?:_F)?'      # Flux name and optional '_F' suffix
    r'_(Q|M)'                                          # Ensure it contains _Q or _M
    r'(?:_\d{8}){1,4}'                                 # Match 1 to 4 date segments (8 digits each)
    r'\.csv$'                                          # Strictly enforce .csv extension at the end
)


# Directories
TEST_DIR = "data"
Q_DIR = os.path.join(TEST_DIR, "Q_FILES")  # Folder for _Q files
M_DIR = os.path.join(TEST_DIR, "M_FILES")  # Folder for _M files
NO_MATCH_DIR = os.path.join(TEST_DIR, "NO_MATCH")
file_path = "Cahier des charges - Reporting Flux Standard - V25.1.0 1.xlsx"


# Ensure necessary directories exist
os.makedirs(Q_DIR, exist_ok=True)
os.makedirs(M_DIR, exist_ok=True)
os.makedirs(NO_MATCH_DIR, exist_ok=True)

# Liste des noms de flux renommés
sheets = pd.read_excel(file_path, sheet_name=None)
flux_sheets = extract_flux_sheet_names(sheets)  
renamed_flux_sheets = {flux_mapping.get(flux, flux) for flux in flux_sheets}  # Utilisation d'un set pour recherche rapide

# Function to get the ENT number from a filename
def get_ent_number(filename):
    match = re.match(r'^ENT-(\d+)', filename)
    return match.group(1) if match else None

# Function to get the destination directory based on ENT number
def get_ent_directory(base_dir, filename):
    ent_number = get_ent_number(filename)
    return os.path.join(base_dir, f"ENT{ent_number}") if ent_number else os.path.join(base_dir, "NO_ENT")

# File classification logic
for filename in os.listdir(TEST_DIR):
    file_path = os.path.join(TEST_DIR, filename)

    # Skip directories, only process files
    if not os.path.isfile(file_path):
        continue

    # Step 1: Validate filename with regex pattern
    match = FILENAME_PATTERN.match(filename)
    if not match:
        shutil.move(file_path, os.path.join(NO_MATCH_DIR, filename))
        print(f"❌ Filename '{filename}' does not match the pattern and was moved to 'NO_MATCH' folder.")
        continue  # Skip invalid files

    # Step 2: Extract the flux name and check if it is in renamed_flux_sheets
    flux_name, period = match.groups()
    flux_name = flux_name.strip()  # Remove accidental spaces

    print(f"🔍 Extracted flux: {flux_name}, Period: {period}")
    #print("\n\n\nFlux name after change : ",renamed_flux_sheets)

    if flux_name not in renamed_flux_sheets:
        shutil.move(file_path, os.path.join(NO_MATCH_DIR, filename))
        print(f"❌ Filename '{filename}' contains unknown flux '{flux_name}' and was moved to 'NO_MATCH' folder.")
        continue

    # Step 3: Check if the filename contains "_Q" or "_M" and classify
    dest_dir = get_ent_directory(Q_DIR if period == "Q" else M_DIR, filename)
    os.makedirs(dest_dir, exist_ok=True)
    shutil.move(file_path, os.path.join(dest_dir, filename))
    print(f"✅ Filename '{filename}' was moved to '{dest_dir}' folder.")
