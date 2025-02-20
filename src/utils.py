import os
import pandas as pd


def load_sheets(excel_file):
    """Charge toutes les feuilles du fichier Excel sous forme de dictionnaire."""
    try:
        return pd.read_excel(excel_file, sheet_name=None, engine='openpyxl')
    except FileNotFoundError:
        print(f"Erreur : Le fichier {excel_file} est introuvable.")
        exit()


#
# def get_flux_names_from_excel(excel_file, sheet_name):
#     """
#     Extrait les noms de flux depuis une feuille Excel.
#     Chaque nom est supposé se trouver dans une colonne spécifique (par exemple : 'NomFlux').
#     """
#     try:
#         # Charger la feuille Excel en DataFrame
#         df = pd.read_excel(excel_file, sheet_name=sheet_name)
#
#         # Extraire la colonne contenant les noms de flux (ajuste si nécessaire)
#         flux_names = df['NomFlux'].dropna().tolist()  # Colonne 'NomFlux' à adapter si différent
#         return flux_names
#     except Exception as e:
#         print(f"Erreur lors de la lecture du fichier Excel : {e}")
#         return []
#
# def find_matching_csv_files(flux_names, csv_folder):
#     """
#     Cherche les fichiers CSV correspondant aux noms de flux extraits de l'Excel.
#     Retourne un dictionnaire avec les noms de flux et leurs chemins complets.
#     """
#     mapping = {}
#
#     # Parcourir le dossier CSV
#     for filename in os.listdir(csv_folder):
#         if filename.endswith(".csv"):
#             # Chercher un nom de flux correspondant dans le fichier CSV
#             for flux_name in flux_names:
#                 if flux_name in filename:
#                     filepath = os.path.abspath(os.path.join(csv_folder, filename))
#                     mapping[flux_name] = filepath
#
#     return mapping
