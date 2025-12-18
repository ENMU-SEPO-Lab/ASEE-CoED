"""
    The entry point of the API
"""

import json

def run_pipeline(checkstyle_xml, pmd_xml, junit_txt, grading_config) -> GradeResult:
    pass
    
if __name__ == "__main__":
    
    with open("build/test-reports/checkstyle-result.xml") as file:
        checkstyle_xml = file.read()

    with open("build/test-reports/pmd.xml") as file:
        pmd_xml = file.read()

    with open("build/test-reports/TEST-TestCases.txt") as file:
        junit_txt = file.read()

    with open("config/grading_config.json", "r") as file:
        grading_config = json.load(file)
    
    result = run_pipeline(checkstyle_xml, pmd_xml, junit_txt, grading_config)
    print(result)