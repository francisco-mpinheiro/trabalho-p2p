import asyncio
import json
from parser_utils import validate_worker_request, validate_status_report
from config import MASTER_HOST, MASTER_PORT, log_master, log_error, INSTANCE_UUID

class TaskQueue:
    def __init__(self):
        self.tasks = []

    def add_task(self, task: dict):
        self.tasks.append(task)

    async def get_next_task(self) -> dict:
        if not self.tasks:
            return {"TASK": "NO_TASK"}
        return self.tasks.pop(0)

global_task_queue = TaskQueue()
# Adiciona uma pilha de tarefas para simular carga
for i in range(1, 11):
    global_task_queue.add_task({"TASK": "QUERY", "USER": f"user_{i}"})

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
                    
                    if validate_worker_request(payload):
                        worker_uuid = payload.get("WORKER_UUID", "Desconhecido")
                        log_master(f"Worker {worker_uuid} ({addr}) solicitou uma tarefa.")
                        
                        response_payload = await global_task_queue.get_next_task()
                        response_message = json.dumps(response_payload) + "\n"
                        
                        writer.write(response_message.encode('utf-8'))
                        await writer.drain()
                        log_master(f"Enviou tarefa {response_payload.get('TASK')} para Worker {worker_uuid}")
                    elif validate_status_report(payload):
                        log_master(f"Auditoria: Tarefa {payload['TASK']} concluída com {payload['STATUS']} pelo Worker {payload['WORKER_UUID']}")
                        ack_message = json.dumps({"STATUS": "ACK"}) + "\n"
                        writer.write(ack_message.encode('utf-8'))
                        await writer.drain()
                    else:
                        log_master(f"Pacote inválido ou não reconhecido de {addr}: {message}")
                        
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
