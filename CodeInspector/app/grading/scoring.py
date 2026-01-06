from app.infrastructure.models import(
    ProcessedSubmission,
    ProcessedViolations,
    ProcessedJunitTests,
    SubmissionData,
)
from pathlib import Path

def evaluate_submission(
    check_date: str,
    student_email: str,
    processed_data: ProcessedSubmission, 
    loc: int, 
    grading_config: dict,
    upload_dir: Path | str
) -> SubmissionData:
    
    coding_stds_dict = grading_config.get("criteria_ratings", {}).get("coding_standards", {})
    req_dict = grading_config.get("criteria_ratings", {}).get("requirements", {})
    run_dict = grading_config.get("criteria_ratings", {}).get("runtime", {})
    weights_dict = grading_config.get("weights", {})
    
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
    run_score = run_dict.get("excellent", 20)
    
    overall_score = coding_std_score + req_score + run_score
    overall_weighted_error = cs_weighted_error + pmd_weighted_error
    
    cs_violation_count = cs_processed.get_error_count_within_submission()
    pmd_violation_count = pmd_processed.get_error_count_within_submission()
    
    top_n_cs_errors = cs_processed.get_top_n_error_types_and_counts_in_subm(3)
    top_n_pmd_errors = pmd_processed.get_top_n_error_types_and_counts_in_subm(3)
    
    upload_dir_name = upload_dir.name
    
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
    
    max_score = coding_std_config.get("excellent", 0)
    min_score = coding_std_config.get("unsatisfactory", 0)
    max_deduction = max_score
    total_penalty = 0
    weighted_error_density = 0

    for severity_class in tool_config:
        severity_weight_value = tool_config.get(severity_class, 0)
        total_errors_within_sev = 0
    
        # iterate over files in submission 
        for severity_data_within_file in processed_violations.files.values():
            # get severity data for current file
            current_severity = severity_data_within_file.severities.get(severity_class)
            total_errors_within_sev += current_severity.get_error_count_in_sev()
        
        absolute_penalty = total_errors_within_sev * severity_weight_value
        error_density = round(total_errors_within_sev / loc, 2)
        adjusted_penalty = absolute_penalty * error_density
        
        weighted_error_density += absolute_penalty / loc
        total_penalty += adjusted_penalty
    
    final_penalty = min(total_penalty, max_deduction)
    final_score = max(max_score - final_penalty, min_score)
    
    return final_score, round(weighted_error_density, 6)

def _calculate_coding_stds_score(cs_score: int, pmd_score: int) -> int:
    return round((cs_score + pmd_score) / 2)

def _calculate_requirements_score(
    processed_junit: ProcessedJunitTests, 
    req_dict: dict
) -> tuple[int, int, int]:
    
    possible_scores = req_dict.values()
    max_score = req_dict.get("excellent", 60)
    number_of_tests = len(processed_junit.all_tests)
    number_of_failed_tests = len(processed_junit.failed_tests)
    
    # [60/60, 48/60, 36/60, 10/60] 
    possible_score_ratios = [round(score / max_score, 1) for score in possible_scores]
    test_success_ratio = 1 - round((number_of_failed_tests / number_of_tests), 1)
    # 5/11 = 0.4545
    # 0.5
    
    for score_ratio in possible_score_ratios:
        if test_success_ratio >= score_ratio:
            req_score = score_ratio * max_score
    
    return req_score, number_of_tests, number_of_failed_tests

def _calculate_runtime_score(processed_runtime_data, run_dict: str) -> tuple[int, float]:
    # TODO runtime_score calculation
    return tuple(0, 0.0)
