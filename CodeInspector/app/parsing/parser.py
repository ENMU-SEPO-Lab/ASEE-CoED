from app.parsing import pmd
from app.parsing import checkstyle
from app.parsing import junit
from app.infrastructure.models import CombinedParsedViolations

def parse_and_combine_test_files (checkstyle_xml, pmd_xml, junit_txt) -> CombinedParsedViolations:
    
    # parse the testing result files
    parsed_checkstyle = checkstyle.parse_checkstyle(checkstyle_xml)
    parsed_pmd = pmd.parse_pmd(pmd_xml)
    parsed_junit = junit.parse_test_results(junit_txt)

    parsed = CombinedParsedViolations(
        checkstyle = parsed_checkstyle,
        pmd = parsed_pmd,
        unit_testing = parsed_junit
    )
    
    return parsed
