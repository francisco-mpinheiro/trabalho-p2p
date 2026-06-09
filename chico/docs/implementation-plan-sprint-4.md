# Sprint 04 Supervisor de Métricas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar o envio de métricas de hardware e do farm P2P para o Supervisor central utilizando sockets TCP puros com TLS (sem HTTP), rodando a cada 10 segundos no Master.

**Architecture:** Isolar a lógica de coleta de OS (psutil), geração do Payload JSON e cliente TCP TLS num módulo `supervisor_client.py`. O `master.py` instanciará uma task assíncrona para chamar esse cliente periodicamente injetando o estado atual das filas.

**Tech Stack:** Python 3, `asyncio`, `ssl`, `psutil`.

---

### Task 1: Setup de Dependências e Configurações

**Files:**
- Create: `requirements.txt`
- Modify: `config.py`
- Create: `tests/test_config_sprint4.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config_sprint4.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py tests/test_config_sprint4.py`
Expected: FAIL with ImportError (cannot import name 'SUPERVISOR_HOST')

- [ ] **Step 3: Write minimal implementation**

```python
# Em config.py (adicione no final)
# Configurações do Supervisor (Sprint 04)
SUPERVISOR_HOST = os.getenv('SUPERVISOR_HOST', 'nuted-ia.dev')
SUPERVISOR_PORT = int(os.getenv('SUPERVISOR_PORT', '443'))
SUPERVISOR_TLS = True
SUPERVISOR_SNI = "nuted-ia.dev"

MAX_TASK = int(os.getenv('MAX_TASK', '100'))
WARN_CPU_PERCENT = int(os.getenv('WARN_CPU_PERCENT', '85'))
WARN_MEMORY_PERCENT = int(os.getenv('WARN_MEMORY_PERCENT', '85'))
RELEASE_TASK = int(os.getenv('RELEASE_TASK', '60'))
```

```text
# Em requirements.txt
psutil==5.9.8
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py tests/test_config_sprint4.py`
Expected: PASS (prints "test_config_vars_exist passed")

- [ ] **Step 5: Commit**

```bash
git add config.py requirements.txt tests/test_config_sprint4.py
git commit -m "feat: add config variables and requirements for sprint 4"
```

---

### Task 2: Cliente do Supervisor e Coleta de Métricas

**Files:**
- Create: `supervisor_client.py`
- Create: `tests/test_supervisor.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_supervisor.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py tests/test_supervisor.py`
Expected: FAIL with ModuleNotFoundError (No module named 'supervisor_client')

- [ ] **Step 3: Write minimal implementation**

