import socket
import json
import time

# Configurações do Master alvo
HOST = '127.0.0.1'
PORT = 5000
SERVER_UUID = "Master_A"

def start_worker():
    """Inicia o ciclo de vida do Worker."""
    print("[*] Iniciando Worker...")
    
    while True:
        try:
            # Cria o socket e tenta conectar
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5) # Timeout para evitar travamento se o Master não responder
                s.connect((HOST, PORT))
                
                # Prepara o Payload Oficial
                payload = {
                    "SERVER_UUID": SERVER_UUID,
                    "TASK": "HEARTBEAT"
                }
                
                # Envia JSON com delimitador \n
                mensagem_json = json.dumps(payload) + '\n'
                s.sendall(mensagem_json.encode('utf-8'))
                
                # Aguarda a resposta
                data = s.recv(1024).decode('utf-8')
                
                if data:
                    # O strip() remove o \n do final para podermos fazer o parse
                    response = json.loads(data.strip())
                    
                    if response.get("RESPONSE") == "ALIVE":
                        print("Log: Status: ALIVE")
                        
        except (ConnectionRefusedError, socket.timeout, OSError):
            # Se der erro de rede, master offline ou timeout
            print("Log: Status: OFFLINE - Tentando Reconectar")
        except json.JSONDecodeError:
            print("Log: Status: ERRO - Resposta inválida do Master")
            
        # Aguarda 30 segundos antes do próximo envio (conforme diagrama)
        time.sleep(30)

if __name__ == "__main__":
    start_worker()