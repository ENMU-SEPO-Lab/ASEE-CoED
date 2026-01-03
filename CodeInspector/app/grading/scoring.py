from app.infrastructure.models import(
    ProcessedSubmission,
    ProcessedViolations,
    ProcessedJunitTests,
    SubmissionData
)
from pathlib import Path

def evaluate_submission(
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
    
    cs_score, cs_weighted_error = _calculate_static_analysis_tool_score(
        processed_data.cs_processed, 
        loc, 
        coding_stds_dict,
        weights_dict.get("checkstyle", {})
    )
    
    pmd_score, pmd_weighted_error = _calculate_static_analysis_tool_score(
        processed_data.pmd_processed, 
        loc, 
        coding_stds_dict,
        weights_dict.get("pmd", {})
    )
    
    coding_std_score = _calculate_coding_stds_score(cs_score, pmd_score)
    req_score, test_success_ratio = _calculate_requirements_score(
        processed_data.junit_processed, 
        req_dict
    )
    # run_score, run_ratio = calculate_runtime_score(processed_runtime_data, run_dict)
    run_score = run_dict.get("excellent", 20)
    
    overall_score = coding_std_score + req_score + run_score
    overall_weighted_error = cs_weighted_error + pmd_weighted_error
    
    top_n_cs_errors = processed_data.cs_processed.get_top_n_error_types_and_counts_in_subm(3)
    top_n_pmd_errors = processed_data.pmd_processed.get_top_n_error_types_and_counts_in_subm(3)
    
    upload_dir_name = upload_dir.name
    
    return SubmissionData(
        upload_dir_name,
        student_email,
        loc,
        cs_score,
        cs_weighted_error,
        pmd_score,
        pmd_weighted_error,
        test_success_ratio,
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
            total_errors_within_sev += current_severity.get_error_count_within_sev()
        
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

def _calculate_requirements_score(processed_junit: ProcessedJunitTests, req_dict: dict) -> tuple[int, float]:
    
    possible_scores = req_dict.values()
    max_score = req_dict.get("excellent", 60)
    number_of_tests = len(processed_junit.all_tests)
    number_of_failed_tests = len(processed_junit.failed_tests)
    
    print(f"number of failed tests: {number_of_failed_tests}\n number of tests: {number_of_tests}")
    
    possible_score_ratios = [round(score / max_score, 1) for score in possible_scores]
    test_success_ratio = 1 - round((number_of_failed_tests / number_of_tests), 1)
    print(f"test success ratio {test_success_ratio}")
    
    for score_ratio in possible_score_ratios:
        if test_success_ratio >= score_ratio:
            req_score = score_ratio * max_score
    
    return req_score, test_success_ratio

def _calculate_runtime_score(processed_runtime_data, run_dict: str) -> tuple[int, float]:
    # TODO runtime_score calculation
    return tuple(0, 0.0)
