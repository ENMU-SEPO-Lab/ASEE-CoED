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

def generate_checkStyle_output(number_of_checkstyle_violations, checkstyle_dict, lines_of_code):
    """The important part in this method is to keep track of the nested dictionary structure, keep in mind
    that one submission might involve multiple code files.
    Structure:
        checkstyle_dict: {
            filename1: {
                info: {
                    category1: {
                        type1: # of occurrences in file
                        type2: # of occurrences in file
                        etc...
                    }
                    category2: {
                        type1: # of occurrences in file
                        type2: # of occurrences in file
                        etc...
                    }
                    etc....
                }
                warning: {
                    category1: {
                        type1: # of occurrences in file
                        etc...
                    }
                    category2: {
                        type1: # of occurrences in file
                        etc...
                    }
                    etc....
                }
                error: {
                    category1: {
                        type1: # of occurrences in file
                        etc...
                    }
                    category2: {
                        type1: # of occurrences in file
                        etc...
                    }
                    etc....
                }
            }
            etc... (one dictionary of this structure exists for every file in the submission)
        }

    Args:
        number_of_checkstyle_violations (int): number of total checkstyle violations detected
        checkstyle_dict (dictionary): dictionary with structure as described above
        lines_of_code (int): total lines of code that were analyzed as part of the submission

    Returns:
        tuple: (generated output lines, checkstyle score, checkstyle weighted error density)
    """
    
    severity_totals = {}
    severity_breakdown = {}

    # iterate over each file and its associated severity dictionary from the CheckStyle violation data
    for file, severity_dict in checkstyle_dict.items():
        # for each severity level and its corresponding category dictionary
        for severity, category_dict in severity_dict.items():
            update_violation_breakdown(severity_breakdown, severity_totals, severity, category_dict)

    checkstyle_lines = [
        f"\nCHECKSTYLE {'-' * 45}\n",
        f"\nAn overall of {number_of_checkstyle_violations} violations were detected by CheckStyle.",
        f"\n\nBreakdown by severity level:\n"
    ]
    
    total_penalty = 0
    total_weighted_error_density = 0
    
    for severity, count in severity_totals.items():
        checkstyle_lines.append(f"\n Severity: {severity} - {count} violations\n")

        # Most common category
        category_counts = severity_breakdown[severity]["categories"]
        most_common_category = max(category_counts.items(), key=lambda x: x[1], default=("None", 0))
        checkstyle_lines.append(f"  Most frequent category: {most_common_category[0]} "
                                f"({most_common_category[1]} occurrences)\n")

        # Most common type
        type_counts_flat = {
            typeName: count
            for category in severity_breakdown[severity]["types"].values()
            for typeName, count in category.items()
        }
        most_common_type = max(type_counts_flat.items(), key=lambda x: x[1], default=("None", 0))
        checkstyle_lines.append(f"  Most frequent type: {most_common_type[0]} "
                                f"({most_common_type[1]} occurrences)\n")
        
        checkstyle_lines.extend(get_style_violation_example(most_common_type[0], "checkstyle"))
        
        adjusted_penalty, weighted_error_denstiy = get_adjusted_penalty(severity, count, lines_of_code, "checkstyle")
        total_penalty += adjusted_penalty
        total_weighted_error_density += weighted_error_denstiy
    
    with open(grading_config_path, "r") as file:
        data = json.load(file)
        coding_std_range = data.get("criteria_ratings", {}).get("coding_standards", {})
        max_score = coding_std_range.get("excellent", 0)
        min_score = coding_std_range.get("unsatisfactory", 0)
        
    final_pen = min(total_penalty, max_score)
    final_score = max(max_score - final_pen, min_score)
    
    if number_of_checkstyle_violations == 0:
        checkstyle_lines = [
            f"\nCheckStyle {'-' * 50}\n",
            f"\nCheckStyle did not find any errors in your submission... Good job!"
        ]

    return checkstyle_lines, final_score, total_weighted_error_density

def generate_pmd_output(number_of_pmd_violations, pmd_dict, lines_of_code):
    """Structure of the pmd_dict is analogue to the checkstyle_dict structure explained in 
    generate_checkStyle_output. The only change is that instead of the severity levels 'info',
    'warning', and 'error', we have the priority levels 'level 1', 'level 2', 'level 3', etc... 

    Args:
        number_of_pmd_violations (int): # of total pmd violations detected
        pmd_dict (dicitonary): dictionary with structure as described in generate_checkStyle_output
        lines_of_code (int): total lines of code that were analyzed as part of the submission

    Returns:
        tuple: (generated output lines, pmd score, pmd weighted error density)
    """
    
    priority_totals = {}
    priority_breakdown = {}

    # iterate over each file and its associated priority dictionary from the PMD violation data
    for file, priority_dict in pmd_dict.items():
        # for each priority level and its corresponding category dictionary
        for priority, category_dict in priority_dict.items():
            update_violation_breakdown(priority_breakdown, priority_totals, priority, category_dict)

    pmd_lines = [
        f"\nPMD {'-' * 50}\n",
        f"\nAn overall of {number_of_pmd_violations} violations were detected by PMD.",
        f"\n\nBreakdown by priority level:\n"
    ]

    total_penalty = 0
    total_weighted_error_density = 0

    for priority, count in sorted(priority_totals.items(), key=lambda x: int(x[0])):
        pmd_lines.append(f"\n Priority {priority} - {count} violations\n")

        # Most common category
        category_counts = priority_breakdown[priority]["categories"]
        most_common_category = max(category_counts.items(), key=lambda x: x[1], default=("None", 0))
        pmd_lines.append(f"  Most frequent category: {most_common_category[0]} "
                         f"({most_common_category[1]} occurrences)\n")

        # Most common type
        type_counts_flat = {
            typeName: count
            for category in priority_breakdown[priority]["types"].values()
            for typeName, count in category.items()
        }
        most_common_type = max(type_counts_flat.items(), key=lambda x: x[1], default=("None", 0))
        pmd_lines.append(f"  Most frequent type: {most_common_type[0]} "
                         f"({most_common_type[1]} occurrences)\n")
        
        pmd_lines.extend(get_style_violation_example(most_common_type[0], "pmd"))
        
        adjusted_penalty, weighted_error_density = get_adjusted_penalty(priority, count, lines_of_code, "pmd")
        total_penalty += adjusted_penalty
        total_weighted_error_density += weighted_error_density
    
    with open(grading_config_path, "r") as file:
        data = json.load(file)
        coding_std_range = data.get("criteria_ratings", {}).get("coding_standards", {})
        max_score = coding_std_range.get("excellent", 0)
        min_score = coding_std_range.get("unsatisfactory", 0)
        
    final_pen = min(total_penalty, max_score)
    final_score = max(max_score - final_pen, min_score)
    
    if number_of_pmd_violations == 0:
        pmd_lines = [
            f"\nPMD {'-' * 50}\n",
            f"\nPMD did not find any errors in your submission... Good job!"
        ]

    return pmd_lines, final_score, total_weighted_error_density

