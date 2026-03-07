from app.infrastructure.models import(
    CheckstyleViolation,
    CheckstyleSeveritiesWithinFile,
    PmdViolation,
    PmdSeveritiesWithinFile,
    ProcessedViolations,
    CombinedParsedViolations,
    UnitTestCase,
    UnitTestingResults,
    ProcessedJunitTests,
    ProcessedSubmission
)

def process_submission_data(parsed_data: CombinedParsedViolations) -> ProcessedSubmission:
    """orchestrates the processing

    Args:
        parsed_data (CombinedParsedViolations): the parsed data

    Returns:
        ProcessedSubmission: the processed data
    """
    cs_processed = _process_checkstyle_violations(parsed_data.checkstyle)
    pmd_processed = _process_pmd_violations(parsed_data.pmd)
    junit_processed = _process_junit(parsed_data.unit_testing)
    
    return ProcessedSubmission(cs_processed, pmd_processed, junit_processed)

def _process_checkstyle_violations (cs_violations: list[CheckstyleViolation]) -> ProcessedViolations:
    """processes the parsed CheckStyle violations by adding them to the ProcessedViolations structure one by one,
    which results in all violations sorted in the structure with the following bucket hierarchy:
     file_name -> severity -> category -> type_name

    Args:
        cs_violations (list[CheckstyleViolation]): list of parsed CheckStyle violations

    Returns:
        ProcessedViolations: structure holding processed CheckStyle violations
    """
    processed = ProcessedViolations(severity_class = CheckstyleSeveritiesWithinFile)
    
    for violation in cs_violations:
        processed.add_violation(
            violation.file_name,
            violation.severity,
            violation.category,
            violation.type_name,
            violation
        )
    
    return processed

def _process_pmd_violations (pmd_violations: list[PmdViolation]) -> ProcessedViolations:
    """processes the parsed PMD violations by adding them to the ProcessedViolations structure one by one,
    which results in all violations sorted in the structure with the following bucket hierarchy:
     file_name -> priority/severity -> category -> type_name

    Args:
        pmd_violations (list[PmdViolation]): list of parsed PMD violations

    Returns:
        ProcessedViolations: structure holding processed PMD violations
    """
    processed = ProcessedViolations(severity_class = PmdSeveritiesWithinFile)
    
    for violation in pmd_violations:
        processed.add_violation(
            violation.file_name,
            str(violation.priority),
            violation.ruleset,
            violation.rule,
            violation
        )
        
    return processed

def _process_junit (unit_testing_report: UnitTestingResults) -> ProcessedJunitTests:
    """processes the parsed Junit testing results by determining which tests failed and
    adding them to a separate list which is stored alongside the list containing all test
    for later evaluation

    Args:
        unit_testing_report (UnitTestingResults): the parsed Junit results

    Returns:
        ProcessedJunitTests: structure holding the processed Junit testing results
    """
    unit_tests = unit_testing_report.testcases
    failed_tests: list[UnitTestCase] = []
        
    for test in unit_tests:
        if test.status == "FAILED":
            failed_tests.append(test)
                
    return ProcessedJunitTests(unit_tests, failed_tests)
