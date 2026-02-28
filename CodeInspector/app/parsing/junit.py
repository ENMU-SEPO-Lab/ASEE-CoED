from app.infrastructure.models import (
    UnitTestCase, 
    UnitTestingResults, 
    UnitTestingSummary, 
    TestFailureDetails
)

def parse_test_results(junit_txt: str) -> UnitTestingResults:
    """parses the junit test result txt file

    Args:
        junit_txt (str): junit result file content as String

    Raises:
        ValueError: if format invalid

    Returns:
        UnitTestingResults: structure containing the summary, list of testcases, and test_suite
    """
    try:
        current_test_case: UnitTestCase | None = None
        summary = UnitTestingSummary()
        result = UnitTestingResults(summary = summary, testcases = [], test_suite = "")

        # Parse the file line by line
        for line in junit_txt.splitlines():
            
            line = line.strip()
            
            if line.startswith("Testsuite:"):
                result.test_suite = line.split(":")[1].strip()
                
            elif line.startswith("Tests run:"):
                parts = line.split(", ")
                summary.tests_ran = int(parts[0].split(":")[1].strip())
                summary.failures = int(parts[1].split(":")[1].strip())
                summary.errors = int(parts[2].split(":")[1].strip())
                summary.skipped = int(parts[3].split(":")[1].strip())
                summary.time_elapsed = parts[4].split(":")[1].strip()
                
            elif line.startswith("Testcase:"):
                
                if current_test_case is not None: # to avoid storing the default None value in the first iteration
                    result.testcases.append(current_test_case) # storing parsed testcase from previous iteration
                    
                parts = line.split(" took ")
                test_case_name = parts[0].split(":")[1].strip()
                time_taken = parts[1].strip()
                
                current_test_case = UnitTestCase(
                    name = test_case_name,
                    time = time_taken,
                    status = "PASSED" 
                )
                
            elif line.startswith("FAILED") and current_test_case:
                current_test_case.status = "FAILED"
                current_test_case.failure_details = TestFailureDetails()
                
            elif line.startswith("Caused an ERROR") and current_test_case: # define behavior for "Caused an ERROR" case
                current_test_case.status = "ERROR"
                current_test_case.failure_details = TestFailureDetails()
                
            elif line.startswith("expected:") and current_test_case.failure_details:
                current_test_case.failure_details.message = line
                
            elif line.startswith("at ") and current_test_case.failure_details:
                current_test_case.failure_details.stack_trace.append(line)

        # Add the last test case if exists
        if current_test_case:
            result.testcases.append(current_test_case)

        return result
 
    except Exception as e:
        print(f"Failed to parse test results: {e}")
        raise ValueError("Invalid JUnit test output") from e