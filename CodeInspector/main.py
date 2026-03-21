"""
    The entry point of the API
"""

import sys
import json
from app.paths import (
    CS_XML_FILE, 
    PMD_XML_FILE, 
    JUNIT_RESULT_FILE, 
    GRADING_CONFIG_FILE, 
    GRADE_REPORTS_DIR,
    RECORDS_JSON_FILE,
    WEIGHTED_DATA_CSV,
    CS_ERROR_DATA_CSV,
    PMD_ERROR_DATA_CSV,
    get_upload_dir_path
)
import app.transforming.helpers as transf_helper
import app.transforming.validation as validator
import app.transforming.loc as line_counter
import app.transforming.aggregation as aggregator
import app.parsing.parser as parser
import app.grading.scoring as scorer
import app.grading.percentiles as percentile_scorer
import app.grading.helpers as grading_helper
import app.grading.reports as report_creator
import app.persistence.records as recorder
import app.persistence.error_counts as error_counter
from app.infrastructure.models import SubmissionData, ProcessedSubmission

def run_pipeline(
    checkstyle_xml: str, 
    pmd_xml: str, 
    junit_xml: str, 
    grading_config: dict
) -> tuple[SubmissionData, ProcessedSubmission]:
    """The pipeline

    Args:
        checkstyle_xml (str): checkstyle test result file
        pmd_xml (str): pmd test result file
        junit_txt (str): junit test result file
        grading_config (dict): grading_config.json contents

    Returns:
        tuple[SubmissionData, ProcessedSubmission]: Data to be extracted and stored in csv and json record files
    """
    
    try:
        upload_dir = get_upload_dir_path()
    except ValueError as e:
        # TODO: abort pipeline
        raise
    
    student_email = validator.extract_author_from_submission(upload_dir) # get student email
    grading_helper.ensure_json_file(RECORDS_JSON_FILE) # make sure records.json exists
    records = grading_helper.load_json(RECORDS_JSON_FILE)
    max_submission_num = grading_config.get("max_submissions_per_assignment")
    
    # check if maximum submissions for this assignment has been reached:
    if records.get(upload_dir.name):
        student_records = records.get(upload_dir.name).get(student_email)
        if student_records:
            num_submissions_made = len(records.get(upload_dir.name).get(student_email))
            if num_submissions_made >= max_submission_num:
                print(f"Student reached the maximum number of submissions ({max_submission_num}) for this assignment", file=sys.stderr) # stderr because stdout is reserved for the report_file_path printing
                # abort pipeline
                sys.exit()
        
    # send xml files to parser logic and receive CombinedParsedViolations object
    parsed = parser.parse_and_combine_test_files(checkstyle_xml, pmd_xml, junit_xml)
            
    check_date = transf_helper.check_date() # get current date and format it    
    # loc = line_counter.count_loc_in_dir(upload_dir) # count the lines of code detected in the submission dir (ignores blank lines and comments)
    loc = line_counter.count_lines_in_dir(upload_dir) # count the lines of code detected in the submission dir (ignores blank lines)
    
    # process the parsed data to prepare for score evaluation
    processed_submission = aggregator.process_submission_data(parsed)
    
    transf_helper.create_grading_dir(GRADE_REPORTS_DIR) # make sure dir for grade report exists
    # create grade_report_file path
    grade_report_file_path = transf_helper.create_grading_rep_file_name(GRADE_REPORTS_DIR, check_date) 
    
    # evaluate the submission
    submission_data = scorer.evaluate_submission(
        check_date,
        student_email, 
        processed_submission, 
        loc, 
        grading_config, 
        upload_dir
    )
    
    submission_data.report_file_path = grade_report_file_path
    weighted_error = submission_data.overall_weighted_error 
    
    percentiles_self, percentiles_class, percentiles_global = None, None, None
    
    if records:
        # relative to current semester submissions
        percentiles_self = percentile_scorer.compare_score_with_self(
            student_email, weighted_error, upload_dir, records, grading_config
        )
        
        percentiles_self_global = percentile_scorer.compare_score_with_self_global(
            student_email, weighted_error, upload_dir, records, grading_config
        )
        
        # relative to current semester submissions
        percentiles_class = percentile_scorer.compare_score_with_class(
            weighted_error, upload_dir, records, grading_config
        )
    
    grading_helper.check_for_weighted_data_csv(WEIGHTED_DATA_CSV)
    weighted_csv_data = grading_helper.load_weighted_data_csv(WEIGHTED_DATA_CSV)
    
    if not weighted_csv_data.empty:
        # relative to historical weighted dataset by previously taught course
        percentiles_global = percentile_scorer.get_global_percentile_score(
            submission_data.cs_weighted_error,
            submission_data.pmd_weighted_error,
            weighted_error,
            weighted_csv_data,
            grading_config 
        )
    
    # send data to grade report creation logic
    report_creator.create_grade_report(
        submission_data, 
        processed_submission,
        grading_config,
        percentiles_self, 
        percentiles_class, 
        percentiles_global,
        percentiles_self_global
    )
    
    # return data to main method for persistence file updates
    return (submission_data, processed_submission)
    
if __name__ == "__main__":
    
    with open(CS_XML_FILE, "r") as file:
        checkstyle_xml = file.read()

    with open(PMD_XML_FILE, "r") as file:
        pmd_xml = file.read()

    with open(JUNIT_RESULT_FILE, "r") as file:
        junit_xml = file.read()

    with open(GRADING_CONFIG_FILE, "r") as file:
        grading_config = json.load(file)
                
    print("Test files read successfully", file=sys.stderr) # stderr because stdout is reserved for the report_file_path printing
    
    # run the pipeline
    submission_data, processed_submission = run_pipeline(
        checkstyle_xml, 
        pmd_xml, 
        junit_xml, 
        grading_config
    )
    
    # update persistence files after pipeline finished
    recorder.update_json(submission_data, RECORDS_JSON_FILE)
    error_counter.update_csv_files(
        processed_submission, 
        CS_ERROR_DATA_CSV, 
        PMD_ERROR_DATA_CSV,
        submission_data.email)
    
    # print report file path to stdout for use in the github actions workflow
    print(submission_data.report_file_path)
    
    # print(submission_data, file=sys.stderr) # debugging
