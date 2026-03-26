import socket
import threading
import json

# Configurações de Rede
HOST = '127.0.0.1'
PORT = 5000
SERVER_UUID = "Master_A"

def handle_client(conn, addr):
    """Lida com a conexão de um Worker individualmente (concorrência)."""
    print(f"[NOVO WORKER] Conectado por {addr}")
    buffer = ""
    
    with conn:
        while True:
            try:
                # Lê os dados do stream TCP
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break # Conexão fechada pelo cliente
                
                buffer += data
                
                # Verifica se encontrou o delimitador de nova linha (\n)
                if '\n' in buffer:
                    messages = buffer.split('\n')
                    
                    # Processa todas as mensagens completas no buffer
                    for msg in messages[:-1]: 
                        try:
                            payload = json.loads(msg)
                            
                            # Valida a Task de Heartbeat
                            if payload.get("TASK") == "HEARTBEAT":
                                response = {
                                    "SERVER_UUID": SERVER_UUID,
                                    "TASK": "HEARTBEAT",
                                    "RESPONSE": "ALIVE"
                                }
                                # Envia a resposta com o delimitador \n
                                resposta_json = json.dumps(response) + '\n'
                                conn.sendall(resposta_json.encode('utf-8'))
                                print(f"[HEARTBEAT] Respondido para {addr}")
                                
                        except json.JSONDecodeError:
                            print("[ERRO] Falha ao decodificar JSON do Worker.")
                            
                    # Mantém no buffer qualquer pedaço de mensagem incompleta
                    buffer = messages[-1] 
                    
            except Exception as e:
                print(f"[ERRO] Falha na conexão com {addr}: {e}")
                break
                
    print(f"[WORKER DESCONECTADO] {addr}")

def start_master():
    """Inicia o servidor TCP do Master."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Permite reuso da porta
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        
        print(f"[*] Master ({SERVER_UUID}) escutando em {HOST}:{PORT}")
        
        # Loop infinito para aceitar novas conexões
        while True:
            conn, addr = server_socket.accept()
            # Inicia uma Thread para cada novo Worker (Garante concorrência)
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

if __name__ == "__main__":
    start_master()