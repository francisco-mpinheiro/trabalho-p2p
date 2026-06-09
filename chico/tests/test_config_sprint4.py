import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SUPERVISOR_HOST, SUPERVISOR_PORT, MAX_TASK, WARN_CPU_PERCENT, WARN_MEMORY_PERCENT, RELEASE_TASK

def test_config_vars_exist():
    assert SUPERVISOR_HOST == "nuted-ia.dev"
    assert SUPERVISOR_PORT == 443
    assert MAX_TASK == 100
    assert WARN_CPU_PERCENT == 85
    assert WARN_MEMORY_PERCENT == 85
    assert RELEASE_TASK == 60
    print("test_config_vars_exist passed")

if __name__ == "__main__":
    test_config_vars_exist()
