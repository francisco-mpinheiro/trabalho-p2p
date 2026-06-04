import asyncio
import json
import random
from config import MASTER_HOST, MASTER_PORT, HEARTBEAT_INTERVAL, INSTANCE_UUID, log_worker, log_error, log_warning

async def simulate_processing(task: dict) -> str:
    """Simula o tempo de execução de uma tarefa com sucesso aleatório."""
    log_worker(f"Processando os dados da tarefa {task.get('TASK', 'desconhecida')}...")
    # Simula um delay entre 0.5 e 2 segundos
    await asyncio.sleep(random.uniform(0.5, 2.0))
    # 80% de chance de sucesso, 20% de falha
    return "OK" if random.random() > 0.2 else "NOK"

async def task_loop(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Solicita tarefas ao Master, simula a execução e reporta o status."""
    while True:
        payload = {
            "WORKER": "ALIVE",
            "WORKER_UUID": INSTANCE_UUID
        }
        
        message = json.dumps(payload) + "\n"
        
        try:
            log_worker("Solicitando tarefa ao Master...")
            writer.write(message.encode('utf-8'))
            await writer.drain()
            
            try:
                data = await asyncio.wait_for(reader.readline(), timeout=5.0)
                if not data:
                    log_error("Conexão fechada pelo Master durante a solicitação.")
                    break
                    
                response_str = data.decode('utf-8').strip()
                if response_str:
                    response_payload = json.loads(response_str)
                    task_type = response_payload.get("TASK")
                    
                    if task_type == "NO_TASK":
                        log_worker(f"Nenhuma tarefa disponível. Aguardando {HEARTBEAT_INTERVAL}s...")
                        await asyncio.sleep(HEARTBEAT_INTERVAL)
                    elif task_type:
                        log_worker(f"Tarefa recebida: {task_type}. Iniciando processamento...")
                        status = await simulate_processing(response_payload)
                        
                        status_payload = {
                            "STATUS": status,
                            "TASK": task_type,
                            "WORKER_UUID": INSTANCE_UUID
                        }
                        writer.write((json.dumps(status_payload) + "\n").encode('utf-8'))
                        await writer.drain()
                        log_worker(f"Status '{status}' reportado. Aguardando ACK...")
                        
                        ack_data = await asyncio.wait_for(reader.readline(), timeout=5.0)
                        if ack_data:
                            ack_str = ack_data.decode('utf-8').strip()
                            if json.loads(ack_str).get("STATUS") == "ACK":
                                log_worker("ACK recebido do Master. Ciclo concluído.")
                            else:
                                log_warning(f"Resposta inesperada aguardando ACK: {ack_str}")
                    else:
                        log_warning(f"Resposta desconhecida do Master: {response_str}")
            except asyncio.TimeoutError:
                log_error("Timeout (5s) aguardando resposta do Master. Forçando reconexão...")
                break
            except json.JSONDecodeError:
                log_error(f"Erro ao decodificar JSON da resposta do Master: {response_str}")
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            log_error(f"Falha na comunicação com o Master: {e}")
            break # Quebra o loop para forçar uma reconexão

async def worker_client():
    """Mantém a conexão com o Master ativa, com suporte a reconexão."""
    while True:
        try:
            log_worker(f"Tentando conectar ao Master em {MASTER_HOST}:{MASTER_PORT}...")
            reader, writer = await asyncio.open_connection(MASTER_HOST, MASTER_PORT)
            log_worker("Conectado com sucesso ao Master!")
            
            # Inicia o loop de tarefas (bloqueia até a conexão cair)
            await task_loop(reader, writer)
            
            writer.close()
            await writer.wait_closed()
            
        except ConnectionRefusedError:
            log_warning("Conexão recusada. O Master está offline? Tentando reconectar em 5 segundos...")
            await asyncio.sleep(5)
        except asyncio.TimeoutError:
            log_warning("Timeout ao tentar conectar. Tentando reconectar em 5 segundos...")
            await asyncio.sleep(5)
        except Exception as e:
            log_error(f"Erro inesperado: {e}. Tentando reconectar em 5 segundos...")
            await asyncio.sleep(5)

if __name__ == '__main__':
    try:
        log_worker(f"Iniciando Worker (UUID: {INSTANCE_UUID})")
        asyncio.run(worker_client())
    except KeyboardInterrupt:
        log_worker("Worker encerrado manualmente.")
