def validate_worker_request(payload: dict) -> bool:
    if "WORKER" not in payload or "WORKER_UUID" not in payload:
        return False
    if payload["WORKER"] != "ALIVE":
        return False
    return True

def validate_status_report(payload: dict) -> bool:
    required = {"STATUS", "TASK", "WORKER_UUID"}
    if not required.issubset(payload.keys()):
        return False
    if payload["STATUS"] not in ["OK", "NOK"]:
        return False
    return True
