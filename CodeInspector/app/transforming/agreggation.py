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
    
    cs_processed = _process_checkstyle_violations(parsed_data.checkstyle)
    pmd_processed = _process_pmd_violations(parsed_data.pmd)
    junit_processed = _process_junit(parsed_data.unit_testing)
    
    return ProcessedSubmission(cs_processed, pmd_processed, junit_processed)

def _process_checkstyle_violations (cs_violations: list[CheckstyleViolation]) -> ProcessedViolations:
    
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
    
    unit_tests = unit_testing_report.testcases
    failed_tests: list[UnitTestCase] = []
        
    for test in unit_tests:
        if test.status == "FAILED":
            failed_tests.append(test)
                
    return ProcessedJunitTests(unit_tests, failed_tests)
