from CodeInspector.app.infrastructure import CheckstyleViolation
import xml.etree.ElementTree as ET

def parse_checkstyle(xml_text: str) -> list[CheckstyleViolation]:
    try:
        root = ET.fromstring(xml_text)  # get tree root from txt file
        errors: list[CheckstyleViolation] = []
 
        for file_element in root.findall('file'):
 
            for error in file_element.findall('error'):
                
                source = file_element.attrib.get("source", "")
                parts = source.split(".")
                
                errors.append(
                    CheckstyleViolation(
                        file_name = file_element.attrib.get("name", ""),
                        line = int(error.attrib.get('line', "0")),
                        severity = file_element.attrib.get("severity", ""),
                        # split the string to get the second to last part, i.e the violation category
                        category = source.rsplit(".", 2)[-2],
                        # split the string to get the last part, i.e the specific violation type
                        type_name = source.rsplit(".", 1)[-1],
                        message = file_element.attrib.get("message", "")
                    )
                )
        return errors
    
    except ET.ParseError as e:
        print(f"Failed to parse XML: {e}")
        return []