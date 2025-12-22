from CodeInspector.app.infrastructure.models import CombinedParsedViolations, ViolationReport
from datetime import datetime
import os

def build_violation_report(student_name: str, check_date: str, loc: int, parsed: CombinedParsedViolations) -> ViolationReport:
    
    report = ViolationReport(
        student_name = student_name,
        check_date = check_date,
        lines_of_code = loc,
        violations = parsed
    )
    
    return report

def check_date() -> str:
    
    # get the current date and time
    current_datetime = datetime.now()
    return current_datetime.strftime("%Y-%m-%d_%H-%M-%S")  # Format to avoid invalid characters in file names

def create_grading_dir(dir_path: str):
    
    os.makedirs(dir_path, exist_ok=True)