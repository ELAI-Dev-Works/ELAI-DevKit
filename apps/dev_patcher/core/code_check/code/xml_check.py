import xml.etree.ElementTree as ET
import re
from ..error_output_block import generate_error_block

def check_xml(content: str) -> str:
    try:
        ET.fromstring(content)
        return None
    except ET.ParseError as e:
        err_msg = str(e)
        match = re.search(r'line (\d+)', err_msg)
        line_num = int(match.group(1)) if match else None
        return generate_error_block(content, err_msg, line_num)
    except Exception as e:
        return generate_error_block(content, str(e), None)