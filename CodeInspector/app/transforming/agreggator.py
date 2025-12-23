from app.infrastructure.models import(
    CheckstyleViolation,
    CheckstyleSeveritiesWithinFile,
    PmdViolation,
    PmdSeveritiesWithinFile,
    ProcessedViolations,
    UnitTestCase,
    UnitTestingResults
)

def process_checkstyle_violations (cs_violations: list[CheckstyleViolation]) -> ProcessedViolations:
    
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

def process_pmd_violations (pmd_violations: list[PmdViolation]) -> ProcessedViolations:
    
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

def get_failed_tests (unit_testing_report: UnitTestingResults) -> list[UnitTestCase]:
    
    unit_tests = unit_testing_report.testcases
    failed_tests: list[UnitTestCase] = []
        
    for test in unit_tests:
        if test.status == "FAILED":
            failed_tests.append(test)
                
    return failed_tests