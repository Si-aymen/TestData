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
   
    "CONTRATSCOLLECTIFS": "CONTRATCOLLECTIF_STOCK",
    "ADHESIONSINDIVIDUELLES": "ADHESIONSINDIVIDUELLES_STOCK",
    "REFERENTIEL_FORMULE_REMB": "FORMULES_REMBOURSEMENTS",
    "REFERENTIEL_GROUPES": "REFERENTIEL_GROUPE",
    "DECLARATION_HONORAIRES": "HONORAIRES",
    "BENEXT":"BENEFICIAIRE_EXTERNE"
       
}

reverse_flux_mapping = {
   
    "CONTRATCOLLECTIF_STOCK": "CONTRATSCOLLECTIFS",
    "ADHESIONSINDIVIDUELLES_STOCK": "ADHESIONSINDIVIDUELLES",
    "FORMULES_REMBOURSEMENTS": "REFERENTIEL_FORMULE_REMB",
    "REFERENTIEL_GROUPE": "REFERENTIEL_GROUPES",
    "DECLARATION_HONORAIRES": "HONORAIRES",
    "BENEFICIAIRE_EXTERNE":"BENEXT"
       
}



# Charger toutes les feuilles du fichier Excel dans un dictionnaire de DataFrames
sheets = pd.read_excel(file_path, sheet_name=None)

# Extraire les noms des feuilles pertinentes
flux_sheets = extract_flux_sheet_names(sheets)

# Appliquer le mapping pour renommer les flux
renamed_flux_sheets = {flux_mapping.get(flux, flux) for flux in flux_sheets}

#reverse to org
org_flux_sheets = {reverse_flux_mapping.get(flux, flux) for flux in flux_sheets}


# Afficher le résultat
#print("\n📌 Flux Sheets (avant mapping) :", flux_sheets)
#print("\n🔄 Mapping des flux :", flux_mapping)
print("\n✅ Flux après mapping :", renamed_flux_sheets)
print("\n📌 org des flux :", org_flux_sheets)



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
    #print(f"\n📌 Colonnes détectées : {list(df.columns)}")

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

def get_entete_csv(df):
    """Retourne les valeurs de la colonne C à partir de la 5ᵉ ligne (index 4) jusqu'à la première cellule vide."""
    try:
        values = []
        for value in df.iloc[4:, 2]:  # Parcours de la colonne C à partir de la ligne 5 (index 4)
            if pd.isna(value) or value == "":  # Arrêter si la cellule est vide
                break
            values.append(value)
        return values
    except IndexError:
        print("⚠️ Erreur : La colonne C n'existe pas dans le DataFrame.")
        return []
import pandas as pd

def extract_headers_and_types(df):
    """
    Extrait les noms d'entête (colonne C) et les types de données (colonne F) à partir de la 5ᵉ ligne.
    
    Args:
        df (pd.DataFrame): Le dataframe contenant les données.
    
    Returns:
        list: Liste de tuples contenant (Nom de l'entête, Type de données)
    """
    headers_types = []
    
    # Parcours des lignes à partir de l'index 4 (5ᵉ ligne)
    for _, row in df.iloc[4:].iterrows():
        header = row.iloc[2]  # Colonne C
        data_type = row.iloc[5]  # Colonne F
        Hlength = row.iloc[6]  # Colonne G
        
        if pd.isna(header) or header == "":  # Arrêter si la cellule est vide
            break
        
        headers_types.append((header, data_type,Hlength))
    
    return headers_types




# Vérifier si la feuille "ENCAISSEMENTS" existe avant de la traiter
if "DECLARATION_HONORAIRES" in sheets:
    df = sheets["DECLARATION_HONORAIRES"]
    header = extract_headers_and_types(df)
    C_column = get_entete_csv(df)
    mandatory_cols = extract_mandatory_columns(df)
    print("\n✅ Colonnes entete type :", header)
    print("\n✅ Colonnes entete extraites :", C_column)
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

