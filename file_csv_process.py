import os
import pandas as pd
import shutil
import logging
import re
import json
from mapping import extract_headers_and_types, extract_mandatory_columns, org_flux_sheets

# 🔹 Configuration des logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 🔹 Définition des dossiers
DATA_DIRS = ["data/M_FILES", "data/Q_FILES"]
REPORT_DIR = "data/Mandatory_columns_failure"
os.makedirs(REPORT_DIR, exist_ok=True)
report_file_path = os.path.join(REPORT_DIR, "failure_report.txt")
json_report_path = os.path.join(REPORT_DIR, "test_results.json")

# 🔹 Chargement du fichier Excel
excel_path = "Cahier des charges - Reporting Flux Standard - V25.1.0 2.xlsx"
while not os.path.exists(excel_path):
    excel_path = input("❌ Fichier introuvable. Veuillez entrer le chemin complet vers le fichier Excel : ")

try:
    cahier_des_charges = pd.read_excel(excel_path, sheet_name=None)
except Exception as e:
    logging.error("Erreur lors de la lecture du fichier Excel : %s", e)
    exit(1)

# 🔹 Extraction des colonnes obligatoires
mandatory_columns_by_flux = {
    sheet.strip().upper(): extract_mandatory_columns(df)
    for sheet, df in cahier_des_charges.items()
    if len(df.columns) >= 4
}

# 🔹 Fonction de validation
def check_mandatory_columns(file_path, flux_name, failed_files):
    logging.info("🔍 Vérification du fichier : %s", file_path)

    try:
        df = pd.read_csv(file_path, sep=";", encoding="utf-8", low_memory=False)
        df.columns = df.columns.str.strip()
    except Exception as e:
        log_and_move(file_path, f"Erreur de lecture -> {e}", failed_files)
        return  

    if len(df) == 1:
        logging.info("🆗 Fichier avec une seule ligne accepté : %s", file_path)
        return

    if flux_name not in mandatory_columns_by_flux:
        logging.warning("⚠️ Flux inconnu : %s", flux_name)
        return

    missing_columns = [col for col in mandatory_columns_by_flux[flux_name] if col not in df.columns]
    if missing_columns:
        log_and_move(file_path, f"Colonnes manquantes : {missing_columns}", failed_files)
        return

    headers_types = extract_headers_and_types(cahier_des_charges[flux_name])
    length_check_failed, type_check_failed = [], []

    for header, expected_type, expected_length in headers_types:
        if header not in df.columns:
            continue

        actual_values = df[header].astype(str).str.strip()  # Supprimer les espaces

        # 🔹 Vérification de la longueur
        if pd.notna(expected_length) and isinstance(expected_length, (int, float)):
            max_allowed_length = 10 if expected_length == 8 else int(expected_length)
            if any(actual_values.str.len() > max_allowed_length):
                length_check_failed.append(f"{header} (Max: {max_allowed_length}, Trouvé: {actual_values.str.len().max()})")

        # 🔹 Vérification du type
        if expected_type == "Numérique":
            if not all(actual_values.isna() | actual_values.str.match(r'^\d+$', na=True)):
                type_check_failed.append(f"{header} : Attendu 'Numérique', trouvé des valeurs non numériques.")

        elif expected_type == "Date aaaammjj":
            if not all(actual_values.isna() | actual_values.str.match(r'^\d{8}$', na=True)):
                type_check_failed.append(f"{header} : Attendu 'Date aaaammjj', format incorrect.")

    # 🔹 Enregistrement des erreurs
    if length_check_failed or type_check_failed:
        log_and_move(
            file_path,
            f"Erreurs -> Longueur: {', '.join(length_check_failed)}, Type: {', '.join(type_check_failed)}",
            failed_files
        )

# 🔹 Fonction pour logguer et déplacer les fichiers échoués
def log_and_move(file_path, reason, failed_files):
    logging.error(f"❌ {file_path} : {reason}")
    failed_files.append((file_path, reason))
    shutil.move(file_path, os.path.join(REPORT_DIR, os.path.basename(file_path)))

    with open(report_file_path, "a", encoding="utf-8") as report_file:
        report_file.write(f"❌ {file_path}\nRaison : {reason}\n\n")

# 🔹 Génération des résultats JSON
def generate_test_results(failed_files, json_path):
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    
    test_results = [{"file_path": f, "status": "Failed", "reason": r} for f, r in failed_files]

    # Ajouter les fichiers valides
    for data_dir in DATA_DIRS:
        if os.path.exists(data_dir):
            for ent_folder in os.listdir(data_dir):
                ent_path = os.path.join(data_dir, ent_folder)
                if os.path.isdir(ent_path):
                    for filename in os.listdir(ent_path):
                        if filename.endswith(".csv"):
                            file_path = os.path.join(ent_path, filename)
                            if file_path not in [f[0] for f in failed_files]:
                                test_results.append({"file_path": file_path, "status": "Passed", "reason": None})

    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(test_results, json_file, indent=4, ensure_ascii=False)
    
    logging.info("📄 Rapport JSON généré : %s", json_path)

# 🔹 Traitement des fichiers
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
                flux_name = next((flux for flux in org_flux_sheets if flux in filename.upper()), filename.upper())
                logging.info("📂 Flux détecté : %s", flux_name)
                check_mandatory_columns(file_path, flux_name, failed_files)

# 🔹 Génération des rapports
if failed_files:
    with open(report_file_path, "w", encoding="utf-8") as report_file:
        for file_path, reason in failed_files:
            report_file.write(f"❌ {file_path}\nRaison : {reason}\n\n")
    logging.info("📑 Rapport des erreurs généré : %s", report_file_path)
else:
    logging.info("✅ Tous les fichiers ont passé les tests.")
    shutil.rmtree(REPORT_DIR, ignore_errors=True)

generate_test_results(failed_files, json_report_path)
