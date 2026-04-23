import socket
import threading
import json
import queue

# Configurações de Rede
HOST = '10.62.217.204'
PORT = 5000
SERVER_UUID = "Master_10"

# Fila de tarefas Thread-Safe (Simulando o Backlog)
task_queue = queue.Queue()
task_queue.put({"USER": "Michel"}) # Tarefas do CT01 [cite: 161]
task_queue.put({"USER": "Julia"})  # Tarefas do CT02 [cite: 161]

def handle_client(conn, addr):
    """Lida com a conexão de um Worker individualmente."""
    print(f"[NOVO WORKER] Conectado por {addr}")
    buffer = ""
    
    with conn:
        while True:
            try:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                
                if '\n' in buffer:
                    messages = buffer.split('\n')
                    
                    for msg in messages[:-1]: 
                        if not msg.strip(): continue # Ignora linhas em branco
                        try:
                            payload = json.loads(msg)
                            
                            # -----------------------------------------
                            # SPRINT 1: HEARTBEAT
                            # -----------------------------------------
                            if payload.get("TASK") == "HEARTBEAT":
                                response = {
                                    "SERVER_UUID": SERVER_UUID,
                                    "TASK": "HEARTBEAT",
                                    "RESPONSE": "ALIVE"
                                }
                                conn.sendall((json.dumps(response) + '\n').encode('utf-8'))
                            
                            # -----------------------------------------
                            # SPRINT 2: APRESENTAÇÃO E ENTREGA DE TAREFA [cite: 101, 106]
                            # -----------------------------------------
                            elif payload.get("WORKER") == "ALIVE":
                                worker_uuid = payload.get("WORKER_UUID")
                                server_uuid = payload.get("SERVER_UUID", "Local") # Opcional [cite: 128]
                                
                                if not worker_uuid:
                                    print("[ERRO] WORKER_UUID ausente na apresentação.")
                                    continue
                                    
                                print(f"[*] Apresentação: Worker {worker_uuid} (Origem: {server_uuid})")
                                
                                # Verifica a fila de tarefas [cite: 108]
                                if not task_queue.empty():
                                    task = task_queue.get()
                                    response = {
                                        "TASK": "QUERY",
                                        "USER": task["USER"]
                                    } # Payload 2.2 [cite: 109]
                                else:
                                    response = {
                                        "TASK": "NO_TASK"
                                    } # Payload 2.3 [cite: 109]
                                    
                                conn.sendall((json.dumps(response) + '\n').encode('utf-8'))
                            
                            # -----------------------------------------
                            # SPRINT 2: REPORTE DE STATUS E ACK [cite: 110, 113]
                            # -----------------------------------------
                            elif payload.get("STATUS") in ["OK", "NOK"] and payload.get("TASK") == "QUERY":
                                worker_uuid = payload.get("WORKER_UUID")
                                status = payload.get("STATUS")
                                
                                if not worker_uuid:
                                    continue
                                
                                # Registra no Log [cite: 115]
                                print(f"[*] Tarefa concluída por {worker_uuid}. Status: {status}")
                                
                                # Confirmação Final (ACK) [cite: 154, 155]
                                response = {
                                    "STATUS": "ACK",
                                    "WORKER_UUID": worker_uuid
                                }
                                conn.sendall((json.dumps(response) + '\n').encode('utf-8'))
                                print(f"[*] ACK enviado para {worker_uuid}. Worker liberado.")

                        except json.JSONDecodeError:
                            print("[ERRO] Falha ao decodificar JSON do Worker.")
                            
                    buffer = messages[-1] 
                    
            except Exception as e:
                print(f"[ERRO] Falha na conexão com {addr}: {e}")
                break
                
    print(f"[WORKER DESCONECTADO] {addr}")

def start_master():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        
        print(f"[*] Master ({SERVER_UUID}) escutando em {HOST}:{PORT}")
        
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

if __name__ == "__main__":
    start_master()