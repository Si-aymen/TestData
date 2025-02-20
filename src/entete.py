import os
import pandas as pd
import re
from src.mapping import extract_simplified_filename , extract_flux_sheet_names_reverse
#recupere la premiere ligne des fichiers csv sep ; 
def get_csv_headers(csv_folder):
    csv_headers = {}

    for filename in os.listdir(csv_folder):
        file_path = os.path.join(csv_folder, filename)

 
        if filename.endswith(".csv"):
            try:
                # Read the first row of the CSV file to get the headers
                df = pd.read_csv(file_path, nrows=0, sep=";")
                csv_headers[filename] = list(df.columns)
            except Exception as e:
                print(f"❌ Erreur lors de la lecture du fichier {filename}: {e}")
    
    return csv_headers


def get_sheet_headers(excel_file, sheet_name):
    try:
        # Lire la feuille spécifiée
        df = pd.read_excel(excel_file, sheet_name=sheet_name, engine='openpyxl')

        # Vérifier si la feuille contient au moins 5 lignes et 3 colonnes
        if df.shape[0] > 3 and df.shape[1] > 2:
            headers = []            
            for value in df.iloc[3:, 2]:  
                if pd.isna(value) or str(value).strip() == "":  # Arrêter si la ligne est vide
                    break
                headers.append(str(value).strip())

            if headers:
                return headers
            else:
                print(f"⚠️ Aucun en-tête valide trouvé dans la feuille '{sheet_name}'.")
                return []
        else:
            print(f"⚠️ La feuille '{sheet_name}' ne contient pas suffisamment de lignes ou de colonnes.")
            return []

    except Exception as e:
        print(f"❌ Erreur lors de la lecture de la feuille '{sheet_name}' : {e}")
        return []


def match_headers_with_filename(csv_file, excel_file):
    # Extraire le nom simplifié du fichier CSV pour identifier la feuille Excel correspondante
    simplified_name = extract_simplified_filename(os.path.basename(csv_file))

    if not simplified_name:
        print("❌ Impossible d'extraire un nom valide pour la feuille Excel.")
        return "Erreur"

    # Mapper le nom simplifié avec les feuilles connues
    sheet_name = extract_flux_sheet_names_reverse([simplified_name])[0]
    
    # Obtenir les en-têtes de la feuille Excel
    excel_headers = get_sheet_headers(excel_file, sheet_name)

    if not excel_headers:
        print("❌ Aucun en-tête trouvé dans le fichier Excel.")
    

    # Obtenir les en-têtes du fichier CSV
    csv_headers = get_csv_headers(os.path.dirname(csv_file)).get(os.path.basename(csv_file), [])

    if not csv_headers:
        print(f"❌ Aucun en-tête trouvé dans le fichier CSV {os.path.basename(csv_file)}.")
    # Comparaison des en-têtes
    if excel_headers == csv_headers:
        return "Correspondance exacte"
    elif all(header in csv_headers for header in excel_headers):
        return "Correspondance partielle"
    else:
        return "Aucune correspondance"
