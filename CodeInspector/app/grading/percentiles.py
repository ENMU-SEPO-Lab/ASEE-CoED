from scipy.stats import percentileofscore
from pathlib import Path
import pandas as pd

def get_global_percentile_score(
    cs_error_density: float ,
    pmd_error_density: float, 
    overall_error_density: float, 
    data: pd.DataFrame
) -> tuple[float, float, float]:
    """Calculates the percentile scores of the computed error densities of the analyzed file in relation
    to the global dataset (weighted_data.csv)

    Args:
        checkStyle_error_density (float): checkstyle error density of the file
        pmd_error_density (float): pmd error density of the file
        total_error_density (float): overall error density of the file

    Returns:
        tuple: (checkstyle percentile score, pmd percentile score, overall percentile score)
    """
    cs_data = data["cs_density"].to_numpy()
    pmd_data = data["pmd_density"].to_numpy()
    total_data = data["total_density"].to_numpy()
    
    percentile_checkstyle = float(round(percentileofscore(cs_data, cs_error_density, kind="rank"), 2))
    percentile_pmd = float(round(percentileofscore(pmd_data, pmd_error_density, kind="rank"), 2))
    percentile_overall = float(round(percentileofscore(total_data, overall_error_density, kind='rank'), 2))
    
    return percentile_checkstyle, percentile_pmd, percentile_overall

def compare_score_with_self(
    student_name: str, 
    error_density: float, 
    upload_dir: Path | str, 
    records: dict
) -> tuple[float, float]:
    
    assignment_dir = upload_dir.name
    assignment_data = records.get(assignment_dir, {})
    
    if not assignment_data:
        print(f"There are no records for {assignment_dir}")
        return
    
    student_data = assignment_data.get(student_name, [])
    
    if not student_data:
        print(f"There are no records for {student_name} under {assignment_dir}")
        return
    
    error_density_list = []
    
    for record in student_data: # iterate over all submission records of student for this assigment
        error_density_list.append(record.get("error density", 0))
    
    if len(error_density_list) <= 1: # if this is the first submission for this assignment
        return
    
    # average recorded error density across all submissions the student made for this assignment
    average_error_density = round(sum(error_density_list) / len(error_density_list), 4)
    # reltive change compared to the last submission
    relative_change = round(error_density / error_density_list[(len(error_density_list) - 2)], 4) * 100
    
    print(
        f"\n{'=' * 30}",
        f"\nYour average error density for this assignment is: {average_error_density}",
        f"\nThe error density of this submission is {relative_change}% of your last submission.",
        f"\n{'=' * 30}"
    )
    
    return average_error_density, relative_change

def compare_score_with_class(
    error_density: float, 
    upload_dir: Path | str,
    records: dict
) -> tuple[float, float]:
    
    assignment_dir = upload_dir.name
    assignment_data = records.get(assignment_dir, {})
    
    if not assignment_data: # if no records under this directory name
        print(f"There are no records for {assignment_dir}")
        return
    
    error_density_list = [] # initialize list to store the error_density values
    
    for student, submissions in assignment_data.items(): # iterate over all student records within the assigment
        if submissions is None: # if student has no submissions 
            continue
        
        for submission in submissions: # iterate over every submission
            if submission is None:
                continue
            
            submission_error_density = submission.get("error density")
            
            if submission_error_density is not None:
                error_density_list.append(submission_error_density)
            
    if not error_density_list:
        print(f"No error density records found for {assignment_dir}")
        return

    # calculate average error of all student submissions for this assignment
    average_assignment_error = round(sum(error_density_list) / len(error_density_list), 4) 
    # compare the score of the current submission to the overall average
    score_relative_to_class = round(error_density / average_assignment_error, 4)
    
    # change output variables based on whether the errordensity is higher or lower
    if score_relative_to_class < 1:
        percent_value = (1 - score_relative_to_class) * 100
        comparator = "lower"
    else:
        percent_value = (score_relative_to_class - 1) * 100
        comparator = "higher"
    
    print(
        f"\n{'=' * 30}"
        f"\nThe average error density of the class for this assignment is: {average_assignment_error}",
        f"\nYour error density was {round(percent_value, 2)}% {comparator} than the class average.",
        f"\n{'=' * 30}"
    )
    
    return average_assignment_error, score_relative_to_class
    