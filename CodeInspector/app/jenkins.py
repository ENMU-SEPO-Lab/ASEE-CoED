import xml.etree.ElementTree as ET
import json
import os
import pandas as pd
from scipy.stats import percentileofscore

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ================================= Grade Report Creation Starts Here =====================================
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

BUILD_XML_PATH = "build.xml"
RECORDS_FILE_PATH = "records/records.json"

# create a dynamic grade report file name
grade_report_file_path = os.path.join(grade_report_dir, f"{check_date}.txt")  

# generate grade report using the previously constructed JSON file
def create_grade_report(json_output_file_path):
    """This function is the main function, calling all other functions during the process of creating the
    .txt file.

    Args:
        json_output_file_path (_type_): The path to the violation report JSON file created by the first 
                                        part of the script

    Returns:
        None: Returns nothing (creates .txt file in specified directory).
    """
    # try:
    with open(json_output_file_path, "r") as file: # open violations JSON file in read-mode
        data = json.load(file)

    # store and split up the extracted data
    student_name = data.get("studentName")
    report_date = data.get("checkDate")
    lines_of_code = data.get("linesOfCode")
    violations = data.get("violations", {})
    
    # extract different violation lists from JSON file
    checkstyle_violations = violations.get("checkstyle", []) 
    pmd_violations = violations.get("pmd", []) 
    unit_testing_report = violations.get("Unit testing", {})
    print(unit_testing_report)
    
    number_of_checkstyle_violations = len(checkstyle_violations)
    number_of_pmd_violations = len(pmd_violations)
    
    # process checkstyle and pmd violations
    checkstyle_dict = process_checkstyle_violations(checkstyle_violations)
    pmd_dict = process_pmd_violations(pmd_violations)
    
    # get unit testing details
    unit_test_failures = get_failed_tests(unit_testing_report)
    number_of_tests = int(unit_testing_report.get("summary").get("testsRun", 0))
    number_of_failures = int(unit_testing_report.get("summary").get("failures", 0))
    
    # intro lines for report
    intro_lines = [
        f"This is report {report_date} for student {student_name}\n",
        f"\nThe report covers a total of {lines_of_code} lines of code\n",
        f"\n{number_of_checkstyle_violations} errors were detected by CheckStyle",
        f"\n{number_of_pmd_violations} errors were detected by PMD",
        f"\n{number_of_failures} out of {number_of_tests} unit tests failed.",
        f"\n\nReport: \n",
        f"\n{'=' * 25}   CODING STANDARDS   {'=' * 50}\n"
    ]
    
    # generate checkstyle lines and stats
    checkStyle_lines, checkStyle_score, checkstyle_weighted_density = generate_checkStyle_output(
        number_of_checkstyle_violations, 
        checkstyle_dict,
        lines_of_code
    )
    
    # generate pmd lines and stats
    pmd_lines, pmd_score, pmd_weighted_density = generate_pmd_output(
        number_of_pmd_violations, 
        pmd_dict,
        lines_of_code
    )
    
    # get percentile scores
    total_weighted_density = checkstyle_weighted_density + pmd_weighted_density
    checkstyle_percentile, pmd_percentile, overall_percentile = calculate_percentile_score(
        checkstyle_weighted_density,
        pmd_weighted_density,
        total_weighted_density
    )
            
    # add checkstyle stats to checkstyle lines 
    checkStyle_lines.append(
        f"\n\nOverall weighted CheckStyle error density: {round(checkstyle_weighted_density, 5)}"
        f"\nThis places you in the {checkstyle_percentile}th percentile of submissions in the database."
        f"\nThat is, {100 - checkstyle_percentile}% of submissions had a higher CheckStyle error density than yours.\n"
    )
    
    # add pmd stats to pmd lines
    pmd_lines.append(
        f"\n\nOverall weighted PMD error density: {round(pmd_weighted_density, 5)}"
        f"\nThis places you in the {pmd_percentile}th percentile of submissions in the database."
        f"\nThat is, {100 - pmd_percentile}% of submissions had a higher PMD error density than yours. "
    )
    
    # add overall stats to coding style summary lines
    coding_style_summary_lines = [
        f"\n\nSUMMARY  {'-' * 40}\n",
        f"\nThe cumulative weighted error density of you submission is: {round(total_weighted_density, 5)}.",
        f"\nThis places you in the: {overall_percentile}th percentile.",
        f"\nThat is, {100 - overall_percentile}% of the average student submission have a higher error density than yours."
    ]
    
    # generate unit testing lines
    unit_testing_lines = generate_unitTesting_output(
        unit_test_failures, number_of_tests, 
        number_of_failures
    )

    # for debugging purposes, i.e. tracing the grade creation algorithm
    print(
        f"CheckStyle Score: {checkStyle_score}\n"
        f"PMD score: {pmd_score}\n"
    )
    
    # generate student score output
    requirements_score, runtime_score = get_run_and_req_score(number_of_tests, number_of_failures)
    coding_std_score = round((checkStyle_score + pmd_score) / 2)
    score_lines = generate_score_output(requirements_score, runtime_score, coding_std_score)
    
    # write all lines to .txt file and store the file under specified path
    with open(grade_report_file_path, "w") as file:
        file.writelines(intro_lines)
        file.writelines(checkStyle_lines)
        file.writelines(pmd_lines)
        file.writelines(coding_style_summary_lines)
        file.writelines(unit_testing_lines)
        file.writelines(score_lines)
    
    upload_dir_name = get_upload_dir_name()
    
    if upload_dir_name:
        update_json(student_name, total_weighted_density, upload_dir_name)
        compare_score_with_class(total_weighted_density, upload_dir_name)
        compare_score_with_self(student_name, total_weighted_density, upload_dir_name)
    else:
        print("Upload directory name is None.")
    
    print(f"Grade report created and saved to: {grade_report_file_path}")
        
    # except Exception as e:
    #     print(f"Failed to generate report: {e}")
    
create_grade_report(output_file_path)