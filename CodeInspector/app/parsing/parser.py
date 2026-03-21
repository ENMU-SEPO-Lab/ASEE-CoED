from app.parsing import pmd
from app.parsing import checkstyle
from app.parsing import junit
from app.infrastructure.models import CombinedParsedViolations

def parse_and_combine_test_files (cs_xml: str, pmd_xml: str, junit_xml: str) -> CombinedParsedViolations:
    """orchestrates the parsing. Assembles the parsed data into a single datastructure 
    for further processing

    Args:
        cs_xml (str): the CheckStyle result xml content as String
        pmd_xml (str): the PMD result xml content as String
        junit_txt (str): the Junit result content as String

    Returns:
        CombinedParsedViolations: structure containing all parsed testing result data
    """
    # parse the testing result files
    parsed_checkstyle = checkstyle.parse_checkstyle(cs_xml)
    parsed_pmd = pmd.parse_pmd(pmd_xml)
    parsed_junit = junit.parse_test_results_xml(junit_xml)

    parsed = CombinedParsedViolations(
        checkstyle = parsed_checkstyle,
        pmd = parsed_pmd,
        unit_testing = parsed_junit
    )
    
    return parsed
