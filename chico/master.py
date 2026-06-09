import asyncio
import json
import random
from config import MASTER_HOST, MASTER_PORT, log_master, log_error, INSTANCE_UUID

# Fila de tarefas real (Queue) do Master
task_queue = asyncio.Queue()

# Dicionário para rastrear os tipos dos workers (Local ou Emprestado)
known_workers = {}

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
                    payload = json.loads(message)
                    
                    # 1. Solicitação de Tarefa
                    if payload.get("WORKER") == "ALIVE":
                        worker_uuid = payload.get("WORKER_UUID", "Desconhecido")
                        server_uuid = payload.get("SERVER_UUID")
                        
                        # Verifica Diferencial de Origem
                        worker_type = "Emprestado" if server_uuid else "Local"
                        known_workers[worker_uuid] = worker_type
                        
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
