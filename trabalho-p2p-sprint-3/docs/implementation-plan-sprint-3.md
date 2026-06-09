# Sprint 03 P2P Negociation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar negociação autônoma Master-to-Master e redirecionamento dinâmico de Workers sob alta carga (Sprint 03).

**Architecture:** Adicionar roteamento de mensagens baseado no campo `type` para comandos de controle (M2M e redirecionamento). Manter o fluxo de tarefas original por compatibilidade (Sprint 02). O Master passa a atuar de forma concorrente como Servidor (para Workers e Masters) e Cliente (para envio do `request_help`). Serão introduzidos componentes de protocolo e estado no Master.

**Tech Stack:** Python 3.10+, `asyncio`, JSON.

---

### Task 1: Configurações de Carga e Vizinhos

**Files:**
- Modify: `config.py`

- [ ] **Step 1: Write the failing test / Prepare config structure**
Modifique o arquivo `config.py` para introduzir o tracking de carga e a rede de vizinhança P2P.

```python
# config.py
# Adicione após as definições do Worker:
MASTER_ID = os.getenv('MASTER_ID', 'Master-Local')
# Limiar para considerar o master saturado (e pedir ajuda)
MASTER_CAPACITY = int(os.getenv('MASTER_CAPACITY', '100'))
# Limiar para devolver os workers (efeito histerese)
RELEASE_THRESHOLD = int(os.getenv('RELEASE_THRESHOLD', '60'))

# Lista de endereços de Masters vizinhos no formato "HOST:PORT"
NEIGHBOR_MASTERS = os.getenv('NEIGHBOR_MASTERS', '127.0.0.1:5001').split(',')
```

- [ ] **Step 2: Commit**

```bash
git add config.py
git commit -m "feat: add sprint 03 P2P network and threshold configurations"
```

---

### Task 2: Protocolo de Mensagens e Utilitários

**Files:**
- Create: `protocol.py`

- [ ] **Step 1: Implementar o builder e parser M2M**
Crie um arquivo puro para agrupar toda a lógica de empacotamento (Sprint 03) para não poluir os arquivos da rede.

```python
# protocol.py
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
```

- [ ] **Step 2: Commit**

```bash
git add protocol.py
git commit -m "feat: json protocol handlers for P2P messages"
```

---

### Task 3: Redirecionamento Dinâmico no Worker

**Files:**
- Modify: `worker.py`

- [ ] **Step 1: Injetar suporte aos comandos de Master**
O Worker precisa conseguir ler comandos fora do fluxo ALIVE/QUERY. Adicionaremos o suporte de parsing e alteração dinâmica das globais do Master.

```python
# worker.py
# Modifique a lógica do response_payload para incluir:

                    # Suporte M2W (Master to Worker) - Sprint 03
                    msg_type = response_payload.get("type")
                    if msg_type == "command_redirect":
                        new_addr = response_payload.get("payload", {}).get("new_master_address")
                        log_warning(f"Sendo emprestado! Redirecionando para: {new_addr}")
                        host, port = new_addr.split(":")
                        
                        global MASTER_HOST, MASTER_PORT, ORIGINAL_MASTER_UUID
                        if not ORIGINAL_MASTER_UUID:
                            ORIGINAL_MASTER_UUID = f"{MASTER_HOST}:{MASTER_PORT}"
                        
                        MASTER_HOST = host
                        MASTER_PORT = int(port)
                        global is_temporary
                        is_temporary = True
                        break # Encerra conexão com master antigo e reconecta ao novo
                        
                    elif msg_type == "command_release":
                        orig_addr = response_payload.get("payload", {}).get("original_master_address")
                        log_warning(f"Liberado do empréstimo! Retornando para: {orig_addr}")
                        host, port = orig_addr.split(":")
                        MASTER_HOST = host
                        MASTER_PORT = int(port)
                        ORIGINAL_MASTER_UUID = None
                        is_temporary = False
                        break # Encerra e volta pro master original
```

- [ ] **Step 2: Lidar com register_temporary_worker**
Adicione no início do `while True` (antes de gerar o payload de ALIVE):

