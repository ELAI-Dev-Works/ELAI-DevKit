import json
from ..error_output_block import generate_error_block

def check_json(content: str) -> str:
    try:
        json.loads(content)
        return None
    except json.JSONDecodeError as e:
        return generate_error_block(content, str(e), e.lineno)
    except Exception as e:
        return generate_error_block(content, str(e), None)