from app.infrastructure.models import (
    SubmissionData, 
    ProcessedSubmission,
    ProcessedViolations,
    ProcessedJunitTests,
    # UnitTestCase
)
from pathlib import Path

# generate grade report using the previously constructed JSON file
def create_grade_report(
    submission_data: SubmissionData,
    processed_submission: ProcessedSubmission,
    grading_config: dict,
    percentiles_self: tuple[float, float, float, float, float, int] | None = None,
    percentiles_class: tuple[float, float, float] | None = None,
    percentiles_global: tuple[float, float, float] | None = None
):
    """Assembles the grade report and writes it to a .txt file at the provided path

    Args:
        submission_data (SubmissionData): the data of the evaluated submission
        processed_submission (ProcessedSubmission): the processed submission (need some info from this)
        grading_config (dict): grading_config.json contents
        percentiles_self (tuple[float, float, float, float, float, int]): for feedback
        percentiles_class (tuple[float, float, float]): for feedback
        percentiles_global (tuple[float, float, float]): for feedback
    """
    # extract data
    grade_report_file_path = submission_data.report_file_path
    student_email = submission_data.email
    report_date = submission_data.date
    assignment_name = submission_data.upload_dir_name
    loc = submission_data.loc
    number_of_cs_violations = submission_data.cs_violation_count
    number_of_pmd_violations = submission_data.pmd_violation_count
    total_weighted_density = submission_data.overall_weighted_error
    cs_weighted_density = submission_data.cs_weighted_error
    pmd_weighted_density = submission_data.pmd_weighted_error

    precision_ed = grading_config.get("system_decimal_precision", {}).get("error_density", 4)
    precision_perc_val = grading_config.get("system_decimal_precision", {}).get("percent_value", 4)
    
    cs_processed = processed_submission.cs_processed
    pmd_processed = processed_submission.pmd_processed
    junit_processed = processed_submission.junit_processed
    
    # junit metrics for intro lines
    number_of_tests = submission_data.junit_test_count
    number_of_failures = submission_data.junit_failed_count
    
    submission_number = percentiles_self[5]
    
    # intro lines for report
    intro_lines = [
        f"This report ({report_date}) is for the submission made by the student with the following email address: {student_email}",
        f"\nThis submission is number {submission_number} by this student for the assignment named '{assignment_name}'",
        f"\nThe report covers a total of {loc} lines of code\n",
        f"\n{number_of_cs_violations} errors were detected by CheckStyle",
        f"\n{number_of_pmd_violations} errors were detected by PMD",
        f"\n{number_of_failures} out of {number_of_tests} unit tests failed.",
        f"\n\nReport: \n",
        f"\n{'=' * 25}   CODING STANDARDS   {'=' * 50}\n"
    ]
    
    # generate checkstyle lines and stats
    cs_lines = generate_checkStyle_output(cs_processed, submission_data)
    
    # generate pmd lines and stats
    pmd_lines = generate_pmd_output(pmd_processed, submission_data)
    
    # extract percentile scores from tuples
    # if records exist and stats were calculated successfully 
    if percentiles_global is not None:
        checkstyle_percentile, pmd_percentile, overall_percentile = percentiles_global
        
         # add checkstyle stats to checkstyle lines 
        cs_lines.append(
            f"\nOverall weighted CheckStyle error density: {round(cs_weighted_density, precision_ed)}"
            f"\nThis ranks in the {checkstyle_percentile}th percentile of submissions in the dataset."
            f"\nThat is, {100 - checkstyle_percentile}% of submissions had a higher CheckStyle error density than this.\n"
        )
        # add pmd stats to pmd lines
        pmd_lines.append(
            f"\n\nOverall weighted PMD error density: {round(pmd_weighted_density, precision_ed)}"
            f"\nThis ranks in the {pmd_percentile}th percentile of submissions in the dataset."
            f"\nThat is, {100 - pmd_percentile}% of submissions had a higher PMD error density than this. "
        )
    
    # if record data could not be loaded / is None    
    else:
        cs_lines.append(
            f"\n\nOverall weighted CheckStyle error density: {round(cs_weighted_density, precision_ed)}"
            f"\n No records available for percentile comparison...\n"
        )
        pmd_lines.append(
            f"\n\nOverall weighted PMD error density: {round(pmd_weighted_density, precision_ed)}"
            f"\n No records available for percentile comparison...\n"
        )
    
    # if records exist and stats were calculated successfully    
    if percentiles_self is not None and percentiles_class is not None:
        average_error_dens_self, density_of_last_submission, density_of_first_submission = percentiles_self[0:3]
        relative_change_to_last, relative_change_to_first = percentiles_self[3:5]
        average_assignment_error_class, relative_change_to_class, comparator_string = percentiles_class
            
        print 
        # add overall stats to coding style summary lines
        coding_style_summary_lines = [
            f"\n\nSUMMARY  {'-' * 40}\n",
            f"\nThe cumulative weighted error density of this submission is: {round(total_weighted_density, precision_ed)}.",
            f"\nThis ranks in the: {overall_percentile}th percentile.",
            f"\nThat is, historically, {100 - overall_percentile}% of the average student submission of previous semesters had a higher error density than this.",
            f"\n{'-' * 40}",
            f"\nThe average error density of the student for this assignment is: {average_error_dens_self}",
            f"\n{'-' * 40}",
            f"\nThe first submission by this student for this assignment had a weighted density of: {density_of_first_submission}",
            f"\nThe error density of this submission is {relative_change_to_first}% of the first submission.",
            f"\n{'-' * 40}",
            f"\nThe previous submission by this student for this assignment had a weighted density of: {density_of_last_submission}",
            f"\nThe error density of this submission is {relative_change_to_last}% of the previous submission.",
            f"\n{'-' * 40}",
            f"\nThe average error density of the class for this assignment is: {average_assignment_error_class}",
            f"\nThe error density of this submission was {round(relative_change_to_class, precision_perc_val)}% {comparator_string} than the class average.",
        ]
    
    # if record data could not be loaded / is None
    else:
        coding_style_summary_lines = [
            f"\n\nSUMMARY  {'-' * 40}\n",
            f"\nThe cumulative weighted error density of this submission is: {round(total_weighted_density, precision_ed)}.",
            f"\nThere are no current records for percentile comparisons of the submission..."
        ]
    
    # generate unit testing lines
    unit_testing_lines = generate_unitTesting_output(junit_processed)

    coding_std_score = submission_data.coding_std_score
    runtime_score = submission_data.run_score
    if not runtime_score:
        runtime_score = 0
    requirements_score = submission_data.req_score
    
    score_lines = generate_score_output(requirements_score, runtime_score, coding_std_score)
    
    # write all lines to .txt file and store the file under specified path
    with open(grade_report_file_path, "w") as file:
        file.writelines(intro_lines)
        file.writelines(cs_lines)
        file.writelines(pmd_lines)
        file.writelines(coding_style_summary_lines)
        file.writelines(unit_testing_lines)
        file.writelines(score_lines)
    
    print(f"Grade report created and saved to: {grade_report_file_path}")
        
    # except Exception as e:
    #     print(f"Failed to generate report: {e}")

