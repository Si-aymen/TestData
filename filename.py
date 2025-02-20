import os
import shutil
import re
from datetime import datetime
from src.mapping import generate_mapping, check_mandatory_columns, extract_simplified_filename
from src.entete import match_headers_with_filename
from longueur_et_type import check_header_lengths, check_header_type

CSV_FOLDER = "data"
EXCEL_FILE_PATTERN = os.path.join("data", "*Cahier des charges*.xlsx")
PROCESSED_FOLDER = "data/PROCESSED"
INVALID_FOLDER = "data/INVALID"  

os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(INVALID_FOLDER, exist_ok=True)

# Récupérer le premier fichier Excel correspondant au pattern
excel_files = [file for file in os.listdir("data") if file.endswith(".xlsx") and "Cahier des charges" in file]
if not excel_files:
    print("❌ Aucun fichier 'Cahier des charges' trouvé.")
    exit()

EXCEL_FILE = os.path.join("data", excel_files[0])
print(f"✅ Fichier Excel sélectionné : {EXCEL_FILE}")

flux_test_total = 0
flux_test_valid = 0
flux_test_invalid = 0

date_test = datetime.strptime("20250219", "%Y%m%d").date()
ent_pattern = re.compile(r"(ENT-\d+)")

try:
    valid_csv_files = generate_mapping(CSV_FOLDER, EXCEL_FILE, date_test)
    if valid_csv_files:
        for file in valid_csv_files:
            filename = os.path.basename(file)
            flux_test_total += 1

            # Vérifier la correspondance des en-têtes
            match_result = match_headers_with_filename(file, EXCEL_FILE)
            if match_result in ["Correspondance exacte", "Correspondance partielle"]:
                mandatory_columns_errors = check_mandatory_columns(file, EXCEL_FILE)
                length_errors = check_header_lengths(file, EXCEL_FILE)
                type_errors = check_header_type(file, EXCEL_FILE)

                if mandatory_columns_errors or length_errors or type_errors:
                    #print(f"❌ Erreurs détectées dans {filename}, déplacement vers {INVALID_FOLDER}")
                    simplified_name = extract_simplified_filename(filename)
                    type_folder = "Q" if "_Q_" in filename else "M" if "_M_" in filename else "Other"
                    destination_folder = os.path.join(INVALID_FOLDER, simplified_name, type_folder)
                    os.makedirs(destination_folder, exist_ok=True)
                    shutil.move(file, os.path.join(destination_folder, filename))
                    flux_test_invalid += 1
                    continue

                base_folder = PROCESSED_FOLDER + ("/Q" if "_Q_" in filename else "/M" if "_M_" in filename else "/NO MATCH")
                match = ent_pattern.search(filename)
                ent_folder = match.group(1) if match else "Other"
                destination_folder = os.path.join(base_folder, ent_folder)
                os.makedirs(destination_folder, exist_ok=True)
                shutil.move(file, os.path.join(destination_folder, filename))
                flux_test_valid += 1
            else:
                print(f"❌ En-têtes non correspondants, fichier ignoré : {filename}")
                simplified_name = extract_simplified_filename(filename)
                type_folder = "Q" if "_Q_" in filename else "M" if "_M_" in filename else "Other"
                destination_folder = os.path.join(INVALID_FOLDER, simplified_name, type_folder)
                os.makedirs(destination_folder, exist_ok=True)
                shutil.move(file, os.path.join(destination_folder, filename))
                flux_test_invalid += 1

        # Affichage 
        print("\n📊 **Résumé du traitement**")
        print(f"📂 Nombre total de fichiers testés : {flux_test_total}")
        print(f"✅ Nombre de fichiers valides déplacés vers PROCESSED : {flux_test_valid}")
        print(f"❌ Nombre de fichiers invalides déplacés vers INVALID : {flux_test_invalid}")
    else:
        print("❌ Aucun fichier CSV valide trouvé.")
except Exception as e:
    print(f"❌ Erreur lors du traitement : {e}")
