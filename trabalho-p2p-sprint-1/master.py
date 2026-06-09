import asyncio
import json
from config import MASTER_HOST, MASTER_PORT, log_master, log_error, INSTANCE_UUID

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
                    
                    if payload.get("TASK") == "HEARTBEAT":
                        worker_uuid = payload.get("SERVER_UUID", "Desconhecido")
                        log_master(f"HEARTBEAT recebido do Worker {worker_uuid} ({addr})")
                        
                        # Prepara a resposta
                        response_payload = {
                            "SERVER_UUID": INSTANCE_UUID,
                            "TASK": "HEARTBEAT",
                            "RESPONSE": "ALIVE"
                        }
                        response_message = json.dumps(response_payload) + "\n"
                        
                        writer.write(response_message.encode('utf-8'))
                        await writer.drain()
                        log_master(f"Enviou resposta ALIVE para Worker {worker_uuid}")
                    else:
                        log_master(f"Tarefa não reconhecida de {addr}: {payload.get('TASK')}")
                        
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
