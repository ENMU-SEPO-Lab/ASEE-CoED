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
    cs_csv_path = Path(cs_csv_path)
    pmd_csv_path = Path(pmd_csv_path)
    
    _ensure_csv_exists(cs_csv_path)
    _ensure_csv_exists(pmd_csv_path)
    
    cs_violations = processed_submission.cs_processed
    pmd_violations = processed_submission.pmd_processed
    
    _update_csv(cs_violations, cs_csv_path, student_email)
    _update_csv(pmd_violations, pmd_csv_path, student_email)

def _update_csv(violations: ProcessedViolations, csv_path: Path, email: str) -> None:
    df = _load_and_prep_data(csv_path, email)
    
    type_counts = violations.get_type_counts_in_submission()
    
    for type_name, type_count in type_counts.items():
        _ensure_column(df, type_name)
        df.loc[email, type_name] += type_count
                    
    df.to_csv(csv_path, index=True, index_label="email")
                
def _ensure_column(df, column_name: str) -> None:
    if column_name not in df.columns:
        df[column_name] = 0

def _ensure_csv_exists(csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not csv_path.is_file():
        csv_path.write_text("email\n", encoding="utf-8")

def _load_and_prep_data(csv_path: Path, email: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, index_col="email")
    if email not in df.index:
        # df.loc[email] = 0 doesn't work here, because email is now the index. So the df is technically empty
        df = df.reindex(df.index.union([email]))
        
    df.fillna(0, inplace=True)
    
    return df
