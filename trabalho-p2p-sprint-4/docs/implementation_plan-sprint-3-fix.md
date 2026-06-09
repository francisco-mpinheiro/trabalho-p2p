# Sprint 03 - Bugfixes P2P (CT01, CT06, CT08) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implementar as peças faltantes do protocolo P2P para gabaritar os cenários CT01 (Emprestar Worker), CT06 (Avisar devolução ao Master vizinho) e CT08 (Fallback de Worker em caso de falha do Master emprestado).

**Architecture:** 
- **CT08:** O Worker ganha inteligência para capturar o término anormal da conexão (no `finally` ou no bloco de erro) e checar se `ORIGINAL_MASTER_UUID` existe. Se sim, ele reseta seu host/port e volta pra casa automaticamente antes de tentar a reconexão.
- **CT06:** O Master passará a registrar o IP de origem dos workers emprestados em um dicionário `borrowed_origins`. Ao emitir o `command_release`, ele abrirá um socket TCP cliente rápido para esse IP de origem mandando o `notify_worker_returned`.
- **CT01:** O Master B, ao receber `request_help`, vai verificar se tem algum Worker `Local` no seu dicionário `known_workers`. Se sim, ele vai devolver `response_accepted`, e na sequência injetar o `command_redirect` direto no `writer` daquele Worker.

---

### Task 1: Correção do CT08 - Fallback do Worker ao Cair

**Files:**
- Modify: `worker.py`

- [ ] **Step 1: Adicionar lógica de restauração de IP no erro**
No arquivo `worker.py`, função `worker_client()`, alteraremos a lógica para capturar quando a conexão fecha inesperadamente e retornar ao master original.

```python
# Em worker.py, na função worker_client(), atualize o try/except:
                # ...
                await heartbeat_loop(reader, writer)
                
                writer.close()
                await writer.wait_closed()
                
            except ConnectionRefusedError:
                log_warning("Conexão recusada...")
                await asyncio.sleep(5)
            except asyncio.TimeoutError:
                log_warning("Timeout...")
                await asyncio.sleep(5)
            except Exception as e:
                log_error(f"Erro inesperado: {e}...")
                await asyncio.sleep(5)
            finally:
                global MASTER_HOST, MASTER_PORT, ORIGINAL_MASTER_UUID, is_temporary
                if ORIGINAL_MASTER_UUID and not is_temporary:
                    log_warning(f"Conexão com Master Emprestado caiu. Retornando para casa: {ORIGINAL_MASTER_UUID}")
                    host, port = ORIGINAL_MASTER_UUID.split(":")
                    MASTER_HOST = host
                    MASTER_PORT = int(port)
                    ORIGINAL_MASTER_UUID = None
```

---

### Task 2: Correção do CT06 - Notificação de Devolução (notify_worker_returned)

**Files:**
- Modify: `master.py`

- [ ] **Step 1: Armazenar a origem do worker emprestado**
Adicione um dicionário global no topo do arquivo: `borrowed_origins = {}`

No `handle_client`, quando processar `register_temporary_worker`:
```python
                            worker_uuid = msg_payload.get("worker_id")
                            orig = msg_payload.get("original_master_address")
                            known_workers[worker_uuid] = "Emprestado"
                            connected_workers[worker_uuid] = writer
                            borrowed_origins[worker_uuid] = orig # Salva a origem
```

- [ ] **Step 2: Emitir a notificação no monitor_load**
No `monitor_load`, no bloco `elif current_load < RELEASE_THRESHOLD`:
```python
            # ...
            for uid in borrowed:
                writer = connected_workers.get(uid)
                orig_master = borrowed_origins.get(uid)
                if writer and orig_master:
                    log_master(f"Carga normalizada. Devolvendo Worker {uid}...")
                    msg = build_message("command_release", {"original_master_address": orig_master})
                    try:
                        writer.write(msg.encode('utf-8'))
                        await writer.drain()
                    except:
                        pass
                    
                    # CT06: Envia notify_worker_returned pro Master Original
                    host, port = orig_master.split(":")
                    try:
                        m_reader, m_writer = await asyncio.open_connection(host, int(port))
                        notify_msg = build_message("notify_worker_returned", {"worker_id": uid})
                        m_writer.write(notify_msg.encode('utf-8'))
                        await m_writer.drain()
                        m_writer.close()
                        await m_writer.wait_closed()
                    except Exception as e:
                        log_error(f"Erro ao notificar Master vizinho da devolução: {e}")
                        
                    known_workers.pop(uid, None)
                    connected_workers.pop(uid, None)
                    borrowed_origins.pop(uid, None)
```

---

### Task 3: Correção do CT01 - Aceitar Pedido de Ajuda e Redirecionar

**Files:**
- Modify: `master.py`

- [ ] **Step 1: Atualizar envio de request_help**
No `monitor_load`, ajuste o envio do `request_help`:
```python
                    req = build_message("request_help", {
                        "master_id": MASTER_ID, 
                        "current_load": current_load, 
                        "capacity": MASTER_CAPACITY, 
                        "workers_needed": 1,
                        "master_address": f"{MASTER_HOST}:{MASTER_PORT}" # Adicionado
                    })
```

- [ ] **Step 2: Atualizar recebimento e aceite (response_accepted)**
No `handle_client`, na seção `if msg_type == "request_help":`
```python
                        if msg_type == "request_help":
                            # Verifica se há workers locais para emprestar
                            locals_available = [uid for uid, t in known_workers.items() if t == "Local"]
                            if locals_available:
                                chosen_worker = locals_available[0]
                                requester_addr = msg_payload.get("master_address", "127.0.0.1:5000")
                                
                                # Responde que aceitou
                                response = build_message("response_accepted", {
                                    "workers_offered": 1,
                                    "worker_details": [{"id": chosen_worker}]
                                }, req_id)
                                writer.write(response.encode('utf-8'))
                                await writer.drain()
                                log_master(f"Emprestando worker {chosen_worker} para {requester_addr}")
                                
                                # Redireciona o worker escolhido
                                worker_writer = connected_workers.get(chosen_worker)
                                if worker_writer:
                                    redirect_msg = build_message("command_redirect", {
                                        "new_master_address": requester_addr
                                    })
                                    try:
                                        worker_writer.write(redirect_msg.encode('utf-8'))
                                        await worker_writer.drain()
                                    except: pass
                                    
                                    known_workers.pop(chosen_worker, None)
                                    connected_workers.pop(chosen_worker, None)
                            else:
                                response = build_message("response_rejected", {"reason": "no_workers_available"}, req_id)
                                writer.write(response.encode('utf-8'))
                                await writer.drain()
```

## User Review Required
> [!IMPORTANT]
> - O plano usa as orientações da Sprint 03 e adapta o fluxo lógico nos 3 cenários faltantes com o mínimo de modificações intrusivas possível.
> - Aprova este plano para execução? Caso sim, posso rodar as modificações diretamente via `executing-plans` para testar.
