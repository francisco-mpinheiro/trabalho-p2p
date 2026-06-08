# Sprint 02: Comunicação de Tarefas e Apresentação de Workers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the full lifecycle of a task between Worker and Master, including task requesting, queue management, simulated processing, and status acknowledgment (ACK), with strict parsing and case-sensitivity.

**Architecture:** 
- **Worker:** The `heartbeat_loop` will be refactored into a `task_loop`. It will present itself (`WORKER: ALIVE`), wait for a task, simulate processing, report the result (`STATUS: OK/NOK`), and wait for an `ACK`.
- **Master:** Will maintain a queue of tasks. The connection handler will use strict parsing to validate incoming payloads. It will hand out tasks when requested and acknowledge completions.
- **Protocol:** Strict JSON validation ensuring required fields are present, exact uppercase matching for control values, and tolerance for extra fields. Nenhuma dependência externa será utilizada (apenas `json` e `asyncio`).

**Tech Stack:** Python 3, `asyncio`, `json` (Testes Manuais).

---

### Task 1: Strict Parser and Validator Utility

**Files:**
- Create: `parser_utils.py`

- [ ] **Step 1: Implementação de validação de dicionários**

```python
# parser_utils.py
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
```

- [ ] **Step 2: Commit**

```bash
git add parser_utils.py
git commit -m "feat: add strict parser utility for worker requests and status"
```

---

### Task 2: Task Queue Management in Master

**Files:**
- Modify: `master.py`

- [ ] **Step 1: Adicionar classe TaskQueue**

```python
# In master.py, add the following before the handle_client function:
class TaskQueue:
    def __init__(self):
        self.tasks = []

    def add_task(self, task: dict):
        self.tasks.append(task)

    async def get_next_task(self) -> dict:
        if not self.tasks:
            return {"TASK": "NO_TASK"}
        return self.tasks.pop(0)

# Global task queue instance
global_task_queue = TaskQueue()
# Add a dummy task for testing distribution
global_task_queue.add_task({"TASK": "QUERY", "USER": "dummy_user"})
```

- [ ] **Step 2: Commit**

```bash
git add master.py
git commit -m "feat: implement task queue management in master"
```

---

### Task 3: Worker Presentation and Master Response

**Files:**
- Modify: `master.py`
- Modify: `worker.py`

- [ ] **Step 1: Implementar request no worker e dispatch no master**

```python
# In master.py
import json
from parser_utils import validate_worker_request, validate_status_report

# Update handle_client in master.py:
# Replace the old HEARTBEAT logic with:
# if validate_worker_request(payload):
#     response_payload = await global_task_queue.get_next_task()
#     response_message = json.dumps(response_payload) + "\n"
#     writer.write(response_message.encode('utf-8'))
#     await writer.drain()

# In worker.py, update heartbeat_loop to be task_loop:
# Send {"WORKER": "ALIVE", "WORKER_UUID": INSTANCE_UUID}
# If we have a master of origin, add "SERVER_UUID"
```

- [ ] **Step 2: Commit**

```bash
git add master.py worker.py
git commit -m "feat: implement worker presentation and master task dispatch"
```

---

### Task 4: Task Execution & Status Reporting (Worker)

**Files:**
- Modify: `worker.py`

- [ ] **Step 1: Função de simulação de processamento**

```python
# In worker.py
import random

async def simulate_processing(task: dict) -> str:
    from config import log_worker
    log_worker(f"Processando tarefa: {task}")
    await asyncio.sleep(random.uniform(0.5, 2.0))
    return "OK" if random.random() > 0.2 else "NOK"

# Update task_loop in worker.py to process the task if TASK != "NO_TASK"
# After processing, send:
# {"STATUS": result, "TASK": task.get("TASK"), "WORKER_UUID": INSTANCE_UUID}
# Wait for ACK.
```

- [ ] **Step 2: Commit**

```bash
git add worker.py
git commit -m "feat: implement simulated task processing and status reporting"
```

---

### Task 5: Master ACK & Auditing

**Files:**
- Modify: `master.py`

- [ ] **Step 1: Validação e resposta de ACK no Master**

```python
# In master.py
# Add logic to handle_client:
# elif validate_status_report(payload):
#     log_master(f"Auditoria: Tarefa {payload['TASK']} concluída com {payload['STATUS']} pelo Worker {payload['WORKER_UUID']}")
#     ack_message = json.dumps({"STATUS": "ACK"}) + "\n"
#     writer.write(ack_message.encode('utf-8'))
#     await writer.drain()
```

- [ ] **Step 2: Commit**

```bash
git add master.py
git commit -m "feat: implement master ACK and audit logging"
```
