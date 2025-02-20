import re
import os
import glob
import shutil
import pandas as pd
from src.utils import load_sheets
from src.mapping import (
    generate_mapping, 
    extract_mandatory_columns
    
)

CSV_FOLDER = "data"
EXCEL_FILE_PATTERN = os.path.join("data", "*Cahier des charges*.xlsx")
PROCESSED_FOLDER = "data/PROCESSED"

flux_test_count = 0  # Variable globale pour compter le nombre de flux testés

def main():
    global flux_test_count  

    # Création des dossiers de sortie
    q_folder = os.path.join(PROCESSED_FOLDER, "Q")
    m_folder = os.path.join(PROCESSED_FOLDER, "M")
    noqnom_folder = os.path.join(CSV_FOLDER, "NO Match")

    os.makedirs(q_folder, exist_ok=True)
    os.makedirs(m_folder, exist_ok=True)
    os.makedirs(noqnom_folder, exist_ok=True)

    # Récupération du fichier Excel
    excel_files = glob.glob(EXCEL_FILE_PATTERN)
    if not excel_files:
        print("❌ Aucun fichier 'Cahier des charges' trouvé.")
        exit()

    EXCEL_FILE = excel_files[0]
    print(f"✅ Fichier Excel sélectionné : {EXCEL_FILE}")

 

    # Chargement des feuilles Excel
    sheets = load_sheets(EXCEL_FILE)  # Assure que `sheets` est bien un dict
 

    # Génération du mapping avec les bons paramètres
    """csv_mapping = generate_mapping(naming_constraints, flux_names)
    print(csv_mapping)

    if not csv_mapping:
        print("❌ Aucun fichier CSV ne correspond aux contraintes de nommage.")
        exit()

    print(f"\n🔍 Total fichiers trouvés : {len(csv_mapping)}")
    print(f"📂 Fichiers détectés pour traitement : {list(csv_mapping.keys())}")

    files_to_move = []

    print("\n🔗 Mapping des fichiers CSV avec leurs chemins complets :")"""
    for flux_name, paths in csv_mapping.items():
        for path in paths:
            try:
                parent_folder = (
                    q_folder if "_Q_" in os.path.basename(path) 
                    else m_folder if "_M_" in os.path.basename(path) 
                    else noqnom_folder
                )

                try:
                    df_excel = pd.read_excel(EXCEL_FILE, sheet_name=flux_name, engine='openpyxl')
                except ValueError:
                    print(f"⚠️ Feuille '{flux_name}' introuvable dans {EXCEL_FILE}.")
                    continue

                if df_excel.shape[1] < 4:
                    print(f"⚠️ La feuille '{flux_name}' ne contient pas assez de colonnes.")
                    continue

                print(f"\n🔄 Chargement de l'en-tête du fichier CSV : {flux_name}")
                df_csv = pd.read_csv(path, nrows=0, sep=";")
                csv_headers = list(df_csv.columns)

                match = re.match(r"^ENT-(\d+)_", os.path.basename(path))
                folder_name = f"ENT-{match.group(1)}" if match else "Other"

                destination_folder = os.path.join(parent_folder, folder_name)
                os.makedirs(destination_folder, exist_ok=True)

                files_to_move.append((path, destination_folder))
                flux_test_count += 1

                print("\n🔎 Vérification des colonnes dans Excel par rapport aux en-têtes du CSV")
                for index, value in df_excel.iloc[3:, 2].items(): 
                    if pd.isna(value) or str(value).strip() == "":
                        print(f"⚠️ Ligne vide détectée à l'index {index}. Arrêt du traitement.")
                        break 

                    value = str(value).strip()
                    if value in csv_headers:
                        print(f"✅ {value} : OK.")
                    else:
                        print(f"❌ {value} : Manquant.")

                mandatory_columns = extract_mandatory_columns(df_excel)
                print(f"\n📌 Colonnes obligatoires pour {flux_name} : {mandatory_columns}")

                df_csv_full = pd.read_csv(path, sep=";")

                for column in mandatory_columns:
                    print(f"\n📍 Vérification de '{column}'...")
                    missing_values = df_csv_full[column].isnull() | df_csv_full[column].astype(str).str.strip().eq("")
                    if missing_values.any():
                        missing_indices = df_csv_full[missing_values].index.tolist()
                        print(f"⚠️ '{column}' a des valeurs manquantes aux lignes : {missing_indices}")
                    else:
                        print(f"✅ '{column}' est complète.")

            except Exception as e:
                print(f"❌ Erreur fichier {path} : {e}")
                continue  

    print("\n📂 Déplacement des fichiers traités...")
    for file_path, destination_folder in files_to_move:
        destination_path = os.path.join(destination_folder, os.path.basename(file_path))
        if os.path.exists(destination_path):
            print(f"⚠️ {destination_path} existe déjà.")
        else:
            shutil.move(file_path, destination_path)
            print(f"✅ {file_path} déplacé vers {destination_path}")

    print(f"\n Total flux testés : {flux_test_count}")
  

if __name__ == "__main__":
    main()
