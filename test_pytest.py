import pytest
from src.mapping import extract_flux_sheet_names , extract_simplified_filename , load_naming_constraints , generate_mapping , controle_date , extract_mandatory_columns
from datetime import datetime
import os
from unittest.mock import patch, MagicMock
import pandas as pd
from io import BytesIO

def test_extract_flux_sheet_names():
    sheet_names = ["CONTRATSCOLLECTIFS", "ADHESIONSINDIVIDUELLES", "REFERENTIEL_GROUPES", "DECLARATION_HONORAIRES", "AUTRE_FEUILLE"]
    expected_output = ["CONTRATCOLLECTIF_STOCK", "ADHESIONSINDIVIDUELLES_STOCK", "REFERENTIEL_GROUPE", "HONORAIRES", "AUTRE_FEUILLE"]
    assert extract_flux_sheet_names(sheet_names) == expected_output


@pytest.mark.parametrize("filename, expected", [
    ("Client_N°Flux_MOD1_HONORAIRES_FREQUENCE_20240101.csv", "HONORAIRES"),
    ("OCIANE_RC2_1_HONORAIRES_Q_20230101.csv", "HONORAIRES"),
    ("OCIANE_RC2_1_FORMULES_REMBOURSEMENTS_20231201.csv", "FORMULES_REMBOURSEMENTS"),
    ("INVALID_FILENAME.csv", "")
])
def test_extract_simplified_filename(filename, expected):
    assert extract_simplified_filename(filename) == expected

def test_load_naming_constraints():
    # Création d'un fichier Excel simulé en mémoire
    data = {
        "A": ["Autre Colonne"] * 12,  # Colonne fictive
        "B": [None] * 11 + [
            "Client_N°Flux_CONTRATCOLLECTIF_STOCK_FREQUENCE_DATEEXECUTION",
            "Client_N°Flux_ADHESIONSINDIVIDUELLES_STOCK_FREQUENCE_DATEEXECUTION",
            "Client_N°Flux_ENCAISSEMENTS_FREQUENCE[_&ModeForce_&DateDebutModeForce&DateFinModeForce]_DATEEXECUTION"
        ] 
    }
    df = pd.DataFrame(data)
    
    excel_file = BytesIO()
    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name="Notice", index=False)
    
    excel_file.seek(0)
    
    # Exécution de la fonction et vérification des résultats
    result = load_naming_constraints(excel_file, sheet_name="Notice")
    expected = ["CONTRATCOLLECTIF_STOCK", "ADHESIONSINDIVIDUELLES_STOCK", "ENCAISSEMENTS"]
    assert result == expected, f"Résultat inattendu : {result}"


@pytest.fixture
def setup_test_env(tmp_path):
    csv_folder = tmp_path / "data"
    csv_folder.mkdir()

    valid_csv = csv_folder / "OCIANE_RC2_1_HONORAIRES_Q_20250116.csv"
    invalid_csv = csv_folder / "INVALID_FILENAME.csv"
    
    valid_csv.write_text("Sample data")
    invalid_csv.write_text("Sample data")

    return str(csv_folder)

@patch("src.mapping.load_naming_constraints", return_value=["HONORAIRES"])
@patch("src.mapping.extract_flux_sheet_names", return_value=["HONORAIRES"])
@patch("src.mapping.controle_date", return_value=True)
def test_generate_mapping(mock_naming, mock_flux, mock_date, setup_test_env):
    csv_folder = setup_test_env
    notices_file = "data\Cahier des charges - Reporting Flux Standard - V25.1.0 1.xlsx"
    date_test = datetime.strptime("20250116", "%Y%m%d").date()

    valid_files = generate_mapping(csv_folder, notices_file, date_test)

    assert len(valid_files) == 1
    assert "HONORAIRES" in valid_files[0]


@pytest.mark.parametrize("filename, date_test, expected", [
    ("OCIANE_RC2_1_HONORAIRES_Q_20250116.csv", datetime.strptime("20250116", "%Y%m%d").date(), True),
    ("OCIANE_RC2_1_HONORAIRES_Q_20240116.csv", datetime.strptime("20250116", "%Y%m%d").date(), False),
    ("INVALID_FILENAME.csv", datetime.strptime("20250116", "%Y%m%d").date(), False)
])
def test_controle_date(tmp_path, filename, date_test, expected):
    file_path = tmp_path / filename
    file_path.write_text("Sample content")
    assert controle_date(str(file_path), date_test) == expected

def test_load_naming_constraints():
    # Création d'un fichier Excel simulé en mémoire
    data = {
        "A": ["Autre Colonne"] * 12,  # Colonne fictive
        "B": [None] * 11 + [
            "Client_N°Flux_CONTRATCOLLECTIF_STOCK_FREQUENCE_DATEEXECUTION"
            
        ]  # si je mets plus qu'un flux -> erreur ??????
    }
    df = pd.DataFrame(data)
    
    excel_file = BytesIO()
    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name="Notice", index=False)
    
    excel_file.seek(0)
    
    # Exécution de la fonction et vérification des résultats
    result = load_naming_constraints(excel_file, sheet_name="Notice")
    expected = ["CONTRATCOLLECTIF_STOCK"]
    assert result == expected, f"Résultat inattendu : {result}"



    
