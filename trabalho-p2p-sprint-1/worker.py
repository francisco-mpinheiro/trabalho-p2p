import asyncio
import json
from config import MASTER_HOST, MASTER_PORT, HEARTBEAT_INTERVAL, INSTANCE_UUID, log_worker, log_error, log_warning

async def heartbeat_loop(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Envia o payload de HEARTBEAT em intervalos regulares."""
    while True:
        payload = {
            "SERVER_UUID": INSTANCE_UUID,
            "TASK": "HEARTBEAT"
        }
        
        # Codifica como JSON e adiciona o delimitador de nova linha '\n'
        message = json.dumps(payload) + "\n"
        
        try:
            log_worker("Enviando requisição de HEARTBEAT...")
            writer.write(message.encode('utf-8'))
            await writer.drain()
            
            # Aguarda a resposta do Master
            try:
                # Usa timeout para não ficar travado indefinidamente caso o Master não responda
                data = await asyncio.wait_for(reader.readline(), timeout=5.0)
                if not data:
                    log_error("Conexão fechada pelo Master durante o HEARTBEAT.")
                    break
                    
                response_str = data.decode('utf-8').strip()
                if response_str:
                    response_payload = json.loads(response_str)
                    
                    if response_payload.get("TASK") == "HEARTBEAT" and response_payload.get("RESPONSE") == "ALIVE":
                        master_uuid = response_payload.get("SERVER_UUID", "Desconhecido")
                        log_worker(f"Master {master_uuid} respondeu: ALIVE. Conexão saudável.")
                    else:
                        log_warning(f"Resposta inesperada do Master: {response_str}")
            except asyncio.TimeoutError:
                log_error("Timeout aguardando resposta do Master. Forçando reconexão...")
                break
            except json.JSONDecodeError:
                log_error(f"Erro ao decodificar JSON da resposta do Master: {response_str}")
            
            # Aguarda o intervalo antes de enviar o próximo heartbeat
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            
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

if __name__ == '__main__':
    try:
        log_worker(f"Iniciando Worker (UUID: {INSTANCE_UUID})")
        asyncio.run(worker_client())
    except KeyboardInterrupt:
        log_worker("Worker encerrado manualmente.")
