import os
import uuid
from colorama import init, Fore, Style

# Inicializa o colorama para compatibilidade entre sistemas (ex: Windows)
init(autoreset=True)

# Configurações de Rede (Master)
MASTER_HOST = '25.45.84.235'
MASTER_PORT = int(os.getenv('MASTER_PORT', '8000'))

# Configurações do Worker
HEARTBEAT_INTERVAL = 10  # Segundos

# Identificadores (UUIDs)
# Se a variável de ambiente não existir, gera um UUID aleatório para esta instância
INSTANCE_UUID = os.getenv('INSTANCE_UUID', str(uuid.uuid4()))

# Identificador do Master Original. Se for preenchido, o Worker atua como "Emprestado"
ORIGINAL_MASTER_UUID = os.getenv('ORIGINAL_MASTER_UUID', None)

# Configurações P2P do Master
MASTER_ID = os.getenv('MASTER_ID', 'Master_9')
MASTER_CAPACITY = int(os.getenv('MASTER_CAPACITY', '5'))
RELEASE_THRESHOLD = int(os.getenv('RELEASE_THRESHOLD', '60'))

# Lista de vizinhos (outros Masters). Ex: "127.0.0.1:5001,127.0.0.1:5002"
NEIGHBOR_MASTERS = os.getenv('NEIGHBOR_MASTERS', '25.45.84.204:8000').split(',')

# Configurações do Supervisor (Sprint 04)
SUPERVISOR_HOST = os.getenv('SUPERVISOR_HOST', 'nuted-ia.dev')
SUPERVISOR_PORT = int(os.getenv('SUPERVISOR_PORT', '443'))
SUPERVISOR_TLS = True
SUPERVISOR_SNI = "nuted-ia.dev"

MAX_TASK = int(os.getenv('MAX_TASK', '100'))
WARN_CPU_PERCENT = int(os.getenv('WARN_CPU_PERCENT', '85'))
WARN_MEMORY_PERCENT = int(os.getenv('WARN_MEMORY_PERCENT', '85'))
RELEASE_TASK = int(os.getenv('RELEASE_TASK', '60'))

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
