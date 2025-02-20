import pandas as pd 
import os
import re
from src.entete import get_csv_headers
from src.mapping import extract_simplified_filename,extract_flux_sheet_names,extract_flux_sheet_names_reverse
#recupere les 3 colonnes( entete , type et longueur ) a partir du cahier des charges sous forme de liste 
def extract_headers_and_types(excel_file, sheet_name):
    try:
        # Map the sheet_name back using extract_flux_sheet_names_reverse
        sheet_name = extract_flux_sheet_names_reverse([sheet_name])[0]

        # Read the sheet after mapping the sheet name
        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
        headers_types = []
        
        # Parcours des lignes à partir de l'index 4 (5ᵉ ligne)
        for _, row in df.iloc[4:].iterrows():
            header = row.iloc[2]  # Colonne entete
            data_type = row.iloc[5]  # Colonne type
            Hlength = row.iloc[6]  # Colonne longueur
            
            if pd.isna(header) or header == "":  # Si vide, arrêter
                break
            
            headers_types.append((header, data_type, Hlength))
        
        return headers_types
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction des données du flux {sheet_name} : {e}")
        return []

def check_header_lengths(csv_file, excel_file):
    # Extract simplified filename to use as the sheet name
    sheet_name = extract_simplified_filename(os.path.basename(csv_file))

    # Use extract_flux_sheet_names to map the sheet name
    sheet_name = extract_flux_sheet_names([sheet_name])[0]

    headers_info = extract_headers_and_types(excel_file, sheet_name)
    filename = os.path.basename(csv_file)
    errors = []

    df = pd.read_csv(csv_file, sep=";" , low_memory=False)
    
    for header, _, max_length in headers_info:
        if header in df.columns:
            if not pd.isna(max_length) and isinstance(max_length, (int, float)):
                max_length = int(max_length) + 2 if max_length == 8 else int(max_length)
                max_actual_length = df[header].astype(str).apply(len).max()
                if max_actual_length > max_length:
                    errors.append(f"🚨 Colonne '{header}': valeur max {max_actual_length} dépasse la limite {max_length}")
    
    if errors:
        print(f"❌ Problèmes détectés de longueur dans le fichier '{filename}':")
        
    else:
        #print(f"✅ Aucune erreur détectée dans le fichier '{filename}'")
        return ""
    return {filename: errors} 

def check_header_type(csv_file, excel_file):
    # Extraire le nom simplifié du fichier CSV pour obtenir le bon sheet_name
    sheet_name = extract_simplified_filename(os.path.basename(csv_file))

    # Mapper le nom du sheet_name via extract_flux_sheet_names
    sheet_name = extract_flux_sheet_names([sheet_name])[0]

    headers_info = extract_headers_and_types(excel_file, sheet_name)
    filename = os.path.basename(csv_file)
    errors = set()  # Utilisation d'un set pour éviter les doublons

    df = pd.read_csv(csv_file, sep=";", dtype=str)  # Lire en tant que chaînes pour éviter des erreurs

    # Définition des types attendus sous forme d'expressions régulières
    type_mapping = {
        "NUMBER": r"^[A-Za-z0-9-]+$",             
        "Numérique": r"^\d+\.\d+$",      
        "Alphanumérique": r"^[A-Za-z0-9-]+$",  
        "Alpha Numérique": r"^[A-Za-z0-9-]+$", 
        "Date aaaammjj": r"^\d{8}$",    
        "Booléen": r"^(0|1)$" 
    }

    for header, expected_type, _ in headers_info:
        if header in df.columns:
            column_values = df[header].dropna().astype(str)  # Convertir en chaînes

            # Vérifier si le type attendu existe dans le mapping
            if expected_type and expected_type.upper() in type_mapping:
                pattern = type_mapping[expected_type.upper()]

                # Vérifier si toutes les valeurs respectent le format attendu
                invalid_values = [val for val in column_values if not re.match(pattern, val)]

                if invalid_values:
                    errors.add(f"🚨 Colonne '{header}': type attendu '{expected_type}', mais certaines valeurs ne respectent pas le format")

    if errors:
        print(f"❌ Problèmes de type détectés dans le fichier '{filename}':")
        for error in errors:
            print(f"   - {error}")
        return {filename: list(errors)}
    else:
        #print(f"✅ Aucune erreur de type détectée dans le fichier '{filename}'")
        return ""
    