```python
        global is_temporary
        if 'is_temporary' in globals() and is_temporary:
            payload = {
                "type": "register_temporary_worker",
                "request_id": "req-temp",
                "payload": {
                    "worker_id": INSTANCE_UUID,
                    "original_master_address": ORIGINAL_MASTER_UUID
                }
            }
            is_temporary = False # Envia apenas 1 vez ao conectar
        else:
            payload = { "WORKER": "ALIVE", "WORKER_UUID": INSTANCE_UUID }
            if ORIGINAL_MASTER_UUID: payload["SERVER_UUID"] = ORIGINAL_MASTER_UUID
```

- [ ] **Step 3: Commit**
```bash
git add worker.py
git commit -m "feat: worker handles dynamic redirection and releases"
```

---

### Task 4: Motor Central de Roteamento P2P (Master)

**Files:**
- Modify: `master.py`

- [ ] **Step 1: Integração de Roteamento no handler principal**
```python
# master.py
from protocol import build_message, parse_message

# Dentro do while True:
            # Substitua a lógica de json.loads direta pelo parser
            message = data.decode('utf-8').strip()
            if message:
                try:
                    payload = json.loads(message)
                    msg_type = payload.get("type")
                    
                    if msg_type:
                        req_id = payload.get("request_id")
                        msg_payload = payload.get("payload", {})
                        
                        if msg_type == "request_help":
                            needed = msg_payload.get("workers_needed", 0)
                            # TO-DO Task 5: Validar capacidade e emitir response_accepted/rejected
                            response = build_message("response_rejected", {"reason": "no_workers_available"}, req_id)
                            writer.write(response.encode())
                            await writer.drain()
                            
                        elif msg_type == "register_temporary_worker":
                            worker_uuid = msg_payload.get("worker_id")
                            orig = msg_payload.get("original_master_address")
                            known_workers[worker_uuid] = "Emprestado"
                            log_master(f"Registrado Worker temporário {worker_uuid} vindo de {orig}")
                            
                        elif msg_type == "notify_worker_returned":
                            worker_id = msg_payload.get("worker_id")
                            log_master(f"Master vizinho confirmou devolução do Worker {worker_id}")
                            
                        continue # Pula o resto (fluxo Sprint 02)
                    
                    # Fluxo da Sprint 02 mantido para payloads sem "type" (ALIVE, STATUS)
                    # ... [codigo original]
```

- [ ] **Step 2: Commit**
```bash
git add master.py
git commit -m "feat: M2M packet router foundation"
```

---

### Task 5: Cliente P2P e Monitor de Saturação

**Files:**
- Modify: `master.py`

- [ ] **Step 1: Loop Automático de Saturação e Devolução**
Crie um task de background que monitora `task_queue.qsize()`. Se ultrapassar `MASTER_CAPACITY`, ele deve iterar em `NEIGHBOR_MASTERS` e enviar um `request_help` via TCP client assíncrono.
Se a carga cair abaixo de `RELEASE_THRESHOLD`, ele deve encontrar um worker marcado como "Emprestado", marcá-lo para receber o `command_release` (isso pode ser feito injetando um comando especial na fila dele, ou o `handle_client` precisa checar uma flag de liberação para fechar a conexão graciosamente).

> **Atenção Executores:** A implementação de concorrência com sockets bidirecionais (liberar worker durante o loop readline) vai requerer locks ou filas de eventos de desconexão. Cuidado com o vazamento de sockets ao desconectar.

## User Review Required
> [!IMPORTANT]
> - O protocolo exige que os Masters funcionem como Clientes e Servidores ao mesmo tempo.
> - A devolução (`command_release`) exige uma forma do loop de recebimento do Master notificar a tarefa `handle_client` específica daquele Worker que ele deve ser desconectado e enviado de volta. Isso implicará em registrar os objetos `writer` em uma tabela global `connected_workers`.
> - Aprova este plano de implementação TDD/Passo-a-passo? Se sim, posso despachar agentes em paralelo (ou executar diretamente) as Tasks 1, 2 e 3 sem impeditivos.
