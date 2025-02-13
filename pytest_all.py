import os
import pytest
import shutil
import pandas as pd
from unittest.mock import patch, MagicMock
from file_csv_process import (  # Replace 'file_csv_process' with the actual module name
    check_mandatory_columns,
    get_flux_name_from_filename,
    DATA_DIRS,
    REPORT_DIR,
    extract_mandatory_columns,
)
from test_filenames import (
    get_ent_number,
    get_ent_directory,
    extract_latest_date,
    FILENAME_PATTERN,
)

# Test for `get_ent_number`
def test_get_ent_number():
    assert get_ent_number("ENT-12_OCIANE_RC2_20220101_FLUX_Q_20230101.csv") == "12"
    assert get_ent_number("OCIANE_RC2_20220101_FLUX_Q_20230101.csv") is None
    assert get_ent_number("ENT-5_OCIANE_RC2_20220101_FLUX_Q_20230101.csv") == "5"

# Test for `get_ent_directory`
def test_get_ent_directory():
    base_dir = "test_dir"
    assert get_ent_directory(base_dir, "ENT-12_file.csv") == os.path.join(base_dir, "ENT12")
    assert get_ent_directory(base_dir, "file.csv") == os.path.join(base_dir, "NO_ENT")

# Test for `extract_latest_date`
def test_extract_latest_date():
    assert extract_latest_date("20220101_20230101") == "20230101"
    assert extract_latest_date("20220101") == "20220101"
    assert extract_latest_date("20220101_20220102_20220103") == "20220103"

# Test for `FILENAME_PATTERN`
def test_filename_pattern():
    valid_filename = "ENT-12_OCIANE_RC2_20220101_FLUX_Q_20230101.csv"
    invalid_filename = "OCIANE_20220101_FLUX_20230101.txt"
    assert FILENAME_PATTERN.match(valid_filename)
    assert not FILENAME_PATTERN.match(invalid_filename)

# Fixture to set up test files
@pytest.fixture
def setup_test_files(tmp_path):
    test_file = tmp_path / "ENT-12_OCIANE_RC2_20220101_FLUX_Q_20230101.csv"
    test_file.write_text("dummy content")
    return test_file

# Test for file movement logic
def test_file_movement(setup_test_files, tmp_path):
    src_file = setup_test_files
    dest_dir = tmp_path / "Q_FILES" / "ENT12"
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(src_file, dest_dir / src_file.name)
    assert (dest_dir / src_file.name).exists()
    # Restore the file after the test
    shutil.move(dest_dir / src_file.name, src_file)

# Fixture to set up test directories
@pytest.fixture(autouse=True)
def setup_test_directories(tmp_path):
    """
    Set up temporary directories for testing.
    """
    from file_csv_process import DATA_DIRS, REPORT_DIR  # Import global variables here

    # Save original values
    original_data_dirs = DATA_DIRS.copy() if isinstance(DATA_DIRS, list) else DATA_DIRS
    original_report_dir = REPORT_DIR

    # Create temporary directories
    data_dir = tmp_path / "data"
    m_files_dir = data_dir / "M_FILES"
    q_files_dir = data_dir / "Q_FILES"
    report_dir = tmp_path / "Mandatory_columns_failure"

    m_files_dir.mkdir(parents=True, exist_ok=True)
    q_files_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(exist_ok=True)

    # Update global variables
    DATA_DIRS = [str(m_files_dir), str(q_files_dir)]
    REPORT_DIR = str(report_dir)

    yield tmp_path

    # Restore original values
    DATA_DIRS = original_data_dirs
    REPORT_DIR = original_report_dir

    # Clean up temporary directories
    shutil.rmtree(tmp_path, ignore_errors=True)

# Test reading Excel file and extracting mandatory columns
def test_read_excel_file(setup_test_directories):
    mock_excel_path = setup_test_directories / "mock_cahier.xlsx"
    mock_excel_data = {
        "FLUX_A": pd.DataFrame({
            "Mandatory": ["Col1", "Col2"],  # Two elements
            "Optional": ["Col3", None]      # Match the length with "Mandatory"
        }),
        "FLUX_B": pd.DataFrame({
            "Mandatory": ["Col4", "Col5"]   # Two elements
        }),
    }

    # Write the mock Excel file
    with pd.ExcelWriter(mock_excel_path) as writer:
        for sheet_name, df in mock_excel_data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    # Define a mock implementation for extract_mandatory_columns
    def mock_extract_mandatory_columns(df):
        return df["Mandatory"].tolist()

    # Patch the function and verify the behavior
    with patch("file_csv_process.extract_mandatory_columns", side_effect=mock_extract_mandatory_columns):
        cahier_des_charges = pd.read_excel(mock_excel_path, sheet_name=None)
        mandatory_columns_by_flux = {
            sheet_name.strip().upper(): extract_mandatory_columns(df) for sheet_name, df in cahier_des_charges.items()
        }

    # Assert the expected result
    assert mandatory_columns_by_flux == {"FLUX_A": ["Col1", "Col2"], "FLUX_B": ["Col4", "Col5"]}
