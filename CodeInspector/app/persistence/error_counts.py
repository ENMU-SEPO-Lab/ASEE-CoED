from app.infrastructure.models import (
    ProcessedSubmission,
    ProcessedViolations,
)
from pathlib import Path
import pandas as pd

def update_csv_files(
    processed_submission: ProcessedSubmission,
    cs_csv_path: Path | str,
    pmd_csv_path: Path | str,
    student_email: str
) -> None:
    """updates the csv file recording all violations along with their frequency for each student,
    across all submission

    Args:
        processed_submission (ProcessedSubmission): processed error reports data
        cs_csv_path (Path | str): path to CheckStyle csv file
        pmd_csv_path (Path | str): path to PMD csv file
        student_email (str): student email
    """
    cs_csv_path = Path(cs_csv_path)
    pmd_csv_path = Path(pmd_csv_path)
    
    _ensure_csv_exists(cs_csv_path)
    _ensure_csv_exists(pmd_csv_path)
    
    cs_violations = processed_submission.cs_processed
    pmd_violations = processed_submission.pmd_processed
    
    _update_csv(cs_violations, cs_csv_path, student_email)
    _update_csv(pmd_violations, pmd_csv_path, student_email)

def _update_csv(violations: ProcessedViolations, csv_path: Path, email: str) -> None:
    """updates the contents of the csv file at the given path

    Args:
        violations (ProcessedViolations): the violation data
        csv_path (Path): path of csv
        email (str): email of student
    """
    df = _load_and_prep_data(csv_path, email)
    
    type_counts = violations.get_type_counts_in_submission()
    
    for type_name, type_count in type_counts.items():
        _ensure_column(df, type_name)
        df.loc[email, type_name] += type_count
                    
    df.to_csv(csv_path, index=True, index_label="email")
                
def _ensure_column(df, column_name: str) -> None:
    """helper method to either increment the counter of a certain error type,
    or create a new column for it, initializing all row counter values as 0

    Args:
        df (_type_): the dataframe
        column_name (str): the vioation type encountered
    """
    if column_name not in df.columns:
        df[column_name] = 0

def _ensure_csv_exists(csv_path: Path) -> None:
    """make sure the csv file exists. If not, it is created and initialized 
    with the email column

    Args:
        csv_path (Path): path of csv file
    """
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not csv_path.is_file():
        csv_path.write_text("email\n", encoding="utf-8")

def _load_and_prep_data(csv_path: Path, email: str) -> pd.DataFrame:
    """load the data of a csv file at the provided path, and set the email column as 
    index for easier handling. If the student email associated with the current submission
    does not exist yet, add anew row to the DataFrame for this student email

    Args:
        csv_path (Path): the csv path
        email (str): the student email

    Returns:
        pd.DataFrame: the loaded DataFrame
    """
    df = pd.read_csv(csv_path, index_col="email")
    if email not in df.index:
        # df.loc[email] = 0 doesn't work here, because email, the only column, is now the index. 
        # So the df is technically empty
        df = df.reindex(df.index.union([email]))
    
    # make sure all nan values are replaced with interger values = 0    
    df.fillna(0, inplace=True)
    
    return df
