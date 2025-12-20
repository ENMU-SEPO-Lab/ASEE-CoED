from datetime import datetime
import xml.etree.ElementTree as ET
import json
import os
import pandas as pd
import subprocess
from scipy.stats import percentileofscore
 
def create_json_output(student_name, check_date, checkstyle_errors, pmd_violations, test_results):

    # Count LOC but ignore white space
    command = r"grep -v '^\s*$' Upload_here/*.java | wc -l"
    
    # Count LOC but ignore white space and comments
    #command = r"grep -v '^\s*$' ../Upload_here/*.java | grep -v '^\s*//' | grep -v '^\s*/\*' | grep -v '^\s*\*' | grep -v '^\s*\*/' | wc -l"
    
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    loc = 200
    current_dir = os.getcwd()
    print("Current directory:", current_dir)
    if result.returncode == 0:
        loc = int(result.stdout.strip())
        print(f"LOC determined dynamically. LOC = {loc}")
    
    if loc <= 0:
        loc = 100
    
    print("LOC: ", loc)
    
    # Combine Checkstyle and PMD violations into a single structure
    output = {
        "System": student_name,
        "studentName": student_name, # TODO: Need this extracted from .java source file dynamically using grep as well
        "checkDate": check_date,
        "linesOfCode": loc,
        "violations": {
            "checkstyle": checkstyle_errors,
            "pmd": pmd_violations,
            "Unit testing": test_results
        }
    }
    return output

# Define the paths to the XML files
checkstyle_file_path = 'build/test-reports/checkstyle-result.xml'
pmd_file_path = 'build/test-reports/pmd.xml'
 
# Directories
test_dir = "test"
reports_dir = "build/test-reports"
 
# Ensure the reports directory exists
os.makedirs(reports_dir, exist_ok=True)
 
# Get the first (and only) file in the test directory
test_files = os.listdir(test_dir)
if not test_files:
    print("No test file found in the 'test' directory.")
    exit(1)  # Exit with an error if no file exists
 
test_file = test_files[0]  # Since there's only one file
file_name, _ = os.path.splitext(test_file)  # Extract filename without extension
 
# Construct the new report filename
new_filename = f"TEST-{file_name}.txt"
test_file_path = os.path.join(reports_dir, new_filename)
 
#test_file_path = "build/test-reports/TEST-TestCases.txt"
print("test_file_path: ", test_file_path)
 
# Parse the Checkstyle XML file
checkstyle_errors = parse_checkstyle(checkstyle_file_path)
 
# Print the parsed Checkstyle errors to the console
if checkstyle_errors:
    print("Checkstyle Errors:")
    for error in checkstyle_errors:
        print(f"File: {error['file']}, Line: {error['line']}, Severity: {error['severity']}, Message: {error['message']}, Source: {error['source']}")
else:
    print("No Checkstyle errors found or failed to parse the file.")
 
# Parse the PMD XML file
pmd_violations = parse_pmd(pmd_file_path)
 
# Print the parsed PMD violations to the console
if pmd_violations:
    print("\\nPMD Violations:")
    for violation in pmd_violations:
        print(f"File: {violation['file']}, Line: {violation['beginline']}, Rule: {violation['rule']}, Message: {violation['message']}, URL: {violation['externalInfoUrl']}")
else:
    print("\\nNo PMD violations found or failed to parse the file.")

test_results = parse_test_results(test_file_path)
 
# Define metadata
student_name = "CodeInspector" # TODO: Need this extracted from .java source file dynamically using grep as well

# Get the current date and time
current_datetime = datetime.now()
check_date = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")  # Format to avoid invalid characters in file names
 
# Generate the JSON output
output_json = create_json_output(student_name, check_date, checkstyle_errors, pmd_violations, test_results)
 
# Create the output directory if it doesn't exist
output_dir = "build/test-reports/"
os.makedirs(output_dir, exist_ok=True)
 
# Create a dynamic output file name
output_file_path = os.path.join(output_dir, f"violations.json")
 
# Save the JSON output to the file
with open(output_file_path, 'w') as json_file:
    json.dump(output_json, json_file, indent=4)
 
print(f"JSON output saved to {output_file_path}")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ================================= Grade Report Creation Starts Here =====================================
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

