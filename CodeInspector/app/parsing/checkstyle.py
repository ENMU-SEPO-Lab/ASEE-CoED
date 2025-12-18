from CodeInspector.app.definitions.models import CheckstyleViolation
import xml.etree.ElementTree as ET

def parse_checkstyle(xml_text: str) -> list[CheckstyleViolation]:
    try:
        root = ET.fromstring(xml_text)  # get tree root from txt file
        errors: list[CheckstyleViolation] = []
 
        for file_element in root.findall('file'):
 
            for error in file_element.findall('error'):
                errors.append(
                    CheckstyleViolation(
                        file = file_element.attrib['name'],
                        line = error.attrib['line'],
                        severity = error.attrib['severity'],
                        message = error.attrib['message'],
                        source = error.attrib['source']
                    )
                )
        return errors
    
    except ET.ParseError as e:
        print(f"Failed to parse XML: {e}")
        return []