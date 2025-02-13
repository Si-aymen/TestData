import os
import pandas as pd
import re
import shutil
from mapping import extract_mandatory_columns,get_entete_csv 

# Définition des dossiers contenant les fichiers CSV
DATA_DIRS = ["data/M_FILES", "data/Q_FILES"]
REPORT_DIR = "data/Mandatory_columns_failure"
os.makedirs(REPORT_DIR, exist_ok=True)
report_file_path = os.path.join(REPORT_DIR, "failure_report.txt")

# Charger le fichier Excel contenant les cahiers des charges
try:
    cahier_des_charges = pd.read_excel(
        "Cahier des charges - Reporting Flux Standard - V25.1.0 1.xlsx", 
        sheet_name=None
    )
except Exception as e:
    print(f"❌ Erreur lors de la lecture du fichier Excel : {e}")
    exit(1)

# Extraction des noms des feuilles et de leurs colonnes obligatoires
mandatory_columns_by_flux = {
    sheet_name.strip().upper(): extract_mandatory_columns(df) for sheet_name, df in cahier_des_charges.items()
}

def get_flux_name_from_filename(filename, flux_names):
    """
    Extrait le nom du flux à partir du nom de fichier en cherchant une correspondance avec les flux connus.
    """
    filename_upper = filename.upper()  # Pour éviter les erreurs de casse
    for flux_name in flux_names:
        if flux_name in filename_upper:
            return flux_name
    return None

def check_mandatory_columns(file_path, flux_name, failed_files):
    """
    Vérifie si le fichier CSV contient toutes les colonnes obligatoires du flux donné et affiche les résultats.
    """
    print(f"\n📂 Traitement du fichier : {file_path}")

    try:
        df = pd.read_csv(file_path, sep=";", encoding="utf-8", low_memory=False)
    except Exception as e:
        print(f"❌ {file_path} : Erreur lors de la lecture -> {e}")
        failed_files.append(file_path)
        shutil.move(file_path, os.path.join(REPORT_DIR, os.path.basename(file_path)))
        return
    
    mandatory_columns = mandatory_columns_by_flux.get(flux_name, [])
    missing_columns = [col for col in mandatory_columns if col not in df.columns]

    if missing_columns:
        print(f"❌ {file_path} : Colonnes manquantes pour {flux_name} -> {missing_columns}")
        failed_files.append(file_path)
        shutil.move(file_path, os.path.join(REPORT_DIR, os.path.basename(file_path)))
    else:
        print(f"✅ {file_path} : Toutes les colonnes obligatoires sont présentes pour {flux_name}")

failed_files = []

# Parcourir les dossiers M_FILES et Q_FILES
for data_dir in DATA_DIRS:
    if not os.path.exists(data_dir):
        print(f"❌ Le dossier {data_dir} n'existe pas.")
        continue
    
    # Parcourir tous les sous-dossiers (ENT folders)
    for ent_folder in os.listdir(data_dir):
        ent_path = os.path.join(data_dir, ent_folder)
        if not os.path.isdir(ent_path):
            continue  # Ignorer les fichiers qui ne sont pas des dossiers
        
        csv_files = [f for f in os.listdir(ent_path) if f.endswith(".csv")]
        
        if not csv_files:
            print(f"⚠️ Aucun fichier CSV trouvé dans {ent_path}.")
        else:
            for filename in csv_files:
                file_path = os.path.join(ent_path, filename)
                
                # Identifier le flux correspondant
                flux_name = get_flux_name_from_filename(filename, mandatory_columns_by_flux.keys())

                if flux_name:
                    check_mandatory_columns(file_path, flux_name, failed_files)
                else:
                    print(f"⚠️ {file_path} : Aucun flux correspondant trouvé.")
                    failed_files.append(file_path)
                    shutil.move(file_path, os.path.join(REPORT_DIR, os.path.basename(file_path)))

# Exporter le rapport des fichiers échoués
if failed_files:
    with open(report_file_path, "w", encoding="utf-8") as report_file:
        report_file.write("\n".join(failed_files))
    print(f"📝 Rapport généré : {report_file_path}")
else:
    print("✅ Tous les fichiers ont passé les tests.")
