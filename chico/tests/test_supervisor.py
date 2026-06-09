import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supervisor_client import generate_payload

def test_generate_payload():
    farm_state = {
        "tasks_pending": 10, "tasks_running": 2, "tasks_completed": 50, "tasks_failed": 1,
        "workers_alive": 3, "workers_idle": 1, "workers_borrowed": 0, "workers_received": 0,
        "workers_home": 3, "borrowed_workers": []
    }
    payload_str = generate_payload("michel_1", farm_state)
    payload = json.loads(payload_str)
    
    assert payload["role"] == "master"
    assert payload["task"] == "performance_report"
    assert "cpu" in payload["performance"]["system"]
    assert payload["performance"]["farm_state"]["tasks"]["tasks_pending"] == 10
    print("test_generate_payload passed")

if __name__ == "__main__":
    test_generate_payload()
