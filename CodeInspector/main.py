"""
    The entry point of the API
"""

import json
from app.paths import (
    UPLOAD_DIR, CS_XML_FILE, PMD_XML_FILE, JUNIT_RESULT_FILE, GRADING_CONFIG_FILE, GRADE_REPORTS_DIR
)
import app.transforming.helpers as helper
import app.transforming.validation as validator
import app.transforming.loc as line_counter
import app.transforming.agreggation as aggregator
import app.parsing.parser as parser
import app.grading.scoring as scorer

def run_pipeline(checkstyle_xml, pmd_xml, junit_txt, grading_config):
    
    parsed = parser.parse_and_combine_test_files(checkstyle_xml, pmd_xml, junit_txt)
            
    check_date = helper.check_date() # get current date and format it    
    loc = line_counter.count_loc_in_dir(UPLOAD_DIR) # count the lines of code detected in the submission dir
    student_name = validator.extract_author_from_submission(UPLOAD_DIR)
    
    print(f"student name: {student_name}")
    
    violation_report = helper.build_violation_report(student_name, check_date, loc, parsed)
    # print(violation_report)
    
    # process the parsed data to prepare for score evaluation
    processed_data = aggregator.process_submission_data(parsed)
    
    helper.create_grading_dir(GRADE_REPORTS_DIR)
    grade_report_file_name = helper.create_grading_rep_file_name(GRADE_REPORTS_DIR, check_date)
    
    submission_scores = scorer.calculate_submission_score(processed_data, loc, grading_config)
    
    
    # TODO: Grading and persistence
    
    return submission_scores
    
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