from app.infrastructure.models import(
    ProcessedSubmission,
    ProcessedViolations,
    ProcessedJunitTests,
    SubmissionData,
)
from pathlib import Path
import sys

def evaluate_submission(
    check_date: str,
    student_email: str,
    processed_data: ProcessedSubmission, 
    loc: int, 
    grading_config: dict,
    upload_dir: Path | str
) -> SubmissionData:
    """evaluates the processed/sorted data. Calculates coding standard, and requirements score and creates
    other metrics for the grade report and data records.

    Args:
        check_date (str): the date and time the submission was made
        student_email (str): the email provided in the author tag of the submission
        processed_data (ProcessedSubmission): the processed submission data
        loc (int): Java lines of code found in the submission directory 
        grading_config (dict): grading config data from JSON file
        upload_dir (Path | str): the upload dir path, needed for Assignment name

    Returns:
        SubmissionData: the data of the evaluated submission
    """
    
    coding_stds_dict = grading_config.get("criteria_ratings", {}).get("coding_standards", {})
    req_dict = grading_config.get("criteria_ratings", {}).get("requirements", {})
    run_dict = grading_config.get("criteria_ratings", {}).get("runtime", {})
    eff_dict = grading_config.get("criteria_rating", {}).get("efficiency", {})
    weights_dict = grading_config.get("weights", {})
    top_n_error_num = grading_config.get("top_n_errors", 3)
    
    cs_processed = processed_data.cs_processed
    pmd_processed = processed_data.pmd_processed
    junit_processed = processed_data.junit_processed
    
    cs_score, cs_weighted_error = _calculate_static_analysis_tool_score(
        cs_processed, 
        loc, 
        coding_stds_dict,
        weights_dict.get("checkstyle", {})
    )
    
    pmd_score, pmd_weighted_error = _calculate_static_analysis_tool_score(
        pmd_processed, 
        loc, 
        coding_stds_dict,
        weights_dict.get("pmd", {})
    )
    
    coding_std_score = _calculate_coding_stds_score(cs_score, pmd_score)
    
    req_score, junit_test_count, junit_failed_test_count = _calculate_requirements_score(
        junit_processed, 
        req_dict
    )
    
    # run_score, run_ratio = calculate_runtime_score(processed_runtime_data, run_dict)
    # TODO: dynamic calculation of runtime and efficiency scores 02/25/2026
    run_score = run_dict.get("excellent", 20)
    eff_score = eff_dict.get("excellent", 10)
    
    overall_score = coding_std_score + req_score + run_score + eff_score
    overall_weighted_error = cs_weighted_error + pmd_weighted_error
    
    cs_violation_count = cs_processed.get_error_count_within_submission()
    pmd_violation_count = pmd_processed.get_error_count_within_submission()
    
    top_n_cs_errors = cs_processed.get_top_n_error_types_and_counts_in_subm(top_n_error_num)
    top_n_pmd_errors = pmd_processed.get_top_n_error_types_and_counts_in_subm(top_n_error_num)
    
    upload_dir_name = upload_dir.name # ..../CodeInspector/Assignment_1
    
    cs_sev_counts = cs_processed.get_severity_counts()
    pmd_sev_counts = pmd_processed.get_severity_counts()
    
    return SubmissionData(
        check_date,
        upload_dir_name,
        student_email,
        loc,
        cs_score,
        cs_weighted_error,
        cs_violation_count,
        cs_sev_counts,
        pmd_score,
        pmd_weighted_error,
        pmd_violation_count,
        pmd_sev_counts,
        junit_test_count,
        junit_failed_test_count,
        coding_std_score,
        req_score,
        eff_score,
        run_score,
        overall_score,
        overall_weighted_error,
        top_n_cs_errors,
        top_n_pmd_errors
    )

def _calculate_static_analysis_tool_score(
    processed_violations: ProcessedViolations, 
    loc: int,
    coding_std_config: dict,
    tool_config: dict
) -> tuple[int, int]:
    """calculates the score of either static analysis tool, based on the processed 
    violation reports provided

    Args:
        processed_violations (ProcessedViolations): processed violations (CheckStyle or PMD)
        loc (int): lines of code in the submission
        coding_std_config (dict): grading config data for scoring purposes
        tool_config (dict): tool specific config data (CheckStyle or PMD)

    Returns:
        tuple[int, int]: [final_score, tool_specific_weighted_error_density]
    """
    
    max_score = coding_std_config.get("excellent", 0)
    min_score = coding_std_config.get("unsatisfactory", 0)
    max_deduction = max_score
    total_penalty = 0
    weighted_error_density = 0

    # the grading algorithm
    
    # collect violation count across each severity class individually, so that the weight can 
    # be applied after each iteration
    for severity_class in tool_config:
        # the weight to be applied once all violations of this severity have been counted
        severity_weight_value = tool_config.get(severity_class, 0)
        total_errors_within_sev = 0
    
        # iterate over files in submission 
        for severity_data_within_file in processed_violations.files.values():
            # get severity data for current file
            current_severity = severity_data_within_file.severities.get(severity_class)
            total_errors_within_sev += current_severity.get_error_count_in_sev()
        
        absolute_penalty = total_errors_within_sev * severity_weight_value # severity weight is applied to the violation count
        error_density = round(total_errors_within_sev / loc, 2) # unweighted error density
        adjusted_penalty = absolute_penalty * error_density # adjusted penalty for scoring purpose
        
        weighted_error_density += absolute_penalty / loc # weighted error density of the current severity is added to the overall
        total_penalty += adjusted_penalty # adjusted penalty of the current severity is added to the total penalty
    
    final_penalty = min(total_penalty, max_deduction)
    final_score = max(max_score - final_penalty, min_score)
    
    return final_score, round(weighted_error_density, 6)

def _calculate_coding_stds_score(cs_score: int, pmd_score: int) -> int:
    return round((cs_score + pmd_score) / 2)

def _calculate_requirements_score(
    processed_junit: ProcessedJunitTests, 
    req_dict: dict
) -> tuple[int, int, int]:
    """determine the requirements score of the submission based on Junit testing results

    Args:
        processed_junit (ProcessedJunitTests): processed Junit testing results
        req_dict (dict): grading config data for scoring purposes

    Returns:
        tuple[int, int, int]: [req_score, total_number_of_tests, number_of_tests_failed]
    """
    
    possible_scores = req_dict.values()
    max_score = req_dict.get("excellent", 60)
    number_of_tests = len(processed_junit.all_tests)
    number_of_failed_tests = len(processed_junit.failed_tests)
    
    # [60/60, 48/60, 36/60, 10/60] 
    possible_score_ratios = [round(score / max_score, 1) for score in possible_scores]
    print(possible_score_ratios, file=sys.stderr)
    test_success_ratio = 1
    
    # if unit tests were ran
    if number_of_tests > 0:
        test_success_ratio = 1 - round((number_of_failed_tests / number_of_tests), 1)
    # 1/12 = 0.08333
    # test_success_ratio = 1 - 0.1 = 0.9  
    
    print(f"test_success_ratio: {test_success_ratio}", file=sys.stderr)
    
    for score_ratio in possible_score_ratios:
        if test_success_ratio >= score_ratio:
            req_score = int(score_ratio * max_score)
            print(f"chose score ratio: {score_ratio}")
            break
    
    return req_score, number_of_tests, number_of_failed_tests

def _calculate_runtime_score(processed_runtime_data, run_dict: str) -> tuple[int, float]:
    # TODO runtime_score calculation
    return tuple(0, 0.0)
