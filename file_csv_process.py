import os
import pandas as pd
import shutil
import logging
import re
import json
from mapping import extract_headers_and_types, extract_mandatory_columns, org_flux_sheets

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define directories
DATA_DIRS = ["data/M_FILES", "data/Q_FILES"]
REPORT_DIR = "data/Mandatory_columns_failure"
os.makedirs(REPORT_DIR, exist_ok=True)
report_file_path = os.path.join(REPORT_DIR, "failure_report.txt")
json_report_path = os.path.join(REPORT_DIR, "test_results.json")  # Path for JSON report

# Load the Excel file
excel_path = "Cahier des charges - Reporting Flux Standard - V25.1.0 2.xlsx"
while not os.path.exists(excel_path):
    excel_path = input("❌ Fichier introuvable. Veuillez entrer le chemin complet vers le fichier Excel : ")

try:
    cahier_des_charges = pd.read_excel(excel_path, sheet_name=None)
except Exception as e:
    logging.error("Erreur lors de la lecture du fichier Excel : %s", e)
    exit(1)

# Extraction des colonnes obligatoires
mandatory_columns_by_flux = {}
for sheet_name, df in cahier_des_charges.items():
    sheet_name_clean = sheet_name.strip().upper()
    mandatory_columns = extract_mandatory_columns(df)
    if mandatory_columns:
        mandatory_columns_by_flux[sheet_name_clean] = mandatory_columns
    else:
        logging.warning("⚠️ Feuille ignorée : Moins de 4 colonnes détectées dans %s.", sheet_name_clean)

# Vérification des colonnes obligatoires
def check_mandatory_columns(file_path, flux_name, failed_files):
    logging.info("🔍 Traitement du fichier : %s", file_path)
    try:
        df = pd.read_csv(file_path, sep=";", encoding="utf-8", low_memory=False)
        df.columns = df.columns.str.strip()
    except Exception as e:
        error_message = f"Erreur lors de la lecture -> {e}"  # Remove file name from reason
        logging.error(f"{file_path} : {error_message}")
        failed_files.append((file_path, error_message))
        shutil.move(file_path, os.path.join(REPORT_DIR, os.path.basename(file_path)))  # 🚨 Déplacement si échec
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
        error_message = f"Colonnes manquantes pour {flux_name} -> {missing_columns}"  # Remove file name from reason
        logging.error(f"{file_path} : {error_message}")
        failed_files.append((file_path, error_message))
        shutil.move(file_path, os.path.join(REPORT_DIR, os.path.basename(file_path)))  # 🚨 Déplacement si échec
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
                if not all(actual_values.isnull() | actual_values.str.isnumeric()):
                    type_check_failed.append(f"{header} : Attendu 'Numérique', trouvé des valeurs non numériques.")
            elif expected_type in ["Alphanumérique", "Alpha Numérique"]:
                # Updated regex to allow spaces, commas, and percentage signs
                alphanumeric_pattern = re.compile(r'^[a-zA-Z0-9 ,%]+$')  # Allows letters, numbers, spaces, commas, and %
                if not all(actual_values.str.match(alphanumeric_pattern)):
                    type_check_failed.append(f"{header} : Attendu 'Alphanumérique', trouvé des valeurs non alphanumériques.")
            elif expected_type == "Date aaaammjj":
                try:
                    pd.to_datetime(actual_values, format='%Y%m%d', errors='raise')
                except Exception:
                    type_check_failed.append(f"{header} : Attendu 'Date aaaammjj', format incorrect pour certaines valeurs.")
    
    # Combine checks
    if length_check_failed or type_check_failed:
        error_message = f"Erreurs -> Longueur: {', '.join(length_check_failed)}, Type: {', '.join(type_check_failed)}"  # Remove file name from reason
        logging.error(f"{file_path} : {error_message}")
        failed_files.append((file_path, error_message))
        shutil.move(file_path, os.path.join(REPORT_DIR, os.path.basename(file_path)))  # 🚨 Déplacement si échec

        # Add failure details to the failure report
        with open(report_file_path, "a", encoding="utf-8") as report_file:
            report_file.write(f"❌ {file_path}\n")
            report_file.write(f"Raison : Longueur -> {', '.join(length_check_failed)}\n")
            report_file.write(f"Raison : Type -> {', '.join(type_check_failed)}\n\n")
        
    else:
        logging.info("%s \n🆗 : Toutes les colonnes obligatoires, leurs longueurs et types sont corrects pour %s", file_path, flux_name)

# Function to generate test results in JSON format
def generate_test_results(failed_files, json_path):
    # Ensure the REPORT_DIR directory exists
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    
    test_results = []
    for file_path, reason in failed_files:
        result = {
            "file_path": file_path,
            "status": "Failed",
            "reason": reason  # Reason no longer includes the file name
        }
        test_results.append(result)
    
    # Add passed files (optional, if you want to track all files)
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
    
    # Save results to JSON file
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(test_results, json_file, indent=4, ensure_ascii=False)
    logging.info("Rapport JSON généré : %s", json_path)

# Traitement des fichiers
failed_files = []
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

                # 🔍 Correction : Garder le fichier même sans correspondance
                flux_name = next((flux for flux in org_flux_sheets if flux in filename.upper()), filename.upper())

                logging.info(f"📂 flux_name utilisé : {flux_name}")

                check_mandatory_columns(file_path, flux_name, failed_files)

# Génération du rapport
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