```python
# supervisor_client.py
import json
import uuid
import ssl
import asyncio
from datetime import datetime, timezone
import psutil
import socket
from config import SUPERVISOR_HOST, SUPERVISOR_PORT, SUPERVISOR_SNI, MAX_TASK, WARN_CPU_PERCENT, WARN_MEMORY_PERCENT, RELEASE_TASK, log_master, log_error

def generate_payload(server_uuid: str, farm_state: dict) -> str:
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Estimativa de uptime do node atual
    uptime_seconds = int(datetime.now().timestamp() - psutil.boot_time())
    
    # Tratamento para load_average (no Windows, psutil.getloadavg() não existe em versões antigas)
    load1, load5, load15 = (0.0, 0.0, 0.0)
    if hasattr(psutil, "getloadavg"):
        load1, load5, load15 = psutil.getloadavg()
    
    payload = {
        "server_uuid": server_uuid,
        "hostname": f"{server_uuid}.farm.local",
        "role": "master",
        "task": "performance_report",
        "timestamp": now_iso,
        "message_id": str(uuid.uuid4()),
        "payload_version": "sprint4-monitor",
        "performance": {
            "system": {
                "uptime_seconds": uptime_seconds,
                "load_average_1m": load1,
                "load_average_5m": load5,
                "cpu": {
                    "usage_percent": psutil.cpu_percent(interval=None),
                    "count_logical": psutil.cpu_count(logical=True),
                    "count_physical": psutil.cpu_count(logical=False)
                },
                "memory": {
                    "total_mb": mem.total // 1048576,
                    "available_mb": mem.available // 1048576,
                    "percent_used": mem.percent,
                    "memory_used": mem.used // 1048576
                },
                "disk": {
                    "total_gb": round(disk.total / 1073741824, 2),
                    "free_gb": round(disk.free / 1073741824, 2),
                    "percent_used": disk.percent
                }
            },
            "farm_state": {
                "workers": {
                    "total_registered": farm_state.get("workers_alive", 0),
                    "workers_utilization": farm_state.get("tasks_running", 0),
                    "workers_alive": farm_state.get("workers_alive", 0),
                    "workers_idle": farm_state.get("workers_idle", 0),
                    "workers_borrowed": farm_state.get("workers_borrowed", 0),
                    "workers_received": farm_state.get("workers_received", 0),
                    "workers_failed": 0,
                    "workers_home": farm_state.get("workers_home", 0),
                    "workers_available_capacity": farm_state.get("workers_idle", 0),
                    "borrowed_workers": farm_state.get("borrowed_workers", [])
                },
                "tasks": {
                    "tasks_pending": farm_state.get("tasks_pending", 0),
                    "tasks_running": farm_state.get("tasks_running", 0),
                    "tasks_completed": farm_state.get("tasks_completed", 0),
                    "tasks_failed": farm_state.get("tasks_failed", 0),
                    "oldest_task_age_s": 0
                }
            },
            "config_thresholds": {
                "max_task": MAX_TASK,
                "warn_cpu_percent": WARN_CPU_PERCENT,
                "warn_memory_percent": WARN_MEMORY_PERCENT,
                "release_task": RELEASE_TASK
            },
            "neighbors": [
                # Mock inicial, futuramente integrado com real heartbeats
            ]
        }
    }
    return json.dumps(payload) + "\n"

async def send_performance_report(server_uuid: str, farm_state: dict):
    payload_str = generate_payload(server_uuid, farm_state)
    ssl_context = ssl.create_default_context()
    
    try:
        reader, writer = await asyncio.open_connection(
            SUPERVISOR_HOST, SUPERVISOR_PORT, 
            ssl=ssl_context, server_hostname=SUPERVISOR_SNI
        )
        writer.write(payload_str.encode('utf-8'))
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        log_master(f"Relatório de performance enviado ao Supervisor ({SUPERVISOR_HOST}).")
    except Exception as e:
        log_error(f"Falha ao enviar relatório ao Supervisor: {e}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pip install psutil`
Run: `py tests/test_supervisor.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add supervisor_client.py tests/test_supervisor.py
git commit -m "feat: implement supervisor metric generation and TLS TCP client"
```

---

### Task 3: Integração do Reporte no Master

**Files:**
- Modify: `master.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_master_integration.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py tests/test_master_integration.py`
Expected: FAIL with AssertionError (master has no attribute 'tasks_completed')

- [ ] **Step 3: Write minimal implementation**

```python
# Em master.py, no topo abaixo das variáveis globais existentes:
tasks_completed = 0
tasks_failed = 0
from supervisor_client import send_performance_report
from config import MASTER_ID

# Na função handle_client, após ler "STATUS": "OK"
# ... onde diz: worker_type = known_workers.get(worker_uuid, "Desconhecido")
# Adicionar:
                        global tasks_completed, tasks_failed
                        if status == "OK":
                            tasks_completed += 1
                        else:
                            tasks_failed += 1

# Adicionar a rotina loop:
async def supervisor_loop():
    while True:
        await asyncio.sleep(10)
        
        alive = len(known_workers)
        received = sum(1 for t in known_workers.values() if t == "Emprestado")
        home = alive - received
        
        # Borrowed workers out (simples heurística temporária: não mapeamos quem saiu perfeitamente ainda, 
        # mas assumimos 0 para o relatório local base)
        out = 0 
        
        borrowed_list = []
        for uid in [k for k,v in known_workers.items() if v == "Emprestado"]:
            orig = borrowed_origins.get(uid, "unknown")
            borrowed_list.append({"direction": "in", "peer_uuid": orig})
            
        farm_state = {
            "tasks_pending": task_queue.qsize(),
            "tasks_running": 0, # Difícil rastrear num sistema assíncrono stateless, mandamos 0 ou o número da fila
            "tasks_completed": tasks_completed,
            "tasks_failed": tasks_failed,
            "workers_alive": alive,
            "workers_idle": alive, 
            "workers_borrowed": out,
            "workers_received": received,
            "workers_home": home,
            "borrowed_workers": borrowed_list
        }
        await send_performance_report(MASTER_ID, farm_state)

# Em main():
# Adicionar: asyncio.create_task(supervisor_loop())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py tests/test_master_integration.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add master.py tests/test_master_integration.py
git commit -m "feat: integrate supervisor periodic reporting loop into master"
```
