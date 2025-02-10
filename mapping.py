import os
import pandas as pd


def extract_flux_sheet_names(sheets):
    """Retourne une liste des noms de feuilles contenant au moins une colonne avec 'Flux'."""
    flux_sheet_names = []  # Liste pour stocker les noms des feuilles pertinentes

    # Parcourir chaque feuille
    for sheet_name, df in sheets.items():
        # Vérifier si au moins une colonne contient 'Flux' dans son nom
        if any('Flux' in column for column in df.columns):
            flux_sheet_names.append(sheet_name)  # Ajouter le nom de la feuille à la liste

    # Afficher les noms des feuilles pour vérification
    return flux_sheet_names  # Retourner la liste


def extract_mandatory_columns(df):
    """Retourne une liste des colonnes obligatoires à partir de la feuille de cahier des charges."""
    mandatory_columns = []

    # Vérifier que le DataFrame a au moins 4 colonnes (indices 0, 1, 2, 3)
    if df.shape[1] < 4:
        print(f"⚠️ Feuille ignorée : Moins de 4 colonnes détectées ({df.shape[1]} colonnes)")
        return mandatory_columns

    # Vérifier les noms des colonnes pour s'assurer de leur position
    #print(f"📌 Colonnes détectées : {list(df.columns)}")

    try:
        # Supposons que la colonne "Obligatoire" est en position 3 et le nom en position 2
        for _, (column_name, mandatory) in df.iloc[3:, [2, 3]].iterrows():
            if str(mandatory).strip().lower() == "oui":
                mandatory_columns.append(column_name.strip())

    except Exception as e:
        print(f"❌ Erreur lors de l'extraction des colonnes obligatoires : {e}")

    return mandatory_columns




# Charger toutes les feuilles du fichier Excel dans un dictionnaire de DataFrames
sheets = pd.read_excel("Cahier des charges - Reporting Flux Standard - V25.1.0 1.xlsx", sheet_name=None)

# Appeler la fonction pour extraire les noms des feuilles pertinentes
flux_sheets = extract_flux_sheet_names(sheets)

# Afficher les résultats
print("Flux names : ",flux_sheets)


# Charger le fichier Excel et lire la feuille contenant le cahier des charges
df = pd.read_excel("Cahier des charges - Reporting Flux Standard - V25.1.0 1.xlsx", sheet_name="PRESTATIONSANTE")

# Extraire les colonnes obligatoires
mandatory_cols = extract_mandatory_columns(df)

# Afficher le résultat
print("\n \n")
print("cols : ",mandatory_cols)

