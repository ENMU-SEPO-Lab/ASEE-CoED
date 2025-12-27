"""
    The entry point of the API
"""

import json
from app.paths import (
    CS_XML_FILE, 
    PMD_XML_FILE, 
    JUNIT_RESULT_FILE, 
    GRADING_CONFIG_FILE, 
    GRADE_REPORTS_DIR,
    RECORDS_JSON_FILE,
    WEIGHTED_DATA_CSV,
    get_upload_dir_path
)
import app.transforming.helpers as transf_helper
import app.transforming.validation as validator
import app.transforming.loc as line_counter
import app.transforming.agreggation as aggregator
import app.parsing.parser as parser
import app.grading.scoring as scorer
import app.grading.percentiles as percentiler
import app.grading.helpers as grading_helper

def run_pipeline(checkstyle_xml, pmd_xml, junit_txt, grading_config):
    
    try:
        upload_dir = get_upload_dir_path()
    except ValueError as e:
        # TODO: abort pipeline
        raise
    
    parsed = parser.parse_and_combine_test_files(checkstyle_xml, pmd_xml, junit_txt)
            
    check_date = transf_helper.check_date() # get current date and format it    
    loc = line_counter.count_loc_in_dir(upload_dir) # count the lines of code detected in the submission dir
    student_name = validator.extract_author_from_submission(upload_dir)
    
    print(f"student name: {student_name}")
    
    violation_report = transf_helper.build_violation_report(student_name, check_date, loc, parsed)
    
    # process the parsed data to prepare for score evaluation
    processed_data = aggregator.process_submission_data(parsed)
    
    transf_helper.create_grading_dir(GRADE_REPORTS_DIR)
    grade_report_file_name = transf_helper.create_grading_rep_file_name(GRADE_REPORTS_DIR, check_date)
    
    submission_scores = scorer.calculate_submission_score(processed_data, loc, grading_config)
    
    grading_helper.ensure_json_file(RECORDS_JSON_FILE)
    records = grading_helper.load_json(RECORDS_JSON_FILE)
    weighted_error = submission_scores.overall_weighted_error
    
    if records:
        percentiles_self = percentiler.compare_score_with_self(
            student_name, weighted_error, upload_dir, records
        )
        percentiles_class = percentiler.compare_score_with_class(
            weighted_error, upload_dir, records
        )
    
    grading_helper.check_for_weighted_data_csv(WEIGHTED_DATA_CSV)
    csv_data = grading_helper.load_weighted_data_csv(WEIGHTED_DATA_CSV)
    
    if not csv_data.empty:
        percentiles_global = percentiler.get_global_percentile_score(
            submission_scores.cs_weighted_error,
            submission_scores.pmd_weighted_error,
            weighted_error,
            csv_data   
        )
        
    print(percentiles_self)
    print(percentiles_class)
    print(percentiles_global)
    
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
