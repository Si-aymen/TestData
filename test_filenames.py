import os
import re
import shutil
import pytest

# Define the updated regex pattern for the filenames
FILENAME_PATTERN = re.compile(r'(?:^ENT-(?:[1-9]|[1][0-9]|[2][0-9]|30))(?:_MOD1)?_OCIANE_RC2_\d+_[A-Z_]+(?:_[A-Z]+)?(?:_\d{8})*(?:_\d{8})*\.csv$')

# Directory containing the files to test
TEST_DIR = "data"  # Change this to the path of your 'data' folder
NO_ENT_DIR = os.path.join(TEST_DIR, "NO_ENT")
NO_MATCH_DIR = os.path.join(TEST_DIR, "NO_MATCH")

# Ensure NO_ENT and NO_MATCH directories exist
os.makedirs(NO_ENT_DIR, exist_ok=True)
os.makedirs(NO_MATCH_DIR, exist_ok=True)

# Function to get the destination directory based on ENT number
def get_ent_directory(filename):
    match = re.match(r'^ENT-(\d+)', filename)
    if match:
        ent_number = match.group(1)
        return os.path.join(TEST_DIR, f"ENT{ent_number}")
    return None

def test_filename_format():
    passed_count = 0

    # Iterate over all files in the directory
    for filename in os.listdir(TEST_DIR):
        file_path = os.path.join(TEST_DIR, filename)

        # Skip directories, only process files
        if not os.path.isfile(file_path):
            continue

        # Check if the filename matches the expected pattern
        if filename.startswith("ENT-") and FILENAME_PATTERN.match(filename):
            dest_dir = get_ent_directory(filename)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)
                shutil.move(file_path, os.path.join(dest_dir, filename))
                passed_count += 1
                print(f"Filename '{filename}' passed the test and was moved to '{dest_dir}' folder.")
        elif FILENAME_PATTERN.match(filename):
            # Move files that match the pattern but do not start with 'ENT-' to NO_ENT folder
            shutil.move(file_path, os.path.join(NO_ENT_DIR, filename))
            print(f"Filename '{filename}' matches the pattern but does not start with 'ENT-', moved to 'NO_ENT' folder.")
        else:
            # Move files that do not match the pattern to NO_MATCH folder
            shutil.move(file_path, os.path.join(NO_MATCH_DIR, filename))
            print(f"Filename '{filename}' does not match the pattern and was moved to 'NO_MATCH' folder.")

    # Assert that at least one file passed the test
    assert passed_count > 0, "No files passed the test."

# Run the test using pytest
if __name__ == "__main__":
    pytest.main([__file__])