grade_report_dir = "build/grade-reports/"
grading_config_path = "lib/grading_config.json"
os.makedirs(grade_report_dir, exist_ok=True)

BUILD_XML_PATH = "build.xml"
RECORDS_FILE_PATH = "records/records.json"

# create a dynamic grade report file name
grade_report_file_path = os.path.join(grade_report_dir, f"{check_date}.txt")

# process checkstyle violations
def process_checkstyle_violations(checkstyle_violations):
    """This method takes the checkstyle violation list read from the JSON file, processes it and stores 
    it in a nested dictionary so that we can access specific values more easily. 
    
    The dictionary structure is described in generate_checkStyle_output()

    Args:
        checkstyle_violations (list): the checkstyle violation list

    Returns:
        dictionary: the dicitonary containing the formatted / processed checkstyle violation data
    """
    processed_checkstyle_violations = {}
        
    for violation in checkstyle_violations:
        file = violation.get("file") # get the filepath of the file where the violation was detected
        
        # split the string to get the second to last part, i.e the violation category
        category = violation.get("source").rsplit(".", 2)[-2]
        # split the string to get the last part, i.e the specific violation type
        type = violation.get("source").rsplit(".", 1)[-1] 
        severity = violation.get("severity")
         
        # this next block simply aims to increase the counter of the found violation type, which is stored 
        # inside a nested dictionary.
        
        # make sure the file exists in the dictionary and set up the desired severity order 
        # (the order is relvant for the report cration later on, because the lines for the .txt file are 
        # created in the order in which the severities are encountered inside the dictionary)
        if file not in processed_checkstyle_violations:
            processed_checkstyle_violations[file] = {
                "info": {},
                "warning": {},
                "error": {}
            }

        # make sure the category exists in the severity dictionary
        if category not in processed_checkstyle_violations[file][severity]:
            processed_checkstyle_violations[file][severity][category] = {}

        # make sure the violation type counter or initialize it with 1
        if type in processed_checkstyle_violations[file][severity][category]:
            processed_checkstyle_violations[file][severity][category][type] += 1
        else:
            processed_checkstyle_violations[file][severity][category][type] = 1
    return processed_checkstyle_violations
            
# process pmd violations            
def process_pmd_violations(pmd_violations):
    """This method takes the pmd violation list read from the JSON file, processes it and stores it in
    a nested dictionary so that we can access specific values more easily. 
    
    The dictionary structure is described in generate_checkStyle_output()

    Args:
        pmd_violations (list): the pmd violation list

    Returns:
        dictionary: the dicitonary containing the formatted / processed pmd violation data
    """
    processed_pmd_violations = {}        
            
    for violation in pmd_violations:
        file = violation.get("file")
        
        category = violation.get("ruleset")
        type = violation.get("rule")
        priority = violation.get("priority")
        
        # this next block simply aims to increase the counter of the found violation type, which is stored 
        # inside a nested dictionary.
        
        # make sure the file exists in the dictionary and set up the desired priority order
        # (the order is relvant for the report creation later on, because the lines for the .txt file are 
        # created in the order in which the priority levels are encountered inside the dictionary)
        if file not in processed_pmd_violations:
           processed_pmd_violations[file] = {
               "5": {},
               "4": {},
               "3": {},
               "2": {},
               "1": {}
           }
        
        # make sure the category exists in the priority level dictionary  
        if category not in processed_pmd_violations[file][priority]:
            processed_pmd_violations[file][priority][category] = {}
        
        # increment the violation type counter or initialize it with 1
        if type in processed_pmd_violations[file][priority][category]:
            processed_pmd_violations[file][priority][category][type] += 1
        else:
            processed_pmd_violations[file][priority][category][type] = 1       
    return processed_pmd_violations     

def get_failed_tests(unit_testing_report):
# extract list of failed test cases from the test results
    unit_tests = unit_testing_report.get("testCases", [])
    failed_tests = []
            
    for unit_test in unit_tests:
        if unit_test.get("status") == "FAILED":
            failed_tests.append(unit_test) 
    return failed_tests     

