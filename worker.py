import socket
import json
import time
import sys
import random

HOST = '10.62.217.204'
PORT = 5000
WORKER_UUID = "W-123" # Simulação de ID único
SERVER_UUID = "Master_10" # Apenas se for emprestado [cite: 128]

def ler_mensagem_completa(s):
    """Função auxiliar para garantir a leitura até o \\n"""
    buffer = ""
    while True:
        chunk = s.recv(1024).decode('utf-8')
        if not chunk:
            return None
        buffer += chunk
        if '\n' in buffer:
            return buffer.split('\n')[0]

def start_worker():
    print("[*] Iniciando Worker... Pressione Ctrl+C para encerrar.")
    
    try:
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5) # Timeout máximo de 5 segundos 
                    s.connect((HOST, PORT))
                    
                    # 1. Apresentação e Pedido de Tarefa [cite: 101, 164]
                    payload_apresentacao = {
                        "WORKER": "ALIVE",
                        "WORKER_UUID": WORKER_UUID
                        # "SERVER_UUID": SERVER_UUID  # Descomente se "emprestado" [cite: 103, 165]
                    }
                    s.sendall((json.dumps(payload_apresentacao) + '\n').encode('utf-8'))
                    
                    # Aguarda distribuição de carga do Master [cite: 106]
                    data = ler_mensagem_completa(s)
                    if not data:
                        continue
                        
                    response = json.loads(data)
                    
                    if response.get("TASK") == "NO_TASK":
                        print("Log: Fila Vazia. Nenhuma tarefa atribuída.") [cite: 109, 182]
                    
                    elif response.get("TASK") == "QUERY":
                        user = response.get("USER")
                        print(f"Log: Tarefa recebida (USER: {user}). Iniciando processamento...")
                        
                        # 2. Simulação de Processamento (Cálculo/Sleep) [cite: 111, 170]
                        tempo_processamento = random.randint(1, 3)
                        time.sleep(tempo_processamento)
                        
                        # 3. Reporte de Status [cite: 110, 174]
                        # Simula 80% de chance de sucesso (OK) e 20% de falha (NOK)
                        status_final = "OK" if random.random() > 0.2 else "NOK"
                        
                        payload_status = {
                            "STATUS": status_final,
                            "TASK": "QUERY",
                            "WORKER_UUID": WORKER_UUID
                        } [cite: 145, 146]
                        s.sendall((json.dumps(payload_status) + '\n').encode('utf-8'))
                        print(f"Log: Reporte enviado ({status_final}). Aguardando ACK...")
                        
                        # 4. Confirmação Final (ACK) do Master [cite: 113, 178]
                        ack_data = ler_mensagem_completa(s)
                        if ack_data:
                            ack_response = json.loads(ack_data)
                            if ack_response.get("STATUS") == "ACK":
                                print("Log: ACK recebido. Ciclo encerrado com sucesso.\n") [cite: 121, 179]
                                
            except (ConnectionRefusedError, socket.timeout, OSError) as e:
                print(f"Log: Status OFFLINE/Timeout - {e} - Tentando Reconectar") [cite: 93]
            except json.JSONDecodeError:
                print("Log: Status ERRO - Resposta inválida")
            
            # Aguarda antes do próximo ciclo para não bombardear o Master com conexões
            time.sleep(4)
            
    except KeyboardInterrupt:
        print("\n[*] Ctrl+C detectado. Encerrando o Worker graciosamente...")
        sys.exit(0)

if __name__ == "__main__":
    start_worker()