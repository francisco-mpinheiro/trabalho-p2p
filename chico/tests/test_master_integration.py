import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import master

def test_master_has_counters():
    assert hasattr(master, 'tasks_completed')
    assert hasattr(master, 'tasks_failed')
    assert hasattr(master, 'supervisor_loop')
    print("test_master_has_counters passed")

if __name__ == "__main__":
    test_master_has_counters()
