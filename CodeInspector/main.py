"""
    The entry point of the API
"""

import json
import CodeInspector.app.transforming.helpers as helper
import CodeInspector.app.transforming.validation as validator
import CodeInspector.app.transforming.loc as line_counter
import CodeInspector.app.parsing.parser as parser

# Paths. should move to config file??
UPLOAD_DIR_PATH = "Upload_here/"
GRADE_REPORT_DIR = "build/grade-reports/"
BUILD_XML_PATH = "build.xml"
RECORDS_FILE_PATH = "records/records.json"

def run_pipeline(checkstyle_xml, pmd_xml, junit_txt, grading_config) -> GradeResult:
    
    parsed = parser.parse_and_combine_test_files(checkstyle_xml, pmd_xml, junit_txt)
    
    check_date = helper.check_date() # get current date and format it
    loc = line_counter.count_loc_in_dir(UPLOAD_DIR_PATH) # count the lines of code detected in the submission dir
    student_name = validator.extract_author_from_submission(UPLOAD_DIR_PATH)
    
    violation_report = helper.build_violation_report(student_name, check_date, loc, parsed)
    
    helper.create_grading_dir(GRADE_REPORT_DIR)
    
    # TODO: Grading and persistence
    
    pass
    
if __name__ == "__main__":
    
    with open("build/test-reports/checkstyle-result.xml") as file:
        checkstyle_xml = file.read()

    with open("build/test-reports/pmd.xml") as file:
        pmd_xml = file.read()

    with open("build/test-reports/TEST-TestCases.txt") as file:
        junit_txt = file.read()

    with open("config/grading_config.json", "r") as file:
        grading_config = json.load(file)
    
    result = run_pipeline(checkstyle_xml, pmd_xml, junit_txt, grading_config)
    print(result)