import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL_FILE = os.path.join(BASE_DIR, 'data', 'CahierdeschargesReportingFluxStandard-V24.6.0.xlsx')
CSV_FOLDER = os.path.join(BASE_DIR, 'flux')  # Dossier contenant les fichiers CSV