from pathlib import Path
from datetime import datetime

def check_date() -> str:
    """get the current date and time and format it

    Returns:
        str: formatted date and time info
    """
    current_datetime = datetime.now()
    return current_datetime.strftime("%Y-%m-%d_%H-%M-%S")  # Format to avoid invalid characters in file names

def create_grading_dir(dir_path: Path | str):
    """creates the directory where the grading report, etc. Will be stored

    Args:
        dir_path (Path | str): the desired path of the dir
    """
    grading_dir_path = Path(dir_path)
    grading_dir_path.mkdir(exist_ok=True)
    
def create_grading_rep_file_name(dir_path: Path | str, date: str) -> Path:
    """assembles the path for the creation of the .txt grade report file

    Args:
        dir_path (Path | str): the grading dir path
        date (str): the date information of the submission

    Returns:
        Path: assembled path
    """
    return Path(dir_path) / f"{date}.txt"
