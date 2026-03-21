import xml.etree.ElementTree as ET
from pathlib import Path

CODE_INSPECTOR = Path(__file__).resolve().parents[1] # .../CodeInspector/
ROOT = Path(__file__).resolve().parents[2] # .../ASEE-COED/

BUILD_XML_PATH = CODE_INSPECTOR / "build.xml"
CONFIG_DIR = CODE_INSPECTOR / "app/app_config"
XML_REPORT_DIR = CODE_INSPECTOR / "build/test_reports"
GRADE_REPORTS_DIR = CODE_INSPECTOR / "build/grade_reports"
RECORDS_DIR = CODE_INSPECTOR / "app/records"

CS_XML_FILE = XML_REPORT_DIR / "checkstyle.xml"
PMD_XML_FILE = XML_REPORT_DIR / "pmd.xml"
JUNIT_RESULT_FILE = XML_REPORT_DIR / "TEST-junit-vintage.xml"
GRADING_CONFIG_FILE = CONFIG_DIR / "grading_config.json"
RECORDS_JSON_FILE = RECORDS_DIR / "records.json"
WEIGHTED_DATA_CSV = RECORDS_DIR / "historical/weighted_data.csv"
CS_ERROR_DATA_CSV = RECORDS_DIR / "cs_errors.csv"
PMD_ERROR_DATA_CSV = RECORDS_DIR / "pmd_errors.csv"

def get_upload_dir_path() -> Path:
    """extract the name of the upload directory name from the build.xml file

    Raises:
        ValueError: if xml has unexpected format

    Returns:
        Path: path of build.xml
    """
    # load the build.xml file
    tree = ET.parse(BUILD_XML_PATH)
    root = tree.getroot()
    for property in root.findall("property"):
        if (property.get("name") == "src.dir"):
            location = property.get("location")
            if not location:
                break
            
            upload_dir_path = Path(location)
            if not upload_dir_path.is_absolute():
                return CODE_INSPECTOR / upload_dir_path
            return upload_dir_path
        
    raise ValueError("build.xml is missing: 'src.dir' property")
