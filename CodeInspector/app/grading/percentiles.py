from scipy.stats import percentileofscore
from pathlib import Path
import pandas as pd

def get_global_percentile_score(
    cs_error_density: float ,
    pmd_error_density: float, 
    overall_error_density: float, 
    data: pd.DataFrame,
    grading_config: dict
) -> tuple[float, float, float]:
    """Calculates the percentile scores of the computed error densities of the analyzed file in relation
    to the global dataset (weighted_data.csv)

    Args:
        checkStyle_error_density (float): checkstyle error density of the file
        pmd_error_density (float): pmd error density of the file
        total_error_density (float): overall error density of the file
        data (pd.DataFrame): dataframe from weighted_data.csv file
        grading_config (dict): grading_config.json contents

    Returns:
        tuple[float, float, float]: [cs percentile score, pmd percentile score, overall percentile score]
    """
    cs_data = data["cs_density"].to_numpy()
    pmd_data = data["pmd_density"].to_numpy()
    total_data = data["total_density"].to_numpy()
    
    precision_perc = grading_config.get("system_decimal_precision", {}).get("percentile_score", 2)
    
    percentile_checkstyle = float(round(percentileofscore(cs_data, cs_error_density, kind="rank"), precision_perc))
    percentile_pmd = float(round(percentileofscore(pmd_data, pmd_error_density, kind="rank"), precision_perc))
    percentile_overall = float(round(percentileofscore(total_data, overall_error_density, kind='rank'), precision_perc))
    
    return percentile_checkstyle, percentile_pmd, percentile_overall

def compare_score_with_self_global(
    student_email: str, 
    error_density: float, 
    upload_dir: Path | str, 
    records: dict,
    grading_config: dict
) -> tuple[float, float, float, float, float, int]:
    assignment_dir = upload_dir.name
    precision_ed = grading_config.get("system_decimal_precision", {}).get("error_density", 4)
    
    if records is None:
        print("No records for assignments available")
        return
    
    error_density_list = []
    
    for assignment, assignment_data in records.items():
        
        # skip records of current assignment
        if assignment == assignment_dir:
            continue
        
        student_data = assignment_data.get(student_email, {})    
        
        if not student_data:
            print(f"No data for {student_email} under assignment {assignment}")
            continue
        
        final_submission = student_data[len(student_data) - 1] # get the last submission of the student
        submission_error_density = final_submission.get("error density", None)
            
        if submission_error_density is not None:
            error_density_list.append(submission_error_density)        
            
    print(f"error density list: {error_density_list}")
    
    if len(error_density_list) < 1: # if this is the first assignment of the student
        return
    
    # average recorded error density across all final submissions of the student
    average_error_density = round(sum(error_density_list) / len(error_density_list), precision_ed)
    # relative change compared to the final submission of the previous assignment
    density_of_first_submission = round(error_density_list[0], precision_ed)
    relative_change_to_first = round(error_density / density_of_first_submission, precision_ed) * 100
    density_of_last_submission = round(error_density_list[(len(error_density_list) - 1)], precision_ed)
    relative_change_to_last = round(error_density / density_of_last_submission, precision_ed) * 100
    assignment_number = len(error_density_list)
    
    return  (
                average_error_density, density_of_last_submission, 
                density_of_first_submission, relative_change_to_last,  
                relative_change_to_first, assignment_number
            )
 
def compare_score_with_self(
    student_email: str, 
    error_density: float, 
    upload_dir: Path | str, 
    records: dict,
    grading_config: dict
) -> tuple[float, float, float, float, float, int]:
    """Compares the score of the current submission to submissions made by 
    the student for the same assignment

    Args:
        student_email (str): student email
        error_density (float): overall weighted error density of submission
        upload_dir (Path | str): upload_dir path
        records (dict): records.json contents
        grading_config (dict): grading_config.json contents

    Returns:
        tuple[float, float, float, float, float, int]:  [
                                                            average_error_density, density_of_last_submission, 
                                                            density_of_first_submission, relative_change_to_last,  
                                                            relative_change_to_first, submission_number
                                                        ]
    """
    
    assignment_dir = upload_dir.name
    assignment_data = records.get(assignment_dir, {})
    precision_ed = grading_config.get("system_decimal_precision", {}).get("error_density", 4)

    if not assignment_data:
        print(f"There are no records for {assignment_dir}")
        return
    
    student_data = assignment_data.get(student_email, [])
    
    if not student_data:
        print(f"There are no records for {student_email} under {assignment_dir}")
        return
    
    error_density_list = []
    
    for record in student_data: # iterate over all submission records of student for this assignment
        error_density_list.append(record.get("error density", 0))
    
    if len(error_density_list) <= 1: # if this is the first submission for this assignment
        return
    
    # average recorded error density across all submissions the student made for this assignment
    average_error_density = round(sum(error_density_list) / len(error_density_list), precision_ed)
    # relative change compared to the last submission
    density_of_first_submission = round(error_density_list[0], precision_ed)
    relative_change_to_first = round(error_density / density_of_first_submission, precision_ed) * 100
    density_of_last_submission = round(error_density_list[(len(error_density_list) - 1)], precision_ed)
    relative_change_to_last = round(error_density / density_of_last_submission, precision_ed) * 100
    submission_number = len(error_density_list)
    
    return  (
                average_error_density, density_of_last_submission, 
                density_of_first_submission, relative_change_to_last,  
                relative_change_to_first, submission_number
            )

def compare_score_with_class(
    error_density: float, 
    upload_dir: Path | str,
    records: dict,
    grading_config: dict
) -> tuple[float, float]:
    """Compares the score of the current submission to submissions made by 
    all other class members for the same assignment

    Args:
        error_density (float): overall weighted error density of submission
        upload_dir (Path | str): upload_dir path
        records (dict): records.json contents
        grading_config (dict): grading_config.json contents

    Returns:
        tuple[float, float, str]: [average_assignment_error, score_relative_to_class, comparator]
    """
    assignment_dir = upload_dir.name
    assignment_data = records.get(assignment_dir, {})
    precision_ed = grading_config.get("system_decimal_precision", {}).get("error_density", 4)
    
    if not assignment_data: # if no records under this directory name
        print(f"There are no records for {assignment_dir}")
        return
    
    error_density_list = [] # initialize list to store the error_density values
    
    for submissions in assignment_data.values(): # iterate over all student records within the assignment
        if submissions is None: # if student has no submissions 
            continue
        
        if len(submissions) < 1:
            continue
        
        final_submission = submissions[len(submissions) - 1] # get the last submission of the student
        submission_error_density = final_submission.get("error density", None)
            
        if submission_error_density is not None:
            error_density_list.append(submission_error_density)
            
    if not error_density_list:
        print(f"No error density records found for {assignment_dir}")
        return

    # calculate average error of all final submissions by students for this assignment
    average_assignment_error = round(sum(error_density_list) / len(error_density_list), precision_ed) 
    # compare the score of the current submission to the overall average
    score_relative_to_class = round(error_density / average_assignment_error, precision_ed)
    
    # change output variables based on whether the error density is higher or lower
    if score_relative_to_class < 1:
        percent_value = (1 - score_relative_to_class) * 100
        comparator = "lower"
    else:
        percent_value = (score_relative_to_class - 1) * 100
        comparator = "higher"
    
    return average_assignment_error, percent_value, comparator
    