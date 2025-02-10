import os
import pandas as pd
import json

# Vérifier si le fichier existe avant de continuer
file_path = "Cahier des charges - Reporting Flux Standard - V25.1.0 1.xlsx"
if not os.path.exists(file_path):
    print(f"❌ Erreur : Le fichier '{file_path}' n'existe pas.")
    exit()

def extract_flux_sheet_names(sheets):
    """Retourne une liste des noms de feuilles contenant au moins une colonne avec 'Flux'."""
    flux_sheet_names = []
    for sheet_name, df in sheets.items():
        if any('Flux' in str(column) for column in df.columns):  # Assurer que column est bien une string
            flux_sheet_names.append(sheet_name)
    return flux_sheet_names

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
#print("Flux names :", flux_sheets)
# Appliquer le mapping pour renommer les flux
renamed_flux_sheets = [flux_mapping.get(flux, flux) for flux in flux_sheets]

# Afficher le résultat
renamed_flux_sheets = {flux_mapping.get(flux, flux) for flux in flux_sheets}  
print("📌 Flux Sheets (avant mapping) :", flux_sheets)
print("🔄 Mapping des flux :", flux_mapping)
print("✅ Flux après mapping :", renamed_flux_sheets)

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
    print(f"📌 Colonnes détectées : {list(df.columns)}")

    try:
        # Supposons que la colonne "Obligatoire" est en position 3 et le nom en position 2
        for _, (column_name, mandatory) in df.iloc[3:, [2, 3]].iterrows():
            if str(mandatory).strip().lower() == "oui":
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
