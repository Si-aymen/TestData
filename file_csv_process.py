import os
import pandas as pd
import shutil
import logging
import re
from mapping import extract_headers_and_types, extract_mandatory_columns, org_flux_sheets

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define directories
DATA_DIRS = ["data/M_FILES", "data/Q_FILES"]
REPORT_DIR = "data/Mandatory_columns_failure"
os.makedirs(REPORT_DIR, exist_ok=True)
report_file_path = os.path.join(REPORT_DIR, "failure_report.txt")

# Load the Excel file
excel_path = "Cahier des charges - Reporting Flux Standard - V25.1.0 1.xlsx"
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
        error_message = f"{file_path} : Erreur lors de la lecture -> {e}"
        logging.error(error_message)
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
        error_message = f"{file_path} : Colonnes manquantes pour {flux_name} -> {missing_columns}"
        logging.error(error_message)
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
                # Ignore null values and check if the value is numeric
                if not all(actual_values.isnull() | actual_values.str.isnumeric()):
                    type_check_failed.append(f"{header} : Attendu 'Numérique', trouvé des valeurs non numériques.")
            elif expected_type == "Number":
                # Ignore null values and check if the value is numeric
                alphanumeric_pattern = re.compile(r'^[\w\W]+$')  # Matches letters, numbers, and symbols
                if not all(actual_values.str.match(alphanumeric_pattern)):
                    type_check_failed.append(f"{header} : Attendu 'Alphanumérique', trouvé des valeurs non alphanumériques.")
            elif expected_type == "Alphanumérique":
                # Adjusting the check for Alphanumérique to allow numbers, letters, and symbols
                alphanumeric_pattern = re.compile(r'^[\w\W]+$')  # Matches letters, numbers, and symbols
                if not all(actual_values.str.match(alphanumeric_pattern)):
                    type_check_failed.append(f"{header} : Attendu 'Alphanumérique', trouvé des valeurs non alphanumériques.")
            elif expected_type == "Alpha Numérique":
                # Adjusting the check for Alphanumérique to allow numbers, letters, and symbols
                alphanumeric_pattern = re.compile(r'^[\w\W]+$')  # Matches letters, numbers, and symbols
                if not all(actual_values.str.match(alphanumeric_pattern)):
                    type_check_failed.append(f"{header} : Attendu 'Alphanumérique', trouvé des valeurs non alphanumériques.")
            elif expected_type == "Date aaaammjj":
                try:
                    pd.to_datetime(actual_values, format='%Y%m%d', errors='raise')
                except Exception:
                    type_check_failed.append(f"{header} : Attendu 'Date aaaammjj', format incorrect pour certaines valeurs.")
    
    # Combine checks
    if length_check_failed or type_check_failed:
        error_message = f"{file_path} : Erreurs -> Longueur: {', '.join(length_check_failed)}, Type: {', '.join(type_check_failed)}"
        logging.error(error_message)
        failed_files.append((file_path, error_message))
        shutil.move(file_path, os.path.join(REPORT_DIR, os.path.basename(file_path)))  # 🚨 Déplacement si échec

        # Add failure details to the failure report
        with open(report_file_path, "a", encoding="utf-8") as report_file:
            report_file.write(f"❌ {file_path}\n")
            report_file.write(f"Raison : Longueur -> {', '.join(length_check_failed)}\n")
            report_file.write(f"Raison : Type -> {', '.join(type_check_failed)}\n\n")
        
    else:
        logging.info("%s \n🆗 : Toutes les colonnes obligatoires, leurs longueurs et types sont corrects pour %s", file_path, flux_name)

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
