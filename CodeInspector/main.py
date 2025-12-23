"""
    The entry point of the API
"""

import json
from app.paths import (
    UPLOAD_DIR, CS_XML_FILE, PMD_XML_FILE, JUNIT_RESULT_FILE, GRADING_CONFIG_FILE, GRADING_DIR
)
import app.transforming.helpers as helper
import app.transforming.validation as validator
import app.transforming.loc as line_counter
import app.parsing.parser as parser


def run_pipeline(checkstyle_xml, pmd_xml, junit_txt, grading_config):
    
    parsed = parser.parse_and_combine_test_files(checkstyle_xml, pmd_xml, junit_txt)
            
    check_date = helper.check_date() # get current date and format it    
    loc = line_counter.count_loc_in_dir(UPLOAD_DIR) # count the lines of code detected in the submission dir
    student_name = validator.extract_author_from_submission(UPLOAD_DIR)
    
    print(f"student name: {student_name}")
    
    violation_report = helper.build_violation_report(student_name, check_date, loc, parsed)
    
    helper.create_grading_dir(GRADING_DIR)
        
    # TODO: Grading and persistence
    
    return violation_report
    
if __name__ == "__main__":
    
    with open(CS_XML_FILE) as file:
        checkstyle_xml = file.read()

    with open(PMD_XML_FILE) as file:
        pmd_xml = file.read()

    with open(JUNIT_RESULT_FILE) as file:
        junit_txt = file.read()

    with open(GRADING_CONFIG_FILE, "r") as file:
        grading_config = json.load(file)
        
    print("Test files read successfully")
    
    result = run_pipeline(checkstyle_xml, pmd_xml, junit_txt, grading_config)
    print(result)