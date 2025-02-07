import os
import pandas as pd
import re
from mapping import extract_mandatory_columns 

# Définition du dossier contenant les fichiers CSV
DATA_DIR = "data/ENT1"

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

def check_mandatory_columns(file_path, flux_name):
    """
    Vérifie si le fichier CSV contient toutes les colonnes obligatoires du flux donné et affiche les résultats.
    """
    print(f"\n📂 Traitement du fichier : {file_path}")

    try:
        df = pd.read_csv(file_path, sep=";", encoding="utf-8", low_memory=False)
    except Exception as e:
        print(f"❌ {file_path} : Erreur lors de la lecture -> {e}")
        return
    
    mandatory_columns = mandatory_columns_by_flux.get(flux_name, [])
    
    missing_columns = [col for col in mandatory_columns if col not in df.columns]

    if missing_columns:
        print(f"❌ {file_path} : Colonnes manquantes pour {flux_name} -> {missing_columns}")
    else:
        print(f"✅ {file_path} : Toutes les colonnes obligatoires sont présentes pour {flux_name}")

# Vérifier que le dossier existe
if not os.path.exists(DATA_DIR):
    print(f"❌ Le dossier {DATA_DIR} n'existe pas.")
    exit(1)

# Traitement des fichiers CSV dans le dossier
csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]

if not csv_files:
    print("⚠️ Aucun fichier CSV trouvé dans le dossier.")
else:
    for filename in csv_files:
        file_path = os.path.join(DATA_DIR, filename)
        
        # Identifier le flux correspondant
        flux_name = get_flux_name_from_filename(filename, mandatory_columns_by_flux.keys())

        if flux_name:
            check_mandatory_columns(file_path, flux_name)
        else:
            print(f"⚠️ {file_path} : Aucun flux correspondant trouvé.")
