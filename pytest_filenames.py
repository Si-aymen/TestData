import os
import pytest
import shutil
import re
from datetime import datetime
from test_filenames import get_ent_number, get_ent_directory, extract_latest_date, FILENAME_PATTERN

def test_get_ent_number():
    assert get_ent_number("ENT-12_OCIANE_RC2_20220101_FLUX_Q_20230101.csv") == "12"
    assert get_ent_number("OCIANE_RC2_20220101_FLUX_Q_20230101.csv") is None
    assert get_ent_number("ENT-5_OCIANE_RC2_20220101_FLUX_Q_20230101.csv") == "5"

def test_get_ent_directory():
    base_dir = "test_dir"
    assert get_ent_directory(base_dir, "ENT-12_file.csv") == os.path.join(base_dir, "ENT12")
    assert get_ent_directory(base_dir, "file.csv") == os.path.join(base_dir, "NO_ENT")

def test_extract_latest_date():
    assert extract_latest_date("20220101_20230101") == "20230101"
    assert extract_latest_date("20220101") == "20220101"
    assert extract_latest_date("20220101_20220102_20220103") == "20220103"

def test_filename_pattern():
    valid_filename = "ENT-12_OCIANE_RC2_20220101_FLUX_Q_20230101.csv"
    invalid_filename = "OCIANE_20220101_FLUX_20230101.txt"
    assert FILENAME_PATTERN.match(valid_filename)
    assert not FILENAME_PATTERN.match(invalid_filename)

@pytest.fixture
def setup_test_files(tmp_path):
    test_file = tmp_path / "ENT-12_OCIANE_RC2_20220101_FLUX_Q_20230101.csv"
    test_file.write_text("dummy content")
    return test_file

def test_file_movement(setup_test_files, tmp_path):
    src_file = setup_test_files
    dest_dir = tmp_path / "Q_FILES" / "ENT12"
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(src_file, dest_dir / src_file.name)
    assert (dest_dir / src_file.name).exists()
