from pathlib import Path
from pandas import DataFrame, read_csv
import json
import sys

def ensure_json_file(file_path: Path | str) -> None:
    """Creates a JSON file at the specified path whose root is an empty object if the file does 
    not already exist to record student submission data

    Args:
        file_path (Path | str): the file path
    """
    json_path = Path(file_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not json_path.exists():
        json_path.write_text("{}", encoding="utf-8")
        
def load_json(file_path: Path | str) -> dict:
    """Loads contents of JSON file. If root object is not a dict. A value error is raised

    Args:
        file_path (Path | str): the JSON file path

    Raises:
        ValueError: if JSON root object is not a dict 

    Returns:
        dict: JSON data
    """
    json_path = Path(file_path)
    with open(json_path, "r") as file:
        data = json.load(file)
        
    if not isinstance(data, dict):
        raise ValueError("records file must contain an object at top level", file=sys.stderr)
    return data

def check_for_weighted_data_csv(csv_path: Path | str) -> bool:
    """Check if the file for the path exists

    Args:
        csv_path (Path | str): the path

    Returns:
        bool: whether the file exists at the provided path
    """
    weighted_csv_path = Path(csv_path)
    return weighted_csv_path.exists()

def load_weighted_data_csv(csv_path: Path | str) -> DataFrame:
    """load csv data from the provided file into a pandas DataFrame

    Args:
        csv_path (Path | str): the path of the csv file

    Returns:
        DataFrame: the csv data
    """
    weighted_csv_path = Path(csv_path)
    return read_csv(weighted_csv_path, header=0)