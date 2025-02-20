import os
import re
import shutil
import json
import pandas as pd
from datetime import datetime
from mapping import extract_flux_sheet_names, flux_mapping, renamed_flux_sheets
from Notice_ext import load_naming_constraints

# Correction de la regex
FILENAME_PATTERN = re.compile(
    r'(?:(?:ENT-(?:[1-9]|[1-9][0-9]|100))_)?'  # Optional ENT-1 to ENT-100
    r'(?:MOD1_)?'  # Optional MOD1_ prefix
    r'OCIANE_RC2_\d+_'  # Required OCIANE_RC2_X_
    r'([A-Z_]+(?:_[A-Z_]+)*)'  # Flux name
    r'_(Q|M)(?:_F)?'  # Period (_Q or _M) + optional _F
    r'_(\d{8}(?:\d{8})?)(?:_(\d{8}))*'  # Dates (YYYYMMDD, YYYYMMDDYYYYMMDD, or multiple)
    r'\.csv$'  # Must end with .csv
)

TEST_DIR = "data"
Q_DIR = os.path.join(TEST_DIR, "Q_FILES")
M_DIR = os.path.join(TEST_DIR, "M_FILES")
NO_MATCH_DIR = os.path.join(TEST_DIR, "NO_MATCH")
RESULTS_FILE = os.path.join(NO_MATCH_DIR, "file_test_results.json")
file_path = "Cahier des charges - Reporting Flux Standard - V25.1.0 2.xlsx"

os.makedirs(Q_DIR, exist_ok=True)
os.makedirs(M_DIR, exist_ok=True)
os.makedirs(NO_MATCH_DIR, exist_ok=True)

sheets = pd.read_excel(file_path, sheet_name=None)
flux_sheets = extract_flux_sheet_names(sheets)  
renamed_flux_sheets = {flux_mapping.get(flux, flux) for flux in flux_sheets}
Notice_constraints = load_naming_constraints(file_path)
Notice_name = set(Notice_constraints.values()) if isinstance(Notice_constraints, dict) else set(Notice_constraints)

def get_ent_number(filename):
    match = re.match(r'^ENT-(\d+)', filename)
    return match.group(1) if match else None

def get_ent_directory(base_dir, filename):
    ent_number = get_ent_number(filename)
    return os.path.join(base_dir, f"ENT{ent_number}") if ent_number else os.path.join(base_dir, "NO_ENT")

def extract_latest_date(dates_str):
    """Extrait la dernière date dans une chaîne qui peut contenir YYYYMMDD ou YYYYMMDDYYYYMMDD."""
    dates = re.findall(r'\d{8}', dates_str)  # Trouver toutes les dates (YYYYMMDD)
    dates = [datetime.strptime(date, "%Y%m%d") for date in dates]  # Conversion en datetime
    return max(dates).strftime("%Y%m%d") if dates else None  # Récupérer la plus récente

def find_failed_part(filename):
    """Identifie la partie du nom de fichier qui ne correspond pas à la regex."""
    segments = [
        (r'^(?:(?:ENT-(?:[1-9]|[1-9][0-9]|100))_)?', "ENT number (optional)"),
        (r'(?:MOD1_)?', "MOD1 prefix (optional)"),
        (r'OCIANE_RC2_\d+_', "OCIANE_RC2 with number"),
        (r'([A-Z_]+(?:_[A-Z_]+)*)', "Flux name"),
        (r'_(Q|M)(?:_F)?', "Period (_Q or _M)"),
        (r'_(\d{8}(?:\d{8})?)', "First date (YYYYMMDD or YYYYMMDDYYYYMMDD)"),
        (r'(?:_(\d{8}))*', "Additional dates (_YYYYMMDD, optional)"),
        (r'\.csv$', "File extension .csv")
    ]

    for part, desc in segments:
        if not re.search(part, filename):  
            return desc
    
    return "Unknown error"

expected_date = None
results = []

for filename in os.listdir(TEST_DIR):
    file_path = os.path.join(TEST_DIR, filename)
    if not os.path.isfile(file_path):
        continue
    
    result = {"filename": filename, "status": "", "reason": "", "failed_part": ""}
    match = FILENAME_PATTERN.match(filename)
    
    if not match:
        result["failed_part"] = find_failed_part(filename)
        shutil.move(file_path, os.path.join(NO_MATCH_DIR, filename))
        result["status"] = "Failed"
        result["reason"] = "Filename does not match the pattern."
        results.append(result)
        continue
    
    flux_name, period, first_date, *additional_dates = match.groups()
    flux_name = flux_name.strip()
    all_dates = [first_date] + [d for d in additional_dates if d]
    latest_date = extract_latest_date("_".join(all_dates))  # Extraction correcte de la dernière date
    
    if flux_name not in renamed_flux_sheets or flux_name not in Notice_name:
        shutil.move(file_path, os.path.join(NO_MATCH_DIR, filename))
        result["status"] = "Failed"
        result["reason"] = f"Unknown flux '{flux_name}'."
        results.append(result)
        continue
    
    if expected_date is None:
        expected_date = latest_date
    elif latest_date != expected_date:
        shutil.move(file_path, os.path.join(NO_MATCH_DIR, filename))
        result["status"] = "Failed"
        result["reason"] = f"Different date '{latest_date}', expected '{expected_date}'."
        results.append(result)
        continue
    
    dest_dir = get_ent_directory(Q_DIR if period == "Q" else M_DIR, filename)
    os.makedirs(dest_dir, exist_ok=True)
    shutil.move(file_path, os.path.join(dest_dir, filename))
    
    result["status"] = "Passed"
    result["reason"] = "File successfully classified."
    results.append(result)

with open(RESULTS_FILE, "w") as json_file:
    json.dump(results, json_file, indent=4)

print(f"✅ Results saved in {RESULTS_FILE}")
