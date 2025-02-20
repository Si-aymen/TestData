import os
import pandas as pd
import json
import re  # Ajout de l'import manquant

# Vérifier si le fichier existe avant de continuer
file_path = "Cahier des charges - Reporting Flux Standard - V25.1.0.xlsx"
if not os.path.exists(file_path):
    print(f"❌ Erreur : Le fichier '{file_path}' n'existe pas.")
    exit()

def extract_flux_sheet_names(sheets):
    """Retourne une liste de tous les noms de feuilles."""
    return list(sheets.keys())


# Charger toutes les feuilles du fichier Excel dans un dictionnaire de DataFrames
sheets = pd.read_excel(file_path, sheet_name=None)

# Extraire les noms des feuilles pertinentes
flux_sheets = extract_flux_sheet_names(sheets)

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
        if match and match.group(1):  # Vérifier qu'un groupe capturé existe
            return match.group(1).upper()

    return ""  # Retourner une chaîne vide si aucun motif ne correspond

# Tester la fonction
naming_constraints = load_naming_constraints(file_path)

# Afficher les résultats
print("\n🔍 Notice files name : ")
print(json.dumps(naming_constraints, indent=4, ensure_ascii=False))
