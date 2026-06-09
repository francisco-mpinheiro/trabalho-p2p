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
                    "workers_failed": farm_state.get("workers_failed", 0),
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
                # Mock inicial, futuramente integrado com real heartbeats se necessário
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