def update_violation_breakdown(breakdown_dict, totals_dict, level_key, nested_dict):
    """This method essentially keeps a spearate count of the total violations encountered within a violation
    category, as well as a counter for each specific violation type within one such category. For easier
    access and processing, two separate dictionaries are implemented. One for the category counter, and one
    to keep track of all specific violation type counters within that category.
    Structure:
        breakdown_dict: {
            categories: {
                category1: # of violations within category
                category2: # of violaitons within category
                etc....
            }
            types: {
                category1: {
                    type1: # of occurrences of this violaiton type within the category
                    type2: # of occurrences of this violaiton type within the category
                    etc....
                }
                category1: {
                    type1: # of occurrences of this violaiton type within the category
                    type2: # of occurrences of this violaiton type within the category
                    etc....
                }
                etc....
            }
        }

    Args:
        breakdown_dict (dictionary): this is where the processed data is stored
        totals_dict (dictionary): _description_
        level_key (severity / priority level): if checkstyle, then severity; if pmd, then priority level
        nested_dict (dictionary): this is the violation dicitionary, specific for each tool, 
                                created from the JSON file (structure exlpained in generate_checkStyle_output)
    """
    # initialize totals
    totals_dict[level_key] = totals_dict.get(level_key, 0)

    # initialize category/type structure if not yet present
    if level_key not in breakdown_dict:
        breakdown_dict[level_key] = {"categories": {}, "types": {}}

    for category, type_dict in nested_dict.items():
        # initialize category coutner values
        categories_of_level = breakdown_dict[level_key]["categories"]
        categories_of_level[category] = categories_of_level.get(category, 0)

        # initialize type breakdown for the current category
        types_of_level = breakdown_dict[level_key]["types"]
        if category not in types_of_level:
            types_of_level[category] = {}

        for violation_type, count in type_dict.items():
            # update counter values
            totals_dict[level_key] += count # number of violations for the severity / priority level
            categories_of_level[category] += count # number of violations for category
            # number of violations for the specific violation type within the current category
            types_of_level[category][violation_type] = types_of_level[category].get(violation_type, 0) + count 

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

def get_adjusted_penalty(violation_level, count, lines_of_code, tool_name):
    # method to calculate the adjusted penalty (part of scoring algorithm)
    try:
        with open (grading_config_path, "r") as file:
            data = json.load(file)
            weights = data.get("weights", {}).get(tool_name, {})
        
        adjusted_pen, absolute_pen = 0, 0
        print(weights)
        if violation_level in weights:
            absolute_pen = weights[violation_level] * count
            # for debugging purposes / tracing the algorithm
            print(
                f"absolute_pen for {tool_name}, {violation_level}: {absolute_pen}\n"
                f"abs_pen = {weights[violation_level]} * {count}\n"
            )
        else:
            # debugging
            print(f"Error calculating penalty for {tool_name}, {violation_level}")
            return 0
        
        if lines_of_code == 0:
            return 0
        
        weighted_error_density = absolute_pen / lines_of_code
        error_density = count / lines_of_code
        adjusted_pen = absolute_pen * error_density
            
    except Exception as e:
        print(f"Error while opening weights JSON file. ERROR: {e}")
        return 0
    
    return adjusted_pen, weighted_error_density     

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

def get_run_and_req_score(number_of_tests, number_of_failures):
    """Calculate runtime and requirements score. Currently this is only based on the unit testing
    results, as we don't have a proper way of automatically analyzing runtime scores.

    Args:
        number_of_tests (int): overall # of tests that were ran
        number_of_failures (int): # of tests that failed

    Returns:
        tuple: (requirements score, runtime score)
    """
    requirements_score_range = [60, 48, 36, 10, 0] # from grading criteria of the course that is taught
    runtime_score_range = [20, 16, 12, 8, 0] # from grading criteria of the course that is taught
    
    if number_of_tests == 0:
        print("Number of Junit tests is 0.")
        return 0, 0
    
    unit_test_success_ratio = 1 - round((number_of_failures / number_of_tests), 1)
    requirements_score = 0
    runtime_score = 0
    
    # assign score based on the unit test success ratio
    if unit_test_success_ratio >= 0.9:
        requirements_score = requirements_score_range[0]
        runtime_score = runtime_score_range[0]
    elif unit_test_success_ratio >= 0.8:
        requirements_score = requirements_score_range[1]
        runtime_score = runtime_score_range[1]
    elif unit_test_success_ratio >= 0.5:
        requirements_score = requirements_score_range[2]
        runtime_score = runtime_score_range[2]
    elif unit_test_success_ratio > 0:
        requirements_score = requirements_score_range[3]
        runtime_score = runtime_score_range[3]
    else:
        requirements_score = requirements_score_range[4]
        runtime_score = runtime_score_range[4]
    return requirements_score,runtime_score

