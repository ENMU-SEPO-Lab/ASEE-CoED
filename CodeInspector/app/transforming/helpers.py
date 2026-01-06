from pathlib import Path
from datetime import datetime

def check_date() -> str:
    
    # get the current date and time
    current_datetime = datetime.now()
    return current_datetime.strftime("%Y-%m-%d_%H-%M-%S")  # Format to avoid invalid characters in file names

def create_grading_dir(dir_path: Path | str):
    
    grading_dir_path = Path(dir_path)
    grading_dir_path.mkdir(exist_ok=True)
    
def create_grading_rep_file_name(dir_path: Path | str, date: str) -> Path:
    
    return Path(dir_path) / f"{date}.txt"
