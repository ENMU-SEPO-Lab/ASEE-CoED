from app.infrastructure.models import CombinedParsedViolations, ViolationReport
from pathlib import Path
from datetime import datetime
import os

def build_violation_report(student_email: str, check_date: str, loc: int, parsed: CombinedParsedViolations) -> ViolationReport:
    
    report = ViolationReport(
        system = "CodeInspector",
        student_name = student_email,
        check_date = check_date,
        lines_of_code = loc,
        violations = parsed
    )
    
    return report

def check_date() -> str:
    
    # get the current date and time
    current_datetime = datetime.now()
    return current_datetime.strftime("%Y-%m-%d_%H-%M-%S")  # Format to avoid invalid characters in file names

def create_grading_dir(dir_path: Path | str):
    
    grading_dir_path = Path(dir_path)
    os.makedirs(grading_dir_path, exist_ok=True)
    
def create_grading_rep_file_name(dir_path: Path | str, date: str) -> str:
    
    grade_report_dir = Path(dir_path)
    return os.path.join(grade_report_dir, f"{date}.txt")
