from flask import Flask, request, jsonify
import os
import re
import shutil
import json
import pandas as pd
from datetime import datetime
from mapping import extract_flux_sheet_names, flux_mapping, renamed_flux_sheets, extract_headers_and_types, extract_mandatory_columns, org_flux_sheets
from Notice_ext import load_naming_constraints
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define directories
TEST_DIR = "data"
Q_DIR = os.path.join(TEST_DIR, "Q_FILES")
M_DIR = os.path.join(TEST_DIR, "M_FILES")
DATA_DIRS = ["data/M_FILES", "data/Q_FILES"]
NO_MATCH_DIR = os.path.join(TEST_DIR, "NO_MATCH")
RESULTS_FILE = os.path.join(NO_MATCH_DIR, "file_test_results.json")
REPORT_DIR = "data/Mandatory_columns_failure"
json_report_path = os.path.join(REPORT_DIR, "test_results.json")
report_file_path = os.path.join(REPORT_DIR, "failure_report.txt")
file_path = "Cahier des charges - Reporting Flux Standard - V25.1.0.xlsx"

# Create directories if they don't exist
os.makedirs(Q_DIR, exist_ok=True)
os.makedirs(M_DIR, exist_ok=True)
os.makedirs(NO_MATCH_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# Load naming constraints and extract flux sheet names
Notice_constraints = load_naming_constraints(file_path)
Notice_name = set(Notice_constraints.values()) if isinstance(Notice_constraints, dict) else set(Notice_constraints)

sheets = pd.read_excel(file_path, sheet_name=None)
flux_sheets = extract_flux_sheet_names(sheets)
renamed_flux_sheets = {flux_mapping.get(flux, flux) for flux in flux_sheets}

# Regular expression for filename pattern
FILENAME_PATTERN = re.compile(
    r'(?:(?:ENT-(?:[1-9]|[1-9][0-9]|100))_)?'  # Optional ENT-1 to ENT-100
    r'(?:MOD1_)?'  # Optional MOD1_ prefix
    r'OCIANE_RC2_\d+_'  # Required OCIANE_RC2_X_
    r'([A-Z_]+(?:_[A-Z_]+)*)'  # Flux name
    r'_(Q|M)(?:_F)?'  # Period (_Q or _M) + optional _F
    r'_(\d{8}(?:\d{8})?)(?:_(\d{8}))*'  # Dates (YYYYMMDD, YYYYMMDDYYYYMMDD, or multiple)
    r'\.csv$'  # Must end with .csv
)

def get_ent_number(filename):
    match = re.match(r'^ENT-(\d+)', filename)
    return match.group(1) if match else None

def get_ent_directory(base_dir, filename):
    ent_number = get_ent_number(filename)
    return os.path.join(base_dir, f"ENT{ent_number}") if ent_number else os.path.join(base_dir, "NO_ENT")

def extract_latest_date(dates_str):
    dates = re.findall(r'\d{8}', dates_str)
    dates = [datetime.strptime(date, "%Y%m%d") for date in dates]
    return max(dates).strftime("%Y%m%d") if dates else None

def find_failed_part(filename):
    """Identifies the part of the filename that does not match the regex."""
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

@app.route('/classify_files', methods=['POST'])
def classify_files():
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
        latest_date = extract_latest_date("_".join(all_dates))
    
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

    return jsonify({"message": f"Results saved in {RESULTS_FILE}", "results": results})

@app.route('/check_mandatory_columns', methods=['POST'])
def check_mandatory_columns_endpoint():
    failed_files = []

    # Load the Excel file
    excel_path = "Cahier des charges - Reporting Flux Standard - V25.1.0.xlsx"
    while not os.path.exists(excel_path):
        excel_path = input("❌ Fichier introuvable. Veuillez entrer le chemin complet vers le fichier Excel : ")

    try:
        cahier_des_charges = pd.read_excel(excel_path, sheet_name=None)
    except Exception as e:
        logging.error("Erreur lors de la lecture du fichier Excel : %s", e)
        return jsonify({"error": "Failed to read Excel file"}), 500

    # Extract mandatory columns
    mandatory_columns_by_flux = {}
    for sheet_name, df in cahier_des_charges.items():
        sheet_name_clean = sheet_name.strip().upper()
        mandatory_columns = extract_mandatory_columns(df)
        if mandatory_columns:
            mandatory_columns_by_flux[sheet_name_clean] = mandatory_columns
        else:
            logging.warning("⚠️ Feuille ignorée : Moins de 4 colonnes détectées dans %s.", sheet_name_clean)

    # Process files
    for data_dir in DATA_DIRS:
        if not os.path.exists(data_dir):
            logging.warning("Le dossier %s n'existe pas.", data_dir)
            continue
        
        for ent_folder in os.listdir(data_dir):
            ent_path = os.path.join(data_dir, ent_folder)
            if not os.path.isdir(ent_path):
                continue

            for filename in os.listdir(ent_path):
                if filename.endswith(".csv"):
                    file_path = os.path.join(ent_path, filename)
                    flux_name = next((flux for flux in org_flux_sheets if flux in filename.upper()), filename.upper())
                    logging.info(f"📂 flux_name utilisé : {flux_name}")
                    check_mandatory_columns(file_path, flux_name, mandatory_columns_by_flux, cahier_des_charges, failed_files)

    # Generate report
    if failed_files:
        with open(report_file_path, "w", encoding="utf-8") as report_file:
            for file_path, reason in failed_files:
                report_file.write(f"❌ {file_path}\nRaison : {reason}\n\n")
        logging.info("Rapport généré : %s", report_file_path)
    else:
        logging.info("\n🆗 Tous les fichiers ont passé les tests.")
        shutil.rmtree(REPORT_DIR, ignore_errors=True)

    # Generate JSON report for dashboard
    generate_test_results(failed_files, json_report_path)

    return jsonify({"message": "Mandatory columns check completed", "failed_files": failed_files})

def check_mandatory_columns(file_path, flux_name, mandatory_columns_by_flux, cahier_des_charges, failed_files):
    logging.info("🔍 Traitement du fichier : %s", file_path)
    try:
        df = pd.read_csv(file_path, sep=";", encoding="utf-8", low_memory=False)
        df.columns = df.columns.str.strip()
    except Exception as e:
        error_message = f"Erreur lors de la lecture -> {e}"
        logging.error(f"{file_path} : {error_message}")
        failed_files.append((file_path, error_message))
        shutil.move(file_path, os.path.join(REPORT_DIR, os.path.basename(file_path)))
        return  

    if len(df) == 1:
        logging.info("%s : Le fichier contient une seule ligne et est considéré comme valide.", file_path)
        return

    if flux_name not in mandatory_columns_by_flux:
        logging.warning("⚠️ Flux inconnu dans le cahier des charges : %s", flux_name)
        return

    mandatory_columns = mandatory_columns_by_flux.get(flux_name, [])
    missing_columns = [col for col in mandatory_columns if col not in df.columns]
    
    if missing_columns:
        error_message = f"Colonnes manquantes pour {flux_name} -> {missing_columns}"
        logging.error(f"{file_path} : {error_message}")
        failed_files.append((file_path, error_message))
        shutil.move(file_path, os.path.join(REPORT_DIR, os.path.basename(file_path)))
        return

    headers_types = extract_headers_and_types(cahier_des_charges[flux_name])
    length_check_failed = []
    type_check_failed = []

    for header, expected_type, expected_length in headers_types:
        if header in df.columns:
            actual_values = df[header].astype(str)

            # Check length
            if pd.notna(expected_length) and isinstance(expected_length, (int, float)):
                expected_length = int(expected_length)
                max_allowed_length = 10 if expected_length == 8 else expected_length
                if any(actual_values.str.len() > max_allowed_length):
                    length_check_failed.append(f"{header} (Attendu max: {max_allowed_length}, Trouvé: {actual_values.str.len().max()})")

            # Check type
            if expected_type == "Numérique":
                df[header] = df[header].astype(str).str.strip()
                df[header] = df[header].replace(['nan', 'NaN', 'None', '-', 'NULL'], pd.NA)
                df[header] = df[header].fillna(0)
                df[header] = df[header].str.replace(',', '.', regex=False)
                df[header] = pd.to_numeric(df[header], errors='coerce')

                if df[header].isna().any():
                    invalid_numbers = df[df[header].isna()][header].unique()
                    type_check_failed.append(f"{header} : Attendu 'Numérique', trouvé des valeurs non numériques. Valeurs problématiques: {invalid_numbers}")

        if length_check_failed or type_check_failed:
            error_message = f"Erreurs -> Longueur: {', '.join(length_check_failed)}, Type: {', '.join(type_check_failed)}"
            logging.error(f"{file_path} : {error_message}")
            failed_files.append((file_path, error_message))
            shutil.move(file_path, os.path.join(REPORT_DIR, os.path.basename(file_path)))

            with open(report_file_path, "a", encoding="utf-8") as report_file:
                report_file.write(f"❌ {file_path}\n")
                report_file.write(f"Raison : Longueur -> {', '.join(length_check_failed)}\n")
                report_file.write(f"Raison : Type -> {', '.join(type_check_failed)}\n\n")
            
        else:
            logging.info("%s \n🆗 : Toutes les colonnes obligatoires, leurs longueurs et types sont corrects pour %s", file_path, flux_name)

def generate_test_results(failed_files, json_path):
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    
    test_results = []
    for file_path, reason in failed_files:
        result = {
            "file_path": file_path,
            "status": "Failed",
            "reason": reason
        }
        test_results.append(result)
    
    for data_dir in DATA_DIRS:
        if os.path.exists(data_dir):
            for ent_folder in os.listdir(data_dir):
                ent_path = os.path.join(data_dir, ent_folder)
                if os.path.isdir(ent_path):
                    for filename in os.listdir(ent_path):
                        if filename.endswith(".csv"):
                            file_path = os.path.join(ent_path, filename)
                            if file_path not in [f[0] for f in failed_files]:
                                test_results.append({
                                    "file_path": file_path,
                                    "status": "Passed",
                                    "reason": None
                                })
    
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(test_results, json_file, indent=4, ensure_ascii=False)
    logging.info("Rapport JSON généré : %s", json_path)

if __name__ == '__main__':
    app.run(debug=True)