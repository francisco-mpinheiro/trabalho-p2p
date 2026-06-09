import asyncio
import json
import random
from config import MASTER_HOST, MASTER_PORT, log_master, log_error, INSTANCE_UUID, MASTER_CAPACITY, RELEASE_THRESHOLD, NEIGHBOR_MASTERS, MASTER_ID
from protocol import build_message, parse_message

# Fila de tarefas real (Queue) do Master
task_queue = asyncio.Queue()

# Dicionário para rastrear os tipos dos workers (Local ou Emprestado)
known_workers = {}
# Dicionário para manter referência ao writer ativo de cada worker conectado
connected_workers = {}
# Dicionário para guardar o endereço do Master de origem dos workers emprestados
borrowed_origins = {}

async def populate_tasks():
    """Adiciona tarefas à fila periodicamente para testes."""
    task_id = 1
    while True:
        # Adiciona uma nova tarefa na fila a cada 3 segundos
        new_task = {
            "TASK": "QUERY",
            "USER": f"usuario_teste_{task_id}"
        }
        await task_queue.put(new_task)
        log_master(f"[SISTEMA] Nova tarefa adicionada à fila: {new_task['USER']} (Total na fila: {task_queue.qsize()})")
        task_id += 1
        await asyncio.sleep(8)

async def monitor_load():
    """Monitora a saturação da fila e interage com Masters vizinhos."""
    while True:
        await asyncio.sleep(5)
        current_load = task_queue.qsize()
        
        if current_load > MASTER_CAPACITY:
            for neighbor in NEIGHBOR_MASTERS:
                if not neighbor or ":" not in neighbor: continue
                host, port = neighbor.split(":")
                try:
                    log_master(f"Saturado ({current_load}/{MASTER_CAPACITY})! Pedindo ajuda ao vizinho {neighbor}...")
                    reader, writer = await asyncio.open_connection(host, int(port))
                    req = build_message("request_help", {
                        "master_id": MASTER_ID, 
                        "current_load": current_load, 
                        "capacity": MASTER_CAPACITY, 
                        "workers_needed": 1,
                        "master_address": f"{MASTER_HOST}:{MASTER_PORT}"
                    })
                    writer.write(req.encode('utf-8'))
                    await writer.drain()
                    
                    data = await asyncio.wait_for(reader.readline(), timeout=5.0)
                    log_master(f"Resposta de {neighbor}: {data.decode().strip()}")
                    writer.close()
                    await writer.wait_closed()
                except Exception as e:
                    log_error(f"Falha ao pedir ajuda a {neighbor}: {e}")
                    
        elif current_load < RELEASE_THRESHOLD:
            # Devolver os workers emprestados se a carga normalizou
            borrowed = [uid for uid, t in known_workers.items() if t == "Emprestado"]
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

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info('peername')
    log_master(f"Nova conexão estabelecida com {addr}")

    try:
        while True:
            # Lê os dados do stream até encontrar o delimitador de nova linha '\n'
            data = await reader.readline()
            
            if not data:
                # Conexão encerrada pelo lado do cliente
                break
            
            message = data.decode('utf-8').strip()
            if message:
                try:
                    msg_type, req_id, msg_payload = parse_message(message)
                    
                    if msg_type:
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
                                    
                                    # Remove ele da lista, pois ele vai desconectar
                                    known_workers.pop(chosen_worker, None)
                                    connected_workers.pop(chosen_worker, None)
                            else:
                                response = build_message("response_rejected", {"reason": "no_workers_available"}, req_id)
                                writer.write(response.encode('utf-8'))
                                await writer.drain()
                            
                        elif msg_type == "register_temporary_worker":
                            worker_uuid = msg_payload.get("worker_id")
                            orig = msg_payload.get("original_master_address")
                            known_workers[worker_uuid] = "Emprestado"
                            connected_workers[worker_uuid] = writer
                            borrowed_origins[worker_uuid] = orig
                            log_master(f"Registrado Worker temporário {worker_uuid} vindo de {orig}")
                            
                        elif msg_type == "notify_worker_returned":
                            worker_id = msg_payload.get("worker_id")
                            log_master(f"Master vizinho confirmou devolução do Worker {worker_id}")
                            
                        continue
                        
                    payload = json.loads(message)
                    
                    # 1. Solicitação de Tarefa
                    if payload.get("WORKER") == "ALIVE":
                        worker_uuid = payload.get("WORKER_UUID", "Desconhecido")
                        server_uuid = payload.get("SERVER_UUID")
                        
                        # Verifica Diferencial de Origem
                        worker_type = "Emprestado" if server_uuid else "Local"
                        known_workers[worker_uuid] = worker_type
                        connected_workers[worker_uuid] = writer
                        
                        log_master(f"Worker [{worker_type}] {worker_uuid} ({addr}) solicitou tarefa (ALIVE)")
                        
                        # 2. Distribuição de Carga e Gestão de Fila
                        if not task_queue.empty():
                            # Entrega de Tarefa (com tarefa)
                            task = task_queue.get_nowait()
                            response_payload = task
                            log_master(f"Distribuindo tarefa QUERY para Worker [{worker_type}] {worker_uuid}")
                        else:
                            # Entrega de Tarefa (sem tarefa)
                            response_payload = {
                                "TASK": "NO_TASK"
                            }
                            log_master(f"Fila vazia. Nenhuma tarefa para Worker [{worker_type}] {worker_uuid}")
                            
                        response_message = json.dumps(response_payload) + "\n"
                        writer.write(response_message.encode('utf-8'))
                        await writer.drain()
                        
                    # 3. Reporte de Status
                    elif "STATUS" in payload and "TASK" in payload:
                        worker_uuid = payload.get("WORKER_UUID", "Desconhecido")
                        status = payload.get("STATUS")
                        task = payload.get("TASK")
                        
                        worker_type = known_workers.get(worker_uuid, "Desconhecido")
                        log_master(f"Worker [{worker_type}] {worker_uuid} reportou STATUS: {status} para a TASK: {task}")
                        
                        # 4. Confirmação Final (ACK)
                        ack_payload = {
                            "STATUS": "ACK",
                            "WORKER_UUID": worker_uuid
                        }
                        ack_message = json.dumps(ack_payload) + "\n"
                        writer.write(ack_message.encode('utf-8'))
                        await writer.drain()
                        log_master(f"Enviou ACK para o Worker [{worker_type}] {worker_uuid}")
                        
                    else:
                        log_master(f"Mensagem não reconhecida de {addr}: {payload}")
                        
                except json.JSONDecodeError:
                    log_error(f"Erro ao decodificar JSON recebido de {addr}: {message}")
                
    except asyncio.CancelledError:
        pass
    except Exception as e:
        log_error(f"Erro inesperado na conexão com {addr}: {e}")
    finally:
        log_master(f"Conexão encerrada com {addr}")
        writer.close()
        await writer.wait_closed()

async def main():
    # Inicia a task de fundo que popula a fila
    asyncio.create_task(populate_tasks())
    # Inicia o monitor de saturação
    asyncio.create_task(monitor_load())
    
    server = await asyncio.start_server(
        handle_client, MASTER_HOST, MASTER_PORT
    )

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    log_master(f"Servidor Master escutando em {addrs}")

    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    try:
        log_master("Iniciando o Servidor Master...")
        asyncio.run(main())
    except KeyboardInterrupt:
        log_master("Servidor Master encerrado manualmente.")