def generate_checkStyle_output(cs_processed: ProcessedViolations, submission_data: SubmissionData) -> list:
    """generates the grade report lines of the CheckStyle section

    Args:
        cs_processed (ProcessedViolations): the CheckStyle violations
        submission_data (SubmissionData): the data of the submission evaluation

    Returns:
        list: the output lines for the CheckStyle section of the report
    """
    number_of_cs_violations = submission_data.cs_violation_count
    
    checkstyle_lines = [
        f"\nCHECKSTYLE {'-' * 45}\n",
        f"\nAn overall of {number_of_cs_violations} violations were detected by CheckStyle.",
        f"\n\nBreakdown by severity level:\n"
    ]
    
    type_counts_in_severities = cs_processed.get_type_counts_per_severity_in_submission()
    
    for severity, type_counter in type_counts_in_severities.items():
        checkstyle_lines.append(f"\n Severity: {severity} - {type_counter.total()} violations\n")

        # most common type
        most_common_type = type_counter.most_common(1)
        if most_common_type:
            checkstyle_lines.append(f"  Most frequent type: {most_common_type[0][0]} "
                                    f"({most_common_type[0][1]} occurrences)\n")
            
    if number_of_cs_violations == 0:
        checkstyle_lines = [
            f"\nCheckStyle {'-' * 50}\n",
            f"\nCheckStyle did not find any errors in this submission..."
        ]

    return checkstyle_lines

