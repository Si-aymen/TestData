import os
import re
import shutil

# Define regex pattern for filenames
FILENAME_PATTERN = re.compile(
    r'(?:(?:ENT-(?:[1-9]|[1][0-9]|[2][0-9]|30))_)?'  # Optional ENT-<number>_
    r'OCIANE_RC2_\d+_[A-Z_]+(?:_[A-Z]+)?'            # Match OCIANE_RC2_<number>_<uppercase_words>
    r'(?:_Q|_M)'                                      # Ensure it contains _Q or _M
    r'(?:_\d{8}){0,2}\.csv$'                         # Match optional _YYYYMMDD dates (0, 1, or 2 times) and .csv
)

# Directories
TEST_DIR = "data"
Q_DIR = os.path.join(TEST_DIR, "Q_FILES")  # Folder for _Q files
M_DIR = os.path.join(TEST_DIR, "M_FILES")  # Folder for _M files
NO_MATCH_DIR = os.path.join(TEST_DIR, "NO_MATCH")

# Ensure necessary directories exist
os.makedirs(Q_DIR, exist_ok=True)
os.makedirs(M_DIR, exist_ok=True)
os.makedirs(NO_MATCH_DIR, exist_ok=True)

# Function to get the ENT number from a filename
def get_ent_number(filename):
    match = re.match(r'^ENT-(\d+)', filename)
    return match.group(1) if match else None

# Function to get the destination directory based on ENT number
def get_ent_directory(base_dir, filename):
    ent_number = get_ent_number(filename)
    if ent_number:
        return os.path.join(base_dir, f"ENT{ent_number}")
    return os.path.join(base_dir, "NO_ENT")  # Default for non-ENT files

# File classification logic
for filename in os.listdir(TEST_DIR):
    file_path = os.path.join(TEST_DIR, filename)

    # Skip directories, only process files
    if not os.path.isfile(file_path):
        continue

    ent_number = get_ent_number(filename)

    # Step 1: Check if the filename contains "_Q" or "_M"
    if "_Q" in filename:
        dest_dir = get_ent_directory(Q_DIR, filename)  # Place in Q_FILES/ENT<number>
        os.makedirs(dest_dir, exist_ok=True)
        shutil.move(file_path, os.path.join(dest_dir, filename))
        print(f"Filename '{filename}' contains '_Q' and was moved to '{dest_dir}' folder.")

    elif "_M" in filename:
        dest_dir = get_ent_directory(M_DIR, filename)  # Place in M_FILES/ENT<number>
        os.makedirs(dest_dir, exist_ok=True)
        shutil.move(file_path, os.path.join(dest_dir, filename))
        print(f"Filename '{filename}' contains '_M' and was moved to '{dest_dir}' folder.")

    # Step 2: If it starts with "ENT-", move to respective ENT folder in TEST_DIR
    elif ent_number and FILENAME_PATTERN.match(filename):
        dest_dir = get_ent_directory(TEST_DIR, filename)
        os.makedirs(dest_dir, exist_ok=True)
        shutil.move(file_path, os.path.join(dest_dir, filename))
        print(f"Filename '{filename}' was moved to '{dest_dir}' folder.")

    # Step 3: If it does not match any pattern, move to NO_MATCH
    else:
        shutil.move(file_path, os.path.join(NO_MATCH_DIR, filename))
        print(f"Filename '{filename}' does not match the pattern and was moved to 'NO_MATCH' folder.")
