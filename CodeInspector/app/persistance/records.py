from app.infrastructure.models import SubmissionData
from pathlib import Path
import json

def update_json (
    submission_data: SubmissionData,
    records_file_path: Path | str
) -> None:
    """updates the records.json file containing submission metrics data
    File existence and format check needs to be made before calling this

    Args:
        submission_data (SubmissionData): submission data
        records_file_path (Path | str): the json file path
    """
    file_path = Path(records_file_path)
    upload_dir_name = submission_data.upload_dir_name
    student_email = submission_data.email
    loc = submission_data.loc
    weighted_error_density = submission_data.overall_weighted_error
    top_cs_errors = submission_data.top_cs_error_types
    top_pmd_errors = submission_data.top_pmd_error_types
    
    try:
        with open(file_path, 'r+') as file:
            # load json file
            content = file.read().strip()
            if content:
                data = json.loads(content)
            else:
                data = {}
                            
            if not upload_dir_name:
                print("No upload directory name.")
                return
            
            if upload_dir_name not in data:
                data[upload_dir_name] = {}
            
            assignment_data = data[upload_dir_name]

            if student_email not in assignment_data:
                assignment_data[student_email] = []
                
            student_data = assignment_data[student_email]
            submission_count = len(student_data) + 1
            new_submission = {
                "counter": submission_count,
                "loc": loc,
                "error density": weighted_error_density,
                "top_cs_errors": top_cs_errors,
                "top_pmd_errors": top_pmd_errors
            }
                
            student_data.append(new_submission)
            
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()
            print("JSON records updated successfully.")
     
    except Exception as e:
        print(e)
        print("Failed to update json")
