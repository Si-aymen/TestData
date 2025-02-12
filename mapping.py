import os
import pandas as pd
import json
import re  # Ajout de l'import manquant

# Vérifier si le fichier existe avant de continuer
file_path = "Cahier des charges - Reporting Flux Standard - V25.1.0 1.xlsx"
if not os.path.exists(file_path):
    print(f"❌ Erreur : Le fichier '{file_path}' n'existe pas.")
    exit()

def extract_flux_sheet_names(sheets):
    """Retourne une liste de tous les noms de feuilles."""
    return list(sheets.keys())

flux_mapping = {
    "ENCAISSEMENTS": "ENCAISSEMENTS", 
    "CONTRATSCOLLECTIFS": "CONTRATCOLLECTIF_STOCK", 
    "COTISATIONS": "COTISATIONS",
    "ADHESIONSINDIVIDUELLES": "ADHESIONSINDIVIDUELLES_STOCK",
    "RELANCES_INDIVIDUELLES": "RELANCES_INDIVIDUELLES",
    "FAMILLE_ACTES_LIMITE": "FAMILLE_ACTES_LIMITE",
    "REMISES_RG": "REMISES_RG",
    "REFERENTIEL_ACTES": "REFERENTIEL_ACTES",
    "PRESTATIONSANTE": "PRESTATIONSANTE",
    "PRESTATIONSANTEATTENTE": "PRESTATIONSANTE",
    "FRANCHISES_FAM_ACTES": "FRANCHISES_FAM_ACTES",
    "REFERENTIEL_FORMULE_REMB": "FORMULES_REMBOURSEMENTS",
    "REFERENTIEL_GROUPES": "REFERENTIEL_GROUPE",
    "REFERENTIEL_PRODUITS_OPTIONS": "REFERENTIEL_PRODUITS_OPTIONS",
    "ECRITURE_COMPTA": "ECRITURE_COMPTA",
    "COMMISSIONS": "COMMISSIONS",
    "PRESTATIONPREV_SIN": "PRESTATIONPREV_SIN",
    "PRESTATIONPREV_PERIOD_REMUN": "PRESTATIONPREV_PERIOD_REMUN",
    "PRESTATIONPREV_BENCAP": "PRESTATIONPREV_BENCAP",
    "DECLARATION_HONORAIRES": "HONORAIRES",
    "PRESTATIONPREV_REG": "PRESTATIONPREV_REG"
}

# Charger toutes les feuilles du fichier Excel dans un dictionnaire de DataFrames
sheets = pd.read_excel(file_path, sheet_name=None)

# Extraire les noms des feuilles pertinentes
flux_sheets = extract_flux_sheet_names(sheets)

# Appliquer le mapping pour renommer les flux
renamed_flux_sheets = {flux_mapping.get(flux, flux) for flux in flux_sheets}

# Afficher le résultat
print("\n📌 Flux Sheets (avant mapping) :", flux_sheets)
#print("\n🔄 Mapping des flux :", flux_mapping)
print("\n✅ Flux après mapping :", renamed_flux_sheets)

# Filtrer uniquement les flux qui existent dans le mapping
filtered_mapping = {flux: flux_mapping[flux] for flux in flux_sheets if flux in flux_mapping}

# Affichage formaté des flux filtrés
#print("\n📌 Mapping des flux correspondants :")
#print(json.dumps(filtered_mapping, indent=4, ensure_ascii=False))

def extract_mandatory_columns(df):
    """Retourne une liste des colonnes obligatoires à partir de la feuille de cahier des charges."""
    mandatory_columns = []

    # Vérifier que le DataFrame a au moins 4 colonnes
    if df.shape[1] < 4:
        print(f"⚠️ Feuille ignorée : Moins de 4 colonnes détectées ({df.shape[1]} colonnes)")
        return mandatory_columns

    # Affichage des colonnes pour debug
    print(f"\n📌 Colonnes détectées : {list(df.columns)}")

    try:
        # Supposons que la colonne "Obligatoire" est en position 3 et le nom en position 2
        for _, row in df.iloc[3:].iterrows():
            column_name = row.iloc[2]  # Nom de la colonne
            mandatory = row.iloc[3]  # Valeur "Oui" ou autre

            if isinstance(mandatory, str) and mandatory.strip().lower() == "oui":
                mandatory_columns.append(column_name.strip())

    except Exception as e:
        print(f"❌ Erreur lors de l'extraction des colonnes obligatoires : {e}")

    return mandatory_columns

# Vérifier si la feuille "ENCAISSEMENTS" existe avant de la traiter
if "ENCAISSEMENTS" in sheets:
    df = sheets["ENCAISSEMENTS"]
    mandatory_cols = extract_mandatory_columns(df)
    print("\n✅ Colonnes obligatoires extraites :", mandatory_cols)
else:
    print("⚠️ La feuille 'ENCAISSEMENTS' n'existe pas dans le fichier Excel.")

def load_naming_constraints(notices_file, sheet_name="Notice"):
    """Charge les contraintes de nommage depuis la feuille 'Notice'."""
    try:
        df = pd.read_excel(notices_file, sheet_name=sheet_name)

        if df.shape[0] < 12 or df.shape[1] < 2:
            raise ValueError("La feuille 'Notice' ne contient pas suffisamment de données.")

        df = df.iloc[11:, [1]].dropna()

        naming_constraints = {}
        for file_name in df.iloc[:, 0]:
            simplified_name = extract_simplified_filename(file_name)
            if simplified_name:
                naming_constraints[file_name] = simplified_name

        return naming_constraints

    except FileNotFoundError:
        print(f"❌ Erreur : Le fichier '{notices_file}' n'existe pas.")
        return {}