def get_style_violation_example(violation_Type, tool_name):
    output_lines = []
    print(violation_Type)
    if violation_Type == "None":
        output_lines.append(
            f"\n{"-" * 90}\n"
            f"No errors detected... Good job!"
            f"\n{"-" * 90}\n"
        )
        return output_lines
    
    with open(output_file_path, "r") as file:
        data = json.load(file)
        violations = data.get("violations", {})
    
    extracted_lines = []
    
    match tool_name:
        case "pmd":
            violations = violations.get("pmd", [])
            for violation in violations:
                if violation.get("rule", "") == violation_Type:
                    filename = os.path.basename(violation.get("file", ""))
                    beginline = int(violation.get("beginline", 0))
                    endline = int(violation.get("endline", 0))
                    message = violation.get("message", "")
                    file_location = os.path.join("Upload_here", filename)
                    with open(file_location, "r") as file:
                        for current_line_number, line in enumerate(file, start=1):
                            if beginline <= current_line_number <= endline:
                                print(line)
                                extracted_lines.append(line)
                            elif current_line_number > endline:
                                break # break after passing endLine
                    print(
                        f"filename: {filename}\n",
                        f"begin line: {beginline}\n",
                        f"end line: {endline}\n",
                        f"message: {message}\n",
                        f"example: {extracted_lines}\n"
                    )
                    output_lines.extend(
                        format_code_violation_example(filename, beginline, message, ("".join(extracted_lines)))
                    )  
                    break # stop iterating over all violations after example was found
            
        case "checkstyle":
            violations = violations.get("checkstyle", [])
            for violation in violations:
                type = violation.get("source", "").rsplit(".", 1)[-1] 
                if type == violation_Type:
                    filename = os.path.basename(violation.get("file", ""))
                    error_line = int(violation.get("line", 0))
                    message = violation.get("message", "")
                    file_location = os.path.join("Upload_here", filename)
                    with open(file_location, "r") as file:
                        for current_line_number, line in enumerate(file, start=1):
                            if error_line == current_line_number:
                                print(line)
                                extracted_lines.append(line)
                                break # break after passing endLine
                    print(
                        f"filename: {filename}\n",
                        f"line: {error_line}\n",
                        f"message: {message}\n",
                        f"example: {extracted_lines}\n"
                    )
                    output_lines.extend(
                        format_code_violation_example(filename, error_line, message, ("".join(extracted_lines)))
                    )        
                    break # stop iterating over all violations after example was found
            
        case _:
            print("Error in match statement of get_style_violation_example()")
            pass 
        
    return output_lines

def format_code_violation_example(filename, line, message, example):
    formatted_lines = [
        f"  Example from file: {filename}, in line {line}",
        f"\n{"-" * 90}\n",
        f"      {example}",
        f"{"-" * 90}\n",
        f"  Feedback: {message}\n"
    ]
    return formatted_lines  

def generate_unitTesting_output(unit_test_failures, number_of_tests, number_of_failures):
    # Generate a formatted output of failed unit test cases with descriptions
    unit_testing_lines = [
            f"\n\n{'=' * 30}   REQUIREMENTS + RUNTIME   {'=' * 40}\n",
            f"\nJUNIT {'-' * 45}\n\n",
            f"An overall of {number_of_failures} out of {number_of_tests} unit tests failed.\n",
            f"\nThe following are the ones that failed:\n"
        ]
                
    for test_fail in unit_test_failures:
        test_name = test_fail.get("name")
        error_message = test_fail.get("failureDetails").get("message")
        unit_testing_lines.append(f"    Test: {test_name} failed with the error: {error_message}\n")
        
    return unit_testing_lines
   
def generate_score_output(requirements_score, runtime_score, coding_stand_score):
    # Compute final score with the individual rubric scores and generate score output lines
    student_score_output = [
            f"\n{'=' * 35}  FINAL SCORE   {'=' * 45}",
            f"\n    - Requirements: {requirements_score}",
            f"\n    - Coding Standards: {coding_stand_score}",
            f"\n    - Runtime: {runtime_score}",
            f"\n    - Efficieny: TBD",
            f"\n{'=' * 100}",
            f"\n    - Overall: {requirements_score + runtime_score + coding_stand_score}",
            f"\n{'=' * 45} END REPORT {'=' * 45}"
        ]
    return student_score_output

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