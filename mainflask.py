from flask import Flask, jsonify, request
import os
import shutil
import re
import json
from datetime import datetime
from src.mapping import generate_mapping, check_mandatory_columns, extract_simplified_filename
from src.entete import match_headers_with_filename
from longueur_et_type import check_header_lengths, check_header_type

app = Flask(__name__)

CSV_FOLDER = "data"
PROCESSED_FOLDER = "data/PROCESSED"
INVALID_FOLDER = "data/INVALID"
RESULTS_FOLDER = "data/RESULTS"

os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(INVALID_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

def process_files():
    excel_files = [file for file in os.listdir(CSV_FOLDER) if file.endswith(".xlsx") and "Cahier des charges" in file]
    if not excel_files:
        return {"error": "Aucun fichier 'Cahier des charges' trouvé."}, 400

    EXCEL_FILE = os.path.join(CSV_FOLDER, excel_files[0])
    date_test = datetime.strptime("20250219", "%Y%m%d").date()
    ent_pattern = re.compile(r"(ENT-\d+)")

    error_counts = {}
    flux_test_total = 0
    flux_test_valid = 0
    flux_test_invalid = 0
    nbr_erreurs_mandatory_columns = 0
    nbr_erreurs_length = 0
    nbr_erreurs_type = 0
    nbr_erreurs_entete = 0

    try:
        valid_csv_files = generate_mapping(CSV_FOLDER, EXCEL_FILE, date_test)
        if valid_csv_files:
            for file in valid_csv_files:
                flux_test_total += 1
                filename = os.path.basename(file)
                match_result = match_headers_with_filename(file, EXCEL_FILE)

                error_types = {
                    "mandatory_columns": 0,
                    "length": 0,
                    "type": 0,
                    "entete": 1 if match_result not in ["Correspondance exacte", "Correspondance partielle"] else 0
                }

                mandatory_columns_errors = check_mandatory_columns(file, EXCEL_FILE)
                length_errors = check_header_lengths(file, EXCEL_FILE)
                type_errors = check_header_type(file, EXCEL_FILE)

                error_types["mandatory_columns"] = len(mandatory_columns_errors)
                error_types["length"] = len(length_errors)
                error_types["type"] = len(type_errors)
                error_types["entete"] = 1 if match_result not in ["Correspondance exacte", "Correspondance partielle"] else 0

                nbr_erreurs_mandatory_columns += len(mandatory_columns_errors)
                nbr_erreurs_length += len(length_errors)
                nbr_erreurs_type += len(type_errors)
                nbr_erreurs_entete += error_types["entete"]

                if any(error_types.values()):
                    error_counts[filename] = error_types
                    flux_test_invalid += 1
                    simplified_name = extract_simplified_filename(filename)
                    type_folder = "Q" if "_Q_" in filename else "M" if "_M_" in filename else "Other"
                    destination_folder = os.path.join(INVALID_FOLDER, simplified_name, type_folder)
                else:
                    flux_test_valid += 1
                    base_folder = os.path.join(PROCESSED_FOLDER, "Q" if "_Q_" in filename else "M" if "_M_" in filename else "NO Match")
                    match = ent_pattern.search(filename)
                    ent_folder = match.group(1) if match else "Other"
                    destination_folder = os.path.join(base_folder, ent_folder)
                
                os.makedirs(destination_folder, exist_ok=True)
                shutil.move(file, os.path.join(destination_folder, filename))

            results = {
                "files_with_errors": error_counts,
                "Summary": {
                    "flux_test_total": flux_test_total,
                    "flux_test_valid": flux_test_valid,
                    "flux_test_invalid": flux_test_invalid
                },
                "Errors": {
                    "nbr_erreurs_mandatory_columns": nbr_erreurs_mandatory_columns,
                    "nbr_erreurs_length": nbr_erreurs_length,
                    "nbr_erreurs_type": nbr_erreurs_type,
                    "nbr_erreurs_entete": nbr_erreurs_entete
                }
            }

            json_filename = f"results_{date_test.strftime('%Y%m%d')}.json"
            json_filepath = os.path.join(RESULTS_FOLDER, json_filename)
            with open(json_filepath, "w", encoding="utf-8") as json_file:
                json.dump(results, json_file, indent=4, ensure_ascii=False)
            
            return results if error_counts else {"message": "Aucun fichier avec des erreurs."}
        else:
            return {"error": "Aucun fichier CSV valide trouvé."}, 400
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/process", methods=["POST"])
def process_endpoint():
    result = process_files()
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
