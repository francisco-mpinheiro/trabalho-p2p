import os
import uuid
from colorama import init, Fore, Style

# Inicializa o colorama para compatibilidade entre sistemas (ex: Windows)
init(autoreset=True)

# Configurações de Rede (Master)
MASTER_HOST = '127.0.0.1'
MASTER_PORT = 5000

# Configurações do Worker
HEARTBEAT_INTERVAL = 10  # Segundos

# Identificadores (UUIDs)
# Se a variável de ambiente não existir, gera um UUID aleatório para esta instância
INSTANCE_UUID = os.getenv('INSTANCE_UUID', str(uuid.uuid4()))

# Identificador do Master Original. Se for preenchido, o Worker atua como "Emprestado"
ORIGINAL_MASTER_UUID = os.getenv('ORIGINAL_MASTER_UUID', None)

# Configurações P2P do Master
MASTER_ID = os.getenv('MASTER_ID', 'Master-Local')
MASTER_CAPACITY = int(os.getenv('MASTER_CAPACITY', '100'))
RELEASE_THRESHOLD = int(os.getenv('RELEASE_THRESHOLD', '60'))

# Lista de vizinhos (outros Masters). Ex: "127.0.0.1:5001,127.0.0.1:5002"
NEIGHBOR_MASTERS = os.getenv('NEIGHBOR_MASTERS', '127.0.0.1:5001').split(',')

# Utilitário de formatação de Logs Coloridos no terminal
def log_master(msg):
    """Log formatado para o Master (Azul Ciano)"""
    print(f"{Fore.CYAN}[MASTER]{Style.RESET_ALL} {msg}")

def log_worker(msg):
    """Log formatado para o Worker (Verde)"""
    print(f"{Fore.GREEN}[WORKER]{Style.RESET_ALL} {msg}")

def log_error(msg):
    """Log de erro (Vermelho)"""
    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {msg}")

def log_warning(msg):
    """Log de aviso (Amarelo)"""
    print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {msg}")
