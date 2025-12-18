from CodeInspector.app.definitions.models import UnitTestCase, UnitTestingResults, UnitTestingSummary

def parse_test_results(junit_txt: str):
    try:

        # Initialize structure
        result = {
            "testSuite": "",
            "summary": {
                "testsRun": 0,
                "failures": 0,
                "errors": 0,
                "skipped": 0,
                "timeElapsed": ""
            },
            "testCases": []
        }

        current_test_case = UnitTestCase()

        # Parse the file line by line
        for line in junit_txt.splitlines():
            line = line.strip()
            print("Test-Line: ", line)
            if line.startswith("Testsuite:"):
                result["testSuite"] = line.split(":")[1].strip()
            elif line.startswith("Tests run:"):
                parts = line.split(", ")
                result["summary"]["testsRun"] = int(parts[0].split(":")[1].strip())
                result["summary"]["failures"] = int(parts[1].split(":")[1].strip())
                result["summary"]["errors"] = int(parts[2].split(":")[1].strip())
                result["summary"]["skipped"] = int(parts[3].split(":")[1].strip())
                result["summary"]["timeElapsed"] = parts[4].split(":")[1].strip()
            elif line.startswith("Testcase:"):
                if current_test_case:
                    result["testCases"].append(current_test_case)
                parts = line.split(" took ")
                test_case_name = parts[0].split(":")[1].strip()
                time_taken = parts[1].strip()
                current_test_case = {
                    "name": test_case_name,
                    "time": time_taken,
                    "status": "PASSED"
                }
            elif line.startswith("FAILED"):
                if current_test_case:
                    current_test_case["status"] = "FAILED"
                    current_test_case["failureDetails"] = {}
            elif line.startswith("Caused an ERROR"): # define behavior for "Caused an ERROR" case
                if current_test_case:
                    current_test_case["status"] = "ERROR"
                    current_test_case["failureDetails"] = {}
            elif line.startswith("expected:") and current_test_case:
                message = line.strip()
                current_test_case["failureDetails"]["message"] = message
            elif line.startswith("at ") and current_test_case:
                # initialize failureDetails value as as empty dict to prevent None type
                if "failureDetails" not in current_test_case: 
                    current_test_case["failureDetails"] = {}
                if "stackTrace" not in current_test_case["failureDetails"]:
                    current_test_case["failureDetails"]["stackTrace"] = []
                current_test_case["failureDetails"]["stackTrace"].append(line.strip())

        # Add the last test case if exists
        if current_test_case:
            result["testCases"].append(current_test_case)

        return result
 
    except Exception as e:
        print(f"Failed to parse test results: {e}")
        return {}