# Test identifying flux names from filenames
def test_get_flux_name_from_filename():
    flux_names = ["FLUX_A", "FLUX_B"]
    test_cases = [
        ("file_FLUX_A.csv", "FLUX_A"),
        ("file_FLUX_B.csv", "FLUX_B"),
        ("file_flux_a.csv", "FLUX_A"),  # Case-insensitive match
        ("file_flux_b.csv", "FLUX_B"),  # Case-insensitive match
        ("file_unknown.csv", None),     # No match
    ]

    for filename, expected_flux in test_cases:
        result = get_flux_name_from_filename(filename, flux_names)
        assert result == expected_flux

# Test checking mandatory columns in a CSV file (missing columns)
def check_mandatory_columns(file_path, flux_name, failed_files):
    """
    Vérifie si le fichier CSV contient toutes les colonnes obligatoires du flux donné et affiche les résultats.
    """
    print(f"\n📂 Traitement du fichier : {file_path}")
    try:
        df = pd.read_csv(file_path, sep=";", encoding="utf-8", low_memory=False)
    except Exception as e:
        print(f"❌ {file_path} : Erreur lors de la lecture -> {e}")
        failed_files.append(file_path)
        shutil.move(file_path, os.path.join(REPORT_DIR, os.path.basename(file_path)))
        return

    # Get the list of mandatory columns for the given flux
    mandatory_columns = mandatory_columns_by_flux.get(flux_name, [])

    # Check for missing columns
    missing_columns = [col for col in mandatory_columns if col not in df.columns]
    if missing_columns:
        print(f"❌ {file_path} : Colonnes manquantes pour {flux_name} -> {missing_columns}")
        failed_files.append(file_path)
        shutil.move(file_path, os.path.join(REPORT_DIR, os.path.basename(file_path)))
    else:
        print(f"✅ {file_path} : Toutes les colonnes obligatoires sont présentes pour {flux_name}")
# Test checking mandatory columns in a CSV file (all present)
def test_check_mandatory_columns_all_present(setup_test_directories):
    csv_file_path = setup_test_directories / "test_file.csv"
    pd.DataFrame({"Col1": [1], "Col2": [2], "Col3": [3]}).to_csv(csv_file_path, sep=";", encoding="utf-8", index=False)

    mandatory_columns_by_flux = {"FLUX_A": ["Col1", "Col2", "Col3"]}
    failed_files = []

    # Pass mandatory_columns_by_flux explicitly
    check_mandatory_columns(str(csv_file_path), "FLUX_A", failed_files, mandatory_columns_by_flux)

    assert os.path.exists(csv_file_path)
    assert str(csv_file_path) not in failed_files
    
# Test generating failure report
def test_generate_failure_report(setup_test_directories):
    report_file_path = os.path.join(REPORT_DIR, "failure_report.txt")
    failed_files = [str(setup_test_directories / "file1.csv"), str(setup_test_directories / "file2.csv")]

    with open(report_file_path, "w", encoding="utf-8") as report_file:
        report_file.write("\n".join(failed_files))

    with open(report_file_path, "r", encoding="utf-8") as report_file:
        content = report_file.read().splitlines()

    assert content == failed_files

# Test processing an empty data directory
def test_process_empty_data_directory(setup_test_directories):
    # Ensure DATA_DIRS are empty before the test
    for data_dir in DATA_DIRS:
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)  # Remove any existing contents
        os.makedirs(data_dir, exist_ok=True)  # Recreate the directory

    # Verify that the directories are empty
    for data_dir in DATA_DIRS:
        assert len(os.listdir(data_dir)) == 0, f"Directory {data_dir} is not empty."

    # Mock the main logic to ensure no warnings or errors are raised
    with patch("file_csv_process.check_mandatory_columns") as mock_check:
        for data_dir in DATA_DIRS:
            if not os.path.exists(data_dir):
                print(f"❌ Le dossier {data_dir} n'existe pas.")
                continue

            for ent_folder in os.listdir(data_dir):
                ent_path = os.path.join(data_dir, ent_folder)
                if not os.path.isdir(ent_path):
                    continue

                csv_files = [f for f in os.listdir(ent_path) if f.endswith(".csv")]
                if not csv_files:
                    print(f"⚠️ Aucun fichier CSV trouvé dans {ent_path}.")
                else:
                    for filename in csv_files:
                        file_path = os.path.join(ent_path, filename)
                        mock_check.assert_not_called()