def calculate_percentile_score(checkStyle_error_density ,pmd_error_density, total_error_density):
    """Calculates the percentile scores of the computed error densities of the analyzed file in relation
    to the global dataset (weighted_data.csv)

    Args:
        checkStyle_error_density (float): checkstyle error density of the file
        pmd_error_density (float): pmd error density of the file
        total_error_density (float): overall error density of the file

    Returns:
        tuple: (checkstyle percentile score, pmd percentile score, overall percentile score)
    """
    data = pd.read_csv("lib/weighted_data.csv", header=0)
    checkstyle_data = data["cs_density"].to_numpy()
    pmd_data = data["pmd_density"].to_numpy()
    total_data = data["total_density"].to_numpy()
    
    percentile_checkstyle = round(percentileofscore(checkstyle_data, checkStyle_error_density, kind="rank"))
    percentile_pmd = round(percentileofscore(pmd_data, pmd_error_density, kind="rank"))
    percentile_overall = round(percentileofscore(total_data, total_error_density, kind='rank'))
    
    return percentile_checkstyle, percentile_pmd, percentile_overall

def update_json (student_name, error_density, upload_dir_name):
    
    if not check_json_exists():
        print(f"Error: JSON file does not exist under {RECORDS_FILE_PATH}")
        return
    try:
        with open(RECORDS_FILE_PATH, 'r+') as file:
            content = file.read().strip()
            if content:
                data = json.loads(content)
            else:
                data = {}
            
            if not upload_dir_name:
                print("Failed to get upload directory name.")
                return
            
            if upload_dir_name not in data:
                data[upload_dir_name] = {}
            
            directory_data = data[upload_dir_name]

            if student_name not in directory_data:
                directory_data[student_name] = []
                
            student_data = directory_data[student_name]
            submission_count = len(student_data) + 1
            new_submission = {
                "counter": submission_count,
                "error density": error_density
            }
            
            student_data.append(new_submission)
            
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()
            print("JSON records updated successfully.")
        
    except Exception as e:
        print(e)
        print("Failed to update json")

def get_upload_dir_name():
    # load the build.xml file
    tree = ET.parse(BUILD_XML_PATH)
    root = tree.getroot()
    for property in root.findall("property"):
        if (property.get("name") == "src.dir"):
            return property.get("location")
    print(f"Failed to get upload directory name from {BUILD_XML_PATH}")

def check_json_exists():
    if not os.path.isfile(RECORDS_FILE_PATH):
        try:
            with open(RECORDS_FILE_PATH, 'w') as file:
                json.dump({}, file, indent=4)
            print(f"JSON records file created under {RECORDS_FILE_PATH}")
            return True
        except Exception as e:
            print(e)
            print("Failed to check if json exists")
            return False
    print(f"JSON records file found at {RECORDS_FILE_PATH}")
    return True

def compare_score_with_self(student_name, error_density, upload_dir_name):
    if not check_json_exists():
        print(f"Error: JSON file does not exist under {RECORDS_FILE_PATH}")
        return
    
    with open(RECORDS_FILE_PATH, 'r') as file:
        data = json.load(file)
        assignment_data = data.get(upload_dir_name, {})
        
        if not assignment_data:
            print(f"There are no records under {upload_dir_name}")
            return
        
        student_data = assignment_data.get(student_name, [])
        
        if not student_data:
            print(f"There are no records for {student_name} under {upload_dir_name}")
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

def compare_score_with_class(error_density, upload_dir_name):
    if not check_json_exists():
        print(f"Error: JSON file does not exist under {RECORDS_FILE_PATH}")
        return
    
    with open(RECORDS_FILE_PATH, 'r') as file:
        data = json.load(file)
        assignment_data = data.get(upload_dir_name, {})
        
        if not assignment_data: # if no records under this directory name
            print(f"There are no records under {upload_dir_name}")
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
            print(f"No error density records found under {upload_dir_name}")
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