def generate_pmd_output(pmd_processed: ProcessedViolations, submission_data: SubmissionData) -> list:
    """generates the grade report lines of the PMD section

    Args:
        pmd_processed (ProcessedViolations): the PMD violations
        submission_data (SubmissionData): the data of the submission evaluation

    Returns:
        list: the output lines for the PMD section of the report
    """

    number_of_pmd_violations = submission_data.pmd_violation_count
        
    pmd_lines = [
        f"\nPMD {'-' * 50}\n",
        f"\nAn overall of {number_of_pmd_violations} violations were detected by PMD.",
        f"\n\nBreakdown by priority level:\n"
    ]
    
    type_counts_in_severities = pmd_processed.get_type_counts_per_severity_in_submission()

    for priority, type_counter in type_counts_in_severities.items():
        pmd_lines.append(f"\n Priority {priority} - {type_counter.total()} violations\n")

        # most common type
        most_common_type = type_counter.most_common(1)
        if most_common_type:
            pmd_lines.append(f"  Most frequent type: {most_common_type[0][0]} "
                            f"({most_common_type[0][1]} occurrences)\n")
                
    if number_of_pmd_violations == 0:
        pmd_lines = [
            f"\nPMD {'-' * 50}\n",
            f"\nPMD did not find any errors in this submission..."
        ]

    return pmd_lines

def generate_unitTesting_output(junit_processed: ProcessedJunitTests) -> list:
    """generates the grade report lines of the Junit section

    Args:
        junit_processed (ProcessedJunitTests): the processed Junit test data

    Returns:
        list: the output lines for the Junit section of the report
    """
    failed_tests = junit_processed.failed_tests
    number_of_failures = len(failed_tests)
    number_of_tests = len(junit_processed.all_tests)
    
    # Generate a formatted output of failed unit test cases with descriptions
    unit_testing_lines = [
            f"\n\n{'=' * 30}   REQUIREMENTS + RUNTIME   {'=' * 40}\n",
            f"\nJUNIT {'-' * 45}\n\n",
            f"An overall of {number_of_failures} out of {number_of_tests} unit tests failed.\n",
            f"\nThe following are the ones that failed:\n"
        ]
                
    for failed_test in failed_tests:
        test_name = failed_test.name
        error_message = failed_test.failure_details.message
        unit_testing_lines.append(f"    Test: {test_name} failed with the error: {error_message}\n")
        
    return unit_testing_lines
   
def generate_score_output(requirements_score, runtime_score, coding_stand_score) -> list:
    # Compute final score with the individual rubric scores and generate score output lines
    student_score_output = [
            f"\n{'=' * 35}  FINAL SCORE   {'=' * 45}",
            f"\n    - Requirements: {requirements_score}",
            f"\n    - Coding Standards: {coding_stand_score}",
            f"\n    - Runtime: TBD", # need dynamically -> GenAI
            f"\n    - Efficiency: TBD", # need dynamically -> GenAI
            f"\n{'=' * 100}",
            f"\n    - Overall: {requirements_score + coding_stand_score}",
            f"\n{'=' * 45} END REPORT {'=' * 45}"
        ]
    return student_score_output
