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
    junit_txt: str, 
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
    
    # send xml files to parser logic and receive CombinedParsedViolations object
    parsed = parser.parse_and_combine_test_files(checkstyle_xml, pmd_xml, junit_txt)
            
    check_date = transf_helper.check_date() # get current date and format it    
    loc = line_counter.count_loc_in_dir(upload_dir) # count the lines of code detected in the submission dir
    student_email = validator.extract_author_from_submission(upload_dir) # get student email
    
    # process the parsed data to prepare for score evaluation
    processed_submission = aggregator.process_submission_data(parsed)
    
    transf_helper.create_grading_dir(GRADE_REPORTS_DIR) # make sure dir for grade report exists
    # create grade_report_file name
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
    
    grading_helper.ensure_json_file(RECORDS_JSON_FILE) # make sure records.json exists
    records = grading_helper.load_json(RECORDS_JSON_FILE)
    weighted_error = submission_data.overall_weighted_error 
    
    percentiles_self, percentiles_class, percentiles_global = None, None, None
    
    if records:
        # relative to current semester submissions
        percentiles_self = percentile_scorer.compare_score_with_self(
            student_email, weighted_error, upload_dir, records
        )
        # relative to current semester submissions
        percentiles_class = percentile_scorer.compare_score_with_class(
            weighted_error, upload_dir, records
        )
    
    grading_helper.check_for_weighted_data_csv(WEIGHTED_DATA_CSV)
    weighted_csv_data = grading_helper.load_weighted_data_csv(WEIGHTED_DATA_CSV)
    
    if not weighted_csv_data.empty:
        # relative to historical weighted dataset by previously taught course
        percentiles_global = percentile_scorer.get_global_percentile_score(
            submission_data.cs_weighted_error,
            submission_data.pmd_weighted_error,
            weighted_error,
            weighted_csv_data   
        )
    
    # send data to grade report creation logic
    report_creator.create_grade_report(
        submission_data, 
        processed_submission,
        percentiles_self, 
        percentiles_class, 
        percentiles_global
    )
    
    # return data to main method for persistence file updates
    return (submission_data, processed_submission)
    
if __name__ == "__main__":
    
    with open(CS_XML_FILE, "r") as file:
        checkstyle_xml = file.read()

    with open(PMD_XML_FILE, "r") as file:
        pmd_xml = file.read()

    with open(JUNIT_RESULT_FILE, "r") as file:
        junit_txt = file.read()

    with open(GRADING_CONFIG_FILE, "r") as file:
        grading_config = json.load(file)
        
    print("Test files read successfully")
    
    # run the pipeline
    submission_data, processed_submission = run_pipeline(
        checkstyle_xml, 
        pmd_xml, 
        junit_txt, 
        grading_config
    )
    
    # update persistence files after pipeline finished
    recorder.update_json(submission_data, RECORDS_JSON_FILE)
    error_counter.update_csv_files(
        processed_submission, 
        CS_ERROR_DATA_CSV, 
        PMD_ERROR_DATA_CSV,
        submission_data.email)
    
    # print(submission_data) # debugging
