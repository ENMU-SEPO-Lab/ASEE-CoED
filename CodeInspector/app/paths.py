from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1] # CodeInspector/
print (PROJECT_ROOT)

UPLOAD_DIR = PROJECT_ROOT / "Upload_here"
CONFIG_DIR = PROJECT_ROOT / "config"
XML_REPORT_DIR = PROJECT_ROOT / "build/test-reports"
GRADE_REPORTS_DIR = PROJECT_ROOT / "build/grade_reports"

CS_XML_FILE = XML_REPORT_DIR / "checkstyle-result.xml"
PMD_XML_FILE = XML_REPORT_DIR / "pmd.xml"
JUNIT_RESULT_FILE = XML_REPORT_DIR / "TEST-TestCardDescription.txt"
GRADING_CONFIG_FILE = CONFIG_DIR / "grading_config.json"

