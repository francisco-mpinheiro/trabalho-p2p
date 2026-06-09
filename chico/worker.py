import asyncio
import json
from config import MASTER_HOST, MASTER_PORT, HEARTBEAT_INTERVAL, INSTANCE_UUID, ORIGINAL_MASTER_UUID, log_worker, log_error, log_warning

async def heartbeat_loop(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Envia solicitações de tarefa e processa as respostas e reportes."""
    while True:
        # 1. Solicitação de Tarefa (Worker -> Master)
        payload = {
            "WORKER": "ALIVE",
            "WORKER_UUID": INSTANCE_UUID
        }
        
        # Diferencial de Origem: Worker "Emprestado"
        if ORIGINAL_MASTER_UUID:
            payload["SERVER_UUID"] = ORIGINAL_MASTER_UUID
        
        # Codifica como JSON e adiciona o delimitador de nova linha '\n'
        message = json.dumps(payload) + "\n"
        
        try:
            log_worker("Enviando solicitação de tarefa (ALIVE)...")
            writer.write(message.encode('utf-8'))
            await writer.drain()
            
            # Aguarda a resposta do Master (Entrega de Tarefa)
            try:
                # Usa timeout para não ficar travado indefinidamente caso o Master não responda
                data = await asyncio.wait_for(reader.readline(), timeout=5.0)
                if not data:
                    log_error("Conexão fechada pelo Master durante a solicitação de tarefa.")
                    break
                    
                response_str = data.decode('utf-8').strip()
                if response_str:
                    response_payload = json.loads(response_str)
                    task = response_payload.get("TASK")
                    
                    if task == "NO_TASK":
                        log_worker("Master respondeu: NO_TASK. Nenhuma tarefa no momento.")
                    elif task == "QUERY":
                        user = response_payload.get("USER", "Desconhecido")
                        log_worker(f"Tarefa recebida: QUERY para o usuário {user}. Executando...")
                        
                        # Simula a execução da tarefa
                        await asyncio.sleep(1) # Simula 1 segundo de processamento
                        log_worker("Tarefa executada com sucesso.")
                        
                        # 3. Reporte de Status (Worker -> Master)
                        status_payload = {
                            "STATUS": "OK",
                            "TASK": "QUERY",
                            "WORKER_UUID": INSTANCE_UUID
                        }
                        status_message = json.dumps(status_payload) + "\n"
                        
                        log_worker("Enviando reporte de status (OK)...")
                        writer.write(status_message.encode('utf-8'))
                        await writer.drain()
                        
                        # 4. Confirmação Final (Master -> Worker)
                        ack_data = await asyncio.wait_for(reader.readline(), timeout=5.0)
                        if not ack_data:
                            log_error("Conexão fechada pelo Master durante aguardo do ACK.")
                            break
                        
                        ack_str = ack_data.decode('utf-8').strip()
                        if ack_str:
                            ack_payload = json.loads(ack_str)
                            if ack_payload.get("STATUS") == "ACK":
                                log_worker("Confirmação final (ACK) recebida do Master.")
                            else:
                                log_warning(f"Master enviou resposta inesperada em vez de ACK: {ack_str}")
                    else:
                        log_warning(f"Resposta inesperada do Master: {response_str}")
            except asyncio.TimeoutError:
                log_error("Timeout aguardando resposta do Master. Forçando reconexão...")
                break
            except json.JSONDecodeError:
                log_error(f"Erro ao decodificar JSON da resposta do Master: {response_str}")
            
            # Aguarda o intervalo antes de enviar a próxima solicitação
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            log_error(f"Falha na comunicação com o Master: {e}")
            break # Quebra o loop para forçar uma reconexão

import sys

async def worker_client():
    """Mantém a conexão com o Master ativa, com suporte a reconexão."""
    try:
        while True:
            try:
                log_worker(f"Tentando conectar ao Master em {MASTER_HOST}:{MASTER_PORT}...")
                reader, writer = await asyncio.open_connection(MASTER_HOST, MASTER_PORT)
                log_worker("Conectado com sucesso ao Master!")
                
                # Inicia o loop de heartbeat (bloqueia até a conexão cair)
                await heartbeat_loop(reader, writer)
                
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
    except asyncio.CancelledError:
        pass

if __name__ == '__main__':
    try:
        log_worker(f"Iniciando Worker (UUID: {INSTANCE_UUID})")
        asyncio.run(worker_client())
    except KeyboardInterrupt:
        log_worker("Worker encerrado manualmente.")
