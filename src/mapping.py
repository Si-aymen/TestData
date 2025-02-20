import os
import pandas as pd
import re
from datetime import datetime
def extract_flux_sheet_names(sheet_names):
    """Retourne une liste de noms de feuilles renommés."""
    flux_mapping = {
        "CONTRATSCOLLECTIFS": "CONTRATCOLLECTIF_STOCK",
        "ADHESIONSINDIVIDUELLES": "ADHESIONSINDIVIDUELLES_STOCK",
        "REFERENTIEL_FORMULE_REMB": "FORMULES_REMBOURSEMENTS",
        "REFERENTIEL_GROUPES": "REFERENTIEL_GROUPE",
        "DECLARATION_HONORAIRES": "HONORAIRES",
        "BENEXT":"BENEFICIAIRE_EXTERNE"
    }
    renamed_flux_sheets = [flux_mapping.get(flux, flux) for flux in sheet_names]
    return renamed_flux_sheets
def extract_flux_sheet_names_reverse(sheet_names):
    """Retourne une liste de noms de feuilles renommés."""
    flux_mapping = {
        "CONTRATCOLLECTIF_STOCK":"CONTRATSCOLLECTIFS",
        "ADHESIONSINDIVIDUELLES_STOCK":"ADHESIONSINDIVIDUELLES",
        "FORMULES_REMBOURSEMENTS":"REFERENTIEL_FORMULE_REMB",
        "REFERENTIEL_GROUPE": "REFERENTIEL_GROUPES",
        "HONORAIRES":"DECLARATION_HONORAIRES",
        "BENEFICIAIRE_EXTERNE":"BENEXT"
    }

    renamed_flux_sheets = [
        flux_mapping.get(flux, flux) for flux in sheet_names
    ]
    return renamed_flux_sheets


def extract_simplified_filename(filename):
    """Extrait un nom simplifié à partir du nom de fichier en utilisant plusieurs expressions régulières."""
    patterns = [
        r"Client_N°Flux_(?:MOD1_)?([A-Za-z]+(?:_[A-Za-z]+)*)_FREQUENCE",  # Pattern notice
        r"OCIANE_RC2_\d+_([A-Za-z_]+?)_[QM]?_?F?_?\d{8}",  # Pattern flux
        r"OCIANE_RC2_\d+_([A-Za-z_]+?)_\d{8}"  
    ]
    
   
    if not isinstance(filename, str):
        return ""

    for pattern in patterns:
        match = re.search(pattern, filename)
        if match and match.group(1): 
            return match.group(1).upper()  

    return ""  

def load_naming_constraints(notices_file, sheet_name="Notice"):
    """Charge les contraintes de nommage depuis la feuille 'Notice' et retourne une liste des noms simplifiés."""
    df = pd.read_excel(notices_file, sheet_name=sheet_name)
    
    if df.shape[0] < 12 or df.shape[1] < 2:
        raise ValueError("La feuille 'Notice' ne contient pas suffisamment de données.")
    
    df = df.iloc[11:, [1]].dropna()  
    simplified_names = [
        extract_simplified_filename(file_name) 
        for file_name in df.iloc[:, 0] 
        if extract_simplified_filename(file_name)
    ]
    
    return simplified_names


def generate_mapping(csv_folder, notices_file, date_test):
    """Génère un mapping des fichiers CSV qui respectent les contraintes de nommage et la date."""
    
    if not os.path.exists(csv_folder):
        raise FileNotFoundError(f"Le dossier {csv_folder} n'existe pas.")
    
    
    naming_constraints = load_naming_constraints(notices_file)

    
    excel_file = pd.ExcelFile(notices_file)
    sheets = excel_file.sheet_names  

    
    flux_names = extract_flux_sheet_names(sheets)  

    valid_csv_files = []  
    # Parcourir tous les fichiers du dossier
    for filename in os.listdir(csv_folder):
        if filename.endswith(".csv"):
            file_path = os.path.join(csv_folder, filename)

            if not controle_date(file_path, date_test):
                print(f"⛔ {filename} a une date incorrecte.")
                continue

            simplified_filename = extract_simplified_filename(filename)

           
            if not simplified_filename:
                print(f"⛔ {filename} ne respecte pas la nomenclature.")
                continue  

            
            if simplified_filename not in naming_constraints:
                print(f"⚠️ {filename} ne correspond à aucune contrainte de nommage.")
                continue  

           
            if simplified_filename not in flux_names:
                print(f"⚠️ {filename} ne correspond à aucun flux extrait.")
                continue  
            
            valid_csv_files.append(file_path)  

    return valid_csv_files

def controle_date(csv_file, date_test):

    filename = os.path.basename(csv_file)  
    if not filename.endswith(".csv"):
        return False  
    
    date_part = filename[-12:-4]  
    
    date_str = date_test.strftime("%Y%m%d")
    
    return date_part == date_str  

def extract_mandatory_columns(df):
    if df.shape[0] < 4 or df.shape[1] < 4:
        raise ValueError("Le dataframe ne contient pas assez de données pour extraire les colonnes obligatoires.")
    mandatory_columns = [col.strip().upper() for col, mandatory in df.iloc[3:, [2, 3]].itertuples(index=False) if str(mandatory).strip().lower() == "oui"]
    return mandatory_columns


def check_mandatory_columns(csv_file, excel_file):
    # Extraire le nom simplifié du fichier pour déterminer le nom de la feuille Excel
    sheet_name = extract_simplified_filename(os.path.basename(csv_file))
    
    # Utiliser extract_flux_sheet_names pour obtenir le nom réel de la feuille
    sheet_name = extract_flux_sheet_names_reverse([sheet_name])[0]

    # Lire la feuille Excel et extraire les colonnes obligatoires
    df_excel = pd.read_excel(excel_file, sheet_name=sheet_name)
    mandatory_columns = extract_mandatory_columns(df_excel)
    
    filename = os.path.basename(csv_file)
    errors = []

    # Lire le fichier CSV
    df_csv = pd.read_csv(csv_file, sep=";", low_memory=False)

    # Normaliser les noms de colonnes en majuscules pour comparaison
    df_csv_columns_normalized = {col.upper() for col in df_csv.columns}
    
    # Vérifier si toutes les colonnes obligatoires sont présentes (indépendamment de la casse)
    missing_columns = [col for col in mandatory_columns if col.upper() not in df_csv_columns_normalized]

    if missing_columns:
        errors.append(f"🚨 Colonnes manquantes : {', '.join(missing_columns)}")

    if errors:
        print(f"❌ Problèmes détectés dans le fichier '{filename}':")
        for error in errors:
            print(error)
    else:
        return ""  # Aucune erreur 
    
    return {filename: errors}
