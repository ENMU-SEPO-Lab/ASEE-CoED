from CodeInspector.app.definitions.models import PmdViolation
import xml.etree.ElementTree as ET

def _to_int(value_to_convert: str | None) -> int | None:
    return int(value_to_convert) if value_to_convert is not None and value_to_convert != "" else None

def parse_pmd(xml_text: str) -> list[PmdViolation]:
    
    try:
        root = ET.fromstring(xml_text) # get tree root from xml text
        # Define the namespace for PMD
        namespace = {'pmd': 'http://pmd.sourceforge.net/report/2.0.0'}
        # Extract information about violations
        violations: list[PmdViolation] = []
        
        for file_element in root.findall('pmd:file', namespace):
            for violation in file_element.findall('pmd:violation', namespace):
                violations.append(
                    PmdViolation(
                        file = file_element.get('name'),
                        begin_line = _to_int(violation.get('beginline')),
                        end_line = _to_int(violation.get('endline')),
                        begin_column = _to_int(violation.get('begincolumn')),
                        end_column = _to_int(violation.get('endcolumn')),
                        rule = violation.get('rule'),
                        ruleset = violation.get('ruleset'),
                        class_name = violation.get('class'),
                        method = violation.get('method'),
                        variable = violation.get('variable'),
                        priority = _to_int(violation.get('priority')),
                        message = violation.text.strip() if violation.text else '',
                        external_info_url= violation.get('externalInfoUrl')
                    )
                )
        return violations
    except ET.ParseError as e:
        print(f"Failed to parse PMD XML: {e}")
        return []