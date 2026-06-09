import json
import uuid

def build_message(msg_type: str, payload: dict, request_id: str = None) -> str:
    if not request_id:
        request_id = str(uuid.uuid4())
    msg = {
        "type": msg_type,
        "request_id": request_id,
        "payload": payload
    }
    return json.dumps(msg) + "\n"

def parse_message(raw_str: str) -> tuple:
    try:
        data = json.loads(raw_str.strip())
        return data.get("type"), data.get("request_id"), data.get("payload", {})
    except json.JSONDecodeError:
        return None, None, {}
